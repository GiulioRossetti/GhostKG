# CognitiveLoop API

The `CognitiveLoop` class provides high-level cognitive operations for agents, including absorbing information, reflecting on statements, and generating contextual replies.

## Overview

CognitiveLoop offers:

- **absorb()**: Learn from incoming text using fast or LLM-based extraction
- **reflect()**: Reinforce beliefs from own statements
- **reply()**: Generate contextual responses based on memory

## Basic Usage

```python
from ghost_kg import GhostAgent, CognitiveLoop
import datetime

# Create agent and cognitive loop
agent = GhostAgent("Alice", db_path="agent.db")
loop = CognitiveLoop(agent, model="llama3.2", fast_mode=False)

# Set time
agent.set_time(datetime.datetime.now(datetime.timezone.utc))

# Agent reads and processes content
loop.absorb("I think UBI is necessary.", author="Bob")

# Agent generates reply
response = loop.reply("UBI", partner_name="Bob")
print(response)

# Agent reflects on own statement
loop.reflect("I believe in economic security")
```

## Extraction Modes

### Fast Mode
- Uses GLiNER for entity extraction
- Uses TextBlob for sentiment analysis
- No LLM required
- Fast processing (~100 messages/second)

### LLM Mode
- Uses Ollama for semantic triplet extraction
- Higher quality extraction
- Requires LLM server
- Slower processing (~1-5 messages/second)

## API Reference

::: ghost_kg.cognitive.CognitiveLoop
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3
