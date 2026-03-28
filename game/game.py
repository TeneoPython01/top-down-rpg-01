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
from game.tilemap import TileMap
from game.player import Player
from game.camera import Camera


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
        while self.running:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()

    # ------------------------------------------------------------------
    # Per-frame steps
    # ------------------------------------------------------------------

    def _handle_events(self) -> None:
        """Process pygame events (quit, keyboard shortcuts)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

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

        pygame.display.flip()
