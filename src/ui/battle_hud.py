"""
src/ui/battle_hud.py - Battle UI: HP/MP bars, command menu, enemy list (Phase 2).
"""

from __future__ import annotations

from typing import List, Any

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    WHITE,
    YELLOW,
    RED,
    CYAN,
    BLACK,
    DARK_GRAY,
    LIGHT_GRAY,
)


class BattleHUD:
    """Renders the battle UI at the bottom of the screen."""

    def __init__(self) -> None:
        self._font = None

    def _get_font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", 8)
        return self._font

    def draw(
        self,
        surface: pygame.Surface,
        player: Any,
        enemies: List[Any],
        command_menu: Any,
        message: str = "",
    ) -> None:
        font = self._get_font()
        font_sm = pygame.font.SysFont("monospace", 7)

        # ── Bottom panel ──────────────────────────────────────────────────────
        panel_rect = pygame.Rect(0, NATIVE_HEIGHT - 60, NATIVE_WIDTH, 60)
        pygame.draw.rect(surface, DARK_GRAY, panel_rect)
        pygame.draw.rect(surface, LIGHT_GRAY, panel_rect, 1)

        # Player stats
        hp_pct = max(0, player.hp / max(1, player.max_hp))
        mp_pct = max(0, player.mp / max(1, player.max_mp))
        py = panel_rect.y + 6
        surface.blit(font.render(player.name, True, WHITE), (8, py))
        pygame.draw.rect(surface, BLACK, (8, py + 10, 60, 5))
        pygame.draw.rect(surface, RED, (8, py + 10, int(60 * hp_pct), 5))
        surface.blit(
            font_sm.render(f"HP {player.hp}/{player.max_hp}", True, WHITE),
            (72, py + 9),
        )
        pygame.draw.rect(surface, BLACK, (8, py + 17, 60, 5))
        pygame.draw.rect(surface, CYAN, (8, py + 17, int(60 * mp_pct), 5))
        surface.blit(
            font_sm.render(f"MP {player.mp}/{player.max_mp}", True, WHITE),
            (72, py + 16),
        )

        # Command menu
        if command_menu is not None:
            command_menu.draw(surface)

        # Message
        if message:
            msg_surf = font.render(message, True, YELLOW)
            surface.blit(msg_surf, (NATIVE_WIDTH // 2 - msg_surf.get_width() // 2, py))

        # Enemy list (top area — enemies appear as colored rectangles for now)
        ex = 16
        for enemy in enemies:
            if enemy.is_alive():
                pygame.draw.rect(surface, RED, (ex, 20, 28, 28))
                label = font_sm.render(enemy.name[:6], True, WHITE)
                surface.blit(label, (ex, 50))
                ex += 36
