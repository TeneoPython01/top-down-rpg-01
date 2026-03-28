import os
import pygame
from game.tile import Tile
from game.settings import TILE_SIZE


class TileMap:
    """Manages a 2-D grid of Tile objects loaded from a text file."""

    def __init__(self, filename):
        self.tiles = pygame.sprite.Group()
        self.wall_tiles = pygame.sprite.Group()
        self.width = 0
        self.height = 0
        self._load(filename)

    def _load(self, filename):
        with open(filename) as f:
            rows = [line.rstrip("\n") for line in f.readlines()]
        self.height = len(rows)
        self.width = max(len(row) for row in rows) if rows else 0
        for y, row in enumerate(rows):
            for x, char in enumerate(row):
                tile = Tile(char, x, y)
                self.tiles.add(tile)
                if not tile.walkable:
                    self.wall_tiles.add(tile)

    @property
    def pixel_width(self):
        return self.width * TILE_SIZE

    @property
    def pixel_height(self):
        return self.height * TILE_SIZE

    def draw(self, surface, camera):
        for tile in self.tiles:
            surface.blit(tile.image, camera.apply(tile.rect))
