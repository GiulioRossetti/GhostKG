"""
Triplet Extraction Module

This module provides different strategies for extracting knowledge triplets from text:
- Fast mode: GLiNER (entity extraction) + TextBlob (sentiment analysis)
- LLM mode: Deep semantic extraction using language models

The module includes thread-safe model caching to avoid reloading models.
"""

import json
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

# Optional dependencies for fast mode
try:
    from gliner import GLiNER
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    HAS_FAST_MODE = True
except ImportError:
    GLiNER = None
    SentimentIntensityAnalyzer = None
    HAS_FAST_MODE = False


class ModelCache:
    """
    Thread-safe cache for GLiNER model.

    Prevents multiple loads of the same model and ensures thread safety.
    """

    _lock = threading.Lock()
    _model = None

    @classmethod
    def get_gliner_model(cls) -> Optional[Any]:
        """
        Get or load GLiNER model (thread-safe).

        Returns:
            Optional[Any]: GLiNER model instance or None if unavailable
        """
        if not HAS_FAST_MODE:
            return None

        if cls._model is None:
            with cls._lock:
                # Double-check pattern
                if cls._model is None:
                    print("⚡ [Fast Mode] Loading GLiNER model...")
                    cls._model = GLiNER.from_pretrained("urchade/gliner_small-v2.1")
        return cls._model


class TripletExtractor(ABC):
    """Abstract base class for triplet extraction strategies."""

    @abstractmethod
    def extract(self, text: str, author: str, agent_name: str) -> Dict[str, Any]:
        """
        Extract triplets from text.

        Args:
            text (str): Input text to analyze
            author (str): Author of the text
            agent_name (str): Name of the agent doing the extraction

        Returns:
            Dict[str, Any]: Dictionary with extraction results and metadata
        """
        pass


class FastExtractor(TripletExtractor):
    """
    Fast triplet extraction using GLiNER + VADER.

    Uses:
    - GLiNER for entity recognition (Topics, People, Concepts, Organizations)
    - VADER for sentiment analysis (better for social/conversational text)
    - Entity-level sentiment analysis (sentiment per entity, not just overall)
    - Heuristic relation mapping based on sentiment with intensity awareness

    This is faster than LLM but more semantically aware than simple TextBlob.
    """

    def __init__(self) -> None:
        """
        Initialize fast extractor and preload models.

        Raises:
            ImportError: If required dependencies are not installed
        """
        if not HAS_FAST_MODE:
            raise ImportError(
                "Fast mode requires 'gliner' and 'vaderSentiment'. "
                "Install with: pip install gliner vaderSentiment"
            )
        self.model = ModelCache.get_gliner_model()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()  # type: ignore[misc]

    def extract(self, text: str, author: str, agent_name: str) -> Dict[str, Any]:
        """
        Extract triplets using fast heuristic approach with entity-level sentiment.

        Args:
            text (str): Input text
            author (str): Text author
            agent_name (str): Agent performing extraction

        Returns:
            Dict[str, Any]: Dict with world_facts, partner_stance, my_reaction, and metadata
        """
        print(f"\n[{agent_name}] reading {author} (FAST): '{text[:40]}...'")

        # 1. Extract Entities (Nodes)
        labels = ["Topic", "Person", "Concept", "Organization"]
        entities = self.model.predict_entities(text, labels)  # type: ignore[union-attr]

        # 2. Extract Overall Sentiment using VADER
        sentiment_scores = self.sentiment_analyzer.polarity_scores(text)  # type: ignore[union-attr]
        overall_sentiment = sentiment_scores["compound"]  # -1.0 to 1.0 (compound score)
        # Clamp overall_sentiment to valid range to handle any edge cases
        overall_sentiment = max(-1.0, min(1.0, overall_sentiment))
        sentiment_intensity = max(abs(sentiment_scores["pos"]), abs(sentiment_scores["neg"]))

        # 3. Build triplets with entity-specific sentiment
        world_facts = []
        partner_stance = []
        my_reaction = []

        for entity in entities:
            topic_text = entity["text"]
            if len(topic_text) < 3:
                continue

            # Extract entity-specific sentiment by analyzing context around entity
            entity_context = self._extract_entity_context(text, topic_text)
            entity_sentiment_scores = self.sentiment_analyzer.polarity_scores(entity_context)  # type: ignore[union-attr]
            entity_sentiment = entity_sentiment_scores["compound"]
            # Clamp entity_sentiment to valid range to handle any edge cases
            entity_sentiment = max(-1.0, min(1.0, entity_sentiment))

            # Use entity-specific sentiment if significantly different from overall
            sentiment_for_entity = (
                entity_sentiment
                if abs(entity_sentiment - overall_sentiment) > 0.2
                else overall_sentiment
            )

            # Determine Relation Verb based on Sentiment with intensity awareness
            relation = self._determine_relation(sentiment_for_entity, sentiment_intensity)

            # A. Partner Stance: Author -> Relation -> Topic
            partner_stance.append(
                {
                    "source": author,
                    "relation": relation,
                    "target": topic_text,
                    "sentiment": sentiment_for_entity,
                    "sentiment_intensity": sentiment_intensity,
                }
            )

            # B. World Fact: Topic -> is -> discussed
            world_facts.append({"source": topic_text, "relation": "is", "target": "discussed"})

            # C. My Reaction: I -> heard about -> Topic
            # Agent's reaction should reflect understanding of sentiment
            my_relation = (
                "heard about"
                if abs(sentiment_for_entity) < 0.1
                else ("interested in" if sentiment_for_entity > 0 else "concerned about")
            )
            my_reaction.append(
                {
                    "source": "I",
                    "relation": my_relation,
                    "target": topic_text,
                    "rating": 3,  # Good rating
                    "sentiment": max(-1.0, min(1.0, sentiment_for_entity * 0.5)),  # Dampened sentiment for observation, clamped to valid range
                }
            )

        result = {
            "world_facts": world_facts,
            "partner_stance": partner_stance,
            "my_reaction": my_reaction,
            "mode": "FAST",
            "sentiment": overall_sentiment,
            "sentiment_breakdown": {
                "positive": sentiment_scores["pos"],
                "negative": sentiment_scores["neg"],
                "neutral": sentiment_scores["neu"],
                "compound": sentiment_scores["compound"],
            },
            "entities": [e["text"] for e in entities],
        }

        print(
            f"   > Fast absorbed {len(entities)} entities "
            f"(sentiment: {overall_sentiment:.2f}, pos: {sentiment_scores['pos']:.2f}, "
            f"neg: {sentiment_scores['neg']:.2f})"
        )
        return result

    def _extract_entity_context(self, text: str, entity: str, window: int = 50) -> str:
        """
        Extract context around an entity for entity-specific sentiment analysis.

        Args:
            text (str): Full text
            entity (str): Entity to find context for
            window (int): Character window on each side of entity

        Returns:
            str: Context around entity, or full text if entity not found
        """
        entity_lower = entity.lower()
        text_lower = text.lower()

        pos = text_lower.find(entity_lower)
        if pos == -1:
            return text  # Entity not found, use full text

        start = max(0, pos - window)
        end = min(len(text), pos + len(entity) + window)
        return text[start:end]

    def _determine_relation(self, sentiment: float, intensity: float) -> str:
        """
        Determine relation verb based on sentiment and intensity.

        Args:
            sentiment (float): Sentiment score (-1.0 to 1.0)
            intensity (float): Sentiment intensity (0.0 to 1.0)

        Returns:
            str: Relation verb that captures sentiment and intensity
        """
        # High intensity: stronger verbs
        if intensity > 0.5:
            if sentiment > 0.5:
                return "strongly supports"
            elif sentiment > 0.2:
                return "advocates"
            elif sentiment < -0.5:
                return "strongly opposes"
            elif sentiment < -0.2:
                return "criticizes"

        # Medium intensity: standard verbs
        if sentiment > 0.3:
            return "supports"
        elif sentiment > 0.1:
            return "likes"
        elif sentiment < -0.3:
            return "opposes"
        elif sentiment < -0.1:
            return "dislikes"

        # Low/neutral sentiment
        return "discusses"


