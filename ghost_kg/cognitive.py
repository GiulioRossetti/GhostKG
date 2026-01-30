"""
Cognitive Loop - High-Level Agent Behavior

This module implements the CognitiveLoop class which provides high-level cognitive
operations for agents:
- Absorbing information from text
- Reflecting on own statements
- Generating replies based on memory
"""

import json
from typing import Optional

from .agent import GhostAgent
from .fsrs import Rating
from .extraction import get_extractor, HAS_FAST_MODE


class CognitiveLoop:
    """
    High-level cognitive operations for agents.
    
    Provides:
    - absorb(): Learn from incoming text (fast or LLM mode)
    - reflect(): Reinforce beliefs from own statements
    - reply(): Generate responses based on memory
    
    Attributes:
        agent (GhostAgent): The agent performing cognitive operations
        model (str): LLM model name for generation
        fast_mode (bool): Whether to use fast extraction or LLM extraction
        extractor: Triplet extraction strategy (fast or LLM)
    """
    
    def __init__(self, agent: GhostAgent, model: str = "llama3.2", fast_mode: bool = False):
        """
        Initialize cognitive loop for an agent.
        
        Args:
            agent: GhostAgent instance to operate on
            model: LLM model name (e.g., "llama3.2")
            fast_mode: If True, use fast extraction; otherwise use LLM
        """
        self.agent = agent
        self.model = model
        self.fast_mode = fast_mode
        
        # Initialize extractor based on mode
        try:
            if self.fast_mode:
                self.extractor = get_extractor(
                    fast_mode=True,
                    client=None,
                    model=None
                )
            else:
                self.extractor = get_extractor(
                    fast_mode=False,
                    client=self.agent.client,
                    model=self.model
                )
        except ImportError as e:
            print(f"Warning: {e}")
            print("Falling back to LLM mode")
            self.fast_mode = False
            self.extractor = get_extractor(
                fast_mode=False,
                client=self.agent.client,
                model=self.model
            )

    def absorb(self, text: str, author: str = "User") -> None:
        """
        Learn from incoming text by extracting and storing knowledge triplets.
        
        Dispatches to either fast mode (GLiNER + TextBlob) or LLM mode
        based on configuration.
        
        Args:
            text: Input text to learn from
            author: Name of the text author
        """
        # Extract triplets using configured extractor
        data = self.extractor.extract(text, author, self.agent.name)
        
        # Process extracted triplets
        for item in data.get("world_facts", []):
            self.agent.learn_triplet(
                item["source"], item["relation"], item["target"]
            )
        
        for item in data.get("partner_stance", []):
            sentiment = item.get("sentiment", 0.0)
            self.agent.learn_triplet(
                item["source"], 
                item["relation"], 
                item["target"],
                sentiment=sentiment
            )
        
        for item in data.get("my_reaction", []):
            s_score = item.get("sentiment", 0.0)
            rating = item.get("rating", Rating.Good)
            self.agent.learn_triplet(
                "I",
                item["relation"],
                item["target"],
                rating=rating,
                sentiment=s_score,
            )
        
        # Log the interaction
        self.agent.db.log_interaction(
            self.agent.name, 
            "READ", 
            text, 
            data, 
            timestamp=self.agent.current_time
        )
        
        # Print summary for LLM mode
        if not self.fast_mode:
            print(
                f"   > Internalized {len(data.get('world_facts', []))} facts & "
                f"formed {len(data.get('my_reaction', []))} opinions."
            )

    def reflect(self, text: str) -> None:
        """
        Reflect on agent's own statement to reinforce expressed beliefs.
        
        Uses LLM to extract beliefs from the agent's own generated text
        and reinforces them with high memory ratings.
        
        Args:
            text: Agent's own statement to reflect on
        """
        print(f"   > [Self-Reflection] Analyzing my own words...")
        
        prompt = f"""
        You are {self.agent.name}. You just said: "{text}"
        Task: Extract the beliefs/stances YOU just expressed.
        CRITICAL: Relations must be active verbs (e.g. "support", "oppose", "fear"), NOT grammatical labels.

        Return JSON: {{ "my_expressed_stances": [ {{"relation": "verb", "target": "Entity", "sentiment": 0.5}} ] }}
        """
        
        try:
            res = self.agent.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
            )
            data = json.loads(res["message"]["content"])
            
            count = 0
            for item in data.get("my_expressed_stances", []):
                s_score = item.get("sentiment", 0.0)
                self.agent.learn_triplet(
                    "I",
                    item["relation"],
                    item["target"],
                    rating=Rating.Easy,  # High rating for self-expressed beliefs
                    sentiment=s_score,
                )
                count += 1
            print(f"   > [Self-Reflection] Reinforced {count} beliefs.")
            
        except Exception as e:
            print(f"Error reflecting: {e}")

    def reply(self, topic: str, partner_name: str) -> Optional[str]:
        """
        Generate a reply about a topic based on agent's memory.
        
        Retrieves relevant context from memory and uses LLM to generate
        a response. Also reflects on the generated response to reinforce
        expressed beliefs.
        
        Args:
            topic: Topic to reply about
            partner_name: Name of conversation partner
            
        Returns:
            Generated reply text, or None if generation fails
        """
        context = self.agent.get_memory_view(topic)
        
        prompt = f"""
        You are {self.agent.name}. Talking to {partner_name} about {topic}.
        YOUR MEMORY: {context}
        Task: Write a short 1-sentence reply. Prioritize YOUR STANCE.
        """
        
        try:
            res = self.agent.client.chat(
                model=self.model, 
                messages=[{"role": "user", "content": prompt}]
            )
            content = res["message"]["content"]
            
            # Log the generated response
            self.agent.db.log_interaction(
                self.agent.name,
                "WRITE",
                content,
                {"context_used": context},
                timestamp=self.agent.current_time,
            )
            
            print(
                f"   > {self.agent.name} "
                f"({self.agent.current_time.strftime('%H:%M')}): {content}"
            )
            
            # Reflect on own statement to reinforce beliefs
            self.reflect(content)
            
            return content
            
        except Exception as e:
            print(f"Error replying: {e}")
            return ""  # Return empty string instead of None for consistency
