import random
from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock
from core.database import DatabaseManager
from core.config import DEFAULT_PLAYER_NAME

CLIMATE_FACTS = [
    "Arctic sea ice has declined ~13% per decade since 1979.",
    "The Arctic warms 4× faster than the global average.",
    "2023 was Earth's hottest year in 125,000 years.",
    "Sea ice loss exposes darker ocean, absorbing more heat.",
    "Emperor penguins may be extinct by 2100 without action.",
    "Greenland loses ~280 billion tonnes of ice per year.",
    "Every 0.5°C of warming doubles the chance of ice-free summers.",
    "Permafrost thaw releases CO₂ trapped for thousands of years.",
    "Ocean heat content reached a record high in 2023.",
    "Limiting warming to 1.5°C saves 70% of coral reefs.",
    "Renewable energy is now cheaper than fossil fuels globally.",
    "1 billion people face water scarcity from glacier retreat.",
    "Antarctica lost 150 billion tonnes of ice per year in the 2010s.",
    "Arctic shipping routes open as sea ice retreats — a double-edged change.",
    "Planting trees and reducing meat consumption can cut emissions 30%.",
]

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
            self.ids.score_label.text = f"AWARENESS INDEX: {self.distance} M"
        if 'climate_fact_label' in self.ids:
            try:
                gameplay = self.manager.get_screen('gameplay')
                biome = gameplay.biome_mgr.current
                fact = random.choice(biome.facts)
            except Exception:
                fact = random.choice(CLIMATE_FACTS)
            self.ids.climate_fact_label.text = f"🌍  {fact}"
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
            # บันทึก Quiz answers ที่สะสมไว้ระหว่างเล่น
            try:
                gameplay = self.manager.get_screen('gameplay')
                for biome_id, q_idx, correct in gameplay._pending_quiz_answers:
                    db.save_quiz_answer(name, biome_id, q_idx, correct)
                gameplay._pending_quiz_answers = []
            except Exception:
                pass
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
        gameplay.gems_collected = 0
        gameplay.chaser.reset()
        
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
