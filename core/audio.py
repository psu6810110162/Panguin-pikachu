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
        self.bgm_muted   = False 

        self.sfx_paths = {
            'click'  : f'{SOUND_DIR}click-b.ogg',
            'tab'    : f'{SOUND_DIR}tap-a.ogg',
            'hit'    : f'{SOUND_DIR}tap-b.ogg',
            'switch' : f'{SOUND_DIR}switch-a.ogg',
            'jump'   : f'{SOUND_DIR}Jump.ogg',
            'jump2'  : f'{SOUND_DIR}Jump 2.ogg',
            'down'   : f'{SOUND_DIR}Down.ogg',
            'coin'   : f'{SOUND_DIR}tap-a.ogg',
        }


    def toggle_mute(self): #สลับเปิด/ปิดเสียง BGM
        self.bgm_muted = not self.bgm_muted
        if self.bgm:
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
        return self.bgm_muted  # คืนค่า state ให้ UI อัปเดตปุ่ม
    

    def play_bgm(self, filename, loop=True):
        self.stop_bgm()
        path = f'{SOUND_DIR}{filename}'
        self.bgm = SoundLoader.load(path)
        if self.bgm:
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
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