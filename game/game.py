<<<<<<< HEAD
<<<<<<< HEAD
"""Main Game class: initializes pygame, owns the game loop."""

import sys
import os

import pygame

from game.settings import (
    TITLE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    BLACK,
    WHITE,
    TILE_SIZE,
)
=======
import os
import sys
import pygame
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, BLACK
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
=======
"""
game/game.py - Main Game class containing the game loop.
"""

import os
import pygame
from game.settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TITLE,
    BLACK,
)
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
from game.tilemap import TileMap
from game.player import Player
from game.camera import Camera

<<<<<<< HEAD
<<<<<<< HEAD

class Game:
    """Manages the game window, loop, and all major subsystems.

    Create one instance and call :meth:`run` to start the game.
    """

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Locate the map file relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        map_path = os.path.join(base_dir, "data", "maps", "map01.csv")

        self.tilemap = TileMap(map_path)
        self.camera = Camera(self.tilemap.width, self.tilemap.height)

        # Spawn player at tile (2, 2)
        self.player = Player(2 * TILE_SIZE, 2 * TILE_SIZE)
        self.all_sprites = pygame.sprite.Group(self.player)

        # HUD font
        self.font = pygame.font.SysFont("monospace", 14)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start and run the main game loop until the player quits."""
=======
MAPS_DIR = os.path.join(os.path.dirname(__file__), "maps")


class Game:
    """Main game class: initialises Pygame, owns the game loop."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self._load_map("map_01.txt")

    def _load_map(self, filename):
        path = os.path.join(MAPS_DIR, filename)
        self.tilemap = TileMap(path)
        self.camera = Camera(self.tilemap.pixel_width, self.tilemap.pixel_height)
        self.player = Player(2, 2)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

    def run(self):
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
        while self.running:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()
<<<<<<< HEAD

    # ------------------------------------------------------------------
    # Per-frame steps
    # ------------------------------------------------------------------

    def _handle_events(self) -> None:
        """Process pygame events (quit, keyboard shortcuts)."""
=======
MAP_PATH = os.path.join(os.path.dirname(__file__), "maps", "map_01.txt")


class Game:
    """Manages initialization, the game loop, and clean shutdown."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.tilemap = TileMap(MAP_PATH)
        spawn_x, spawn_y = self.tilemap.player_spawn
        self.player = Player(spawn_x, spawn_y)
        self.camera = Camera()

    def run(self) -> None:
        """Start and run the main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # delta time in seconds
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

<<<<<<< HEAD
    def _update(self) -> None:
        """Update all game objects for the current frame."""
        self.player.update(self.tilemap.solid_tiles)
        self.camera.update(self.player)

    def _draw(self) -> None:
        """Render everything to the screen."""
        self.screen.fill(BLACK)

        # Draw tiles
        self.tilemap.draw(self.screen, self.camera.offset)

        # Draw player
        self.screen.blit(
            self.player.image,
            self.camera.apply(self.player.rect),
        )

        # HUD: coordinates
        hud = self.font.render(
            f"X:{self.player.rect.x}  Y:{self.player.rect.y}", True, WHITE
        )
        self.screen.blit(hud, (8, 8))

=======
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def _update(self):
        self.player.update(self.tilemap.wall_tiles)
        self.camera.update(self.player.rect)

    def _draw(self):
        self.screen.fill(BLACK)
        self.tilemap.draw(self.screen, self.camera)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite.rect))
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
=======
    def _update(self, dt: float) -> None:
        self.player.update(dt, self.tilemap.wall_tiles)
        self.camera.update(self.player)

    def _draw(self) -> None:
        self.screen.fill(BLACK)
        self.tilemap.draw(self.screen, self.camera.offset)
        # Draw player with camera offset applied
        self.screen.blit(
            self.player.image,
            self.player.rect.move(self.camera.offset),
        )
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
        pygame.display.flip()
