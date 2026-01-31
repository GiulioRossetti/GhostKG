# Code Quality Configuration

This directory contains configuration files for code quality tools used in the GhostKG project.

## Configuration Files

### `.flake8`
Flake8 linting configuration.
- **Max line length**: 100 characters
- **Ignored rules**: E203 (Black compatibility), W503 (modern style)
- **Exclusions**: git, cache, build directories

### `.pylintrc`
Pylint configuration for advanced static analysis.
- **Max line length**: 100 characters
- **Design limits**: max-args=7, max-locals=15
- **Exclusions**: tests, examples, site directories

### `.pre-commit-config.yaml`
Pre-commit hooks configuration for automated quality checks.
- **Hooks**: black, isort, flake8, mypy
- **Usage**: Run `pre-commit install` to enable

### `pyproject.toml`
Contains configuration for:
- **Black**: Code formatter (line-length: 100)
- **isort**: Import sorter (profile: black)
- **mypy**: Type checker

## Usage

### Running Quality Checks

```bash
# Format code
black ghost_kg/ tests/
isort ghost_kg/ tests/

# Check without modifying
black --check ghost_kg/
isort --check-only ghost_kg/

# Lint
flake8 ghost_kg/
pylint ghost_kg/

# Type check
mypy ghost_kg/
```

### Installing Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install

# Now quality checks run automatically on commit
```

### Running Pre-commit Manually

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

## Standards

All tools use consistent settings:
- **Line length**: 100 characters
- **Import sorting**: Black-compatible
- **Type checking**: Enabled with mypy
- **Python versions**: 3.8-3.12

## Continuous Integration

Quality checks run automatically in GitHub Actions:
1. Black (formatting)
2. isort (imports)
3. Flake8 (linting)
4. mypy (types)

All checks must pass before merge.

## Tool Versions

See `pyproject.toml` for exact version constraints:
- black: >=23.0,<27.0
- isort: >=5.12,<6.0
- flake8: >=6.0,<7.0
- mypy: >=1.0,<2.0
- pylint: >=2.17,<4.0
- pre-commit: >=3.0,<4.0

## Updating Configurations

When updating configurations:
1. Test changes locally first
2. Run `pre-commit run --all-files` to verify
3. Update this README if standards change
4. Document breaking changes in PR

## Troubleshooting

### "Command not found" errors
```bash
pip install -e ".[dev]"
```

### Pre-commit hook failures
```bash
# Skip hooks temporarily (not recommended)
git commit --no-verify

# Update hooks
pre-commit autoupdate
```

### Conflicts between tools
Our configurations are designed to work together:
- Black formats code
- isort uses Black profile
- Flake8 ignores Black-incompatible rules
- All use same line length (100)

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Pylint Documentation](https://pylint.readthedocs.io/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
