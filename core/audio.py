from typing import Any

from kivy.core.audio import SoundLoader

SOUND_DIR = "assets/Component_UI/Sounds/"


class AudioManager:
    _instance: "AudioManager | None" = None
    _initialized: bool
    bgm: Any
    bgm_volume: float
    sfx_volume: float
    bgm_muted: bool
    sfx_paths: dict[str, str]
    sounds: dict[str, Any]

    def __new__(cls) -> "AudioManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self.bgm = None
        self.bgm_volume = 0.5
        self.sfx_volume = 0.8
        self._sfx_ref = None
        self.bgm_muted = False
        self._bgm_paused = False
        self._bgm_pause_pos = 0.0

        self.sfx_paths = {
            "click": f"{SOUND_DIR}click-b.ogg",
            "tab": f"{SOUND_DIR}tap-a.ogg",
            "hit": f"{SOUND_DIR}tap-b.ogg",
            "switch": f"{SOUND_DIR}switch-a.ogg",
            "jump": f"{SOUND_DIR}Jump.ogg",
            "jump2": f"{SOUND_DIR}Jump 2.ogg",
            "down": f"{SOUND_DIR}Down.ogg",
            "coin": f"{SOUND_DIR}tap-a.ogg",
        }

        # Pre-load sounds to avoid lag and channel leaks
        self.sounds = {}
        for name, path in self.sfx_paths.items():
            s = SoundLoader.load(path)
            if s:
                self.sounds[name] = s

    def toggle_mute(self) -> bool:  # สลับเปิด/ปิดเสียง BGM
        self.bgm_muted = not self.bgm_muted
        if self.bgm:
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
        return self.bgm_muted  # คืนค่า state ให้ UI อัปเดตปุ่ม

    def play_bgm(self, filename: str, loop: bool = True) -> None:
        self.stop_bgm()
        path = f"{SOUND_DIR}{filename}"
        self.bgm = SoundLoader.load(path)
        if self.bgm:
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
            self.bgm.loop = loop
            self.bgm.play()
            print(f"[AudioManager] ✅ เล่น BGM: {filename}")
        else:
            print(f"[AudioManager] ⚠️ โหลด BGM ไม่ได้: {filename}")

    def stop_bgm(self) -> None:
        if self.bgm:
            self.bgm.stop()
            self.bgm = None
        self._bgm_paused = False
        self._bgm_pause_pos = 0.0

    def pause_bgm(self) -> None:
        """Pause BGM in place; idempotent — a second call while already
        paused (e.g. opening Help from the Pause menu, which requests pause
        again) is a no-op instead of losing the remembered position.
        """
        if not self.bgm or self._bgm_paused:
            return
        self._bgm_paused = True
        get_pos = getattr(self.bgm, "get_pos", None)
        self._bgm_pause_pos = get_pos() if get_pos else 0.0
        self.bgm.stop()

    def resume_bgm(self) -> None:
        """Resume BGM from the position remembered by ``pause_bgm``.

        Idempotent — calling this while not paused (e.g. no reasons were
        ever active) is a no-op. Providers that don't expose ``seek`` simply
        restart from 0, which is an accepted degradation, not a crash.
        """
        if not self.bgm or not self._bgm_paused:
            return
        self._bgm_paused = False
        self.bgm.play()
        seek = getattr(self.bgm, "seek", None)
        if seek and self._bgm_pause_pos:
            seek(self._bgm_pause_pos)
        self._bgm_pause_pos = 0.0

    def play_sfx(self, name: str) -> None:
        if self.bgm_muted:
            return
        sound = self.sounds.get(name.lower())
        if sound:
            # Note: playing an already playing sound depends on the provider.
            # Some restart, some do nothing. For brief SFX, this is usually okay.
            sound.volume = self.sfx_volume
            sound.play()
            print(f"[AudioManager] ✅ เล่น SFX: {name}")
        else:
            print(f"[AudioManager] ⚠️ ไม่พบหรือโหลด SFX ไม่ได้: {name}")

    def set_bgm_volume(self, volume: float) -> None:
        self.bgm_volume = volume
        if self.bgm:
            self.bgm.volume = volume
