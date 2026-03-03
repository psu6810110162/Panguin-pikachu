from kivy.uix.screenmanager import Screen
from core.logger import logger

class PauseScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ Pause")
        
    def resume_game(self):
        logger.info("เล่นต่อ...")
        self.manager.current = 'gameplay'
        
    def restart_game(self):
        logger.info("เริ่มเกมใหม่จากหน้าจอ Pause...")
        self.manager.current = 'gameplay'
        
    def go_home(self):
        logger.info("กลับไปหน้าเมนูหลัก...")
        self.manager.current = 'menu'
