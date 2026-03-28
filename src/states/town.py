"""
src/states/town.py - Town exploration state (Phase 4).

Similar to OverworldState but without random encounters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT, WHITE
from src.states.base_state import BaseState

if TYPE_CHECKING:
    from src.game import Game


class TownState(BaseState):
    """Town exploration — no random encounters, NPC interaction, shops, inn."""

    def __init__(self, game: "Game", town_name: str = "Town") -> None:
        super().__init__(game)
        self.town_name = town_name

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.pop_state()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((30, 50, 30))
        font = pygame.font.SysFont("monospace", 10, bold=True)
        lbl = font.render(f"{self.town_name} (Phase 4)", True, WHITE)
        surface.blit(lbl, lbl.get_rect(center=(NATIVE_WIDTH // 2, NATIVE_HEIGHT // 2)))
