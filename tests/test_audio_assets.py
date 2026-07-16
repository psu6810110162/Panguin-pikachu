import wave
from pathlib import Path

EXPECTED_SFX = {
    "step.wav",
    "quiz_open.wav",
    "choice_left.wav",
    "choice_right.wav",
    "correct.wav",
    "wrong.wav",
    "respawn.wav",
    "boss_alert.wav",
    "victory.wav",
}


def test_generated_gameplay_sfx_are_small_mono_wav_files():
    root = Path("assets/generated/audio")
    assert {path.name for path in root.glob("*.wav")} == EXPECTED_SFX
    for path in root.glob("*.wav"):
        with wave.open(str(path), "rb") as audio:
            assert audio.getnchannels() == 1
            assert audio.getsampwidth() == 2
            assert audio.getframerate() == 44_100
            assert 0 < audio.getnframes() < 44_100 * 2
