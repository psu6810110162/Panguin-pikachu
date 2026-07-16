"""Kivy audio adapter with bundle-safe absolute resource paths."""

from __future__ import annotations

from typing import Any

from kivy.core.audio import SoundLoader

from infrastructure.logging_config import logger
from infrastructure.paths import resource_path


class AudioManager:
    _instance: AudioManager | None = None
    _initialized: bool

    def __new__(cls) -> AudioManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.bgm: Any = None
        self.bgm_volume = 0.5
        self.sfx_volume = 0.8
        self.bgm_muted = False
        self.audio_available = True
        self._backend_warning_shown = False
        filenames = {
            "click": "click-b.ogg",
            "tab": "tap-a.ogg",
            "hit": "tap-b.ogg",
            "switch": "switch-a.ogg",
            "jump": "Jump.ogg",
            "jump2": "Jump 2.ogg",
            "down": "Down.ogg",
            "coin": "tap-a.ogg",
            # Generated, project-owned gameplay palette.
            "step": "step.wav",
            "quiz_open": "quiz_open.wav",
            "choice_left": "choice_left.wav",
            "choice_right": "choice_right.wav",
            "correct": "correct.wav",
            "wrong": "wrong.wav",
            "respawn": "respawn.wav",
            "boss_alert": "boss_alert.wav",
            "victory": "victory.wav",
        }
        self.sfx_paths = {
            name: str(
                resource_path("assets", "generated", "audio", filename)
                if filename.endswith(".wav")
                else resource_path("assets", "Component_UI", "Sounds", filename)
            )
            for name, filename in filenames.items()
        }
        self.sounds = {}
        for name, path in self.sfx_paths.items():
            if (sound := self._safe_load(path)) is not None:
                self.sounds[name] = sound

    def _safe_load(self, path: str) -> Any | None:
        """Load an optional sound without making the gameplay loop depend on audio."""
        try:
            sound = SoundLoader.load(path)
        except Exception as error:
            self.audio_available = False
            if not self._backend_warning_shown:
                logger.warning("Audio backend unavailable; continuing silently: %s", error)
                self._backend_warning_shown = True
            return None
        if sound is None:
            self.audio_available = False
        return sound

    def toggle_mute(self) -> bool:
        self.bgm_muted = not self.bgm_muted
        if self.bgm:
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
        return self.bgm_muted

    def play_bgm(self, filename: str, loop: bool = True) -> None:
        self.stop_bgm()
        path = str(resource_path("assets", "Component_UI", "Sounds", filename))
        self.bgm = self._safe_load(path)
        if self.bgm:
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
            self.bgm.loop = loop
            self.bgm.play()
        else:
            if self.audio_available:
                logger.warning("Optional BGM could not be loaded: %s", filename)

    def stop_bgm(self) -> None:
        if self.bgm:
            self.bgm.stop()
            self.bgm = None

    def play_sfx(self, name: str) -> None:
        if self.bgm_muted:
            return
        sound = self.sounds.get(name.lower())
        if sound:
            sound.volume = self.sfx_volume
            sound.play()
        else:
            if self.audio_available:
                logger.warning("Optional SFX could not be loaded: %s", name)

    def set_bgm_volume(self, volume: float) -> None:
        self.bgm_volume = volume
        if self.bgm:
            self.bgm.volume = volume
