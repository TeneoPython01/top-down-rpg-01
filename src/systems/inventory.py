"""
src/systems/inventory.py - Item storage and equipment management (Phase 3).
"""

from __future__ import annotations

from typing import Dict, Any


STACK_LIMIT = 99


class Inventory:
    """Holds consumables and tracks equipped items.

    Attributes
    ----------
    items:
        Mapping item_id → count.
    equipment:
        Mapping slot → item_id (or None if empty).
    gold:
        Current gold amount.
    """

    SLOTS = ("weapon", "shield", "helmet", "armor", "accessory")

    def __init__(self) -> None:
        self.items: Dict[str, int] = {}
        self.equipment: Dict[str, str | None] = {slot: None for slot in self.SLOTS}
        self.gold: int = 0

    def add(self, item_id: str, count: int = 1) -> int:
        """Add *count* of *item_id*.  Returns actual amount added (capped at stack limit)."""
        current = self.items.get(item_id, 0)
        actual = min(count, STACK_LIMIT - current)
        if actual > 0:
            self.items[item_id] = current + actual
        return actual

    def remove(self, item_id: str, count: int = 1) -> bool:
        """Remove *count* of *item_id*.  Returns False if not enough stock."""
        if self.items.get(item_id, 0) < count:
            return False
        self.items[item_id] -= count
        if self.items[item_id] == 0:
            del self.items[item_id]
        return True

    def has(self, item_id: str, count: int = 1) -> bool:
        return self.items.get(item_id, 0) >= count

    def equip(self, slot: str, item_id: str | None) -> None:
        """Equip (or un-equip) an item in a slot."""
        if slot in self.equipment:
            self.equipment[slot] = item_id

    def equipped(self, slot: str) -> str | None:
        return self.equipment.get(slot)
