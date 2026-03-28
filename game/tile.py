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
