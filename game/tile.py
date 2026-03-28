<<<<<<< HEAD
"""Tile class representing a single map tile."""

import pygame
from game.settings import TILE_SIZE, TILE_PROPERTIES, TILE_EMPTY, GRAY


class Tile(pygame.sprite.Sprite):
    """A single tile on the map.

    Args:
        tile_id: Integer tile identifier (see settings.TILE_PROPERTIES).
        x: Tile column index.
        y: Tile row index.
    """

    def __init__(self, tile_id: int, x: int, y: int) -> None:
        super().__init__()
        self.tile_id = tile_id
        color, self.walkable = TILE_PROPERTIES.get(tile_id, (GRAY, False))

        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)

        # Draw a subtle grid line
        pygame.draw.rect(self.image, (0, 0, 0), self.image.get_rect(), 1)

        self.rect = self.image.get_rect(topleft=(x * TILE_SIZE, y * TILE_SIZE))
=======
import pygame
from game.settings import TILE_SIZE, TILE_COLORS, DARK_GRAY


class Tile(pygame.sprite.Sprite):
    """A single tile on the map."""

    def __init__(self, tile_type, x, y):
        super().__init__()
        self.tile_type = tile_type
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        color = TILE_COLORS.get(tile_type, DARK_GRAY)
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x * TILE_SIZE, y * TILE_SIZE))

    @property
    def walkable(self):
        """Return True if the player can walk on this tile."""
        from game.settings import TILE_WALL
        return self.tile_type != TILE_WALL
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
