# GhostKG Documentation

This directory contains the source files for GhostKG's documentation, built with [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

## Building the Documentation

### Prerequisites

Install documentation dependencies:

```bash
# Using pip
pip install "mkdocs>=1.5,<2.0" "mkdocs-material>=9.5,<10.0" "mkdocstrings[python]>=0.24,<1.0" "pymdown-extensions>=10.0,<11.0"

# Or install all dev dependencies
pip install -e ".[docs]"
```

### Build Commands

```bash
# Build the documentation
mkdocs build

# Serve locally with live reload (recommended for development)
mkdocs serve

# Deploy to GitHub Pages (maintainers only)
mkdocs gh-deploy
```

### Viewing Documentation

After running `mkdocs serve`, open your browser to:
- http://127.0.0.1:8000

The documentation will automatically reload when you make changes to the source files.

## Documentation Structure

```
docs/
├── index.md                    # Home page
├── ARCHITECTURE.md             # System architecture
├── CORE_COMPONENTS.md          # Component details
├── DATABASE_SCHEMA.md          # Database schema
├── ALGORITHMS.md               # FSRS and algorithms
├── CONFIGURATION.md            # Configuration guide
├── FAST_MODE_CONFIG.md         # Fast mode setup
├── API.md                      # External API guide
├── UV_SETUP.md                 # UV package manager setup
├── REFACTORING_PLAN.md         # Development roadmap
├── PHASE*_SUMMARY.md           # Phase summaries
└── api/                        # API reference (auto-generated)
    ├── manager.md              # AgentManager API
    ├── agent.md                # GhostAgent API
    ├── cognitive.md            # CognitiveLoop API
    ├── fsrs.md                 # FSRS API
    ├── storage.md              # Storage API
    ├── extraction.md           # Extraction API
    ├── config.md               # Configuration API
    ├── cache.md                # Cache API
    └── exceptions.md           # Exceptions API
```

## API Documentation

The API reference is automatically generated from Python docstrings using [mkdocstrings](https://mkdocstrings.github.io/). 

When updating code:
1. Write clear docstrings in Google style format
2. Include Args, Returns, Raises, Example, and See Also sections
3. Rebuild docs to see changes: `mkdocs serve`

### Docstring Format

```python
def method_name(arg1: str, arg2: int = 0) -> bool:
    """
    Short description of the method.
    
    Longer description providing more context about what the method does,
    how it works, and when to use it.
    
    Args:
        arg1 (str): Description of arg1
        arg2 (int): Description of arg2, defaults to 0
        
    Returns:
        bool: Description of return value
        
    Raises:
        ValueError: When validation fails
        
    Example:
        >>> result = method_name("test", 5)
        >>> print(result)
        True
        
    See Also:
        - related_method(): Does something related
        - another_method(): Alternative approach
    """
    pass
```

## Contributing

When adding new documentation:

1. Place markdown files in `docs/`
2. Update `mkdocs.yml` navigation if adding new pages
3. For API docs, just update docstrings - they're auto-generated
4. Test locally with `mkdocs serve`
5. Check for broken links and formatting issues

## Troubleshooting

### Missing Dependencies

If you see import errors when building:
```bash
pip install -e ".[docs]"
```

### Broken Links

The build will warn about broken links. Common causes:
- Links to files outside the docs directory (e.g., `../README.md`)
- Links to missing anchors
- Relative links that should be absolute

### Module Not Found

If mkdocstrings can't find modules:
```bash
# Install GhostKG in development mode
pip install -e .
```

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)
- [Google Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
