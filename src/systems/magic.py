"""
src/systems/magic.py - Spell definitions and casting logic (Phase 3).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from settings import DATA_DIR


def load_spells() -> Dict[str, Any]:
    """Load spell definitions from data/spells.json."""
    path = os.path.join(DATA_DIR, "spells.json")
    with open(path) as f:
        return {s["id"]: s for s in json.load(f)}


def get_learnable_spells(all_spells: Dict[str, Any], level: int) -> List[str]:
    """Return spell IDs the player should know at the given level."""
    return [
        sid
        for sid, data in all_spells.items()
        if data.get("learn_level", 99) <= level
    ]
