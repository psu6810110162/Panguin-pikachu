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
        from core.state import StateManager
        AudioManager().play_sfx('tab')
        logger.info(f"เลือกใช้สกิน: {item_id}")
        
        # อัปเดต StateManager (ลอจิกคือเลือกปุ๊บใส่ปั๊บ)
        StateManager().selected_skin = item_id
        
    def _go_menu(self):
        self.manager.current = 'menu'
