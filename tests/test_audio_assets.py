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


def test_audio_manager_falls_back_when_backend_is_unavailable(monkeypatch):
    from infrastructure.audio import AudioManager, SoundLoader

    AudioManager._instance = None

    def unavailable(_path):
        raise RuntimeError("no audio device")

    monkeypatch.setattr(SoundLoader, "load", unavailable)
    manager = AudioManager()

    assert manager.audio_available is False
    assert manager.sounds == {}
    manager.play_sfx("step")
    manager.play_bgm("Bgm.gameplay.mp3")

    AudioManager._instance = None
