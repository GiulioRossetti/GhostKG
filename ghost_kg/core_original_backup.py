"""
DEPRECATED: This module has been refactored into multiple focused modules.

For backward compatibility, this module re-exports all classes from the new modules.
New code should import from the specific modules:
- ghost_kg.fsrs: FSRS, Rating
- ghost_kg.agent: GhostAgent
- ghost_kg.cognitive: CognitiveLoop
- ghost_kg.extraction: FastExtractor, LLMExtractor

Old imports will continue to work:
    from ghost_kg.core import GhostAgent, CognitiveLoop, Rating, FSRS
"""

from .agent import GhostAgent
from .cognitive import CognitiveLoop

# Re-export from new modules for backward compatibility
from .fsrs import FSRS, Rating

__all__ = ["FSRS", "Rating", "GhostAgent", "CognitiveLoop"]

# Keep original implementation for reference, but mark as deprecated
# If you see this code being executed, update your imports!

import datetime
import json
import math
import re
import warnings

from ollama import Client

from .storage import KnowledgeDB, NodeState

# Show deprecation warning when this module is imported directly
warnings.warn(
    "Importing from ghost_kg.core is deprecated. "
    "Please import from specific modules: "
    "ghost_kg.fsrs, ghost_kg.agent, ghost_kg.cognitive, ghost_kg.extraction",
    DeprecationWarning,
    stacklevel=2,
)

# --- LEGACY CODE BELOW (for reference) ---
# This code is kept for backward compatibility but should not be used in new code.

# --- FAST MODE IMPORTS ---
try:
    from gliner import GLiNER
    from textblob import TextBlob

    GLINER_MODEL = None  # Global cache to prevent reloading
except ImportError:
    GLiNER = None
    TextBlob = None


# --- 1. FSRS Logic (Standard v4.5) ---
class _LegacyRating:
    Again = 1
    Hard = 2
    Good = 3
    Easy = 4


class _LegacyFSRS:
    def __init__(self):
        self.p = [
            0.4,
            0.6,
            2.4,
            5.8,
            4.93,
            0.94,
            0.86,
            0.01,
            1.49,
            0.14,
            0.94,
            2.18,
            0.05,
            0.34,
            1.26,
            0.29,
            2.61,
        ]

    def calculate_next(self, current_state: NodeState, rating, now):
        # 1. New Cards
        if current_state.state == 0:
            s = self.p[rating - 1]
            d = min(max(self.p[4] - (rating - 3) * self.p[5], 1), 10)
            return NodeState(s, d, now, 1, 1)

        # 2. Existing Cards
        s = current_state.stability
        d = current_state.difficulty

        if current_state.last_review:
            last_review = current_state.last_review
            if last_review.tzinfo is None:
                last_review = last_review.replace(tzinfo=datetime.timezone.utc)
            elapsed_days = (now - last_review).total_seconds() / 86400
            if elapsed_days < 0:
                elapsed_days = 0
            retrievability = (1 + elapsed_days / (9 * s)) ** -1
        else:
            retrievability = 1.0

        next_d = min(
            max(
                self.p[7] * self.p[4] + (1 - self.p[7]) * (d - self.p[6] * (rating - 3)),
                1,
            ),
            10,
        )

        if rating == Rating.Again:
            next_s = (
                self.p[11]
                * (next_d ** -self.p[12])
                * ((s + 1) ** self.p[13] - 1)
                * math.exp((1 - retrievability) * self.p[14])
            )
            state = 1
        else:
            hard_penalty = self.p[15] if rating == Rating.Hard else 1
            easy_bonus = self.p[16] if rating == Rating.Easy else 1
            next_s = s * (
                1
                + math.exp(self.p[8])
                * (11 - next_d)
                * (s ** -self.p[9])
                * (math.exp((1 - retrievability) * self.p[10]) - 1)
                * hard_penalty
                * easy_bonus
            )
            state = 2

        next_s = max(next_s, 0.1)
        return NodeState(next_s, next_d, now, current_state.reps + 1, state)


