"""
src/entities/npc.py - NPC entity (Phase 4).
"""

from __future__ import annotations

from typing import Dict, Any

import pygame

from settings import TILE_SIZE, LIGHT_GRAY, BLACK


class NPC(pygame.sprite.Sprite):
    """A non-player character with a dialog reference and sprite.

    Fully implemented in Phase 4.
    """

    def __init__(self, data: Dict[str, Any], col: int, row: int) -> None:
        super().__init__()
        self.name: str = data.get("name", "NPC")
        self.dialog_id: str = data.get("dialog_id", "")
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(LIGHT_GRAY)
        self.rect = self.image.get_rect(
            topleft=(col * TILE_SIZE, row * TILE_SIZE)
        )

    def interaction_rect(self) -> pygame.Rect:
        """Return a slightly enlarged rect used to detect player proximity."""
        return self.rect.inflate(4, 4)
