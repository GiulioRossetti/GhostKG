# GhostKG Architecture

## System Overview

GhostKG is a dynamic knowledge graph management system designed specifically for LLM agents, featuring built-in memory decay through FSRS (Free Spaced Repetition Scheduler). The system enables agents to maintain temporal, evolving knowledge bases that naturally forget information over time, mimicking human memory.

## Design Philosophy

### Core Principles

1. **Separation of Concerns**: Knowledge management is decoupled from LLM logic, allowing maximum flexibility in integration
2. **Time-Aware**: All operations are time-conscious, enabling realistic temporal simulations
3. **Memory Decay**: Uses FSRS to model realistic forgetting curves
4. **Multi-Agent**: Supports multiple independent agents with separate knowledge bases
5. **Flexibility**: Can be used as a library (external API) or with integrated LLM support

### Architecture Goals

- **Simplicity**: Easy to integrate with any LLM or application
- **Efficiency**: Fast queries and updates using SQLite
- **Scalability**: Support multiple agents and large knowledge bases
- **Testability**: Clear interfaces for unit and integration testing
- **Extensibility**: Easy to add new features without breaking existing code

## Package Structure

GhostKG is organized into logical subpackages for improved maintainability and discoverability:

```
ghost_kg/
├── __init__.py          # Main API exports
│
├── core/               # Core agent and manager functionality
│   ├── agent.py        # GhostAgent - Individual agent with KG
│   ├── manager.py      # AgentManager - Multi-agent management API
│   └── cognitive.py    # CognitiveLoop - Integrated LLM operations
│
├── memory/             # Memory management and caching
│   ├── fsrs.py         # FSRS algorithm, Rating enum
│   └── cache.py        # AgentCache for performance
│
├── storage/            # Database and persistence layer
│   └── database.py     # KnowledgeDB, NodeState - SQLite storage
│
├── extraction/         # Triplet extraction strategies
│   └── extraction.py   # FastExtractor, LLMExtractor, get_extractor
│
├── utils/              # Utilities and helpers
│   ├── config.py       # Configuration classes
│   ├── exceptions.py   # Custom exception hierarchy
│   └── dependencies.py # Dependency checking utilities
│
└── templates/          # HTML and JSON templates for visualization
```

### Import Patterns

**Recommended**: Import from top-level package
```python
from ghost_kg import AgentManager, GhostAgent, Rating
from ghost_kg import KnowledgeDB, FSRSConfig
```

**Also supported**: Import from subpackages
```python
from ghost_kg.core import AgentManager, GhostAgent
from ghost_kg.memory import FSRS, Rating
from ghost_kg.storage import KnowledgeDB
from ghost_kg.utils import ConfigurationError
```

**Backward compatible**: Old flat imports still work
```python
from ghost_kg.agent import GhostAgent
from ghost_kg.manager import AgentManager
```

### Module Responsibilities

**ghost_kg.core**
- `agent.py`: Individual agent with knowledge graph and memory
- `manager.py`: High-level API for managing multiple agents
- `cognitive.py`: Integrated LLM operations (optional)

**ghost_kg.memory**
- `fsrs.py`: Spaced repetition algorithm for memory decay
- `cache.py`: Performance caching for frequently accessed data

**ghost_kg.storage**
- `database.py`: SQLite-based persistence layer for KG

**ghost_kg.extraction**
- `extraction.py`: Strategies for extracting triplets from text
  - FastExtractor: GLiNER + VADER (no LLM required)
  - LLMExtractor: Deep semantic extraction with LLM

**ghost_kg.utils**
- `config.py`: Configuration management (FSRSConfig, DatabaseConfig, etc.)
- `exceptions.py`: Custom exception hierarchy
- `dependencies.py`: Dependency checking and validation

## System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  External Program / LLM Integration                      │ │
│  │  • Business Logic                                        │ │
│  │  • Text Generation (GPT-4, Claude, Ollama, etc.)       │ │
│  │  • Conversation Management                               │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────┬──────────────────────────────────────┘
                          │ AgentManager API
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                      GhostKG Core Layer                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              AgentManager (manager.py)                   │ │
│  │  • create_agent()        • get_context()                │ │
│  │  • absorb_content()      • update_with_response()       │ │
│  │  • set_agent_time()      • learn_triplet()             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                GhostAgent (core.py)                      │ │
│  │  • Knowledge Graph Management                            │ │
│  │  • Memory View Construction                              │ │
│  │  • Triplet Learning                                      │ │
│  │  • Time Management                                       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                      │
│         ┌────────────────┴────────────────┐                   │
│         ▼                                  ▼                   │
│  ┌──────────────┐                  ┌──────────────────────┐  │
│  │     FSRS     │                  │   CognitiveLoop      │  │
│  │   (core.py)  │                  │     (core.py)        │  │
│  │              │                  │                      │  │
│  │ • Stability  │                  │ • absorb() - Fast   │  │
│  │ • Difficulty │                  │ • absorb() - LLM    │  │
│  │ • Calculate  │                  │ • reply()           │  │
│  │   Next State │                  │ • reflect()         │  │
│  └──────────────┘                  └──────────────────────┘  │
│         │                                                      │
│         ▼                                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │            KnowledgeDB (storage.py)                      │ │
│  │  • Node Management (upsert_node, get_node)              │ │
│  │  • Edge Management (add_relation)                       │ │
│  │  • Query Operations (get_agent_stance, get_world_knowledge)│
│  │  • Logging (log_interaction)                            │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────┬──────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                    Persistence Layer                            │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    SQLite Database                       │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐       │ │
│  │  │   nodes    │  │   edges    │  │    logs    │       │ │
│  │  │            │  │            │  │            │       │ │
│  │  │ • FSRS     │  │ • Triplets │  │ • History  │       │ │
│  │  │   state    │  │ • Sentiment│  │ • Annotations│     │ │
│  │  └────────────┘  └────────────┘  └────────────┘       │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

