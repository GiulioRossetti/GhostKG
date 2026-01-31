# External Program Integration

**Source:** `examples/external_program.py`

This example demonstrates how to integrate GhostKG with an external application that uses its own LLM (like GPT-4, Claude, or any other LLM service). GhostKG handles knowledge graph management while your program handles all the LLM interactions.

## Overview

The example simulates a conversation between two agents (Alice and Bob) discussing Universal Basic Income (UBI). The key difference from other examples is that:
- **Your program controls everything**: LLM calls, triplet extraction, conversation flow
- **GhostKG only manages knowledge**: Stores triplets, tracks memory strength, provides context

This pattern is ideal when you want full control over your LLM provider and prompting strategy.

## Step-by-Step Walkthrough

### Step 1: Initialize the Manager

```python
from ghost_kg import AgentManager, Rating

DB_PATH = "external_program_example.db"
manager = AgentManager(db_path=DB_PATH)
```

The `AgentManager` is your main interface to GhostKG. It manages multiple agents and their knowledge graphs stored in a SQLite database.

### Step 2: Create Agents

```python
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")
```

Creates two agents with separate knowledge graphs in the same database.

### Step 3: Set Simulation Time

```python
import datetime

sim_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", sim_time)
manager.set_agent_time("Bob", sim_time)
```

**Why this matters:** GhostKG uses FSRS (spaced repetition) to model memory decay. Each agent has its own simulation clock to track when they learned or reviewed information.

### Step 4: Seed Initial Beliefs

```python
manager.learn_triplet(
    "Alice", "I", "support", "UBI", 
    rating=Rating.Easy, 
    sentiment=0.8
)

manager.learn_triplet(
    "Bob", "I", "oppose", "UBI", 
    rating=Rating.Easy, 
    sentiment=-0.7
)
```

**What's happening:**
- Creates triplets in each agent's knowledge graph
- `"I"` is a special node representing the agent themselves
- `rating` controls initial memory strength (Easy = strong memory)
- `sentiment` tracks emotional association (-1.0 to 1.0)

### Step 5: External Triplet Extraction

The example includes helper functions that simulate triplet extraction:

```python
def extract_triplets_from_content(content: str, author: str):
    """
    Simulate external triplet extraction from content.
    In production, call your own NLP model or LLM.
    """
    triplets = []
    
    if "automation" in content.lower():
        triplets.append((author, "mentions", "automation"))
        triplets.append(("automation", "affects", "jobs"))
    
    # ... more extraction logic
    return triplets
```

**In production**, you would:
- Call GPT-4 with a prompt to extract structured information
- Use a dedicated NER/relation extraction model
- Parse the content with your own business logic

### Step 6: Process Incoming Content

```python
# Agent reads content from another agent
triplets = extract_triplets_from_content(last_content, last_author)

# Update knowledge graph with what was read
manager.absorb_content(
    "Bob",               # Who is reading
    last_content,        # What they read
    author=last_author,  # Who wrote it
    triplets=triplets    # Extracted structured info
)
```

**What `absorb_content` does:**
1. Adds the extracted triplets to Bob's knowledge graph
2. Updates memory strength using FSRS based on current time
3. Records who said what

### Step 7: Get Context for Response

```python
context = manager.get_context("Bob", topic)
```

**Returns**: A formatted string containing:
- Bob's personal beliefs about the topic
- World facts Bob knows
- What other agents have said

**Example output:**
```
MY CURRENT STANCE: I oppose UBI. 
KNOWN FACTS: automation affects jobs; UBI provides safety net.
WHAT OTHERS THINK: Alice mentions automation.
```

### Step 8: Generate Response with External LLM

```python
def simulate_llm_response(context: str, topic: str, agent_name: str) -> str:
    """
    In production, this would call your LLM service:
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"You are {agent_name}"},
            {"role": "user", "content": f"Context: {context}\n\nRespond about {topic}"}
        ]
    )
    return response.choices[0].message.content
    """
    # Simulation for demo purposes
    if agent_name == "Alice":
        return "I believe UBI could provide a safety net..."
    else:
        return "I'm concerned that UBI might discourage..."
```

**Key point:** You control the LLM interaction completely. Use any provider, any model, any prompting strategy.

### Step 9: Update with Agent's Own Response

```python
# Extract beliefs from agent's response
response_triplets = extract_triplets_from_response(bob_response)

# Update agent's knowledge with their own beliefs
manager.update_with_response(
    "Bob",
    bob_response,
    triplets=response_triplets,
    context=context
)
```

**What this does:**
- Records Bob's new beliefs/statements in his knowledge graph
- Uses special formatting: `("relation", "target", sentiment)` tuples
- Updates memory strength based on review

### Step 10: Advance Time and Repeat

```python
from datetime import timedelta

sim_time += timedelta(hours=1)
manager.set_agent_time("Bob", sim_time)
```

**Why advancing time matters:**
- FSRS uses time to calculate memory decay
- Longer gaps = more forgotten information
- More recent reviews = stronger memories

## Complete Conversation Flow

```
1. Alice starts: "I think UBI is necessary..."
   ↓
2. Time +1 hour → Bob's turn
   - Bob absorbs Alice's message
   - Extract triplets from it
   - Get Bob's context
   - Generate Bob's response with external LLM
   - Update Bob's KG with his response
   ↓
3. Time +2 hours → Alice's turn
   - Alice absorbs Bob's message
   - ... (repeat process)
```

## Key Takeaways

1. **Separation of Concerns**: GhostKG handles knowledge management, your code handles LLM interactions
2. **Full Control**: Choose any LLM provider, any extraction method, any prompting strategy
3. **Time Awareness**: Memory strength degrades naturally over time using FSRS
4. **Flexible Integration**: Easy to integrate into existing applications

## Running the Example

```bash
cd examples
python external_program.py
```

**Expected output:**
- Initialization messages
- Multi-round conversation between Alice and Bob
- Final knowledge graphs for both agents
- Database file `external_program_example.db` created

## Next Steps

- See [Multi-Agent Conversation](use_case_example.md) for using Ollama integration
- See [Temporal Simulation](hourly_simulation.md) for realistic time gaps
- Read [API Documentation](../API.md) for complete API reference
