# Temporal Simulation

**Source:** `examples/hourly_simulation.py`

This example demonstrates how to run realistic time-based simulations where agents interact with variable time gaps between messages, simulating real-world conversation patterns.

## Overview

Alice and Bob discuss UBI (Universal Basic Income) with random time delays (12-36 hours) between each exchange. This showcases:
- **Variable time progression**: Realistic gaps between interactions
- **Memory decay**: FSRS calculations based on elapsed time
- **CognitiveLoop usage**: Integrated LLM operations (optional)
- **Simple, focused code**: ~75 lines for a complete simulation

## Key Concepts

### Why Variable Time Matters

In real conversations:
- People don't respond immediately
- Some messages get quick replies (1 hour)
- Some get delayed responses (days later)
- **Memory decays** over longer gaps

GhostKG's FSRS system models this realistically:
- Recent memories are strong (high retrievability)
- Old, unreviewed memories fade (low retrievability)
- Time gaps affect what agents remember

## Step-by-Step Walkthrough

### Step 1: Initialize with Start Time

```python
import datetime
from datetime import timedelta

# Set explicit start time
sim_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
```

**Why start time matters:**
- All memory calculations are relative to current time
- Allows you to simulate past or future scenarios
- Makes debugging reproducible

### Step 2: Create Agents with CognitiveLoop

```python
from ghost_kg import GhostAgent, CognitiveLoop, Rating

alice = GhostAgent("Alice", db_path="hourly_simulation.db")
alice_mind = CognitiveLoop(alice)

bob = GhostAgent("Bob", db_path="hourly_simulation.db")
bob_mind = CognitiveLoop(bob)
```

**What is CognitiveLoop?**
- Higher-level API that wraps GhostAgent
- Integrates with LLMs for automatic triplet extraction
- Provides `absorb()` and `reply()` convenience methods
- Optional - you can use GhostAgent directly like in other examples

### Step 3: Sync Clocks

```python
alice.set_time(sim_time)
bob.set_time(sim_time)
```

Both agents start at the same time: Day 1, 09:00.

### Step 4: Seed Initial Beliefs

```python
topic = "UBI"
alice.learn_triplet("I", "support", "UBI", Rating.Easy)
bob.learn_triplet("I", "oppose", "UBI", Rating.Easy)
```

Simple initialization - Alice supports UBI, Bob opposes it.

### Step 5: The Conversation Loop

```python
num_rounds = 10
last_msg = "I think UBI is necessary because automation will take our jobs."

for i in range(num_rounds):
    # Bob responds (1 hour later)
    sim_time += timedelta(hours=1)
    bob.set_time(sim_time)
    
    # Process and reply
    bob_mind.absorb(last_msg, author="Alice")
    last_msg = bob_mind.reply(topic, partner_name="Alice")
    
    # Random gap (12-36 hours)
    gap = random.randint(12, 36)
    sim_time += timedelta(hours=gap)
    
    # Alice responds
    alice.set_time(sim_time)
    
    # Process and reply
    alice_mind.absorb(last_msg, author="Bob")
    last_msg = alice_mind.reply(topic, partner_name="Bob")
```

### Breaking Down Each Step

**Bob's Turn:**

```python
# 1. Advance time by 1 hour (quick response)
sim_time += timedelta(hours=1)
bob.set_time(sim_time)

# 2. Absorb Alice's message
bob_mind.absorb(last_msg, author="Alice")
```

**What `absorb()` does:**
- Extracts triplets from the message (using LLM or Fast Mode)
- Updates Bob's knowledge graph
- Updates FSRS memory strength based on current time

```python
# 3. Generate reply
last_msg = bob_mind.reply(topic, partner_name="Alice")
```

**What `reply()` does:**
- Gets Bob's context about the topic
- Calls LLM to generate a response
- Extracts triplets from Bob's own response
- Updates Bob's knowledge graph with new beliefs

**Random Time Gap:**

```python
# Simulate realistic delay
gap = random.randint(12, 36)  # 12-36 hours
sim_time += timedelta(hours=gap)
print(f"💤 ... {gap} hours pass ...")
```

**Effect on memory:**
- If gap = 12 hours: Recent memories still strong
- If gap = 36 hours: Some memories start to fade
- FSRS calculates retrievability: `R = (1 + t/(9S))^-1`
  - `t` = elapsed time in days
  - `S` = stability (memory strength)

**Alice's Turn:**

Same process as Bob:
1. Set her current time (after the gap)
2. Absorb Bob's message
3. Generate her reply

### Step 6: Memory Decay in Action

After each time gap, memory retrievability decreases:

```python
# Initially (Day 1, 09:00)
alice.learn_triplet("I", "support", "UBI", Rating.Easy)
# Stability ≈ 5.0, Retrievability = 1.0 (just learned)

# After 1 day (Day 2, 09:00)  
# Retrievability ≈ 0.98 (still very strong)

# After 5 days (Day 6, 09:00)
# Retrievability ≈ 0.82 (starting to fade)

# After 15 days (Day 16, 09:00)
# Retrievability ≈ 0.43 (significantly faded)
```

