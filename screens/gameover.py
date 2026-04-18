from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock
from core.database import DatabaseManager
from core.config import DEFAULT_PLAYER_NAME

class GameOverScreen(Screen):
    """ คลาสหน้าจอจบเกม (Game Over) """
    def on_enter(self):
        """ ทำงานเมื่อเข้าสู่หน้าจอ Game Over """
        logger.info("เข้าสู่หน้าจอ GameOver")
        db = DatabaseManager()
        
        # 1. ดึงชื่อผู้เล่นล่าสุดมาแสดงในช่องกรอกชื่อ (Auto-fill)
        last_name = db.get_last_player_name()
        if 'name_input' in self.ids:
            self.ids.name_input.text = last_name
        
        # 2. ดึงข้อมูลคะแนน (ระยะทางและเพชร) จากหน้า gameplay ล่าสุด
        try:
            gameplay = self.manager.get_screen('gameplay')
            self.distance = int(gameplay.grid.get_distance_m())
            self.gems = gameplay.gems_collected
        except Exception as e:
            logger.error(f"Error getting gameplay data: {e}")
            self.distance = 0
            self.gems = 0
        
        # แสดงผลระยะทางบนหน้าจอ
        if 'score_label' in self.ids:
            self.ids.score_label.text = f"DISTANCE: {self.distance} M"
        self._saved = False # สถานะว่าบันทึกข้อมูลลง Database หรือยัง

    def _save_data(self):
        """ ฟังก์ชันภายในสำหรับบันทึกข้อมูลการเล่นลง SQLite """
        if hasattr(self, '_saved') and self._saved: return # ป้องกันการบันทึกซ้ำ
        
        # ดึงชื่อจากช่อง Input ถ้าว่างให้ใช้ชื่อพื้นฐาน
        name = self.ids.name_input.text.strip() if 'name_input' in self.ids else DEFAULT_PLAYER_NAME
        if not name: name = DEFAULT_PLAYER_NAME
        
        try:
            db = DatabaseManager()
            # บันทึก Session การเล่น (ชื่อ, ระยะทาง, เพชร)
            db.save_game_session(name, distance=self.distance, gems=self.gems)
            logger.info(f"บันทึกข้อมูลเรียบร้อยสำหรับ {name}: {self.distance}m, {self.gems} gems")
            self._saved = True

        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def retry_game(self):
        """ ฟังก์ชันสำหรับกดเริ่มเล่นใหม่อีกครั้ง (Retry) """
        self._save_data() # บันทึกคะแนนรอบที่เพิ่งจบไปก่อน
        AudioManager().play_sfx('click')
        
        # รีเซ็ตสถานะเกมในหน้า Gameplay เพื่อให้พร้อมเริ่มรอบใหม่
        gameplay = self.manager.get_screen('gameplay')
        gameplay.grid.reset()
        gameplay.penguin.is_dead = False
        start_pos = gameplay.grid.path[0]
        gameplay.penguin.col = start_pos[0]
        gameplay.penguin.row = start_pos[1]
        gameplay.path_index = 0
        gameplay.gems_collected = 0 # รีเซ็ตเพชรที่เก็บได้
        
        # เปลี่ยนหน้าจอกลับไปที่ Gameplay
        Clock.schedule_once(lambda dt: self._go_gameplay(), 0.2)
        
    def view_history(self):
        """ ฟังก์ชันไปหน้าประวัติคะแนนสูงสุด """
        self._save_data()
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_history(), 0.2)
        
    def go_home(self):
        """ ฟังก์ชันกลับไปยังเมนูหลัก """
        self._save_data()
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_gameplay(self):
        self.manager.current = 'gameplay'

    def _go_history(self):
        self.manager.current = 'history'

    def _go_menu(self):
        self.manager.current = 'menu'
