"""
Triplet Extraction Module

This module provides different strategies for extracting knowledge triplets from text:
- Fast mode: GLiNER (entity extraction) + TextBlob (sentiment analysis)
- LLM mode: Deep semantic extraction using language models

The module includes thread-safe model caching to avoid reloading models.
"""

import json
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import threading

# Optional dependencies for fast mode
try:
    from gliner import GLiNER
    from textblob import TextBlob
    HAS_FAST_MODE = True
except ImportError:
    GLiNER = None
    TextBlob = None
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
    Fast triplet extraction using GLiNER + TextBlob.
    
    Uses:
    - GLiNER for entity recognition (Topics, People, Concepts, Organizations)
    - TextBlob for sentiment analysis
    - Heuristic relation mapping based on sentiment
    
    This is faster than LLM but less semantically rich.
    """
    
    def __init__(self) -> None:
        """
        Initialize fast extractor and preload model.
        
        Raises:
            ImportError: If required dependencies are not installed
        """
        if not HAS_FAST_MODE:
            raise ImportError(
                "Fast mode requires 'gliner' and 'textblob'. "
                "Install with: pip install gliner textblob"
            )
        self.model = ModelCache.get_gliner_model()
    
    def extract(self, text: str, author: str, agent_name: str) -> Dict[str, Any]:
        """
        Extract triplets using fast heuristic approach.
        
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
        
        # 2. Extract Sentiment (Edge Coloring)
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity  # -1.0 to 1.0
        
        # 3. Determine Relation Verb based on Sentiment
        relation = "discusses"
        if sentiment > 0.3:
            relation = "supports"
        elif sentiment < -0.3:
            relation = "opposes"
        elif sentiment > 0.1:
            relation = "likes"
        elif sentiment < -0.1:
            relation = "dislikes"
        
        # 4. Build triplets
        world_facts = []
        partner_stance = []
        my_reaction = []
        
        for entity in entities:
            topic_text = entity["text"]
            if len(topic_text) < 3:
                continue
            
            # A. Partner Stance: Author -> Relation -> Topic
            partner_stance.append({
                "source": author,
                "relation": relation,
                "target": topic_text,
                "sentiment": sentiment
            })
            
            # B. World Fact: Topic -> is -> discussed
            world_facts.append({
                "source": topic_text,
                "relation": "is",
                "target": "discussed"
            })
            
            # C. My Reaction: I -> heard about -> Topic
            my_reaction.append({
                "source": "I",
                "relation": "heard about",
                "target": topic_text,
                "rating": 3,  # Good rating
                "sentiment": 0.0
            })
        
        result = {
            "world_facts": world_facts,
            "partner_stance": partner_stance,
            "my_reaction": my_reaction,
            "mode": "FAST",
            "sentiment": sentiment,
            "entities": [e["text"] for e in entities]
        }
        
        print(f"   > Fast absorbed {len(entities)} entities with sentiment {sentiment:.2f}")
        return result


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
            return {
                "world_facts": [],
                "partner_stance": [],
                "my_reaction": []
            }


def get_extractor(fast_mode: bool, client: Optional[Any] = None, model: str = "llama3.2") -> TripletExtractor:
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
