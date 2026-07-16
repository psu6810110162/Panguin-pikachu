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
        filenames = {
            "click": "click-b.ogg",
            "tab": "tap-a.ogg",
            "hit": "tap-b.ogg",
            "switch": "switch-a.ogg",
            "jump": "Jump.ogg",
            "jump2": "Jump 2.ogg",
            "down": "Down.ogg",
            "coin": "tap-a.ogg",
        }
        self.sfx_paths = {
            name: str(resource_path("assets", "Component_UI", "Sounds", filename))
            for name, filename in filenames.items()
        }
        self.sounds = {
            name: sound
            for name, path in self.sfx_paths.items()
            if (sound := SoundLoader.load(path)) is not None
        }

    def toggle_mute(self) -> bool:
        self.bgm_muted = not self.bgm_muted
        if self.bgm:
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
        return self.bgm_muted

    def play_bgm(self, filename: str, loop: bool = True) -> None:
        self.stop_bgm()
        path = str(resource_path("assets", "Component_UI", "Sounds", filename))
        self.bgm = SoundLoader.load(path)
        if self.bgm:
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
            self.bgm.loop = loop
            self.bgm.play()
        else:
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
            logger.warning("Optional SFX could not be loaded: %s", name)

    def set_bgm_volume(self, volume: float) -> None:
        self.bgm_volume = volume
        if self.bgm:
            self.bgm.volume = volume
