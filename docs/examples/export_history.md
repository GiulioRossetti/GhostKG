# Export and Visualization

**Source:** `examples/export_history.py`

This example shows how to export agent knowledge graphs from the SQLite database to JSON format suitable for visualization tools.

## Overview

After running a simulation (like `use_case_example.py`), you'll have a database file containing:
- Nodes (concepts/entities with memory strength)
- Edges (relationships between concepts)  
- Logs (timestamped actions)

This script:
1. Connects to the database
2. Reconstructs the knowledge graph at each time step
3. Calculates FSRS retrievability scores
4. Exports to JSON for visualization

## Prerequisites

- A database file from a previous simulation (e.g., `use_case_example.db`)
- Basic understanding of SQLite and JSON

## Database Schema

GhostKG stores data in three main tables:

### 1. Nodes Table

```sql
CREATE TABLE nodes (
    owner_id TEXT,          -- Agent name
    id TEXT,                -- Concept name
    stability REAL,         -- FSRS stability
    difficulty REAL,        -- FSRS difficulty
    last_review TEXT,       -- Last review timestamp
    reps INTEGER,           -- Number of reviews
    state INTEGER,          -- FSRS state
    created_at TEXT         -- Creation timestamp
)
```

### 2. Edges Table

```sql
CREATE TABLE edges (
    owner_id TEXT,          -- Agent name
    source TEXT,            -- Source concept
    relation TEXT,          -- Relationship type
    target TEXT,            -- Target concept
    sentiment REAL,         -- Emotional association
    created_at TEXT         -- Creation timestamp
)
```

### 3. Logs Table

```sql
CREATE TABLE logs (
    agent_name TEXT,        -- Agent name
    action_type TEXT,       -- Action (absorb, reply, learn)
    timestamp TEXT,         -- When it happened
    details TEXT            -- Additional info (JSON)
)
```

## Step-by-Step Walkthrough

### Step 1: Connect to Database

```python
import sqlite3
import os

DB_PATH = "use_case_example.db"

if not os.path.exists(DB_PATH):
    print(f"❌ Error: Database not found at {DB_PATH}")
    exit()

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row  # Access columns by name
```

**Key point:** Using `row_factory = sqlite3.Row` lets you access columns like `row["owner_id"]` instead of `row[0]`.

### Step 2: Load All Data

```python
# Get all logs (chronologically ordered)
logs = conn.execute(
    "SELECT * FROM logs ORDER BY timestamp ASC"
).fetchall()

# Get all nodes
all_nodes = conn.execute("SELECT * FROM nodes").fetchall()

# Get all edges  
all_edges = conn.execute("SELECT * FROM edges").fetchall()
```

**Why load everything?** We'll reconstruct the graph state at each time point by filtering based on timestamps.

### Step 3: Initialize Output Structure

```python
history = {
    "metadata": {
        "topic": "Greenland",  # Or extract from logs
        "date": "2025-01-01"
    },
    "agents": ["Alice", "Bob"],
    "steps": []
}
```

**Output format:**
- `metadata`: Simulation information
- `agents`: List of agent names
- `steps`: Array of graph states at each time point

### Step 4: Create Initial State

```python
# Step 0: Before any interactions
history["steps"].append({
    "step": 0,
    "round": 0,
    "action": "Init",
    "graphs": {
        "Alice": {"nodes": [], "links": []},
        "Bob": {"nodes": [], "links": []}
    }
})
```

### Step 5: Process Each Log Entry

```python
for i, log in enumerate(logs):
    # Parse timestamp
    current_time_str = log["timestamp"]
    current_time = datetime.datetime.fromisoformat(current_time_str)
    
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=datetime.timezone.utc)
    
    # Create step data
    step_data = {
        "step": i + 1,
        "round": i + 1,
        "action": f"{log['agent_name']} {log['action_type']} ({current_time.strftime('%H:%M')})",
        "graphs": {}
    }
```

### Step 6: Reconstruct Graph for Each Agent

For each agent at this time point:

```python
for agent in ["Alice", "Bob"]:
    # Gather valid nodes (created before current_time)
    potential_nodes = {}
    
    for n in all_nodes:
        if n["owner_id"] != agent:
            continue
            
        # Parse creation time
        created_at = datetime.datetime.fromisoformat(n["created_at"])
        
        # Skip if node doesn't exist yet
        if created_at > current_time:
            continue
```

