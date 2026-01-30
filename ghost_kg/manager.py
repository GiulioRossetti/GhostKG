"""
AgentManager - External API for GhostKG

This module provides a high-level interface for external programs to interact
with individual agent Knowledge Graphs without handling the LLM logic.
"""

import datetime
from typing import Optional, Dict, List, Tuple
from .agent import GhostAgent
from .fsrs import Rating
from .storage import KnowledgeDB
from .exceptions import ValidationError, AgentNotFoundError


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

    def __init__(self, db_path: str = "agent_memory.db") -> None:
        """
        Initialize the AgentManager.

        Args:
            db_path (str): Path to the SQLite database file
            
        Returns:
            None
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
            name (str): Name of the agent
            llm_host (str): LLM host URL (optional, for internal LLM operations)

        Returns:
            GhostAgent: GhostAgent instance
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError("Agent name must be a non-empty string")
            
        if name not in self.agents:
            self.agents[name] = GhostAgent(
                name, db_path=self.db_path, llm_host=llm_host
            )
        return self.agents[name]

    def get_agent(self, name: str) -> Optional[GhostAgent]:
        """
        Get an existing agent.

        Args:
            name (str): Name of the agent

        Returns:
            Optional[GhostAgent]: GhostAgent instance or None if not found
        """
        return self.agents.get(name)

    def set_agent_time(self, agent_name: str, time: datetime.datetime) -> None:
        """
        Set the current time for an agent (for simulation/tracking purposes).

        Args:
            agent_name (str): Name of the agent
            time (datetime.datetime): Current time to set
            
        Returns:
            None
            
        Raises:
            AgentNotFoundError: If agent doesn't exist
            ValidationError: If time is invalid
        """
        if not isinstance(time, datetime.datetime):
            raise ValidationError("time must be a datetime object")
            
        agent = self.get_agent(agent_name)
        if not agent:
            raise AgentNotFoundError(f"Agent '{agent_name}' not found")
        agent.set_time(time)

    def absorb_content(
        self,
        agent_name: str,
        content: str,
        author: str = "User",
        triplets: Optional[List[Tuple[str, str, str]]] = None,
        fast_mode: bool = False,
    ) -> None:
        """
        Update agent's KG with content they are replying to.

        This allows external programs to:
        1. Provide their own triplet extraction (via triplets parameter)
        2. Let the agent extract triplets internally (if triplets=None and LLM available)

        Args:
            agent_name (str): Name of the agent
            content (str): The content to absorb
            author (str): Author of the content
            triplets (Optional[List[Tuple[str, str, str]]]): Optional list of (source, relation, target) triplets
                     If provided, these will be learned directly
            fast_mode (bool): If True, use faster processing (if supported by LLM)
            
        Returns:
            None
            
        Raises:
            AgentNotFoundError: If agent doesn't exist
            ValidationError: If parameters are invalid
        """
        if not content or not isinstance(content, str):
            raise ValidationError("content must be a non-empty string")
        if not author or not isinstance(author, str):
            raise ValidationError("author must be a non-empty string")
            
        agent = self.get_agent(agent_name)
        if not agent:
            raise AgentNotFoundError(f"Agent '{agent_name}' not found")

        if triplets:
            # Validate triplets
            if not isinstance(triplets, list):
                raise ValidationError("triplets must be a list")
            for triplet in triplets:
                if not isinstance(triplet, (tuple, list)) or len(triplet) != 3:
                    raise ValidationError("Each triplet must be a 3-tuple (source, relation, target)")
                    
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

            loop = CognitiveLoop(agent, fast_mode=fast_mode)
            loop.absorb(content, author=author)

    def get_context(self, agent_name: str, topic: str) -> str:
        """
        Get all context to be used when the agent replies to content on a topic.

        This retrieves the agent's memory view including:
        - Their current stance on the topic
        - Known facts about the topic
        - What others think about the topic

        Args:
            agent_name (str): Name of the agent
            topic (str): Topic to get context for

        Returns:
            str: Formatted context string
            
        Raises:
            AgentNotFoundError: If agent doesn't exist
            ValidationError: If topic is invalid
        """
        if not topic or not isinstance(topic, str):
            raise ValidationError("topic must be a non-empty string")
            
        agent = self.get_agent(agent_name)
        if not agent:
            raise AgentNotFoundError(f"Agent '{agent_name}' not found")

        return agent.get_memory_view(topic)

    def process_and_get_context(
        self,
        agent_name: str,
        topic: str,
        text: str,
        author: str = "User",
        triplets: Optional[List[Tuple[str, str, str]]] = None,
            fast_mode: bool = False,
    ) -> str:
        """
        Update agent's KG with content and return context for replying (atomic operation).

        This is a convenience method that combines absorb_content() and get_context()
        into a single operation, which is useful for the common workflow:
        1. Agent receives content (topic, text) from a peer
        2. Agent updates its KG with this information
        3. Agent needs context to generate a response

        Args:
            agent_name (str): Name of the agent
            topic (str): The topic of the content
            text (str): The text content to process
            author (str): Author of the content
            triplets (Optional[List[Tuple[str, str, str]]]): Optional list of (source, relation, target) triplets
                     If provided, these will be learned directly
            fast_mode (bool): If True, use faster processing

        Returns:
            str: Formatted context string for the topic (updated with new content)

        Example:
            >>> manager = AgentManager()
            >>> manager.create_agent("Alice")
            >>> manager.set_agent_time("Alice", datetime.datetime.now())
            >>> context = manager.process_and_get_context(
            ...     "Alice", "climate", "Bob says climate change is urgent",
            ...     author="Bob", triplets=[("Bob", "says", "climate urgent")]
            ... )
            >>> # Use context with external LLM to generate response
        """
        # Update KG with the content
        self.absorb_content(agent_name, text, author, triplets, fast_mode)

        # Return updated context for the topic
        return self.get_context(agent_name, topic)

    def update_with_response(
        self,
        agent_name: str,
        response: str,
        triplets: Optional[List[Tuple[str, str, float]]] = None,
        context: Optional[str] = None,
    ) -> None:
        """
        Update agent's personal KG with the text they generated as response.

        This allows external programs to:
        1. Provide their own triplet extraction with sentiment (via triplets parameter)
        2. Let the agent reflect on their own response (if triplets=None and LLM available)

        Args:
            agent_name (str): Name of the agent
            response (str): The response text generated
            triplets (Optional[List[Tuple[str, str, float]]]): Optional list of (relation, target, sentiment) triplets
                     Source is assumed to be "I" (the agent)
            context (Optional[str]): Optional context that was used to generate the response
                    This will be stored in the logs annotations
                    
        Returns:
            None
            
        Raises:
            ValueError: If agent not found
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

            # Log the interaction with context
            annotations = {"triplets_count": len(triplets), "external": True}
            if context is not None:
                annotations["context_used"] = context

            self.db.log_interaction(
                agent_name,
                "WRITE",
                response,
                annotations,
                timestamp=agent.current_time,
            )
        else:
            # Let agent reflect internally (requires LLM)
            from .core import CognitiveLoop

            loop = CognitiveLoop(agent)
            loop.reflect(response)

            # Log the interaction with context
            annotations = {"external": False}
            if context is not None:
                annotations["context_used"] = context

            self.db.log_interaction(
                agent_name,
                "WRITE",
                response,
                annotations,
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
            agent_name (str): Name of the agent
            source (str): Source node
            relation (str): Relation/edge label
            target (str): Target node
            rating (int): FSRS rating (1-4, see Rating class)
            sentiment (float): Sentiment score (-1.0 to 1.0)
            
        Returns:
            None
            
        Raises:
            ValueError: If agent not found
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
            agent_name (str): Name of the agent
            topic (Optional[str]): Optional topic to filter knowledge

        Returns:
            Dict: Dictionary with nodes and edges information
            
        Raises:
            ValueError: If agent not found
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
