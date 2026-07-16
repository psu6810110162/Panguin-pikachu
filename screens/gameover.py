from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

from core.audio import AudioManager
from core.database import DatabaseManager
from core.logger import logger
from core.messages import game_over_reason_text


class GameOverScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ GameOver")
        db = DatabaseManager()

        # 1. พรีฟิลชื่อล่าสุด
        last_name = db.get_last_player_name()
        if "name_input" in self.ids:
            self.ids.name_input.text = last_name

        # 2. ดึงข้อมูลจากหน้า gameplay
        try:
            gameplay = self.manager.get_screen("gameplay")
            self.distance = int(gameplay.grid.get_distance_m())
            self.gems = gameplay.gems_collected
            reason = gameplay.metrics.game_over_reason
            self.reason = game_over_reason_text(reason) if reason is not None else "ไม่ทราบสาเหตุ"
        except Exception as e:
            logger.error(f"Error getting gameplay data: {e}")
            self.distance = 0
            self.gems = 0
            self.reason = "ไม่ทราบสาเหตุ"

        # แสดงผลคะแนน
        if "score_label" in self.ids:
            self.ids.score_label.text = f"DISTANCE: {self.distance} M"
        if "reason_label" in self.ids:
            self.ids.reason_label.text = self.reason
        self._saved = False

    def _save_data(self):
        if hasattr(self, "_saved") and self._saved:
            return
        name = self.ids.name_input.text.strip() if "name_input" in self.ids else "Penguin"
        if not name:
            name = "Penguin"

        try:
            db = DatabaseManager()
            db.save_game_session(name, distance=self.distance, gems=self.gems)
            logger.info(f"บันทึกข้อมูลเรียบร้อยสำหรับ {name}: {self.distance}m, {self.gems} gems")
            self._saved = True

        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def retry_game(self):
        self._save_data()
        AudioManager().play_sfx("click")
        # รีเซ็ตสถานะเกมก่อนกลับไปเล่น
        gameplay = self.manager.get_screen("gameplay")
        gameplay.restart_game()

        Clock.schedule_once(lambda dt: self._go_gameplay(), 0.2)

    def view_history(self):
        self._save_data()
        AudioManager().play_sfx("click")
        Clock.schedule_once(lambda dt: self._go_history(), 0.2)

    def go_home(self):
        self._save_data()
        AudioManager().play_sfx("click")
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_gameplay(self):
        self.manager.current = "gameplay"

    def _go_history(self):
        self.manager.current = "history"

    def _go_menu(self):
        self.manager.current = "menu"
