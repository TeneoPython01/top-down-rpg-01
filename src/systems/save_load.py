"""
src/systems/save_load.py - Serialize/deserialize game state to/from JSON (Phase 5).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict


SAVE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "save.json"
)


def save_game(data: Dict[str, Any], path: str = SAVE_FILE) -> None:
    """Write *data* dict to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_game(path: str = SAVE_FILE) -> Dict[str, Any] | None:
    """Read and return save data dict, or None if the file doesn't exist."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)
