"""
Allow running Ghost KG CLI as a module: python -m ghost_kg

This enables dev mode usage without package installation.
However, due to how Python's -m flag works, __init__.py gets loaded first.

RECOMMENDED DEV MODE USAGE:
    python ghostkg_dev.py --help
    python ghostkg_dev.py export --database mydb.db --serve

After installation, use:
    ghostkg --help
"""

# Note: This file exists for completeness, but the ghostkg_dev.py script
# is preferred for development as it avoids loading __init__.py dependencies.

if __name__ == '__main__':
    print("Note: Due to Python's import system, 'python -m ghost_kg' loads all dependencies.")
    print("For development without full installation, use:")
    print("    python ghostkg_dev.py --help")
    print()
    
    # Try to import and run, will fail if dependencies not installed
    try:
        from ghost_kg.cli import main
        main()
    except ImportError as e:
        print(f"Import error: {e}")
        print()
        print("Install dependencies with:")
        print("    pip install -e .")
        print("Or use the dev script:")
        print("    python ghostkg_dev.py --help")
        import sys
        sys.exit(1)
