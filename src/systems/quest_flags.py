"""
src/systems/quest_flags.py - Story progression flags (Phase 5).
"""

from __future__ import annotations

from typing import Dict


class QuestFlags:
    """Boolean flag store for tracking story events.

    All flags start as False and are set to True when the event occurs.
    """

    def __init__(self) -> None:
        self._flags: Dict[str, bool] = {}

    def set(self, flag: str, value: bool = True) -> None:
        self._flags[flag] = value

    def get(self, flag: str) -> bool:
        return self._flags.get(flag, False)

    def __contains__(self, flag: str) -> bool:
        return self.get(flag)

    def to_dict(self) -> Dict[str, bool]:
        return dict(self._flags)

    def from_dict(self, data: Dict[str, bool]) -> None:
        self._flags.update(data)
