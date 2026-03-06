from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock

class GameOverScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ GameOver")

    def retry_game(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_gameplay(), 0.2)
        
    def view_history(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_history(), 0.2)
        
    def go_home(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_gameplay(self):
        self.manager.current = 'gameplay'
    

    def _go_history(self):
        self.manager.current = 'history'

    def _go_menu(self):
        self.manager.current = 'menu'
