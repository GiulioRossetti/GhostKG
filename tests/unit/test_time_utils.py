"""Tests for SimulationTime and time_utils module."""
import pytest
import datetime
from ghost_kg.utils.time_utils import SimulationTime, parse_time_input


class TestSimulationTime:
    """Test SimulationTime class."""
    
    def test_datetime_mode_creation(self):
        """Test creating SimulationTime with datetime."""
        dt = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
        sim_time = SimulationTime(datetime_value=dt)
        
        assert sim_time.is_datetime_mode()
        assert not sim_time.is_round_mode()
        assert sim_time.to_datetime() == dt
        assert sim_time.to_round() is None
    
    def test_round_mode_creation(self):
        """Test creating SimulationTime with round-based time."""
        sim_time = SimulationTime(day=5, hour=14)
        
        assert sim_time.is_round_mode()
        assert not sim_time.is_datetime_mode()
        assert sim_time.to_round() == (5, 14)
        assert sim_time.to_datetime() is None
    
    def test_from_datetime_classmethod(self):
        """Test from_datetime classmethod."""
        dt = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
        sim_time = SimulationTime.from_datetime(dt)
        
        assert sim_time.is_datetime_mode()
        assert sim_time.to_datetime() == dt
    
    def test_from_round_classmethod(self):
        """Test from_round classmethod."""
        sim_time = SimulationTime.from_round(10, 23)
        
        assert sim_time.is_round_mode()
        assert sim_time.to_round() == (10, 23)
    
    def test_datetime_timezone_handling(self):
        """Test that naive datetime gets UTC timezone."""
        naive_dt = datetime.datetime(2025, 1, 1, 9, 0, 0)
        sim_time = SimulationTime(datetime_value=naive_dt)
        
        result_dt = sim_time.to_datetime()
        assert result_dt.tzinfo == datetime.timezone.utc
    
    def test_invalid_both_params(self):
        """Test that providing both datetime and round params raises error."""
        dt = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
        with pytest.raises(ValueError, match="Cannot specify both"):
            SimulationTime(datetime_value=dt, day=1, hour=9)
    
    def test_invalid_no_params(self):
        """Test that providing no params raises error."""
        with pytest.raises(ValueError, match="Must specify either"):
            SimulationTime()
    
    def test_invalid_partial_round(self):
        """Test that providing only day or only hour raises error."""
        with pytest.raises(ValueError, match="Must specify either"):
            SimulationTime(day=1)
        with pytest.raises(ValueError, match="Must specify either"):
            SimulationTime(hour=9)
    
    def test_invalid_day_zero(self):
        """Test that day < 1 raises error."""
        with pytest.raises(ValueError, match="Day must be >= 1"):
            SimulationTime(day=0, hour=9)
    
    def test_invalid_day_negative(self):
        """Test that negative day raises error."""
        with pytest.raises(ValueError, match="Day must be >= 1"):
            SimulationTime(day=-1, hour=9)
    
    def test_invalid_hour_negative(self):
        """Test that hour < 0 raises error."""
        with pytest.raises(ValueError, match="Hour must be in"):
            SimulationTime(day=1, hour=-1)
    
    def test_invalid_hour_too_large(self):
        """Test that hour > 23 raises error."""
        with pytest.raises(ValueError, match="Hour must be in"):
            SimulationTime(day=1, hour=24)
    
    def test_str_representation_datetime(self):
        """Test string representation for datetime mode."""
        dt = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
        sim_time = SimulationTime.from_datetime(dt)
        
        str_repr = str(sim_time)
        assert "SimulationTime" in str_repr
        assert "datetime" in str_repr
    
    def test_str_representation_round(self):
        """Test string representation for round mode."""
        sim_time = SimulationTime.from_round(5, 14)
        
        str_repr = str(sim_time)
        assert "SimulationTime" in str_repr
        assert "day=5" in str_repr
        assert "hour=14" in str_repr
    
    def test_equality_datetime(self):
        """Test equality comparison for datetime mode."""
        dt = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
        sim_time1 = SimulationTime.from_datetime(dt)
        sim_time2 = SimulationTime.from_datetime(dt)
        
        assert sim_time1 == sim_time2
    
    def test_equality_round(self):
        """Test equality comparison for round mode."""
        sim_time1 = SimulationTime.from_round(5, 14)
        sim_time2 = SimulationTime.from_round(5, 14)
        
        assert sim_time1 == sim_time2
    
    def test_inequality_different_modes(self):
        """Test that datetime and round modes are not equal."""
        dt = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
        sim_time1 = SimulationTime.from_datetime(dt)
        sim_time2 = SimulationTime.from_round(1, 9)
        
        assert sim_time1 != sim_time2
    
    def test_inequality_different_values(self):
        """Test inequality for different values."""
        sim_time1 = SimulationTime.from_round(5, 14)
        sim_time2 = SimulationTime.from_round(5, 15)
        
        assert sim_time1 != sim_time2


class TestParseTimeInput:
    """Test parse_time_input function."""
    
    def test_parse_datetime(self):
        """Test parsing datetime input."""
        dt = datetime.datetime(2025, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)
        result = parse_time_input(dt)
        
        assert isinstance(result, SimulationTime)
        assert result.is_datetime_mode()
        assert result.to_datetime() == dt
    
    def test_parse_tuple(self):
        """Test parsing (day, hour) tuple."""
        result = parse_time_input((5, 14))
        
        assert isinstance(result, SimulationTime)
        assert result.is_round_mode()
        assert result.to_round() == (5, 14)
    
    def test_parse_simulation_time(self):
        """Test that SimulationTime is returned as-is."""
        sim_time = SimulationTime.from_round(5, 14)
        result = parse_time_input(sim_time)
        
        assert result is sim_time
    
    def test_invalid_tuple_length(self):
        """Test that invalid tuple length raises error."""
        with pytest.raises(ValueError, match="Invalid time input type"):
            parse_time_input((1, 2, 3))
    
    def test_invalid_tuple_types(self):
        """Test that non-integer tuple values raise error."""
        with pytest.raises(ValueError, match="Tuple must contain two integers"):
            parse_time_input((1.5, 9))
        with pytest.raises(ValueError, match="Tuple must contain two integers"):
            parse_time_input((1, "9"))
    
    def test_invalid_type(self):
        """Test that invalid input type raises error."""
        with pytest.raises(ValueError, match="Invalid time input type"):
            parse_time_input("not a valid time")
        with pytest.raises(ValueError, match="Invalid time input type"):
            parse_time_input(12345)
