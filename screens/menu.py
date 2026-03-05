from kivy.uix.screenmanager import Screen
from core.audio import AudioManager
from core.logger import logger

class MenuScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ MenuScreen")
        AudioManager().play_bgm('Bgm.gameplay.mp3')

    def start_game(self):
        AudioManager().play_sfx('click')
        # สั่งให้ ScreenManager เปลี่ยนหน้าไปที่ 'gameplay'
        logger.info("กำลังเริ่มต้นเกม...")
        self.manager.current = 'gameplay'
    
    def go_to_history(self):
        AudioManager().play_sfx('click')
        logger.info("ไปที่หน้าประวัติการเล่น...")
        self.manager.current = 'history'

    def go_to_shop(self):
        AudioManager().play_sfx('click')
        logger.info("ไปที่หน้าร้านค้า...")
        self.manager.current = 'shop'

    def exit_game(self):
        AudioManager().play_sfx('click')
        from kivy.app import App
        App.get_running_app().stop()
