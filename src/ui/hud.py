"""
src/ui/hud.py - Overworld HUD: HP/MP bars, area name (Phase 5).
"""

from __future__ import annotations

import pygame

from settings import NATIVE_WIDTH, NATIVE_HEIGHT, WHITE, RED, CYAN, DARK_GRAY


class HUD:
    """Draws HP/MP bars and the current area name onto the overworld surface."""

    def __init__(self) -> None:
        self._font = None  # lazily initialised after pygame.init()

    def _get_font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", 7)
        return self._font

    def draw(
        self,
        surface: pygame.Surface,
        player: "Any",
        area_name: str = "",
    ) -> None:
        font = self._get_font()

        # Area name (top-left)
        if area_name:
            surf = font.render(area_name, True, WHITE)
            surface.blit(surf, (4, 4))

        # HP/MP bars (bottom-left corner)
        bar_x = 4
        bar_y = NATIVE_HEIGHT - 20
        bar_w = 50
        bar_h = 4

        # HP bar
        hp_pct = max(0.0, player.hp / max(1, player.max_hp))
        pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, RED, (bar_x, bar_y, int(bar_w * hp_pct), bar_h))
        hp_label = font.render(f"HP {player.hp}/{player.max_hp}", True, WHITE)
        surface.blit(hp_label, (bar_x + bar_w + 4, bar_y - 1))

        # MP bar
        mp_pct = max(0.0, player.mp / max(1, player.max_mp))
        pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y + 6, bar_w, bar_h))
        pygame.draw.rect(surface, CYAN, (bar_x, bar_y + 6, int(bar_w * mp_pct), bar_h))
        mp_label = font.render(f"MP {player.mp}/{player.max_mp}", True, WHITE)
        surface.blit(mp_label, (bar_x + bar_w + 4, bar_y + 5))
