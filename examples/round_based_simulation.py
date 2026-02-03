"""
Round-Based Simulation Example

This example demonstrates using round-based time instead of real datetime objects.
Perfect for simulations where time is discretized into rounds or turns.

In this simulation:
- Time is measured in (day, hour) tuples
- Day starts at 1 and increments indefinitely
- Hour is always in [0, 23]
- Two agents discuss artificial intelligence over multiple rounds
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghost_kg import GhostAgent, CognitiveLoop, Rating

DB_PATH = "round_based_simulation.db"

# Cleanup old database
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


def run_round_based_simulation():
    """Run a simulation using round-based time (day, hour) instead of datetime."""
    print("🎲 Initializing Round-Based Simulation...")
    print("   Time format: (day, hour) where day >= 1, hour in [0, 23]\n")

    # 1. Initialize Agents
    alice = GhostAgent("Alice", db_path=DB_PATH)
    bob = GhostAgent("Bob", db_path=DB_PATH)

    # 2. Set Initial Round-Based Time: Day 1, Hour 9
    initial_time = (1, 9)
    alice.set_time(initial_time)
    bob.set_time(initial_time)
    print(f"⏰ Starting at Day {initial_time[0]}, Hour {initial_time[1]:02d}:00")

    # 3. Seed Initial Beliefs
    print("\n📚 Seeding Initial Beliefs...")
    alice.learn_triplet("I", "support", "AI safety research", Rating.Easy)
    alice.learn_triplet("AI", "will", "transform society", Rating.Good)
    print("   [Alice]: I support AI safety research")

    bob.learn_triplet("I", "believe", "AI progress is unstoppable", Rating.Easy)
    bob.learn_triplet("regulation", "might", "slow innovation", Rating.Good)
    print("   [Bob]: I believe AI progress is unstoppable")

    # 4. Run Simulation Rounds
    print("\n" + "=" * 70)
    print("SIMULATION ROUNDS")
    print("=" * 70)

    # Track current time
    current_day = 1
    current_hour = 10

    rounds = [
        {
            "day": 1,
            "hour": 10,
            "agent": alice,
            "name": "Alice",
            "action": ("learn", "AI", "needs", "ethical guidelines", Rating.Good),
        },
        {
            "day": 1,
            "hour": 14,
            "agent": bob,
            "name": "Bob",
            "action": ("learn", "innovation", "drives", "progress", Rating.Easy),
        },
        {
            "day": 2,
            "hour": 9,
            "agent": alice,
            "name": "Alice",
            "action": (
                "learn",
                "collaboration",
                "between",
                "researchers",
                Rating.Good,
            ),
        },
        {
            "day": 2,
            "hour": 15,
            "agent": bob,
            "name": "Bob",
            "action": ("learn", "AI", "requires", "massive data", Rating.Hard),
        },
        {
            "day": 3,
            "hour": 11,
            "agent": alice,
            "name": "Alice",
            "action": ("review", "AI safety research"),
        },
        {
            "day": 3,
            "hour": 16,
            "agent": bob,
            "name": "Bob",
            "action": ("review", "AI progress"),
        },
    ]

    for i, round_data in enumerate(rounds, 1):
        day = round_data["day"]
        hour = round_data["hour"]
        agent = round_data["agent"]
        name = round_data["name"]
        action = round_data["action"]

        print(f"\n🔄 Round {i}: Day {day}, Hour {hour:02d}:00")
        print("-" * 70)

        # Set time for this round
        round_time = (day, hour)
        agent.set_time(round_time)

        if action[0] == "learn":
            _, source, relation, target, rating = action
            agent.learn_triplet(source, relation, target, rating)
            print(f"   [{name}] learned: {source} {relation} {target}")
        elif action[0] == "review":
            _, topic = action
            memory = agent.get_memory_view(topic)
            print(f"   [{name}] reviewing '{topic}':")
            print(f"   {memory[:150]}..." if len(memory) > 150 else f"   {memory}")

    # 5. Final Knowledge State
    print("\n" + "=" * 70)
    print("FINAL KNOWLEDGE STATE (Day 3, Hour 18)")
    print("=" * 70)

    final_time = (3, 18)
    alice.set_time(final_time)
    bob.set_time(final_time)

    print("\n🧠 Alice's Knowledge about AI:")
    alice_ai = alice.get_memory_view("AI")
    print(f"   {alice_ai}")

    print("\n🧠 Bob's Knowledge about AI:")
    bob_ai = bob.get_memory_view("AI")
    print(f"   {bob_ai}")

    # 6. Show Database Storage
    print("\n" + "=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70)

    cursor = alice.db.conn.cursor()

    # Check nodes with round-based time
    cursor.execute(
        """
        SELECT id, sim_day, sim_hour, created_at 
        FROM kg_nodes 
        WHERE owner_id = 'Alice' AND sim_day IS NOT NULL 
        LIMIT 3
    """
    )
    print("\n📊 Sample nodes with round-based time (Alice):")
    for row in cursor.fetchall():
        print(
            f"   Node: {row[0]}, Day: {row[1]}, Hour: {row[2]}, Created: {row[3]}"
        )

    # Check edges with round-based time
    cursor.execute(
        """
        SELECT source, relation, target, sim_day, sim_hour 
        FROM kg_edges 
        WHERE owner_id = 'Alice' AND sim_day IS NOT NULL 
        LIMIT 3
    """
    )
    print("\n📊 Sample edges with round-based time (Alice):")
    for row in cursor.fetchall():
        print(
            f"   {row[0]} --{row[1]}--> {row[2]}, Day: {row[3]}, Hour: {row[4]}"
        )

    print("\n✅ Simulation Complete!")
    print(f"   Database saved to: {DB_PATH}")
    print("   Round-based time successfully stored in database")


if __name__ == "__main__":
    run_round_based_simulation()
