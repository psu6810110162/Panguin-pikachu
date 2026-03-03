from kivy.uix.screenmanager import Screen
from core.logger import logger

class HistoryScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ History")
        
    def go_back(self):
        logger.info("กลับหน้าก่อนหน้า...")
        # กลับไปหน้าเมนูเป็นค่าเริ่มต้น (อาจจะต้องแก้ให้กลับไปหน้า GameOver ได้ด้วยหากมาจากหน้านั้น)
        self.manager.current = 'menu'
