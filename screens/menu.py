from kivy.uix.screenmanager import Screen
from core.logger import logger

class MenuScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ MenuScreen")

    def start_game(self):
        # สั่งให้ ScreenManager เปลี่ยนหน้าไปที่ 'gameplay'
        logger.info("กำลังเริ่มต้นเกม...")
        self.manager.current = 'gameplay'
