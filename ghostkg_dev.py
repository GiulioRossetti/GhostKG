#!/usr/bin/env python
"""
Development mode launcher for Ghost KG CLI.

Usage in dev mode (without package installation):
    python ghostkg_dev.py --help
    python ghostkg_dev.py export --database mydb.db --serve --browser
    python ghostkg_dev.py serve --json history.json --browser

After installation, use:
    ghostkg --help
"""

import sys
import importlib.util
from pathlib import Path

def main():
    """Load and run the CLI module without triggering heavy imports."""
    # Load cli module directly
    cli_path = Path(__file__).parent / 'ghost_kg' / 'cli.py'
    
    if not cli_path.exists():
        print(f"Error: CLI module not found at {cli_path}")
        sys.exit(1)
    
    # Load the module
    spec = importlib.util.spec_from_file_location("ghost_kg.cli", cli_path)
    cli_module = importlib.util.module_from_spec(spec)
    
    # Make it available as ghost_kg.cli for internal imports
    sys.modules['ghost_kg.cli'] = cli_module
    
    try:
        spec.loader.exec_module(cli_module)
    except ImportError as e:
        print(f"Error loading CLI: {e}")
        print("\nMake sure you have the required dependencies installed:")
        print("  pip install -r requirements/base.txt")
        print("  pip install flask  # for visualization server")
        sys.exit(1)
    
    # Run the CLI
    cli_module.main()

if __name__ == '__main__':
    main()
