# Development Guide

This guide explains how to work with GhostKG in development mode, contribute to the project, and understand the development workflow.

## Setting Up Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/GiulioRossetti/GhostKG.git
cd GhostKG
```

### 2. Install Dependencies

#### Option A: Using UV (Recommended)

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Or install all features
uv pip install -e ".[all]"
```

#### Option B: Using pip

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Or install all features
pip install -e ".[all]"
```

#### Option C: Minimal Installation (For CLI Development)

```bash
# Install only base requirements
pip install -r requirements/base.txt

# Add Flask for visualization
pip install flask
```

## Development Mode CLI

### The Problem

When developing, running `python -m ghost_kg` fails if dependencies aren't installed because Python loads `ghost_kg/__init__.py` first, which imports all modules.

### The Solution: ghostkg_dev.py

Use the `ghostkg_dev.py` script for development without full package installation:

```bash
# Show help
python ghostkg_dev.py --help

# Export history
python ghostkg_dev.py export --database agent_memory.db --output history.json

# Serve visualization
python ghostkg_dev.py serve --json history.json --browser

# Combined: export and serve
python ghostkg_dev.py export --database agent_memory.db --serve --browser
```

### After Full Installation

Once you've installed the package with `pip install -e .`, you can use the standard `ghostkg` command:

```bash
ghostkg --help
ghostkg export --database agent_memory.db --serve --browser
```

## Project Structure

```
GhostKG/
├── ghost_kg/                # Main package
│   ├── __init__.py         # Package initialization
│   ├── __main__.py         # Module entry point (python -m ghost_kg)
│   ├── cli.py              # Command-line interface
│   ├── visualization.py    # History export functionality
│   ├── core/               # Core components (Agent, Manager, etc.)
│   ├── memory/             # FSRS memory system
│   ├── storage/            # Database and ORM models
│   ├── extraction/         # Knowledge extraction (LLM/Fast mode)
│   ├── templates/          # Web visualization templates
│   └── utils/              # Utility modules
├── docs/                   # Documentation
│   ├── summaries/          # Implementation summaries
│   ├── examples/           # Example documentation
│   └── *.md                # Core documentation files
├── examples/               # Working code examples
├── tests/                  # Test suite
├── requirements/           # Dependency specifications
├── ghostkg_dev.py          # Development mode launcher
└── setup.py                # Package configuration
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agent.py

# Run with coverage
pytest --cov=ghost_kg --cov-report=html

# Run specific test
pytest tests/unit/test_agent.py::TestGhostAgent::test_basic_functionality
```

## Code Style and Linting

```bash
# Format code with black
black ghost_kg/

# Check code style
flake8 ghost_kg/

# Type checking (if configured)
mypy ghost_kg/

# Run pre-commit hooks
pre-commit run --all-files
```

## Working with Examples

### Running Examples

```bash
# Basic example
python examples/use_case_example.py

# External program pattern
python examples/external_program.py

# Time-based simulation
python examples/hourly_simulation.py
```

### Creating New Examples

1. Create a new `.py` file in `examples/`
2. Add documentation in `docs/examples/`
3. Update `docs/examples/index.md`
4. Test thoroughly
5. Submit a pull request

## Development Workflows

### Adding a New Feature

1. **Create a branch**: `git checkout -b feature/your-feature`
2. **Implement the feature**: Make minimal, focused changes
3. **Add tests**: Create tests in `tests/unit/` or `tests/integration/`
4. **Update documentation**: Add to relevant docs in `docs/`
5. **Test locally**: Run tests and examples
6. **Submit PR**: Create pull request with clear description

### Fixing a Bug

1. **Create a branch**: `git checkout -b fix/bug-description`
2. **Write a failing test**: Reproduce the bug in a test
3. **Fix the bug**: Make minimal changes
4. **Verify the fix**: Ensure test passes
5. **Submit PR**: Include test and fix

### Updating Documentation

1. **Main docs**: Edit files in `docs/`
2. **API docs**: Update docstrings in source code
3. **Examples**: Add or update in `docs/examples/`
4. **Summaries**: For major features, add to `docs/summaries/`

## CLI Development

The CLI is implemented in `ghost_kg/cli.py`. Key points:

- Uses `argparse` for command parsing
- Lazy imports to avoid loading heavy dependencies
- Two main commands: `serve` and `export`
- Entry point defined in `setup.py`

### Testing CLI Changes

```bash
# Test with dev script
python ghostkg_dev.py --help
python ghostkg_dev.py export --help

# Test after installation
pip install -e .
ghostkg --help
ghostkg export --help
```

## Database Development

### Working with Different Databases

```bash
# SQLite (default)
python examples/use_case_example.py

# PostgreSQL (requires setup)
export DB_URL="postgresql://user:pass@localhost/ghostkg"
python examples/use_case_example.py

# MySQL (requires setup)
export DB_URL="mysql+pymysql://user:pass@localhost/ghostkg"
python examples/use_case_example.py
```

### Schema Changes

When modifying database schema:

1. Update ORM models in `ghost_kg/storage/models.py`
2. Update documentation in `docs/DATABASE_SCHEMA.md`
3. Add migration logic if needed
4. Test with all database types
5. Update tests

## Visualization Development

The visualization system has three components:

1. **Backend**: `ghost_kg/visualization.py` (export logic)
2. **Server**: `ghost_kg/cli.py` (Flask server)
3. **Frontend**: `ghost_kg/templates/` (HTML, CSS, JS)

### Frontend Development

```bash
# Make changes to templates
cd ghost_kg/templates/
# Edit index.html, style.css, or app.js

# Test changes
python ghostkg_dev.py serve --json simulation_history.json --browser
```

### Backend Development

```bash
# Make changes to visualization.py
vim ghost_kg/visualization.py

# Test export
python ghostkg_dev.py export --database test.db --output test.json

# Verify JSON format
cat test.json | jq .
```

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError` when running scripts

**Solution**: Install dependencies
```bash
pip install -r requirements/base.txt
# or
pip install -e ".[dev]"
```

### CLI Not Working

**Problem**: `ghostkg` command not found

**Solution**: Install package or use dev script
```bash
# Install package
pip install -e .

# Or use dev script
python ghostkg_dev.py --help
```

### Database Errors

**Problem**: `sqlalchemy` errors or missing tables

**Solution**: Ensure SQLAlchemy is installed
```bash
pip install sqlalchemy>=2.0.0
```

### Visualization Not Loading

**Problem**: Server starts but browser shows errors

**Solution**: Check Flask is installed and JSON is valid
```bash
pip install flask
python -m json.tool history.json  # Validate JSON
```

## Getting Help

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions
- **Documentation**: Check `docs/` directory
- **Examples**: Review `examples/` directory

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

For detailed guidelines, check the repository's contribution guidelines.

## Release Process

For maintainers:

1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.x.0`
4. Push tag: `git push origin v0.x.0`
5. Build and publish to PyPI

## Additional Resources

- **Architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference**: [docs/API.md](API.md)
- **Database Schema**: [docs/DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- **Implementation Summaries**: [docs/summaries/](summaries/)
