"""
Cognitive Loop - High-Level Agent Behavior

This module implements the CognitiveLoop class which provides high-level cognitive
operations for agents:
- Absorbing information from text
- Reflecting on own statements
- Generating replies based on memory
"""

import json
import time
from typing import Any, Dict, Optional

from .agent import GhostAgent
from ..utils.exceptions import ExtractionError, LLMError
from ..extraction.extraction import HAS_FAST_MODE, get_extractor
from ..memory.fsrs import Rating


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

    def __init__(self, agent: GhostAgent, model: str = "llama3.2", fast_mode: bool = False) -> None:
        """
        Initialize cognitive loop for an agent.

        Args:
            agent (GhostAgent): GhostAgent instance to operate on
            model (str): LLM model name (e.g., "llama3.2")
            fast_mode (bool): If True, use fast extraction; otherwise use LLM

        Returns:
            None
        """
        self.agent = agent
        self.model = model
        self.fast_mode = fast_mode

        # Initialize extractor based on mode
        try:
            if self.fast_mode:
                self.extractor = get_extractor(
                    fast_mode=True, llm_service=None, model=None  # type: ignore[arg-type]
                )
            else:
                # Require LLM service for LLM mode
                if self.agent.llm_service is None:
                    raise ValueError(
                        "LLM service is required for CognitiveLoop in LLM mode. "
                        "Please provide llm_service when creating the agent."
                    )
                self.extractor = get_extractor(
                    fast_mode=False,
                    llm_service=self.agent.llm_service,
                    model=self.model or "llama3.2",  # type: ignore[arg-type]
                    max_retries=3,
                )
        except ImportError as e:
            print(f"Warning: {e}")
            print("Falling back to LLM mode")
            self.fast_mode = False
            if self.agent.llm_service is None:
                raise ValueError(
                    "LLM service is required for CognitiveLoop. "
                    "Please provide llm_service when creating the agent."
                ) from e
            self.extractor = get_extractor(
                fast_mode=False,
                llm_service=self.agent.llm_service,
                model=self.model,  # type: ignore[arg-type]
                max_retries=3,
            )

    def _call_llm_with_retry(
        self, prompt: str, format: Optional[str] = None, timeout: int = 30, max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Call LLM with timeout and retry logic.

        Args:
            prompt (str): Prompt to send to LLM
            format (Optional[str]): Optional format specification (e.g., "json")
            timeout (int): Timeout in seconds
            max_retries (int): Maximum number of retry attempts

        Returns:
            Dict[str, Any]: LLM response

        Raises:
            LLMError: If all retries fail or if no LLM service is available
        """
        # Require LLM service
        if self.agent.llm_service is None:
            raise LLMError("No LLM service available. Please provide llm_service when creating the agent.")
        
        for attempt in range(max_retries):
            try:
                kwargs = {
                    "messages": [{"role": "user", "content": prompt}],
                }
                if format:
                    kwargs["format"] = format

                # Use agent's LLM service
                res = self.agent.llm_service.chat(model=self.model, **kwargs)
                
                return res  # type: ignore[no-any-return]

            except Exception as e:
                if attempt == max_retries - 1:
                    raise LLMError(f"LLM call failed after {max_retries} attempts: {e}") from e
                # Exponential backoff (capped at 30 seconds)
                wait_time = min(2**attempt, 30)
                print(
                    f"LLM call failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

        # Should never reach here due to raise in loop
        raise LLMError("All retries exhausted")

    def absorb(self, text: str, author: str = "User") -> None:
        """
        Learn from incoming text by extracting and storing knowledge triplets.

        Dispatches to either fast mode (GLiNER + TextBlob) or LLM mode
        based on configuration.

        Args:
            text (str): Input text to learn from
            author (str): Name of the text author

        Returns:
            None
        """
        # Extract triplets using configured extractor
        data = self.extractor.extract(text, author, self.agent.name)

        # Process extracted triplets
        for item in data.get("world_facts", []):
            source = item.get("source", "")
            relation = item.get("relation", "")
            target = item.get("target", "")
            
            # Skip malformed triplets missing required fields
            if not source or not relation or not target:
                print(f"   ! Skipping malformed world_fact triplet: {item}")
                continue
                
            self.agent.learn_triplet(source, relation, target)

        for item in data.get("partner_stance", []):
            source = item.get("source", "")
            relation = item.get("relation", "")
            target = item.get("target", "")
            sentiment = item.get("sentiment", 0.0)
            
            # Skip malformed triplets missing required fields
            if not source or not relation or not target:
                print(f"   ! Skipping malformed partner_stance triplet: {item}")
                continue
                
            self.agent.learn_triplet(source, relation, target, sentiment=sentiment)

        for item in data.get("my_reaction", []):
            relation = item.get("relation", "")
            target = item.get("target", "")
            s_score = item.get("sentiment", 0.0)
            rating = item.get("rating", Rating.Good)
            
            # Skip malformed triplets missing required fields
            if not relation or not target:
                print(f"   ! Skipping malformed my_reaction triplet: {item}")
                continue
                
            self.agent.learn_triplet(
                "I",
                relation,
                target,
                rating=rating,
                sentiment=s_score,
            )

        # Log the interaction
        self.agent.db.log_interaction(
            self.agent.name, "READ", text, data, timestamp=self.agent.current_time
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
            text (str): Agent's own statement to reflect on

        Returns:
            None

        Raises:
            LLMError: If LLM call fails after retries
            ExtractionError: If JSON parsing fails
        """
        print(f"   > [Self-Reflection] Analyzing my own words...")

        prompt = f"""
        You are {self.agent.name}. You just said: "{text}"
        Task: Extract the beliefs/stances YOU just expressed.
        CRITICAL: Relations must be active verbs (e.g. "support", "oppose", "fear"), NOT grammatical labels.

        Return JSON: {{ "my_expressed_stances": [ {{"relation": "verb", "target": "Entity", "sentiment": 0.5}} ] }}
        """

        try:
            res = self._call_llm_with_retry(prompt, format="json")

            try:
                data = json.loads(res["message"]["content"])
            except json.JSONDecodeError as e:
                raise ExtractionError(f"Invalid JSON in reflection response: {e}") from e

            count = 0
            for item in data.get("my_expressed_stances", []):
                relation = item.get("relation", "")
                target = item.get("target", "")
                s_score = item.get("sentiment", 0.0)
                
                # Skip malformed triplets missing required fields
                if not relation or not target:
                    print(f"   ! Skipping malformed stance triplet: {item}")
                    continue
                    
                self.agent.learn_triplet(
                    "I",
                    relation,
                    target,
                    rating=Rating.Easy,  # High rating for self-expressed beliefs
                    sentiment=s_score,
                )
                count += 1
            print(f"   > [Self-Reflection] Reinforced {count} beliefs.")

        except (LLMError, ExtractionError) as e:
            print(f"Error reflecting: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error reflecting: {e}")

    def reply(self, topic: str, partner_name: str) -> str:
        """
        Generate a reply about a topic based on agent's memory.

        Retrieves relevant context from memory and uses LLM to generate
        a response. Also reflects on the generated response to reinforce
        expressed beliefs.

        Args:
            topic (str): Topic to reply about
            partner_name (str): Name of conversation partner

        Returns:
            str: Generated reply text, or empty string if generation fails

        Raises:
            LLMError: If LLM call fails after retries
        """
        context = self.agent.get_memory_view(topic)

        prompt = f"""
        You are {self.agent.name}. Talking to {partner_name} about {topic}.
        YOUR MEMORY: {context}
        Task: Write a short 1-sentence reply. Prioritize YOUR STANCE.
        """

        try:
            res = self._call_llm_with_retry(prompt)
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

            return content  # type: ignore[no-any-return]

        except LLMError as e:
            print(f"Error replying: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error replying: {e}")
            return ""  # Return empty string instead of None for consistency
