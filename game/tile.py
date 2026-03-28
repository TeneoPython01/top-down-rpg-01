"""
game/tile.py - Tile class representing a single map tile.
"""

import pygame
from game.settings import TILE_SIZE, DARK_GRAY, LIGHT_GRAY


class Tile(pygame.sprite.Sprite):
    """A single tile in the map (wall or floor)."""

    def __init__(self, x: int, y: int, tile_type: str) -> None:
        super().__init__()
        self.tile_type = tile_type
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))

        if tile_type == "W":
            self.image.fill(DARK_GRAY)
        else:
            self.image.fill(LIGHT_GRAY)

        self.rect = self.image.get_rect(topleft=(x * TILE_SIZE, y * TILE_SIZE))