**What this means:**
- Strong memories (high stability) last longer
- Weak memories fade quickly
- Re-reviewing memories increases stability

## Time Progression Example

```
Day 1, 09:00 - Simulation starts
  Alice: "UBI is necessary because automation..."

Day 1, 10:00 - Bob responds (1 hour later)
  Bob: "I'm concerned UBI might discourage work..."

  💤 (25 hours pass)

Day 2, 11:00 - Alice responds
  Alice: "But without UBI, unemployment from AI..."

  💤 (18 hours pass)

Day 3, 05:00 - Bob responds
  Bob: "We need job retraining programs instead..."

  💤 (31 hours pass)

Day 4, 12:00 - Alice responds
  (Some early memories starting to fade)
```

## Output Example

```
⏳ Initializing Temporal Simulation...

[2025-01-01 09:00:00+00:00] Seeding Initial Beliefs...
[Alice]: I think UBI is necessary because automation will take our jobs.

--- 🔔 ROUND 1 ---
🕒 Time is now: 2025-01-01 10:00:00+00:00
💤 ... 24 hours pass ...
🕒 Time is now: 2025-01-02 10:00:00+00:00

--- 🔔 ROUND 2 ---
🕒 Time is now: 2025-01-02 11:00:00+00:00
💤 ... 15 hours pass ...
🕒 Time is now: 2025-01-03 02:00:00+00:00

...

✅ Simulation Complete.
Final Time: 2025-01-15 18:00:00+00:00
Data stored in hourly_simulation.db
```

## Customization

### Change Time Gaps

```python
# Shorter gaps (more frequent interaction)
gap = random.randint(1, 4)  # 1-4 hours

# Longer gaps (more memory decay)
gap = random.randint(24, 72)  # 1-3 days

# Fixed gap (deterministic testing)
gap = 6  # Always 6 hours
```

### Change Response Time

```python
# Quick responses (both agents)
sim_time += timedelta(minutes=30)

# Slower responses
sim_time += timedelta(hours=3)
```

### Disable LLM (Testing Mode)

CognitiveLoop requires an LLM by default. For testing without LLM:

```python
# Option 1: Use AgentManager instead (no LLM needed)
from ghost_kg import AgentManager

manager = AgentManager(db_path="test.db")
# ... use manager.absorb_content() and manual responses

# Option 2: Mock the LLM client
alice.client = None  # Disable LLM calls
```

## Use Cases

This pattern is perfect for:

1. **Social Media Simulation**: Variable response times like real users
2. **Email Conversations**: Hours/days between messages
3. **Forum Discussions**: Participants respond when available
4. **Long-term Relationships**: Track belief evolution over weeks/months
5. **Memory Research**: Study how time gaps affect knowledge retention

## Memory Decay Analysis

After running the simulation, you can analyze how memories decayed:

```python
# Query retrievability scores over time
import sqlite3

conn = sqlite3.connect("hourly_simulation.db")
cursor = conn.cursor()

# Get all memory snapshots for Alice
cursor.execute("""
    SELECT id, stability, last_review 
    FROM nodes 
    WHERE owner_id = 'Alice'
    ORDER BY last_review
""")

for concept, stability, last_review in cursor.fetchall():
    # Calculate retrievability at final time
    elapsed_days = (final_time - last_review).days
    retrievability = (1 + elapsed_days/(9*stability)) ** -1
    print(f"{concept}: {retrievability:.2%}")
```

## Comparison with Other Examples

| Feature | External Program | Use Case | **Hourly Simulation** |
|---------|-----------------|----------|----------------------|
| **Time Control** | Manual | Fixed 1-hour | **Random 12-36 hours** |
| **LLM Integration** | External only | Ollama | CognitiveLoop (optional) |
| **Code Complexity** | Medium | High | **Low (~75 lines)** |
| **Best For** | Custom LLM | Full demo | **Realistic timing** |

## Running the Example

```bash
cd examples
python hourly_simulation.py
```

**Runtime:** ~30 seconds (if LLM is mocked) or ~2 minutes (with Ollama)

**Output:** Database file `hourly_simulation.db` containing the full conversation history with time stamps.

## Next Steps

- Try [Export History](export_history.md) to visualize the knowledge graph evolution
- See [External Program](external_program.md) for more control over LLM interactions
- Read [FSRS Documentation](../ALGORITHMS.md#fsrs-algorithm) to understand memory calculations

## Pro Tips

1. **Start time matters**: Use UTC timezone for consistency
2. **Variable gaps create realism**: Real conversations have delays
3. **Monitor retrievability**: Use queries to track memory decay
4. **Test memory limits**: Run for 100+ rounds to see long-term effects
5. **Save simulation states**: Export at key points for analysis
