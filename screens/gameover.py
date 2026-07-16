from kivy.clock import Clock
from kivy.uix.screenmanager import Screen

from core.messages import game_over_reason_text
from infrastructure.audio import AudioManager
from infrastructure.logging_config import logger
from infrastructure.repository import LocalCompletedRunRepository
from infrastructure.telemetry import TelemetryRecorder
from infrastructure.version import APP_VERSION


class GameOverScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ GameOver")
        repository = LocalCompletedRunRepository()

        # 1. พรีฟิลชื่อล่าสุด
        last_name = repository.last_player_name()
        if "name_input" in self.ids:
            self.ids.name_input.text = last_name

        # 2. ดึงข้อมูลจากหน้า gameplay
        try:
            gameplay = self.manager.get_screen("gameplay")
            snapshot = gameplay.controller.view_state()
            self.terminal_result = gameplay.controller.take_terminal_result()
            if self.terminal_result is None:
                self.terminal_result = gameplay.controller.finish(snapshot.terminal_reason)
            self.distance = self.terminal_result.distance_m
            self.gems = self.terminal_result.gems
            reason = self.terminal_result.reason
            self.reason = game_over_reason_text(reason) if reason is not None else "ไม่ทราบสาเหตุ"
        except Exception as e:
            logger.error(f"Error getting gameplay data: {e}")
            self.distance = 0
            self.gems = 0
            self.reason = "ไม่ทราบสาเหตุ"

        try:
            TelemetryRecorder().record(
                build_version=APP_VERSION,
                play_duration_s=round(gameplay.session.elapsed(), 3),
                terminal_reason=reason.value if reason is not None else "unknown",
            )
        except Exception as error:
            logger.exception("Optional telemetry could not be recorded: %s", error)

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
            repository = LocalCompletedRunRepository()
            repository.save_completed_run(name, self.terminal_result)
            gameplay = self.manager.get_screen("gameplay")
            gameplay.controller.set_recoverable_error(None)
            logger.info(f"บันทึกข้อมูลเรียบร้อยสำหรับ {name}: {self.distance}m, {self.gems} gems")
            self._saved = True

        except Exception as e:
            logger.exception("Error saving Game Run: %s", e)
            gameplay = self.manager.get_screen("gameplay")
            notice = "บันทึกไม่สำเร็จ เกมยังเล่นต่อได้ กรุณาตรวจ error.log"
            gameplay.controller.set_recoverable_error(notice)
            if "reason_label" in self.ids:
                self.ids.reason_label.text = f"{self.reason}\n{notice}"

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
