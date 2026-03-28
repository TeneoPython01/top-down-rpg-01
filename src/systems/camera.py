"""
src/systems/camera.py - Follow-camera that clamps to map boundaries.
"""

from __future__ import annotations

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT


class Camera:
    """Maintains a world-to-screen offset so the target stays centred.

    The offset is applied by the rendering code; sprites keep their world
    positions at all times.

    Parameters
    ----------
    map_pixel_width, map_pixel_height:
        Full size of the map in native pixels.  Used to clamp the offset so
        the camera never reveals empty space beyond the map edges.
    """

    def __init__(self, map_pixel_width: int, map_pixel_height: int) -> None:
        self.offset = pygame.Vector2(0, 0)
        self._map_w = map_pixel_width
        self._map_h = map_pixel_height

    def update(self, target: pygame.sprite.Sprite) -> None:
        """Recompute offset to centre *target* on screen, clamped to map bounds."""
        x = NATIVE_WIDTH // 2 - target.rect.centerx
        y = NATIVE_HEIGHT // 2 - target.rect.centery

        # Clamp so the camera never shows outside the map
        max_x = 0
        min_x = NATIVE_WIDTH - self._map_w
        max_y = 0
        min_y = NATIVE_HEIGHT - self._map_h

        self.offset.x = max(min_x, min(max_x, x))
        self.offset.y = max(min_y, min(max_y, y))