### Step 7: Calculate FSRS Retrievability

For each valid node, calculate how strong the memory is:

```python
# Get FSRS parameters
stability = n["stability"]
last_review = datetime.datetime.fromisoformat(n["last_review"])

# Calculate elapsed time
elapsed_days = (current_time - last_review).total_seconds() / 86400
if elapsed_days < 0:
    elapsed_days = 0

# FSRS retrievability formula
if stability > 0:
    retrievability = (1 + elapsed_days / (9 * stability)) ** -1
else:
    retrievability = 1.0  # New memories
```

**What retrievability means:**
- **1.0**: Perfectly remembered (just learned or reviewed)
- **0.9**: Still very strong
- **0.5**: Fading (needs review)
- **0.2**: Almost forgotten
- **<0.1**: Effectively forgotten

### Step 8: Build Node Data

```python
is_self = (n["id"].lower() == "i")

potential_nodes[n["id"]] = {
    "id": n["id"],
    "group": 0 if is_self else 1,  # Visual grouping
    "radius": 25 if is_self else 10 + (stability * 0.5),  # Size by strength
    "retrievability": round(retrievability, 3),
    "stability": round(stability, 2)
}
```

**Visualization hints:**
- `group`: Color grouping (0 = self, 1 = other)
- `radius`: Node size (bigger = stronger memory)
- `retrievability`: Can control opacity

### Step 9: Filter Edges

Only include edges where both nodes exist:

```python
valid_edges = []

for e in all_edges:
    if e["owner_id"] != agent:
        continue
    
    # Check timestamp
    e_created = datetime.datetime.fromisoformat(e["created_at"])
    if e_created > current_time:
        continue
    
    # Check both nodes exist
    if e["source"] in potential_nodes and e["target"] in potential_nodes:
        valid_edges.append({
            "source": e["source"],
            "target": e["target"],
            "label": e["relation"],
            "value": 1,
            "dashed": False
        })
```

**Why check node existence?** Edges are meaningless without their connected nodes.

### Step 10: Prune Orphaned Nodes

Remove nodes that have no connections (except "I"):

```python
touched_node_ids = set()

# Mark nodes that have edges
for edge in valid_edges:
    touched_node_ids.add(edge["source"])
    touched_node_ids.add(edge["target"])

# Always keep "I" node
for node_id in potential_nodes:
    if node_id.lower() == "i":
        touched_node_ids.add(node_id)

# Build final node list
final_nodes = [
    node_data 
    for node_id, node_data in potential_nodes.items()
    if node_id in touched_node_ids
]
```

### Step 11: Export to JSON

```python
import json

OUTPUT_FILE = "simulation_history.json"

with open(OUTPUT_FILE, "w") as f:
    json.dump(history, f, indent=2)

print(f"✅ History exported to {OUTPUT_FILE}")
```

## Output Format

The exported JSON looks like:

```json
{
  "metadata": {
    "topic": "Greenland",
    "date": "2025-01-01"
  },
  "agents": ["Alice", "Bob"],
  "steps": [
    {
      "step": 0,
      "round": 0,
      "action": "Init",
      "graphs": {
        "Alice": {
          "nodes": [
            {
              "id": "I",
              "group": 0,
              "radius": 25,
              "retrievability": 1.0,
              "stability": 5.0
            },
            {
              "id": "Greenland",
              "group": 1,
              "radius": 12.5,
              "retrievability": 0.98,
              "stability": 5.0
            }
          ],
          "links": [
            {
              "source": "I",
              "target": "Greenland",
              "label": "value",
              "value": 1,
              "dashed": false
            }
          ]
        },
        "Bob": { ... }
      }
    },
    {
      "step": 1,
      "round": 1,
      "action": "Bob absorb (10:00)",
      "graphs": { ... }
    }
  ]
}
```

## Visualization Tools

The exported JSON can be used with:

### 1. D3.js Force-Directed Graph