# --- 2. Ghost Agent (Time-Aware & Hardened) ---


class GhostAgent:
    def __init__(self, name, db_path="agent_memory.db", llm_host="http://localhost:11434"):
        self.name = name
        self.db = KnowledgeDB(db_path)
        self.fsrs = FSRS()
        self.client = Client(host=llm_host)

        # Simulation Clock
        self.current_time = datetime.datetime.now(datetime.timezone.utc)
        self.db.upsert_node(self.name, "I", timestamp=self.current_time)

    def set_time(self, new_time):
        """Updates internal clock for simulation steps."""
        if new_time.tzinfo is None:
            new_time = new_time.replace(tzinfo=datetime.timezone.utc)
        self.current_time = new_time

    def _normalize(self, text):
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

    def _is_valid_triple(self, src, rel, tgt):
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

    def update_memory(self, concept_name, rating):
        norm_name = self._normalize(concept_name)
        if not norm_name:
            return

        row = self.db.get_node(self.name, norm_name)
        if row and row["last_review"]:
            last_review = row["last_review"]
            if isinstance(last_review, str):
                try:
                    last_review = datetime.datetime.fromisoformat(last_review)
                except:
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

    def learn_triplet(self, source, relation, target, rating=Rating.Good, sentiment=0.0):
        n_source = self._normalize(source)
        n_target = self._normalize(target)
        n_relation = self._normalize(relation)

        if not self._is_valid_triple(n_source, n_relation, n_target):
            return  # Silent rejection of garbage

        self.update_memory(n_target, rating)
        if n_source != "I":
            self.update_memory(n_source, Rating.Good)

        self.db.add_relation(
            self.name,
            n_source,
            n_relation,
            n_target,
            sentiment=sentiment,
            timestamp=self.current_time,
        )

    def _get_retrievability(self, stability, last_review):
        if not last_review or stability == 0:
            return 0.0
        elapsed_days = (self.current_time - last_review).days
        if elapsed_days < 0:
            elapsed_days = 0
        return (1 + elapsed_days / (9 * stability)) ** -1

    def get_memory_view(self, topic):
        n_topic = self._normalize(topic)
        if not n_topic:
            return "(I am confused)"

        row = self.db.get_node(self.name, n_topic)
        if row:
            lr = row["last_review"]
            if isinstance(lr, str):
                try:
                    lr = datetime.datetime.fromisoformat(lr)
                except:
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


# --- 3. Cognitive Loop (Strict Semantic Extraction) ---


