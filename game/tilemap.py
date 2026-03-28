"""TileMap class for loading and managing tile-based maps."""

import csv
import os
from typing import List, Optional

import pygame

from game.settings import TILE_SIZE, TILE_EMPTY
from game.tile import Tile


class TileMap:
    """Loads a CSV map file and manages a grid of Tile objects.

    Args:
        filename: Path to the CSV map file.
    """

    def __init__(self, filename: str) -> None:
        self.tiles: pygame.sprite.Group = pygame.sprite.Group()
        self.solid_tiles: pygame.sprite.Group = pygame.sprite.Group()
        self.map_data: List[List[int]] = []
        self.width = 0   # map width in pixels
        self.height = 0  # map height in pixels

        self._load(filename)

    def _load(self, filename: str) -> None:
        """Parse the CSV file and instantiate Tile objects."""
        with open(filename, newline="") as f:
            reader = csv.reader(f)
            for row_index, row in enumerate(reader):
                self.map_data.append([int(cell) for cell in row])
                for col_index, tile_id in enumerate(row):
                    tile_id_int = int(tile_id)
                    if tile_id_int == TILE_EMPTY:
                        continue
                    tile = Tile(tile_id_int, col_index, row_index)
                    self.tiles.add(tile)
                    if not tile.walkable:
                        self.solid_tiles.add(tile)

        rows = len(self.map_data)
        cols = max(len(r) for r in self.map_data) if rows > 0 else 0
        self.width = cols * TILE_SIZE
        self.height = rows * TILE_SIZE

    def draw(self, surface: pygame.Surface, camera_offset: pygame.math.Vector2) -> None:
        """Draw all tiles to the surface, offset by the camera.

        Args:
            surface: The pygame surface to draw onto.
            camera_offset: The (x, y) offset applied by the camera.
        """
        for tile in self.tiles:
            draw_rect = tile.rect.move(-camera_offset.x, -camera_offset.y)
            surface.blit(tile.image, draw_rect)
