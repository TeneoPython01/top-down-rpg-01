"""
src/systems/inventory.py - Item storage and equipment management (Phase 3).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Tuple

from settings import DATA_DIR


STACK_LIMIT = 99

# Module-level cache so items.json is loaded only once
_ITEMS_CACHE: Dict[str, Any] | None = None


def load_items() -> Dict[str, Any]:
    """Load item definitions from data/items.json (cached after first call)."""
    global _ITEMS_CACHE
    if _ITEMS_CACHE is None:
        path = os.path.join(DATA_DIR, "items.json")
        with open(path) as f:
            _ITEMS_CACHE = {item["id"]: item for item in json.load(f)}
    return _ITEMS_CACHE


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

    # ── Item use ──────────────────────────────────────────────────────────────

    def use_item(self, item_id: str, target: Any) -> Tuple[bool, str]:
        """Use a consumable item on *target* (typically the player).

        Removes one instance from inventory on success.

        Returns
        -------
        (success, message):
            success – True if the item was used successfully.
            message – Human-readable result description.
        """
        if not self.has(item_id):
            return False, "No item."

        all_items = load_items()
        data = all_items.get(item_id)
        if data is None:
            return False, "Unknown item."

        effect = data.get("effect", "")
        power = data.get("power", 0)

        if effect == "heal_hp":
            healed = target.heal(power)
            self.remove(item_id)
            return True, f"{data['name']}: restored {healed} HP."

        if effect == "heal_mp":
            restored = target.restore_mp(power)
            self.remove(item_id)
            return True, f"{data['name']}: restored {restored} MP."

        if effect == "full_restore":
            hp_healed = target.heal(target.max_hp)
            mp_restored = target.restore_mp(target.max_mp)
            self.remove(item_id)
            return True, f"{data['name']}: fully restored HP+MP."

        if effect == "revive":
            if target.hp > 0:
                return False, f"{target.name} is not KO'd."
            revive_hp = max(1, int(target.max_hp * power / 100))
            target.hp = revive_hp
            self.remove(item_id)
            return True, f"{data['name']}: {target.name} revived with {revive_hp} HP."

        if effect == "cure_poison":
            target.status.pop("poison", None)
            self.remove(item_id)
            return True, f"{data['name']}: Poison cured."

        if effect == "cure_blind":
            target.status.pop("blind", None)
            self.remove(item_id)
            return True, f"{data['name']}: Blind cured."

        if effect == "cure_silence":
            target.status.pop("silence", None)
            self.remove(item_id)
            return True, f"{data['name']}: Silence cured."

        if effect == "tent":
            # Tent is usable only outside battle (caller should check).
            hp_restore = target.max_hp // 2
            mp_restore = target.max_mp // 2
            target.heal(hp_restore)
            target.restore_mp(mp_restore)
            self.remove(item_id)
            return True, f"{data['name']}: restored 50% HP/MP."

        return False, f"{data['name']} cannot be used here."

    # ── Equipment helpers ─────────────────────────────────────────────────────

    def equip_item(self, item_id: str, player: Any) -> Tuple[bool, str]:
        """Equip *item_id* from inventory onto *player*; auto-detect slot.

        Returns (success, message).
        """
        all_items = load_items()
        data = all_items.get(item_id)
        if data is None:
            return False, "Unknown item."

        slot = data.get("type")
        if slot not in self.SLOTS:
            return False, f"{data['name']} is not equippable."

        # Swap: put previous item back in bag (if any)
        prev = self.equipment.get(slot)
        if prev is not None:
            self.add(prev)

        self.remove(item_id)
        self.equip(slot, item_id)
        player.recalculate_stats()
        return True, f"Equipped {data['name']}."

    def unequip_slot(self, slot: str, player: Any) -> Tuple[bool, str]:
        """Remove equipped item from *slot* and return it to inventory.

        Returns (success, message).
        """
        item_id = self.equipment.get(slot)
        if item_id is None:
            return False, f"Nothing equipped in {slot}."
        self.add(item_id)
        self.equip(slot, None)
        player.recalculate_stats()
        all_items = load_items()
        name = all_items.get(item_id, {}).get("name", item_id)
        return True, f"Unequipped {name}."

    # ── Battle item helpers ────────────────────────────────────────────────────

    def battle_items(self) -> Dict[str, int]:
        """Return items usable in battle (consumables and battle-type)."""
        all_items = load_items()
        return {
            iid: qty
            for iid, qty in self.items.items()
            if all_items.get(iid, {}).get("type") in ("consumable", "battle")
        }

    def healing_items(self) -> Dict[str, int]:
        """Return consumable (non-battle) items."""
        all_items = load_items()
        return {
            iid: qty
            for iid, qty in self.items.items()
            if all_items.get(iid, {}).get("type") == "consumable"
        }
