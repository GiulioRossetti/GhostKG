"""
FSRS (Free Spaced Repetition Scheduler) Implementation

This module implements the FSRS v4.5 algorithm for spaced repetition learning.
FSRS is used to track memory stability and difficulty of concepts over time.

References:
- FSRS Algorithm: https://github.com/open-spaced-repetition/fsrs4anki
"""

import datetime
import math
from typing import Optional

from .storage import NodeState


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
    Free Spaced Repetition Scheduler v4.5

    Implements the FSRS algorithm for calculating memory stability and difficulty.
    Uses 17 parameters optimized for knowledge retention modeling.

    Attributes:
        p (list): 17 FSRS parameters for stability and difficulty calculations

    Methods:
        calculate_next: Calculate next memory state based on current state and rating
    """

    def __init__(self) -> None:
        """
        Initialize FSRS with default v4.5 parameters.

        Returns:
            None
        """
        self.p = [
            0.4,
            0.6,
            2.4,
            5.8,
            4.93,
            0.94,
            0.86,
            0.01,
            1.49,
            0.14,
            0.94,
            2.18,
            0.05,
            0.34,
            1.26,
            0.29,
            2.61,
        ]

    def calculate_next(
        self, current_state: NodeState, rating: int, now: datetime.datetime
    ) -> NodeState:
        """
        Calculate the next memory state after a review.

        Args:
            current_state (NodeState): Current NodeState with stability, difficulty, etc.
            rating (int): Review rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            now (datetime.datetime): Current timestamp for the review

        Returns:
            NodeState: New memory state with updated stability and difficulty

        Algorithm:
            For new cards (state=0):
                - Initial stability based on rating
                - Initial difficulty based on rating

            For existing cards:
                - Calculate retrievability based on time elapsed
                - Update stability based on rating and retrievability
                - Update difficulty based on rating and current difficulty
        """
        # 1. New Cards
        if current_state.state == 0:
            s = self.p[rating - 1]
            d = min(max(self.p[4] - (rating - 3) * self.p[5], 1), 10)
            return NodeState(s, d, now, 1, 1)

        # 2. Existing Cards
        s = current_state.stability
        d = current_state.difficulty

        if current_state.last_review:
            last_review = current_state.last_review
            if last_review.tzinfo is None:
                last_review = last_review.replace(tzinfo=datetime.timezone.utc)
            elapsed_days = (now - last_review).total_seconds() / 86400
            if elapsed_days < 0:
                elapsed_days = 0
            retrievability = (1 + elapsed_days / (9 * s)) ** -1
        else:
            # Match legacy implementation: new cards have 1.0 retrievability
            retrievability = 1.0

        # Update difficulty (matches legacy core_legacy.py lines 91-98)
        next_d = min(
            max(
                self.p[7] * self.p[4] + (1 - self.p[7]) * (d - self.p[6] * (rating - 3)),
                1,
            ),
            10,
        )

        # Update stability based on rating (matches legacy core_legacy.py lines 100-120)
        if rating == Rating.Again:
            next_s = (
                self.p[11]
                * (next_d ** -self.p[12])
                * ((s + 1) ** self.p[13] - 1)
                * math.exp((1 - retrievability) * self.p[14])
            )
            state = 1
        else:
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
        return NodeState(next_s, next_d, now, current_state.reps + 1, state)
