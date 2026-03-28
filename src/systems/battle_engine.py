"""
src/systems/battle_engine.py - Turn-based battle engine (Phase 2 & 3).

This is the core combat system.  Phase 2 wires it into the battle state.
Phase 3 adds status effects and spell/item integration.
"""

from __future__ import annotations

import math
import random
from typing import List, Any, Dict

from settings import BASE_HIT_RATE, CRIT_CHANCE_DIVISOR, DAMAGE_VARIANCE, BLIND_HIT_PENALTY


def physical_damage(
    attacker: Any,
    target: Any,
    attack_power: int = 10,
    armor_defense: int = 0,
) -> int:
    """Physical damage formula: (STR * power / 2) - (DEF * armor / 4) ± 10%.

    Uses effective stats (with active buffs applied).
    Returns at least 1.
    """
    from src.systems.magic import effective_stat
    str_val = effective_stat(attacker, "str")
    def_val = effective_stat(target, "def")

    # Add weapon ATK bonus for the attacker (if player)
    weapon_atk = 0
    if hasattr(attacker, "inventory"):
        from src.systems.inventory import load_items
        weapon_id = attacker.inventory.equipped("weapon")
        if weapon_id:
            weapon_atk = load_items().get(weapon_id, {}).get("atk", 0)
    total_power = attack_power + weapon_atk

    # Add armor DEF bonus for the target (if player)
    armor_bonus = armor_defense
    if hasattr(target, "inventory"):
        from src.systems.inventory import load_items
        all_items = load_items()
        for slot in ("shield", "helmet", "armor"):
            eq_id = target.inventory.equipped(slot)
            if eq_id:
                armor_bonus += all_items.get(eq_id, {}).get("def", 0)

    base = (str_val * total_power / 2) - (def_val * armor_bonus / 4)
    base = max(1.0, base)
    variance = 1.0 + random.uniform(-DAMAGE_VARIANCE, DAMAGE_VARIANCE)
    return max(1, math.floor(base * variance))


def magical_damage(
    caster: Any,
    target: Any,
    spell_power: int = 10,
    resist: int = 0,
    element: str | None = None,
) -> int:
    """Magical damage formula: (MAG * power) - (MDF * resist / 4) ± 10%.

    Applies elemental weakness (2×) or resistance (0.5×).
    Returns at least 1.
    """
    from src.systems.magic import effective_stat
    mag_val = effective_stat(caster, "mag")
    mdf_val = effective_stat(target, "mdf")

    base = (mag_val * spell_power) - (mdf_val * resist / 4)
    base = max(1.0, base)
    variance = 1.0 + random.uniform(-DAMAGE_VARIANCE, DAMAGE_VARIANCE)
    dmg = base * variance

    if element and hasattr(target, "weaknesses") and element in target.weaknesses:
        dmg *= 2.0
    if element and hasattr(target, "resistances") and element in target.resistances:
        dmg *= 0.5

    # Exo Armor elemental resistance
    if element and hasattr(target, "inventory"):
        from src.systems.inventory import load_items
        armor_id = target.inventory.equipped("armor")
        if armor_id:
            resist_pct = load_items().get(armor_id, {}).get("elemental_resist", 0)
            dmg *= 1.0 - resist_pct / 100.0

    return max(1, math.floor(dmg))


def check_hit(attacker: Any, target: Any) -> bool:
    """Return True if the attack connects."""
    blind_penalty = BLIND_HIT_PENALTY if getattr(attacker, "status", {}).get("blind") else 0.0
    hit_rate = BASE_HIT_RATE - blind_penalty
    return random.random() < hit_rate


def check_crit(attacker: Any) -> bool:
    """Return True if the attack is a critical hit."""
    lck = attacker.stats.get("lck", 5)
    return random.random() < (lck / CRIT_CHANCE_DIVISOR)


def flee_chance(party: List[Any], enemies: List[Any]) -> float:
    """Probability [0, 1] that the party can flee successfully."""
    from src.systems.magic import effective_stat
    avg_party_spd = sum(effective_stat(c, "spd") for c in party) / max(1, len(party))
    avg_enemy_spd = sum(effective_stat(e, "spd") for e in enemies) / max(1, len(enemies))
    ratio = avg_party_spd / max(1, avg_enemy_spd)
    return min(0.95, max(0.05, ratio * 0.5))


def turn_order(combatants: List[Any]) -> List[Any]:
    """Return combatants sorted by effective SPD descending (faster acts first)."""
    from src.systems.magic import effective_stat
    return sorted(combatants, key=lambda c: effective_stat(c, "spd"), reverse=True)


def apply_battle_item(item_id: str, user: Any, target: Any) -> tuple[bool, str]:
    """Use a battle-type item (bomb fragment, arctic wind, etc.) on *target*.

    Returns (success, message).
    """
    from src.systems.inventory import load_items
    all_items = load_items()
    data = all_items.get(item_id)
    if data is None:
        return False, "Unknown item."
    if not user.inventory.has(item_id):
        return False, "No item."

    effect = data.get("effect", "")
    power = data.get("power", 0)

    elemental_effects = {
        "fire_damage": "fire",
        "ice_damage": "ice",
        "lightning_damage": "lightning",
    }

    if effect in elemental_effects:
        element = elemental_effects[effect]
        dmg = power
        variance = 1.0 + random.uniform(-DAMAGE_VARIANCE, DAMAGE_VARIANCE)
        dmg_int = max(1, math.floor(dmg * variance))
        if element in getattr(target, "weaknesses", []):
            dmg_int = math.floor(dmg_int * 2.0)
        elif element in getattr(target, "resistances", []):
            dmg_int = max(1, math.floor(dmg_int * 0.5))
        target.take_damage(dmg_int)
        user.inventory.remove(item_id)
        return True, f"{data['name']} deals {dmg_int} {element} damage to {target.name}!"

    if effect == "non_elemental_all":
        # Caller must handle multi-target; returns single-target message
        dmg_int = max(1, math.floor(power * (1.0 + random.uniform(-DAMAGE_VARIANCE, DAMAGE_VARIANCE))))
        target.take_damage(dmg_int)
        user.inventory.remove(item_id)
        return True, f"{data['name']} deals {dmg_int} damage to {target.name}!"

    if effect == "sleep_all":
        chance = power / 100.0
        if random.random() < chance:
            if not hasattr(target, "status"):
                target.status = {}
            target.status["sleep"] = 3
            user.inventory.remove(item_id)
            return True, f"{data['name']}: {target.name} fell asleep!"
        user.inventory.remove(item_id)
        return True, f"{data['name']}: {target.name} resisted sleep."

    if effect == "guaranteed_flee":
        user.inventory.remove(item_id)
        return True, "smoke_bomb"  # sentinel for caller to handle flee

    return False, f"{data['name']} cannot be used here."
