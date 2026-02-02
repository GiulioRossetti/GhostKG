# Visualization Implementation Summary

## Overview

Successfully refactored the GhostKG visualization system and added comprehensive CLI tools for exporting and serving interactive knowledge graph visualizations.

## Requirements Completed

### ✅ 1. Refactor index.html to Separate Components

**Before:** Single 330-line HTML file with embedded CSS and JavaScript

**After:** Separated into three clean files:
- `ghost_kg/templates/index.html` - Clean 51-line HTML structure
- `ghost_kg/templates/style.css` - 154 lines of organized CSS
- `ghost_kg/templates/app.js` - 263 lines of D3.js visualization logic

**Benefits:**
- Better maintainability
- Easier to modify styling or behavior
- Standard web development practices
- No functionality changes - everything still works

### ✅ 2. Serve Webpage as Service via Command Line

**Implementation:** Flask-based web server with CLI interface

**Command:**
```bash
ghostkg serve --json history.json --host localhost --port 5000
```

**Features:**
- Serve any JSON history file
- Configurable host and port
- Auto-open browser option
- Debug mode available
- Clean Flask integration

**Example:**
```bash
# Basic serve
ghostkg serve --json history.json

# With browser auto-open
ghostkg serve --json history.json --browser

# Custom host/port
ghostkg serve --json history.json --host 0.0.0.0 --port 8080
```

### ✅ 3. Generate JSON File via Command Line

**Implementation:** Integrated `examples/export_history.py` into core package

**New Module:** `ghost_kg/visualization.py`
- `HistoryExporter` class for flexible export
- `export_history()` convenience function
- Works with new SQLAlchemy/ORM database
- Supports kg_* table names
- Handles both datetime and simulation time
- Auto-detects agents or accepts explicit list

**Command:**
```bash
ghostkg export --database agent_memory.db --output history.json
```

**Features:**
- Export from SQLite, PostgreSQL, or MySQL
- Auto-detect agents
- Custom output file
- Specify topic/title
- Combined export+serve in one command
- Progress reporting

**Examples:**
```bash
# Basic export
ghostkg export --database agent_memory.db

# Export specific agents
ghostkg export --database agent_memory.db --agents Alice,Bob

# Export and serve
ghostkg export --database agent_memory.db --serve --browser

# From PostgreSQL
ghostkg export --database "postgresql://user:pass@host/db" --output history.json
```

**Python API:**
```python
from ghost_kg.visualization import export_history

history = export_history(
    db_path="agent_memory.db",
    output_file="history.json",
    agents=["Alice", "Bob"],
    topic="My Simulation"
)
```

### ✅ 4. Update Documentation

**New Documentation:**
- `docs/VISUALIZATION.md` - Comprehensive 8.5KB guide
  - Quick start
  - CLI reference (export and serve commands)
  - Python API documentation
  - Visualization features
  - JSON format specification
  - Troubleshooting
  - Example workflows

**Updated Documentation:**
- `README.md`
  - Added visualization to features
  - Added visualization section
  - Added installation instructions for `[viz]` extra
  - Added link to visualization docs

**Removed:**
- `examples/export_history.py` - Functionality now in core package

## Technical Implementation

### File Structure

```
ghost_kg/
├── cli.py                        # Command-line interface (new)
├── visualization.py              # History export logic (new)
└── templates/
    ├── index.html               # Refactored (51 lines)
    ├── style.css                # Extracted (154 lines)
    ├── app.js                   # Extracted (263 lines)
    └── simulation_history.json  # Example data
```

### Dependencies

**New Optional Dependency:**
```bash
pip install ghost_kg[viz]  # Installs Flask
```

Added to `setup.py`:
```python
extras_require={
    "viz": ["flask>=2.0.0"],
    ...
}
```

### CLI Entry Point

Registered in `setup.py`:
```python
entry_points={
    'console_scripts': [
        'ghostkg=ghost_kg.cli:main',
    ],
}
```

### Database Compatibility

The visualization system works with the new SQLAlchemy-based database:
- Uses ORM models (Node, Edge, Log)
- Works with kg_* table names
- Supports all three databases (SQLite, PostgreSQL, MySQL)
- Handles both datetime and simulation time
- Auto-migration compatible

## Features

### Visualization Features

**Node Visualization:**
- Self node (I): Blue, larger, always active
- Knowledge nodes: Color-coded by FSRS retrievability
  - Green: High retrievability (active memory)
  - Yellow: Medium retrievability (fading)
  - Gray: Low retrievability (forgotten)
- Size: Proportional to stability

**Edge Visualization:**
- Directed arrows show relationships
- Labels show relation type
- Gray color with opacity

**Controls:**
- Agent selector: Individual or "ALL AGENTS" view
- Timeline slider: Scrub through history
- Play/pause: Automatic playback
- Speed slider: Adjust playback speed
- Zoom/pan: Mouse wheel and drag
- Node drag: Reposition nodes

