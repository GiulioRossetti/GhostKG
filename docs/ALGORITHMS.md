# GhostKG Algorithms and Formulas

This document provides detailed mathematical and algorithmic descriptions of the core algorithms used in GhostKG.

## Table of Contents

1. [FSRS Algorithm](#fsrs-algorithm)
2. [Memory Decay Calculations](#memory-decay-calculations)
3. [Retrievability Formula](#retrievability-formula)
4. [Stability Updates](#stability-updates)
5. [Difficulty Updates](#difficulty-updates)
6. [Sentiment Analysis](#sentiment-analysis)
7. [Query Algorithms](#query-algorithms)

---

## FSRS Algorithm

### Overview

FSRS (Free Spaced Repetition Scheduler) v4.5 is based on the principles of spaced repetition and the spacing effect in cognitive psychology. It models how memories strengthen with successful recall and decay over time.

### Key Variables

| Variable | Symbol | Range | Description |
|----------|--------|-------|-------------|
| Stability | S | [0.1, ∞) | Days until retrievability drops to 90% |
| Difficulty | D | [1, 10] | Inherent complexity of recall |
| Retrievability | R | [0, 1] | Current probability of successful recall |
| State | state | {0, 1, 2} | Learning phase (New/Learning/Review) |
| Repetitions | reps | [0, ∞) | Number of reviews |
| Rating | r | {1, 2, 3, 4} | Review outcome (Again/Hard/Good/Easy) |

### Algorithm Parameters

FSRS uses 17 parameters (p[0] through p[16]) that define the learning curves:

```python
p = [
    0.4,    # p[0]  - Initial stability for "Again" rating
    0.6,    # p[1]  - Initial stability for "Hard" rating
    2.4,    # p[2]  - Initial stability for "Good" rating
    5.8,    # p[3]  - Initial stability for "Easy" rating
    4.93,   # p[4]  - Initial difficulty baseline
    0.94,   # p[5]  - Difficulty adjustment step
    0.86,   # p[6]  - Difficulty weight factor
    0.01,   # p[7]  - Difficulty smoothing factor
    1.49,   # p[8]  - Stability growth rate
    0.14,   # p[9]  - Stability decay exponent
    0.94,   # p[10] - Retrievability impact factor
    2.18,   # p[11] - "Again" stability multiplier
    0.05,   # p[12] - "Again" difficulty exponent
    0.34,   # p[13] - "Again" state exponent
    1.26,   # p[14] - "Again" retrievability impact
    0.29,   # p[15] - "Hard" rating penalty
    2.61,   # p[16] - "Easy" rating bonus
]
```

These parameters are optimized based on research into human memory and spaced repetition systems.

---

## Memory Decay Calculations

### Retrievability Formula

The retrievability R represents the probability that the agent can recall a piece of knowledge at time t.

**Formula:**
```
R(t) = (1 + Δt / (9 × S))^(-1)
```

Where:
- `R(t)` = Retrievability at time t
- `Δt` = Elapsed time since last review (in days)
- `S` = Current stability (in days)
- `9` = Constant from FSRS algorithm

**Interpretation:**
- At Δt = 0 (just reviewed): R = 1.0 (perfect recall)
- At Δt = 9×S: R ≈ 0.5 (50% chance of recall)
- As Δt → ∞: R → 0 (forgotten)

**Example:**

```python
# Stability = 10 days
S = 10

# Just reviewed
Δt = 0
R = (1 + 0 / (9 * 10))^(-1) = 1.0

# After 5 days
Δt = 5
R = (1 + 5 / 90)^(-1) ≈ 0.947

# After 30 days
Δt = 30
R = (1 + 30 / 90)^(-1) ≈ 0.750

# After 90 days (9 * S)
Δt = 90
R = (1 + 90 / 90)^(-1) = 0.5
```

### Decay Curve Visualization

```
R (Retrievability)
1.0 ┤●                    
0.9 ┤ ●                   
0.8 ┤  ●●                 
0.7 ┤    ●●               
0.6 ┤      ●●             
0.5 ┤        ●●           
0.4 ┤          ●●         
0.3 ┤            ●●       
0.2 ┤              ●●●    
0.1 ┤                 ●●● 
0.0 ┤                    ●
    └─────────────────────────> Δt (days)
    0   10  20  30  40  50

(For S = 10 days)
```

The curve shows exponential decay, with faster initial forgetting that gradually slows down.

---

## Stability Updates

### New Cards (state = 0)

When encountering knowledge for the first time:

**Formula:**
```
S_new = p[rating - 1]
```

**Values:**
- Rating = 1 (Again): S = 0.4 days
- Rating = 2 (Hard): S = 0.6 days
- Rating = 3 (Good): S = 2.4 days
- Rating = 4 (Easy): S = 5.8 days

The initial stability depends on how easily the knowledge was learned.

### Review State Updates

#### Success (rating ∈ {2, 3, 4})

When successfully recalling knowledge:

**Formula:**
```
S_next = S × (1 + exp(p[8]) × (11 - D_next) × (S^(-p[9])) 
           × (exp((1 - R) × p[10]) - 1) × penalty × bonus)
```

Where:
- `penalty = p[15]` if rating = 2 (Hard), else 1
- `bonus = p[16]` if rating = 4 (Easy), else 1
- `R` = Current retrievability
- `D_next` = Next difficulty value

**Components:**

1. **Growth Factor**: `exp(p[8]) ≈ 4.44`
   - Controls how much stability increases

2. **Difficulty Modifier**: `(11 - D_next)`
   - Easier items get more stability boost
   - Range: [1, 10] → boost multiplier: [1x, 10x]

3. **Stability Decay**: `S^(-p[9])` where p[9] = 0.14
   - Diminishing returns for high stability
   - Prevents infinite growth

4. **Retrievability Impact**: `exp((1 - R) × p[10]) - 1`
   - If R is low (near forgetting), bigger boost
   - If R is high (just learned), smaller boost

5. **Rating Modifiers**:
   - Hard (2): penalty = 0.29 (29% of normal boost)
   - Good (3): no modifier
   - Easy (4): bonus = 2.61 (261% of normal boost)

**Example:**

```python
# Existing knowledge
S = 10 days
D = 5.0
R = 0.85 (recently reviewed)
rating = 3 (Good)

# Calculate next stability
growth = exp(1.49) × (11 - 5) × (10^(-0.14)) × (exp((1 - 0.85) × 0.94) - 1)
       ≈ 4.44 × 6 × 0.725 × 0.148
       ≈ 2.86

S_next = 10 × (1 + 2.86) = 38.6 days
```

#### Failure (rating = 1, "Again")

When failing to recall:

**Formula:**
```
S_next = p[11] × (D_next^(-p[12])) × ((S + 1)^p[13] - 1) × exp((1 - R) × p[14])
```

**Components:**

1. **Base Multiplier**: `p[11] = 2.18`
   - Determines minimum stability after failure

2. **Difficulty Impact**: `D_next^(-p[12])` where p[12] = 0.05
   - Harder items lose more stability
   - Exponent is small, so effect is moderate

3. **Previous Stability**: `(S + 1)^p[13] - 1` where p[13] = 0.34
   - Retains some benefit from previous learning
   - Prevents complete reset

4. **Retrievability Adjustment**: `exp((1 - R) × p[14])`
   - If nearly forgotten anyway (R low), less penalty
   - If should have remembered (R high), bigger penalty

**Example:**

```python
# Failed recall
S = 10 days
D = 5.0
R = 0.6 (starting to forget)
rating = 1 (Again)

S_next = 2.18 × (5.0^(-0.05)) × ((10 + 1)^0.34 - 1) × exp((1 - 0.6) × 1.26)
       ≈ 2.18 × 0.92 × 1.14 × 1.56
       ≈ 3.56 days
```

The stability drops from 10 days to ~3.5 days, requiring more frequent review.

---

## Difficulty Updates

Difficulty represents the inherent complexity of recalling a piece of knowledge.

### Initial Difficulty

For new cards:

**Formula:**
```
D_initial = min(max(p[4] - (rating - 3) × p[5], 1), 10)
```

**Values:**
- Rating = 1 (Again): D = 4.93 + 2×0.94 = 6.81
- Rating = 2 (Hard): D = 4.93 + 1×0.94 = 5.87
- Rating = 3 (Good): D = 4.93
- Rating = 4 (Easy): D = 4.93 - 1×0.94 = 3.99

Clamped to [1, 10] range.

### Difficulty Updates (Existing Cards)

**Formula:**
```
D_next = min(max(
    p[7] × p[4] + (1 - p[7]) × (D_current - p[6] × (rating - 3)),
    1
), 10)
```

**Components:**

1. **Baseline**: `p[7] × p[4]` where p[7] = 0.01, p[4] = 4.93
   - Small constant baseline: ~0.05
   - Prevents difficulty from dropping to zero

2. **Current Difficulty**: `(1 - p[7]) × D_current`
   - Weight = 0.99 (keeps most of current value)
   - Difficulty changes slowly

3. **Rating Adjustment**: `p[6] × (rating - 3)` where p[6] = 0.86
   - rating = 1 (Again): +1.72 (increases difficulty)
   - rating = 2 (Hard): +0.86
   - rating = 3 (Good): 0 (no change)
   - rating = 4 (Easy): -0.86 (decreases difficulty)

**Example:**

```python
# Current state
D = 5.0
rating = 4 (Easy)

# Calculate next difficulty
D_next = 0.01 × 4.93 + 0.99 × (5.0 - 0.86 × (4 - 3))
       = 0.05 + 0.99 × (5.0 - 0.86)
       = 0.05 + 0.99 × 4.14
       = 4.15

# Clamped to [1, 10]
D_next = 4.15
```

Difficulty decreases slightly when rated Easy, making future recalls easier.

---

## Sentiment Analysis

### Fast Mode Sentiment (TextBlob)

When using fast mode, sentiment is calculated using TextBlob's polarity score:

**Formula:**
```
sentiment = TextBlob(text).sentiment.polarity
```

**Range**: [-1.0, 1.0]
- `-1.0`: Extremely negative
- `0.0`: Neutral
- `1.0`: Extremely positive

**Relation Mapping:**

```python
if sentiment > 0.3:
    relation = "supports"
elif sentiment < -0.3:
    relation = "opposes"
elif sentiment > 0.1:
    relation = "likes"
elif sentiment < -0.1:
    relation = "dislikes"
else:
    relation = "discusses"
```

### LLM Mode Sentiment

When using LLM extraction, sentiment is provided in the JSON response:

```json
{
    "my_reaction": [
        {
            "relation": "support",
            "target": "UBI",
            "sentiment": 0.8
        }
    ]
}
```

The LLM is prompted to provide sentiment on the [-1.0, 1.0] scale.

---

## Query Algorithms

### Agent Stance Query

**Purpose**: Retrieve agent's beliefs about a topic.

**Algorithm:**

1. **Keyword Matching**: Find edges where target contains topic
2. **Recency Filter**: Include all edges from last 60 minutes
3. **Source Filter**: Only include agent's own statements (source="I" or agent name)
4. **Sort**: Most recent first
5. **Limit**: Top 8 results

**SQL:**
```sql
SELECT source, relation, target, sentiment 
FROM edges
WHERE owner_id = ?
  AND (source = 'I' OR source = ?)
  AND (
    target LIKE ?
    OR created_at >= datetime(?, '-60 minutes')
  )
ORDER BY created_at DESC
LIMIT 8
```

**Time Complexity**: O(log n) with index on (owner_id, created_at)

### World Knowledge Query

**Purpose**: Retrieve general facts about a topic.

**Algorithm:**

1. **Keyword Matching**: Find edges where source or target contains topic
2. **Source Filter**: Exclude agent's own statements
3. **Sort**: Most recent first
4. **Limit**: Configurable (default 10)

**SQL:**
```sql
SELECT source, relation, target
FROM edges
WHERE owner_id = ?
  AND source != 'I'
  AND source != ?
  AND (source LIKE ? OR target LIKE ?)
ORDER BY created_at DESC
LIMIT ?
```

**Time Complexity**: O(log n) with index on (owner_id, created_at)

### Memory View Construction

**Algorithm:**

1. Query agent stance (max 8 items)
2. Query world knowledge (max 10 items)
3. Format stance as sentences
4. Format world knowledge as sentences
5. Concatenate with headers
6. Return formatted string

**Pseudocode:**
```python
def get_memory_view(topic):
    stance = query_agent_stance(topic)
    world = query_world_knowledge(topic)
    
    # Format stance
    if stance:
        stance_text = "; ".join([
            f"{s} {r} {t}" for s, r, t in stance
        ])
    else:
        stance_text = "(I have no strong opinion yet)"
    
    # Format world knowledge
    if world:
        world_text = "; ".join([
            f"{s} {r} {t}" for s, r, t in world
        ])
    else:
        world_text = "(limited knowledge on this)"
    
    return f"MY CURRENT STANCE: {stance_text}. KNOWN FACTS: {world_text}."
```

---

## Computational Complexity

### Operation Complexities

| Operation | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| calculate_next | O(1) | O(1) |
| learn_triplet | O(log n) | O(1) |
| get_memory_view | O(log n + k) | O(k) |
| absorb (fast) | O(m) | O(m) |
| absorb (LLM) | O(LLM) | O(m) |
| query stance | O(log n) | O(1) |
| query world | O(log n) | O(1) |

Where:
- `n` = Number of edges in database
- `k` = Number of results returned
- `m` = Number of entities in text
- `LLM` = LLM inference time (varies)

### Storage Complexity

| Component | Space |
|-----------|-------|
| Node | ~100 bytes |
| Edge | ~150 bytes |
| Log entry | ~500 bytes |
| Agent (in-memory) | ~1 KB |

**Example Database Sizes:**

| Scenario | Nodes | Edges | Size |
|----------|-------|-------|------|
| Small (1 agent, 100 triplets) | 200 | 100 | ~40 KB |
| Medium (10 agents, 1000 triplets) | 2000 | 1000 | ~400 KB |
| Large (100 agents, 10000 triplets) | 20000 | 10000 | ~4 MB |

---

## Algorithm Optimizations

### FSRS Optimizations

1. **Pre-computed Constants**: exp(p[8]) calculated once
2. **Early Bailout**: Min/max clamping prevents invalid values
3. **Integer State**: State stored as int (0/1/2) not string

### Database Optimizations

1. **Indexes**: (owner_id, created_at) for time-based queries
2. **Prepared Statements**: Parameterized queries prevent SQL injection
3. **Batch Commits**: Multiple operations in single transaction

### Memory Optimizations

1. **Lazy Loading**: Agents loaded on-demand
2. **Connection Pooling**: Reuse SQLite connections
3. **Row Factory**: Efficient row-to-dict conversion

---

## Mathematical Properties

### Stability Properties

1. **Non-negative**: S ≥ 0.1 always
2. **Monotonic (success)**: S_next ≥ S when rating ≥ 2
3. **Bounded Growth**: Diminishing returns at high stability
4. **Reset on Failure**: S drops but doesn't reach zero

### Difficulty Properties

1. **Bounded**: 1 ≤ D ≤ 10
2. **Stable**: Changes slowly (weighted average)
3. **Converges**: Tends toward actual difficulty over time

### Retrievability Properties

1. **Bounded**: 0 ≤ R ≤ 1
2. **Decreasing**: R monotonically decreases with time
3. **Continuous**: Smooth decay curve
4. **Asymptotic**: Approaches zero but never reaches it

---

## References

### FSRS Algorithm

- [FSRS v4.5 Specification](https://github.com/open-spaced-repetition/fsrs4anki/wiki)
- Ye, L., et al. (2024). "A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling"

### Cognitive Psychology

- Ebbinghaus, H. (1885). "Memory: A Contribution to Experimental Psychology"
- Cepeda, N. J., et al. (2006). "Distributed practice in verbal recall tasks"
- Bjork, R. A., & Bjork, E. L. (1992). "A new theory of disuse and an old theory of stimulus fluctuation"

### Spaced Repetition

- Wozniak, P. A., & Gorzelańczyk, E. J. (1994). "Optimization of repetition spacing in the practice of learning"
- Pashler, H., et al. (2005). "When does feedback facilitate learning of words?"

---

## Summary

The algorithms in GhostKG combine:

1. **FSRS**: Sophisticated spaced repetition for realistic memory modeling
2. **Retrievability**: Continuous decay functions for forgetting
3. **Stability/Difficulty**: Dynamic properties that evolve with use
4. **Sentiment**: Emotional associations with knowledge
5. **Efficient Queries**: Optimized database access for fast retrieval

These algorithms enable GhostKG to model agent memory realistically while maintaining computational efficiency.