class LLMExtractor(TripletExtractor):
    """
    Deep semantic triplet extraction using LLM.

    Uses language model to perform deep semantic analysis and extract:
    - World facts (objective SVO triplets)
    - Partner stance (what the author believes)
    - Agent's reaction (agent's opinion)

    This is slower but more semantically accurate than fast mode.
    """

    def __init__(self, client: Any, model: str = "llama3.2") -> None:
        """
        Initialize LLM extractor.

        Args:
            client (Any): Ollama client instance
            model (str): Model name to use for extraction

        Returns:
            None
        """
        self.client = client
        self.model = model

    def extract(self, text: str, author: str, agent_name: str) -> Dict[str, Any]:
        """
        Extract triplets using LLM semantic analysis.

        Args:
            text (str): Input text
            author (str): Text author
            agent_name (str): Agent performing extraction

        Returns:
            Dict[str, Any]: Dict with world_facts, partner_stance, my_reaction
        """
        print(f"\n[{agent_name}] reading {author}: '{text[:40]}...'")

        prompt = f"""
        You are {agent_name}. Analyze this text by {author}: "{text}"

        Goal: Build a Semantic Knowledge Graph.

        CRITICAL INSTRUCTIONS:
        1. EXTRACT MEANING, NOT GRAMMAR. 
           - BAD:  "Bob" -> "noun" -> "UBI"
           - BAD:  "Text" -> "adverb" -> "strongly"
           - GOOD: "Bob" -> "supports" -> "UBI"
           - GOOD: "UBI" -> "reduces" -> "poverty"

        2. World Facts: Objective SVO triplets.
        3. Partner Stance: What {author} explicitly believes.
        4. Your Reaction: Your opinion (Source MUST be "I").

        Return JSON:
        {{
            "world_facts":    [{{"source": "Concept", "relation": "active_verb", "target": "Concept"}}],
            "partner_stance": [{{"source": "{author}", "relation": "active_verb", "target": "Concept"}}],
            "my_reaction":    [{{"source": "I", "relation": "active_verb", "target": "Concept", "rating": 3, "sentiment": 0.0}}] 
        }}
        """

        try:
            res = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
            )
            data = json.loads(res["message"]["content"])
            print(f"   > LLM extracted triplets successfully")
            return data  # type: ignore[no-any-return]

        except Exception as e:
            print(f"   ! LLM extraction failed: {e}")
            return {"world_facts": [], "partner_stance": [], "my_reaction": []}


def get_extractor(
    fast_mode: bool, client: Optional[Any] = None, model: str = "llama3.2"
) -> TripletExtractor:
    """
    Factory function to get appropriate extractor.

    Args:
        fast_mode (bool): If True, use fast extractor; otherwise use LLM
        client (Optional[Any]): Ollama client (required for LLM mode)
        model (str): Model name (for LLM mode)

    Returns:
        TripletExtractor: TripletExtractor instance

    Raises:
        ImportError: If fast mode requested but dependencies not available
        ValueError: If LLM mode requested but no client provided
    """
    if fast_mode:
        if not HAS_FAST_MODE:
            raise ImportError(
                "Fast mode requires 'gliner' and 'textblob'. "
                "Install with: pip install gliner textblob"
            )
        return FastExtractor()
    else:
        if client is None:
            raise ValueError("LLM mode requires an Ollama client")
        return LLMExtractor(client, model)
