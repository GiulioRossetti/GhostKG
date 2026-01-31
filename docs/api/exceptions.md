# Exceptions API

The exceptions module defines custom exception classes for error handling throughout GhostKG.

## Module Location

```python
# Recommended: Import from top-level package
from ghost_kg import GhostKGError, DatabaseError, LLMError, ValidationError

# Also supported: Import from subpackage
from ghost_kg.utils import GhostKGError, DatabaseError, LLMError, ValidationError
```

## Overview

GhostKG defines a hierarchy of exceptions for different error scenarios:

```
GhostKGError (base)
├── DatabaseError
├── LLMError
├── ExtractionError
├── ConfigurationError
├── AgentNotFoundError
├── ValidationError
└── DependencyError
```

## Exception Hierarchy

### GhostKGError

Base exception for all GhostKG errors.

```python
from ghost_kg.exceptions import GhostKGError

try:
    # GhostKG operation
    pass
except GhostKGError as e:
    print(f"GhostKG error: {e}")
```

### DatabaseError

Raised when database operations fail.

```python
from ghost_kg.exceptions import DatabaseError

try:
    db.upsert_node(owner_id="", node_id="test")
except DatabaseError as e:
    print(f"Database error: {e}")
```

### LLMError

Raised when LLM operations fail.

```python
from ghost_kg.exceptions import LLMError

try:
    loop.reply("topic")
except LLMError as e:
    print(f"LLM error: {e}")
```

### ExtractionError

Raised when triplet extraction fails.

```python
from ghost_kg.exceptions import ExtractionError

try:
    extractor.extract_triplets(text="...")
except ExtractionError as e:
    print(f"Extraction error: {e}")
```

### ConfigurationError

Raised for invalid configuration.

```python
from ghost_kg.exceptions import ConfigurationError

try:
    config = FSRSConfig(request_retention=1.5)  # Invalid value
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

### AgentNotFoundError

Raised when an agent doesn't exist.

```python
from ghost_kg.exceptions import AgentNotFoundError

try:
    agent = manager.get_agent("NonExistent")
    if not agent:
        raise AgentNotFoundError("Agent not found")
except AgentNotFoundError as e:
    print(f"Agent error: {e}")
```

### ValidationError

Raised for invalid input validation.

```python
from ghost_kg.exceptions import ValidationError

try:
    manager.create_agent("")  # Empty name
except ValidationError as e:
    print(f"Validation error: {e}")
```

### DependencyError

Raised when required dependencies are missing.

```python
from ghost_kg.exceptions import DependencyError

try:
    from ghost_kg.extraction import FastExtractor
    extractor = FastExtractor()
except DependencyError as e:
    print(f"Dependency error: {e}")
    print("Install with: pip install ghost_kg[fast]")
```

## Error Handling Best Practices

### Specific Exceptions

Catch specific exceptions rather than the base class:

```python
from ghost_kg.exceptions import DatabaseError, ValidationError

try:
    manager.create_agent("Alice")
    manager.learn_triplet("Alice", "I", "support", "UBI")
except ValidationError as e:
    print(f"Invalid input: {e}")
except DatabaseError as e:
    print(f"Database issue: {e}")
```

### Graceful Degradation

Handle errors gracefully:

```python
from ghost_kg.exceptions import LLMError

try:
    response = loop.reply("topic")
except LLMError as e:
    print(f"LLM unavailable: {e}")
    response = "I'm having trouble generating a response right now."
```

## API Reference

::: ghost_kg.utils.exceptions
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3
