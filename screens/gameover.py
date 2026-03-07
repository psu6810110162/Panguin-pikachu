from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock

class GameOverScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ GameOver")
        # ดึงระยะทางจากหน้า gameplay มาแสดง
        gameplay = self.manager.get_screen('gameplay')
        distance = gameplay.grid.get_distance_m()
        self.ids.score_label.text = f"DISTANCE: {distance} M"

    def retry_game(self):
        AudioManager().play_sfx('click')
        # รีเซ็ตสถานะเกมก่อนกลับไปเล่น
        gameplay = self.manager.get_screen('gameplay')
        gameplay.grid.reset()
        gameplay.penguin.is_dead = False
        start_pos = gameplay.grid.path[0]
        gameplay.penguin.col = start_pos[0]
        gameplay.penguin.row = start_pos[1]
        gameplay.path_index = 0
        
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
