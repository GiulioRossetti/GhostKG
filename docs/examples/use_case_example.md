# Multi-Agent Conversation

**Source:** `examples/use_case_example.py`

This is the most comprehensive example, demonstrating a complete multi-round conversation between two agents using LLM services for text generation and triplet extraction.

## Overview

Alice (a Denmark politician) and Bob (an American alt-right analyst) discuss Greenland. The example showcases:
- The `process_and_get_context()` atomic operation
- Both **Fast Mode** (GLiNER + TextBlob) and **LLM Mode** for triplet extraction
- LLM service integration (supports Ollama, OpenAI, Anthropic, etc.)
- Knowledge graph evolution across 10 conversation rounds

## Prerequisites

This example requires:
1. **An LLM service** - Choose one:
   - **Ollama** (local, free): `curl -fsSL https://ollama.com/install.sh | sh` then `ollama pull llama3.2`
   - **OpenAI** (commercial): Set `OPENAI_API_KEY` environment variable
   - **Anthropic** (commercial): Set `ANTHROPIC_API_KEY` environment variable

2. **Required packages**: `pip install ghost-kg`

**Optional for Fast Mode:**
- GLiNER: `pip install gliner`
- TextBlob: `pip install textblob`

## Configuration

At the top of the file, configure your LLM service:

```python
from ghost_kg.llm import get_llm_service

# Option 1: Ollama (local)
llm_service = get_llm_service("ollama", "llama3.2", host="http://localhost:11434")

# Option 2: OpenAI (commercial)
# llm_service = get_llm_service("openai", "gpt-4")

# Option 3: Anthropic (commercial)
# llm_service = get_llm_service("anthropic", "claude-3-opus-20240229")

# Choose extraction mode:
USE_FAST_MODE = False  # True for GLiNER+TextBlob, False for LLM extraction
```

## Step-by-Step Walkthrough

### Step 1: Initialize Manager and Create Agents

```python
from ghost_kg import AgentManager, Rating

DB_PATH = "use_case_example.db"
manager = AgentManager(db_path=DB_PATH)

alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")
```

Standard initialization - nothing new here.

### Step 2: Set Initial Time

```python
import datetime

current_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)
manager.set_agent_time("Bob", current_time)
```

Both agents start at Day 1, 09:00.

### Step 3: Initialize Agent Beliefs

```python
# Alice's beliefs
manager.learn_triplet("Alice", "I", "value", "Greenland", 
                      rating=Rating.Easy, sentiment=0.9)
manager.learn_triplet("Alice", "Greenland", "is_part_of", "Denmark", 
                      rating=Rating.Easy, sentiment=0.9)

# Bob's beliefs
manager.learn_triplet("Bob", "I", "know", "Greenland", 
                      rating=Rating.Easy, sentiment=0.8)
manager.learn_triplet("Bob", "United States", "must_buy", "Greenland", 
                      rating=Rating.Easy, sentiment=0.8)
```

Sets up opposing viewpoints to create an interesting conversation.

### Step 4: Triplet Extraction (LLM Mode)

When `USE_FAST_MODE = False`, the example uses an LLM service to extract structured knowledge:

```python
def extract_triplets(text: str, author: str):
    """Use LLM service to extract semantic triplets."""
    
    prompt = f"""
    Analyze this text by {author}: "{text}"
    
    Goal: Build a Semantic Knowledge Graph.
    
    CRITICAL: Extract MEANING, not grammar.
    - BAD:  "Bob" -> "noun" -> "climate"  
    - GOOD: "Bob" -> "emphasizes" -> "climate action"
    
    Return JSON with:
    - world_facts: Objective statements
    - partner_stance: What {author} believes
    """
    
    response = llm_service.chat(
        messages=[{"role": "user", "content": prompt}],
        model=LLM_MODEL,
        format="json"
    )
    
    data = json.loads(response["message"]["content"])
    # Parse and return triplets
```

