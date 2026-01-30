# GhostKG External API Documentation

## Overview

GhostKG can now be used as a library by external programs to manage agent Knowledge Graphs (KGs) without handling the internal LLM logic. This allows you to:

1. **Manage multiple agents** with individual KGs
2. **Update agent KGs** with content they are replying to
3. **Retrieve context** for generating responses on a topic
4. **Update KGs** with generated responses
5. **Control time** for each interaction (for simulation or tracking)

## Key Components

### AgentManager

The `AgentManager` class provides the main API for external programs to interact with agent KGs.

```python
from ghost_kg import AgentManager

# Initialize the manager
manager = AgentManager(db_path="my_agents.db")
```

## Core Operations

### 1. Create/Get Agents

```python
# Create a new agent or get existing one
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")

# Get an existing agent
agent = manager.get_agent("Alice")
```

### 2. Set Agent Time

For simulation or time-tracking purposes:

```python
import datetime

current_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)
```

### 3. Absorb Content (Update KG with Input)

When an agent receives content, update their KG:

**Option A: Provide your own triplet extraction**

```python
# External program extracts triplets
triplets = [
    ("Bob", "mentions", "automation"),
    ("automation", "affects", "jobs"),
    ("UBI", "provides", "safety net")
]

manager.absorb_content(
    agent_name="Alice",
    content="Bob mentioned that automation affects jobs and UBI provides a safety net.",
    author="Bob",
    triplets=triplets
)
```

**Option B: Let GhostKG extract triplets (requires LLM)**

```python
manager.absorb_content(
    agent_name="Alice",
    content="Bob mentioned that automation affects jobs.",
    author="Bob"
    # No triplets parameter - will use internal LLM to extract
)
```

### 4. Get Context for Reply

Retrieve all relevant context for an agent to reply about a topic:

```python
context = manager.get_context("Alice", topic="UBI")
# Returns: "MY CURRENT STANCE: I support ubi. KNOWN FACTS: automation affects jobs..."

# Use this context with your own LLM to generate a response
response = your_llm_api.generate(context, topic)
```

### 5. Update with Response

After generating a response, update the agent's KG with what they said:

**Option A: Provide your own triplet extraction with sentiment**

```python
# External program extracts triplets from response
triplets = [
    ("support", "UBI", 0.8),  # (relation, target, sentiment)
    ("value", "safety net", 0.7)
]

manager.update_with_response(
    agent_name="Alice",
    response="I support UBI because it provides a safety net.",
    triplets=triplets
)
```

**Option B: Let GhostKG reflect on response (requires LLM)**

```python
manager.update_with_response(
    agent_name="Alice",
    response="I support UBI because it provides a safety net."
    # No triplets parameter - will use internal LLM to reflect
)
```

### 6. Direct Triplet Learning

Directly add triplets to an agent's KG:

```python
from ghost_kg import Rating

manager.learn_triplet(
    agent_name="Alice",
    source="I",
    relation="support",
    target="UBI",
    rating=Rating.Easy,  # 1-4 scale for spaced repetition
    sentiment=0.8        # -1.0 (negative) to 1.0 (positive)
)
```

### 7. Retrieve Agent Knowledge

Get the agent's knowledge graph:

```python
# Get all knowledge about a specific topic
knowledge = manager.get_agent_knowledge("Alice", topic="UBI")

print(knowledge["agent_beliefs"])    # What Alice believes
print(knowledge["world_knowledge"])  # What Alice knows about the world
```

## Complete Example: External Program Integration

```python
from ghost_kg import AgentManager, Rating
import datetime

# 1. Initialize
manager = AgentManager(db_path="my_simulation.db")

# 2. Create agents
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")

# 3. Set time
sim_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", sim_time)
manager.set_agent_time("Bob", sim_time)

# 4. Initialize beliefs
manager.learn_triplet("Alice", "I", "support", "UBI", rating=Rating.Easy, sentiment=0.8)
manager.learn_triplet("Bob", "I", "oppose", "UBI", rating=Rating.Easy, sentiment=-0.7)

# 5. Simulate conversation
content = "I think UBI is necessary."

# Bob processes Alice's content
triplets = [("Alice", "thinks", "UBI necessary")]
manager.absorb_content("Bob", content, author="Alice", triplets=triplets)

# Bob generates response (using your LLM)
context = manager.get_context("Bob", topic="UBI")
bob_response = your_llm.generate(context, topic="UBI")

# Update Bob's KG with his response
response_triplets = [("concerned_about", "UBI", -0.5)]
manager.update_with_response("Bob", bob_response, triplets=response_triplets)
```

## Ratings (FSRS Spaced Repetition)

The system uses spaced repetition to model memory decay:

```python
from ghost_kg import Rating

Rating.Again = 1  # Failed to recall
Rating.Hard = 2   # Difficult to recall
Rating.Good = 3   # Normal recall (default)
Rating.Easy = 4   # Easy to recall
```

## Time Management

Time is crucial for memory simulation:

```python
import datetime
from datetime import timedelta

# Set current time
current_time = datetime.datetime.now(datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)

# Advance time
current_time += timedelta(hours=1)
manager.set_agent_time("Alice", current_time)
```

## Sentiment Scores

Sentiment is used to track emotional associations:

- `-1.0` to `-0.5`: Strong negative sentiment
- `-0.5` to `0.0`: Mild negative sentiment  
- `0.0`: Neutral
- `0.0` to `0.5`: Mild positive sentiment
- `0.5` to `1.0`: Strong positive sentiment

## Architecture

```
External Program (Your Code)
    │
    ├── Business Logic (agent communication flow)
    ├── LLM Integration (GPT-4, Claude, etc.)
    ├── Triplet Extraction (NLP/LLM-based)
    │
    └── GhostKG API (AgentManager)
            │
            ├── Agent Management
            ├── Knowledge Graph Storage
            ├── Memory Decay (FSRS)
            └── Context Retrieval
```

## Benefits of This Approach

1. **Flexibility**: Use any LLM provider (OpenAI, Anthropic, local models, etc.)
2. **Control**: Full control over conversation flow and business logic
3. **Separation of Concerns**: KG management separate from text generation
4. **Scalability**: Manage multiple agents with separate KGs
5. **Time Awareness**: Built-in support for temporal simulation

## Backward Compatibility

The original `GhostAgent` and `CognitiveLoop` classes are still available for users who want the integrated LLM approach:

```python
from ghost_kg import GhostAgent, CognitiveLoop

agent = GhostAgent("Alice", db_path="agent.db")
loop = CognitiveLoop(agent)

# Old style - uses internal Ollama LLM
loop.absorb("Some content", author="Bob")
response = loop.reply("topic", partner_name="Bob")
```

## See Also

- `examples/external_program.py` - Complete working example
- `examples/hourly_simulation.py` - Original integrated LLM example
