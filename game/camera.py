<<<<<<< HEAD
"""Camera class that keeps the player centered on screen."""

=======
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
import pygame
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
<<<<<<< HEAD
    """Tracks a target sprite and provides an offset for rendering.

    The camera clamps to the map boundaries so the background is never
    shown outside the map edges.

    Args:
        map_width: Total map width in pixels.
        map_height: Total map height in pixels.
    """

    def __init__(self, map_width: int, map_height: int) -> None:
=======
    """Tracks the player and offsets all draw calls accordingly."""

    def __init__(self, map_width, map_height):
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
        self.offset = pygame.math.Vector2(0, 0)
        self.map_width = map_width
        self.map_height = map_height

<<<<<<< HEAD
    def update(self, target: pygame.sprite.Sprite) -> None:
        """Recompute the camera offset to center on *target*.

        Args:
            target: The sprite (typically the player) to follow.
        """
        # Center the target in the viewport
        x = target.rect.centerx - SCREEN_WIDTH // 2
        y = target.rect.centery - SCREEN_HEIGHT // 2

        # Clamp so we never scroll past map edges
        x = max(0, min(x, self.map_width - SCREEN_WIDTH))
        y = max(0, min(y, self.map_height - SCREEN_HEIGHT))

        self.offset.x = x
        self.offset.y = y

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Return a new rect shifted by the camera offset.

        Args:
            rect: The world-space rectangle to transform.

        Returns:
            A new pygame.Rect in screen space.
        """
        return rect.move(-self.offset.x, -self.offset.y)
=======
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
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