**Why this matters:**
- LLMs can understand semantic relationships, not just keywords
- Extracts beliefs, intentions, and complex relationships
- Returns structured triplets: `(source, relation, target)`
- Works with any LLM provider (Ollama, OpenAI, Anthropic, etc.)

### Step 5: Fast Mode Alternative

When `USE_FAST_MODE = True`, GhostKG uses GLiNER for entity recognition:

```python
# In the main loop
if USE_FAST_MODE:
    triplets = None  # Let CognitiveLoop handle it internally
    context = manager.process_and_get_context(
        agent_name, topic, content,
        author=peer,
        triplets=None,
        fast_mode=True  # Triggers GLiNER + TextBlob
    )
```

**Fast Mode characteristics:**
- ~100x faster than LLM extraction
- Uses GLiNER for named entity recognition
- Uses TextBlob for sentiment analysis
- Good for real-time applications

### Step 6: The Atomic Operation

This is the **key feature** demonstrated:

```python
context = manager.process_and_get_context(
    "Bob",           # Agent processing the content
    "Greenland",     # Topic for context retrieval
    alice_message,   # Content to process
    author="Alice",  # Who sent it
    triplets=triplets,  # Extracted structure (or None for fast mode)
    fast_mode=USE_FAST_MODE
)
```

**What happens in one call:**
1. Updates Bob's knowledge graph with the content
2. Extracts triplets (if not provided)
3. Updates FSRS memory strength
4. Retrieves relevant context for replying

**Why atomic?** Ensures consistency - you can't retrieve context before updating, or forget to update after retrieving.

### Step 7: Generate Response with External LLM

```python
def external_llm_generate(agent_name: str, context: str, 
                          topic: str, profile: str) -> str:
    """Use LLM service to generate agent response."""
    
    prompt = f"""
    You are {agent_name}: {profile}. 
    Talking about {topic}.
    
    YOUR MEMORY: {context}
    
    Task: Write a short 1-sentence reply. 
    Prioritize YOUR STANCE.
    """
    
    response = llm_service.chat(
        messages=[{"role": "user", "content": prompt}],
        model=LLM_MODEL
    )
    
    return response["message"]["content"]
```

**Agent profiles:**
- Alice: "a Denmark politician"
- Bob: "an American alt-right geopolitical analyst supporting expansion"

These profiles guide the LLM to generate appropriate responses.
Works with any configured LLM provider.

### Step 8: Extract Response Triplets

After generating a response, extract what beliefs the agent expressed:

```python
def extract_response_triplets(text: str, agent_name: str):
    """Extract beliefs from agent's own statement."""
    
    prompt = f"""
    You are {agent_name}. You just said: "{text}"
    
    Extract the beliefs/stances YOU expressed.
    Relations must be active verbs (support, oppose, fear).
    
    Return JSON: 
    {{ "my_expressed_stances": [
        {{"relation": "verb", "target": "Entity", "sentiment": 0.5}}
    ]}}
    """
    
    # ... LLM service call and parsing
```

Returns tuples: `(relation, target, sentiment)`.
Works with any LLM provider.

### Step 9: Update with Response

```python
response_triplets = extract_response_triplets(bob_response, "Bob")

manager.update_with_response(
    "Bob",
    bob_response,
    triplets=response_triplets,
    context=context
)
```

Records Bob's new beliefs in his knowledge graph.

### Step 10: Multi-Round Loop

```python
num_rounds = 10

for round_num in range(1, num_rounds + 1):
    # Advance time
    current_time += timedelta(hours=1)
    
    # Determine responder (alternate between Alice and Bob)
    responding_agent = "Bob" if current_speaker == "Alice" else "Alice"
    
    # Set agent time
    manager.set_agent_time(responding_agent, current_time)
    
    # Process content atomically
    context = manager.process_and_get_context(...)
    
    # Generate response
    response = external_llm_generate(...)
    
    # Update with response
    manager.update_with_response(...)
    
    # Switch speaker
    current_speaker = responding_agent
```

## Conversation Flow Diagram

