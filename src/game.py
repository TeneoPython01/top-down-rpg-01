"""
src/game.py - Game class: main loop and state manager.
"""

from __future__ import annotations

import sys
from typing import List

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SCALE,
    FPS,
    TITLE,
    BLACK,
)
from src.states.base_state import BaseState
from src.systems.inventory import Inventory


class Game:
    """Owns the window, clock, native surface, and state stack.

    The native surface is rendered at NATIVE_WIDTH × NATIVE_HEIGHT (256×224)
    and then scaled up 3× to the actual window size (768×672).
    """

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        # Native surface — all states render here, then we scale.
        self.screen = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self._state_stack: List[BaseState] = []

        # Shared player inventory / gold (persists across all states)
        self.inventory = Inventory()
        self.inventory.gold = 200  # starting gold

        # Kick off with the title screen (imported here to avoid circular deps)
        from src.states.title import TitleState
        self.push_state(TitleState(self))

    # ── State management ──────────────────────────────────────────────────────

    def push_state(self, state: BaseState) -> None:
        """Push a new state on top of the stack and enter it."""
        if self._state_stack:
            self._state_stack[-1].exit()
        self._state_stack.append(state)
        state.enter()

    def pop_state(self) -> None:
        """Remove the current state and resume the one below it."""
        if self._state_stack:
            self._state_stack[-1].exit()
            self._state_stack.pop()
        if self._state_stack:
            self._state_stack[-1].enter()
        else:
            self.running = False

    def change_state(self, state: BaseState) -> None:
        """Replace the current state (exit old, enter new)."""
        if self._state_stack:
            self._state_stack[-1].exit()
            self._state_stack[-1] = state
        else:
            self._state_stack.append(state)
        state.enter()

    @property
    def current_state(self) -> BaseState | None:
        return self._state_stack[-1] if self._state_stack else None

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start and run the game loop until ``self.running`` is False."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.current_state is not None:
                    self.current_state.handle_input(event)

            if self.current_state is not None:
                self.current_state.update(dt)

            self.screen.fill(BLACK)
            if self._state_stack:
                # Find the lowest state that must be drawn.  Overlay states
                # (e.g. dialog boxes) are transparent — we still need to show
                # whatever is beneath them.
                start = len(self._state_stack) - 1
                while start > 0 and self._state_stack[start].is_overlay:
                    start -= 1
                for state in self._state_stack[start:]:
                    state.draw(self.screen)

            # Scale native surface → window
            scaled = pygame.transform.scale(self.screen, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.window.blit(scaled, (0, 0))
            pygame.display.flip()

        pygame.quit()
        sys.exit()
