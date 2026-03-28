"""
src/states/shop.py - Buy/sell shop state (Phase 4).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Dict, Any

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT, WHITE, YELLOW, DARK_GRAY, LIGHT_GRAY
from src.states.base_state import BaseState
from src.ui.menu import Menu

if TYPE_CHECKING:
    from src.game import Game


class ShopState(BaseState):
    """Buy/sell interface."""

    def __init__(
        self,
        game: "Game",
        inventory: List[Dict[str, Any]],
        player_inventory: Any,
    ) -> None:
        super().__init__(game)
        self._items = inventory
        self._player_inv = player_inventory
        options = [f"{i['name']} - {i['price']}G" for i in inventory] + ["Exit"]
        self._menu = Menu(options, x=20, y=30)

    def handle_input(self, event: pygame.event.Event) -> None:
        result = self._menu.handle_input(event)
        if result == "Exit" or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        ):
            self.game.pop_state()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(DARK_GRAY)
        pygame.draw.rect(surface, LIGHT_GRAY, surface.get_rect(), 2)
        font = pygame.font.SysFont("monospace", 9, bold=True)
        surface.blit(font.render("SHOP", True, YELLOW), (NATIVE_WIDTH // 2 - 18, 8))
        self._menu.draw(surface)
