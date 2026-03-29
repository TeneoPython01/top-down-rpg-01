"""
src/utils/tilemap.py - Simple 2-D array tilemap for Phase 1.

Phase 4 will upgrade this to a pytmx/pyscroll TMX-based loader.
Each cell holds a tile-ID integer (see settings.TILE_* constants).
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import pygame

from settings import TILE_SIZE, TILE_COLORS, TILE_WALL, TILE_WATER, TILE_GRID_COLOR


"""
src/utils/tilemap.py - Simple 2-D array tilemap for Phase 1.

Phase 4 will upgrade this to a pytmx/pyscroll TMX-based loader.
Each cell holds a tile-ID integer (see settings.TILE_* constants).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pygame

from settings import (
    TILE_SIZE,
    TILE_COLORS,
    TILE_WALL,
    TILE_WATER,
    TILE_GRID_COLOR,
    TILE_ZONE_EXIT,
    TILE_DUNGEON,
    TILE_HIDDEN,
)


# ---------------------------------------------------------------------------
# Tile-ID aliases for readability inside map literals
# ---------------------------------------------------------------------------
_G = 0   # grass / walkable floor
_W = 1   # wall (blocked)
_T = 2   # water (blocked)
_P = 3   # path
_E = 4   # TILE_TOWN — town entrance
_Z = 5   # TILE_ZONE_EXIT — zone transition
_D = 6   # TILE_DUNGEON — boss arena entrance
_H = 7   # TILE_HIDDEN — secret wall (Subterra)

# ---------------------------------------------------------------------------
# Default map (Verdant Plains / Ashenvale area).  Tile IDs:
#   0 = grass, 1 = wall, 2 = water, 3 = path, 4 = town entrance
#   5 = zone exit (north → Silverwood Forest)
# ---------------------------------------------------------------------------
DEFAULT_MAP: List[List[int]] = [
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _Z, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # 0 north→silverwood
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _P, _P, _P, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _P, _G, _P, _G, _G, _G, _W, _W, _W, _W, _G, _G, _G, _G, _G, _G, _G, _P, _P, _E, _G, _W],
    [_W, _G, _G, _P, _G, _P, _G, _G, _G, _W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _P, _P, _P, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _W, _W, _W, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _P, _P, _E, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _T, _T, _T, _T, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _T, _T, _T, _T, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _P, _P, _P, _P, _P, _P, _P, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _P, _G, _G, _G, _G, _G, _P, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _P, _G, _G, _G, _G, _G, _P, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _P, _P, _G, _P, _P, _P, _P, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],
]

# Player spawn tile (col, row)
DEFAULT_SPAWN: Tuple[int, int] = (4, 9)

# Zone exits: (col, row) → (target_zone, spawn_col, spawn_row)
DEFAULT_ZONE_EXITS: Dict[Tuple[int, int], Tuple[str, int, int]] = {
    (12, 0): ("silverwood_forest", 12, 18),
}

