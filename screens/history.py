from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen

from core.audio import AudioManager
from core.database import DatabaseManager
from core.logger import logger

KENNEY_FONT = "assets/Component_UI/Font/Kenney Future.ttf"
TROPHY_ICON = "assets/Component_UI/history/trophy_normal.png"


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
                    font_name=KENNEY_FONT,
                    size_hint_y=None,
                    height=50,
                )
            )
            return

        for i, row in enumerate(history, 1):
            dist = row["distance_m"]
            gems = row["gems_collected"]

            label_text = f"{i}. {dist} m ({gems} Gems)"

            row_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=8)
            row_box.add_widget(
                Label(
                    text=label_text,
                    font_name=KENNEY_FONT,
                    font_size="18sp",
                    color=(1, 1, 1, 0.9),
                )
            )
            if i == 1:
                # Personal-best marker as an image, not a "🏆" glyph: Kenney
                # Future has no emoji glyphs, so embedding one in Label text
                # renders a square/tofu box instead of a trophy.
                row_box.add_widget(
                    Image(
                        source=TROPHY_ICON,
                        size_hint=(None, None),
                        size=(32, 32),
                        allow_stretch=True,
                        keep_ratio=True,
                    )
                )
            self.ids.history_list.add_widget(row_box)

    def go_back(self):
        AudioManager().play_sfx("click")
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_menu(self):
        self.manager.current = "menu"
