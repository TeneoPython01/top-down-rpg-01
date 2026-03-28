"""
game/camera.py - Camera class that keeps the player centered on screen.
"""

import pygame
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    """Computes a world-to-screen offset so the player stays centered."""

    def __init__(self) -> None:
        self.offset = pygame.Vector2(0, 0)

    def update(self, target: pygame.sprite.Sprite) -> None:
        """Recalculate the offset based on the target's position."""
        self.offset.x = SCREEN_WIDTH // 2 - target.rect.centerx
        self.offset.y = SCREEN_HEIGHT // 2 - target.rect.centery