class CognitiveLoop:
    def __init__(self, agent: GhostAgent, model="llama3.2", fast_mode=False):
        self.agent = agent
        self.model = model
        self.fast_mode = fast_mode

        # Preload GLiNER if fast mode is enabled and available
        if self.fast_mode and GLiNER:
            global GLINER_MODEL
            if GLINER_MODEL is None:
                print("⚡ [Fast Mode] Loading GLiNER model...")
                GLINER_MODEL = GLiNER.from_pretrained("urchade/gliner_small-v2.1")

    def absorb(self, text, author="User"):
        """
        Main entry point for learning.
        Dispatches to fast mode (GLiNER) or semantic mode (LLM) based on config.
        """
        if self.fast_mode and GLiNER:
            self._absorb_fast(text, author)
        else:
            self._absorb_llm(text, author)

    def _absorb_fast(self, text, author):
        """High-speed heuristic extraction using GLiNER + TextBlob."""
        print(f"\n[{self.agent.name}] reading {author} (FAST): '{text[:40]}...'")

        # 1. Extract Entities (Nodes)
        labels = ["Topic", "Person", "Concept", "Organization"]
        entities = GLINER_MODEL.predict_entities(text, labels)

        # 2. Extract Sentiment (Edge Coloring)
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity  # -1.0 to 1.0

        # Determine Relation Verb based on Sentiment
        relation = "discusses"
        if sentiment > 0.3:
            relation = "supports"
        elif sentiment < -0.3:
            relation = "opposes"
        elif sentiment > 0.1:
            relation = "likes"
        elif sentiment < -0.1:
            relation = "dislikes"

        fact_count = 0

        for entity in entities:
            topic_text = entity["text"]
            if len(topic_text) < 3:
                continue

            # A. Partner Stance: Author -> Relation -> Topic
            # e.g. "Bob" -> "supports" -> "UBI"
            self.agent.learn_triplet(
                source=author,
                relation=relation,
                target=topic_text,
                rating=Rating.Good,  # Standard retention
                sentiment=sentiment,
            )

            # B. World Fact (Simple Existence): Topic -> is -> mentioned
            # Useful so the agent knows this concept exists in the world
            self.agent.learn_triplet(
                source=topic_text,
                relation="is",
                target="discussed",
                rating=Rating.Good,
                sentiment=0.0,
            )

            # C. My Reaction (Passive Hearing): I -> heard -> Topic
            # In fast mode, we don't generate deep thoughts, but we record we heard it.
            self.agent.learn_triplet(
                source="I",
                relation="heard about",
                target=topic_text,
                rating=Rating.Good,  # Good = standard retention
                sentiment=0.0,
            )

            fact_count += 1

        # Log interaction for visualization
        log_data = {
            "mode": "FAST",
            "sentiment": sentiment,
            "entities": [e["text"] for e in entities],
        }
        self.agent.db.log_interaction(
            self.agent.name, "READ", text, log_data, timestamp=self.agent.current_time
        )
        print(f"   > Fast absorbed {fact_count} entities with sentiment {sentiment:.2f}")

    def _absorb_llm(self, text, author):
        """Deep semantic extraction using LLM (Original Logic)."""
        print(f"\n[{self.agent.name}] reading {author}: '{text[:40]}...'")

        prompt = f"""
        You are {self.agent.name}. Analyze this text by {author}: "{text}"

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
            res = self.agent.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
            )
            data = json.loads(res["message"]["content"])

            for item in data.get("world_facts", []):
                self.agent.learn_triplet(item["source"], item["relation"], item["target"])

            for item in data.get("partner_stance", []):
                self.agent.learn_triplet(item["source"], item["relation"], item["target"])

            for item in data.get("my_reaction", []):
                s_score = item.get("sentiment", 0.0)
                self.agent.learn_triplet(
                    "I",
                    item["relation"],
                    item["target"],
                    rating=Rating.Good,
                    sentiment=s_score,
                )

            self.agent.db.log_interaction(
                self.agent.name, "READ", text, data, timestamp=self.agent.current_time
            )
            print(
                f"   > Internalized {len(data.get('world_facts', []))} facts & formed {len(data.get('my_reaction', []))} opinions."
            )

        except Exception as e:
            print(f"Error absorbing: {e}")

    def reflect(self, text):
        # Reflection usually requires self-awareness, so we stick to LLM here
        # unless we want a very simple keyword extractor.
        # For now, we use the LLM to ensure high-quality self-consistency.
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
                    rating=Rating.Easy,
                    sentiment=s_score,
                )
                count += 1
            print(f"   > [Self-Reflection] Reinforced {count} beliefs.")

        except Exception as e:
            print(f"Error reflecting: {e}")

    def reply(self, topic, partner_name):
        context = self.agent.get_memory_view(topic)
        prompt = f"""
        You are {self.agent.name}. Talking to {partner_name} about {topic}.
        YOUR MEMORY: {context}
        Task: Write a short 1-sentence reply. Prioritize YOUR STANCE.
        """
        try:
            res = self.agent.client.chat(
                model=self.model, messages=[{"role": "user", "content": prompt}]
            )
            content = res["message"]["content"]

            self.agent.db.log_interaction(
                self.agent.name,
                "WRITE",
                content,
                {"context_used": context},
                timestamp=self.agent.current_time,
            )
            print(
                f"   > {self.agent.name} ({self.agent.current_time.strftime('%H:%M')}): {content}"
            )

            # We always reflect using LLM to ensure we lock in our own generated stance
            self.reflect(content)
            return content
        except Exception as e:
            print(f"Error replying: {e}")
            return "..."
