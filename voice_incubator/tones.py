"""Short sounds the app makes itself, at the satellites' rate: the chime before
an announcement, the tone once a wake word has been checked, and the
intercom's tones as it connects and ends."""

from __future__ import annotations

import numpy as np

from .instruments import LOUDNESS, PEAK, leveled
from .protocol import SAMPLE_RATE

LEVEL = 0.3
"""Of full scale: about as loud as speech."""


def _notes(notes: list[float], note_s: float, gap_s: float) -> np.ndarray:
    """Notes one after another, each struck and dying away, at full scale,
    with the quiet after each."""
    parts = []
    for frequency in notes:
        t = np.arange(int(note_s * SAMPLE_RATE)) / SAMPLE_RATE
        envelope = np.minimum(1.0, t / 0.004) * np.exp(-t * 7.0)
        wave = np.sin(2 * np.pi * frequency * t) + 0.25 * np.sin(4 * np.pi * frequency * t)
        parts += [wave * envelope / 1.25, np.zeros(int(gap_s * SAMPLE_RATE))]
    return np.concatenate(parts)


def _pcm(x: np.ndarray) -> bytes:
    """16-bit PCM, at most full scale."""
    return (np.clip(x, -1.0, 1.0) * 32767).astype("<i2").tobytes()


REVERB = 0.35
"""How much of the room is heard beside the tone: about ten dB below the
note's own loudness."""

REVERB_TAIL = 0.05
"""The room's length: a small room's first reflections, in the quiet after
the note. Kept inside the chime's fifth of a second."""


def _room_ir() -> np.ndarray:
    """The room's impulse: decaying, low-passed noise of unit energy, with its
    first two milliseconds still -- the note itself is the direct sound."""
    count = int(REVERB_TAIL * SAMPLE_RATE)
    t = np.arange(count) / SAMPLE_RATE
    noise = np.random.default_rng(0).uniform(-1.0, 1.0, count)
    low_pass = np.empty(count)
    y = 0.0
    for i, value in enumerate(noise):
        y = 0.35 * value + 0.65 * y
        low_pass[i] = y
    ir = low_pass * np.exp(-t * 75.0)
    ir[: int(0.002 * SAMPLE_RATE)] = 0.0
    return ir / np.sqrt(np.sum(ir**2))


_ROOM_IR = _room_ir()


def _room(x: np.ndarray) -> np.ndarray:
    """``x`` with its short room: the note, then REVERB of its reflections."""
    out = np.zeros(len(x) + len(_ROOM_IR) - 1)
    out[: len(x)] = x
    out += REVERB * np.convolve(x, _ROOM_IR)
    return out


def bell(notes: list[float], note_s: float = 0.22, gap_s: float = 0.03, level: float = LEVEL) -> bytes:
    """Notes (Hz) one after another, each struck and dying away, as 16-bit PCM."""
    return _pcm(_notes(notes, note_s, gap_s) * level)


CHIME = bell([659.25, 523.25], note_s=0.4)
"""Before an announcement: ding, dong."""

CONNECTED = bell([523.25, 783.99])
"""The intercom connects: up."""

ENDED = bell([783.99, 523.25])
"""The intercom ends: down."""

WAKE_NOTES: dict[str, tuple[list[float], float, float]] = {
    "note": ([880.0], 0.13, 0.01),
    "ding_dong": ([783.99, 523.25], 0.065, 0.005),
    "dong_ding": ([523.25, 783.99], 0.065, 0.005),
    "stairs": ([523.25, 587.33, 659.25], 0.045, 0.004),
    "ping": ([1318.51], 0.07, 0.005),
}
"""What the wake chime may be: the notes (Hz), how long each sounds, and the
quiet after it (little: the room fills it). All short: the command being said
is recognized from the same speaker output, which hears the chime too."""

WAKE_LEVELS: dict[str, tuple[float, float]] = {
    "normal": (LOUDNESS, PEAK),
    "loud": (-15.0, 0.9),
    "loudest": (-12.0, 0.9),
}
"""How loud: as the call's sounds (-19 dB where it sounds, its peak at most
0.7), louder (-15: a timer's ring is -15), or loudest (-12). There is no
louder: speech-to-text hears the chime on the command's own capture, and the
command comes right after it."""

_WAKE_ROOMS = {sound: _room(_notes(*notes)) for sound, notes in WAKE_NOTES.items()}

WAKE_TONES: dict[str, dict[str, bytes]] = {
    sound: {level: _pcm(leveled(x, *loudness)) for level, loudness in WAKE_LEVELS.items()}
    for sound, x in _WAKE_ROOMS.items()
}

WAKE = WAKE_TONES["note"]["normal"]
"""Once the wake word has been checked, unless the home's or the area's is
another: one short note, at the call's sounds' loudness."""


def wake(sound: str = "note", level: str = "normal") -> bytes:
    """The tone once a wake word has been checked: ``sound`` (WAKE_NOTES) at
    ``level`` (WAKE_LEVELS). Anything else: the default, ``WAKE``."""
    return WAKE_TONES.get(sound, {}).get(level) or WAKE
