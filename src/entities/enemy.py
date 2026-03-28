"""
src/entities/enemy.py - Enemy entity (Phase 2).
"""

from __future__ import annotations

from typing import Any, Dict

import pygame

from settings import TILE_SIZE, RED, WHITE


class Enemy(pygame.sprite.Sprite):
    """A single enemy loaded from enemies.json data.

    Attributes filled in Phase 2.
    """

    def __init__(self, data: Dict[str, Any], x: int, y: int) -> None:
        super().__init__()
        self.name: str = data.get("name", "Unknown")
        self.hp: int = data.get("hp", 10)
        self.max_hp: int = self.hp
        self.mp: int = data.get("mp", 0)
        self.max_mp: int = self.mp
        self.stats: Dict[str, int] = {
            "str": data.get("str", 5),
            "def": data.get("def", 3),
            "mag": data.get("mag", 0),
            "mdf": data.get("mdf", 2),
            "spd": data.get("spd", 5),
            "lck": data.get("lck", 5),
        }
        self.weaknesses: list = data.get("weaknesses", [])
        self.resistances: list = data.get("resistances", [])
        self.xp_reward: int = data.get("xp", 10)
        self.gold_reward: int = data.get("gold", 5)
        self.loot_table: list = data.get("loot", [])

        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(RED)
        self.rect = self.image.get_rect(topleft=(x, y))

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """Apply damage and return actual HP lost."""
        actual = min(amount, self.hp)
        self.hp -= actual
        return actual
