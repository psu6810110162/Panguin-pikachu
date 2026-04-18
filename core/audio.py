from kivy.core.audio import SoundLoader
from core.logger import logger

# โฟลเดอร์ที่เก็บไฟล์เสียงทั้งหมด
SOUND_DIR = 'assets/Component_UI/Sounds/'

class AudioManager:
    """ คลาสสำหรับจัดการเสียง (Audio Manager) แบบ Singleton """
    _instance = None

    def __new__(cls):
        # สร้าง Instance เดียวตลอดอายุการใช้งานของแอป (Singleton)
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.bgm        = None   # ตัวแปรเก็บเพลงประกอบปัจจุบัน
        self.bgm_volume = 0.5    # ระดับความดังเพลงประกอบ (0.0 - 1.0)
        self.sfx_volume = 0.8    # ระดับความดังเสียง Effect
        self.bgm_muted  = False  # สถานะการปิดเสียงเพลงประกอบ

        # รายการไฟล์เสียง SFX (เสียงสั้นๆ เช่น กดปุ่ม, ตกหลุม)
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
        
        # โหลดไฟล์เสียงเตรียมไว้ล่วงหน้า (Pre-load) เพื่อลดความหน่วงเวลาเล่น
        self.sounds = {}
        for name, path in self.sfx_paths.items():
            s = SoundLoader.load(path)
            if s:
                self.sounds[name] = s

    def toggle_mute(self):
        """ สลับการเปิด/ปิดเสียงเพลงประกอบ (BGM) """
        self.bgm_muted = not self.bgm_muted
        if self.bgm:
            # ถ้าปิดเสียง (Muted) ให้ปรับ Volume เป็น 0
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
        return self.bgm_muted  # คืนค่าสถานะให้ UI นำไปอัปเดตรูปปุ่ม

    def play_bgm(self, filename, loop=True):
        """ สั่งเริ่มเล่นเพลงประกอบ (Background Music) """
        self.stop_bgm() # หยุดเพลงเก่ก่อน
        path = f'{SOUND_DIR}{filename}'
        self.bgm = SoundLoader.load(path)
        if self.bgm:
            self.bgm.volume = 0 if self.bgm_muted else self.bgm_volume
            self.bgm.loop   = loop # ตั้งค่าให้เล่นวนซ้ำ
            self.bgm.play()
            logger.debug(f"Playing BGM: {filename}")
        else:
            logger.warning(f"Failed to load BGM: {filename}")

    def stop_bgm(self):
        """ สั่งหยุดเพลงประกอบปัจจุบัน """
        if self.bgm:
            self.bgm.stop()
            self.bgm = None

    def play_sfx(self, name):
        """ สั่งเล่นเสียง Effect (เช่น เสียงกระโดด, เสียงเก็บเหรียญ) """
        sound = self.sounds.get(name.lower())
        if sound:
            sound.volume = self.sfx_volume
            sound.play()
            logger.debug(f"Playing SFX: {name}")
        else:
            logger.warning(f"Failed to load SFX: {name}")

    def set_bgm_volume(self, volume):
        """ ปรับระดับความดังของเพลงประกอบ """
        self.bgm_volume = volume
        if self.bgm and not self.bgm_muted:
            self.bgm.volume = volume