"""
src/utils/tilemap.py - Simple 2-D array tilemap for Phase 1.

Phase 4 will upgrade this to a pytmx/pyscroll TMX-based loader.
Each cell holds a tile-ID integer (see settings.TILE_* constants).
"""

from __future__ import annotations

from typing import List, Tuple

import pygame

from settings import TILE_SIZE, TILE_COLORS, TILE_WALL, TILE_WATER, TILE_GRID_COLOR


# Default test map (Ashenvale area). Tile IDs:
#   0 = grass, 1 = wall, 2 = water, 3 = path
DEFAULT_MAP: List[List[int]] = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 3, 0, 3, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 3, 0, 3, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 3, 3, 3, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 3, 3, 0, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# Player spawn tile (col, row)
DEFAULT_SPAWN: Tuple[int, int] = (4, 9)


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
    blocked:
        pygame.sprite.Group of Rect-like objects for impassable tiles.
    """

    def __init__(
        self,
        data: List[List[int]] | None = None,
        spawn: Tuple[int, int] | None = None,
    ) -> None:
        self.data: List[List[int]] = data if data is not None else DEFAULT_MAP
        self.spawn: Tuple[int, int] = spawn if spawn is not None else DEFAULT_SPAWN
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
