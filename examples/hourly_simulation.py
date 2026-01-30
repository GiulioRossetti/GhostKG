import sys
import os
import random
import datetime
from datetime import timedelta

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ghost_kg import GhostAgent, CognitiveLoop, Rating

DB_PATH = "hourly_simulation.db"

# Cleanup
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)


def run_hourly_simulation():
    print("⏳ Initializing Temporal Simulation...")

    # 1. Setup Start Time (Day 1, 09:00 AM)
    sim_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)

    # 2. Init Agents
    alice = GhostAgent("Alice", db_path=DB_PATH)
    alice_mind = CognitiveLoop(alice)

    bob = GhostAgent("Bob", db_path=DB_PATH)
    bob_mind = CognitiveLoop(bob)

    # Sync clocks
    alice.set_time(sim_time)
    bob.set_time(sim_time)

    # 3. Seed Initial Memory
    topic = "UBI"
    print(f"\n[{sim_time}] Seeding Initial Beliefs...")
    alice.learn_triplet("I", "support", "UBI", Rating.Easy)
    bob.learn_triplet("I", "oppose", "UBI", Rating.Easy)

    last_msg = "I think UBI is necessary because automation will take our jobs."
    print(f"[Alice]: {last_msg}")

    # 4. Run Loop
    num_rounds = 10

    for i in range(num_rounds):
        print(f"\n--- 🔔 ROUND {i+1} ---")

        # --- A. Bob Responds (1 hour later) ---
        sim_time += timedelta(hours=1)
        bob.set_time(sim_time)
        print(f"🕒 Time is now: {sim_time}")

        bob_mind.absorb(last_msg, author="Alice")
        last_msg = bob_mind.reply(topic, partner_name="Alice")

        # --- B. Random Gap (2 to 12 hours) ---
        gap = random.randint(12, 36)
        sim_time += timedelta(hours=gap)
        print(f"💤 ... {gap} hours pass ...")

        # --- C. Alice Responds ---
        alice.set_time(sim_time)
        print(f"🕒 Time is now: {sim_time}")

        alice_mind.absorb(last_msg, author="Bob")
        last_msg = alice_mind.reply(topic, partner_name="Bob")

    print("\n✅ Simulation Complete.")
    print(f"Final Time: {sim_time}")
    print(f"Data stored in {DB_PATH}")


if __name__ == "__main__":
    run_hourly_simulation()
