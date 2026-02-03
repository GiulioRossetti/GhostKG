# Examples Overview

This section provides step-by-step walkthroughs of the example scripts included with GhostKG. Each example demonstrates different features and use cases of the library.

## Available Examples

### 1. [Existing Database Integration](existing_database_integration.md) 🆕
**File:** `examples/existing_database_integration.py`

Learn how to integrate GhostKG into an application that already uses SQLite. This example shows:
- Using GhostKG with an existing SQLite database
- Preserving existing application tables
- Creating GhostKG tables alongside application tables
- Verifying data coexistence and integrity

**Best for:** Integrating GhostKG into existing applications without creating a separate database.

---

### 2. [External Program Integration](external_program.md)
**File:** `examples/external_program.py`

Learn how to integrate GhostKG with your own application that uses external LLMs (like GPT-4, Claude, etc.) for text generation. This example shows:
- How to use the AgentManager API
- Managing agent knowledge graphs from an external program
- Extracting triplets externally and updating agent memories
- Simulating multi-round conversations with time progression

**Best for:** Building applications where you control the LLM and use GhostKG purely for knowledge management.

---

### 3. [Multi-Agent Conversation](use_case_example.md)
**File:** `examples/use_case_example.py`

A complete example of two agents (Alice and Bob) having a multi-round conversation about Greenland using LLM services. Demonstrates:
- Setting up the simulation time
- Processing content and retrieving context atomically
- Using LLM service (supports Ollama, OpenAI, Anthropic, etc.)
- Both Fast Mode (GLiNER) and LLM Mode for triplet extraction
- Knowledge graph evolution over time

**Best for:** Understanding the complete workflow of multi-agent simulations with any LLM provider.

---

### 3. [Temporal Simulation](hourly_simulation.md)
---

### 4. [Temporal Simulation](hourly_simulation.md)
**File:** `examples/hourly_simulation.py`

Shows how to run time-based simulations with realistic time gaps between interactions. Features:
- Setting and advancing simulation time with datetime objects
- Using CognitiveLoop for integrated LLM operations
- Random time delays between messages
- Memory decay over time

**Best for:** Simulating realistic conversation patterns with temporal dynamics.

---

### 5. [Round-Based Simulation](round_based_simulation.md) 🆕
**File:** `examples/round_based_simulation.py`

Demonstrates using **round-based time** `(day, hour)` tuples instead of datetime objects. Perfect for:
- Game simulations with discrete rounds or turns
- Agent-based models with step-based time
- Economic or social simulations with time periods
- Any scenario where real datetime is not appropriate

**Key Features:**
- Simple `(day, hour)` tuple format where day >= 1, hour in [0, 23]
- Automatic database storage of round-based time
- Full FSRS memory system compatibility
- Can mix with datetime mode as needed

**Best for:** Simulations with discrete time steps rather than continuous time.

---

### 6. Export and Visualization 🆕
**CLI:** `ghostkg export` and `ghostkg serve`

Learn how to export and visualize agent knowledge graphs. GhostKG includes built-in CLI tools for:
- Exporting interaction history to JSON
- Starting a web visualization server
- Interactive timeline and graph exploration
- FSRS memory state heatmaps

See [Visualization Documentation](../VISUALIZATION.md) for complete guide.

**Best for:** Analyzing and visualizing knowledge graph evolution.

**Quick start:**
```bash
# Export and visualize in one command
ghostkg export --database mydb.db --serve --browser

# Or in dev mode (without installation)
python ghostkg_dev.py export --database mydb.db --serve --browser
```

---

## Quick Start

All examples can be run directly from the `examples/` directory:

```bash
cd examples

# Run the existing database integration example 🆕
python existing_database_integration.py

# Run the external program example
python external_program.py

# Run the multi-agent conversation (requires LLM service)
python use_case_example.py

# Run the temporal simulation with datetime
python hourly_simulation.py

# Run the round-based simulation (no LLM required) 🆕
python round_based_simulation.py

# Export and visualize (using CLI) 🆕
ghostkg export --database use_case_example.db --serve --browser

# Or in dev mode
python ../ghostkg_dev.py export --database use_case_example.db --serve --browser
```

## Prerequisites

Different examples have different requirements:

- **Base examples** (external_program.py, hourly_simulation.py): Only core GhostKG
- **LLM examples** (use_case_example.py): Requires an LLM service:
  - **Ollama** (local): Install and run `ollama serve`, then `ollama pull llama3.2`
  - **OpenAI**: Set `OPENAI_API_KEY` environment variable
  - **Anthropic**: Set `ANTHROPIC_API_KEY` environment variable
- **Fast mode**: Requires GLiNER and TextBlob (`pip install gliner textblob`)

See the [Installation Guide](https://github.com/GiulioRossetti/GhostKG#installation) for setup instructions.