# ---------------------------------------------------------------------------
# Silverwood Forest (25×20) — Act 1 dungeon zone
# ---------------------------------------------------------------------------
SILVERWOOD_MAP: List[List[int]] = [
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _Z, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # north→stormcrag
    [_W, _G, _W, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _G, _W],
    [_W, _G, _W, _G, _G, _G, _W, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _W, _W, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _W],
    [_W, _W, _G, _G, _D, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # D=Silverwood Clearing
    [_W, _G, _G, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _W, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _W, _G, _W],
    [_W, _G, _W, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _W, _G, _G, _G, _G, _G, _G, _W, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _E, _G, _G, _G, _G, _G, _W],  # E=Willowmere
    [_W, _G, _G, _W, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _T, _T, _T, _T, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # lake
    [_W, _G, _G, _G, _G, _G, _G, _G, _T, _T, _T, _T, _T, _T, _T, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _T, _T, _T, _T, _T, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _W, _G, _W],
    [_W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _W, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _W, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _P, _P, _P, _P, _P, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _Z, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # south→verdant_plains
]

SILVERWOOD_SPAWN: Tuple[int, int] = (12, 17)  # near south exit

SILVERWOOD_ZONE_EXITS: Dict[Tuple[int, int], Tuple[str, int, int]] = {
    (12, 0): ("stormcrag_mountains", 12, 18),
    (12, 19): ("verdant_plains", 12, 1),
}

SILVERWOOD_DUNGEON_ENTRIES: Dict[Tuple[int, int], Dict[str, Any]] = {
    (4, 4): {
        "boss_id": "dire_wolf_alpha",
        "flag": "wolf_alpha_defeated",
        "narration": "The Silverwood Clearing — something stirs in the trees...",
    },
}

SILVERWOOD_TOWN_ENTRANCES: Dict[Tuple[int, int], str] = {
    (18, 9): "willowmere",
}

# ---------------------------------------------------------------------------
# Stormcrag Mountains (25×20) — Act 2 zone
# ---------------------------------------------------------------------------
STORMCRAG_MAP: List[List[int]] = [
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _Z, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # north→dark_lands
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _W, _G, _G, _W, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _W, _G, _G, _G, _W, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _G, _W, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _W, _W, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _W, _W, _G, _G, _G, _G, _D, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _W],  # D=Mountain Pass boss
    [_W, _G, _G, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _W],
    [_W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _H, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # H=hidden Subterra wall
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _W],
    [_W, _G, _G, _W, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _W, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _W, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _G, _G, _G, _W],
    [_W, _W, _G, _G, _W, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _W, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _P, _P, _P, _P, _P, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _Z, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # south→silverwood
]

STORMCRAG_SPAWN: Tuple[int, int] = (12, 17)

STORMCRAG_ZONE_EXITS: Dict[Tuple[int, int], Tuple[str, int, int]] = {
    (12, 0): ("dark_lands", 12, 18),
    (12, 19): ("silverwood_forest", 12, 1),
}

STORMCRAG_DUNGEON_ENTRIES: Dict[Tuple[int, int], Dict[str, Any]] = {
    (12, 6): {
        "boss_id": "bk_lieutenant",
        "flag": "bk_lieutenant_defeated",
        "narration": "The Mountain Pass — a Black Knight soldier blocks the way!",
    },
}

STORMCRAG_HIDDEN_WALLS: Dict[Tuple[int, int], Dict[str, Any]] = {
    (8, 10): {
        "to_zone": "subterra_passage",
        "spawn": (10, 13),
        "flag_required": None,  # always accessible
        "reveal_text": "The rock face shudders... A passage opens!",
    },
}

# ---------------------------------------------------------------------------
# Dark Lands (25×20) — Final overworld zone
# ---------------------------------------------------------------------------
DARK_LANDS_MAP: List[List[int]] = [
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # no further north
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _D, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # D=Black Fortress
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _P, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _P, _P, _P, _P, _P, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _Z, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # south→stormcrag
]

DARK_LANDS_SPAWN: Tuple[int, int] = (12, 17)

DARK_LANDS_ZONE_EXITS: Dict[Tuple[int, int], Tuple[str, int, int]] = {
    (12, 19): ("stormcrag_mountains", 12, 1),
}

DARK_LANDS_DUNGEON_ENTRIES: Dict[Tuple[int, int], Dict[str, Any]] = {
    (12, 4): {
        "boss_id": "beast_king",
        "chain_boss_id": "black_knight",
        "flag": "beast_king_defeated",
        "chain_flag": "black_knight_defeated",
        "narration": "The Black Fortress looms ahead. An immense beast guards the gate...",
        "chain_narration": "The Corrupted Beast King falls. The Black Knight steps forward...",
    },
}

# ---------------------------------------------------------------------------
# Subterra Passage (20×15) — secret cave zone
# ---------------------------------------------------------------------------
SUBTERRA_PASSAGE_MAP: List[List[int]] = [
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _E, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],  # E=Subterra
    [_W, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _W],
    [_W, _G, _W, _G, _G, _G, _G, _G, _G, _G, _D, _G, _G, _G, _G, _G, _W, _G, _G, _W],  # D=Crystal Sentinel
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _W, _W, _W, _G, _G, _G, _W, _W, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _W],
    [_W, _G, _G, _W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _G, _W],
    [_W, _W, _W, _W, _W, _W, _W, _W, _W, _W, _Z, _W, _W, _W, _W, _W, _W, _W, _W, _W],  # south→stormcrag
]

SUBTERRA_PASSAGE_SPAWN: Tuple[int, int] = (10, 12)

SUBTERRA_PASSAGE_ZONE_EXITS: Dict[Tuple[int, int], Tuple[str, int, int]] = {
    (10, 14): ("stormcrag_mountains", 8, 11),
}

SUBTERRA_PASSAGE_DUNGEON_ENTRIES: Dict[Tuple[int, int], Dict[str, Any]] = {
    (10, 4): {
        "boss_id": "crystal_sentinel",
        "flag": "crystal_sentinel_defeated",
        "narration": "A glowing crystal golem blocks the passage to Subterra!",
    },
}

SUBTERRA_PASSAGE_TOWN_ENTRANCES: Dict[Tuple[int, int], str] = {
    (9, 2): "subterra",
}

# ---------------------------------------------------------------------------
# Zone registry
# ---------------------------------------------------------------------------
_ZONES: Dict[str, Dict[str, Any]] = {
    "verdant_plains": {
        "map": DEFAULT_MAP,
        "spawn": DEFAULT_SPAWN,
        "zone_exits": DEFAULT_ZONE_EXITS,
        "dungeon_entries": {},
        "town_entrances": {(22, 3): "ironhaven", (22, 9): "ashenvale"},
        "hidden_walls": {},
        "display_name": "Verdant Plains",
        "encounter_zone": "grasslands",
    },
    "silverwood_forest": {
        "map": SILVERWOOD_MAP,
        "spawn": SILVERWOOD_SPAWN,
        "zone_exits": SILVERWOOD_ZONE_EXITS,
        "dungeon_entries": SILVERWOOD_DUNGEON_ENTRIES,
        "town_entrances": SILVERWOOD_TOWN_ENTRANCES,
        "hidden_walls": {},
        "display_name": "Silverwood Forest",
        "encounter_zone": "forest",
    },
    "stormcrag_mountains": {
        "map": STORMCRAG_MAP,
        "spawn": STORMCRAG_SPAWN,
        "zone_exits": STORMCRAG_ZONE_EXITS,
        "dungeon_entries": STORMCRAG_DUNGEON_ENTRIES,
        "town_entrances": {},
        "hidden_walls": STORMCRAG_HIDDEN_WALLS,
        "display_name": "Stormcrag Mountains",
        "encounter_zone": "mountains",
    },
    "dark_lands": {
        "map": DARK_LANDS_MAP,
        "spawn": DARK_LANDS_SPAWN,
        "zone_exits": DARK_LANDS_ZONE_EXITS,
        "dungeon_entries": DARK_LANDS_DUNGEON_ENTRIES,
        "town_entrances": {},
        "hidden_walls": {},
        "display_name": "Dark Lands",
        "encounter_zone": "dark_lands",
    },
    "subterra_passage": {
        "map": SUBTERRA_PASSAGE_MAP,
        "spawn": SUBTERRA_PASSAGE_SPAWN,
        "zone_exits": SUBTERRA_PASSAGE_ZONE_EXITS,
        "dungeon_entries": SUBTERRA_PASSAGE_DUNGEON_ENTRIES,
        "town_entrances": SUBTERRA_PASSAGE_TOWN_ENTRANCES,
        "hidden_walls": {},
        "display_name": "Subterra Passage",
        "encounter_zone": "subterra_passage",
    },
}


def get_zone_data(zone_name: str) -> Dict[str, Any]:
    """Return the zone data dict for *zone_name*."""
    return _ZONES[zone_name]





class TileMap:
    """Stores a 2-D grid of tile IDs and pre-builds surfaces and collision rects.

    Attributes
    ----------
    data:
        2-D list ``[row][col]`` of tile-ID integers.
    width, height:
        Map dimensions in tiles.
    pixel_width, pixel_height:
        Map dimensions in native pixels.
    spawn:
        (col, row) of the player spawn tile.
    blocked_rects:
        List of pygame.Rect for impassable tiles.
    town_entrances:
        Mapping ``(col, row) → town_name`` for TILE_TOWN tiles.
    zone_exits:
        Mapping ``(col, row) → (zone_name, spawn_col, spawn_row)`` for TILE_ZONE_EXIT tiles.
    dungeon_entries:
        Mapping ``(col, row) → boss_config_dict`` for TILE_DUNGEON tiles.
    hidden_walls:
        Mapping ``(col, row) → config_dict`` for TILE_HIDDEN tiles (interactable).
    """

    def __init__(
        self,
        data: Optional[List[List[int]]] = None,
        spawn: Optional[Tuple[int, int]] = None,
        town_entrances: Optional[Dict[Tuple[int, int], str]] = None,
        zone_exits: Optional[Dict[Tuple[int, int], Tuple[str, int, int]]] = None,
        dungeon_entries: Optional[Dict[Tuple[int, int], Dict[str, Any]]] = None,
        hidden_walls: Optional[Dict[Tuple[int, int], Dict[str, Any]]] = None,
    ) -> None:
        self.data: List[List[int]] = data if data is not None else DEFAULT_MAP
        self.spawn: Tuple[int, int] = spawn if spawn is not None else DEFAULT_SPAWN
        self.town_entrances: Dict[Tuple[int, int], str] = (
            town_entrances if town_entrances is not None else {}
        )
        self.zone_exits: Dict[Tuple[int, int], Tuple[str, int, int]] = (
            zone_exits if zone_exits is not None else {}
        )
        self.dungeon_entries: Dict[Tuple[int, int], Dict[str, Any]] = (
            dungeon_entries if dungeon_entries is not None else {}
        )
        self.hidden_walls: Dict[Tuple[int, int], Dict[str, Any]] = (
            hidden_walls if hidden_walls is not None else {}
        )
        self.height = len(self.data)
        self.width = max(len(row) for row in self.data)
        self.pixel_width = self.width * TILE_SIZE
        self.pixel_height = self.height * TILE_SIZE

        # Build a surface for the whole map and collect blocked rects.
        self._surface = pygame.Surface(
            (self.pixel_width, self.pixel_height)
        )
        self.blocked_rects: List[pygame.Rect] = []
        self._build()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build(self) -> None:
        """Pre-render every tile onto the map surface."""
        for row, row_data in enumerate(self.data):
            for col, tile_id in enumerate(row_data):
                color = TILE_COLORS.get(tile_id, TILE_COLORS[0])
                rect = pygame.Rect(
                    col * TILE_SIZE,
                    row * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(self._surface, color, rect)
                # Draw a subtle grid line
                pygame.draw.rect(self._surface, TILE_GRID_COLOR, rect, 1)
                if tile_id in (TILE_WALL, TILE_WATER):
                    self.blocked_rects.append(rect.copy())

    # ── Public API ────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Blit the pre-rendered map onto *surface* with the camera offset."""
        surface.blit(self._surface, camera_offset)

    def tile_at(self, col: int, row: int) -> int:
        """Return the tile ID at grid position (col, row), or -1 if out of bounds."""
        if 0 <= row < self.height and 0 <= col < len(self.data[row]):
            return self.data[row][col]
        return -1

    def pixel_to_tile(self, px: float, py: float) -> Tuple[int, int]:
        """Convert a native-pixel position to a tile grid coordinate."""
        return int(px // TILE_SIZE), int(py // TILE_SIZE)

