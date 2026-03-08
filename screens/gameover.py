from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock
from core.database import DatabaseManager

class GameOverScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ GameOver")
        db = DatabaseManager()
        
        # 1. พรีฟิลชื่อล่าสุด
        last_name = db.get_last_player_name()
        self.ids.name_input.text = last_name
        
        # 2. ดึงข้อมูลระยะทาง
        gameplay = self.manager.get_screen('gameplay')
        self.distance = int(gameplay.grid.get_distance_m())
        self.gems = gameplay.gems_collected
        
        # แสดงผลคะแนนเบื้องต้น
        self.ids.score_label.text = f"DISTANCE: {self.distance} M"
        self._saved = False

    def _save_data(self):
        if self._saved: return
        name = self.ids.name_input.text.strip()
        if not name: name = "Penguin"
        
        try:
            db = DatabaseManager()
            db.save_game_session(name, distance=self.distance, gems=self.gems)
            logger.info(f"บันทึกข้อมูลเรียบร้อยสำหรับ {name}: {self.distance}m, {self.gems} gems")
            self._saved = True
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def retry_game(self):
        self._save_data()
        AudioManager().play_sfx('click')
        # รีเซ็ตสถานะเกมก่อนกลับไปเล่น
        gameplay = self.manager.get_screen('gameplay')
        gameplay.grid.reset()
        gameplay.penguin.is_dead = False
        start_pos = gameplay.grid.path[0]
        gameplay.penguin.col = start_pos[0]
        gameplay.penguin.row = start_pos[1]
        gameplay.path_index = 0
        gameplay.gems_collected = 0 # รีเซ็ตเพชรที่เก็บได้ในรอบใหม่
        
        Clock.schedule_once(lambda dt: self._go_gameplay(), 0.2)
        
    def view_history(self):
        self._save_data()
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_history(), 0.2)
        
    def go_home(self):
        self._save_data()
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_gameplay(self):
        self.manager.current = 'gameplay'

    def _go_history(self):
        self.manager.current = 'history'

    def _go_menu(self):
        self.manager.current = 'menu'
