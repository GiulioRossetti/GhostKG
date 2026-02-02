"""
Time utilities for GhostKG.

This module provides flexible time representation for simulations,
supporting both real datetime objects and simplified round-based time.
"""

import datetime
from typing import Optional, Tuple, Union


class SimulationTime:
    """
    Flexible time representation for agent simulations.
    
    Supports two modes:
    1. Datetime mode: Uses standard datetime.datetime objects
    2. Round-based mode: Uses (day: int, hour: int) tuples
    
    Attributes:
        datetime_value (Optional[datetime.datetime]): The datetime representation (if in datetime mode)
        day (Optional[int]): The day number (if in round-based mode, >= 1)
        hour (Optional[int]): The hour (if in round-based mode, 0-23)
    """
    
    def __init__(
        self,
        datetime_value: Optional[datetime.datetime] = None,
        day: Optional[int] = None,
        hour: Optional[int] = None,
    ) -> None:
        """
        Initialize a SimulationTime.
        
        Args:
            datetime_value: A datetime object (for datetime mode)
            day: Day number starting from 1 (for round-based mode)
            hour: Hour in [0, 23] (for round-based mode)
            
        Raises:
            ValueError: If invalid arguments are provided
        
        Note:
            Either provide datetime_value OR (day, hour), not both.
        """
        if datetime_value is not None and (day is not None or hour is not None):
            raise ValueError("Cannot specify both datetime_value and (day, hour)")
        
        if datetime_value is None and (day is None or hour is None):
            raise ValueError("Must specify either datetime_value or both (day, hour)")
        
        if datetime_value is not None:
            # Datetime mode
            # Ensure timezone awareness
            if datetime_value.tzinfo is None:
                datetime_value = datetime_value.replace(tzinfo=datetime.timezone.utc)
            self.datetime_value = datetime_value
            self.day = None
            self.hour = None
        else:
            # Round-based mode
            if day < 1:
                raise ValueError("Day must be >= 1")
            if hour < 0 or hour > 23:
                raise ValueError("Hour must be in [0, 23]")
            self.datetime_value = None
            self.day = day
            self.hour = hour
    
    @classmethod
    def from_datetime(cls, dt: datetime.datetime) -> "SimulationTime":
        """Create from datetime object."""
        return cls(datetime_value=dt)
    
    @classmethod
    def from_round(cls, day: int, hour: int) -> "SimulationTime":
        """Create from round-based time."""
        return cls(day=day, hour=hour)
    
    def is_datetime_mode(self) -> bool:
        """Check if using datetime mode."""
        return self.datetime_value is not None
    
    def is_round_mode(self) -> bool:
        """Check if using round-based mode."""
        return self.day is not None
    
    def to_datetime(self) -> Optional[datetime.datetime]:
        """Get datetime representation (None if in round mode)."""
        return self.datetime_value
    
    def to_round(self) -> Optional[Tuple[int, int]]:
        """Get round-based representation (None if in datetime mode)."""
        if self.day is not None and self.hour is not None:
            return (self.day, self.hour)
        return None
    
    def __str__(self) -> str:
        """String representation."""
        if self.is_datetime_mode():
            return f"SimulationTime(datetime={self.datetime_value})"
        else:
            return f"SimulationTime(day={self.day}, hour={self.hour})"
    
    def __repr__(self) -> str:
        """Repr representation."""
        return self.__str__()
    
    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        # Allow comparison with datetime objects
        if isinstance(other, datetime.datetime):
            if self.is_datetime_mode():
                return self.datetime_value == other
            return False
        if not isinstance(other, SimulationTime):
            return False
        if self.is_datetime_mode() and other.is_datetime_mode():
            return self.datetime_value == other.datetime_value
        if self.is_round_mode() and other.is_round_mode():
            return self.day == other.day and self.hour == other.hour
        return False


def parse_time_input(
    time_input: Union[datetime.datetime, Tuple[int, int], SimulationTime]
) -> SimulationTime:
    """
    Parse various time input formats into SimulationTime.
    
    Args:
        time_input: Can be:
            - datetime.datetime object
            - (day, hour) tuple
            - SimulationTime object (returned as-is)
    
    Returns:
        SimulationTime object
    
    Raises:
        ValueError: If input format is invalid
    """
    if isinstance(time_input, SimulationTime):
        return time_input
    elif isinstance(time_input, datetime.datetime):
        return SimulationTime.from_datetime(time_input)
    elif isinstance(time_input, tuple) and len(time_input) == 2:
        day, hour = time_input
        if not isinstance(day, int) or not isinstance(hour, int):
            raise ValueError("Tuple must contain two integers (day, hour)")
        return SimulationTime.from_round(day, hour)
    else:
        raise ValueError(
            f"Invalid time input type: {type(time_input)}. "
            "Expected datetime.datetime, (day, hour) tuple, or SimulationTime"
        )
