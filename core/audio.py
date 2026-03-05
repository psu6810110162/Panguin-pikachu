from kivy.core.audio import SoundLoader

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

        self.bgm = None          # เพลงที่กำลังเล่นอยู่
        self.bgm_volume = 0.5   # ระดับเสียง 0.0 - 1.0
        self.sfx_volume = 0.8
        self.sfx = {
            'click'    : SoundLoader.load('assets/Component_UI/Sounds/click-b.ogg'),
            'tab'     : SoundLoader.load('assets/Component_UI/Sounds/tap-a.ogg'),
            'switch'     : SoundLoader.load('assets/Component_UI/Sounds/switch-a.ogg'),
            'Jump'     : SoundLoader.load('assets/Component_UI/Sounds/Jump.ogg'),
            'Down'     : SoundLoader.load('assets/Component_UI/Sounds/Down.ogg'),
        }

    def play_bgm(self, filename, loop=True): #หยุดเล่นเพลงเดิมก่อนเล่นเพลงใหม่
        self.stop_bgm()
        self.bgm = SoundLoader.load(f'assets/Component_UI/Sounds/{filename}')
        if self.bgm:
            self.bgm.volume = self.bgm_volume
            self.bgm.loop   = loop
            self.bgm.play()

    def stop_bgm(self):#หยุดเพลงที่กำลังเล่นอยู่ก่อนที่จะเล่นเพลงใหม่
        if self.bgm:
            self.bgm.stop()
            self.bgm = None

    def play_sfx(self, name):#เล่นเสียงเอฟเฟกต์ตามชื่อที่กำหนดไว้ใน self.sfx
        sound = self.sfx.get(name)
        if sound:
            sound.volume = self.sfx_volume
            sound.play()

    def set_bgm_volume(self, volume):#ปรับระดับเสียง BGM (0.0 - 1.0)
        self.bgm_volume = volume
        if self.bgm:
            self.bgm.volume = volume