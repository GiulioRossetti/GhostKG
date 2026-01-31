"""
GhostAgent - Autonomous Knowledge Agent

This module implements the GhostAgent class, which represents an autonomous agent
with its own knowledge graph, memory system, and learning capabilities.

Each agent maintains:
- Personal knowledge graph with triplets (source, relation, target)
- Memory strength tracking via FSRS algorithm
- Temporal awareness with simulation clock
- Belief and opinion management
"""

import datetime
import re
from typing import Any, Optional

try:
    from ollama import Client

    HAS_OLLAMA = True
except ImportError:
    Client = None
    HAS_OLLAMA = False

from .fsrs import FSRS, Rating
from .storage import KnowledgeDB, NodeState


class GhostAgent:
    """
    Autonomous knowledge agent with memory and learning capabilities.

    Each agent has:
    - Unique name/identity
    - Personal knowledge graph (stored in database)
    - Memory system (FSRS-based strength tracking)
    - Temporal awareness (simulation clock)
    - LLM client for text generation

    Attributes:
        name (str): Agent's unique identifier
        db (KnowledgeDB): Database connection for knowledge storage
        fsrs (FSRS): Memory scheduler for tracking concept strength
        client (Client): Ollama LLM client for generation
        current_time (datetime): Simulation clock for temporal tracking

    Methods:
        set_time: Update simulation clock
        learn_triplet: Add new knowledge triplet to graph
        update_memory: Update memory strength of a concept
        get_memory_view: Retrieve agent's knowledge about a topic
    """

    def __init__(
        self, name: str, db_path: str = "agent_memory.db", llm_host: str = "http://localhost:11434"
    ) -> None:
        """
        Initialize a new GhostAgent.

        Args:
            name (str): Unique identifier for the agent
            db_path (str): Path to SQLite database file
            llm_host (str): URL for Ollama LLM server

        Returns:
            None
        """
        self.name = name
        self.db = KnowledgeDB(db_path)
        self.fsrs = FSRS()

        # Initialize ollama client if available
        if HAS_OLLAMA:
            self.client = Client(host=llm_host)
        else:
            self.client = None

        # Simulation Clock
        self.current_time = datetime.datetime.now(datetime.timezone.utc)
        self.db.upsert_node(self.name, "I", timestamp=self.current_time)

    def set_time(self, new_time: datetime.datetime) -> None:
        """
        Update the agent's simulation clock.

        Args:
            new_time (datetime.datetime): New timestamp for the simulation clock

        Returns:
            None
        """
        if new_time.tzinfo is None:
            new_time = new_time.replace(tzinfo=datetime.timezone.utc)
        self.current_time = new_time

    def _normalize(self, text: Optional[str]) -> Optional[str]:
        """
        Normalize text for consistent knowledge graph representation.

        Handles:
        - Lowercasing and whitespace trimming
        - Special case for "I" (self-reference)
        - Agent name mapping to "I"
        - Pronouns (me, myself) mapping to "I"

        Args:
            text (Optional[str]): Raw text to normalize

        Returns:
            Optional[str]: Normalized text or None if invalid
        """
        if not text:
            return None
        clean = text.strip().lower()
        clean = re.sub(r"[^a-z0-9\s]", "", clean)

        # Handle explicit self-references
        if clean == "i":
            return "I"
        if clean == self.name.lower():
            return "I"
        if clean in ["me", "myself"]:
            return "I"

        return clean

    def _is_valid_triple(self, src: str, rel: str, tgt: str) -> bool:
        """
        Validate a knowledge triplet before adding to graph.

        Filters out:
        - Stopwords and garbage
        - Grammatical/meta terms (noun, verb, adjective, etc.)
        - Generic/meaningless nodes
        - Too-short terms

        Args:
            src (str): Source node (normalized)
            rel (str): Relation (normalized)
            tgt (str): Target node (normalized)

        Returns:
            bool: True if triplet is semantically meaningful
        """
        # 1. Stopwords / Garbage
        stopwords = {"it", "is", "the", "a", "an", "this", "that"}

        # 2. BANNED GRAMMATICAL TERMS (Semantic Gatekeeper)
        banned_relations = {
            "noun",
            "verb",
            "adjective",
            "adverb",
            "preposition",
            "conjunction",
            "pronoun",
            "phrase",
            "clause",
            "sentence",
            "statement",
            "text",
            "topic",
            "concept",
            "word",
            "term",
            "rating",
            "evaluation",
            "opinion",
        }

        # 3. BANNED GENERIC NODES
        banned_nodes = {
            "text",
            "entity",
            "author",
            "none",
            "unknown",
            "wikipedia",
            "general knowledge",
            "source",
            "target",
            "adjective",
            "noun",
        }

        if not src or not rel or not tgt:
            return False

        # Length & Content checks
        if len(src) < 2 and src != "I":
            return False
        if len(tgt) < 2 and tgt != "I":
            return False

        if src in stopwords or tgt in stopwords:
            return False
        if src in banned_nodes or tgt in banned_nodes:
            return False
        if rel in banned_relations:
            return False

        return True

    def update_memory(self, concept_name: str, rating: int) -> None:
        """
        Update the memory strength of a concept using FSRS.

        Args:
            concept_name (str): Name of the concept to update
            rating (int): Review rating (1=Again, 2=Hard, 3=Good, 4=Easy)

        Returns:
            None
        """
        norm_name = self._normalize(concept_name)
        if not norm_name:
            return

        row = self.db.get_node(self.name, norm_name)
        if row and row["last_review"]:
            last_review = row["last_review"]
            if isinstance(last_review, str):
                try:
                    last_review = datetime.datetime.fromisoformat(last_review)
                except (ValueError, TypeError):
                    last_review = self.current_time
            if last_review.tzinfo is None:
                last_review = last_review.replace(tzinfo=datetime.timezone.utc)
            current = NodeState(
                row["stability"],
                row["difficulty"],
                last_review,
                row["reps"],
                row["state"],
            )
        else:
            current = NodeState(0, 0, None, 0, 0)

        # Use Simulation Time
        new_state = self.fsrs.calculate_next(current, rating, self.current_time)
        self.db.upsert_node(self.name, norm_name, new_state, timestamp=self.current_time)

    def learn_triplet(
        self,
        source: str,
        relation: str,
        target: str,
        rating: Optional[int] = None,
        sentiment: float = 0.0,
    ) -> None:
        """
        Add a knowledge triplet to the agent's knowledge graph.

        The triplet represents a semantic relationship: subject-relation-object.
        Memory strength is tracked using FSRS algorithm, and sentiment captures
        emotional valence.

        Args:
            source (str): Subject entity (e.g., "I", "Bob", "climate")
            relation (str): Relationship verb (e.g., "supports", "opposes", "mentions")
            target (str): Object entity (e.g., "UBI", "economy", "action")
            rating (Optional[int]): Memory strength rating (1-4). Use Rating.Again/Hard/Good/Easy
            sentiment (float): Emotional valence from -1.0 (negative) to 1.0 (positive)

        Returns:
            None

        Example:
            >>> agent = GhostAgent("Alice")
            >>> # Positive belief
            >>> agent.learn_triplet("I", "support", "climate_action",
            ...                     rating=Rating.Good, sentiment=0.8)
            >>> # Negative opinion
            >>> agent.learn_triplet("I", "oppose", "fossil_fuels",
            ...                     rating=Rating.Easy, sentiment=-0.7)
            >>> # Neutral fact
            >>> agent.learn_triplet("Bob", "mentioned", "economics",
            ...                     rating=Rating.Good, sentiment=0.0)

        See Also:
            - update_memory(): Update memory strength of existing concept
            - get_memory_view(): Retrieve agent's knowledge about a topic
        """
        if rating is None:
            rating = Rating.Good

        n_source = self._normalize(source)
        n_target = self._normalize(target)
        n_relation = self._normalize(relation)

        if not self._is_valid_triple(n_source, n_relation, n_target):  # type: ignore[arg-type]
            return  # Silent rejection of garbage

        self.update_memory(n_target, rating)  # type: ignore[arg-type]
        if n_source != "I":
            self.update_memory(n_source, Rating.Good)  # type: ignore[arg-type]

        self.db.add_relation(
            self.name,
            n_source,  # type: ignore[arg-type]
            n_relation,  # type: ignore[arg-type]
            n_target,  # type: ignore[arg-type]
            sentiment=sentiment,
            timestamp=self.current_time,
        )

    def _get_retrievability(
        self, stability: float, last_review: Optional[datetime.datetime]
    ) -> float:
        """
        Calculate retrievability of a memory based on FSRS formula.

        Args:
            stability (float): Memory stability value
            last_review (Optional[datetime.datetime]): Timestamp of last review

        Returns:
            float: Retrievability score (0.0 to 1.0)
        """
        if not last_review or stability == 0:
            return 0.0
        elapsed_days = (self.current_time - last_review).days
        if elapsed_days < 0:
            elapsed_days = 0
        return (1 + elapsed_days / (9 * stability)) ** -1

    def get_memory_view(self, topic: str) -> str:
        """
        Retrieve agent's knowledge and beliefs about a topic.

        Returns a structured view including:
        - Agent's personal stance/beliefs
        - Known facts from world knowledge
        - What other agents think about the topic

        Args:
            topic (str): Topic to retrieve knowledge about

        Returns:
            str: Formatted string with agent's knowledge view
        """
        n_topic = self._normalize(topic)
        if not n_topic:
            return "(I am confused)"

        row = self.db.get_node(self.name, n_topic)
        if row:
            lr = row["last_review"]
            if isinstance(lr, str):
                try:
                    lr = datetime.datetime.fromisoformat(lr)
                except (ValueError, TypeError):
                    lr = self.current_time
            if lr.tzinfo is None:
                lr = lr.replace(tzinfo=datetime.timezone.utc)

            r = self._get_retrievability(row["stability"], lr)
            if r < 0.2:
                return f"(I have forgotten the details about {topic})"

        # Pass self.current_time to DB for retrieval
        my_rows = self.db.get_agent_stance(self.name, n_topic, current_time=self.current_time)
        world_rows = self.db.get_world_knowledge(self.name, n_topic, limit=8)

        my_beliefs = set()
        world_facts = set()
        others_beliefs = set()

        for row in my_rows:
            my_beliefs.add(f"I {row['relation']} {row['target']}")

        for row in world_rows:
            src, rel, tgt = row["source"], row["relation"], row["target"]
            fact_str = f"{src} {rel} {tgt}"
            if rel in ["said", "thinks", "believes", "wants"]:
                others_beliefs.add(fact_str)
            else:
                world_facts.add(fact_str)

        parts = []
        if my_beliefs:
            parts.append(f"MY CURRENT STANCE: {'; '.join(my_beliefs)}.")
        else:
            parts.append("MY CURRENT STANCE: (I have no strong opinion yet).")

        if world_facts:
            parts.append(f"KNOWN FACTS: {'; '.join(list(world_facts)[:5])}.")
        if others_beliefs:
            parts.append(f"WHAT OTHERS THINK: {'; '.join(list(others_beliefs)[:3])}.")

        return " ".join(parts)
