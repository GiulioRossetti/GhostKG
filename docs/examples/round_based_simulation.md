# Round-Based Simulation Example

This example demonstrates using **round-based time** instead of real datetime objects. This is perfect for simulations where time is discretized into rounds, turns, or game ticks.

## 🎯 Use Case

In many simulative scenarios, time is not measured in real datetime but rather as:
- **Game rounds** (e.g., turn-based strategy games)
- **Simulation steps** (e.g., agent-based models)
- **Discrete time periods** (e.g., economic models)

In these cases, you can use `(day, hour)` tuples where:
- `day`: An unbounded integer starting from 1
- `hour`: An integer in the range [0, 23]

## 📋 Step-by-Step Explanation

### 1. Import and Setup

```python
from ghost_kg import GhostAgent, Rating

DB_PATH = "round_based_simulation.db"

# Create agents
alice = GhostAgent("Alice", db_path=DB_PATH)
bob = GhostAgent("Bob", db_path=DB_PATH)
```

### 2. Set Round-Based Time

Instead of using `datetime.datetime` objects, you can pass `(day, hour)` tuples:

```python
# Day 1, Hour 9 (equivalent to 09:00 on day 1)
initial_time = (1, 9)
alice.set_time(initial_time)
bob.set_time(initial_time)
```

**Key Points:**
- `day` must be >= 1
- `hour` must be in [0, 23]
- Time is stored in the database with `sim_day` and `sim_hour` columns

### 3. Learning with Round-Based Time

Learning works exactly the same as with datetime:

```python
# Day 1, Hour 10
alice.set_time((1, 10))
alice.learn_triplet("AI", "needs", "ethical guidelines", Rating.Good)
```

The system automatically:
- Associates the learned knowledge with the current round-based time
- Stores both the tuple `(1, 10)` and a NULL datetime in the database
- Maintains FSRS memory tracking

### 4. Advancing Time

Simply update the time to the next round:

```python
# Advance to Day 2, Hour 9
alice.set_time((2, 9))

# You can skip hours or days as needed
bob.set_time((3, 15))  # Jump to Day 3, Hour 15
```

### 5. Memory Retrieval

Memory retrieval works the same way:

```python
alice.set_time((3, 11))
memory = alice.get_memory_view("AI safety research")
print(memory)
```

The FSRS memory system adapts to round-based time:
- In pure round mode (no datetime), same-day reviews are assumed
- Memory decay calculations are simplified for discrete time steps

### 6. Database Storage

The database automatically stores round-based time information:

```sql
-- Nodes table includes sim_day and sim_hour
SELECT id, sim_day, sim_hour FROM nodes WHERE owner_id = 'Alice';

-- Output:
-- id                    | sim_day | sim_hour
-- AI safety research    | 1       | 9
-- ethical guidelines    | 1       | 10

-- Edges table also includes round-based time
SELECT source, relation, target, sim_day, sim_hour 
FROM edges 
WHERE owner_id = 'Alice';

-- Output:
-- source | relation | target              | sim_day | sim_hour
-- I      | support  | AI safety research  | 1       | 9
-- AI     | needs    | ethical guidelines  | 1       | 10
```

## 🔄 Mixed Usage

You can even switch between datetime and round-based time:

```python
import datetime

# Use datetime
agent.set_time(datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc))

# Switch to round-based
agent.set_time((5, 14))

# Switch back to datetime
agent.set_time(datetime.datetime(2025, 1, 2, 10, 0, 0, tzinfo=datetime.timezone.utc))
```

## 🚀 Running the Example

```bash
cd examples
python round_based_simulation.py
```

## 📊 Expected Output

```
🎲 Initializing Round-Based Simulation...
   Time format: (day, hour) where day >= 1, hour in [0, 23]

⏰ Starting at Day 1, Hour 09:00

📚 Seeding Initial Beliefs...
   [Alice]: I support AI safety research
   [Bob]: I believe AI progress is unstoppable

======================================================================
SIMULATION ROUNDS
======================================================================

🔄 Round 1: Day 1, Hour 10:00
----------------------------------------------------------------------
   [Alice] learned: AI needs ethical guidelines

🔄 Round 2: Day 1, Hour 14:00
----------------------------------------------------------------------
   [Bob] learned: innovation drives progress

...

✅ Simulation Complete!
   Database saved to: round_based_simulation.db
   Round-based time successfully stored in database
```

## 🎓 Key Takeaways

1. **Simple API**: Just pass `(day, hour)` tuples to `set_time()`
2. **Automatic Storage**: Round-based time is automatically stored in the database
3. **Backward Compatible**: Existing datetime code continues to work
4. **Flexible**: Switch between datetime and round-based time as needed
5. **FSRS Compatible**: Memory system adapts to discrete time representation

## 📚 Related Examples

- **[hourly_simulation.py](hourly_simulation.md)**: Using real datetime for temporal simulations
- **[use_case_example.py](use_case_example.md)**: Basic agent usage patterns

## 🔗 API Reference

- [`GhostAgent.set_time()`](../api/agent.md#set_time): Set simulation clock
- [`SimulationTime`](../api/time_utils.md): Flexible time representation class
- [Database Schema](../DATABASE_SCHEMA.md): Database design and time storage
