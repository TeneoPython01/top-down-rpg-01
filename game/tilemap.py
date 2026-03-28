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

        self._load(filename)

    def _load(self, filename: str) -> None:
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
