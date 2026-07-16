import kivy

kivy.require("2.1.0")

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform

# โหลดค่าคอนฟิกขนาดหน้าจอ
from core.config import WINDOW_HEIGHT, WINDOW_WIDTH
from core.database import DatabaseManager
from core.logger import logger
from core.shop_catalog import load_shop_catalog
from core.state import StateManager
from screens.gameover import GameOverScreen

# โหลด Screens
from screens.gameplay import GamePlayScreen
from screens.history import HistoryScreen
from screens.menu import MenuScreen
from screens.pause import PauseScreen
from screens.report import ReportScreen
from screens.shop import ShopScreen
from ui.components import AnimatedSkin, HoverButton  # noqa: F401

# โหลดไฟล์ออกแบบ KV
Builder.load_file("style.kv")


class PenguinDashApp(App):
    def build(self):
        db = DatabaseManager()
        db.init_db()  # เตรียมฐานข้อมูลก่อนเริ่มเกม
        self._hydrate_equipped_skin(db)

        # ตั้งค่าขนาดหน้าจอคงที่เฉพาะ desktop dev/test — mobile (android/ios)
        # ต้องใช้ logical window ขนาดจริงของอุปกรณ์จากระบบ ไม่ใช่ค่านี้ ไม่งั้น
        # ui/responsive.py จะคำนวณ breakpoint จากขนาดหน้าต่างปลอมที่ไม่ตรงจอจริง
        if platform not in ("android", "ios"):
            Window.size = (WINDOW_WIDTH, WINDOW_HEIGHT)

        # ใส่ตัวจัดการหน้าจอ (State Machine)
        sm = ScreenManager()

        # เพิ่มหน้าจอต่างๆ
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(GamePlayScreen(name="gameplay"))
        sm.add_widget(GameOverScreen(name="gameover"))
        sm.add_widget(ReportScreen(name="report"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(ShopScreen(name="shop"))
        sm.add_widget(PauseScreen(name="pause"))

        logger.info("เริ่มเปิดเข้าสู่เกม Penguin Dash")
        return sm

    def _hydrate_equipped_skin(self, db: DatabaseManager) -> None:
        """Load the last-saved player's equipped skin into StateManager once,
        at startup — the in-memory default used to always be a hardcoded
        "Ninja Frog" and equip/purchase never persisted past a restart even
        though ``players.equipped_skin`` already existed as a DB column."""
        catalog = load_shop_catalog()
        player_name = db.get_last_player_name()
        db.ensure_default_skin(player_name, catalog.default_skin_id)

        equipped = db.get_equipped_skin(player_name)
        if not equipped or catalog.get(equipped) is None:
            # First run ever (column's SQL-level "default" placeholder) or a
            # stale id from a since-removed skin — fall back to the shop's
            # default and persist it so this branch is self-healing once.
            equipped = catalog.default_skin_id
            db.set_equipped_skin(player_name, equipped)
        StateManager().selected_skin = equipped


if __name__ == "__main__":
    PenguinDashApp().run()