```
Round 1 (09:00):
Alice: "Greenland should remain part of Denmark..."
    ↓
Round 2 (10:00):
Bob reads Alice's message
  → Extracts triplets: (Alice, value, Denmark), (Greenland, part_of, Denmark)
  → Gets context: "I know Greenland. United States must_buy Greenland..."
  → Generates: "The strategic value of Greenland..."
  → Updates: (I, emphasize, strategic value)
    ↓
Round 3 (11:00):
Alice reads Bob's message
  → Process → Get context → Generate → Update
    ↓
... continues for 10 rounds
```

## Output Example

```
═══════════════════════════════════════════════
USE CASE: Two Agents Multi-Round Communication
═══════════════════════════════════════════════

⚙️  Configuration: Triplet Extraction Mode = LLM (Deep Semantic)

📋 Step 1: Create agents
  ✓ Created Alice
  ✓ Created Bob

⏰ Step 2: Set initial time
  ✓ Set time to Day 1, 09:00 (2025-01-01 09:00)

📝 Step 3: Initialize agent beliefs
  ✓ Alice thinks Greenland must be under Denmark
  ✓ Bob wants Greenland to become a new United States state

═══════════════════════════════════════════════
🗣️  CONVERSATION START
═══════════════════════════════════════════════

💬 Alice: I think Greenland should remain a part of Denmark...

───────────────────────────────────────────────────
🔄 ROUND 1/10
───────────────────────────────────────────────────

⏰ Time: Day 1, Hour 10:00

📥 Bob receives from Alice:
    Topic: 'Greenland'
    Text: 'I think Greenland should...'
  🤖 Using LLM mode - Extracted 3 triplets

🧠 Bob processes content and retrieves context...
  ✓ KG updated
  ✓ Context retrieved: MY CURRENT STANCE: I know Greenland...

🤖 Bob generates response using external LLM...
  ✓ Generated: 'The strategic value of Greenland cannot be understated...'

💾 Bob updates KG with own response...
  ✓ KG updated with 2 new beliefs

💬 Bob: The strategic value of Greenland cannot be understated...
```

## Key Features Demonstrated

1. **Atomic Operation**: `process_and_get_context()` ensures consistency
2. **Two Extraction Modes**: Fast (GLiNER) vs. LLM (semantic)
3. **External LLM Control**: Full flexibility in prompting and model choice
4. **Time Progression**: Realistic hourly intervals
5. **Knowledge Evolution**: Agents learn from each other over time
6. **Opposing Viewpoints**: Creates dynamic, interesting conversations

## Running the Example

```bash
# Option 1: With Ollama (local, free)
ollama serve  # Start Ollama server
ollama pull llama3.2  # Download model

# Option 2: With commercial LLM (OpenAI, Anthropic, etc.)
export OPENAI_API_KEY="sk-..."  # Set API key
# or
export ANTHROPIC_API_KEY="sk-ant-..."

# Run the example
cd examples
python use_case_example.py
```

**Runtime:** ~2-5 minutes for 10 rounds (depending on LLM speed)

## Customization

Change these variables to experiment:

```python
# LLM Service configuration
llm_service = get_llm_service("ollama", "llama3.2")  # Or "openai", "gpt-4"

# Number of conversation rounds
num_rounds = 10  # Try 3 for quick tests, 20 for longer conversations

# Extraction mode
USE_FAST_MODE = True  # True = fast, False = accurate

# Model selection
LLM_MODEL = "llama3.2"  # Or "gpt-4", "claude-3-opus-20240229", etc.

# LLM model
LLM_MODEL = "llama3.2"  # Or "llama3", "mistral", etc.

# Agent profiles
agent_profile = "a Denmark politician"  # Customize personalities
```

## Next Steps

- Try [External Program](external_program.md) for non-Ollama integration
- See [Temporal Simulation](hourly_simulation.md) for variable time gaps
- Read [Configuration Guide](../CONFIGURATION.md) for Fast Mode setup
