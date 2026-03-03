from kivy.uix.screenmanager import Screen
from core.logger import logger

class ShopScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ Shop")
        
    def go_back(self):
        logger.info("กลับไปหน้าเมนูหลัก...")
        self.manager.current = 'menu'
        
    def buy_item(self, item_id):
        logger.info(f"สมมติว่าซื้อไอเทม: {item_id}")
