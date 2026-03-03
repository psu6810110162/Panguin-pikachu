from kivy.uix.screenmanager import Screen
from core.logger import logger

class GameOverScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ GameOver")

    def retry_game(self):
        logger.info("เริ่มเล่นใหม่อีกครั้ง...")
        self.manager.current = 'gameplay'
        
    def view_history(self):
        logger.info("ไปหน้าประวัติการเล่น...")
        self.manager.current = 'history'
        
    def go_home(self):
        logger.info("กลับไปหน้าเมนูหลัก...")
        self.manager.current = 'menu'
