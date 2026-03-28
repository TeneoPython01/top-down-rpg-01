"""
src/utils/town_maps.py - Static town map data (Phase 4).

Each town is described by:
  tiles    — 2-D list[row][col] of tile IDs (0=grass, 1=wall, 3=path)
  spawn    — (col, row) player appears when entering from the overworld
  npcs     — list of NPC descriptor dicts
  events   — {(col, row): {"type": ...}} for shop / inn / exit triggers

OVERWORLD_TOWN_ENTRANCES maps overworld tile positions to town names.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Any

# Tile-ID shortcuts
_G = 0  # grass (walkable floor)
_W = 1  # wall  (blocked)
_P = 3  # path  (walkable, cosmetic)

# ── Ashenvale Town (20 cols × 15 rows) ───────────────────────────────────────
#
#  Buildings (rows 2-4):
#    cols 2-4  — General Store      interior at (3, 3)  → shop trigger
#    cols 7-9  — Inn                interior at (8, 3)  → inn trigger
#    cols 13-15 — Elder's House     (decoration only)
#    cols 17-19 — Healer's Cottage  (decoration only)
#  Exit: (10, 14) — gap in the south wall
#
ASHENVALE_TILES: List[List[int]] = [
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # 0
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 1
    [_W, _G, _W, _W, _W, _G, _G, _W, _W, _W, _G, _G, _G, _W, _W, _W, _G, _W, _W, _W],  # 2  buildings
    [_W, _G, _W, _G, _W, _G, _G, _W, _G, _W, _G, _G, _G, _W, _G, _W, _G, _W, _G, _W],  # 3  interiors
    [_W, _G, _W, _G, _G, _G, _G, _W, _G, _G, _G, _G, _G, _W, _W, _G, _G, _W, _W, _W],  # 4  doors open
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 5
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 6
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 7
    [_W, _G, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _G, _W],  # 8  main street
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 9
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 10
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 11
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 12
    [_W, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _G, _W],  # 13 south path
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _G, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # 14 south wall + exit col 10
]

ASHENVALE_SPAWN: Tuple[int, int] = (10, 12)

ASHENVALE_NPCS: List[Dict[str, Any]] = [
    {
        "name": "Village Elder",
        "dialog_id": "village_elder_before",
        "col": 5,
        "row": 6,
        "color": (220, 200, 50),   # gold
    },
    {
        "name": "Farmer",
        "dialog_id": "farmer_ashenvale",
        "col": 4,
        "row": 11,
        "color": (80, 160, 60),    # green
    },
    {
        "name": "Healer",
        "dialog_id": "healer_npc",
        "col": 15,
        "row": 11,
        "color": (60, 200, 200),   # cyan
    },
]

# (col, row) → event descriptor
ASHENVALE_EVENTS: Dict[Tuple[int, int], Dict[str, Any]] = {
    (3, 3): {"type": "shop", "shop_id": "ashenvale"},
    (8, 3): {"type": "inn"},
    (10, 14): {"type": "exit"},
}

# ── Ironhaven Town (20 cols × 15 rows) ───────────────────────────────────────
#
#  Buildings (rows 2-4):
#    cols 2-5  — Ironhaven Armory   interior at (3, 3)  → shop trigger
#    cols 8-10 — Smithy             (decoration)
#    cols 13-17 — Traveller's Rest  interior at (15, 3) → inn trigger
#  Exit: (10, 14)
#
IRONHAVEN_TILES: List[List[int]] = [
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # 0
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 1
    [_W, _G, _W, _W, _W, _W, _G, _G, _W, _W, _W, _G, _G, _W, _W, _W, _W, _W, _G, _W],  # 2
    [_W, _G, _W, _G, _G, _W, _G, _G, _W, _G, _W, _G, _G, _W, _G, _G, _G, _W, _G, _W],  # 3
    [_W, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _W, _G, _W, _G, _G, _W],  # 4  doors open
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 5
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 6
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 7
    [_W, _G, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _G, _W],  # 8  main street
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 9
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 10
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 11
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 12
    [_W, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _G, _W],  # 13 south path
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _G, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # 14 south wall + exit
]

IRONHAVEN_SPAWN: Tuple[int, int] = (10, 12)

IRONHAVEN_NPCS: List[Dict[str, Any]] = [
    {
        "name": "Blacksmith",
        "dialog_id": "ironhaven_blacksmith",
        "col": 6,
        "row": 6,
        "color": (200, 120, 50),   # orange-brown
    },
]

IRONHAVEN_EVENTS: Dict[Tuple[int, int], Dict[str, Any]] = {
    (3, 3): {"type": "shop", "shop_id": "ironhaven"},
    (15, 3): {"type": "inn"},
    (10, 14): {"type": "exit"},
}

# ── Registry ──────────────────────────────────────────────────────────────────

_TOWN_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ashenvale": {
        "tiles": ASHENVALE_TILES,
        "spawn": ASHENVALE_SPAWN,
        "npcs": ASHENVALE_NPCS,
        "events": ASHENVALE_EVENTS,
        "display_name": "Ashenvale",
    },
    "ironhaven": {
        "tiles": IRONHAVEN_TILES,
        "spawn": IRONHAVEN_SPAWN,
        "npcs": IRONHAVEN_NPCS,
        "events": IRONHAVEN_EVENTS,
        "display_name": "Ironhaven",
    },
}


def get_town_data(town_name: str) -> Dict[str, Any]:
    """Return the town data dict for *town_name* (case-insensitive)."""
    return _TOWN_REGISTRY[town_name.lower()]


# ── Overworld entrance mapping ────────────────────────────────────────────────
# Maps overworld tile positions (col, row) to town names.
# Must match TILE_TOWN placements in DEFAULT_MAP.

OVERWORLD_TOWN_ENTRANCES: Dict[Tuple[int, int], str] = {
    (22, 3): "ironhaven",
    (22, 9): "ashenvale",
}
