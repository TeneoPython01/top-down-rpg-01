"""
src/systems/encounter.py - Step-based random encounter system (Phase 2).
"""

from __future__ import annotations

import random

from settings import ENCOUNTER_RATE_VARIANCE


class EncounterSystem:
    """Counts steps on the overworld and triggers random encounters.

    Attributes
    ----------
    steps:
        Number of tiles moved since the last encounter.
    encounter_rate:
        Average steps between encounters (configurable per zone).
    """

    def __init__(self, encounter_rate: int = 20) -> None:
        self.steps = 0
        self.encounter_rate = encounter_rate
        self._threshold = self._roll_threshold()

    def _roll_threshold(self) -> int:
        """Pick the next encounter step count (±ENCOUNTER_RATE_VARIANCE of rate)."""
        half = max(1, int(self.encounter_rate * ENCOUNTER_RATE_VARIANCE))
        return random.randint(self.encounter_rate - half, self.encounter_rate + half)

    def step(self) -> bool:
        """Record one step.  Returns True if an encounter should trigger."""
        self.steps += 1
        if self.steps >= self._threshold:
            self.steps = 0
            self._threshold = self._roll_threshold()
            return True
        return False

    def reset(self) -> None:
        """Reset after leaving an encounter zone."""
        self.steps = 0
        self._threshold = self._roll_threshold()
