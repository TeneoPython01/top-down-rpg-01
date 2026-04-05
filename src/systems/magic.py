"""
src/systems/magic.py - Spell definitions and casting logic (Phase 3).
"""

from __future__ import annotations

import json
import math
import os
import random
from typing import Any, Dict, List, Tuple

from settings import DATA_DIR, DAMAGE_VARIANCE


def load_spells() -> Dict[str, Any]:
    """Load spell definitions from data/spells.json."""
    path = os.path.join(DATA_DIR, "spells.json")
    with open(path) as f:
        return {s["id"]: s for s in json.load(f)}


def get_learnable_spells(all_spells: Dict[str, Any], level: int) -> List[str]:
    """Return spell IDs the player should know at the given level."""
    return [
        sid
        for sid, data in all_spells.items()
        if data.get("learn_level", 99) <= level
    ]


def cast_spell(
    spell_id: str,
    caster: Any,
    target: Any,
    all_spells: Dict[str, Any],
    power_mult: float = 1.0,
) -> Tuple[bool, str]:
    """Cast *spell_id* from *caster* toward *target*.

    Parameters
    ----------
    power_mult:
        Multiplier applied to spell power (e.g. 0.5 for AoE spread).

    Returns
    -------
    (success, message):
        success – False when the cast fails (not enough MP, Silence, etc.).
        message – Description of what happened.
    """
    data = all_spells.get(spell_id)
    if data is None:
        return False, "Unknown spell."

    # Silence check
    if getattr(caster, "status", {}).get("silence"):
        return False, f"{caster.name} is silenced and cannot cast!"

    mp_cost = data.get("mp", 0)
    if caster.mp < mp_cost:
        return False, f"Not enough MP to cast {data['name']}!"

    caster.mp -= mp_cost
    effect = data.get("effect", "")
    power = data.get("power", 0) * power_mult
    element = data.get("element")

    # ── Damage spells ─────────────────────────────────────────────────────────
    if effect == "damage":
        caster_mag = effective_stat(caster, "mag")
        target_mdf = effective_stat(target, "mdf")
        base = max(1.0, caster_mag * power - target_mdf / 4.0)
        variance = 1.0 + random.uniform(-DAMAGE_VARIANCE, DAMAGE_VARIANCE)
        dmg = base * variance

        if element and hasattr(target, "weaknesses") and element in target.weaknesses:
            dmg *= 2.0
        if element and hasattr(target, "resistances") and element in target.resistances:
            dmg *= 0.5

        # Exo Armor: 25% elemental damage reduction
        if element and hasattr(target, "inventory"):
            armor_id = target.inventory.equipped("armor")
            if armor_id:
                from src.systems.inventory import load_items
                armor_data = load_items().get(armor_id, {})
                resist_pct = armor_data.get("elemental_resist", 0)
                dmg *= 1.0 - resist_pct / 100.0

        dmg_int = max(1, math.floor(dmg))
        target.take_damage(dmg_int)
        elem_str = f" [{element}]" if element else ""
        return True, f"{data['name']}{elem_str} hits {target.name} for {dmg_int} damage!"

    # ── Healing spells ────────────────────────────────────────────────────────
    if effect == "heal_hp":
        healed = target.heal(power)
        return True, f"{data['name']} restores {healed} HP to {target.name}."

    if effect == "revive":
        if target.hp > 0:
            return False, f"{target.name} is not KO'd."
        revive_hp = max(1, target.max_hp // 2)
        target.hp = revive_hp
        return True, f"{data['name']}: {target.name} revived with {revive_hp} HP."

    # ── Buffs ─────────────────────────────────────────────────────────────────
    if effect == "buff_def":
        target.buffs["def"] = [1.5, 5]
        return True, f"{data['name']}: {target.name}'s DEF increased!"

    if effect == "buff_mdf":
        target.buffs["mdf"] = [1.5, 5]
        return True, f"{data['name']}: {target.name}'s MDF increased!"

    if effect == "buff_spd":
        target.buffs["spd"] = [1.5, 5]
        return True, f"{data['name']}: {target.name}'s SPD increased!"

    # ── Debuffs ───────────────────────────────────────────────────────────────
    if effect == "debuff_spd":
        target.buffs["spd"] = [0.5, 3]
        return True, f"{data['name']}: {target.name}'s SPD decreased!"

    # ── Utility ───────────────────────────────────────────────────────────────
    if effect == "reveal_stats":
        hp = getattr(target, "hp", "?")
        max_hp = getattr(target, "max_hp", "?")
        spd = target.stats.get("spd", "?")
        weak = getattr(target, "weaknesses", [])
        resist = getattr(target, "resistances", [])
        msg = (
            f"{target.name}: HP {hp}/{max_hp}  SPD {spd}"
            + (f"  Weak: {','.join(weak)}" if weak else "")
            + (f"  Resist: {','.join(resist)}" if resist else "")
        )
        return True, msg

    if effect == "remove_buffs":
        if hasattr(target, "buffs"):
            target.buffs.clear()
        if hasattr(target, "status"):
            target.status.clear()
        return True, f"{data['name']}: {target.name}'s buffs removed."

    return True, f"{data['name']} was cast."


def tick_status_effects(combatant: Any) -> List[str]:
    """Advance all status effect and buff timers; apply Poison tick.

    Returns list of messages describing what happened.
    """
    messages: List[str] = []

    # Poison: deal 5% max_hp damage each turn
    if combatant.status.get("poison", 0) > 0:
        max_hp = getattr(combatant, "max_hp", None) or getattr(combatant, "hp", 20)
        poison_dmg = max(1, int(max_hp * 0.05))
        combatant.take_damage(poison_dmg)
        combatant.status["poison"] -= 1
        if combatant.status["poison"] <= 0:
            del combatant.status["poison"]
            messages.append(f"{combatant.name}'s Poison wore off.")
        else:
            messages.append(f"{combatant.name} takes {poison_dmg} poison damage!")

    # Sleep: wake up after turns expire (battle engine checks each turn)
    if combatant.status.get("sleep", 0) > 0:
        combatant.status["sleep"] -= 1
        if combatant.status["sleep"] <= 0:
            del combatant.status["sleep"]
            messages.append(f"{combatant.name} woke up!")

    # Blind, Silence countdowns
    for effect in ("blind", "silence"):
        if combatant.status.get(effect, 0) > 0:
            combatant.status[effect] -= 1
            if combatant.status[effect] <= 0:
                del combatant.status[effect]
                messages.append(f"{combatant.name}'s {effect.capitalize()} wore off.")

    # Buff/debuff countdowns
    expired = []
    for stat, (mult, turns) in list(getattr(combatant, "buffs", {}).items()):
        new_turns = turns - 1
        if new_turns <= 0:
            expired.append(stat)
        else:
            combatant.buffs[stat] = [mult, new_turns]
    for stat in expired:
        del combatant.buffs[stat]
        messages.append(f"{combatant.name}'s {stat} buff/debuff expired.")

    return messages


def effective_stat(combatant: Any, stat: str) -> float:
    """Return the effective value of *stat* after applying active buffs."""
    base = combatant.stats.get(stat, 1)
    buff = getattr(combatant, "buffs", {}).get(stat)
    if buff:
        return base * buff[0]
    return float(base)
