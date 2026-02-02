"""
FSRS (Free Spaced Repetition Scheduler) Implementation

This module implements the FSRS v6 algorithm for spaced repetition learning.
FSRS is used to track memory stability and difficulty of concepts over time.

References:
- FSRS Algorithm: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
"""

import datetime
import math
from typing import Optional, Union

from ..storage.database import NodeState
from ..utils.time_utils import SimulationTime


class Rating:
    """
    Rating enum for review quality in FSRS algorithm.

    Attributes:
        Again (int): Complete failure to recall (1)
        Hard (int): Difficult recall with significant effort (2)
        Good (int): Normal recall with some effort (3)
        Easy (int): Perfect recall with no effort (4)
    """

    Again = 1
    Hard = 2
    Good = 3
    Easy = 4


class FSRS:
    """
    Free Spaced Repetition Scheduler v6

    Implements the FSRS-6 algorithm for calculating memory stability and difficulty.
    Uses 21 parameters optimized for knowledge retention modeling.

    Attributes:
        p (list): 21 FSRS-6 parameters for stability and difficulty calculations

    Methods:
        calculate_next: Calculate next memory state based on current state and rating
    """

    def __init__(self) -> None:
        """
        Initialize FSRS with default v6 parameters.

        Returns:
            None
        """
        self.p = [
            0.212,
            1.2931,
            2.3065,
            8.2956,
            6.4133,
            0.8334,
            3.0194,
            0.001,
            1.8722,
            0.1666,
            0.796,
            1.4835,
            0.0614,
            0.2629,
            1.6483,
            0.6014,
            1.8729,
            0.5425,
            0.0912,
            0.0658,
            0.1542,
        ]

    def _calculate_initial_difficulty(self, rating: int) -> float:
        """
        Calculate initial difficulty for a given rating.

        Args:
            rating (int): Review rating (1-4)

        Returns:
            float: Initial difficulty, clamped to [1, 10]

        Formula (FSRS-6):
            D_0(G) = w_4 - e^(w_5 * (G - 1)) + 1
        """
        d = self.p[4] - math.exp(self.p[5] * (rating - 1)) + 1
        return min(max(d, 1), 10)

    def calculate_next(
        self, current_state: NodeState, rating: int, now: Union[datetime.datetime, SimulationTime]
    ) -> NodeState:
        """
        Calculate the next memory state after a review using FSRS-6.

        Args:
            current_state (NodeState): Current NodeState with stability, difficulty, etc.
            rating (int): Review rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            now (Union[datetime.datetime, SimulationTime]): Current timestamp for the review

        Returns:
            NodeState: New memory state with updated stability and difficulty

        Algorithm (FSRS-6):
            For new cards (state=0):
                - Initial stability based on rating: S_0(G) = w[G-1]
                - Initial difficulty: D_0(G) = w_4 - e^(w_5 * (G - 1)) + 1

            For existing cards:
                - Calculate retrievability with trainable decay: 
                  R(t,S) = (1 + factor * t/S)^(-w_20)
                - Update difficulty with linear damping and mean reversion to D_0(4)
                - Update stability based on rating and retrievability
                - For same-day reviews: S'(S,G) = S * e^(w_17 * (G - 3 + w_18)) * S^(-w_19)
        """
        # Convert SimulationTime to datetime for last_review storage
        if isinstance(now, SimulationTime):
            now_dt = now.to_datetime()
        else:
            now_dt = now
        
        # 1. New Cards
        if current_state.state == 0:
            # Initial stability: S_0(G) = w[G-1]
            s = self.p[rating - 1]
            # Initial difficulty (FSRS-6)
            d = self._calculate_initial_difficulty(rating)
            return NodeState(s, d, now_dt, 1, 1)

        # 2. Existing Cards
        s = current_state.stability
        d = current_state.difficulty

        # Calculate retrievability with trainable decay (FSRS-6)
        elapsed_days = 0
        if current_state.last_review:
            last_review = current_state.last_review
            if last_review.tzinfo is None:
                last_review = last_review.replace(tzinfo=datetime.timezone.utc)
            
            # Calculate elapsed time in days
            if isinstance(now, SimulationTime):
                if now.is_round_mode():
                    # For round-based time, we need to convert to datetime for calculation
                    # or calculate directly from rounds
                    # For simplicity in FSRS, we'll use datetime if available, otherwise approximate
                    if now_dt and last_review:
                        elapsed_days = (now_dt - last_review).total_seconds() / 86400
                    else:
                        # Fallback when datetime conversion isn't available in pure round mode
                        # Assumes same-day review which is conservative for memory calculations
                        elapsed_days = 0
                else:
                    elapsed_days = (now_dt - last_review).total_seconds() / 86400
            else:
                elapsed_days = (now - last_review).total_seconds() / 86400
            
            if elapsed_days < 0:
                elapsed_days = 0
            
            # R(t,S) = (1 + factor * t/S)^(-w_20)
            # where factor = 0.9^(-1/w_20) - 1 to ensure R(S,S) = 90%
            factor = 0.9 ** (-1 / self.p[20]) - 1
            retrievability = (1 + factor * elapsed_days / s) ** -self.p[20]
        else:
            # Match legacy implementation: new cards have 1.0 retrievability
            retrievability = 1.0

        # Calculate D_0(4) for mean reversion (FSRS-6)
        d_0_4 = self._calculate_initial_difficulty(4)

        # Update difficulty with linear damping (FSRS-5+)
        # ΔD(G) = -w_6 * (G - 3)
        delta_d = -self.p[6] * (rating - 3)
        # D' = D + ΔD * (10 - D) / 9 (linear damping)
        d_prime = d + delta_d * (10 - d) / 9
        # Mean reversion to D_0(4)
        next_d = min(max(self.p[7] * d_0_4 + (1 - self.p[7]) * d_prime, 1), 10)

        # Check if same-day review (elapsed_days == 0 or very small)
        is_same_day = elapsed_days < 1

        # Update stability based on rating
        if rating == Rating.Again:
            # Post-lapse stability (same as FSRS-4.5)
            next_s = (
                self.p[11]
                * (next_d ** -self.p[12])
                * ((s + 1) ** self.p[13] - 1)
                * math.exp((1 - retrievability) * self.p[14])
            )
            state = 1
        else:
            if is_same_day:
                # Same-day review stability (FSRS-6)
                # S'(S,G) = S * e^(w_17 * (G - 3 + w_18)) * S^(-w_19)
                next_s = s * math.exp(self.p[17] * (rating - 3 + self.p[18])) * (s ** -self.p[19])
            else:
                # Regular review stability with hard penalty and easy bonus
                hard_penalty = self.p[15] if rating == Rating.Hard else 1
                easy_bonus = self.p[16] if rating == Rating.Easy else 1
                next_s = s * (
                    1
                    + math.exp(self.p[8])
                    * (11 - next_d)
                    * (s ** -self.p[9])
                    * (math.exp((1 - retrievability) * self.p[10]) - 1)
                    * hard_penalty
                    * easy_bonus
                )
            state = 2

        next_s = max(next_s, 0.1)
        return NodeState(next_s, next_d, now_dt, current_state.reps + 1, state)