```javascript
// Load the JSON
fetch('simulation_history.json')
  .then(response => response.json())
  .then(data => {
    // Display step 0 initially
    let currentStep = 0;
    renderGraph(data.steps[currentStep].graphs['Alice']);
    
    // Add controls to step through time
    nextButton.onclick = () => {
      currentStep++;
      renderGraph(data.steps[currentStep].graphs['Alice']);
    };
  });
```

### 2. Cytoscape.js

```javascript
cytoscape({
  container: document.getElementById('cy'),
  elements: {
    nodes: data.steps[step].graphs[agent].nodes.map(n => ({
      data: { 
        id: n.id,
        size: n.radius,
        opacity: n.retrievability
      }
    })),
    edges: data.steps[step].graphs[agent].links.map(e => ({
      data: { 
        source: e.source,
        target: e.target,
        label: e.label
      }
    }))
  }
});
```

### 3. NetworkX (Python)

```python
import networkx as nx
import matplotlib.pyplot as plt

# Load JSON
with open('simulation_history.json') as f:
    data = json.load(f)

# Create graph for Alice at step 5
step_data = data['steps'][5]['graphs']['Alice']

G = nx.DiGraph()
for node in step_data['nodes']:
    G.add_node(node['id'], 
               retrievability=node['retrievability'],
               stability=node['stability'])

for edge in step_data['links']:
    G.add_edge(edge['source'], edge['target'], 
               label=edge['label'])

# Draw
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True)
plt.show()
```

## Memory Evolution Analysis

You can analyze how knowledge evolved:

```python
# Load the history
with open('simulation_history.json') as f:
    history = json.load(f)

# Track a specific concept over time
concept = "Greenland"
agent = "Alice"

for step in history['steps']:
    nodes = step['graphs'][agent]['nodes']
    node = next((n for n in nodes if n['id'] == concept), None)
    
    if node:
        print(f"Step {step['step']}: R={node['retrievability']:.2f}, S={node['stability']:.2f}")
```

**Output:**
```
Step 0: R=1.00, S=5.00
Step 1: R=0.98, S=5.00
Step 2: R=0.96, S=5.50
Step 5: R=0.85, S=6.20
Step 10: R=0.72, S=7.00
```

Shows how the concept's retrievability and stability changed.

## Troubleshooting

### Database Not Found

```python
if not os.path.exists(DB_PATH):
    print(f"❌ Error: Database not found at {DB_PATH}")
    print("Run use_case_example.py first to create the database")
    exit()
```

### Empty Database

```python
if not logs:
    print("⚠️ Warning: Database is empty.")
    print("No simulation data to export.")
    exit()
```

### Timestamp Parsing Errors

```python
try:
    current_time = datetime.datetime.fromisoformat(current_time_str)
except:
    # Fallback to current time
    current_time = datetime.datetime.now(datetime.timezone.utc)
```

## Running the Example

```bash
# First, run a simulation to create the database
cd examples
python use_case_example.py

# Then export the history
python export_history.py
```

**Output:**
```
📂 Working Directory: /path/to/GhostKG
✅ History exported to ghost_kg/templates/simulation_history.json
```

## Customization

### Change Output Location

```python
OUTPUT_DIR = "./visualizations"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "my_simulation.json")
```

### Filter by Time Range

```python
# Only export steps between Day 1 and Day 3
start_time = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
end_time = datetime.datetime(2025, 1, 3, tzinfo=datetime.timezone.utc)

for log in logs:
    current_time = datetime.datetime.fromisoformat(log["timestamp"])
    if start_time <= current_time <= end_time:
        # Process this step
```

### Include Additional Metadata

```python
step_data = {
    "step": i + 1,
    "action": f"{log['agent_name']} {log['action_type']}",
    "timestamp": current_time.isoformat(),
    "details": json.loads(log["details"]) if log["details"] else {},
    "graphs": {}
}
```

## Next Steps

- Build a web-based visualization using D3.js
- Create animated timelines showing graph evolution
- Compare knowledge graphs between multiple agents
- Analyze memory decay patterns across simulations
- Export to Gephi format for advanced network analysis

## Pro Tips

1. **Run simulations first**: Export requires existing database
2. **Check timestamps**: Ensure consistent timezone handling
3. **Prune orphans**: Remove isolated nodes for cleaner visualization
4. **Use retrievability for opacity**: Faded nodes = faded memories
5. **Animate transitions**: Show how graphs change over time
