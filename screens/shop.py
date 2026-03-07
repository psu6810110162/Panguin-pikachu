from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock

class ShopScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ Shop")
        
    def go_back(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)
        
    def buy_item(self, item_id):
        AudioManager().play_sfx('tab')
        logger.info(f"ซื้อไอเทม {item_id} แล้ว!")
    def _go_menu(self):
        self.manager.current = 'menu'
