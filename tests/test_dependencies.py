"""Tests for dependency checking utilities."""

import pytest
from ghost_kg import (
    DependencyChecker,
    has_llm_support,
    has_fast_support,
)


class TestDependencyChecker:
    """Test DependencyChecker class."""

    def test_check_llm_available(self):
        """Test LLM availability check."""
        available, missing = DependencyChecker.check_llm_available()
        assert isinstance(available, bool)
        assert isinstance(missing, list)
        # If not available, should have missing deps
        if not available:
            assert len(missing) > 0
            assert "ollama" in missing

    def test_check_fast_available(self):
        """Test fast mode availability check."""
        available, missing = DependencyChecker.check_fast_available()
        assert isinstance(available, bool)
        assert isinstance(missing, list)
        # If not available, should have missing deps
        if not available:
            assert len(missing) > 0
            # Should check for gliner and/or textblob
            assert any(dep in missing for dep in ["gliner", "textblob"])

    def test_get_available_extractors(self):
        """Test getting list of available extractors."""
        extractors = DependencyChecker.get_available_extractors()
        assert isinstance(extractors, list)
        # Should contain valid extractor names
        for ext in extractors:
            assert ext in ["fast", "llm"]

    def test_require_llm_missing(self):
        """Test require_llm raises ImportError when dependencies missing."""
        llm_available, _ = DependencyChecker.check_llm_available()
        if not llm_available:
            with pytest.raises(ImportError) as exc_info:
                DependencyChecker.require_llm()
            assert "LLM dependencies" in str(exc_info.value)
            assert "pip install ghost_kg[llm]" in str(exc_info.value)

    def test_require_fast_missing(self):
        """Test require_fast raises ImportError when dependencies missing."""
        fast_available, _ = DependencyChecker.check_fast_available()
        if not fast_available:
            with pytest.raises(ImportError) as exc_info:
                DependencyChecker.require_fast()
            assert "Fast mode dependencies" in str(exc_info.value)
            assert "pip install ghost_kg[fast]" in str(exc_info.value)

    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test has_llm_support
        llm_result = has_llm_support()
        assert isinstance(llm_result, bool)
        assert llm_result == DependencyChecker.check_llm_available()[0]

        # Test has_fast_support
        fast_result = has_fast_support()
        assert isinstance(fast_result, bool)
        assert fast_result == DependencyChecker.check_fast_available()[0]

    def test_print_status(self):
        """Test print_status doesn't crash."""
        # Should not raise any exceptions
        DependencyChecker.print_status()


class TestDependencyIntegration:
    """Integration tests for dependency checking."""

    def test_import_from_main_module(self):
        """Test that dependency checker can be imported from main module."""
        from ghost_kg import DependencyChecker as DC
        assert DC is not None

    def test_convenience_import(self):
        """Test convenience function imports."""
        from ghost_kg import has_llm_support, has_fast_support
        assert callable(has_llm_support)
        assert callable(has_fast_support)
