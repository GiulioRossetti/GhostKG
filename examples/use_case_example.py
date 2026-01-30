"""
Use Case Example - Two Agents Multi-Round Communication

This example demonstrates the specific use case requested:

In the main program:
- Set the current day+hour in ghost_kg
- Agent A reads a tuple (topic, text) describing content from a peer
- A asks ghost_kg to update its KG with (topic, text) and get relevant context
- A uses the context with an external LLM to generate a response
- A passes the generated text to ghost_kg to update its KG

This example shows two agents (Alice and Bob) in multi-round communication.
Uses ollama with llama3.2 for all LLM-related tasks.
"""

import sys
import os
import datetime
import json
from datetime import timedelta
from ollama import Client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghost_kg import AgentManager, Rating

DB_PATH = "use_case_example.db"
LLM_MODEL = "llama3.2"

# Initialize ollama client
ollama_client = Client(host="http://localhost:11434")

# Cleanup
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


def external_llm_generate(agent_name: str, context: str, topic: str, agent_profile: str) -> str:
    """
    Use ollama with llama3.2 to generate a response based on context.
    """
    print(f"  [Ollama LLM] Generating response for {agent_name}...")
    print(f"  [Ollama LLM] Using context: {context[:100]}...")

    prompt = f"""
    You are {agent_name}: a {agent_profile}. Talking about {topic}.
    YOUR MEMORY: {context}
    Task: Write a short 1-sentence reply. Prioritize YOUR STANCE.
    """

    try:
        res = ollama_client.chat(
            model=LLM_MODEL, messages=[{"role": "user", "content": prompt}]
        )
        response = res["message"]["content"]
        return response
    except Exception as e:
        print(f"  Error generating response: {e}")
        # Fallback to simple response
        return f"I have thoughts about {topic}."


def extract_triplets(text: str, author: str):
    """
    Use ollama with llama3.2 to extract triplets from text.
    """
    prompt = f"""
    Analyze this text by {author}: "{text}"

    Goal: Build a Semantic Knowledge Graph.

    CRITICAL INSTRUCTIONS:
    1. EXTRACT MEANING, NOT GRAMMAR.
       - BAD:  "Bob" -> "noun" -> "climate"
       - BAD:  "Text" -> "adverb" -> "strongly"
       - GOOD: "Bob" -> "emphasizes" -> "climate action"
       - GOOD: "climate change" -> "requires" -> "action"

    2. World Facts: Objective SVO triplets.
    3. Partner Stance: What {author} explicitly believes or says.

    Return JSON:
    {{
        "world_facts":    [{{"source": "Concept", "relation": "active_verb", "target": "Concept"}}],
        "partner_stance": [{{"source": "{author}", "relation": "active_verb", "target": "Concept"}}]
    }}
    """

    try:
        res = ollama_client.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json",
        )
        data = json.loads(res["message"]["content"])

        triplets = []

        # Extract world facts
        for item in data.get("world_facts", []):
            triplets.append((item["source"], item["relation"], item["target"]))

        # Extract partner stance
        for item in data.get("partner_stance", []):
            triplets.append((item["source"], item["relation"], item["target"]))

        return triplets
    except Exception as e:
        print(f"  Warning: Error extracting triplets: {e}")
        # Fallback to simple extraction
        return [(author, "says", "something")]


def extract_response_triplets(text: str, agent_name: str):
    """
    Use ollama with llama3.2 to extract triplets from agent's own response.
    Returns list of (relation, target, sentiment) tuples.
    """
    prompt = f"""
    You are {agent_name}. You just said: "{text}"
    Task: Extract the beliefs/stances YOU just expressed.
    CRITICAL: Relations must be active verbs (e.g. "support", "oppose", "fear"), NOT grammatical labels.

    Return JSON: {{ "my_expressed_stances": [ {{"relation": "verb", "target": "Entity", "sentiment": 0.5}} ] }}
    """

    try:
        res = ollama_client.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json",
        )
        data = json.loads(res["message"]["content"])

        triplets = []
        for item in data.get("my_expressed_stances", []):
            s_score = item.get("sentiment", 0.0)
            triplets.append((item["relation"], item["target"], s_score))

        return triplets
    except Exception as e:
        print(f"  Warning: Error extracting response triplets: {e}")
        # Fallback to empty list
        return []


