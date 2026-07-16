"""Generate the small, license-free SFX palette used by Penguin Dash.

The sounds are intentionally short and synthetic so they remain readable over
the existing gameplay music.  Re-running this script deterministically
recreates ``assets/generated/audio/*.wav`` without requiring an audio package.
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44_100
OUTPUT_DIR = Path("assets/generated/audio")


def _envelope(t: float, duration: float, attack: float = 0.008) -> float:
    release = min(0.08, duration * 0.35)
    if t < attack:
        return t / attack
    if t > duration - release:
        return max(0.0, (duration - t) / release)
    return 1.0


def _tone(
    samples: list[float],
    start: float,
    duration: float,
    frequency: float,
    volume: float,
    end_frequency: float | None = None,
    harmonics: float = 0.15,
) -> None:
    first = max(0, int(start * SAMPLE_RATE))
    count = int(duration * SAMPLE_RATE)
    for index in range(count):
        pos = index / SAMPLE_RATE
        ratio = pos / duration if duration else 0.0
        freq = (
            frequency if end_frequency is None else frequency + (end_frequency - frequency) * ratio
        )
        phase = 2 * math.pi * freq * pos
        value = math.sin(phase) + harmonics * math.sin(phase * 2.0)
        target = first + index
        if target < len(samples):
            samples[target] += value * volume * _envelope(pos, duration)


def _noise(samples: list[float], start: float, duration: float, volume: float) -> None:
    first = max(0, int(start * SAMPLE_RATE))
    count = int(duration * SAMPLE_RATE)
    # A deterministic pseudo-noise burst keeps generated assets reproducible.
    for index in range(count):
        target = first + index
        if target < len(samples):
            value = math.sin((index + 1) * 12.9898) * 0.5
            samples[target] += value * volume * _envelope(index / SAMPLE_RATE, duration, 0.002)


def _write(name: str, duration: float, layers: list[tuple[str, tuple]]) -> None:
    samples = [0.0] * int(duration * SAMPLE_RATE)
    for kind, args in layers:
        if kind == "tone":
            _tone(samples, *args)
        else:
            _noise(samples, *args)
    peak = max(1.0, max(abs(value) for value in samples))
    pcm = b"".join(
        struct.pack("<h", int(max(-1.0, min(1.0, value / peak)) * 30_000)) for value in samples
    )
    path = OUTPUT_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm)


def main() -> None:
    _write("step.wav", 0.09, [("tone", (0.0, 0.09, 520.0, 0.18, None, 0.05))])
    _write(
        "quiz_open.wav",
        0.38,
        [
            ("tone", (0.00, 0.13, 392.0, 0.18, None, 0.12)),
            ("tone", (0.12, 0.13, 523.0, 0.18, None, 0.12)),
            ("tone", (0.24, 0.14, 784.0, 0.22, None, 0.12)),
        ],
    )
    _write("choice_left.wav", 0.18, [("tone", (0.0, 0.18, 330.0, 0.25, 285.0, 0.1))])
    _write("choice_right.wav", 0.18, [("tone", (0.0, 0.18, 520.0, 0.25, 680.0, 0.1))])
    _write(
        "correct.wav",
        0.42,
        [
            ("tone", (0.00, 0.16, 659.0, 0.23, None, 0.1)),
            ("tone", (0.14, 0.25, 988.0, 0.24, None, 0.1)),
        ],
    )
    _write(
        "wrong.wav",
        0.40,
        [
            ("tone", (0.00, 0.20, 260.0, 0.25, 180.0, 0.2)),
            ("noise", (0.18, 0.16, 0.08)),
        ],
    )
    _write(
        "respawn.wav",
        0.75,
        [("tone", (0.00, 0.70, 180.0, 0.25, 720.0, 0.12))],
    )
    _write(
        "boss_alert.wav",
        0.90,
        [
            ("tone", (0.00, 0.28, 110.0, 0.34, 82.0, 0.2)),
            ("tone", (0.34, 0.28, 110.0, 0.34, 82.0, 0.2)),
            ("tone", (0.68, 0.20, 220.0, 0.28, 150.0, 0.15)),
        ],
    )
    _write(
        "victory.wav",
        0.95,
        [
            ("tone", (0.00, 0.18, 523.0, 0.20, None, 0.1)),
            ("tone", (0.16, 0.18, 659.0, 0.20, None, 0.1)),
            ("tone", (0.32, 0.18, 784.0, 0.20, None, 0.1)),
            ("tone", (0.48, 0.42, 1046.0, 0.24, None, 0.1)),
        ],
    )


if __name__ == "__main__":
    main()
