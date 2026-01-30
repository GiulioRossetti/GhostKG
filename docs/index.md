# GhostKG Documentation Index

Welcome to the comprehensive documentation for **GhostKG** - a dynamic knowledge graph management system for LLM agents with built-in memory decay using FSRS (Free Spaced Repetition Scheduler).

## 📚 Documentation Structure

### Quick Start
- [README](../README.md) - Overview, installation, and quick start guide

### Core Documentation

#### 1. [Architecture & Design](ARCHITECTURE.md)
**Complete system architecture and design philosophy**

Topics covered:
- System overview and design principles
- Component relationships and data flow
- Layer responsibilities
- Integration patterns (External API, Integrated LLM, Hybrid)
- Design decisions and rationale
- Scalability considerations
- Security considerations
- Testing strategy

**Read this if you want to**: Understand how GhostKG is structured and why design decisions were made.

**Cross-references**:
- [Core Components](CORE_COMPONENTS.md) - Detailed component specifications
- [Algorithms](ALGORITHMS.md) - Mathematical foundations
- [Database Schema](DATABASE_SCHEMA.md) - Persistence layer details

---

#### 2. [Core Components](CORE_COMPONENTS.md)
**Detailed documentation of each component in the system**

Topics covered:
- **FSRS Memory System** - Spaced repetition algorithm
- **NodeState** - Memory state data structure
- **GhostAgent** - Individual agent with knowledge graph
- **CognitiveLoop** - LLM integration layer
- **KnowledgeDB** - Database operations
- **AgentManager** - External API interface

**Read this if you want to**: Understand what each component does and how to use it.

**Cross-references**:
- [API Documentation](API.md) - How to use the external API
- [Algorithms](ALGORITHMS.md) - Mathematical details of FSRS
- [Database Schema](DATABASE_SCHEMA.md) - Storage details

---

#### 3. [Algorithms & Formulas](ALGORITHMS.md)
**Mathematical and algorithmic foundations**

Topics covered:
- FSRS v4.5 algorithm details
- Memory decay calculations
- Retrievability formula and decay curves
- Stability update formulas (success and failure)
- Difficulty update algorithm
- Sentiment analysis methods
- Query algorithms and optimization
- Computational complexity analysis

**Read this if you want to**: Understand the mathematics behind memory modeling and forgetting curves.

**Cross-references**:
- [Core Components](CORE_COMPONENTS.md) - FSRS class implementation
- [Architecture](ARCHITECTURE.md) - Why FSRS was chosen
- Scientific papers on spaced repetition (see references in document)

---

#### 4. [Database Schema](DATABASE_SCHEMA.md)
**Complete database schema and query patterns**

Topics covered:
- Schema overview and ER diagrams
- **nodes** table - Entities with FSRS states
- **edges** table - Relationships (triplets)
- **logs** table - Interaction history
- Indexes and foreign keys
- Common query patterns
- Performance considerations
- Backup and migration

**Read this if you want to**: Understand how data is stored and queried.

**Cross-references**:
- [Core Components](CORE_COMPONENTS.md) - KnowledgeDB class
- [Architecture](ARCHITECTURE.md) - Why SQLite was chosen
- [Algorithms](ALGORITHMS.md) - Query complexity analysis

---

#### 5. [API Documentation](API.md)
**External API reference for integrating GhostKG**

Topics covered:
- AgentManager API overview
- Creating and managing agents
- Absorbing content (updating KG with input)
- Getting context for reply generation
- Updating with responses
- Time management
- Complete workflow examples

**Read this if you want to**: Integrate GhostKG with your own LLM or application.

**Cross-references**:
- [Core Components](CORE_COMPONENTS.md) - AgentManager details
- [Architecture](ARCHITECTURE.md) - Integration patterns
- [Examples](../examples/) - Working code examples

---

#### 6. [Fast Mode Configuration](FAST_MODE_CONFIG.md)
**Guide to fast mode vs LLM mode for triplet extraction**

Topics covered:
- Fast mode (GLiNER + TextBlob)
- LLM mode (semantic extraction)
- Configuration options
- Trade-offs and use cases
- Performance comparison

**Read this if you want to**: Choose between fast heuristic extraction or deep LLM-based extraction.

**Cross-references**:
- [Core Components](CORE_COMPONENTS.md) - CognitiveLoop fast mode
- [Algorithms](ALGORITHMS.md) - Sentiment analysis in fast mode
- [Examples](../examples/use_case_example.py) - Fast mode in practice