def run_use_case():
    """
    Run the complete use case with two agents and multi-round communication.
    """
    print("=" * 70)
    print("USE CASE: Two Agents Multi-Round Communication")
    print("=" * 70)

    # Initialize the manager
    manager = AgentManager(db_path=DB_PATH)

    # Create two agents
    print("\n📋 Step 1: Create agents")
    alice = manager.create_agent("Alice")
    bob = manager.create_agent("Bob")
    print("  ✓ Created Alice")
    print("  ✓ Created Bob")

    # Set initial time (Day 1, Hour 9)
    print("\n⏰ Step 2: Set initial time")
    current_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
    manager.set_agent_time("Alice", current_time)
    manager.set_agent_time("Bob", current_time)
    print(f"  ✓ Set time to Day 1, 09:00 ({current_time.strftime('%Y-%m-%d %H:%M')})")

    # Initialize agent beliefs
    print("\n📝 Step 3: Initialize agent beliefs")
    manager.learn_triplet(
        "Alice", "I", "care_about", "climate change", rating=Rating.Easy, sentiment=0.9
    )
    manager.learn_triplet(
        "Bob",
        "I",
        "care_about",
        "economic stability",
        rating=Rating.Easy,
        sentiment=0.8,
    )
    print("  ✓ Alice cares about climate change")
    print("  ✓ Bob cares about economic stability")

    # Define the conversation topic
    topic = "climate change"

    # Alice starts the conversation
    print("\n" + "=" * 70)
    print("🗣️  CONVERSATION START")
    print("=" * 70)

    alice_initial = "Climate change is the most urgent challenge we face today."
    print(f"\n💬 Alice: {alice_initial}")

    # Multi-round communication (3 rounds)
    num_rounds = 10
    current_speaker = "Alice"
    current_text = alice_initial

    for round_num in range(1, num_rounds + 1):
        print(f"\n{'─' * 70}")
        print(f"🔄 ROUND {round_num}/{num_rounds}")
        print(f"{'─' * 70}")

        # Determine who responds
        if current_speaker == "Alice":
            responding_agent = "Bob"
            current_speaker = "Bob"
        else:
            responding_agent = "Alice"
            current_speaker = "Alice"

        # Advance time by 1 hour
        current_time += timedelta(hours=1)
        manager.set_agent_time(responding_agent, current_time)
        print(f"\n⏰ Time: Day {current_time.day}, Hour {current_time.hour:02d}:00")

        # Step A: Agent reads tuple (topic, text) from peer
        peer = "Alice" if responding_agent == "Bob" else "Bob"
        content_tuple = (topic, current_text)
        print(f"\n📥 {responding_agent} receives from {peer}:")
        print(f"    Topic: '{content_tuple[0]}'")
        print(f"    Text: '{content_tuple[1]}'")

        # Extract triplets from the content
        triplets = extract_triplets(current_text, peer)
        print(f"  ✓ Extracted {len(triplets)} triplets")

        # Step B: Update KG and get context (atomic operation)
        print(f"\n🧠 {responding_agent} processes content and retrieves context...")
        context = manager.process_and_get_context(
            responding_agent, topic, current_text, author=peer, triplets=triplets
        )
        print(f"  ✓ KG updated")
        print(f"  ✓ Context retrieved: {context[:80]}...")

        # Step C: Use context with external LLM to generate response
        print(f"\n🤖 {responding_agent} generates response using external LLM...")

        if responding_agent == "Alice":
            agent_profile = "a democrat environmentalist"
        else:
            agent_profile = "an alt-right skeptic who values economic growth and do not believe in climate change"
        response = external_llm_generate(responding_agent, context, topic, agent_profile)
        print(f"  ✓ Generated: '{response}'")

        # Step D: Update KG with the generated response
        print(f"\n💾 {responding_agent} updates KG with own response...")
        response_triplets = extract_response_triplets(response, responding_agent)
        manager.update_with_response(
            responding_agent, response, triplets=response_triplets, context=context
        )
        print(f"  ✓ KG updated with {len(response_triplets)} new beliefs")

        # Print the response
        print(f"\n💬 {responding_agent}: {response}")

        # Set for next round
        current_text = response

    # Final summary
    print("\n" + "=" * 70)
    print("✅ CONVERSATION COMPLETE")
    print("=" * 70)

    print(f"\n📊 Final Knowledge Graphs:")
    print(f"{'─' * 70}")

    for agent_name in ["Alice", "Bob"]:
        print(f"\n👤 {agent_name}'s Knowledge:")
        knowledge = manager.get_agent_knowledge(agent_name, topic=topic)

        print(f"  Personal Beliefs: {len(knowledge['agent_beliefs'])} entries")
        for belief in knowledge["agent_beliefs"][:5]:
            sentiment = belief.get("sentiment", 0)
            print(
                f"    • I {belief['relation']} {belief['target']} (sentiment: {sentiment:+.2f})"
            )

        print(f"  World Knowledge: {len(knowledge['world_knowledge'])} entries")
        for fact in knowledge["world_knowledge"][:5]:
            print(f"    • {fact['source']} {fact['relation']} {fact['target']}")

    print(f"\n💾 Database saved to: {DB_PATH}")
    print(f"⏰ Final time: Day {current_time.day}, Hour {current_time.hour:02d}:00")


if __name__ == "__main__":
    run_use_case()
