"""
AgentManager - External API for GhostKG

This module provides a high-level interface for external programs to interact
with individual agent Knowledge Graphs without handling the LLM logic.
"""

import datetime
from typing import Optional, Dict, List, Tuple
from .core import GhostAgent, Rating
from .storage import KnowledgeDB


class AgentManager:
    """
    Manager for handling multiple agents and their Knowledge Graphs.

    This class provides an external-facing API that allows programs to:
    - Create and manage individual agents
    - Update agent KGs with content they are replying to
    - Retrieve context for generating responses
    - Update agent KGs with generated responses
    - Control time for each interaction
    """

    def __init__(self, db_path: str = "agent_memory.db"):
        """
        Initialize the AgentManager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.agents: Dict[str, GhostAgent] = {}
        self.db = KnowledgeDB(db_path)

    def create_agent(
        self, name: str, llm_host: str = "http://localhost:11434"
    ) -> GhostAgent:
        """
        Create or retrieve an agent.

        Args:
            name: Name of the agent
            llm_host: LLM host URL (optional, for internal LLM operations)

        Returns:
            GhostAgent instance
        """
        if name not in self.agents:
            self.agents[name] = GhostAgent(
                name, db_path=self.db_path, llm_host=llm_host
            )
        return self.agents[name]

    def get_agent(self, name: str) -> Optional[GhostAgent]:
        """
        Get an existing agent.

        Args:
            name: Name of the agent

        Returns:
            GhostAgent instance or None if not found
        """
        return self.agents.get(name)

    def set_agent_time(self, agent_name: str, time: datetime.datetime) -> None:
        """
        Set the current time for an agent (for simulation/tracking purposes).

        Args:
            agent_name: Name of the agent
            time: Current time to set
        """
        agent = self.get_agent(agent_name)
        if agent:
            agent.set_time(time)

    def absorb_content(
        self,
        agent_name: str,
        content: str,
        author: str = "User",
        triplets: Optional[List[Tuple[str, str, str]]] = None,
    ) -> None:
        """
        Update agent's KG with content they are replying to.

        This allows external programs to:
        1. Provide their own triplet extraction (via triplets parameter)
        2. Let the agent extract triplets internally (if triplets=None and LLM available)

        Args:
            agent_name: Name of the agent
            content: The content to absorb
            author: Author of the content
            triplets: Optional list of (source, relation, target) triplets
                     If provided, these will be learned directly
        """
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        if triplets:
            # External program provides triplets
            for source, relation, target in triplets:
                agent.learn_triplet(source, relation, target, rating=Rating.Good)

            # Log the interaction
            self.db.log_interaction(
                agent_name,
                "READ",
                content,
                {"author": author, "triplets_count": len(triplets), "external": True},
                timestamp=agent.current_time,
            )
        else:
            # Let agent extract triplets internally (requires LLM)
            # This is for backward compatibility
            from .core import CognitiveLoop

            loop = CognitiveLoop(agent)
            loop.absorb(content, author=author)

    def get_context(self, agent_name: str, topic: str) -> str:
        """
        Get all context to be used when the agent replies to content on a topic.

        This retrieves the agent's memory view including:
        - Their current stance on the topic
        - Known facts about the topic
        - What others think about the topic

        Args:
            agent_name: Name of the agent
            topic: Topic to get context for

        Returns:
            Formatted context string
        """
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        return agent.get_memory_view(topic)

    def update_with_response(
        self,
        agent_name: str,
        response: str,
        triplets: Optional[List[Tuple[str, str, str, float]]] = None,
    ) -> None:
        """
        Update agent's personal KG with the text they generated as response.

        This allows external programs to:
        1. Provide their own triplet extraction with sentiment (via triplets parameter)
        2. Let the agent reflect on their own response (if triplets=None and LLM available)

        Args:
            agent_name: Name of the agent
            response: The response text generated
            triplets: Optional list of (relation, target, sentiment) triplets
                     Source is assumed to be "I" (the agent)
        """
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        if triplets:
            # External program provides triplets with sentiment
            for relation, target, sentiment in triplets:
                agent.learn_triplet(
                    "I", relation, target, rating=Rating.Easy, sentiment=sentiment
                )

            # Log the interaction
            self.db.log_interaction(
                agent_name,
                "WRITE",
                response,
                {"triplets_count": len(triplets), "external": True},
                timestamp=agent.current_time,
            )
        else:
            # Let agent reflect internally (requires LLM)
            from .core import CognitiveLoop

            loop = CognitiveLoop(agent)
            loop.reflect(response)

            # Log the interaction
            self.db.log_interaction(
                agent_name,
                "WRITE",
                response,
                {"external": False},
                timestamp=agent.current_time,
            )

    def learn_triplet(
        self,
        agent_name: str,
        source: str,
        relation: str,
        target: str,
        rating: int = Rating.Good,
        sentiment: float = 0.0,
    ) -> None:
        """
        Directly add a triplet to an agent's KG.

        Args:
            agent_name: Name of the agent
            source: Source node
            relation: Relation/edge label
            target: Target node
            rating: FSRS rating (1-4, see Rating class)
            sentiment: Sentiment score (-1.0 to 1.0)
        """
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        agent.learn_triplet(
            source, relation, target, rating=rating, sentiment=sentiment
        )

    def get_agent_knowledge(self, agent_name: str, topic: Optional[str] = None) -> Dict:
        """
        Retrieve agent's knowledge graph information.

        Args:
            agent_name: Name of the agent
            topic: Optional topic to filter knowledge

        Returns:
            Dictionary with nodes and edges information
        """
        agent = self.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found")

        if topic:
            n_topic = agent._normalize(topic)
            my_rows = self.db.get_agent_stance(
                agent_name, n_topic, current_time=agent.current_time
            )
            world_rows = self.db.get_world_knowledge(agent_name, n_topic, limit=20)
        else:
            # Get all knowledge
            my_rows = self.db.conn.execute(
                "SELECT source, relation, target, sentiment FROM edges WHERE owner_id = ? AND source = 'I'",
                (agent_name,),
            ).fetchall()
            world_rows = self.db.conn.execute(
                "SELECT source, relation, target FROM edges WHERE owner_id = ? AND source != 'I'",
                (agent_name,),
            ).fetchall()

        return {
            "agent_beliefs": [dict(row) for row in my_rows],
            "world_knowledge": [dict(row) for row in world_rows],
        }