## Component Relationships

### Data Flow

#### 1. Content Absorption (Reading)

```
External Program
    ↓ (content, author, triplets)
AgentManager.absorb_content()
    ↓
GhostAgent.learn_triplet()
    ↓
FSRS.calculate_next() → KnowledgeDB.upsert_node()
    ↓
KnowledgeDB.add_relation()
    ↓
SQLite Database
```

#### 2. Context Retrieval (Preparing to Reply)

```
External Program
    ↓ (agent_name, topic)
AgentManager.get_context()
    ↓
GhostAgent.get_memory_view()
    ↓
KnowledgeDB.get_agent_stance()
KnowledgeDB.get_world_knowledge()
    ↓
SQLite Queries
    ↓
Formatted Context String
```

#### 3. Response Update (After Generating Reply)

```
External Program
    ↓ (agent_name, response, triplets, context)
AgentManager.update_with_response()
    ↓
GhostAgent.learn_triplet() (with source="I")
    ↓
KnowledgeDB.log_interaction()
    ↓
SQLite Database
```

## Layer Responsibilities

### Application Layer

**Responsibilities:**
- Business logic and conversation flow
- LLM integration and prompt engineering
- Text generation
- Triplet extraction (optional - can be delegated to GhostKG)
- User interface / API endpoints

**Does NOT handle:**
- Knowledge graph storage
- Memory decay calculations
- Time management for agents

### Core Layer

#### AgentManager (Public API)

**Responsibilities:**
- Multi-agent management
- High-level operations (create, absorb, get_context, update)
- Coordination between agents and database

**Interface:**
- `create_agent(name)` - Create/retrieve agent
- `absorb_content(agent, content, author, triplets)` - Process input
- `get_context(agent, topic)` - Retrieve context
- `update_with_response(agent, response, triplets, context)` - Update with output
- `set_agent_time(agent, time)` - Set simulation time

#### GhostAgent

**Responsibilities:**
- Individual agent knowledge graph
- Memory view construction
- Triplet learning with FSRS integration
- Time tracking

**Key Methods:**
- `learn_triplet(source, relation, target, rating, sentiment)`
- `get_memory_view(topic)` - Formatted context string
- `set_time(datetime)` - Update agent's current time

#### FSRS

**Responsibilities:**
- Spaced repetition calculations
- Stability and difficulty updates
- State transitions

**Algorithm:**
- Calculate next state based on rating and elapsed time
- Update stability, difficulty, repetitions
- Determine new state (0=new, 1=learning, 2=review)

#### CognitiveLoop

**Responsibilities:**
- Integrated LLM operations (optional)
- Triplet extraction (fast mode: GLiNER+VADER, LLM mode: semantic)
- Response generation
- Self-reflection

**Modes:**
- Fast Mode: Heuristic extraction with GLiNER + VADER
- LLM Mode: Deep semantic extraction with Ollama

#### KnowledgeDB

**Responsibilities:**
- Database schema management
- CRUD operations for nodes and edges
- Semantic queries (stance, world knowledge)
- Interaction logging

**Schema:**
- `nodes` - Entities with FSRS state
- `edges` - Relationships (triplets) with sentiment
- `logs` - Interaction history with annotations

### Persistence Layer

**Responsibilities:**
- Data persistence
- Transaction management
- Query optimization

**Technology:**
- SQLite for simplicity and portability
- Row factory for easy access
- Check same_thread=False for multi-threading support

## Integration Patterns

### Pattern 1: External API (Recommended)

```python
# Application controls everything
manager = AgentManager()
agent = manager.create_agent("Alice")

# Application extracts triplets
triplets = extract_with_your_nlp(text)
manager.absorb_content("Alice", text, "Bob", triplets)

# Application gets context
context = manager.get_context("Alice", topic)

# Application generates with LLM
response = your_llm.generate(context)

# Application updates KG
response_triplets = extract_with_your_nlp(response)
manager.update_with_response("Alice", response, response_triplets, context)
```

