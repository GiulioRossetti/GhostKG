"""Dependency checking utilities for optional GhostKG features.

This module provides utilities to check for optional dependencies and provide
helpful error messages when they are missing.
"""

from typing import List, Tuple
import importlib.util


class DependencyChecker:
    """Check for optional dependencies and provide helpful error messages."""

    @staticmethod
    def check_llm_available() -> Tuple[bool, List[str]]:
        """Check if LLM dependencies are available.

        Returns:
            Tuple containing:
            - bool: True if all LLM dependencies are available
            - List[str]: Names of missing dependencies

        Example:
            >>> available, missing = DependencyChecker.check_llm_available()
            >>> if not available:
            ...     print(f"Missing: {missing}")
        """
        missing = []
        try:
            import ollama  # noqa: F401
        except ImportError:
            missing.append("ollama")
        return len(missing) == 0, missing

    @staticmethod
    def check_fast_available() -> Tuple[bool, List[str]]:
        """Check if fast mode dependencies are available.

        Fast mode uses GLiNER for entity extraction and TextBlob for sentiment
        analysis, allowing triplet extraction without requiring an LLM.

        Returns:
            Tuple containing:
            - bool: True if all fast mode dependencies are available
            - List[str]: Names of missing dependencies

        Example:
            >>> available, missing = DependencyChecker.check_fast_available()
            >>> if available:
            ...     # Use fast mode
            ...     pass
        """
        missing = []
        try:
            import gliner  # noqa: F401
        except ImportError:
            missing.append("gliner")
        try:
            import textblob  # noqa: F401
        except ImportError:
            missing.append("textblob")
        return len(missing) == 0, missing

    @staticmethod
    def require_llm() -> None:
        """Raise ImportError if LLM dependencies are missing.

        Raises:
            ImportError: If any LLM dependencies are missing, with instructions
                on how to install them.

        Example:
            >>> try:
            ...     DependencyChecker.require_llm()
            ...     # Use LLM features
            ... except ImportError as e:
            ...     print(e)
        """
        available, missing = DependencyChecker.check_llm_available()
        if not available:
            raise ImportError(
                f"LLM dependencies are required but missing: {', '.join(missing)}\n\n"
                "Install them with:\n"
                "  pip install ghost_kg[llm]\n\n"
                "Or install ollama separately:\n"
                "  pip install ollama"
            )

    @staticmethod
    def require_fast() -> None:
        """Raise ImportError if fast mode dependencies are missing.

        Raises:
            ImportError: If any fast mode dependencies are missing, with
                instructions on how to install them.

        Example:
            >>> try:
            ...     DependencyChecker.require_fast()
            ...     # Use fast mode
            ... except ImportError as e:
            ...     print(e)
        """
        available, missing = DependencyChecker.check_fast_available()
        if not available:
            raise ImportError(
                f"Fast mode dependencies are required but missing: {', '.join(missing)}\n\n"
                "Install them with:\n"
                "  pip install ghost_kg[fast]\n\n"
                "Or install packages separately:\n"
                "  pip install gliner textblob"
            )

    @staticmethod
    def get_available_extractors() -> List[str]:
        """Get list of available extraction modes based on installed dependencies.

        Returns:
            List[str]: Names of available extractors ('fast', 'llm', or both)

        Example:
            >>> extractors = DependencyChecker.get_available_extractors()
            >>> print(f"Available: {extractors}")
            Available: ['fast', 'llm']
        """
        extractors = []
        if DependencyChecker.check_fast_available()[0]:
            extractors.append("fast")
        if DependencyChecker.check_llm_available()[0]:
            extractors.append("llm")
        return extractors

    @staticmethod
    def print_status() -> None:
        """Print the status of all optional dependencies.

        This is useful for debugging and understanding what features are available.

        Example:
            >>> DependencyChecker.print_status()
            GhostKG Dependency Status:
            ✓ LLM mode: Available
            ✗ Fast mode: Missing dependencies: gliner, textblob
        """
        llm_available, llm_missing = DependencyChecker.check_llm_available()
        fast_available, fast_missing = DependencyChecker.check_fast_available()

        print("GhostKG Dependency Status:")
        print(f"  {'✓' if llm_available else '✗'} LLM mode: "
              f"{'Available' if llm_available else f'Missing: {', '.join(llm_missing)}'}")
        print(f"  {'✓' if fast_available else '✗'} Fast mode: "
              f"{'Available' if fast_available else f'Missing: {', '.join(fast_missing)}'}")

        if not llm_available and not fast_available:
            print("\n⚠ Warning: No extraction modes available!")
            print("  Install at least one mode:")
            print("    pip install ghost_kg[llm]   # For LLM-based extraction")
            print("    pip install ghost_kg[fast]  # For fast local extraction")
            print("    pip install ghost_kg[all]   # For both modes")


# Convenience functions for backward compatibility
def has_llm_support() -> bool:
    """Check if LLM support is available (convenience function)."""
    return DependencyChecker.check_llm_available()[0]


def has_fast_support() -> bool:
    """Check if fast mode support is available (convenience function)."""
    return DependencyChecker.check_fast_available()[0]
