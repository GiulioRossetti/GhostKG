# GhostKG Configuration Guide

This guide explains how to configure GhostKG using the configuration system.

## Overview

GhostKG uses a dataclass-based configuration system that provides:

- Type-safe configuration with validation
- Multiple loading methods (code, env vars, YAML, JSON)
- Sensible defaults for quick start
- Clear documentation of all options

## Configuration Structure

```
GhostKGConfig
├── FSRSConfig        # FSRS algorithm parameters
├── DatabaseConfig    # Database settings
├── LLMConfig         # LLM settings
└── FastModeConfig    # Fast mode extraction settings
```

## Quick Start

### Default Configuration

The simplest way to use GhostKG is with default settings:

```python
from ghost_kg import GhostKGConfig

config = GhostKGConfig()
```

This uses:

- Default FSRS parameters optimized for general use
- SQLite database at `./agent_memory.db`
- Ollama at `localhost:11434` with `llama3.2` model
- Standard fast mode settings

### Custom Configuration

Override specific settings while keeping other defaults:

```python
from ghost_kg import GhostKGConfig, LLMConfig, DatabaseConfig

config = GhostKGConfig(
    llm=LLMConfig(
        host="http://my-server:11434",
        model="llama2",
        timeout=60
    ),
    database=DatabaseConfig(
        path="/data/agents.db",
        timeout=10.0
    )
)
```

## Configuration Methods

### 1. From Code (Recommended for Defaults)

Direct instantiation with defaults or custom values:

```python
from ghost_kg import GhostKGConfig

# Use all defaults
config = GhostKGConfig()

# Or customize
from ghost_kg import LLMConfig

config = GhostKGConfig(
    llm=LLMConfig(model="llama2")
)
```

**Pros**: Type-safe, auto-complete support, clear at code level
**Cons**: Settings hardcoded in code

### 2. From Environment Variables (Recommended for Deployment)

Set environment variables with `GHOSTKG_` prefix:

```bash
export GHOSTKG_LLM_HOST=http://my-server:11434
export GHOSTKG_LLM_MODEL=llama2
export GHOSTKG_LLM_TIMEOUT=60
export GHOSTKG_DATABASE_PATH=/data/agents.db
export GHOSTKG_DATABASE_TIMEOUT=10.0
```

Load in code:

```python
from ghost_kg import GhostKGConfig

config = GhostKGConfig.from_env()
```

**Environment Variable Format**: `GHOSTKG_{SECTION}_{PARAMETER}`

- Section: `LLM`, `DATABASE`, `FAST_MODE`
- Parameter: uppercase version of config attribute

**Type Conversion**:

- Strings: Used as-is
- Integers: Auto-converted (e.g., `GHOSTKG_LLM_TIMEOUT=60`)
- Floats: Auto-converted (e.g., `GHOSTKG_DATABASE_TIMEOUT=10.5`)
- Booleans: `true`/`1`/`yes`/`on` → True, otherwise False

**Pros**: Environment-specific, 12-factor app compliant, secure
**Cons**: Must document variable names

### 3. From YAML File (Recommended for Complex Configs)

Create a `config.yaml` file:

```yaml
llm:
  host: http://my-server:11434
  model: llama2
  timeout: 60
  max_retries: 5

database:
  path: /data/agents.db
  timeout: 10.0

fast_mode:
  gliner_model: urchade/gliner_small-v2.1
  entity_labels:
    - Topic
    - Person
    - Concept
```

Load in code:

```python
from ghost_kg import GhostKGConfig

config = GhostKGConfig.from_yaml("config.yaml")
```

**Requirements**: `pip install pyyaml` or `uv pip install pyyaml`

**Pros**: Human-readable, supports comments, complex structures
**Cons**: Requires PyYAML dependency

### 4. From JSON File

Create a `config.json` file:

