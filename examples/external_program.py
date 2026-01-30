"""
External Program Example - Using GhostKG API

This example demonstrates how an external program can:
1. Handle business logic for agent communication
2. Generate text using external LLMs
3. Update agent KGs with content and responses
4. Control time for each interaction
"""

import sys
import os
import datetime
from datetime import timedelta

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghost_kg import AgentManager, Rating

DB_PATH = "external_program_example.db"

# Cleanup
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


def simulate_llm_response(context: str, topic: str, agent_name: str) -> str:
    """
    Simulate an external LLM generating a response.
    In a real scenario, this would call GPT-4, Claude, or another LLM API.
    """
    # Simulate response based on agent name
    if agent_name == "Alice":
        return "I believe UBI could provide a safety net as automation increases."
    else:
        return "I'm concerned that UBI might discourage people from working."


def extract_triplets_from_content(content: str, author: str):
    """
    Simulate external triplet extraction from content.
    In a real scenario, this would use an NLP model or LLM to extract structured info.
    """
    # Simple simulation based on content
    triplets = []

    if "automation" in content.lower():
        triplets.append((author, "mentions", "automation"))
        triplets.append(("automation", "affects", "jobs"))

    if "safety net" in content.lower():
        triplets.append(("UBI", "provides", "safety net"))

    if "discourage" in content.lower():
        triplets.append(("UBI", "might_discourage", "work"))

    return triplets


def extract_triplets_from_response(response: str):
    """
    Simulate external triplet extraction from agent's own response.
    Returns list of (relation, target, sentiment) tuples.
    """
    triplets = []

    if "believe" in response.lower() or "support" in response.lower():
        if "UBI" in response or "ubi" in response.lower():
            triplets.append(("support", "UBI", 0.7))

    if "concerned" in response.lower() or "worried" in response.lower():
        if "UBI" in response or "ubi" in response.lower():
            triplets.append(("concerned_about", "UBI", -0.5))

    if "safety net" in response.lower():
        triplets.append(("value", "safety net", 0.8))

    if "discourage" in response.lower():
        triplets.append(("worry_about", "work motivation", -0.6))

    return triplets


def run_external_program_example():
    """
    Demonstrates external program using GhostKG API without internal LLM logic.
    """
    print("🚀 External Program Example - Using GhostKG API")
    print("=" * 60)

    # 1. Initialize AgentManager
    manager = AgentManager(db_path=DB_PATH)

    # 2. Create agents
    alice = manager.create_agent("Alice")
    bob = manager.create_agent("Bob")

    # 3. Set initial time
    sim_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
    manager.set_agent_time("Alice", sim_time)
    manager.set_agent_time("Bob", sim_time)

    print(f"\n⏰ Simulation Time: {sim_time}")
    print("\n📝 Initializing agent knowledge...")

    # 4. Seed initial beliefs directly
    manager.learn_triplet(
        "Alice", "I", "support", "UBI", rating=Rating.Easy, sentiment=0.8
    )
    manager.learn_triplet(
        "Bob", "I", "oppose", "UBI", rating=Rating.Easy, sentiment=-0.7
    )

    print("   ✓ Alice supports UBI")
    print("   ✓ Bob opposes UBI")

    # 5. Simulate conversation
    topic = "UBI"
    last_content = "I think UBI is necessary because automation will take our jobs."
    last_author = "Alice"

    print(f"\n💬 [{last_author}]: {last_content}")

    num_rounds = 3

    for i in range(num_rounds):
        print(f"\n{'─' * 60}")
        print(f"🔄 ROUND {i+1}/{num_rounds}")
        print(f"{'─' * 60}")

        # --- Bob responds ---
        sim_time += timedelta(hours=1)
        manager.set_agent_time("Bob", sim_time)

        print(f"\n⏰ Time: {sim_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"\n📥 Bob is processing Alice's message...")

        # External program extracts triplets from content
        triplets = extract_triplets_from_content(last_content, last_author)
        print(f"   ✓ Extracted {len(triplets)} triplets from content")

        # Update Bob's KG with what he read
        manager.absorb_content(
            "Bob", last_content, author=last_author, triplets=triplets
        )

        # External program gets context for Bob
        context = manager.get_context("Bob", topic)
        print(f"\n🧠 Bob's context for reply:")
        print(f"   {context[:100]}...")

        # External program generates response using its own LLM
        bob_response = simulate_llm_response(context, topic, "Bob")
        print(f"\n💬 [Bob]: {bob_response}")

        # Extract triplets from Bob's response
        response_triplets = extract_triplets_from_response(bob_response)
        print(f"   ✓ Extracted {len(response_triplets)} triplets from response")

        # Update Bob's KG with his own response
        manager.update_with_response("Bob", bob_response, triplets=response_triplets)

        last_content = bob_response
        last_author = "Bob"

        # --- Alice responds ---
        sim_time += timedelta(hours=2)
        manager.set_agent_time("Alice", sim_time)

        print(f"\n⏰ Time: {sim_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"\n📥 Alice is processing Bob's message...")

        # External program extracts triplets from content
        triplets = extract_triplets_from_content(last_content, last_author)
        print(f"   ✓ Extracted {len(triplets)} triplets from content")

        # Update Alice's KG with what she read
        manager.absorb_content(
            "Alice", last_content, author=last_author, triplets=triplets
        )

        # External program gets context for Alice
        context = manager.get_context("Alice", topic)
        print(f"\n🧠 Alice's context for reply:")
        print(f"   {context[:100]}...")

        # External program generates response using its own LLM
        alice_response = simulate_llm_response(context, topic, "Alice")
        print(f"\n💬 [Alice]: {alice_response}")

        # Extract triplets from Alice's response
        response_triplets = extract_triplets_from_response(alice_response)
        print(f"   ✓ Extracted {len(response_triplets)} triplets from response")

        # Update Alice's KG with her own response
        manager.update_with_response(
            "Alice", alice_response, triplets=response_triplets
        )

        last_content = alice_response
        last_author = "Alice"

    print(f"\n{'=' * 60}")
    print("✅ Simulation Complete!")
    print(f"\n📊 Final Knowledge Graphs:")
    print(f"{'=' * 60}")

    # Retrieve and display agent knowledge
    for agent_name in ["Alice", "Bob"]:
        print(f"\n👤 {agent_name}'s Knowledge:")
        knowledge = manager.get_agent_knowledge(agent_name, topic="UBI")

        print(f"   Personal Beliefs: {len(knowledge['agent_beliefs'])} triplets")
        for belief in knowledge["agent_beliefs"][:3]:
            print(
                f"      - I {belief['relation']} {belief['target']} (sentiment: {belief.get('sentiment', 0):.2f})"
            )

        print(f"   World Knowledge: {len(knowledge['world_knowledge'])} triplets")
        for fact in knowledge["world_knowledge"][:3]:
            print(f"      - {fact['source']} {fact['relation']} {fact['target']}")

    print(f"\n💾 Data stored in: {DB_PATH}")


if __name__ == "__main__":
    run_external_program_example()
