import sys

if "--self-test" in sys.argv:
    from infrastructure.self_test import run_self_test

    raise SystemExit(run_self_test())

import kivy

kivy.require("2.1.0")

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.resources import resource_add_path
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager

# โหลดค่าคอนฟิกขนาดหน้าจอ
from core.config import WINDOW_HEIGHT, WINDOW_WIDTH
from infrastructure.crash_report import write_crash_report
from infrastructure.database import DatabaseManager
from infrastructure.logging_config import configure_file_logging, logger

# โหลดไฟล์ออกแบบ KV
from infrastructure.paths import resource_path, resource_root
from infrastructure.resources import validate_resources
from infrastructure.version import load_build_info
from screens.gameover import GameOverScreen

# โหลด Screens
from screens.gameplay import GamePlayScreen
from screens.history import HistoryScreen
from screens.menu import MenuScreen
from screens.pause import PauseScreen
from screens.report import ReportScreen
from screens.shop import ShopScreen
from ui.components import AnimatedSkin, HoverButton  # noqa: F401


class PenguinDashApp(App):
    def build(self):
        configure_file_logging()
        try:
            report = validate_resources()
            if report.pending_licenses:
                logger.warning("assets pending license review: %s", report.pending_licenses)

            resource_add_path(str(resource_root()))
            Builder.load_file(str(resource_path("style.kv")))

            database = DatabaseManager()
            database.init_db()
            if database.recovery_notice:
                logger.error(database.recovery_notice)

            Window.size = (WINDOW_WIDTH, WINDOW_HEIGHT)
            sm = ScreenManager()
            sm.add_widget(MenuScreen(name="menu"))
            sm.add_widget(GamePlayScreen(name="gameplay"))
            sm.add_widget(GameOverScreen(name="gameover"))
            sm.add_widget(ReportScreen(name="report"))
            sm.add_widget(HistoryScreen(name="history"))
            sm.add_widget(ShopScreen(name="shop"))
            sm.add_widget(PauseScreen(name="pause"))

            logger.info("เริ่มเปิดเข้าสู่เกม Penguin Dash")
            return sm
        except Exception as error:
            report_path = write_crash_report(error, build_info=load_build_info())
            logger.exception("fatal startup error; crash report: %s", report_path)
            return Label(
                text=(f"Penguin Dash could not start safely.\nCrash report: {report_path}"),
                halign="center",
            )


if __name__ == "__main__":
    PenguinDashApp().run()
