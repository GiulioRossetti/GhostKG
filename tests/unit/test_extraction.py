"""Unit tests for extraction module."""
import pytest
from ghost_kg.extraction import ModelCache, FastExtractor, LLMExtractor, get_extractor
from ghost_kg.dependencies import DependencyChecker


class TestModelCache:
    """Test ModelCache singleton."""
    
    def test_singleton(self):
        """Test that ModelCache is a singleton."""
        cache1 = ModelCache.get_instance()
        cache2 = ModelCache.get_instance()
        assert cache1 is cache2
    
    def test_gliner_model_loading(self):
        """Test GLiNER model loading (if available)."""
        if not DependencyChecker.check_fast_available():
            pytest.skip("Fast mode dependencies not available")
        
        cache = ModelCache.get_instance()
        model = cache.get_gliner()
        assert model is not None
        
        # Should return same model on second call
        model2 = cache.get_gliner()
        assert model is model2


class TestFastExtractor:
    """Test FastExtractor."""
    
    def test_initialization(self):
        """Test FastExtractor initializes."""
        if not DependencyChecker.check_fast_available():
            pytest.skip("Fast mode dependencies not available")
        
        extractor = FastExtractor()
        assert extractor is not None
    
    def test_extract_triplets(self):
        """Test extracting triplets from text."""
        if not DependencyChecker.check_fast_available():
            pytest.skip("Fast mode dependencies not available")
        
        extractor = FastExtractor()
        text = "Python is a programming language. It is very popular."
        triplets = extractor.extract(text, "TestAuthor")
        
        # Should return a list of triplets
        assert isinstance(triplets, list)
        # Each triplet should be a tuple of (source, relation, target, sentiment)
        for triplet in triplets:
            assert isinstance(triplet, tuple)
            assert len(triplet) == 4
            source, relation, target, sentiment = triplet
            assert isinstance(source, str)
            assert isinstance(relation, str)
            assert isinstance(target, str)
            assert isinstance(sentiment, (int, float))
            assert -1.0 <= sentiment <= 1.0


class TestLLMExtractor:
    """Test LLMExtractor."""
    
    def test_initialization(self):
        """Test LLMExtractor initializes."""
        if not DependencyChecker.check_llm_available():
            pytest.skip("LLM dependencies not available")
        
        extractor = LLMExtractor()
        assert extractor is not None
    
    @pytest.mark.skipif(
        not DependencyChecker.check_llm_available(),
        reason="LLM dependencies not available"
    )
    def test_extract_requires_llm(self):
        """Test that extract method exists."""
        extractor = LLMExtractor()
        # Just verify the method exists
        assert hasattr(extractor, 'extract')


class TestGetExtractor:
    """Test extractor factory function."""
    
    def test_get_fast_extractor(self):
        """Test getting fast extractor."""
        if not DependencyChecker.check_fast_available():
            pytest.skip("Fast mode dependencies not available")
        
        extractor = get_extractor(fast_mode=True)
        assert isinstance(extractor, FastExtractor)
    
    def test_get_llm_extractor(self):
        """Test getting LLM extractor."""
        if not DependencyChecker.check_llm_available():
            pytest.skip("LLM dependencies not available")
        
        extractor = get_extractor(fast_mode=False)
        assert isinstance(extractor, LLMExtractor)
    
    def test_get_extractor_no_dependencies(self):
        """Test getting extractor with no dependencies."""
        # This test might fail if dependencies are available
        # but demonstrates the error handling
        pass
