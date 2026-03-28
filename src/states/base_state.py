"""
src/states/base_state.py - Abstract base class for all game states.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.game import Game


class BaseState(abc.ABC):
    """All game states inherit from this class.

    The Game class calls ``handle_input``, ``update``, and ``draw`` once per
    frame for the currently active state.  ``enter`` and ``exit`` are called
    when the state is pushed onto / popped off the state stack.
    """

    def __init__(self, game: "Game") -> None:
        self.game = game

    def enter(self) -> None:
        """Called when the state becomes active."""

    def exit(self) -> None:
        """Called when the state is removed or covered by another state."""

    @abc.abstractmethod
    def handle_input(self, event: pygame.event.Event) -> None:
        """Process a single SDL event."""

    @abc.abstractmethod
    def update(self, dt: float) -> None:
        """Advance logic by *dt* seconds."""

    @abc.abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Render to the native-resolution *surface*."""
