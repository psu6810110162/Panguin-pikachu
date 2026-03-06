from kivy.core.audio import SoundLoader

SOUND_DIR = 'assets/Component_UI/Sounds/'

class AudioManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.bgm        = None
        self.bgm_volume = 0.5
        self.sfx_volume = 0.8
        self._sfx_ref   = None  

        self.sfx_paths = {
            'click'  : f'{SOUND_DIR}click-b.ogg',
            'tab'    : f'{SOUND_DIR}tap-a.ogg',
            'switch' : f'{SOUND_DIR}switch-a.ogg',
            'jump'   : f'{SOUND_DIR}Jump.ogg',
            'down'   : f'{SOUND_DIR}Down.ogg',
        }

    def play_bgm(self, filename, loop=True):
        self.stop_bgm()
        path = f'{SOUND_DIR}{filename}'
        self.bgm = SoundLoader.load(path)
        if self.bgm:
            self.bgm.volume = self.bgm_volume
            self.bgm.loop   = loop
            self.bgm.play()
            print(f"[AudioManager] ✅ เล่น BGM: {filename}")
        else:
            print(f"[AudioManager] ⚠️ โหลด BGM ไม่ได้: {filename}")

    def stop_bgm(self):
        if self.bgm:
            self.bgm.stop()
            self.bgm = None

    def play_sfx(self, name):
        path = self.sfx_paths.get(name.lower())
        if not path:
            print(f"[AudioManager] ⚠️ ไม่พบ SFX: {name}")
            return

        self._sfx_ref = SoundLoader.load(path)  
        if self._sfx_ref:
            self._sfx_ref.volume = self.sfx_volume
            self._sfx_ref.play()
            print(f"[AudioManager] ✅ เล่น SFX: {name}")
        else:
            print(f"[AudioManager] ⚠️ โหลด SFX ไม่ได้: {path}")

    def set_bgm_volume(self, volume):
        self.bgm_volume = volume
        if self.bgm:
            self.bgm.volume = volume