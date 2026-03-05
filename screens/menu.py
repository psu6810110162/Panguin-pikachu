from kivy.uix.screenmanager import Screen
from core.audio import AudioManager
from core.logger import logger

class MenuScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ MenuScreen")
        AudioManager().play_bgm('Bgm.gameplay.mp3')

    def start_game(self):
        # สั่งให้ ScreenManager เปลี่ยนหน้าไปที่ 'gameplay'
        logger.info("กำลังเริ่มต้นเกม...")
        self.manager.current = 'gameplay'
