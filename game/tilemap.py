<<<<<<< HEAD
<<<<<<< HEAD
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
=======
"""
game/tilemap.py - TileMap class for loading and rendering a map from a text file.
"""

import pygame
from game.tile import Tile
from game.settings import TILE_WALL, TILE_PLAYER_SPAWN


class TileMap:
    """Loads a map from a .txt file and manages tile sprites."""

    def __init__(self, filename: str) -> None:
        self.floor_tiles: pygame.sprite.Group = pygame.sprite.Group()
        self.wall_tiles: pygame.sprite.Group = pygame.sprite.Group()
        self.all_tiles: pygame.sprite.Group = pygame.sprite.Group()
        self.player_spawn: tuple[int, int] = (1, 1)
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df

        self._load(filename)

    def _load(self, filename: str) -> None:
<<<<<<< HEAD
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
=======
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
        with open(filename, encoding="utf-8") as f:
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
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
=======
        """Parse the map file and create tile sprites."""
        with open(filename) as f:
            for row, line in enumerate(f):
                for col, char in enumerate(line.rstrip("\n")):
                    if char == TILE_WALL:
                        tile = Tile(col, row, "W")
                        self.wall_tiles.add(tile)
                        self.all_tiles.add(tile)
                    elif char == TILE_PLAYER_SPAWN:
                        self.player_spawn = (col, row)
                        tile = Tile(col, row, ".")
                        self.floor_tiles.add(tile)
                        self.all_tiles.add(tile)
                    else:
                        tile = Tile(col, row, ".")
                        self.floor_tiles.add(tile)
                        self.all_tiles.add(tile)

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Draw all tiles offset by the camera."""
        for tile in self.all_tiles:
            surface.blit(tile.image, tile.rect.move(camera_offset))
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
