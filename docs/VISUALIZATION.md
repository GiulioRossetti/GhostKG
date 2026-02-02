# Visualization

GhostKG provides an interactive web-based visualization for exploring how agent knowledge graphs evolve over time.

## Overview

The visualization system includes:

- **Interactive Memory Heatmap**: D3.js-powered force-directed graph showing nodes and relationships
- **Temporal Playback**: Step through agent interactions chronologically
- **Multi-Agent View**: Switch between individual agents or view all agents together
- **FSRS Memory Tracking**: Node colors represent memory retrievability (forgetting curve)

## Quick Start

### 1. Export History from Database

```bash
# Export from your database
ghostkg export --database agent_memory.db --output history.json

# Export with specific agents
ghostkg export --database agent_memory.db --agents Alice,Bob --output history.json

# Export and automatically start server
ghostkg export --database agent_memory.db --serve --browser
```

### 2. Serve Visualization

```bash
# Serve existing JSON file
ghostkg serve --json history.json

# Open browser automatically
ghostkg serve --json history.json --browser

# Custom host and port
ghostkg serve --json history.json --host 0.0.0.0 --port 8080
```

## Command Line Interface

### Export Command

Export interaction history from a GhostKG database to JSON format.

```bash
ghostkg export --database <db_path> [options]
```

**Options:**
- `--database`, `--db` (required): Path to database file or connection string
- `--output`, `-o`: Output JSON file path (default: templates/simulation_history.json)
- `--agents`, `-a`: Comma-separated list of agent names (default: auto-detect)
- `--topic`, `-t`: Title/topic for visualization (default: "Knowledge Graph Evolution")
- `--serve`: Start server after export
- `--browser`: Open browser automatically (requires --serve)
- `--host`: Server host (default: localhost, requires --serve)
- `--port`: Server port (default: 5000, requires --serve)

**Examples:**
```bash
# Basic export
ghostkg export --database agent_memory.db

# Export specific agents to custom file
ghostkg export --database agent_memory.db --agents Alice,Bob --output my_history.json

# Export and serve with browser
ghostkg export --database agent_memory.db --serve --browser

# Export from PostgreSQL database
ghostkg export --database "postgresql://user:pass@localhost/ghostkg" --output history.json
```

### Serve Command

Start a web server to visualize exported history.

```bash
ghostkg serve --json <json_file> [options]
```

**Options:**
- `--json`, `--json-file` (required): Path to JSON history file
- `--host`: Host to bind server (default: localhost)
- `--port`: Port to bind server (default: 5000)
- `--browser`: Open browser automatically
- `--debug`: Run server in debug mode

**Examples:**
```bash
# Basic serve
ghostkg serve --json history.json

# Serve with browser
ghostkg serve --json history.json --browser

# Serve on all interfaces
ghostkg serve --json history.json --host 0.0.0.0 --port 8080

# Debug mode
ghostkg serve --json history.json --debug
```

## Python API

You can also export history programmatically:

```python
from ghost_kg.visualization import export_history

# Basic export
history = export_history(
    db_path="agent_memory.db",
    output_file="history.json"
)

# With specific agents and topic
history = export_history(
    db_path="agent_memory.db",
    output_file="history.json",
    agents=["Alice", "Bob"],
    topic="Multi-Agent Simulation"
)

# Export from PostgreSQL
history = export_history(
    db_path="postgresql://user:pass@localhost/ghostkg",
    output_file="history.json"
)
```

Using the `HistoryExporter` class:

```python
from ghost_kg.visualization import HistoryExporter

exporter = HistoryExporter(db_path="agent_memory.db")
history = exporter.export_history(
    output_file="history.json",
    agents=["Alice", "Bob"],
    topic="My Simulation"
)
```

## Visualization Features

### Node Visualization

- **Self Node (I)**: Blue circle, larger radius, always fully active
- **Knowledge Nodes**: Colored by FSRS retrievability:
  - 🟢 Green: High retrievability (recently accessed, strong memory)
  - 🟡 Yellow: Medium retrievability (fading memory)
  - ⚫ Gray: Low retrievability (forgotten)
- **Node Size**: Proportional to stability (larger = more stable memory)

