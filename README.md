# GhostKG - Dynamic Knowledge Graphs with Memory Decay for LLM Agents

GhostKG is a Python package that provides dynamic knowledge graph management for LLM agents with built-in memory decay using FSRS (Free Spaced Repetition Scheduler). It enables agents to maintain temporal, evolving knowledge bases that naturally forget information over time.

## Features

- **Dynamic Knowledge Graphs**: Maintain structured knowledge as semantic triplets (subject-relation-object)
- **Memory Decay**: FSRS-based spaced repetition models realistic memory retention and forgetting
- **Time-Aware**: Full support for temporal simulation and time-based queries
- **Sentiment Tracking**: Emotional associations with knowledge (-1.0 to 1.0 scale)
- **Multi-Agent Support**: Manage multiple agents with separate knowledge bases
- **Flexible Integration**: Use with any LLM (GPT-4, Claude, Ollama, etc.)
- **External API**: Decouple KG management from LLM logic for maximum flexibility

## Installation

```bash
pip install ghost_kg
```

Or install from source:

```bash
git clone https://github.com/GiulioRossetti/GhostKG.git
cd GhostKG
pip install -e .
```

## Quick Start

### Option 1: External Program API (Recommended)

Use GhostKG as a library to manage agent KGs while keeping full control over LLM and business logic:

```python
from ghost_kg import AgentManager, Rating
import datetime

# Initialize manager
manager = AgentManager(db_path="agents.db")

# Create agents
alice = manager.create_agent("Alice")
bob = manager.create_agent("Bob")

# Set time
current_time = datetime.datetime.now(datetime.timezone.utc)
manager.set_agent_time("Alice", current_time)

# Add knowledge
manager.learn_triplet("Alice", "I", "support", "UBI", rating=Rating.Easy, sentiment=0.8)

# Process incoming content
triplets = [("Bob", "mentions", "automation")]
manager.absorb_content("Alice", "Bob mentioned automation", author="Bob", triplets=triplets)

# Get context for reply
context = manager.get_context("Alice", topic="UBI")
# Use context with your LLM to generate response
response = your_llm.generate(context)

# Update KG with response
response_triplets = [("value", "economic security", 0.7)]
manager.update_with_response("Alice", response, triplets=response_triplets)
```

See [API Documentation](docs/API.md) for complete details.

### Option 2: Integrated LLM Approach

Use GhostKG with built-in Ollama LLM integration:

```python
from ghost_kg import GhostAgent, CognitiveLoop
import datetime

# Create agent
agent = GhostAgent("Alice", db_path="agent.db")
loop = CognitiveLoop(agent)

# Set time
agent.set_time(datetime.datetime.now(datetime.timezone.utc))

# Agent reads and processes content
loop.absorb("I think UBI is necessary.", author="Bob")

# Agent generates reply
response = loop.reply("UBI", partner_name="Bob")
```

## Use Cases

1. **Multi-Agent Simulations**: Model conversations between agents with evolving beliefs
2. **Chatbot Memory**: Give chatbots persistent, time-aware memory that naturally decays
3. **Research Assistants**: Track what an AI assistant knows and when it learned it
4. **Game NPCs**: Create NPCs with realistic memory and knowledge evolution
5. **Social Simulations**: Model opinion dynamics and information spread

## Key Concepts

### Knowledge Triplets

Knowledge is stored as semantic triplets:
- **Subject**: The source node (e.g., "I", "Bob", "automation")
- **Relation**: The relationship (e.g., "supports", "mentions", "affects")
- **Object**: The target node (e.g., "UBI", "jobs", "economy")

### Memory Decay (FSRS)

GhostKG uses FSRS v4.5 for realistic memory modeling:
- **Stability**: How well information is retained
- **Difficulty**: How hard it is to recall
- **Retrievability**: Current probability of recall based on elapsed time
- **Ratings**: Easy (4), Good (3), Hard (2), Again (1)

### Time Management

All operations are time-aware:
```python
import datetime

# Set simulation time
time = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
manager.set_agent_time("Alice", time)

# Advance time
from datetime import timedelta
time += timedelta(hours=1)
manager.set_agent_time("Alice", time)
```

## Architecture

```
┌─────────────────────────────────────┐
│   Your Application/LLM Integration   │
│  (Business Logic, Text Generation)   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         GhostKG (AgentManager)      │
│  ┌─────────────────────────────┐   │
│  │   Agent Management          │   │
│  │   • Create/retrieve agents  │   │
│  │   • Update/query KGs        │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │   Knowledge Graph Storage   │   │
│  │   • Triplet management      │   │
│  │   • Semantic filtering      │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │   Memory System (FSRS)      │   │
│  │   • Spaced repetition       │   │
│  │   • Forgetting curves       │   │
│  └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
               ▼
       ┌──────────────┐
       │   SQLite DB  │
       └──────────────┘
```

## Examples

- **[external_program.py](examples/external_program.py)**: Complete example of external program integration
- **[hourly_simulation.py](examples/hourly_simulation.py)**: Time-based agent conversation simulation
- **[export_history.py](examples/export_history.py)**: Export knowledge graph history

## Documentation

- [API Documentation](docs/API.md) - Complete API reference
- [Examples](examples/) - Working code examples

## Requirements

- Python >= 3.8
- networkx >= 3.0
- fsrs >= 1.0.0
- ollama >= 0.1.6 (optional, only for integrated LLM approach)

## License

MIT License

## Citation

If you use GhostKG in your research, please cite:

```bibtex
@software{ghostkg2025,
  title={GhostKG: Dynamic Knowledge Graphs with Memory Decay for LLM Agents},
  author={Your Name},
  year={2025},
  url={https://github.com/GiulioRossetti/GhostKG}
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For questions and support, please open an issue on GitHub.
