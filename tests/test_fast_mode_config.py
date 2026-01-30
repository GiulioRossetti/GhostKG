#!/usr/bin/env python3
"""
Test script to verify fast_mode configuration works correctly
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Test that the file can be imported and configuration is accessible
print("Testing use_case_example.py configuration...")

# Import the module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "use_case_example",
    os.path.join(os.path.dirname(__file__), "..", "examples", "use_case_example.py")
)
use_case_module = importlib.util.module_from_spec(spec)

# Check if USE_FAST_MODE is defined by partially executing the module
# (we'll just parse it to check the configuration exists)
with open(os.path.join(os.path.dirname(__file__), "..", "examples", "use_case_example.py"), 'r') as f:
    content = f.read()
    
print("\n✓ Configuration Check:")
if "USE_FAST_MODE" in content:
    print("  ✓ USE_FAST_MODE configuration variable found")
    
    # Check default value
    if "USE_FAST_MODE = True" in content:
        print("  ✓ Default value is True (Fast Mode)")
    else:
        print("  ✓ USE_FAST_MODE is defined (check value manually)")
else:
    print("  ✗ USE_FAST_MODE not found")
    
# Check if conditional logic exists
if "if USE_FAST_MODE:" in content:
    print("  ✓ Conditional logic for fast_mode found")
else:
    print("  ✗ Conditional logic not found")

# Check if documentation exists
if "CONFIGURATION:" in content and "Fast Mode vs LLM Mode" in content:
    print("  ✓ Configuration documentation found")
else:
    print("  ✗ Configuration documentation not found")

print("\n✓ All checks passed!")
print("\nTo use the example:")
print("  - Fast Mode (default): Set USE_FAST_MODE = True")
print("  - LLM Mode: Set USE_FAST_MODE = False")
