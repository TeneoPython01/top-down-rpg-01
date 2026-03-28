"""
src/states/overworld.py - Overworld exploration state.

Handles tile-map rendering, player movement, camera, collision, NPC
interaction, and scene dialog triggers.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, List

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    TILE_SIZE,
    WHITE,
    BLACK,
    DARK_BLUE,
    YELLOW,
    DATA_DIR,
)
from src.states.base_state import BaseState
from src.entities.player import Player
from src.entities.npc import NPC
from src.systems.camera import Camera
from src.utils.tilemap import TileMap

if TYPE_CHECKING:
    from src.game import Game

# ── NPC definitions for the Ashenvale overworld map ───────────────────────────
# Each entry: dialog_id (key in dialog.json), display name, tile col, tile row.
_ASHENVALE_NPCS = [
    {"dialog_id": "village_elder_before", "name": "Village Elder", "col": 10, "row": 4},
    {"dialog_id": "farmer_ashenvale",     "name": "Farmer",        "col": 8,  "row": 14},
    {"dialog_id": "healer_npc",           "name": "Healer",        "col": 20, "row": 9},
]

# Intro scene shown once when the player first enters the overworld.
_INTRO_LINES = [
    "Ashenvale — a quiet village on the edge of the Verdant Plains.",
    "100 years after the pandemic, nature has reclaimed the land.",
    "Strange beast attacks have been increasing near the village.",
    "The White Knight has returned to investigate...",
]


class OverworldState(BaseState):
    """Overworld exploration — tile map, player, camera, collision, NPCs.

    Phase 1 uses the hardcoded default map.  Phase 4 will upgrade this to
    load TMX files via pytmx/pyscroll.
    """

    # Proximity threshold (native pixels) within which Z triggers NPC dialog.
    _INTERACT_RANGE = 20

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
        self._intro_shown = False

        # Load dialog data
        dialog_path = os.path.join(DATA_DIR, "dialog.json")
        with open(dialog_path, "r", encoding="utf-8") as fh:
            self._dialog_data: dict = json.load(fh)

        # Build NPC list
        self._npcs: List[NPC] = []
        for idx, spec in enumerate(_ASHENVALE_NPCS):
            npc = NPC(spec, col=spec["col"], row=spec["row"], color_index=idx)
            self._npcs.append(npc)

    def enter(self) -> None:
        self._paused = False
        # Trigger the intro scene the first time we enter the overworld.
        if not self._intro_shown:
            self._intro_shown = True
            self._push_scene_dialog(_INTRO_LINES, speaker="")

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._paused = not self._paused
            elif event.key in (pygame.K_z, pygame.K_RETURN):
                self._try_interact()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _try_interact(self) -> None:
        """Check for a nearby NPC and push a DialogState if found."""
        player_center = pygame.Vector2(self.player.rect.center)
        for npc in self._npcs:
            npc_center = pygame.Vector2(npc.rect.center)
            if player_center.distance_to(npc_center) <= self._INTERACT_RANGE:
                entry = self._dialog_data.get(npc.dialog_id)
                if entry:
                    lines = entry.get("lines", [])
                    self._push_npc_dialog(lines, speaker=npc.name)
                    return

    def _push_npc_dialog(self, lines: list[str], speaker: str) -> None:
        from src.states.dialog import DialogState
        self.game.push_state(DialogState(self.game, lines, speaker=speaker))

    def _push_scene_dialog(self, lines: list[str], speaker: str = "") -> None:
        from src.states.dialog import DialogState
        self.game.push_state(DialogState(self.game, lines, speaker=speaker))

    # ── Update / draw ─────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._paused:
            return
        self.player.update(dt, self.tilemap.blocked_rects)
        self.camera.update(self.player)

    def draw(self, surface: pygame.Surface) -> None:
        # Draw the tile map
        self.tilemap.draw(surface, self.camera.offset)

        # Draw NPCs (sorted by bottom-y for natural depth order)
        for npc in sorted(self._npcs, key=lambda n: n.rect.bottom):
            npc.draw(surface, self.camera.offset)

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

    def _draw_hud(self, surface: pygame.Surface) -> None:
        """Draw a minimal heads-up display (area name, basic controls hint)."""
        font = pygame.font.SysFont("monospace", 7)
        area_surf = font.render("Ashenvale", True, WHITE)
        surface.blit(area_surf, (4, 4))

        hint_surf = font.render(
            "WASD/Arrows: move  Z: talk  ESC: pause", True, (160, 160, 160)
        )
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