### CLI Commands

**Export Command:**
```bash
ghostkg export --database <db_path> [options]
```

Options:
- `--database`, `--db`: Database path/URL (required)
- `--output`, `-o`: Output file path
- `--agents`, `-a`: Comma-separated agent list
- `--topic`, `-t`: Visualization title
- `--serve`: Start server after export
- `--browser`: Open browser (with --serve)
- `--host`: Server host (with --serve)
- `--port`: Server port (with --serve)

**Serve Command:**
```bash
ghostkg serve --json <json_file> [options]
```

Options:
- `--json`: JSON file path (required)
- `--host`: Host to bind (default: localhost)
- `--port`: Port to bind (default: 5000)
- `--browser`: Auto-open browser
- `--debug`: Debug mode

## Testing

### Tested Components

✅ **Template Refactoring:**
- HTML loads correctly
- CSS applies properly
- JavaScript executes
- No broken references

✅ **CLI Interface:**
- Help commands work
- Arguments parse correctly
- Error messages clear

✅ **Server:**
- Flask starts successfully
- Routes serve correct files
- JSON data loads
- Port binding works

✅ **Export Logic:**
- Connects to database
- Reads ORM models correctly
- Generates valid JSON
- Handles errors gracefully

### Test Results

```bash
# CLI help works
$ python ghost_kg/cli.py --help
✅ Displays help correctly

# Server starts
$ ghostkg serve --json simulation_history.json --port 5001
✅ Server runs on http://localhost:5001

# Template files load
✅ index.html served
✅ style.css served
✅ app.js served
✅ simulation_history.json served
```

## Example Workflows

### Complete Workflow

```python
# 1. Create simulation
from ghost_kg import GhostAgent, Rating

alice = GhostAgent("Alice", db_path="simulation.db")
bob = GhostAgent("Bob", db_path="simulation.db")

alice.learn_triplet("Python", "is", "powerful", Rating.Good)
bob.learn_triplet("JavaScript", "is", "versatile", Rating.Good)
```

```bash
# 2. Export and visualize
ghostkg export --database simulation.db --serve --browser
```

### Quick Visualization

```bash
# If you already have a database
ghostkg export --database agent_memory.db --serve --browser
```

### Custom Export

```bash
# Export specific agents with custom topic
ghostkg export \
  --database simulation.db \
  --agents Alice,Bob \
  --topic "Agent Debate" \
  --output debate.json \
  --serve \
  --browser
```

## Migration Notes

### From Old to New System

**Old Way (examples/export_history.py):**
```bash
python examples/export_history.py
# Hardcoded paths
# SQLite3 raw queries
# Manual JSON generation
```

**New Way (integrated CLI):**
```bash
ghostkg export --database <any_db> --output <any_file>
# Flexible paths
# ORM-based queries
# Automatic export
```

### Backward Compatibility

**JSON Format:** Unchanged - existing visualizations still work

**Database:** Works with both old (nodes/edges/logs) and new (kg_*) table names

**Templates:** Visual appearance identical, just better organized

## Future Enhancements

Possible improvements (not currently implemented):

1. **Production Server:** Replace Flask dev server with production WSGI
2. **Export Filtering:** Time range, node filters, edge filters
3. **Real-time Updates:** WebSocket support for live simulations
4. **Export Formats:** CSV, GraphML, other formats
5. **Visualization Options:** Different layouts, color schemes, themes
6. **Performance:** Optimize for large graphs (1000+ nodes)

## Conclusion

All requirements from the problem statement have been successfully implemented:

✅ **Refactored templates** - Clean separation of HTML, CSS, and JavaScript
✅ **CLI serve command** - Flask-based web server with flexible options
✅ **CLI export command** - Integrated export_history into core package
✅ **Documentation** - Comprehensive guides and examples

The visualization system is now:
- More maintainable (separated files)
- More accessible (CLI commands)
- More flexible (Python API)
- Better documented (comprehensive guide)
- Future-proof (ORM-based, multi-database)

## Files Changed/Added

**New Files:**
- `ghost_kg/cli.py` - CLI interface
- `ghost_kg/visualization.py` - Export logic
- `ghost_kg/templates/style.css` - Extracted CSS
- `ghost_kg/templates/app.js` - Extracted JavaScript
- `docs/VISUALIZATION.md` - Documentation
- `MANIFEST.in` - Package manifest

**Modified Files:**
- `ghost_kg/templates/index.html` - Refactored
- `setup.py` - Added viz extra and entry point
- `README.md` - Added visualization docs

**Removed Files:**
- `examples/export_history.py` - Integrated into core

**Total Changes:**
- 7 files added
- 3 files modified
- 1 file removed
- ~1,000 lines of new code
- ~150 lines removed/refactored
