# GhostKG Refactoring Plan

**Version**: 1.0  
**Date**: 2026-01-30  
**Status**: Proposed

## Executive Summary

This document outlines a comprehensive refactoring plan for the GhostKG package to improve maintainability, efficiency, code quality, and developer experience. The plan is based on a thorough analysis of the current codebase and identifies specific improvements across multiple dimensions.

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Refactoring Goals](#refactoring-goals)
3. [Detailed Refactoring Steps](#detailed-refactoring-steps)
4. [Implementation Phases](#implementation-phases)
5. [Success Metrics](#success-metrics)
6. [Risk Assessment](#risk-assessment)

---

## Current State Analysis

### Codebase Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| Total Python Files | 12 | 3 core modules, 4 examples, 3 tests, 2 setup |
| Lines of Code | ~2,200 | Excluding docs and config |
| Core Modules | 3 | core.py (502), manager.py (323), storage.py (158) |
| Test Files | 3 | Coverage incomplete |
| Documentation Files | 6 | Comprehensive but could be better linked |
| External Dependencies | 7+ | Some optional, some required |

### Identified Issues

#### 1. Code Organization & Structure

**Issue**: `core.py` has multiple responsibilities (502 lines)
- FSRS algorithm (Rating, FSRS class)
- GhostAgent class with KG management
- CognitiveLoop with LLM integration
- Fast mode and LLM mode extraction logic

**Impact**: 
- Hard to test individual components
- Difficult to maintain and extend
- Violates Single Responsibility Principle
- Harder onboarding for new contributors

**Priority**: HIGH

---

#### 2. Global State Management

**Issue**: Global `GLINER_MODEL` variable in core.py
```python
GLINER_MODEL = None  # Global cache to prevent reloading
```

**Impact**:
- Not thread-safe
- Difficult to test
- Hidden dependencies
- Memory management unclear

**Priority**: MEDIUM

---

#### 3. Dependency Management

**Issue**: Optional dependencies not clearly managed
```python
try:
    from gliner import GLiNER
    from textblob import TextBlob
except ImportError:
    GLiNER = None
    TextBlob = None
```

**Impact**:
- Users don't know what to install
- No clear dependency groups (dev, optional, required)
- No requirements.txt with versions
- setup.py missing optional dependencies

**Priority**: HIGH

---

#### 4. Error Handling

**Issue**: Limited error handling throughout codebase

Examples:
- Database operations without error handling
- LLM calls without timeout/retry logic
- JSON parsing without validation
- No graceful degradation

**Impact**:
- Crashes on unexpected input
- Poor user experience
- Hard to debug issues
- Production instability

**Priority**: HIGH

---

#### 5. Type Hints

**Issue**: Inconsistent type hint usage

Examples:
- Some functions have full type hints
- Others have partial or no hints
- No mypy or type checking in CI

**Impact**:
- IDE autocomplete inconsistent
- Harder to catch bugs
- Poor developer experience
- Documentation less clear

**Priority**: MEDIUM

---

#### 6. Testing Coverage

**Issue**: Limited test coverage

Current state:
- Only 3 test files
- No unit tests for FSRS algorithm
- No tests for error conditions
- No integration tests for database
- No performance tests

**Impact**:
- Regressions easy to introduce
- Refactoring risky
- Hard to verify correctness
- Confidence in changes low

**Priority**: HIGH

---

#### 7. Code Duplication

**Issue**: Similar patterns repeated across examples

Examples:
- LLM client initialization repeated
- Triplet extraction logic duplicated
- Error handling patterns repeated
- Logging setup duplicated

**Impact**:
- Maintenance burden
- Inconsistent behavior
- Bug fixes need multiple changes
- Code bloat

**Priority**: MEDIUM

---

#### 8. Configuration Management

**Issue**: Hardcoded values throughout codebase

Examples:
- LLM host: `"http://localhost:11434"`
- Database path: `"agent_memory.db"`
- Model names: `"llama3.2"`
- Timeout values hardcoded
- FSRS parameters hardcoded

**Impact**:
- Not configurable
- Hard to test
- Environment-specific issues
- Poor user experience

**Priority**: MEDIUM

---

#### 9. Performance Considerations

**Issue**: Potential performance bottlenecks

Examples:
- Global GLINER model loaded once (good) but not configurable
- No query optimization in database layer
- No connection pooling
- No caching of frequently accessed data
- Linear scans in some queries

**Impact**:
- Slower than necessary
- Poor scaling
- Resource usage higher than needed

**Priority**: LOW (functional, but could be better)

---

#### 10. Documentation-Code Sync

**Issue**: Documentation and code can drift

Examples:
- API signatures change but docs lag
- Examples might not match current API
- No automated doc generation
- No doc tests

**Impact**:
- User confusion
- Wasted support time
- Bad first impression
- Lower adoption

**Priority**: MEDIUM

---

## Refactoring Goals

### Primary Goals

1. **Improve Maintainability**
   - Clear separation of concerns
   - Single Responsibility Principle
   - DRY (Don't Repeat Yourself)
   - Consistent coding patterns

2. **Enhance Testability**
   - Unit testable components
   - Dependency injection
   - Mock-friendly interfaces
   - Clear test boundaries

3. **Increase Performance**
   - Optimize database queries
   - Reduce redundant computations
   - Better resource management
   - Caching where appropriate

4. **Better Developer Experience**
   - Clear API boundaries
   - Comprehensive type hints
   - Better error messages
   - Consistent patterns

5. **Production Readiness**
   - Robust error handling
   - Graceful degradation
   - Configuration management
   - Logging and monitoring

---

## Detailed Refactoring Steps

### Phase 1: Code Organization (2-3 days) ✅ COMPLETE

**Status**: ✅ **COMPLETED** - All objectives achieved

**Implementation Date**: January 30, 2026

**Summary**: Successfully split core.py (502 lines) into 4 focused modules following Single Responsibility Principle. Maintained 100% backward compatibility.

#### 1.1: Split core.py into Multiple Modules ✅

**Before**:
```
ghost_kg/
  ├── core.py (502 lines)
  ├── manager.py
  └── storage.py
```

**After**:
```
ghost_kg/
  ├── fsrs.py          # FSRS algorithm (Rating, FSRS)
  ├── agent.py         # GhostAgent class
  ├── cognitive.py     # CognitiveLoop class
  ├── extraction.py    # Triplet extraction (fast & LLM modes)
  ├── manager.py       # Unchanged
  ├── storage.py       # Unchanged
  └── __init__.py      # Updated exports
```

**Steps**:
1. Create `ghost_kg/fsrs.py`
   - Move Rating class
   - Move FSRS class
   - Add comprehensive docstrings
   - Add unit tests

2. Create `ghost_kg/agent.py`
   - Move GhostAgent class
   - Import from fsrs module
   - Add type hints
   - Add unit tests

3. Create `ghost_kg/cognitive.py`
   - Move CognitiveLoop class
   - Import from agent module
   - Add type hints
   - Add unit tests

4. Create `ghost_kg/extraction.py`
   - Move triplet extraction logic
   - Create TripletExtractor interface
   - Implement FastExtractor (GLiNER + TextBlob)
   - Implement LLMExtractor (Ollama)
   - Add configuration class
   - Add unit tests

5. Update `ghost_kg/__init__.py`
   - Export all public classes
   - Maintain backward compatibility
   - Add deprecation warnings if needed

**Benefits**:
- Easier to navigate
- Easier to test
- Easier to maintain
- Clear responsibilities

**Backward Compatibility**:
```python
# Old import still works
from ghost_kg.core import GhostAgent, FSRS, Rating

# New imports also work
from ghost_kg.agent import GhostAgent
from ghost_kg.fsrs import FSRS, Rating
```

**Testing**:
- All existing tests must pass
- Add new unit tests for each module
- Integration tests verify interaction

---

#### 1.2: Introduce Dependency Injection ✅

**Status**: ✅ **COMPLETED** - Implemented in extraction.py

**Implementation**: Created abstraction layer with TripletExtractor interface and factory function.

**Before**:
```python
class GhostAgent:
    def __init__(self, name, db_path="agent_memory.db", llm_host="..."):
        self.db = KnowledgeDB(db_path)  # Hard-coded
        self.fsrs = FSRS()              # Hard-coded
        self.client = Client(host=llm_host)  # Hard-coded
```

**After**:
```python
# Extraction strategies can be injected
extractor = get_extractor(fast_mode=True)  # or custom extractor
cognitive_loop = CognitiveLoop(agent, extractor=extractor)
```

**Benefits**:
- ✅ Easy to inject different extraction strategies
- ✅ Easy to customize behavior
- ✅ Follows Dependency Inversion Principle
- ✅ Better testability

---

#### 1.3: Remove Global State ✅

**Status**: ✅ **COMPLETED** - Replaced with thread-safe ModelCache

**Issue**: `GLINER_MODEL` global variable

**Before**:
```python
GLINER_MODEL = None  # Global cache

class CognitiveLoop:
    def _absorb_fast(self, text, author):
        global GLINER_MODEL
        if GLINER_MODEL is None:
            GLINER_MODEL = GLiNER.from_pretrained(...)
```

**After**:
```python
class ModelCache:
    """Thread-safe model cache."""
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._models = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get_gliner(self, model_name: str = "urchade/gliner_small-v2.1"):
        if model_name not in self._models:
            self._models[model_name] = GLiNER.from_pretrained(model_name)
        return self._models[model_name]

class FastExtractor:
    def __init__(self, model_cache: Optional[ModelCache] = None):
        self.cache = model_cache or ModelCache.get_instance()
```

**Benefits**:
- ✅ Thread-safe singleton pattern with lock
- ✅ Testable - can be injected
- ✅ Memory management clear
- ✅ Prevents duplicate model loads

**Implementation**: Created `ModelCache` class in `extraction.py` with:
- Thread lock for safe concurrent access
- Lazy loading of GLiNER model
- Clean abstraction for model management

---

### Phase 2: Dependency Management (1 day) 📋 PENDING

#### 2.1: Restructure Dependencies

**Create `requirements/base.txt`**:
```
networkx>=3.0,<4.0
fsrs>=1.0.0,<2.0
```

**Create `requirements/llm.txt`**:
```
ollama>=0.1.6,<1.0
```

**Create `requirements/fast.txt`**:
```
gliner>=0.1.0
textblob>=0.15.0
```

**Create `requirements/dev.txt`**:
```
pytest>=7.0
pytest-cov>=4.0
pytest-asyncio>=0.21
mypy>=1.0
black>=23.0
flake8>=6.0
pylint>=2.17
radon>=5.1
```

**Create `requirements/docs.txt`**:
```
mkdocs>=1.4
mkdocs-material>=9.0
mkdocstrings[python]>=0.20
```

**Update `setup.py`**:
```python
setup(
    name="ghost_kg",
    version="0.2.0",
    install_requires=[
        "networkx>=3.0,<4.0",
        "fsrs>=1.0.0,<2.0",
    ],
    extras_require={
        "llm": ["ollama>=0.1.6,<1.0"],
        "fast": ["gliner>=0.1.0", "textblob>=0.15.0"],
        "dev": [...],
        "docs": [...],
        "all": [...]  # All optional dependencies
    }
)
```

**Installation**:
```bash
# Base installation
pip install ghost_kg

# With LLM support
pip install ghost_kg[llm]

# With fast mode
pip install ghost_kg[fast]

# Everything
pip install ghost_kg[all]

# Development
pip install ghost_kg[dev]
```

---

#### 2.2: Add Dependency Checks

**Create `ghost_kg/dependencies.py`**:
```python
"""Dependency checking utilities."""
from typing import List, Tuple
import importlib

class DependencyChecker:
    """Check for optional dependencies."""
    
    @staticmethod
    def check_llm_available() -> Tuple[bool, List[str]]:
        """Check if LLM dependencies are available."""
        missing = []
        try:
            import ollama
        except ImportError:
            missing.append("ollama")
        return len(missing) == 0, missing
    
    @staticmethod
    def check_fast_available() -> Tuple[bool, List[str]]:
        """Check if fast mode dependencies are available."""
        missing = []
        try:
            import gliner
        except ImportError:
            missing.append("gliner")
        try:
            import textblob
        except ImportError:
            missing.append("textblob")
        return len(missing) == 0, missing
    
    @staticmethod
    def require_llm():
        """Raise error if LLM dependencies missing."""
        available, missing = DependencyChecker.check_llm_available()
        if not available:
            raise ImportError(
                f"LLM dependencies missing: {', '.join(missing)}\n"
                "Install with: pip install ghost_kg[llm]"
            )
```

**Usage**:
```python
from ghost_kg.dependencies import DependencyChecker

if DependencyChecker.check_fast_available()[0]:
    # Use fast mode
else:
    # Fall back to basic mode
```

---

### Phase 3: Error Handling (2 days)

#### 3.1: Define Custom Exceptions

**Create `ghost_kg/exceptions.py`**:
```python
"""Custom exceptions for GhostKG."""

class GhostKGError(Exception):
    """Base exception for GhostKG."""
    pass

class DatabaseError(GhostKGError):
    """Database operation failed."""
    pass

class LLMError(GhostKGError):
    """LLM operation failed."""
    pass

class ExtractionError(GhostKGError):
    """Triplet extraction failed."""
    pass

class ConfigurationError(GhostKGError):
    """Configuration invalid."""
    pass

class AgentNotFoundError(GhostKGError):
    """Agent does not exist."""
    pass

class ValidationError(GhostKGError):
    """Input validation failed."""
    pass
```

---

#### 3.2: Add Error Handling to Critical Paths

**Database Operations**:
```python
def upsert_node(self, owner_id, node_id, fsrs_state=None, timestamp=None):
    """Upsert a node with error handling."""
    try:
        # ... existing logic ...
        self.conn.commit()
    except sqlite3.Error as e:
        self.conn.rollback()
        raise DatabaseError(f"Failed to upsert node {node_id}: {e}") from e
```

**LLM Operations**:
```python
def _call_llm(self, prompt: str, timeout: int = 30) -> str:
    """Call LLM with timeout and retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout
            )
            return response["message"]["content"]
        except Exception as e:
            if attempt == max_retries - 1:
                raise LLMError(f"LLM call failed after {max_retries} attempts: {e}") from e
            time.sleep(2 ** attempt)  # Exponential backoff
```

**JSON Parsing**:
```python
def _parse_json_response(self, text: str) -> dict:
    """Parse JSON from LLM response with validation."""
    try:
        # Try to extract JSON from markdown code blocks
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
        
        data = json.loads(text)
        return data
    except json.JSONDecodeError as e:
        raise ExtractionError(f"Invalid JSON response: {e}\nText: {text[:100]}") from e
```

---

### Phase 4: Configuration Management (1-2 days)

#### 4.1: Create Configuration System

**Create `ghost_kg/config.py`**:
```python
"""Configuration management for GhostKG."""
from dataclasses import dataclass, field
from typing import Optional
import os

@dataclass
class FSRSConfig:
    """FSRS algorithm configuration."""
    parameters: list = field(default_factory=lambda: [
        0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01,
        1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61,
    ])

@dataclass
class DatabaseConfig:
    """Database configuration."""
    path: str = "agent_memory.db"
    check_same_thread: bool = False
    timeout: float = 5.0

@dataclass
class LLMConfig:
    """LLM configuration."""
    host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    model: str = "llama3.2"
    timeout: int = 30
    max_retries: int = 3

@dataclass
class FastModeConfig:
    """Fast mode extraction configuration."""
    gliner_model: str = "urchade/gliner_small-v2.1"
    entity_labels: list = field(default_factory=lambda: [
        "Topic", "Person", "Concept", "Organization"
    ])
    sentiment_thresholds: dict = field(default_factory=lambda: {
        "support": 0.3,
        "oppose": -0.3,
        "like": 0.1,
        "dislike": -0.1,
    })

@dataclass
class GhostKGConfig:
    """Main GhostKG configuration."""
    fsrs: FSRSConfig = field(default_factory=FSRSConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    fast_mode: FastModeConfig = field(default_factory=FastModeConfig)
    
    @classmethod
    def from_file(cls, path: str) -> 'GhostKGConfig':
        """Load configuration from file (YAML/JSON)."""
        # Implementation
        pass
    
    @classmethod
    def from_env(cls) -> 'GhostKGConfig':
        """Load configuration from environment variables."""
        # Implementation
        pass
```

**Usage**:
```python
# Default configuration
config = GhostKGConfig()

# Custom configuration
config = GhostKGConfig(
    llm=LLMConfig(host="http://my-server:11434", model="llama2"),
    database=DatabaseConfig(path="/data/agents.db")
)

# From file
config = GhostKGConfig.from_file("config.yaml")

# From environment
config = GhostKGConfig.from_env()
```

---

### Phase 5: Testing Infrastructure (3-4 days)

#### 5.1: Add Comprehensive Unit Tests

**Test Structure**:
```
tests/
  ├── unit/
  │   ├── test_fsrs.py          # FSRS algorithm tests
  │   ├── test_agent.py          # GhostAgent tests
  │   ├── test_cognitive.py      # CognitiveLoop tests
  │   ├── test_extraction.py     # Extraction tests
  │   ├── test_storage.py        # Database tests
  │   └── test_manager.py        # Manager tests
  ├── integration/
  │   ├── test_workflows.py      # End-to-end workflows
  │   └── test_multi_agent.py    # Multi-agent scenarios
  ├── performance/
  │   ├── test_benchmarks.py     # Performance benchmarks
  │   └── test_memory.py         # Memory usage tests
  ├── fixtures/
  │   ├── conftest.py            # Pytest fixtures
  │   └── mock_data.py           # Test data
  └── conftest.py
```

**Example Test: `test_fsrs.py`**:
```python
"""Unit tests for FSRS algorithm."""
import pytest
from datetime import datetime, timezone, timedelta
from ghost_kg.fsrs import FSRS, Rating
from ghost_kg.storage import NodeState

class TestFSRS:
    """Test FSRS algorithm."""
    
    def test_new_card_again(self):
        """Test new card with 'Again' rating."""
        fsrs = FSRS()
        now = datetime.now(timezone.utc)
        
        initial = NodeState(0, 0, None, 0, 0)
        result = fsrs.calculate_next(initial, Rating.Again, now)
        
        assert result.stability == pytest.approx(0.4, rel=0.01)
        assert result.state == 1
        assert result.reps == 1
    
    def test_new_card_good(self):
        """Test new card with 'Good' rating."""
        fsrs = FSRS()
        now = datetime.now(timezone.utc)
        
        initial = NodeState(0, 0, None, 0, 0)
        result = fsrs.calculate_next(initial, Rating.Good, now)
        
        assert result.stability == pytest.approx(2.4, rel=0.01)
        assert result.state == 1
        assert result.reps == 1
    
    def test_stability_increases_on_success(self):
        """Test that stability increases on successful recall."""
        fsrs = FSRS()
        now = datetime.now(timezone.utc)
        
        # Start with a card in review state
        initial = NodeState(
            stability=5.0,
            difficulty=5.0,
            last_review=now - timedelta(days=2),
            reps=1,
            state=2
        )
        
        result = fsrs.calculate_next(initial, Rating.Good, now)
        
        assert result.stability > initial.stability
        assert result.reps == 2
    
    def test_stability_decreases_on_failure(self):
        """Test that stability decreases on failed recall."""
        fsrs = FSRS()
        now = datetime.now(timezone.utc)
        
        initial = NodeState(
            stability=10.0,
            difficulty=5.0,
            last_review=now - timedelta(days=5),
            reps=2,
            state=2
        )
        
        result = fsrs.calculate_next(initial, Rating.Again, now)
        
        assert result.stability < initial.stability
        assert result.state == 1  # Back to learning
```

---

#### 5.2: Add Integration Tests

**Example: `test_workflows.py`**:
```python
"""Integration tests for complete workflows."""
import pytest
from ghost_kg import AgentManager

class TestWorkflows:
    """Test complete workflows."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Create agent manager with temp database."""
        db_path = tmp_path / "test.db"
        return AgentManager(str(db_path))
    
    def test_simple_conversation(self, manager):
        """Test simple two-agent conversation."""
        # Create agents
        alice = manager.create_agent("Alice")
        bob = manager.create_agent("Bob")
        
        # Alice learns about climate
        manager.absorb_content(
            "Alice",
            "Climate change is urgent",
            author="Bob",
            triplets=[("climate change", "is", "urgent")]
        )
        
        # Get context for Alice
        context = manager.get_context("Alice", "climate")
        
        # Verify context contains learned info
        assert "climate change" in context.lower()
        assert "urgent" in context.lower()
    
    def test_memory_decay(self, manager):
        """Test that memory decays over time."""
        # Implementation
        pass
```

---

#### 5.3: Add Test Coverage Requirements

**Add `.coveragerc`**:
```ini
[run]
source = ghost_kg
omit =
    */tests/*
    */examples/*
    */__pycache__/*

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
```

**Add to CI/CD**:
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -e .[dev]
      - run: pytest --cov=ghost_kg --cov-report=xml --cov-report=html
      - run: coverage report --fail-under=80
```

**Target Coverage**: 80% minimum

---

### Phase 6: Type Hints & Validation (1-2 days)

#### 6.1: Add Complete Type Hints

**Example: Before**:
```python
def learn_triplet(self, source, relation, target, rating=Rating.Good, sentiment=0.0):
    """Learn a triplet."""
    # ...
```

**After**:
```python
def learn_triplet(
    self,
    source: str,
    relation: str,
    target: str,
    rating: int = Rating.Good,
    sentiment: float = 0.0
) -> None:
    """
    Learn a triplet (knowledge piece).
    
    Args:
        source: Subject entity
        relation: Relationship verb
        target: Object entity
        rating: Memory strength (1-4)
        sentiment: Emotional valence (-1.0 to 1.0)
    
    Raises:
        ValidationError: If inputs are invalid
    """
    # ...
```

---

#### 6.2: Add mypy Configuration

**Create `mypy.ini`**:
```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = False
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-ollama.*]
ignore_missing_imports = True

[mypy-gliner.*]
ignore_missing_imports = True

[mypy-textblob.*]
ignore_missing_imports = True
```

**Add to CI**:
```bash
mypy ghost_kg/
```

---

### Phase 7: Performance Optimization (2-3 days)

#### 7.1: Database Query Optimization

**Add Indexes**:
```python
def _init_schema(self):
    # ... existing schema ...
    
    # Add performance indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edges_owner_source 
        ON edges(owner_id, source)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edges_owner_target 
        ON edges(owner_id, target)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_edges_created 
        ON edges(owner_id, created_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_nodes_last_review 
        ON nodes(owner_id, last_review DESC)
    """)
```

---

#### 7.2: Add Caching Layer

**Create `ghost_kg/cache.py`**:
```python
"""Caching layer for frequently accessed data."""
from functools import lru_cache
from typing import Optional

class AgentCache:
    """Cache for agent data."""
    
    def __init__(self, max_size: int = 128):
        self.max_size = max_size
        self._context_cache = {}
    
    @lru_cache(maxsize=128)
    def get_memory_view(self, agent_name: str, topic: str, cache_key: str):
        """Cached memory view retrieval."""
        # Implementation
        pass
    
    def invalidate_agent(self, agent_name: str):
        """Invalidate cache for an agent."""
        # Implementation
        pass
```

---

#### 7.3: Connection Pooling

**Enhance Database Class**:
```python
class KnowledgeDB:
    """Knowledge database with connection pooling."""
    
    _pools = {}  # Database path -> connection pool
    
    def __init__(self, db_path: str = "agent_memory.db", pool_size: int = 5):
        if db_path not in self._pools:
            self._pools[db_path] = self._create_pool(db_path, pool_size)
        self.pool = self._pools[db_path]
    
    @staticmethod
    def _create_pool(db_path: str, size: int):
        """Create connection pool."""
        # Implementation using queue
        pass
```

---

### Phase 8: Documentation Improvements (1-2 days)

#### 8.1: Add Docstring Standards

**Use Google Style**:
```python
def process_and_get_context(
    self,
    agent_name: str,
    topic: str,
    text: str,
    author: str,
    triplets: Optional[List[Tuple[str, str, str]]] = None,
    fast_mode: bool = False
) -> str:
    """
    Process content and get context in one atomic operation.
    
    This is a convenience method that combines absorb_content()
    and get_context() into a single call, ensuring atomicity.
    
    Args:
        agent_name: Name of the agent processing the content
        topic: Topic keyword to focus context on
        text: Content text to process
        author: Author of the content
        triplets: Optional pre-extracted triplets. If None, will extract
                 internally using fast_mode or LLM.
        fast_mode: If True and triplets is None, use fast extraction
                  (GLiNER + TextBlob). If False, use LLM extraction.
    
    Returns:
        Formatted context string containing agent's current stance
        and relevant knowledge about the topic.
    
    Raises:
        AgentNotFoundError: If agent doesn't exist
        ExtractionError: If triplet extraction fails
        DatabaseError: If database operation fails
    
    Example:
        >>> manager = AgentManager()
        >>> context = manager.process_and_get_context(
        ...     "Alice",
        ...     topic="climate",
        ...     text="Climate action is urgent",
        ...     author="Bob"
        ... )
        >>> print(context)
        MY CURRENT STANCE: ...
    
    See Also:
        - absorb_content(): For just processing content
        - get_context(): For just retrieving context
    """
    # Implementation
```

---

#### 8.2: Add API Reference Generation

**Use mkdocstrings**:
```yaml
# mkdocs.yml
site_name: GhostKG Documentation
theme:
  name: material

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true
            show_root_heading: true
            show_category_heading: true
            show_signature_annotations: true
            
nav:
  - Home: index.md
  - Architecture: ARCHITECTURE.md
  - API Reference:
    - FSRS: api/fsrs.md
    - Agent: api/agent.md
    - Manager: api/manager.md
    - Storage: api/storage.md
  - Algorithms: ALGORITHMS.md
  - Refactoring: REFACTORING_PLAN.md
```

---

### Phase 9: Code Quality Tools (1 day)

#### 9.1: Add Linting Configuration

**Create `.flake8`**:
```ini
[flake8]
max-line-length = 100
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist
ignore =
    E203,  # whitespace before ':'
    W503,  # line break before binary operator
per-file-ignores =
    __init__.py:F401
```

**Create `.pylintrc`**:
```ini
[MASTER]
ignore=tests,examples

[MESSAGES CONTROL]
disable=
    C0111,  # missing-docstring (handled by flake8)
    R0903,  # too-few-public-methods

[FORMAT]
max-line-length=100

[DESIGN]
max-args=7
max-locals=15
```

---

#### 9.2: Add Code Formatting

**Create `pyproject.toml`**:
```toml
[tool.black]
line-length = 100
target-version = ['py38']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
```

---

#### 9.3: Add Pre-commit Hooks

**Create `.pre-commit-config.yaml`**:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## Implementation Phases

### Timeline Overview

| Phase | Duration | Priority | Dependencies |
|-------|----------|----------|--------------|
| Phase 1: Code Organization | 2-3 days | HIGH | None |
| Phase 2: Dependency Management | 1 day | HIGH | None |
| Phase 3: Error Handling | 2 days | HIGH | Phase 1 |
| Phase 4: Configuration | 1-2 days | MEDIUM | Phase 1 |
| Phase 5: Testing | 3-4 days | HIGH | Phase 1, 3 |
| Phase 6: Type Hints | 1-2 days | MEDIUM | Phase 1 |
| Phase 7: Performance | 2-3 days | LOW | Phase 1, 5 |
| Phase 8: Documentation | 1-2 days | MEDIUM | Phase 1, 6 |
| Phase 9: Code Quality | 1 day | MEDIUM | Phase 1 |

**Total Estimated Time**: 14-20 days

### Recommended Order

#### Sprint 1 (Week 1): Foundation
1. Phase 2: Dependency Management (1 day)
2. Phase 1: Code Organization (3 days)
3. Phase 6: Type Hints (1 day)

**Goal**: Clean, well-organized, properly typed codebase

#### Sprint 2 (Week 2): Robustness
1. Phase 3: Error Handling (2 days)
2. Phase 4: Configuration (2 days)
3. Phase 5: Testing (1 day - start)

**Goal**: Robust, configurable, error-resistant

#### Sprint 3 (Week 3): Polish
1. Phase 5: Testing (3 days - complete)
2. Phase 7: Performance (2 days)

**Goal**: Well-tested, performant

#### Sprint 4 (Week 4): Finalization
1. Phase 8: Documentation (2 days)
2. Phase 9: Code Quality (1 day)
3. Final review and release (2 days)

**Goal**: Production-ready release

---

## Success Metrics

### Code Quality Metrics

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| Test Coverage | ~30% | 80%+ | HIGH |
| Type Coverage | ~40% | 95%+ | MEDIUM |
| Linting Score | Unknown | 9.0/10 | MEDIUM |
| Complexity (avg) | Unknown | <10 | MEDIUM |
| Documentation | 70% | 95%+ | HIGH |
| Dependency Count | 7+ | <10 | LOW |

### Performance Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Query Response Time | <100ms | Benchmark tests |
| Memory Usage | <500MB | Memory profiler |
| Startup Time | <2s | Time import |
| Test Suite Runtime | <30s | pytest timing |

### Developer Experience Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Onboarding Time | <2 hours | Developer survey |
| PR Review Time | <1 day | GitHub metrics |
| Build Success Rate | >95% | CI statistics |
| Documentation Clarity | 4.5/5 | User feedback |

---

## Risk Assessment

### High Risk Items

#### 1. Breaking Changes

**Risk**: Refactoring might break existing user code

**Mitigation**:
- Maintain backward compatibility in Phase 1
- Add deprecation warnings, not immediate removal
- Semantic versioning (0.2.0 → 0.3.0)
- Migration guide in documentation
- Support old API for at least one major version

**Contingency**:
- If breaks detected, revert and redesign
- Feature flags for new vs old API
- Parallel API support

---

#### 2. Performance Regression

**Risk**: Refactoring might slow down performance

**Mitigation**:
- Benchmark before changes
- Benchmark after each phase
- Performance tests in CI
- Monitor memory usage
- Profile critical paths

**Contingency**:
- Identify bottleneck
- Optimize specific component
- Consider caching
- Rollback if needed

---

### Medium Risk Items

#### 3. Test Complexity

**Risk**: Writing comprehensive tests is time-consuming

**Mitigation**:
- Start with critical paths
- Add tests incrementally
- Use test generators for data
- Share fixtures
- Parallelize test writing

**Contingency**:
- Reduce coverage target to 70%
- Focus on integration tests
- Defer edge case tests

---

#### 4. Documentation Drift

**Risk**: Docs might not match code after refactoring

**Mitigation**:
- Update docs with code changes
- Automated doc generation
- Doc tests verify examples
- CI checks for doc coverage
- Review process includes docs

**Contingency**:
- Dedicated doc sprint
- External technical writer
- Community contributions

---

### Low Risk Items

#### 5. Tool Integration Issues

**Risk**: New tools might not integrate well

**Mitigation**:
- Test tools in isolation first
- Use widely-adopted tools
- Check compatibility
- Gradual rollout

**Contingency**:
- Remove problematic tool
- Find alternative
- Manual process if needed

---

## Rollback Plan

### If Major Issues Arise

1. **Identify Problem**
   - What broke?
   - What was the cause?
   - How critical is it?

2. **Assess Impact**
   - Users affected?
   - Workaround available?
   - Timeline to fix?

3. **Decision Tree**
   ```
   Can fix in < 4 hours?
     YES → Fix and deploy
     NO → Can we work around it?
       YES → Document workaround, schedule fix
       NO → Rollback to previous version
   ```

4. **Rollback Steps**
   - Tag last stable version
   - Revert commits
   - Test thoroughly
   - Deploy previous version
   - Communicate to users

5. **Post-Mortem**
   - What went wrong?
   - How to prevent?
   - Update process

---

## Communication Plan

### Internal Team

- **Daily Standups**: Progress, blockers, next steps
- **Weekly Review**: Metrics, demo, plan adjustment
- **Slack Channel**: #ghostkg-refactoring
- **Documentation**: Living doc updated daily

### External Users

- **GitHub Discussions**: Announce refactoring plan
- **Blog Post**: Why and what we're doing
- **Migration Guide**: How to upgrade
- **Changelog**: Detailed changes
- **Version Tags**: Clear versioning

---

## Post-Refactoring Maintenance

### Continuous Improvement

1. **Regular Code Reviews**
   - All PRs reviewed by 2+ people
   - Focus on maintainability
   - Enforce standards

2. **Technical Debt Tracking**
   - Label issues as tech-debt
   - Monthly review and prioritization
   - Allocate 20% time to debt

3. **Performance Monitoring**
   - Regular benchmarks
   - Memory profiling
   - User feedback

4. **Documentation Updates**
   - Update with every API change
   - Quarterly review of all docs
   - Community contributions welcome

5. **Dependency Updates**
   - Monthly dependency review
   - Automated security alerts
   - Keep dependencies current

---

## Conclusion

This refactoring plan provides a comprehensive roadmap to improve GhostKG's maintainability, efficiency, and developer experience. The phased approach allows for incremental progress while maintaining stability and minimizing risk.

### Key Takeaways

1. **Modular Architecture**: Split monolithic core.py into focused modules
2. **Robust Error Handling**: Comprehensive exception handling and recovery
3. **Extensive Testing**: Achieve 80%+ test coverage
4. **Type Safety**: Full type hints and mypy validation
5. **Configuration**: Flexible, environment-aware configuration
6. **Performance**: Optimized queries, caching, and resource management
7. **Developer Experience**: Clear APIs, good documentation, quality tools

### Next Steps

1. **Review this plan** with the team
2. **Prioritize phases** based on current needs
3. **Start with Sprint 1** (Foundation)
4. **Iterate and adjust** based on learnings
5. **Communicate progress** regularly

### Success Criteria

The refactoring will be considered successful when:
- ✅ Test coverage >= 80%
- ✅ Type coverage >= 95%
- ✅ All linting passes
- ✅ Documentation complete and accurate
- ✅ No breaking changes (or clear migration path)
- ✅ Performance maintained or improved
- ✅ Developer onboarding time < 2 hours
- ✅ User feedback positive

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-30  
**Next Review**: After Sprint 1 completion

**Related Documents**:
- [Architecture Documentation](ARCHITECTURE.md)
- [Core Components](CORE_COMPONENTS.md)
- [Algorithms & Formulas](ALGORITHMS.md)
- [Database Schema](DATABASE_SCHEMA.md)
- [API Reference](API.md)

**Maintainers**:
- Primary: Development Team
- Reviewers: Technical Leads
- Approvers: Project Maintainers
