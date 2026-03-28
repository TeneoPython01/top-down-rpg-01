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
