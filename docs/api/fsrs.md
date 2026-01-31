# FSRS API

The `FSRS` (Free Spaced Repetition Scheduler) class implements the FSRS v6 algorithm for memory modeling and spaced repetition.

## Module Location

```python
# Recommended: Import from top-level package
from ghost_kg import FSRS, Rating

# Also supported: Import from subpackage
from ghost_kg.memory import FSRS, Rating
```

## Overview

FSRS is a sophisticated spaced repetition algorithm that models memory retention and forgetting curves. It's used by GhostKG to:

- Track memory strength (stability) of knowledge
- Calculate forgetting curves
- Determine optimal review intervals
- Update memory states based on recall performance

## Key Concepts

### Memory States

- **Stability (S)**: How well information is retained over time
- **Difficulty (D)**: How hard the information is to recall (0-10 scale)
- **Retrievability (R)**: Current probability of recall based on elapsed time

### Ratings

The `Rating` enum defines recall performance:

```python
class Rating:
    Again = 1  # Failed to recall
    Hard = 2   # Difficult recall
    Good = 3   # Normal recall
    Easy = 4   # Easy recall
```

## Basic Usage

```python
from ghost_kg import FSRS, Rating
from ghost_kg.storage import NodeState
import datetime

# Initialize FSRS
fsrs = FSRS()

# New card state
initial_state = NodeState(
    stability=0,
    difficulty=0,
    last_review=None,
    reps=0,
    state=0
)

# Calculate next state after review
now = datetime.datetime.now(datetime.timezone.utc)
next_state = fsrs.calculate_next(initial_state, Rating.Good, now)

print(f"New stability: {next_state.stability:.2f}")
print(f"New difficulty: {next_state.difficulty:.2f}")
print(f"Retrievability: {next_state.retrievability:.2f}")
```

## Memory States

| State | Meaning |
|-------|---------|
| 0 | New (never reviewed) |
| 1 | Learning (being learned) |
| 2 | Review (established in memory) |
| 3 | Relearning (forgotten, being relearned) |

## Forgetting Curve

The retrievability (probability of recall) decays exponentially over time with trainable decay:

```
R(t) = (1 + factor × t / S)^(-w_20)
```

Where:
- R(t) = retrievability at time t
- t = time elapsed since last review
- S = stability (time until 90% retrievability)
- w_20 = trainable decay parameter (default: 0.1542)
- factor = 0.9^(-1/w_20) - 1 (ensures R(S,S) = 90%)

## API Reference

::: ghost_kg.fsrs.FSRS
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: ghost_kg.fsrs.Rating
    options:
      show_root_heading: true
      show_source: false
      heading_level: 3
