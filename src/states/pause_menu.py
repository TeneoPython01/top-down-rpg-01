"""
src/states/pause_menu.py - Pause/inventory menu (Phase 3).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT, WHITE, YELLOW, DARK_GRAY, LIGHT_GRAY
from src.states.base_state import BaseState
from src.ui.menu import Menu

if TYPE_CHECKING:
    from src.game import Game


_TABS = ["Items", "Equipment", "Magic", "Stats"]


class PauseMenuState(BaseState):
    """Out-of-battle pause menu with tabs: Items, Equipment, Magic, Stats."""

    def __init__(self, game: "Game", player: "Any") -> None:
        super().__init__(game)
        self.player = player
        self._tab_menu = Menu(_TABS, x=8, y=20, item_height=14)

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.pop_state()
        self._tab_menu.handle_input(event)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        # Semi-transparent overlay
        overlay = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 30, 200))
        surface.blit(overlay, (0, 0))

        # Box
        box = pygame.Rect(4, 4, NATIVE_WIDTH - 8, NATIVE_HEIGHT - 8)
        pygame.draw.rect(surface, DARK_GRAY, box)
        pygame.draw.rect(surface, LIGHT_GRAY, box, 2)

        font = pygame.font.SysFont("monospace", 8, bold=True)
        surface.blit(
            font.render("MENU", True, YELLOW),
            (NATIVE_WIDTH // 2 - 16, 8),
        )

        self._tab_menu.draw(surface)

        font_sm = pygame.font.SysFont("monospace", 7)
        hint = font_sm.render("ESC: close", True, (150, 150, 150))
        surface.blit(hint, (NATIVE_WIDTH - hint.get_width() - 8, NATIVE_HEIGHT - 14))
