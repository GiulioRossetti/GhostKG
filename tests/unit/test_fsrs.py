"""Unit tests for FSRS algorithm."""
import pytest
from datetime import datetime, timezone, timedelta
from ghost_kg import FSRS, Rating, NodeState


class TestRating:
    """Test Rating enum."""
    
    def test_rating_values(self):
        """Test Rating enum has correct values."""
        assert Rating.Again == 1
        assert Rating.Hard == 2
        assert Rating.Good == 3
        assert Rating.Easy == 4


class TestFSRS:
    """Test FSRS algorithm."""
    
    def test_initialization(self):
        """Test FSRS initializes with default parameters."""
        fsrs = FSRS()
        assert len(fsrs.p) == 21
        assert all(isinstance(p, (int, float)) for p in fsrs.p)
    
    def test_new_card_again(self):
        """Test new card with 'Again' rating."""
        fsrs = FSRS()
        now = datetime.now(timezone.utc)
        
        initial = NodeState(0, 0, None, 0, 0)
        result = fsrs.calculate_next(initial, Rating.Again, now)
        
        # New card with Again should have low stability (FSRS-6: w[0] = 0.212)
        assert result.stability == pytest.approx(0.212, rel=0.01)
        assert result.state == 1  # Learning state
        assert result.reps == 1
        assert result.last_review == now
    
    def test_new_card_good(self):
        """Test new card with 'Good' rating."""
        fsrs = FSRS()
        now = datetime.now(timezone.utc)
        
        initial = NodeState(0, 0, None, 0, 0)
        result = fsrs.calculate_next(initial, Rating.Good, now)
        
        # Good should have decent stability (FSRS-6: w[2] = 2.3065)
        assert result.stability == pytest.approx(2.3065, rel=0.01)
        assert result.state == 1
        assert result.reps == 1
    
    def test_stability_increases_on_success(self):
        """Test that stability increases on successful recall."""
        fsrs = FSRS()
        now = datetime.now(timezone.utc)
        
        # Start with a card in review state
        initial = NodeState(
            stability=5.0,
            difficulty=5.0,
            last_review=now - timedelta(days=2),
            reps=1,
            state=2
        )
        
        result = fsrs.calculate_next(initial, Rating.Good, now)
        
        assert result.stability > initial.stability
        assert result.reps == 2
        assert result.state == 2
    
    def test_difficulty_increases_on_failure(self):
        """Test that difficulty increases when failing."""
        fsrs = FSRS()
        now = datetime.now(timezone.utc)
        
        initial = NodeState(
            stability=5.0,
            difficulty=3.0,
            last_review=now - timedelta(days=2),
            reps=1,
            state=2
        )
        
        result = fsrs.calculate_next(initial, Rating.Again, now)
        
        # Difficulty should increase on failure
        assert result.difficulty > initial.difficulty
        # But should be capped at 10
        assert result.difficulty <= 10.0
