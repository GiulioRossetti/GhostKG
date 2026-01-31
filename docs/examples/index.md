# Examples Overview

This section provides step-by-step walkthroughs of the example scripts included with GhostKG. Each example demonstrates different features and use cases of the library.

## Available Examples

### 1. [External Program Integration](external_program.md)
**File:** `examples/external_program.py`

Learn how to integrate GhostKG with your own application that uses external LLMs (like GPT-4, Claude, etc.) for text generation. This example shows:
- How to use the AgentManager API
- Managing agent knowledge graphs from an external program
- Extracting triplets externally and updating agent memories
- Simulating multi-round conversations with time progression

**Best for:** Building applications where you control the LLM and use GhostKG purely for knowledge management.

---

### 2. [Multi-Agent Conversation](use_case_example.md)
**File:** `examples/use_case_example.py`

A complete example of two agents (Alice and Bob) having a multi-round conversation about Greenland using Ollama's LLaMA model. Demonstrates:
- Setting up the simulation time
- Processing content and retrieving context atomically
- Using external LLM for response generation
- Both Fast Mode (GLiNER) and LLM Mode for triplet extraction
- Knowledge graph evolution over time

**Best for:** Understanding the complete workflow of multi-agent simulations.

---

### 3. [Temporal Simulation](hourly_simulation.md)
**File:** `examples/hourly_simulation.py`

Shows how to run time-based simulations with realistic time gaps between interactions. Features:
- Setting and advancing simulation time
- Using CognitiveLoop for integrated LLM operations
- Random time delays between messages
- Memory decay over time

**Best for:** Simulating realistic conversation patterns with temporal dynamics.

---

### 4. [Export and Visualization](export_history.md)
**File:** `examples/export_history.py`

Learn how to export agent knowledge graphs for visualization. This example:
- Connects to the SQLite database
- Extracts nodes and edges with temporal filtering
- Calculates FSRS retrievability scores
- Exports to JSON format for visualization tools

**Best for:** Analyzing and visualizing knowledge graph evolution.

---

## Quick Start

All examples can be run directly from the `examples/` directory:

```bash
cd examples

# Run the external program example
python external_program.py

# Run the multi-agent conversation (requires Ollama)
python use_case_example.py

# Run the temporal simulation
python hourly_simulation.py

# Export history from a previous simulation
python export_history.py
```

## Prerequisites

Different examples have different requirements:

- **Base examples** (external_program.py, hourly_simulation.py): Only core GhostKG
- **LLM examples** (use_case_example.py): Requires Ollama with llama3.2 model
- **Fast mode**: Requires GLiNER and TextBlob (`pip install gliner textblob`)

See the [Installation Guide](https://github.com/GiulioRossetti/GhostKG#installation) for setup instructions.
