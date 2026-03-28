"""
src/systems/battle_engine.py - Turn-based battle engine (Phase 2).

This is the core combat system.  Phase 2 wires it into the battle state.
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

    Returns at least 1.
    """
    base = (attacker.stats["str"] * attack_power / 2) - (
        target.stats["def"] * armor_defense / 4
    )
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
    base = (caster.stats["mag"] * spell_power) - (
        target.stats["mdf"] * resist / 4
    )
    base = max(1.0, base)
    variance = 1.0 + random.uniform(-DAMAGE_VARIANCE, DAMAGE_VARIANCE)
    dmg = base * variance

    if element and hasattr(target, "weaknesses") and element in target.weaknesses:
        dmg *= 2.0
    if element and hasattr(target, "resistances") and element in target.resistances:
        dmg *= 0.5

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
    avg_party_spd = sum(c.stats["spd"] for c in party) / max(1, len(party))
    avg_enemy_spd = sum(e.stats["spd"] for e in enemies) / max(1, len(enemies))
    ratio = avg_party_spd / max(1, avg_enemy_spd)
    return min(0.95, max(0.05, ratio * 0.5))


def turn_order(combatants: List[Any]) -> List[Any]:
    """Return combatants sorted by SPD descending (faster acts first)."""
    return sorted(combatants, key=lambda c: c.stats["spd"], reverse=True)
