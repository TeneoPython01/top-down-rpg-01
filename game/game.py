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
from game.tilemap import TileMap
from game.player import Player
from game.camera import Camera

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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

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
        pygame.display.flip()