---

## 🎯 Use Case Guides

### By Goal

#### I want to integrate GhostKG with my application
1. Read: [Architecture](ARCHITECTURE.md#integration-patterns) - Integration patterns
2. Read: [API Documentation](API.md) - Complete API reference
3. See: [external_program.py](../examples/external_program.py) - Example integration
4. Read: [Core Components](CORE_COMPONENTS.md#agentmanager) - AgentManager details

#### I want to understand how memory decay works
1. Read: [Algorithms](ALGORITHMS.md#memory-decay-calculations) - Decay formulas
2. Read: [Algorithms](ALGORITHMS.md#fsrs-algorithm) - FSRS overview
3. Read: [Core Components](CORE_COMPONENTS.md#fsrs-memory-system) - Implementation
4. See: Python code in `ghost_kg/core.py` - FSRS class

#### I want to build a multi-agent simulation
1. Read: [API Documentation](API.md) - AgentManager usage
2. See: [use_case_example.py](../examples/use_case_example.py) - Multi-round conversation
3. See: [hourly_simulation.py](../examples/hourly_simulation.py) - Time-based simulation
4. Read: [Core Components](CORE_COMPONENTS.md#time-management) - Time handling

#### I want to query the knowledge graph directly
1. Read: [Database Schema](DATABASE_SCHEMA.md#query-patterns) - Query examples
2. Read: [Core Components](CORE_COMPONENTS.md#knowledgedb) - KnowledgeDB methods
3. See: [export_history.py](../examples/export_history.py) - Exporting data

#### I want to optimize performance
1. Read: [Database Schema](DATABASE_SCHEMA.md#performance-considerations) - DB optimization
2. Read: [Algorithms](ALGORITHMS.md#computational-complexity) - Complexity analysis
3. Read: [Architecture](ARCHITECTURE.md#scalability-considerations) - Scalability
4. Read: [Core Components](CORE_COMPONENTS.md) - Algorithm optimizations

#### I want to understand design decisions
1. Read: [Architecture](ARCHITECTURE.md#design-decisions) - Key decisions and rationale
2. Read: [Architecture](ARCHITECTURE.md#design-philosophy) - Core principles
3. Read: [Algorithms](ALGORITHMS.md#references) - Scientific foundations

---

## 📖 Reading Paths

### For New Users
1. [README](../README.md) - Start here
2. [Architecture](ARCHITECTURE.md#system-overview) - Understand the big picture
3. [API Documentation](API.md) - Learn the API
4. [Examples](../examples/) - See it in action

### For Researchers
1. [Algorithms](ALGORITHMS.md) - Mathematical foundations
2. [Core Components](CORE_COMPONENTS.md#fsrs-memory-system) - FSRS implementation
3. [Architecture](ARCHITECTURE.md#design-decisions) - Design rationale
4. Scientific papers (linked in Algorithms doc)

### For Developers
1. [Architecture](ARCHITECTURE.md) - System design
2. [Core Components](CORE_COMPONENTS.md) - Component details
3. [Database Schema](DATABASE_SCHEMA.md) - Data structures
4. Source code in `ghost_kg/` - Implementation

### For Integrators
1. [API Documentation](API.md) - External API
2. [Architecture](ARCHITECTURE.md#integration-patterns) - Integration patterns
3. [Fast Mode Config](FAST_MODE_CONFIG.md) - Extraction modes
4. [Examples](../examples/external_program.py) - Integration example

---

## 🔗 Cross-Reference Matrix

| From Document | To Documents |
|---------------|--------------|
| **Architecture** | Core Components (implementation)<br>Algorithms (mathematical basis)<br>Database Schema (storage)<br>API (external interface) |
| **Core Components** | Architecture (design context)<br>Algorithms (formulas)<br>Database Schema (storage details)<br>API (usage patterns) |
| **Algorithms** | Core Components (implementation)<br>Architecture (why FSRS)<br>Scientific papers (theory) |
| **Database Schema** | Core Components (KnowledgeDB)<br>Architecture (why SQLite)<br>Algorithms (query complexity) |
| **API** | Core Components (AgentManager)<br>Architecture (integration patterns)<br>Examples (code) |
| **Fast Mode Config** | Core Components (CognitiveLoop)<br>Algorithms (sentiment)<br>Examples (use_case_example.py) |

---

## 📁 Code Examples

All code examples are located in the [`examples/`](../examples/) directory:

- **[external_program.py](../examples/external_program.py)** - Complete external program integration
- **[use_case_example.py](../examples/use_case_example.py)** - Multi-round agent conversation with fast mode
- **[hourly_simulation.py](../examples/hourly_simulation.py)** - Time-based simulation with CognitiveLoop
- **[export_history.py](../examples/export_history.py)** - Export and analyze knowledge graphs

---

## 🧪 Testing

Tests are located in the [`tests/`](../tests/) directory:

- **[test_comprehensive.py](../tests/test_comprehensive.py)** - Full workflow tests
- **[test_process_and_get_context.py](../tests/test_process_and_get_context.py)** - API integration tests
- **[test_fast_mode_config.py](../tests/test_fast_mode_config.py)** - Configuration validation

---

## 📊 Quick Reference Tables

### Component Lookup

| Component | Location | Documentation | Purpose |
|-----------|----------|---------------|---------|
| FSRS | `ghost_kg/core.py` | [Core Components](CORE_COMPONENTS.md#fsrs-memory-system) | Memory modeling |
| GhostAgent | `ghost_kg/core.py` | [Core Components](CORE_COMPONENTS.md#ghostagent) | Individual agent |
| CognitiveLoop | `ghost_kg/core.py` | [Core Components](CORE_COMPONENTS.md#cognitiveloop) | LLM integration |
| KnowledgeDB | `ghost_kg/storage.py` | [Core Components](CORE_COMPONENTS.md#knowledgedb) | Database ops |
| AgentManager | `ghost_kg/manager.py` | [Core Components](CORE_COMPONENTS.md#agentmanager) | External API |

### Formula Lookup

| Formula | Location | Purpose |
|---------|----------|---------|
| Retrievability | [Algorithms](ALGORITHMS.md#retrievability-formula) | Memory recall probability |
| Stability Update (Success) | [Algorithms](ALGORITHMS.md#success-rating--2-3-4) | Strengthen memory |
| Stability Update (Failure) | [Algorithms](ALGORITHMS.md#failure-rating--1-again) | Weaken memory |
| Difficulty Update | [Algorithms](ALGORITHMS.md#difficulty-updates) | Adjust complexity |

### Table Lookup

| Table | Schema | Purpose |
|-------|--------|---------|
| nodes | [Database Schema](DATABASE_SCHEMA.md#nodes-table) | Entities with FSRS states |
| edges | [Database Schema](DATABASE_SCHEMA.md#edges-table) | Relationships (triplets) |
| logs | [Database Schema](DATABASE_SCHEMA.md#logs-table) | Interaction history |

---

## 🆘 Getting Help

### Common Questions

**Q: How do I integrate GhostKG with my LLM?**  
A: See [API Documentation](API.md) and [external_program.py](../examples/external_program.py)

**Q: What's the difference between fast mode and LLM mode?**  
A: See [Fast Mode Configuration](FAST_MODE_CONFIG.md)

**Q: How does memory decay work?**  
A: See [Algorithms](ALGORITHMS.md#memory-decay-calculations)

**Q: How do I query the knowledge graph?**  
A: See [Database Schema](DATABASE_SCHEMA.md#query-patterns)

**Q: Can I use a different database?**  
A: Not currently, but see [Architecture](ARCHITECTURE.md#why-sqlite) for why SQLite was chosen

### For More Information

- **Issues**: [GitHub Issues](https://github.com/GiulioRossetti/GhostKG/issues)
- **Examples**: [`examples/`](../examples/) directory
- **Tests**: [`tests/`](../tests/) directory
- **Source Code**: [`ghost_kg/`](../ghost_kg/) directory

---

## 📝 Contributing

When contributing documentation:

1. Maintain cross-references between documents
2. Update this index when adding new documents
3. Follow the established structure and style
4. Include examples and code snippets
5. Add entries to the cross-reference matrix

---

## 📄 License

GhostKG is released under the MIT License. See [LICENSE](../LICENSE) for details.

---

## 🎓 Citation

If you use GhostKG in your research, please cite:

```bibtex
@software{ghostkg2025,
  title={GhostKG: Dynamic Knowledge Graphs with Memory Decay for LLM Agents},
  author={Rossetti, Giulio},
  year={2025},
  url={https://github.com/GiulioRossetti/GhostKG}
}
```

---

## 📮 Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-30 | Initial comprehensive documentation |

---

**Last Updated**: 2025-01-30  
**Maintained By**: GhostKG Documentation Team
