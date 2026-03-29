#!/usr/bin/env python3
"""
scripts/generate_audio.py - Generate placeholder WAV audio assets.

Run once (from the repository root) to populate assets/music/ and assets/sfx/
with synthesised chiptune-style audio.  Existing files are NOT overwritten.

Usage:
    python scripts/generate_audio.py
"""

import math
import os
import random
import struct
import sys
import wave

# ── Constants ─────────────────────────────────────────────────────────────────

SR = 44100        # sample rate (Hz)
AMP = 24000       # peak amplitude (headroom below 16-bit max of 32767)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_DIR = os.path.join(ROOT_DIR, "assets", "music")
SFX_DIR = os.path.join(ROOT_DIR, "assets", "sfx")

# ── Note frequencies (Hz) ─────────────────────────────────────────────────────

NOTE: dict[str, float] = {
    "C2": 65.41,  "D2": 73.42,  "Eb2": 77.78,  "E2": 82.41,  "F2": 87.31,  "G2": 98.00,
    "Ab2": 103.83, "A2": 110.00, "Bb2": 116.54, "B2": 123.47,
    "C3": 130.81, "D3": 146.83, "Eb3": 155.56, "E3": 164.81, "F3": 174.61,
    "F#3": 185.00, "G3": 196.00, "Ab3": 207.65, "A3": 220.00,
    "Bb3": 233.08, "B3": 246.94,
    "C4": 261.63, "D4": 293.66, "Eb4": 311.13, "E4": 329.63, "F4": 349.23,
    "F#4": 369.99, "G4": 392.00, "Ab4": 415.30, "A4": 440.00,
    "Bb4": 466.16, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "G5": 783.99,
    "REST": 0.0,
}

# ── Low-level synthesis helpers ───────────────────────────────────────────────


def _t(n: int) -> list[float]:
    """Return a list of *n* time values at sample rate SR."""
    return [i / SR for i in range(n)]


def sine(freq: float, t_arr: list[float], amp: int = AMP) -> list[int]:
    """Sine wave."""
    if freq == 0:
        return [0] * len(t_arr)
    return [int(amp * math.sin(2 * math.pi * freq * t)) for t in t_arr]


def triangle(freq: float, t_arr: list[float], amp: int = AMP) -> list[int]:
    """Triangle wave (softer timbre than square, richer than sine)."""
    if freq == 0:
        return [0] * len(t_arr)
    p = 1.0 / freq
    return [int(amp * (2 * abs(2 * ((t % p) / p) - 1) - 1)) for t in t_arr]


def envelope(
    samples: list[int],
    attack: float = 0.01,
    decay: float = 0.04,
    sustain: float = 0.7,
    release: float = 0.08,
) -> list[int]:
    """Apply a simple ADSR envelope."""
    n = len(samples)
    atk = int(attack * SR)
    dec = int(decay * SR)
    rel = int(release * SR)
    out = []
    for i, s in enumerate(samples):
        if i < atk:
            env = i / max(atk, 1)
        elif i < atk + dec:
            env = 1.0 - (i - atk) / max(dec, 1) * (1.0 - sustain)
        elif i < n - rel:
            env = sustain
        else:
            env = sustain * (1.0 - (i - (n - rel)) / max(rel, 1))
        out.append(int(s * env))
    return out


