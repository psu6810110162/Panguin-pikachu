from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock

class HistoryScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ History")
        
    def go_back(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_menu(self):
        self.manager.current = 'menu'