### Edge Visualization

- **Arrows**: Indicate relationship direction
- **Labels**: Show the relationship type
- **Color**: Gray with 60% opacity

### Controls

- **Agent Selector**: Choose individual agent or "ALL AGENTS" view
- **Timeline Slider**: Scrub through history steps
- **Play/Pause Button**: Automatic playback
- **Speed Slider**: Adjust playback speed (100ms to 2000ms per step)
- **Zoom/Pan**: Mouse wheel to zoom, drag background to pan
- **Node Drag**: Drag nodes to reposition (double-click to release)

### ALL AGENTS View

When "ALL AGENTS (Consolidated)" is selected:
- Merges knowledge from all agents
- Removes duplicate nodes and edges
- Excludes self-referential "I" connections for clarity
- Shows shared knowledge across agents

## Installation

The visualization feature requires Flask:

```bash
# Install with visualization support
pip install ghost_kg[viz]

# Or install Flask separately
pip install flask
```

## File Structure

The visualization system uses these files:

```
ghost_kg/
├── cli.py                        # Command-line interface
├── visualization.py              # History export logic
└── templates/
    ├── index.html               # Main HTML page
    ├── style.css                # Stylesheet
    ├── app.js                   # JavaScript application
    └── simulation_history.json  # Example data
```

## JSON Format

The exported history JSON has this structure:

```json
{
  "metadata": {
    "topic": "Knowledge Graph Evolution",
    "date": "2024-01-15T10:30:00",
    "exported_at": "2024-01-15 10:30:00"
  },
  "agents": ["Alice", "Bob"],
  "steps": [
    {
      "step": 0,
      "round": 0,
      "action": "Initialization",
      "graphs": {
        "Alice": {
          "nodes": [
            {
              "id": "I",
              "group": 0,
              "radius": 25,
              "retrievability": 1.0,
              "stability": 0.0
            }
          ],
          "links": []
        }
      }
    }
  ]
}
```

## Troubleshooting

### "Module 'flask' not found"

Install Flask:
```bash
pip install ghost_kg[viz]
```

### "Database not found"

Ensure the database path is correct:
```bash
# Check if file exists
ls -l agent_memory.db

# Use absolute path
ghostkg export --database /full/path/to/agent_memory.db
```

### "No interaction logs found"

The database must contain logged interactions. Make sure agents have performed actions that were logged.

### Server doesn't start

Check if the port is already in use:
```bash
# Use a different port
ghostkg serve --json history.json --port 5001
```

### JSON file is empty

Ensure the database has content and the export completed successfully. Check the export output for errors.

## Example Workflow

Complete workflow from simulation to visualization:

```python
from ghost_kg import GhostAgent, Rating

# Create agents
alice = GhostAgent("Alice", db_path="simulation.db")
bob = GhostAgent("Bob", db_path="simulation.db")

# Run simulation
alice.learn_triplet("Python", "is", "powerful", Rating.Good)
bob.learn_triplet("JavaScript", "is", "versatile", Rating.Good)
alice.learn_triplet("Python", "beats", "JavaScript", Rating.Good)
bob.learn_triplet("JavaScript", "beats", "Python", Rating.Good)
```

Then from command line:

```bash
# Export and visualize
ghostkg export --database simulation.db --serve --browser
```

## Advanced Usage

### Custom Topic and Agents

```bash
ghostkg export \
  --database simulation.db \
  --agents Alice,Bob,Charlie \
  --topic "Multi-Agent Debate Simulation" \
  --output debate_history.json \
  --serve \
  --browser
```

### Production Deployment

For production, use a production-grade WSGI server:

```bash
# Export history
ghostkg export --database production.db --output /var/www/history.json

# Serve with gunicorn (install separately)
gunicorn -w 4 -b 0.0.0.0:8000 'ghost_kg.cli:create_app("/var/www/history.json")'
```

Note: The CLI currently uses Flask's development server. For production, consider implementing a proper WSGI application.

## See Also

- [Core Components](CORE_COMPONENTS.md) - Agent and memory system architecture
- [Database Schema](DATABASE_SCHEMA.md) - Database structure
- [Examples](examples/) - Code examples and tutorials
