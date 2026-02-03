# Using UV Package Manager with GhostKG

This project uses [uv](https://github.com/astral-sh/uv) for fast, modern Python package management.

## Installation

### Installing UV

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Installing GhostKG

#### Base Installation (Core Features)

```bash
# Clone the repository
git clone https://github.com/GiulioRossetti/GhostKG.git
cd GhostKG

# Install base dependencies with uv
uv pip install -e .
```

#### With Optional Features

```bash
# Install with LLM support (Ollama)
uv pip install -e ".[llm]"

# Install with fast mode (GLiNER + VADER)
uv pip install -e ".[fast]"

# Install with all optional features
uv pip install -e ".[all]"

# Install for development
uv pip install -e ".[dev]"

# Install for documentation
uv pip install -e ".[docs]"
```

## Development Workflow with UV

### Creating a Virtual Environment

```bash
# Create a new virtual environment
uv venv

# Activate it
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows
```

### Installing Dependencies

```bash
# Install all dependencies (including dev)
uv pip install -e ".[dev,all]"

# Just sync from lock file
uv sync
```

### Adding New Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Add an optional dependency (add to pyproject.toml manually, then:)
uv lock
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package package-name
```

## Dependency Groups

GhostKG uses the following dependency groups:

### Core Dependencies (Always Installed)

- `networkx` - Graph operations
- `fsrs` - Spaced repetition algorithm

### Optional Dependencies

#### `llm` - LLM Support

- `ollama` - For semantic triplet extraction with LLMs

Install with: `uv pip install -e ".[llm]"`

#### `fast` - Fast Mode

- `gliner` - Entity extraction without LLM
- `textblob` - Sentiment analysis

Install with: `uv pip install -e ".[fast]"`

#### `dev` - Development Tools

- `pytest`, `pytest-cov` - Testing
- `mypy` - Type checking
- `black` - Code formatting
- `flake8`, `pylint` - Linting
- `radon` - Code metrics
- `pre-commit` - Git hooks

Install with: `uv pip install -e ".[dev]"`

#### `docs` - Documentation

- `mkdocs` - Documentation generator
- `mkdocs-material` - Material theme
- `mkdocstrings` - API docs from docstrings

Install with: `uv pip install -e ".[docs]"`

#### `all` - All Optional Features

Installs both `llm` and `fast` dependencies.

Install with: `uv pip install -e ".[all]"`

## Checking Installed Features

```python
from ghost_kg import DependencyChecker

# Print status of all optional features
DependencyChecker.print_status()

# Check specific features
llm_available, missing = DependencyChecker.check_llm_available()
fast_available, missing = DependencyChecker.check_fast_available()
```

## Why UV?

UV provides several advantages over traditional pip:

1. **Speed** - 10-100x faster than pip
2. **Lock Files** - `uv.lock` ensures reproducible installations
3. **Better Resolution** - More accurate dependency resolution
4. **Modern** - Built in Rust, actively maintained
5. **Compatible** - Works with existing pip packages and pyproject.toml

## Migration from pip

If you're migrating from pip:

```bash
# Old way
pip install -r requirements.txt

# New way with uv
uv pip install -e .

# Or sync from lock file
uv sync
```

## Troubleshooting

### UV not found

```bash
# Install uv
pip install uv

# Or use the installer script
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Dependencies not resolving

```bash
# Clear cache and try again
uv cache clean
uv lock --no-cache
uv pip install -e ".[all]"
```

### Lock file conflicts

```bash
# Regenerate lock file
rm uv.lock
uv lock
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv pip install -e ".[dev]"

- name: Run tests
  run: uv run pytest
```

### Docker

```dockerfile
FROM python:3.11
RUN pip install uv
COPY . /app
WORKDIR /app
RUN uv pip install -e ".[all]"
```

## Resources

- [UV Documentation](https://github.com/astral-sh/uv)
- [UV Installation Guide](https://github.com/astral-sh/uv#installation)
- [Python Packaging Guide](https://packaging.python.org/)