def mix(*wave_lists: list[int]) -> list[int]:
    """Average-mix multiple same-length wave arrays (prevents clipping)."""
    n = max(len(w) for w in wave_lists)
    result = [0] * n
    for w in wave_lists:
        for i, v in enumerate(w):
            result[i] += v
    d = len(wave_lists)
    return [s // d for s in result]


def pad(a: list[int], b: list[int]) -> tuple[list[int], list[int]]:
    """Zero-pad the shorter of two arrays so they are the same length."""
    diff = len(a) - len(b)
    if diff > 0:
        b = b + [0] * diff
    elif diff < 0:
        a = a + [0] * (-diff)
    return a, b


# ── Note / sequence helpers ───────────────────────────────────────────────────


def note(freq: float, dur_s: float, wave_fn=triangle, amp: int = AMP) -> list[int]:
    """Generate a single note with ADSR envelope applied."""
    n = int(SR * dur_s)
    raw = wave_fn(freq, _t(n), amp)
    return envelope(raw, attack=0.01, decay=0.04, sustain=0.7, release=0.12)


def sequence(
    notes: list[tuple[str, float]],
    bpm: float,
    wave_fn=triangle,
    amp: int = AMP,
) -> list[int]:
    """
    Render a list of (note_name, beat_count) tuples at the given BPM.

    Each note is gated at 88% of its beat duration before the envelope is
    applied so adjacent notes are distinctly separated.
    """
    beat = 60.0 / bpm
    out: list[int] = []
    for name, beats in notes:
        freq = NOTE[name]
        total = int(SR * beat * beats)
        gate = int(total * 0.88)
        raw = note(freq, gate / SR, wave_fn, amp)
        raw += [0] * (total - len(raw))
        out.extend(raw)
    return out


# ── Write helpers ─────────────────────────────────────────────────────────────


def write_wav(path: str, samples: list[int]) -> None:
    """Write a mono 16-bit 44100 Hz WAV file."""
    clamped = [max(-32768, min(32767, s)) for s in samples]
    data = struct.pack("<" + "h" * len(clamped), *clamped)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(data)
    dur = len(clamped) / SR
    print(f"  wrote  {os.path.basename(path)}  ({dur:.2f}s)")


def save(path: str, samples: list[int]) -> None:
    """Write *path* only if it does not already exist."""
    if os.path.exists(path):
        print(f"  skip   {os.path.basename(path)}  (exists)")
        return
    write_wav(path, samples)


# ── Music generators ──────────────────────────────────────────────────────────


def gen_title() -> list[int]:
    """Slow, peaceful C-major arpeggio — title screen."""
    melody = sequence(
        [
            ("C3", 2), ("E3", 2), ("G3", 2), ("C4", 2),
            ("G3", 2), ("E3", 2), ("C3", 2), ("G2", 2),
            ("C3", 2), ("F3", 2), ("A3", 2), ("C4", 2),
            ("A3", 2), ("F3", 2), ("C3", 2), ("C3", 4),
        ],
        bpm=58, amp=18000,
    )
    bass = sequence(
        [
            ("C2", 4), ("C2", 4), ("F2", 4), ("G2", 4),
            ("C2", 4), ("C2", 4), ("F2", 4), ("G2", 4),
        ],
        bpm=58, wave_fn=sine, amp=7000,
    )
    a, b = pad(melody, bass)
    return mix(a, b)


def gen_overworld() -> list[int]:
    """Upbeat G-major walking feel — overworld exploration."""
    melody = sequence(
        [
            ("G3", 1), ("B3", 1), ("D4", 1), ("G4", 1),
            ("F#4", 1), ("E4", 1), ("D4", 1), ("B3", 1),
            ("G3", 1), ("A3", 1), ("B3", 1), ("C4", 1),
            ("D4", 2), ("REST", 1), ("G3", 1),
            ("G3", 1), ("B3", 1), ("D4", 1), ("E4", 1),
            ("D4", 1), ("C4", 1), ("B3", 1), ("A3", 1),
            ("G3", 2), ("D3", 2), ("G3", 4),
        ],
        bpm=115, amp=17000,
    )
    bass = sequence(
        [
            ("G2", 2), ("D3", 2), ("G2", 2), ("D3", 2),
            ("C3", 2), ("G2", 2), ("D3", 2), ("G2", 2),
            ("G2", 2), ("D3", 2), ("G2", 4),
        ],
        bpm=115, wave_fn=sine, amp=7000,
    )
    a, b = pad(melody, bass)
    return mix(a, b)


def gen_town() -> list[int]:
    """Warm F-major theme — town / inn."""
    melody = sequence(
        [
            ("F3", 2), ("A3", 2), ("C4", 2), ("A3", 2),
            ("F3", 2), ("G3", 2), ("A3", 4),
            ("Bb3", 2), ("A3", 2), ("G3", 2), ("F3", 2),
            ("C3", 2), ("F3", 2), ("C4", 4),
            ("F3", 2), ("A3", 2), ("C4", 2), ("A3", 2),
            ("G3", 2), ("F3", 2), ("E3", 2), ("F3", 2),
            ("C4", 2), ("A3", 2), ("G3", 2), ("F3", 2),
            ("F3", 4), ("REST", 4),
        ],
        bpm=96, amp=17000,
    )
    bass = sequence(
        [
            ("F2", 4), ("C3", 4), ("Bb2", 4), ("C3", 4),
            ("F2", 4), ("C3", 4), ("F2", 4), ("F2", 4),
        ],
        bpm=96, wave_fn=sine, amp=7000,
    )
    a, b = pad(melody, bass)
    return mix(a, b)


def gen_battle() -> list[int]:
    """Intense E-minor — normal battle."""
    melody = sequence(
        [
            ("E3", 1), ("E3", 1), ("G3", 1), ("E3", 1),
            ("F3", 1), ("E3", 1), ("D3", 1), ("E3", 1),
            ("E3", 1), ("E3", 1), ("G3", 1), ("A3", 1),
            ("B3", 2), ("REST", 1), ("E3", 1),
            ("G3", 1), ("F#3", 1), ("E3", 1), ("D3", 1),
            ("E3", 1), ("B2", 1), ("E3", 2),
            ("D3", 1), ("E3", 1), ("F3", 1), ("E3", 1),
            ("E3", 4),
        ],
        bpm=158, amp=19000,
    )
    bass = sequence(
        [
            ("E2", 2), ("B2", 2), ("E2", 2), ("B2", 2),
            ("A2", 2), ("E2", 2), ("B2", 2), ("E2", 2),
            ("G2", 2), ("D3", 2), ("E2", 4),
        ],
        bpm=158, wave_fn=sine, amp=9000,
    )
    a, b = pad(melody, bass)
    return mix(a, b)


def gen_boss_battle() -> list[int]:
    """Heavy, ominous E-Phrygian — boss encounters."""
    melody = sequence(
        [
            ("E3", 1), ("REST", 1), ("E3", 1), ("REST", 1),
            ("Ab3", 1), ("REST", 1), ("G3", 2),
            ("E3", 1), ("REST", 1), ("E3", 1), ("REST", 1),
            ("F3", 2), ("Eb3", 2),
            ("E3", 1), ("REST", 1), ("E3", 1), ("REST", 1),
            ("Ab3", 1), ("REST", 1), ("Bb3", 2),
            ("Ab3", 2), ("G3", 2), ("E3", 4),
        ],
        bpm=135, amp=20000,
    )
    bass = sequence(
        [
            ("E2", 2), ("E2", 2), ("Ab2", 2), ("G2", 2),
            ("E2", 2), ("E2", 2), ("F2", 2), ("Eb2", 2),
            ("E2", 2), ("E2", 2), ("Ab2", 2), ("Bb2", 2),
            ("Ab2", 2), ("G2", 2), ("E2", 4),
        ],
        bpm=135, wave_fn=sine, amp=11000,
    )
    a, b = pad(melody, bass)
    return mix(a, b)


def gen_cutscene() -> list[int]:
    """Slow, dramatic D-minor — cutscenes and story moments."""
    melody = sequence(
        [
            ("D3", 3), ("F3", 1), ("A3", 3), ("F3", 1),
            ("D3", 3), ("E3", 1), ("F3", 2), ("E3", 2),
            ("D4", 3), ("C4", 1), ("Bb3", 2), ("A3", 2),
            ("G3", 2), ("F3", 2), ("E3", 2), ("D3", 2),
            ("D3", 4), ("REST", 4),
        ],
        bpm=68, amp=17000,
    )
    bass = sequence(
        [
            ("D2", 4), ("A2", 4), ("D2", 4), ("E2", 4),
            ("D3", 4), ("C3", 4), ("G2", 4), ("D2", 4),
        ],
        bpm=68, wave_fn=sine, amp=8000,
    )
    a, b = pad(melody, bass)
    return mix(a, b)


def gen_victory() -> list[int]:
    """Triumphant C-major fanfare — plays once after battle victory."""
    melody = sequence(
        [
            ("C4", 1), ("E4", 1), ("G4", 1), ("C5", 2),
            ("G4", 1), ("C5", 1), ("E5", 3),
            ("E4", 1), ("G4", 1), ("C5", 1), ("E5", 2),
            ("C5", 1), ("G4", 1), ("C5", 3),
            ("C4", 1), ("D4", 1), ("E4", 1), ("F4", 1), ("G4", 1),
            ("A4", 1), ("B4", 1), ("C5", 4),
            ("REST", 4),
        ],
        bpm=138, amp=20000,
    )
    bass = sequence(
        [
            ("C3", 3), ("G3", 3), ("C4", 3),
            ("C4", 3), ("G3", 3), ("C3", 3),
            ("G2", 7), ("C3", 5),
            ("REST", 4),
        ],
        bpm=138, wave_fn=sine, amp=9000,
    )
    a, b = pad(melody, bass)
    return mix(a, b)


def gen_game_over() -> list[int]:
    """Somber A-minor descent — game over screen."""
    return sequence(
        [
            ("A3", 3), ("G3", 2), ("F3", 3),
            ("E3", 3), ("D3", 2), ("C3", 3),
            ("E3", 4), ("A2", 8),
            ("REST", 8),
        ],
        bpm=58, amp=15000,
    )


# ── SFX generators ────────────────────────────────────────────────────────────


def gen_cursor() -> list[int]:
    """Tiny high blip for menu cursor movement."""
    n = int(SR * 0.055)
    s = sine(880, _t(n), amp=9000)
    return envelope(s, attack=0.003, decay=0.015, sustain=0.0, release=0.04)


def gen_confirm() -> list[int]:
    """Two ascending tones — menu confirm / select."""
    n1 = int(SR * 0.065)
    n2 = int(SR * 0.065)
    s1 = envelope(sine(660, _t(n1), 10000), 0.003, 0.01, 0.0, 0.05)
    gap = [0] * int(SR * 0.018)
    s2 = envelope(sine(880, _t(n2), 10000), 0.003, 0.01, 0.0, 0.05)
    return s1 + gap + s2


def gen_cancel() -> list[int]:
    """Low descending tone — cancel / back."""
    n = int(SR * 0.09)
    s = sine(330, _t(n), amp=9000)
    return envelope(s, attack=0.003, decay=0.01, sustain=0.2, release=0.07)


def gen_attack_hit() -> list[int]:
    """Percussive impact — physical attack landing."""
    n = int(SR * 0.16)
    rng = random.Random(42)
    noise = [int(AMP * 0.38 * (rng.random() * 2 - 1)) for _ in range(n)]
    low = sine(110, _t(n), amp=int(AMP * 0.28))
    mixed = [noise[i] + low[i] for i in range(n)]
    return envelope(mixed, attack=0.002, decay=0.03, sustain=0.08, release=0.10)


def gen_spell_cast() -> list[int]:
    """Rising frequency sweep with tremolo — magical spell cast."""
    n = int(SR * 0.32)
    result: list[int] = []
    for i in range(n):
        t = i / SR
        freq = 380 + (1180 - 380) * (t / 0.32)
        s = int(13000 * math.sin(2 * math.pi * freq * t))
        s = int(s * (0.5 + 0.5 * math.sin(2 * math.pi * 18 * t)))
        result.append(s)
    return envelope(result, attack=0.02, decay=0.05, sustain=0.6, release=0.10)


def gen_item_use() -> list[int]:
    """Gentle double-tone chime — item used."""
    n = int(SR * 0.22)
    s1 = sine(523, _t(n), amp=9000)   # C5
    s2 = sine(659, _t(n), amp=5500)   # E5
    mixed = [s1[i] + s2[i] for i in range(n)]
    return envelope(mixed, attack=0.01, decay=0.05, sustain=0.35, release=0.10)


def gen_level_up() -> list[int]:
    """Bright ascending arpeggio — level gained."""
    steps = [
        ("C4", 0.09), ("E4", 0.09), ("G4", 0.09),
        ("C5", 0.18), ("E5", 0.14), ("G5", 0.28),
    ]
    out: list[int] = []
    for name, dur in steps:
        freq = NOTE[name]
        n = int(SR * dur)
        s = triangle(freq, _t(n), amp=17000)
        s = envelope(s, attack=0.01, decay=0.02, sustain=0.7, release=0.05)
        out.extend(s)
    return out


def gen_door_open() -> list[int]:
    """Short click-burst — door / chest opening."""
    n = int(SR * 0.18)
    rng = random.Random(99)
    noise = [int(7500 * (rng.random() * 2 - 1)) for _ in range(n)]
    low = sine(180, _t(n), amp=4000)
    mixed = [noise[i] + low[i] for i in range(n)]
    return envelope(mixed, attack=0.005, decay=0.06, sustain=0.04, release=0.10)


def gen_dialog_open() -> list[int]:
    """Bright short chime — dialogue box appears."""
    n = int(SR * 0.13)
    s = sine(880, _t(n), amp=11000)
    s2 = sine(1100, _t(n), amp=5500)
    mixed = [s[i] + s2[i] for i in range(n)]
    return envelope(mixed, attack=0.005, decay=0.02, sustain=0.25, release=0.08)


def gen_dialog_close() -> list[int]:
    """Softer lower tone — dialogue box closes."""
    n = int(SR * 0.09)
    s = sine(660, _t(n), amp=9000)
    return envelope(s, attack=0.003, decay=0.01, sustain=0.2, release=0.07)


def gen_item_get() -> list[int]:
    """Bright ascending three-note chime — item/gold received."""
    steps = [
        ("C5", 0.07), ("E5", 0.07), ("G5", 0.14),
    ]
    out: list[int] = []
    for name, dur in steps:
        freq = NOTE[name]
        n = int(SR * dur)
        s = triangle(freq, _t(n), amp=16000)
        s = envelope(s, attack=0.005, decay=0.02, sustain=0.6, release=0.06)
        out.extend(s)
    return out


def gen_quest_start() -> list[int]:
    """Two rising tones with a brief pause — new quest accepted."""
    n1 = int(SR * 0.09)
    n2 = int(SR * 0.13)
    s1 = envelope(triangle(440, _t(n1), 12000), 0.005, 0.02, 0.4, 0.06)
    gap = [0] * int(SR * 0.03)
    s2 = envelope(triangle(660, _t(n2), 14000), 0.005, 0.02, 0.5, 0.08)
    return s1 + gap + s2


def gen_quest_complete() -> list[int]:
    """Short triumphant ascending arpeggio — quest completed."""
    steps = [
        ("C4", 0.07), ("E4", 0.07), ("G4", 0.07), ("C5", 0.20),
    ]
    out: list[int] = []
    for name, dur in steps:
        freq = NOTE[name]
        n = int(SR * dur)
        s = triangle(freq, _t(n), amp=18000)
        s = envelope(s, attack=0.005, decay=0.02, sustain=0.65, release=0.07)
        out.extend(s)
    return out


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    os.makedirs(MUSIC_DIR, exist_ok=True)
    os.makedirs(SFX_DIR, exist_ok=True)

    print("Generating music tracks …")
    music = {
        "title":       gen_title,
        "overworld":   gen_overworld,
        "town":        gen_town,
        "battle":      gen_battle,
        "boss_battle": gen_boss_battle,
        "cutscene":    gen_cutscene,
        "victory":     gen_victory,
        "game_over":   gen_game_over,
    }
    for name, fn in music.items():
        save(os.path.join(MUSIC_DIR, f"{name}.wav"), fn())

    print("\nGenerating sound effects …")
    sfx = {
        "cursor":         gen_cursor,
        "confirm":        gen_confirm,
        "cancel":         gen_cancel,
        "attack_hit":     gen_attack_hit,
        "spell_cast":     gen_spell_cast,
        "item_use":       gen_item_use,
        "level_up":       gen_level_up,
        "door_open":      gen_door_open,
        "dialog_open":    gen_dialog_open,
        "dialog_close":   gen_dialog_close,
        "item_get":       gen_item_get,
        "quest_start":    gen_quest_start,
        "quest_complete": gen_quest_complete,
    }
    for name, fn in sfx.items():
        save(os.path.join(SFX_DIR, f"{name}.wav"), fn())

    print("\nDone.  All audio assets are in assets/music/ and assets/sfx/")


if __name__ == "__main__":
    main()
