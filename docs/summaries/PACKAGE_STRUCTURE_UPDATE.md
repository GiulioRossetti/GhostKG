# Package Structure Documentation Update

## Problem Statement

Documentation contained outdated references to the old flat file structure (e.g., `ghost_kg/core.py`, `ghost_kg/storage.py`) before the package was restructured into subpackages.

## Solution

Updated all documentation to reflect the current subpackage organization.

---

## Changes Made

### Files Updated

1. **docs/CORE_COMPONENTS.md** - 6 location references updated
2. **docs/index.md** - 2 references updated (FAQ + component table)

### Specific Updates

| Component | Old Location | New Location |
|-----------|-------------|--------------|
| FSRS | `ghost_kg/core.py` | `ghost_kg/memory/fsrs.py` |
| NodeState | `ghost_kg/storage.py` | `ghost_kg/storage/database.py` |
| GhostAgent | `ghost_kg/core.py` | `ghost_kg/core/agent.py` |
| CognitiveLoop | `ghost_kg/core.py` | `ghost_kg/core/cognitive.py` |
| KnowledgeDB | `ghost_kg/storage.py` | `ghost_kg/storage/database.py` |
| AgentManager | `ghost_kg/manager.py` | `ghost_kg/core/manager.py` |

---

## Current Package Structure

```
ghost_kg/
├── __init__.py
├── __main__.py
├── cli.py                    # CLI commands
├── visualization.py          # Visualization export
├── core/                     # Core agent functionality
│   ├── __init__.py
│   ├── agent.py             # GhostAgent class
│   ├── cognitive.py         # CognitiveLoop class
│   └── manager.py           # AgentManager class
├── storage/                  # Database operations
│   ├── __init__.py
│   ├── database.py          # KnowledgeDB, NodeState
│   ├── engine.py            # Database engine
│   └── models.py            # ORM models
├── memory/                   # Memory systems
│   ├── __init__.py
│   ├── fsrs.py              # FSRS algorithm
│   └── cache.py             # Agent caching
├── extraction/               # Knowledge extraction
│   ├── __init__.py
│   └── extraction.py        # FastExtractor, LLMExtractor
├── utils/                    # Utilities
│   ├── __init__.py
│   ├── config.py            # Configuration classes
│   ├── exceptions.py        # Custom exceptions
│   ├── time_utils.py        # Time handling
│   └── dependencies.py      # Dependency checks
└── templates/                # Visualization templates
    ├── index.html
    ├── style.css
    └── app.js
```

---

## Old Structure (No Longer Exists)

The following files were previously at the top level but have been reorganized:

```
ghost_kg/
├── core.py          ❌ Split into:
│                       - core/agent.py
│                       - core/cognitive.py
│                       - memory/fsrs.py
├── storage.py       ❌ Moved to:
│                       - storage/database.py
└── manager.py       ❌ Moved to:
                        - core/manager.py
```

---

## Top-Level Files

Only two .py files remain at the top level of `ghost_kg/`:
- `cli.py` - Command-line interface
- `visualization.py` - History export and visualization

These are intentionally kept at the top level as they're utilities rather than core components.

---

## Verification

### Search Results
✅ No references to `ghost_kg/core.py` found in docs
✅ No references to `ghost_kg/storage.py` found in docs  
✅ No references to `ghost_kg/manager.py` found in docs
✅ No references to other old flat structure files found

### Documentation Accuracy
✅ All component locations now match actual file structure
✅ Component lookup table updated in index.md
✅ FAQ section updated with correct file paths
✅ CORE_COMPONENTS.md has accurate location information

---

## Impact

### For Developers
- Can now find components in the locations specified in docs
- No confusion about where code is located
- Documentation matches actual codebase organization

### For Users
- API imports remain unchanged (all exported through `__init__.py`)
- No user-facing breaking changes
- Documentation is now trustworthy

---

## Related Documentation

- [CORE_COMPONENTS.md](../CORE_COMPONENTS.md) - Component details
- [index.md](../index.md) - Main documentation index
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture

---

## Date

2026-02-02
