"""
src/systems/save_load.py - Save/load system with five named slots (Phase 6).

Each slot is stored as ``data/saves/save_<N>.json`` and contains:
  - slot        : slot number (1-5)
  - timestamp   : human-readable save time
  - location    : current map/area name
  - player_name : quick-access display name
  - player_level: quick-access level for the slot-select UI
  - player      : full player serialization dict (see Player.to_dict)
  - quest_flags : dict of all story-progress flags
"""

from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, Optional

from settings import DATA_DIR, NUM_SAVE_SLOTS

# Directory that holds the per-slot JSON files.
SAVES_DIR = os.path.join(DATA_DIR, "saves")


# ── Slot path ─────────────────────────────────────────────────────────────────

def get_slot_path(slot: int) -> str:
    """Return the file-system path for *slot* (1-based).  Creates the saves
    directory if it does not yet exist."""
    os.makedirs(SAVES_DIR, exist_ok=True)
    return os.path.join(SAVES_DIR, f"save_{slot}.json")


# ── Slot metadata (for UI display) ───────────────────────────────────────────

def get_slot_info(slot: int) -> Optional[Dict[str, Any]]:
    """Return a lightweight summary dict for displaying in the UI, or ``None``
    if the slot is empty / unreadable.

    Keys: ``slot``, ``name``, ``level``, ``location``, ``timestamp``.
    """
    path = get_slot_path(slot)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return {
            "slot": slot,
            "name": data.get("player_name", "Unknown"),
            "level": data.get("player_level", 1),
            "location": data.get("location", "Unknown"),
            "timestamp": data.get("timestamp", ""),
        }
    except (OSError, json.JSONDecodeError):
        return None


# ── Save ─────────────────────────────────────────────────────────────────────

def save_to_slot(game: Any, slot: int) -> bool:
    """Serialize the full game state to *slot* (1-``NUM_SAVE_SLOTS``).

    Returns ``True`` on success, ``False`` if the player is not yet set or
    the file cannot be written.
    """
    player = getattr(game, "player", None)
    if player is None:
        return False

    quest_flags = getattr(game, "quest_flags", None)
    quest_log = getattr(game, "quest_log", None)
    data: Dict[str, Any] = {
        "slot": slot,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "location": getattr(game, "current_location", "overworld"),
        "player_name": player.name,
        "player_level": player.level,
        "player": player.to_dict(),
        "quest_flags": quest_flags.to_dict() if quest_flags is not None else {},
        "quest_log": quest_log.to_dict() if quest_log is not None else {},
    }

    path = get_slot_path(slot)
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        return True
    except OSError:
        return False


# ── Load ─────────────────────────────────────────────────────────────────────

def load_from_slot(slot: int) -> Optional[Dict[str, Any]]:
    """Load and return raw save data from *slot*, or ``None`` if the slot is
    empty or the file is corrupt."""
    path = get_slot_path(slot)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def apply_save_to_game(data: Dict[str, Any], game: Any) -> None:
    """Restore game state from a save data dict, modifying *game* in place.

    After this call ``game.player`` is a fully-restored ``Player`` and
    ``game.current_location`` reflects where the game was saved.
    """
    from src.entities.player import Player

    player_data = data.get("player", {})
    game.player = Player.from_dict(player_data)
    game.current_location = data.get("location", "overworld")

    # Sync the shared inventory reference so shops, chests, and battle rewards
    # all operate on the same inventory object that the pause menu reads.
    game.inventory = game.player.inventory

    quest_flags = getattr(game, "quest_flags", None)
    if quest_flags is not None:
        quest_flags.from_dict(data.get("quest_flags", {}))

    quest_log = getattr(game, "quest_log", None)
    if quest_log is not None:
        quest_log.from_dict(data.get("quest_log", {}))
