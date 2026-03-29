"""
tests/conftest.py - shared pytest fixtures and pygame initialisation.
"""

import os
import pytest

# Use a headless video/audio driver so the tests don't need a display.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(scope="session", autouse=True)
def pygame_init():
    """Initialise pygame once for the entire test session."""
    import pygame
    pygame.init()
    yield
    pygame.quit()
