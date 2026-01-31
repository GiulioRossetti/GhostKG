# Configuration API

The configuration module provides dataclasses for managing GhostKG settings across different components.

## Module Location

```python
# Recommended: Import from top-level package
from ghost_kg import GhostKGConfig, FSRSConfig, DatabaseConfig, LLMConfig, FastModeConfig

# Also supported: Import from subpackage
from ghost_kg.utils import GhostKGConfig, FSRSConfig, DatabaseConfig, LLMConfig, FastModeConfig
```

## Overview

Configuration classes available:

- **GhostKGConfig**: Main configuration container
- **FSRSConfig**: FSRS algorithm parameters
- **DatabaseConfig**: Database settings
- **LLMConfig**: LLM integration settings
- **FastModeConfig**: Fast extraction settings

## Basic Usage

```python
from ghost_kg.config import (
    GhostKGConfig,
    FSRSConfig,
    DatabaseConfig,
    LLMConfig,
    get_default_config
)

# Get default configuration
config = get_default_config()

# Create custom configuration
custom_config = GhostKGConfig(
    fsrs=FSRSConfig(
        request_retention=0.9,
        maximum_interval=36500
    ),
    database=DatabaseConfig(
        db_path="custom.db",
        enable_wal=True
    ),
    llm=LLMConfig(
        host="http://localhost:11434",
        model="llama3.2",
        timeout=60
    )
)

# Use configuration
print(f"Database path: {config.database.db_path}")
print(f"FSRS retention: {config.fsrs.request_retention}")
```

## Configuration File

Configuration can be loaded from YAML or JSON:

```yaml
# config.yaml
fsrs:
  request_retention: 0.9
  maximum_interval: 36500
  
database:
  db_path: "agents.db"
  enable_wal: true
  
llm:
  host: "http://localhost:11434"
  model: "llama3.2"
  timeout: 60
```

```python
from ghost_kg.config import GhostKGConfig

# Load from file
config = GhostKGConfig.from_yaml("config.yaml")
# or
config = GhostKGConfig.from_json("config.json")

# Save to file
config.to_yaml("config.yaml")
config.to_json("config.json")
```

## FSRS Configuration

Key parameters for memory modeling:

- **request_retention**: Target retention rate (0.0-1.0)
- **maximum_interval**: Max days between reviews
- **w**: FSRS weight parameters (17 values)

## API Reference

::: ghost_kg.utils.config.GhostKGConfig
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: ghost_kg.utils.config.FSRSConfig
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: ghost_kg.utils.config.DatabaseConfig
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: ghost_kg.utils.config.LLMConfig
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

::: ghost_kg.utils.config.FastModeConfig
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3
