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

    def enter(self) -> None:
        pass

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from src.states.pause_menu import PauseMenuState
                self.game.push_state(PauseMenuState(self.game, self.player))

    def update(self, dt: float) -> None:
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

    # ── Private helpers ───────────────────────────────────────────────────────

    def _draw_hud(self, surface: pygame.Surface) -> None:
        """Draw a minimal heads-up display (area name, HP/MP, controls hint)."""
        font = pygame.font.SysFont("monospace", 7)
        area_surf = font.render("Ashenvale", True, WHITE)
        surface.blit(area_surf, (4, 4))

        # Player HP/MP
        p = self.player
        hud_text = f"HP:{p.hp}/{p.max_hp}  MP:{p.mp}/{p.max_mp}  G:{p.gold}"
        hud_surf = font.render(hud_text, True, (180, 255, 180))
        surface.blit(hud_surf, (4, 14))

        hint_surf = font.render("WASD/Arrows: move  ESC: menu", True, (160, 160, 160))
        surface.blit(hint_surf, (4, NATIVE_HEIGHT - 10))
