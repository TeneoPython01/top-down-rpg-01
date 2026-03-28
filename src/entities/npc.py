"""
src/entities/npc.py - NPC entity (Phase 4).
"""

from __future__ import annotations

from typing import Dict, Any

import pygame

from settings import TILE_SIZE, LIGHT_GRAY, BLACK, WHITE


class NPC(pygame.sprite.Sprite):
    """A non-player character with a dialog reference and sprite.

    Parameters
    ----------
    data:
        Dict with keys: name, dialog_id, and optional color (RGB tuple).
    col, row:
        Tile-grid position of the NPC.
    """

    def __init__(self, data: Dict[str, Any], col: int, row: int) -> None:
        super().__init__()
        self.name: str = data.get("name", "NPC")
        self.dialog_id: str = data.get("dialog_id", "")
        color = data.get("color", LIGHT_GRAY)

        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)
        # Simple face: two dark eye dots
        pygame.draw.rect(self.image, BLACK, (4, 5, 2, 2))
        pygame.draw.rect(self.image, BLACK, (10, 5, 2, 2))
        # White highlight on top half to suggest a head shape
        pygame.draw.rect(self.image, WHITE, (5, 1, 6, 3))

        self.rect = self.image.get_rect(
            topleft=(col * TILE_SIZE, row * TILE_SIZE)
        )

    def interaction_rect(self) -> pygame.Rect:
        """Return a slightly enlarged rect used to detect player proximity."""
        return self.rect.inflate(4, 4)