### Pattern 2: Integrated LLM

```python
# GhostKG handles LLM operations
agent = GhostAgent("Alice")
loop = CognitiveLoop(agent)

# GhostKG extracts and learns
loop.absorb(text, author="Bob")

# GhostKG generates response
response = loop.reply(topic, partner_name="Bob")
```

### Pattern 3: Hybrid

```python
# Mix external control with GhostKG extraction
manager = AgentManager()

# Let GhostKG extract triplets
manager.absorb_content("Alice", text, "Bob")  # No triplets - uses LLM

# Application controls response generation
context = manager.get_context("Alice", topic)
response = your_custom_llm(context)

# Let GhostKG extract from response
manager.update_with_response("Alice", response)  # No triplets - uses LLM
```

## Design Decisions

### Why FSRS?

**Decision**: Use FSRS v4.5 for memory modeling

**Rationale**:
- Well-researched spaced repetition algorithm
- Realistic forgetting curves
- Simple to implement
- Proven effectiveness in flashcard applications
- Applicable to knowledge graphs

**Alternatives Considered**:
- Simple decay: Too simplistic
- Custom algorithm: Reinventing the wheel
- Ebbinghaus curves: Less flexible than FSRS

### Why SQLite?

**Decision**: Use SQLite for persistence

**Rationale**:
- Zero configuration
- Single file database
- Fast for small to medium datasets
- Portable
- Good Python support

**Alternatives Considered**:
- PostgreSQL: Overkill for most use cases
- MongoDB: Doesn't fit relational model well
- In-memory only: Loses data on restart

### Why Separate AgentManager API?

**Decision**: Create external-facing AgentManager API

**Rationale**:
- Decouples knowledge management from LLM logic
- Allows any LLM to be used
- Enables custom business logic
- Simplifies testing
- Maintains flexibility

**Benefits**:
- Use GPT-4, Claude, Ollama, or custom LLMs
- Implement custom conversation flows
- Integrate with existing systems
- Test without LLM dependency

### Why Support Both Fast and LLM Modes?

**Decision**: Implement both GLiNER+VADER (fast) and LLM extraction

**Rationale**:
- Fast mode: Good for demos, testing, large-scale simulations
- LLM mode: Better accuracy for production use
- User choice based on requirements
- Graceful degradation when LLM unavailable

## Scalability Considerations

### Current Limitations

1. **Single SQLite file**: Not suitable for distributed systems
2. **In-memory agent dict**: Limited by RAM
3. **No caching**: Queries hit database each time
4. **No sharding**: All agents in same database

### Future Enhancements

1. **Connection pooling**: For high concurrency
2. **Caching layer**: Redis or in-memory cache
3. **Database per agent**: Better isolation
4. **Read replicas**: For read-heavy workloads
5. **Background cleanup**: Prune old, forgotten knowledge

## Security Considerations

### Current Implementation

1. **SQL injection**: Parameterized queries throughout
2. **File access**: Database path validation needed
3. **Input validation**: Minimal - relies on application

### Recommendations

1. Validate agent names (alphanumeric only)
2. Limit triplet sizes to prevent DoS
3. Implement rate limiting at application level
4. Sanitize log content before storage
5. Use read-only mode for query-only operations

## Testing Strategy

### Unit Tests

- FSRS calculations with known inputs
- Database operations (CRUD)
- Memory view formatting
- Triplet learning logic

### Integration Tests

- Full workflow: absorb → get_context → update
- Multi-agent scenarios
- Time progression
- Fast vs LLM mode

### Performance Tests

- Large knowledge bases (1000+ triplets)
- Many agents (100+)
- Query performance
- Memory usage

## Monitoring and Observability

### Logging Points

1. Agent creation
2. Content absorption
3. Context retrieval
4. Response updates
5. FSRS state changes

### Metrics to Track

1. Number of agents
2. Triplets per agent
3. Query latency
4. Memory usage
5. Database size

### Debug Information

- Logs table: Full interaction history
- Annotations field: Context used for generation
- FSRS states: Stability, difficulty, retrievability
- Timestamps: When knowledge was acquired

## Configuration

### Database Path

```python
manager = AgentManager(db_path="custom_path.db")
```

### LLM Host

```python
agent = GhostAgent("Alice", llm_host="http://custom:11434")
```

### Fast Mode

```python
loop = CognitiveLoop(agent, fast_mode=True)
```

### FSRS Parameters

Currently hardcoded in FSRS class. Future: make configurable.

## Conclusion

GhostKG's architecture prioritizes simplicity, flexibility, and realistic memory modeling. The clean separation between knowledge management and LLM operations enables integration with any AI system while providing sophisticated temporal knowledge graphs out of the box.
