from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from infrastructure.audio import AudioManager
from infrastructure.database import DatabaseManager
from infrastructure.logging_config import logger


class HistoryScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ History")
        self.load_history()

    def load_history(self):
        # ล้างข้อมูลเดิมก่อน
        self.ids.history_list.clear_widgets()

        db = DatabaseManager()
        # เรียงจากคะแนนดีสุดก่อนแล้ว (get_history), แถวแรกคือ PB จริงเสมอ
        history = db.get_history(db.get_last_player_name())  # ดึงมา 100 ตาม default ใหม่

        if not history:
            self.ids.history_list.add_widget(
                Label(
                    text="NO HISTORY YET",
                    font_name="assets/Component_UI/Font/Kenney Future.ttf",
                    size_hint_y=None,
                    height=50,
                )
            )
            return

        for i, row in enumerate(history, 1):
            dist = row["distance_m"]
            gems = row["gems_collected"]

            award = " 🏆" if i == 1 else ""

            label_text = f"{i}. {dist} m ({gems} Gems){award}"

            self.ids.history_list.add_widget(
                Label(
                    text=label_text,
                    font_name="assets/Component_UI/Font/Kenney Future.ttf",
                    font_size="18sp",
                    size_hint_y=None,
                    height=50,
                    color=(1, 1, 1, 0.9),
                )
            )

    def go_back(self):
        AudioManager().play_sfx("click")
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_menu(self):
        self.manager.current = "menu"
