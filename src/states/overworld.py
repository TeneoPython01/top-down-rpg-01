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
    TILE_TOWN,
    TOWN_ENTRY_COOLDOWN,
    WHITE,
    BLACK,
    DARK_BLUE,
    YELLOW,
)
from src.states.base_state import BaseState
from src.entities.player import Player
from src.systems.camera import Camera
from src.utils.tilemap import TileMap
from src.utils.town_maps import OVERWORLD_TOWN_ENTRANCES

if TYPE_CHECKING:
    from src.game import Game


class OverworldState(BaseState):
    """Overworld exploration — tile map, player, camera, collision.

    Phase 1 uses the hardcoded default map.  Phase 4 will upgrade this to
    load TMX files via pytmx/pyscroll.
    """

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self.tilemap = TileMap(town_entrances=OVERWORLD_TOWN_ENTRANCES)
        spawn_col, spawn_row = self.tilemap.spawn
        self.player = Player(spawn_col, spawn_row)
        self.camera = Camera(
            self.tilemap.pixel_width,
            self.tilemap.pixel_height,
        )
        self._paused = False
        self._town_cooldown = 0.0  # prevents re-entering a town immediately after exit

    def enter(self) -> None:
        self._paused = False
        # Brief cooldown so the player doesn't loop back into the town
        # the instant they return from it.
        self._town_cooldown = TOWN_ENTRY_COOLDOWN

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

        # ── Town entrance detection ───────────────────────────────────────────
        if self._town_cooldown > 0:
            self._town_cooldown = max(0.0, self._town_cooldown - dt)
        else:
            col, row = self.tilemap.pixel_to_tile(
                self.player.rect.centerx, self.player.rect.centery
            )
            if self.tilemap.tile_at(col, row) == TILE_TOWN:
                town_name = self.tilemap.town_entrances.get((col, row), "")
                if town_name:
                    from src.states.town import TownState  # avoid circular import
                    self.game.push_state(TownState(self.game, town_name))

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

        # Show town name hint when player is standing on an entrance tile
        if self._town_cooldown <= 0:
            col, row = self.tilemap.pixel_to_tile(
                self.player.rect.centerx, self.player.rect.centery
            )
            if self.tilemap.tile_at(col, row) == TILE_TOWN:
                town_name = self.tilemap.town_entrances.get((col, row), "")
                if town_name:
                    lbl = font.render(
                        f"Entering {town_name.capitalize()}...", True, YELLOW
                    )
                    surface.blit(
                        lbl, lbl.get_rect(centerx=NATIVE_WIDTH // 2, top=4)
                    )

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