```json
{
  "llm": {
    "host": "http://my-server:11434",
    "model": "llama2",
    "timeout": 60
  },
  "database": {
    "path": "/data/agents.db",
    "timeout": 10.0
  }
}
```

Load in code:

```python
from ghost_kg import GhostKGConfig

config = GhostKGConfig.from_json("config.json")
```

**Pros**: Standard library only, machine-readable
**Cons**: No comments, less human-friendly than YAML

### 5. From Dictionary

Useful for programmatic configuration:

```python
from ghost_kg import GhostKGConfig

config_dict = {
    "llm": {"model": "llama2"},
    "database": {"path": "/data/agents.db"}
}

config = GhostKGConfig.from_dict(config_dict)
```

**Pros**: Flexible, programmatic, testable
**Cons**: No IDE support, easy to make typos

## Configuration Options Reference

### FSRSConfig

FSRS (Free Spaced Repetition Scheduler) algorithm configuration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parameters` | `List[float]` | 21 optimized values | FSRS algorithm parameters |

**Example**:
```python
from ghost_kg import FSRSConfig

fsrs = FSRSConfig(
    parameters=[0.212, 1.2931, 2.3065, ...]  # 21 float values
)
```

**Note**: The default parameters are optimized for general use. Only modify if you understand the FSRS algorithm.

### DatabaseConfig

SQLite database configuration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | `"agent_memory.db"` | Path to SQLite database file |
| `check_same_thread` | `bool` | `False` | SQLite thread safety check |
| `timeout` | `float` | `5.0` | Connection timeout in seconds |

**Example**:
```python
from ghost_kg import DatabaseConfig

db = DatabaseConfig(
    path="/data/production.db",
    timeout=10.0
)
```

**Environment Variables**:
```bash
GHOSTKG_DATABASE_PATH=/data/production.db
GHOSTKG_DATABASE_TIMEOUT=10.0
GHOSTKG_DATABASE_CHECK_SAME_THREAD=false
```

### LLMConfig

Language model (Ollama) configuration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | `$OLLAMA_HOST` or `http://localhost:11434` | Ollama server URL |
| `model` | `str` | `"llama3.2"` | Model name |
| `timeout` | `int` | `30` | Request timeout in seconds |
| `max_retries` | `int` | `3` | Maximum retry attempts |

**Example**:
```python
from ghost_kg import LLMConfig

llm = LLMConfig(
    host="http://gpu-server:11434",
    model="llama2",
    timeout=60,
    max_retries=5
)
```

**Environment Variables**:
```bash
GHOSTKG_LLM_HOST=http://gpu-server:11434
GHOSTKG_LLM_MODEL=llama2
GHOSTKG_LLM_TIMEOUT=60
GHOSTKG_LLM_MAX_RETRIES=5
```

### FastModeConfig

Fast mode entity extraction configuration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gliner_model` | `str` | `"urchade/gliner_small-v2.1"` | GLiNER model name/path |
| `entity_labels` | `List[str]` | `["Topic", "Person", "Concept", "Organization"]` | Entity types to extract |
| `sentiment_thresholds` | `Dict[str, float]` | See below | Sentiment classification thresholds |

**Default Sentiment Thresholds**:
```python
{
    "support": 0.3,    # Polarity >= 0.3 → support
    "oppose": -0.3,    # Polarity <= -0.3 → oppose
    "like": 0.1,       # Polarity >= 0.1 → like
    "dislike": -0.1,   # Polarity <= -0.1 → dislike
}
```

**Example**:
```python
from ghost_kg import FastModeConfig

fast = FastModeConfig(
    gliner_model="custom-model",
    entity_labels=["Person", "Organization", "Location"],
    sentiment_thresholds={
        "support": 0.4,
        "oppose": -0.4,
    }
)
```

**Environment Variables**:
```bash
GHOSTKG_FAST_MODE_GLINER_MODEL=custom-model
# Note: Lists and dicts best configured via file or code
```

## Common Use Cases

### Development Setup

Use defaults for quick local development:

```python
from ghost_kg import GhostKGConfig

