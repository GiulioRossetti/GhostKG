import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import from the package (now that __init__.py is fixed)
from ghost_kg import GhostAgent, CognitiveLoop, Rating

DB_PATH = "debate_simulation.db"

# Cleanup previous run to start fresh
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


def run_relational_debate():
    print("🧠 Initializing SQL-Backed Agents...")

    # Init Agents
    agent_a = GhostAgent("Alice", db_path=DB_PATH)
    mind_a = CognitiveLoop(agent_a)

    agent_b = GhostAgent("Bob", db_path=DB_PATH)
    mind_b = CognitiveLoop(agent_b)

    # --- SEEDING MEMORY ---
    print("\n--- Seeding Initial Beliefs ---")
    # Alice Loves Pizza
    # (Source, Relation, Target, Rating)
    agent_a.learn_triplet("Alice", "don't like", "USA", Rating.Easy)
    agent_a.learn_triplet("USA", "wants", "Greenland", Rating.Easy)
    agent_a.learn_triplet("Greenland", "must remain", "independent", Rating.Easy)

    # Bob Hates Pizza
    agent_b.learn_triplet("Bob", "likes", "USA", Rating.Easy)
    agent_b.learn_triplet("USA", "wants", "Greenland", Rating.Easy)
    agent_a.learn_triplet("Greenland", "must become", "USA state", Rating.Easy)

    # --- CONVERSATION ---
    topic = "greenland"
    last_msg = "I think US should acquire Greenland for its strategic value."
    print(f"\n[Alice] starts: {last_msg}")

    # Short conversation loop
    for i in range(10):
        print(f"\n--- Round {i+1} ---")

        # Bob Hears Alice
        mind_b.absorb(last_msg, author="Alice")
        # Bob Replies
        last_msg = mind_b.reply(topic, partner_name="Alice")

        # Alice Hears Bob
        mind_a.absorb(last_msg, author="Bob")
        # Alice Replies
        last_msg = mind_a.reply(topic, partner_name="Bob")

    print(f"\n✅ Done. Data stored in {DB_PATH}")


if __name__ == "__main__":
    run_relational_debate()
