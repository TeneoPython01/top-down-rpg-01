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

# ── Willowmere Town (20 cols × 15 rows) ──────────────────────────────────────
#
#  A lakeside hamlet with a magic shop and inn.
#  Buildings (rows 2-4):
#    cols 2-5  — Magic Shop     interior at (3, 3)  → shop trigger
#    cols 8-10 — Healer         (NPC only)
#    cols 13-16 — Willowmere Inn interior at (14, 3) → inn trigger
#  Lake: rows 9-12, cols 8-14
#  Exit: (10, 14)
#
WILLOWMERE_TILES: List[List[int]] = [
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # 0
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 1
    [_W, _G, _W, _W, _W, _W, _G, _G, _W, _W, _W, _G, _G, _W, _W, _W, _W, _G, _G, _W],  # 2  buildings
    [_W, _G, _W, _G, _G, _W, _G, _G, _W, _G, _W, _G, _G, _W, _G, _G, _W, _G, _G, _W],  # 3  interiors
    [_W, _G, _W, _G, _G, _G, _G, _G, _W, _G, _G, _G, _G, _W, _W, _G, _G, _G, _G, _W],  # 4  doors open
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 5
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 6
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 7
    [_W, _G, _P, _P, _P, _P, _P, _P, _G, _G, _G, _G, _G, _P, _P, _P, _P, _G, _G, _W],  # 8  paths around lake
    [_W, _G, _G, _G, _G, _G, _G, _G, _T, _T, _T, _T, _T, _G, _G, _G, _G, _G, _G, _W],  # 9  lake
    [_W, _G, _G, _G, _G, _G, _G, _T, _T, _T, _T, _T, _T, _T, _G, _G, _G, _G, _G, _W],  # 10
    [_W, _G, _G, _G, _G, _G, _G, _T, _T, _T, _T, _T, _T, _T, _G, _G, _G, _G, _G, _W],  # 11
    [_W, _G, _G, _G, _G, _G, _G, _G, _T, _T, _T, _T, _T, _G, _G, _G, _G, _G, _G, _W],  # 12
    [_W, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _G, _W],  # 13 south path
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _G, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # 14 exit
]

WILLOWMERE_SPAWN: Tuple[int, int] = (10, 12)

WILLOWMERE_NPCS: List[Dict[str, Any]] = [
    {
        "name": "Traveler",
        "dialog_id": "willowmere_traveler",
        "col": 6,
        "row": 7,
        "color": (140, 160, 200),  # blue-grey
    },
    {
        "name": "Willowmere Elder",
        "dialog_id": "willowmere_elder",
        "col": 17,
        "row": 7,
        "color": (200, 200, 100),  # pale gold
    },
]

WILLOWMERE_EVENTS: Dict[Tuple[int, int], Dict[str, Any]] = {
    (3, 3): {"type": "shop", "shop_id": "willowmere"},
    (14, 3): {"type": "inn"},
    (10, 14): {"type": "exit"},
}

# ── Subterra (20 cols × 15 rows) ──────────────────────────────────────────────
#
#  Hidden underground city. No random encounters.
#  Buildings:
#    cols 2-5  — Archivist's Library  NPC Archivist Lena at (3, 7)
#    cols 8-10 — Merchant Dax's Shop  interior at (9, 3) → shop trigger
#    cols 13-16 — Ancestral Home      interior at (14, 3) → journal event
#  Elder Marek wanders the central plaza.
#  No inn (Subterra provides free rest at the ancestral home).
#  Exit: (10, 14) → back to Subterra Passage
#
SUBTERRA_TILES: List[List[int]] = [
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # 0
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 1
    [_W, _G, _W, _W, _W, _W, _G, _G, _W, _W, _W, _G, _G, _W, _W, _W, _W, _G, _G, _W],  # 2
    [_W, _G, _W, _G, _G, _W, _G, _G, _W, _G, _W, _G, _G, _W, _G, _G, _W, _G, _G, _W],  # 3
    [_W, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _G, _G, _W],  # 4
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 5
    [_W, _G, _G, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _G, _G, _G, _W],  # 6 central plaza
    [_W, _G, _G, _P, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _P, _G, _G, _G, _W],  # 7
    [_W, _G, _G, _P, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _P, _G, _G, _G, _W],  # 8
    [_W, _G, _G, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _G, _G, _G, _W],  # 9
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 10
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 11
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # 12
    [_W, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _G, _W],  # 13
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _G, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # 14 exit
]

SUBTERRA_SPAWN: Tuple[int, int] = (10, 12)

SUBTERRA_NPCS: List[Dict[str, Any]] = [
    {
        "name": "Elder Marek",
        "dialog_id": "elder_marek",
        "col": 9,
        "row": 7,
        "color": (180, 220, 180),  # pale green (bioluminescent glow)
    },
    {
        "name": "Archivist Lena",
        "dialog_id": "archivist_lena",
        "col": 3,
        "row": 7,
        "color": (200, 180, 230),  # pale purple
    },
    {
        "name": "Merchant Dax",
        "dialog_id": "merchant_dax",
        "col": 16,
        "row": 7,
        "color": (200, 160, 80),   # golden
    },
]

SUBTERRA_EVENTS: Dict[Tuple[int, int], Dict[str, Any]] = {
    (9, 3): {"type": "shop", "shop_id": "subterra"},
    (14, 3): {"type": "journal"},   # ancestral home — show journal dialog
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
    "willowmere": {
        "tiles": WILLOWMERE_TILES,
        "spawn": WILLOWMERE_SPAWN,
        "npcs": WILLOWMERE_NPCS,
        "events": WILLOWMERE_EVENTS,
        "display_name": "Willowmere",
    },
    "subterra": {
        "tiles": SUBTERRA_TILES,
        "spawn": SUBTERRA_SPAWN,
        "npcs": SUBTERRA_NPCS,
        "events": SUBTERRA_EVENTS,
        "display_name": "Subterra",
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