config = GhostKGConfig()  # Uses localhost Ollama, local DB
```

### Production Deployment

Use environment variables for security and flexibility:

```bash
# In .env or deployment config
export GHOSTKG_DATABASE_PATH=/var/lib/ghostkg/production.db
export GHOSTKG_LLM_HOST=http://llm-server:11434
export GHOSTKG_LLM_MODEL=llama2
export GHOSTKG_LLM_TIMEOUT=60
```

```python
from ghost_kg import GhostKGConfig

config = GhostKGConfig.from_env()
```

### Testing

Use in-memory database and mock LLM:

```python
from ghost_kg import GhostKGConfig, DatabaseConfig

config = GhostKGConfig(
    database=DatabaseConfig(path=":memory:")
)
```

### Multiple Environments

Use different config files per environment:

```python
import os
from ghost_kg import GhostKGConfig

env = os.getenv("ENVIRONMENT", "development")
config_file = f"config.{env}.yaml"

config = GhostKGConfig.from_yaml(config_file)
```

## Validation

All configurations are automatically validated when loaded:

```python
from ghost_kg import GhostKGConfig, LLMConfig
from ghost_kg.exceptions import ConfigurationError

try:
    config = GhostKGConfig(
        llm=LLMConfig(timeout=-1)  # Invalid!
    )
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

**Validation Rules**:

- Database path cannot be empty
- All timeout values must be positive
- LLM max_retries must be at least 1
- FSRS parameters must be exactly 17 floats
- Entity labels cannot be empty

## Best Practices

1. **Use Defaults First**: Start with default configuration and only customize what you need
2. **Environment Variables in Production**: Use env vars for deployment-specific settings
3. **Files for Complex Configs**: Use YAML/JSON for complex configurations with many options
4. **Validate Early**: Call `config.validate()` explicitly if building configs programmatically
5. **Document Custom Settings**: Comment why you deviate from defaults
6. **Security**: Never commit credentials in config files; use environment variables
7. **Testing**: Use separate configs for test environments

## Troubleshooting

### "Configuration file not found"

**Problem**: File path is incorrect or file doesn't exist

**Solution**: Check the path is correct, use absolute paths, or check working directory

```python
from pathlib import Path

config_path = Path(__file__).parent / "config.yaml"
config = GhostKGConfig.from_yaml(str(config_path))
```

### "Invalid YAML/JSON"

**Problem**: Syntax error in configuration file

**Solution**: Validate syntax with a linter or online validator

### "PyYAML not installed"

**Problem**: Trying to load YAML without PyYAML

**Solution**: Install PyYAML: `pip install pyyaml` or use JSON instead

### Environment Variables Not Working

**Problem**: Variables not being picked up

**Solution**: 

- Check variable names are correct (uppercase, `GHOSTKG_` prefix)
- Check variables are exported: `export GHOSTKG_LLM_MODEL=llama2`
- Verify with: `echo $GHOSTKG_LLM_MODEL`

## Migration from Hardcoded Values

If you have existing code with hardcoded values:

**Before**:
```python
from ghost_kg import CognitiveLoop

loop = CognitiveLoop(name="agent1", db_path="/data/agents.db")
```

**After (Backward Compatible)**:
```python
from ghost_kg import CognitiveLoop, GhostKGConfig, DatabaseConfig

config = GhostKGConfig(
    database=DatabaseConfig(path="/data/agents.db")
)
loop = CognitiveLoop(name="agent1", config=config)
# OR continue using old API (config will use defaults)
loop = CognitiveLoop(name="agent1", db_path="/data/agents.db")
```

## See Also

- [Architecture Documentation](ARCHITECTURE.md) - System design
- [Core Components](CORE_COMPONENTS.md) - Component details
- [API Reference](API.md) - API documentation
