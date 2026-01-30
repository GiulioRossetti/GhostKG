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
"""

import sys
import os
import datetime
from datetime import timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghost_kg import AgentManager, Rating

DB_PATH = "use_case_example.db"

# Cleanup
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


def external_llm_generate(agent_name: str, context: str, topic: str) -> str:
    """
    Simulate external LLM generating a response based on context.
    In production, this would call GPT-4, Claude, or another LLM API.
    """
    print(f"  [External LLM] Generating response for {agent_name}...")
    print(f"  [External LLM] Using context: {context[:100]}...")

    # Simulate different responses based on agent
    if agent_name == "Alice":
        responses = [
            "I think renewable energy is the key to addressing climate change.",
            "Solar and wind power have become much more affordable recently.",
            "We need government incentives to accelerate the transition.",
        ]
    else:  # Bob
        responses = [
            "I agree that climate action is important, but we must consider costs.",
            "Economic stability is also crucial for sustainable development.",
            "We should pursue balanced policies that protect both environment and economy.",
        ]

    # Simple rotation through responses
    import hashlib

    idx = hash(context) % len(responses)
    return responses[idx]


def extract_triplets(text: str, author: str):
    """
    Simulate triplet extraction from text.
    In production, this would use NLP/LLM to extract structured knowledge.
    """
    triplets = []

    # Always extract basic mention triplet
    # Extract main concept from text
    text_lower = text.lower()

    # Extract author's stance
    if any(word in text_lower for word in ["urgent", "important", "crucial"]):
        if "climate" in text_lower:
            triplets.append((author, "emphasizes", "urgency"))

    if "challenge" in text_lower:
        triplets.append((author, "discusses", "challenges"))

    # Simple keyword-based extraction (in production, use proper NLP)
    keywords = {
        "renewable energy": [
            (author, "mentions", "renewable energy"),
            ("renewable energy", "addresses", "climate change"),
        ],
        "solar": [
            (author, "talks about", "solar power"),
            ("solar", "is_type_of", "renewable energy"),
        ],
        "wind": [
            (author, "talks about", "wind power"),
            ("wind", "is_type_of", "renewable energy"),
        ],
        "government": [
            (author, "mentions", "government"),
            ("government", "can_provide", "incentives"),
        ],
        "costs": [
            (author, "considers", "costs"),
            ("costs", "relate_to", "economic stability"),
        ],
        "economy": [
            (author, "values", "economy"),
            ("economy", "important_for", "development"),
        ],
        "balanced": [(author, "advocates", "balanced policies")],
        "stability": [
            (author, "mentions", "stability"),
            ("stability", "relates_to", "development"),
        ],
    }

    for keyword, keyword_triplets in keywords.items():
        if keyword in text_lower:
            triplets.extend(keyword_triplets)

    # Always have at least one triplet
    if not triplets:
        triplets.append((author, "says", "something"))

    return triplets


def extract_response_triplets(text: str):
    """
    Extract triplets from agent's own response.
    Returns list of (relation, target, sentiment) tuples.
    """
    triplets = []

    # Simple keyword-based extraction
    if "renewable energy" in text.lower():
        triplets.append(("support", "renewable energy", 0.8))
    if "solar" in text.lower():
        triplets.append(("interested_in", "solar power", 0.7))
    if "wind" in text.lower():
        triplets.append(("interested_in", "wind power", 0.7))
    if "government" in text.lower():
        triplets.append(("want", "government action", 0.6))
    if "costs" in text.lower():
        triplets.append(("concerned_about", "costs", -0.3))
    if "economy" in text.lower():
        triplets.append(("value", "economic stability", 0.7))
    if "balanced" in text.lower():
        triplets.append(("prefer", "balanced approach", 0.8))

    return triplets


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
    num_rounds = 3
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
        response = external_llm_generate(responding_agent, context, topic)
        print(f"  ✓ Generated: '{response}'")

        # Step D: Update KG with the generated response
        print(f"\n💾 {responding_agent} updates KG with own response...")
        response_triplets = extract_response_triplets(response)
        manager.update_with_response(
            responding_agent, response, triplets=response_triplets
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
