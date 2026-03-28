"""
src/states/overworld.py - Overworld exploration state.

Handles tile-map rendering, player movement, camera, and collision.
Random encounters will be wired in during Phase 2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    TILE_SIZE,
    WHITE,
    BLACK,
    DARK_BLUE,
    YELLOW,
)
from src.states.base_state import BaseState
from src.entities.player import Player
from src.systems.camera import Camera
from src.utils.tilemap import TileMap

if TYPE_CHECKING:
    from src.game import Game


class OverworldState(BaseState):
    """Overworld exploration — tile map, player, camera, collision.

    Phase 1 uses the hardcoded default map.  Phase 4 will upgrade this to
    load TMX files via pytmx/pyscroll.
    """

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self.tilemap = TileMap()
        spawn_col, spawn_row = self.tilemap.spawn
        self.player = Player(spawn_col, spawn_row)
        self.camera = Camera(
            self.tilemap.pixel_width,
            self.tilemap.pixel_height,
        )
        self._paused = False

    def enter(self) -> None:
        self._paused = False

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Phase 1: toggle a simple pause overlay
                self._paused = not self._paused

    def update(self, dt: float) -> None:
        if self._paused:
            return
        self.player.update(dt, self.tilemap.blocked_rects)
        self.camera.update(self.player)

    def draw(self, surface: pygame.Surface) -> None:
        # Draw the tile map
        self.tilemap.draw(surface, self.camera.offset)

        # Draw the player
        surface.blit(
            self.player.image,
            self.player.rect.move(self.camera.offset),
        )

        # ── Minimal HUD ───────────────────────────────────────────────────────
        self._draw_hud(surface)

        # ── Pause overlay ─────────────────────────────────────────────────────
        if self._paused:
            self._draw_pause(surface)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _draw_hud(self, surface: pygame.Surface) -> None:
        """Draw a minimal heads-up display (area name, basic controls hint)."""
        font = pygame.font.SysFont("monospace", 7)
        area_surf = font.render("Ashenvale", True, WHITE)
        surface.blit(area_surf, (4, 4))

        hint_surf = font.render("WASD/Arrows: move  ESC: pause", True, (160, 160, 160))
        surface.blit(hint_surf, (4, NATIVE_HEIGHT - 10))

    def _draw_pause(self, surface: pygame.Surface) -> None:
        """Draw a semi-transparent pause overlay."""
        overlay = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        font = pygame.font.SysFont("monospace", 14, bold=True)
        pause_surf = font.render("PAUSED", True, YELLOW)
        surface.blit(
            pause_surf,
            pause_surf.get_rect(center=(NATIVE_WIDTH // 2, NATIVE_HEIGHT // 2)),
        )
        font_sm = pygame.font.SysFont("monospace", 8)
        hint_surf = font_sm.render("Press ESC to resume", True, WHITE)
        surface.blit(
            hint_surf,
            hint_surf.get_rect(
                centerx=NATIVE_WIDTH // 2,
                top=NATIVE_HEIGHT // 2 + 14,
            ),
        )
