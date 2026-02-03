# GhostKG API Reference

## Overview

GhostKG provides a comprehensive API for building dynamic knowledge graph systems for LLM agents with built-in memory decay. This reference covers all exposed APIs and their usage.

**Key Features:**
1. **Manage multiple agents** with individual knowledge graphs
2. **Flexible triplet extraction** strategies (fast local or deep LLM-based)
3. **Multi-provider LLM support** (Ollama, OpenAI, Anthropic, Google, Cohere)
4. **Time-aware simulations** with datetime or round-based (day, hour) time
5. **Memory decay modeling** using FSRS spaced repetition
6. **External integration** API for custom LLM workflows

## Table of Contents

1. [Agent Management API](#agent-management-api) - Managing agents and knowledge graphs
2. [Triplet Extraction API](#triplet-extraction-api) - Fast and LLM-based extraction
3. [LLM Service API](#llm-service-api) - Multi-provider LLM integration
4. [Time Management API](#time-management-api) - Datetime and round-based time
5. [Memory System API](#memory-system-api) - FSRS and ratings
6. [Configuration API](#configuration-api) - System configuration

---

## 1. Agent Management API

The `AgentManager` class provides the main high-level API for managing multiple agents and their knowledge graphs.

### Import

```python
from ghost_kg import AgentManager
```

### Create AgentManager

```python
# Initialize with default SQLite database
manager = AgentManager(db_path="my_agents.db")

# Or with custom configuration
from ghost_kg import GhostKGConfig
config = GhostKGConfig()
manager = AgentManager(db_path="my_agents.db", config=config)
```

### Agent Operations

### Agent Operations

#### 1.1 Create or Get Agents

```python
# Create a new agent or get existing one
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")

# Get an existing agent
agent = manager.get_agent("Alice")
```

#### 1.2 Set Agent Time

Control time for simulations or tracking. Supports both **datetime objects** and **round-based (day, hour) tuples**.

**Option A: Using datetime objects**

```python
import datetime

current_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)

# Advance time
from datetime import timedelta
current_time += timedelta(hours=1)
manager.set_agent_time("Alice", current_time)
```

**Option B: Using round-based time (day, hour)**

Perfect for simulations where time is discretized:

```python
# Day 1, Hour 9 (09:00 on day 1)
manager.set_agent_time("Alice", (1, 9))

# Day 1, Hour 10  
manager.set_agent_time("Alice", (1, 10))

# Day 5, Hour 14
manager.set_agent_time("Alice", (5, 14))
```

**Constraints:**
- `day` must be >= 1
- `hour` must be in [0, 23]

See [Time Management API](#time-management-api) for more details.

#### 1.3 Absorb Content (Update KG with Input)

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

#### 1.4 Get Context for Reply

Retrieve all relevant context for an agent to reply about a topic:

```python
context = manager.get_context("Alice", topic="UBI")
# Returns: "MY CURRENT STANCE: I support ubi. KNOWN FACTS: automation affects jobs..."

# Use this context with your own LLM to generate a response
response = your_llm_api.generate(context, topic)
```

#### 1.5 Process Content and Get Context (Combined Operation)

**New in this update**: Atomic operation that updates KG and returns context:

```python
# Agent receives a (topic, text) tuple from a peer
topic = "climate change"
text = "Climate change requires urgent action"
author = "Bob"

# Extract triplets (external program responsibility)
triplets = [("Bob", "emphasizes", "urgency"), ("climate change", "requires", "action")]

# Update KG and get context in one call
context = manager.process_and_get_context(
    agent_name="Alice",
    topic=topic,
    text=text,
    author=author,
    triplets=triplets
)

# Use context with external LLM to generate response
response = your_llm_api.generate(context, topic)
```

This method is perfect for the common workflow where you:
1. Receive content from a peer
2. Update your KG with that content
3. Immediately need context to generate a response

#### 1.6 Update with Response

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

#### 1.7 Direct Triplet Learning

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

#### 1.8 Retrieve Agent Knowledge

Get the agent's knowledge graph:

```python
# Get all knowledge about a specific topic
knowledge = manager.get_agent_knowledge("Alice", topic="UBI")

print(knowledge["agent_beliefs"])    # What Alice believes
print(knowledge["world_knowledge"])  # What Alice knows about the world
```

## Complete Example: Specific Use Case

The following example demonstrates the complete workflow as specified in the use case:

```python
from ghost_kg import AgentManager, Rating
import datetime
from datetime import timedelta

# Initialize
manager = AgentManager(db_path="conversation.db")

# Create agents
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")

# Set initial time (Day 1, Hour 9)
current_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)
manager.set_agent_time("Bob", current_time)

# Initialize beliefs
manager.learn_triplet("Alice", "I", "care_about", "climate", rating=Rating.Easy, sentiment=0.9)
manager.learn_triplet("Bob", "I", "care_about", "economy", rating=Rating.Easy, sentiment=0.8)

# Multi-round conversation
topic = "climate change"
alice_says = "Climate change is urgent"

for round in range(3):
    # Advance time by 1 hour
    current_time += timedelta(hours=1)
    manager.set_agent_time("Bob", current_time)
    
    # Bob receives tuple (topic, text) from Alice
    content_tuple = (topic, alice_says)
    
    # Bob processes content and gets context (atomic operation)
    triplets = [("Alice", "emphasizes", "urgency")]  # External triplet extraction
    context = manager.process_and_get_context(
        "Bob", topic, alice_says, author="Alice", triplets=triplets
    )
    
    # Bob uses external LLM to generate response
    bob_response = your_llm.generate(context, topic)
    
    # Bob updates his KG with his response
    response_triplets = [("concerned_about", "costs", -0.3)]
    manager.update_with_response("Bob", bob_response, triplets=response_triplets)
    
    # Alice's turn (similar process)
    current_time += timedelta(hours=1)
    manager.set_agent_time("Alice", current_time)
    
    context = manager.process_and_get_context(
        "Alice", topic, bob_response, author="Bob", triplets=[("Bob", "mentions", "costs")]
    )
    alice_response = your_llm.generate(context, topic)
    manager.update_with_response("Alice", alice_response, triplets=[("support", "action", 0.8)])
    
    alice_says = alice_response  # Set for next round
```

See `examples/use_case_example.py` for a complete working implementation.

---

## 2. Triplet Extraction API

GhostKG provides two strategies for extracting knowledge triplets from text: **Fast Mode** (local, no LLM required) and **LLM Mode** (deep semantic extraction).

### Import

```python
from ghost_kg import FastExtractor, LLMExtractor, get_extractor
```

### 2.1 Fast Mode Extraction (GLiNER + VADER)

Fast mode uses **GLiNER** for entity extraction and **VADER** for sentiment analysis - no LLM required!

**Features:**
- ⚡ Very fast (~100 messages/second)
- 🔒 Works offline, no API calls
- 📦 Uses local models (GLiNER + VADER)
- 🎯 Good quality for most use cases

**Installation:**

```bash
pip install ghost-kg[fast]
# Or: pip install gliner vaderSentiment
```

**Usage:**

```python
from ghost_kg import FastExtractor

# Initialize (models load once, then cached)
extractor = FastExtractor()

# Extract triplets
result = extractor.extract(
    text="I strongly support UBI because automation will displace workers",
    author="Alice",
    agent_name="Bob"
)

# Result contains:
print(result["world_facts"])      # Objective triplets
print(result["partner_stance"])   # Author's beliefs
print(result["my_reaction"])      # Agent's reaction
print(result["sentiment"])        # Overall sentiment (-1.0 to 1.0)
print(result["entities"])         # Extracted entities
```

**How It Works:**
1. **GLiNER** extracts entities (Topics, People, Concepts, Organizations)
2. **VADER** analyzes sentiment (optimized for social/conversational text)
3. Heuristic rules map sentiment to relations (supports, opposes, discusses, etc.)
4. Entity-level sentiment analysis for nuanced understanding

**Example Output:**

```python
{
    "world_facts": [
        {"source": "UBI", "relation": "is", "target": "discussed"},
        {"source": "automation", "relation": "is", "target": "discussed"}
    ],
    "partner_stance": [
        {"source": "Alice", "relation": "strongly supports", "target": "UBI", "sentiment": 0.85},
        {"source": "Alice", "relation": "concerned about", "target": "automation", "sentiment": -0.3}
    ],
    "my_reaction": [
        {"source": "I", "relation": "interested in", "target": "UBI", "rating": 3, "sentiment": 0.42}
    ],
    "mode": "FAST",
    "sentiment": 0.67,
    "entities": ["UBI", "automation", "workers"]
}
```

### 2.2 LLM Mode Extraction

LLM mode uses a language model for deep semantic understanding.

**Features:**
- 🎯 High quality semantic extraction
- 🧠 Understands complex relationships
- 🌐 Supports multiple LLM providers
- 📊 Better for complex or nuanced text

**Usage:**

```python
from ghost_kg import LLMExtractor
from ghost_kg.llm import get_llm_service

# Create LLM service (see LLM Service API section)
llm_service = get_llm_service("ollama", "llama3.2")

# Initialize extractor
extractor = LLMExtractor(
    llm_service=llm_service,
    model="llama3.2",
    max_retries=3
)

# Extract triplets
result = extractor.extract(
    text="I think UBI is necessary",
    author="Alice",
    agent_name="Bob"
)
```

### 2.3 Factory Function

Use `get_extractor()` to automatically choose the appropriate extractor:

```python
from ghost_kg import get_extractor
from ghost_kg.llm import get_llm_service

# Fast mode
fast_extractor = get_extractor(fast_mode=True)

# LLM mode
llm_service = get_llm_service("openai", "gpt-4")
llm_extractor = get_extractor(
    fast_mode=False,
    llm_service=llm_service,
    model="gpt-4"
)
```

### 2.4 Comparison

| Feature | Fast Mode (GLiNER + VADER) | LLM Mode |
|---------|---------------------------|----------|
| **Speed** | ⚡ Very Fast (100 msg/s) | 🐌 Slower (1-5 msg/s) |
| **Quality** | ✓ Good | ✓✓ Excellent |
| **Offline** | ✓ Yes | ✗ Requires LLM |
| **Dependencies** | gliner, vaderSentiment | LLM service |
| **Cost** | Free | Varies by provider |
| **Best For** | High volume, demos | Research, accuracy-critical |

### 2.5 Integration with AgentManager

```python
from ghost_kg import AgentManager, get_extractor
from ghost_kg.llm import get_llm_service

# Option 1: Fast mode (automatic)
manager = AgentManager(db_path="agents.db")
# When you don't provide triplets, it won't extract automatically

# Option 2: Manual extraction with fast mode
extractor = get_extractor(fast_mode=True)
result = extractor.extract("Some text", "Author", "Agent")
triplets = result["partner_stance"]  # or world_facts, etc.
manager.absorb_content("Agent", "Some text", "Author", triplets=triplets)

# Option 3: Manual extraction with LLM mode
llm_service = get_llm_service("openai", "gpt-4")
extractor = get_extractor(fast_mode=False, llm_service=llm_service)
result = extractor.extract("Some text", "Author", "Agent")
```

---

## 3. LLM Service API

GhostKG provides a unified interface for multiple LLM providers: Ollama (local), OpenAI, Anthropic, Google, and Cohere.

### Import

```python
from ghost_kg.llm import get_llm_service, LLMServiceBase
```

### 3.1 Supported Providers

**Local:**
- **Ollama**: Run models locally (Llama, Mistral, Gemma, etc.)

**Commercial (via LangChain):**
- **OpenAI**: GPT-4, GPT-3.5, etc.
- **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
- **Google**: Gemini Pro
- **Cohere**: Command models

### 3.2 Installation

```bash
# Base installation
pip install ghost-kg

# With Ollama support
pip install ghost-kg[llm]

# With commercial providers
pip install ghost-kg[langchain-openai]    # OpenAI
pip install ghost-kg[langchain-anthropic] # Anthropic
pip install ghost-kg[langchain-google]    # Google
pip install ghost-kg[langchain-cohere]    # Cohere
pip install ghost-kg[langchain-all]       # All providers
```

### 3.3 API Keys

Set API keys as environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export COHERE_API_KEY="..."
```

### 3.4 Creating LLM Services

#### Ollama (Local)

```python
from ghost_kg.llm import get_llm_service

# Default: localhost:11434
llm = get_llm_service("ollama", "llama3.2")

# Custom host
llm = get_llm_service(
    "ollama", 
    "llama3.2",
    base_url="http://192.168.1.100:11434"
)
```

#### OpenAI

```python
# Uses OPENAI_API_KEY from environment
llm = get_llm_service("openai", "gpt-4")

# Or pass API key directly
llm = get_llm_service(
    "openai", 
    "gpt-4",
    api_key="sk-..."
)
```

#### Anthropic (Claude)

```python
# Uses ANTHROPIC_API_KEY from environment
llm = get_llm_service("anthropic", "claude-3-opus-20240229")

# With custom parameters
llm = get_llm_service(
    "anthropic",
    "claude-3-sonnet-20240229",
    temperature=0.7,
    max_tokens=1000
)
```

#### Google (Gemini)

```python
# Uses GOOGLE_API_KEY from environment
llm = get_llm_service("google", "gemini-pro")
```

#### Cohere

```python
# Uses COHERE_API_KEY from environment
llm = get_llm_service("cohere", "command")
```

### 3.5 Using LLM Services

All services provide a unified `.chat()` interface:

```python
# Works with any provider
response = llm.chat(
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response["message"]["content"])

# With system message
response = llm.chat(
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "What is UBI?"}
    ]
)

# With options (provider-specific)
response = llm.chat(
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7,
    max_tokens=500
)
```

### 3.6 Integration with Extraction

```python
from ghost_kg.llm import get_llm_service
from ghost_kg import LLMExtractor

# Create any LLM service
llm_service = get_llm_service("openai", "gpt-4")
# Or: llm_service = get_llm_service("anthropic", "claude-3-opus-20240229")
# Or: llm_service = get_llm_service("ollama", "llama3.2")

# Use with extractor
extractor = LLMExtractor(llm_service=llm_service)

result = extractor.extract("Some text", "Author", "Agent")
```

### 3.7 Provider Recommendations

| Use Case | Recommended Provider | Model |
|----------|---------------------|-------|
| Development/Testing | Ollama | llama3.2 |
| Production Quality | OpenAI | gpt-4 |
| Best Quality | Anthropic | claude-3-opus-20240229 |
| Balanced Cost/Quality | Anthropic | claude-3-sonnet-20240229 |
| Privacy/Security | Ollama | llama3.2 (local) |
| Low Cost | OpenAI | gpt-3.5-turbo |

### 3.8 Error Handling

```python
from ghost_kg.llm import get_llm_service
from ghost_kg.utils import LLMError

try:
    llm = get_llm_service("openai", "gpt-4")
    response = llm.chat(messages=[{"role": "user", "content": "Hello!"}])
except ImportError as e:
    print(f"Provider package not installed: {e}")
except ValueError as e:
    print(f"Invalid configuration: {e}")
except LLMError as e:
    print(f"LLM request failed: {e}")
```

---

## 4. Time Management API

GhostKG supports two time representations: **datetime objects** (absolute time) and **round-based tuples** (day, hour) for simulations.

### Import

```python
from ghost_kg import SimulationTime, parse_time_input
import datetime
```

### 4.1 DateTime Mode

Use standard Python datetime objects:

```python
import datetime

# Create time
current_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)

# With AgentManager
manager.set_agent_time("Alice", current_time)

# Advance time
from datetime import timedelta
current_time += timedelta(hours=1)
manager.set_agent_time("Alice", current_time)

# Or with GhostAgent directly
from ghost_kg import GhostAgent
agent = GhostAgent("Alice", db_path="agent.db")
agent.set_time(current_time)
```

### 4.2 Round-Based Mode

Use (day, hour) tuples for discrete simulations:

```python
# Set time to Day 1, Hour 9 (09:00)
manager.set_agent_time("Alice", (1, 9))

# Advance to Day 1, Hour 10
manager.set_agent_time("Alice", (1, 10))

# Jump to Day 5, Hour 14
manager.set_agent_time("Alice", (5, 14))

# Or with GhostAgent
agent.set_time((1, 9))
```

**Constraints:**
- `day` must be >= 1 (no day 0)
- `hour` must be in [0, 23]

### 4.3 SimulationTime Class

For advanced time handling:

```python
from ghost_kg import SimulationTime

# Create from datetime
dt = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
sim_time = SimulationTime.from_datetime(dt)

# Create from round
sim_time = SimulationTime.from_round(day=5, hour=14)

# Or direct construction
sim_time = SimulationTime(day=5, hour=14)
sim_time = SimulationTime(datetime_value=dt)

# Check mode
if sim_time.is_datetime_mode():
    print(f"Using datetime: {sim_time.to_datetime()}")
elif sim_time.is_round_mode():
    day, hour = sim_time.to_round()
    print(f"Using round: Day {day}, Hour {hour}")
```

### 4.4 parse_time_input Helper

Parse various time formats:

```python
from ghost_kg import parse_time_input

# All of these work:
time1 = parse_time_input((5, 14))  # Tuple
time2 = parse_time_input(datetime.datetime.now())  # Datetime
time3 = parse_time_input(SimulationTime.from_round(5, 14))  # SimulationTime

# Use with agent
agent.set_time(parse_time_input((1, 9)))
```

### 4.5 Time in Database

Time is stored in the database with both formats:

```sql
-- For datetime mode
SELECT * FROM nodes WHERE created_at > '2025-01-01 09:00:00';

-- For round-based mode  
SELECT * FROM nodes WHERE sim_day = 5 AND sim_hour >= 14;
```

### 4.6 Use Cases

**DateTime mode is best for:**
- Real-world simulations
- Historical analysis
- Integration with external time systems
- Variable time gaps (minutes, hours, days)

**Round-based mode is best for:**
- Turn-based games
- Discrete simulation models
- Deterministic testing
- Simple time progression

---

## 5. Memory System API

GhostKG uses FSRS (Free Spaced Repetition Scheduler) for memory decay modeling.

### Import

```python
from ghost_kg import Rating, FSRS
```

### 5.1 Rating Enum

Control memory strength when learning triplets:

```python
from ghost_kg import Rating

Rating.Again = 1  # Failed to recall - memory weakens
Rating.Hard = 2   # Difficult to recall - small strength increase
Rating.Good = 3   # Normal recall - medium strength increase (default)
Rating.Easy = 4   # Easy to recall - large strength increase
```

**Usage:**

```python
# Strong memory (easy to remember)
manager.learn_triplet("Alice", "I", "support", "UBI", rating=Rating.Easy, sentiment=0.8)

# Normal memory
manager.learn_triplet("Alice", "UBI", "helps", "workers", rating=Rating.Good, sentiment=0.5)

# Weak memory (hard to remember)
manager.learn_triplet("Alice", "details", "about", "implementation", rating=Rating.Hard, sentiment=0.0)
```

### 5.2 FSRS Algorithm

GhostKG automatically handles memory decay using FSRS:

**Key Concepts:**
- **Stability (S)**: How long a memory lasts
- **Retrievability (R)**: Probability of recall at current time
- **Difficulty (D)**: How hard the concept is to remember

**Decay Formula:**

```
R(t) = (1 + t / (9S))^(-1)
```

Where:
- `R(t)` = retrievability at time t
- `t` = elapsed time since last review (in days)
- `S` = stability (memory strength)

**Automatic Updates:**
- Each time a memory is reviewed, stability increases
- The longer between reviews, the more retrievability decreases
- Stronger memories (high stability) last longer

### 5.3 Advanced: FSRS Configuration

```python
from ghost_kg import FSRSConfig, GhostKGConfig

# Custom FSRS parameters
fsrs_config = FSRSConfig(
    w=[0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61],
    request_retention=0.9,  # Target 90% retention
    maximum_interval=36500,  # Max 100 years
    enable_fuzz=False
)

# Use with AgentManager
config = GhostKGConfig(fsrs=fsrs_config)
manager = AgentManager(db_path="agents.db", config=config)
```

---

## 6. Configuration API

### Import

```python
from ghost_kg import (
    GhostKGConfig,
    FSRSConfig,
    DatabaseConfig,
    LLMConfig,
    FastModeConfig
)
```

### 6.1 GhostKGConfig

Main configuration class:

```python
from ghost_kg import GhostKGConfig

# Default configuration
config = GhostKGConfig()

# Custom configuration
config = GhostKGConfig(
    fsrs=FSRSConfig(...),
    database=DatabaseConfig(...),
    llm=LLMConfig(...),
    fast_mode=FastModeConfig(...)
)

# Use with AgentManager
manager = AgentManager(db_path="agents.db", config=config)
```

### 6.2 FSRSConfig

```python
from ghost_kg import FSRSConfig

config = FSRSConfig(
    w=[...],  # FSRS weights (17 parameters)
    request_retention=0.9,  # Target retention rate
    maximum_interval=36500,  # Max interval in days
    enable_fuzz=False  # Disable interval fuzziness
)
```

### 6.3 DatabaseConfig

```python
from ghost_kg import DatabaseConfig

config = DatabaseConfig(
    db_type="sqlite",  # or "postgresql", "mysql"
    connection_string="path/to/db.sqlite",
    pool_size=5,
    max_overflow=10
)
```

### 6.4 LLMConfig

```python
from ghost_kg import LLMConfig

config = LLMConfig(
    provider="ollama",  # or "openai", "anthropic", etc.
    model="llama3.2",
    api_key=None,  # Or your API key
    base_url="http://localhost:11434"
)
```

### 6.5 FastModeConfig

```python
from ghost_kg import FastModeConfig

config = FastModeConfig(
    gliner_model="urchade/gliner_small-v2.1",
    entity_labels=["Topic", "Person", "Concept", "Organization"]
)
```

---

## Complete Example: Multi-Round Conversation

This example demonstrates the complete workflow with fast extraction and LLM service:

```python
from ghost_kg import AgentManager, Rating, get_extractor
from ghost_kg.llm import get_llm_service
import datetime
from datetime import timedelta

# 1. Initialize
manager = AgentManager(db_path="conversation.db")

# 2. Create LLM service (choose any provider)
llm_service = get_llm_service("openai", "gpt-4")
# Or: llm_service = get_llm_service("ollama", "llama3.2")

# 3. Create extractor (fast mode for this example)
extractor = get_extractor(fast_mode=True)

# 4. Create agents
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")

# 5. Set initial time
current_time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)
manager.set_agent_time("Bob", current_time)

# 6. Initialize beliefs
manager.learn_triplet("Alice", "I", "support", "UBI", rating=Rating.Easy, sentiment=0.8)
manager.learn_triplet("Bob", "I", "oppose", "UBI", rating=Rating.Easy, sentiment=-0.7)

# 7. Multi-round conversation
topic = "UBI"
alice_says = "I think UBI is necessary because automation will take jobs."

for round_num in range(3):
    print(f"\n=== Round {round_num + 1} ===")
    
    # Bob's turn
    current_time += timedelta(hours=1)
    manager.set_agent_time("Bob", current_time)
    
    # Extract triplets from Alice's message
    extraction = extractor.extract(alice_says, "Alice", "Bob")
    triplets = extraction["partner_stance"]
    
    # Bob absorbs content and gets context
    context = manager.process_and_get_context(
        "Bob", topic, alice_says, author="Alice", triplets=triplets
    )
    
    # Generate Bob's response with LLM
    response = llm_service.chat(
        messages=[
            {"role": "system", "content": f"You are Bob. Context: {context}"},
            {"role": "user", "content": f"Respond to Alice about {topic}"}
        ]
    )
    bob_says = response["message"]["content"]
    
    # Extract triplets from Bob's response and update his KG
    bob_extraction = extractor.extract(bob_says, "Bob", "Bob")
    bob_triplets = [(t["relation"], t["target"], t.get("sentiment", 0.0)) 
                    for t in bob_extraction["my_reaction"]]
    manager.update_with_response("Bob", bob_says, triplets=bob_triplets)
    
    print(f"Bob: {bob_says}")
    
    # Alice's turn (similar process)
    current_time += timedelta(hours=1)
    manager.set_agent_time("Alice", current_time)
    
    extraction = extractor.extract(bob_says, "Bob", "Alice")
    context = manager.process_and_get_context(
        "Alice", topic, bob_says, author="Bob", triplets=extraction["partner_stance"]
    )
    
    response = llm_service.chat(
        messages=[
            {"role": "system", "content": f"You are Alice. Context: {context}"},
            {"role": "user", "content": f"Respond to Bob about {topic}"}
        ]
    )
    alice_says = response["message"]["content"]
    
    alice_extraction = extractor.extract(alice_says, "Alice", "Alice")
    alice_triplets = [(t["relation"], t["target"], t.get("sentiment", 0.0))
                      for t in alice_extraction["my_reaction"]]
    manager.update_with_response("Alice", alice_says, triplets=alice_triplets)
    
    print(f"Alice: {alice_says}")

print("\n✓ Conversation complete!")
```

---

## Sentiment Scores

Sentiment is used to track emotional associations:

- `-1.0` to `-0.5`: Strong negative sentiment
- `-0.5` to `0.0`: Mild negative sentiment  
- `0.0`: Neutral
- `0.0` to `0.5`: Mild positive sentiment
- `0.5` to `1.0`: Strong positive sentiment

---

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
