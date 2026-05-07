import random
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from core.logger import logger
from core.audio import AudioManager
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
    """หน้าจอจบเกม — แสดงคะแนน, เกร็ดความรู้, และตัวเลือกถัดไป"""

    def on_enter(self):
        """ดึงข้อมูลจาก gameplay และแสดงผล"""
        logger.info("เข้าสู่หน้าจอ GameOver")
        db = DatabaseManager()

        # Auto-fill ชื่อผู้เล่นล่าสุด
        if 'name_input' in self.ids:
            self.ids.name_input.text = db.get_last_player_name()

        # ดึงคะแนนจาก gameplay screen
        self.distance, self.gems = self._get_gameplay_score()

        if 'score_label' in self.ids:
            self.ids.score_label.text = f"AWARENESS INDEX: {self.distance} M"

        if 'climate_fact_label' in self.ids:
            self.ids.climate_fact_label.text = f"🌍  {self._pick_fact()}"

        self._saved = False

    # ── ฟังก์ชันช่วย (Private Helpers) ─────────────────────────────────────

    def _get_gameplay_score(self):
        """ดึงระยะทางและเพชรจาก gameplay screen"""
        try:
            gameplay = self.manager.get_screen('gameplay')
            return int(gameplay.grid.get_distance_m()), gameplay.gems_collected
        except Exception as e:
            logger.error(f"Error getting gameplay data: {e}")
            return 0, 0

    def _pick_fact(self):
        """เลือกเกร็ดความรู้ตาม biome ปัจจุบัน (fallback = random global fact)"""
        try:
            gameplay = self.manager.get_screen('gameplay')
            return random.choice(gameplay.biome_mgr.current.facts)
        except Exception:
            return random.choice(CLIMATE_FACTS)

    def _save_data(self):
        """บันทึก session ลง SQLite — ป้องกันการบันทึกซ้ำด้วย _saved flag"""
        if getattr(self, '_saved', False):
            return

        name = DEFAULT_PLAYER_NAME
        if 'name_input' in self.ids:
            name = self.ids.name_input.text.strip() or DEFAULT_PLAYER_NAME

        try:
            db = DatabaseManager()
            db.save_game_session(name, distance=self.distance, gems=self.gems)
            # บันทึก Quiz answers ที่สะสมไว้ระหว่างเล่น (ถ้ามี)
            try:
                gameplay = self.manager.get_screen('gameplay')
                for biome_id, q_idx, correct in gameplay._pending_quiz_answers:
                    db.save_quiz_answer(name, biome_id, q_idx, correct)
                gameplay._pending_quiz_answers = []
            except Exception:
                pass
            logger.info(f"บันทึก: {name} — {self.distance}m, {self.gems} gems")
            self._saved = True
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def _navigate(self, target: str):
        """บันทึกคะแนน → เล่นเสียง → เปลี่ยนหน้าจอ"""
        self._save_data()
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', target), 0.2)

    # ── Action handlers (เรียกจาก KV หรือปุ่ม) ──────────────────────────────

    def retry_game(self):
        """บันทึก → reset gameplay → กลับไปเล่นใหม่"""
        self._save_data()
        AudioManager().play_sfx('click')
        self.manager.get_screen('gameplay').restart_game()
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'gameplay'), 0.2)

    def view_history(self):
        """ไปหน้าประวัติคะแนน"""
        self._navigate('history')

    def go_home(self):
        """กลับเมนูหลัก"""
        self._navigate('menu')
