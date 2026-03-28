import pygame
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    """Tracks the player and offsets all draw calls accordingly."""

    def __init__(self, map_width, map_height):
        self.offset = pygame.math.Vector2(0, 0)
        self.map_width = map_width
        self.map_height = map_height

    def apply(self, rect):
        """Return a new rect shifted by the camera offset."""
        return rect.move(-self.offset.x, -self.offset.y)

    def update(self, target_rect):
        """Centre the camera on *target_rect*, clamped to map bounds."""
        x = target_rect.centerx - SCREEN_WIDTH // 2
        y = target_rect.centery - SCREEN_HEIGHT // 2
        x = max(0, min(x, self.map_width - SCREEN_WIDTH))
        y = max(0, min(y, self.map_height - SCREEN_HEIGHT))
        self.offset.x = x
        self.offset.y = y
