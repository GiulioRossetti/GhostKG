# GhostKG Core Components

This document provides detailed information about each core component in the GhostKG system.

## Table of Contents

1. [FSRS Memory System](#fsrs-memory-system)
2. [NodeState](#nodestate)
3. [GhostAgent](#ghostagent)
4. [CognitiveLoop](#cognitiveloop)
5. [KnowledgeDB](#knowledgedb)
6. [AgentManager](#agentmanager)

---

## FSRS Memory System

### Overview

FSRS (Free Spaced Repetition Scheduler) v6 is the memory modeling algorithm at the heart of GhostKG. It determines how well agents remember information over time.

### Class: `FSRS`

**Location**: `ghost_kg/memory/fsrs.py`

**Purpose**: Calculate memory retention and forgetting curves for knowledge nodes.

### Parameters

The FSRS-6 algorithm uses 21 parameters (p[0] through p[20]):

```python
self.p = [
    0.212,   # p[0] - Initial stability for Rating.Again
    1.2931,  # p[1] - Initial stability for Rating.Hard
    2.3065,  # p[2] - Initial stability for Rating.Good
    8.2956,  # p[3] - Initial stability for Rating.Easy
    6.4133,  # p[4] - Initial difficulty baseline
    0.8334,  # p[5] - Difficulty exponential factor
    3.0194,  # p[6] - Difficulty linear damping factor
    0.001,   # p[7] - Mean reversion weight to D_0(4)
    1.8722,  # p[8] - Stability growth factor
    0.1666,  # p[9] - Stability decay exponent
    0.796,   # p[10] - Retrievability impact
    1.4835,  # p[11] - Again stability multiplier
    0.0614,  # p[12] - Again difficulty exponent
    0.2629,  # p[13] - Again state exponent
    1.6483,  # p[14] - Again retrievability factor
    0.6014,  # p[15] - Hard penalty
    1.8729,  # p[16] - Easy bonus
    0.5425,  # p[17] - Same-day review growth rate
    0.0912,  # p[18] - Same-day review rating adjustment
    0.0658,  # p[19] - Same-day review stability damping
    0.1542,  # p[20] - Trainable decay parameter
]
```

### Key Concepts

#### 1. Stability (S)

**Definition**: How long (in days) the agent can remember this knowledge before retrievability drops to 90%.

**Range**: [0.1, ∞)

**Interpretation**:
- Low stability (< 1 day): Easily forgotten
- Medium stability (1-30 days): Normal retention
- High stability (> 30 days): Well-remembered

#### 2. Difficulty (D)

**Definition**: How hard it is to recall this knowledge.

**Range**: [1, 10]

**Interpretation**:
- Low difficulty (< 3): Easy to remember
- Medium difficulty (3-7): Normal complexity
- High difficulty (> 7): Challenging to recall

#### 3. Retrievability (R)

**Definition**: Probability of successfully recalling this knowledge right now.

**Range**: [0, 1]

**Formula**:
```
R = (1 + elapsed_days / (9 * stability)) ^ -1
```

**Interpretation**:
- R ≈ 1.0: Just learned or well-retained
- R ≈ 0.9: At the edge of forgetting
- R < 0.5: Likely forgotten

#### 4. State

**Definition**: Learning state of the knowledge.

**Values**:
- `0` - New: Never learned
- `1` - Learning: Recently failed, needs review
- `2` - Review: Successfully learned, in maintenance

#### 5. Repetitions (reps)

**Definition**: Number of times this knowledge has been reviewed.

**Range**: [0, ∞)

### Algorithm

#### calculate_next(current_state, rating, now)

**Purpose**: Calculate the next memory state after a review.

**Parameters**:
- `current_state`: Current NodeState (stability, difficulty, etc.)
- `rating`: Review rating (1=Again, 2=Hard, 3=Good, 4=Easy)
- `now`: Current timestamp

**Returns**: New NodeState

**Algorithm Flow**:

```
1. IF state == 0 (New Card):
   - Set initial stability based on rating
   - Set initial difficulty based on rating
   - State becomes 1 (Learning)
   - Reps = 1

2. ELSE (Existing Card):
   a. Calculate retrievability:
      R = (1 + elapsed_days / (9 * S)) ^ -1
   
   b. Update difficulty:
      D_next = weighted_average(D_current, rating_adjustment)
   
   c. IF rating == Again:
      - Calculate reduced stability (forgetting)
      - State = 1 (back to Learning)
   
   d. ELSE (Hard/Good/Easy):
      - Calculate increased stability (reinforcement)
      - Apply Hard penalty or Easy bonus
      - State = 2 (Review)
   
   e. Increment reps

3. Return new NodeState
```

### Example Usage

```python
from ghost_kg.core import FSRS, Rating
from ghost_kg.storage import NodeState
import datetime

fsrs = FSRS()

# New knowledge
initial_state = NodeState(
    stability=0,
    difficulty=0,
    last_review=None,
    reps=0,
    state=0
)

now = datetime.datetime.now(datetime.timezone.utc)

# First review - rated Good
next_state = fsrs.calculate_next(initial_state, Rating.Good, now)
print(f"Stability: {next_state.stability:.2f} days")
print(f"Difficulty: {next_state.difficulty:.2f}")
print(f"State: {next_state.state}")

# Simulate time passing (10 days)
later = now + datetime.timedelta(days=10)

# Second review - rated Easy
final_state = fsrs.calculate_next(next_state, Rating.Easy, later)
print(f"New Stability: {final_state.stability:.2f} days")
```

---

## NodeState

### Overview

`NodeState` is a data class representing the memory state of a knowledge node.

### Class: `NodeState`

**Location**: `ghost_kg/storage/database.py`

**Type**: `@dataclass`

### Attributes

```python
@dataclass
class NodeState:
    stability: float      # Days until R=0.9
    difficulty: float     # Complexity [1-10]
    last_review: datetime # When last reviewed
    reps: int            # Review count
    state: int           # 0=New, 1=Learning, 2=Review
```

### Example

```python
from ghost_kg.storage import NodeState
import datetime

state = NodeState(
    stability=2.4,
    difficulty=5.0,
    last_review=datetime.datetime.now(datetime.timezone.utc),
    reps=1,
    state=1
)
```

---

## GhostAgent

### Overview

`GhostAgent` represents an individual agent with its own knowledge graph and memory system.

### Class: `GhostAgent`

**Location**: `ghost_kg/core/agent.py`

**Purpose**: Manage an agent's knowledge, memory, and temporal state.

### Initialization

```python
def __init__(
    self, 
    name: str, 
    db_path: str = "agent_memory.db",
    llm_host: str = "http://localhost:11434"
)
```

**Parameters**:
- `name`: Unique agent identifier
- `db_path`: SQLite database file path
- `llm_host`: LLM server URL (for backward compatibility with Ollama)
- `llm_service`: Optional LLMService instance (supports Ollama, OpenAI, Anthropic, etc.)

### Attributes

```python
self.name              # Agent's name
self.db                # KnowledgeDB instance
self.fsrs              # FSRS instance
self.client            # LLM client (backward compatibility)
self.llm_service       # LLMService instance (supports multiple providers)
self.current_time      # Simulation time
```

### Key Methods

#### learn_triplet(source, relation, target, rating=Good, sentiment=0.0)

**Purpose**: Learn a new triplet (knowledge piece).

**Parameters**:
- `source`: Subject entity (e.g., "I", "Bob", "UBI")
- `relation`: Relationship verb (e.g., "supports", "opposes")
- `target`: Object entity (e.g., "climate action", "automation")
- `rating`: Memory strength (1-4, default: Good)
- `sentiment`: Emotional valence (-1.0 to 1.0, default: 0.0)

**Process**:
1. Get or create source node
2. Get or create target node
3. Calculate FSRS states for both nodes
4. Store triplet with sentiment
5. Update node states in database

**Example**:
```python
agent.learn_triplet(
    source="I",
    relation="support",
    target="renewable energy",
    rating=Rating.Easy,
    sentiment=0.8
)
```

#### get_memory_view(topic)

**Purpose**: Generate a formatted context string for a topic.

**Parameters**:
- `topic`: Topic keyword to focus on

**Returns**: Formatted string with:
- Agent's current stance
- Known facts about the topic
- Others' opinions

**Process**:
1. Query agent's stance (edges with source="I" or agent name)
2. Query world knowledge (other entities' relationships)
3. Format into readable text
4. Return context string

**Example**:
```python
context = agent.get_memory_view("climate change")
# Returns:
# "MY CURRENT STANCE: I support renewable energy; I am_concerned_about climate impacts.
#  KNOWN FACTS: climate change affects ecosystems; renewable energy reduces emissions.
#  OTHERS' VIEWS: Bob supports carbon tax; Alice advocates for green policy."
```

#### set_time(new_time)

**Purpose**: Set the agent's current time (for simulation).

**Parameters**:
- `new_time`: Can be one of:
  - `datetime.datetime`: Real datetime with timezone
  - `(day, hour)` tuple: Round-based time where day >= 1, hour in [0, 23]
  - `SimulationTime`: Pre-constructed SimulationTime object

**Examples**:
```python
import datetime

# Using real datetime
time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
agent.set_time(time)

# Using round-based time (day, hour)
agent.set_time((1, 9))  # Day 1, Hour 9

# Using SimulationTime object
from ghost_kg import SimulationTime
sim_time = SimulationTime.from_round(5, 14)
agent.set_time(sim_time)
```

**Notes**:
- Round-based time is perfect for game simulations, agent-based models, or any scenario with discrete time steps
- You can switch between datetime and round-based time modes as needed
- Round-based time is automatically stored in the database with `sim_day` and `sim_hour` columns

---

## CognitiveLoop

### Overview

`CognitiveLoop` provides integrated LLM operations for agents, including content absorption, reflection, and response generation.

### Class: `CognitiveLoop`

**Location**: `ghost_kg/core/cognitive.py`

**Purpose**: Handle LLM-based operations for GhostAgent.

### Initialization

```python
def __init__(
    self,
    agent: GhostAgent,
    model: str = "llama3.2",
    fast_mode: bool = False
)
```

**Parameters**:
- `agent`: GhostAgent instance
- `model`: LLM model name (e.g., "llama3.2", "gpt-4", "claude-3-opus")
- `fast_mode`: Use GLiNER+TextBlob (True) or LLM service (False)

### Key Methods

#### absorb(text, author="User")

**Purpose**: Process and learn from incoming text.

**Modes**:

1. **Fast Mode** (GLiNER + TextBlob):
   - Extract entities with GLiNER
   - Analyze sentiment with TextBlob
   - Create triplets heuristically
   - Very fast, no LLM needed

2. **LLM Mode** (Semantic):
   - Send text to LLM service (Ollama, OpenAI, Anthropic, etc.)
   - Extract structured knowledge
   - World facts, partner stance, agent reaction
   - More accurate, slower

**Example**:
```python
loop = CognitiveLoop(agent, fast_mode=True)
loop.absorb("Climate change requires urgent action.", author="Bob")
```

#### reflect(text)

**Purpose**: Extract agent's own beliefs from their statements.

**Process**:
1. Send agent's statement to LLM
2. Extract expressed stances
3. Learn triplets with source="I"
4. Update memory

**Example**:
```python
loop.reflect("I believe in renewable energy.")
# Learns: ("I", "believe_in", "renewable energy")
```

#### reply(topic, partner_name)

**Purpose**: Generate a response on a topic.

**Process**:
1. Get memory view for topic
2. Create prompt with context
3. Generate response with LLM
4. Reflect on own response
5. Log interaction
6. Return response

**Example**:
```python
response = loop.reply("climate change", partner_name="Bob")
print(response)  # "I support renewable energy initiatives..."
```

### Fast Mode Details

**Requirements**: `pip install gliner textblob`

**Process**:
1. **Entity Extraction** (GLiNER):
   - Labels: ["Topic", "Person", "Concept", "Organization"]
   - Extracts named entities from text
   
2. **Sentiment Analysis** (TextBlob):
   - Polarity: -1.0 (negative) to 1.0 (positive)
   - Determines emotional tone
   
3. **Relation Mapping**:
   - sentiment > 0.3 → "supports"
   - sentiment < -0.3 → "opposes"
   - sentiment > 0.1 → "likes"
   - sentiment < -0.1 → "dislikes"
   - else → "discusses"

4. **Triplet Creation**:
   - Partner stance: (author, relation, entity)
   - World fact: (entity, "is", "discussed")
   - Agent reaction: ("I", "heard about", entity)

**Trade-offs**:
- ✅ Very fast (no LLM calls)
- ✅ Works offline
- ✅ Predictable results
- ❌ Less nuanced than LLM
- ❌ Misses complex relationships

---

## KnowledgeDB

### Overview

`KnowledgeDB` manages the SQLite database for knowledge persistence.

### Class: `KnowledgeDB`

**Location**: `ghost_kg/storage/database.py`

**Purpose**: Handle all database operations for nodes, edges, and logs.

### Schema

#### nodes Table

```sql
CREATE TABLE nodes (
    owner_id TEXT,        -- Agent name
    id TEXT,              -- Node identifier
    stability REAL,       -- FSRS stability
    difficulty REAL,      -- FSRS difficulty
    last_review TIMESTAMP,-- Last review time
    reps INTEGER,         -- Review count
    state INTEGER,        -- FSRS state (0/1/2)
    created_at TIMESTAMP, -- Creation time
    PRIMARY KEY (owner_id, id)
)
```

#### edges Table

```sql
CREATE TABLE edges (
    owner_id TEXT,        -- Agent name
    source TEXT,          -- Subject entity
    target TEXT,          -- Object entity
    relation TEXT,        -- Relationship type
    weight REAL,          -- Connection strength
    sentiment REAL,       -- Emotional valence [-1, 1]
    created_at TIMESTAMP, -- Creation time
    PRIMARY KEY (owner_id, source, target, relation),
    FOREIGN KEY(owner_id, source) REFERENCES nodes(owner_id, id),
    FOREIGN KEY(owner_id, target) REFERENCES nodes(owner_id, id)
)
```

#### logs Table

```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT,      -- Agent name
    action_type TEXT,     -- READ/WRITE
    content TEXT,         -- Text content
    annotations JSON,     -- Metadata
    timestamp TIMESTAMP   -- Action time
)
```

### Key Methods

#### upsert_node(owner_id, node_id, fsrs_state, timestamp)

**Purpose**: Insert or update a node with FSRS state.

**Parameters**:
- `owner_id`: Agent name
- `node_id`: Node identifier
- `fsrs_state`: NodeState object (optional)
- `timestamp`: Current time

**Behavior**:
- If node exists: Update FSRS state
- If node doesn't exist: Create new node
- If no fsrs_state: Create node without FSRS data

#### add_relation(owner_id, source, relation, target, sentiment, timestamp)

**Purpose**: Add a triplet (edge) to the knowledge graph.

**Parameters**:
- `owner_id`: Agent name
- `source`: Subject entity
- `relation`: Relationship verb
- `target`: Object entity
- `sentiment`: Emotional valence
- `timestamp`: Current time

**Behavior**:
- Ensures source and target nodes exist
- Inserts or replaces edge
- Updates timestamp

#### get_agent_stance(owner_id, topic, current_time)

**Purpose**: Retrieve agent's beliefs about a topic.

**Query Logic**:
```sql
SELECT source, relation, target, sentiment 
FROM edges
WHERE owner_id = ?
  AND (source = 'I' OR source = ?)  -- Agent's own beliefs
  AND (
    target LIKE ?                    -- Contains topic keyword
    OR created_at >= datetime(?, '-60 minutes')  -- Recent memories
  )
ORDER BY created_at DESC
LIMIT 8
```

**Parameters**:
- `owner_id`: Agent name
- `topic`: Topic keyword (with wildcards)
- `current_time`: Reference time for recency

**Returns**: List of rows with agent's stance

#### get_world_knowledge(owner_id, topic, limit)

**Purpose**: Retrieve general facts about a topic.

**Query Logic**:
```sql
SELECT source, relation, target
FROM edges
WHERE owner_id = ?
  AND source != 'I'               -- Not agent's beliefs
  AND source != ?                 -- Not agent's statements
  AND (source LIKE ? OR target LIKE ?)  -- Contains topic
ORDER BY created_at DESC
LIMIT ?
```

**Parameters**:
- `owner_id`: Agent name
- `topic`: Topic keyword
- `limit`: Max results

**Returns**: List of rows with world knowledge

#### log_interaction(agent, action, content, annotations, timestamp)

**Purpose**: Log an interaction for debugging/analysis.

**Parameters**:
- `agent`: Agent name
- `action`: "READ" or "WRITE"
- `content`: Text content
- `annotations`: Dict with metadata (e.g., context_used, triplets_count)
- `timestamp`: Action time

**Storage**: Annotations stored as JSON string

---

## AgentManager

### Overview

`AgentManager` provides a high-level API for external programs to manage multiple agents.

### Class: `AgentManager`

**Location**: `ghost_kg/core/manager.py`

**Purpose**: Simplify multi-agent knowledge graph management.

### Initialization

```python
def __init__(self, db_path: str = "agent_memory.db")
```

**Parameters**:
- `db_path`: SQLite database file path

### Key Methods

#### create_agent(name, llm_host, llm_service)

**Purpose**: Create or retrieve an agent.

**Parameters**:
- `name`: Agent identifier
- `llm_host`: Optional LLM host URL (for backward compatibility)
- `llm_service`: Optional LLMService instance (supports multiple providers)

**Returns**: GhostAgent instance

**Example**:
```python
manager = AgentManager("agents.db")
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")
```

#### set_agent_time(agent_name, time)

**Purpose**: Set simulation time for an agent.

**Example**:
```python
import datetime
time = datetime.datetime(2025, 1, 1, 9, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", time)
```

#### absorb_content(agent_name, content, author, triplets, fast_mode)

**Purpose**: Update agent's KG with incoming content.

**Parameters**:
- `agent_name`: Target agent
- `content`: Text content
- `author`: Source of content
- `triplets`: Pre-extracted triplets (optional)
- `fast_mode`: Use fast extraction if no triplets provided

**Example**:
```python
# With external triplets
triplets = [("Bob", "mentions", "automation")]
manager.absorb_content("Alice", "Bob mentioned automation", "Bob", triplets)

# Let GhostKG extract
manager.absorb_content("Alice", "Bob mentioned automation", "Bob")
```

#### get_context(agent_name, topic)

**Purpose**: Get context for generating a response.

**Returns**: Formatted context string

**Example**:
```python
context = manager.get_context("Alice", "automation")
# Use context with your LLM
```

#### update_with_response(agent_name, response, triplets, context)

**Purpose**: Update agent's KG with generated response.

**Parameters**:
- `agent_name`: Agent who generated response
- `response`: Generated text
- `triplets`: Extracted beliefs (optional)
- `context`: Context used (for logging)

**Example**:
```python
response_triplets = [("value", "economic security", 0.7)]
manager.update_with_response(
    "Alice", 
    "I value economic security", 
    response_triplets,
    context
)
```

#### learn_triplet(agent_name, source, relation, target, rating, sentiment)

**Purpose**: Directly add a triplet to agent's KG.

**Example**:
```python
manager.learn_triplet(
    "Alice",
    "I",
    "support",
    "UBI",
    rating=Rating.Easy,
    sentiment=0.8
)
```

#### process_and_get_context(agent_name, topic, text, author, triplets, fast_mode)

**Purpose**: Atomic operation - absorb content and get context.

**Returns**: Context string

**Example**:
```python
# One call instead of two
context = manager.process_and_get_context(
    "Alice",
    "climate",
    "Bob talks about climate change",
    author="Bob"
)
```

## Component Interaction Examples

### Example 1: Simple Learning

```python
from ghost_kg import AgentManager, Rating

manager = AgentManager()
manager.create_agent("Alice")

# Learn a fact
manager.learn_triplet(
    "Alice",
    "renewable energy",
    "reduces",
    "emissions",
    rating=Rating.Good
)
```

### Example 2: Multi-Round Conversation

```python
manager = AgentManager()
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")

# Bob speaks
bob_text = "I support renewable energy"
bob_triplets = [("I", "support", "renewable energy")]
manager.absorb_content("Alice", bob_text, "Bob", bob_triplets)

# Alice prepares response
context = manager.get_context("Alice", "renewable energy")

# Alice responds
alice_text = "I agree, it's crucial for climate"
alice_triplets = [("agree", "renewable energy", 0.8)]
manager.update_with_response("Alice", alice_text, alice_triplets, context)
```

### Example 3: Time-Based Simulation

```python
import datetime
from datetime import timedelta

manager = AgentManager()
agent = manager.create_agent("Alice")

# Day 1, 9 AM
time = datetime.datetime(2025, 1, 1, 9, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", time)
manager.learn_triplet("Alice", "I", "support", "UBI", rating=Rating.Good)

# Day 10, 9 AM (memory decay)
time += timedelta(days=9)
manager.set_agent_time("Alice", time)
context = manager.get_context("Alice", "UBI")
# Context will show reduced retrievability
```

## Summary

The core components work together to provide:

1. **FSRS**: Realistic memory modeling
2. **NodeState**: Memory state representation
3. **GhostAgent**: Individual agent with knowledge graph
4. **CognitiveLoop**: LLM integration (optional)
5. **KnowledgeDB**: Persistent storage
6. **AgentManager**: High-level API

This architecture enables flexible, time-aware knowledge graphs with natural forgetting, suitable for various AI agent applications.
