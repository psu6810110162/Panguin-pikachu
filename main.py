import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder

# โหลดค่าคอนฟิกขนาดหน้าจอ
from core.config import WINDOW_WIDTH, WINDOW_HEIGHT
from core.logger import logger
from ui.components import HoverButton, AnimatedSkin # noqa: F401

# โหลด Screens
from screens.gameplay import GamePlayScreen
from screens.menu import MenuScreen
from screens.gameover import GameOverScreen
from screens.history import HistoryScreen
from screens.shop import ShopScreen
from screens.pause import PauseScreen
from core.database import DatabaseManager

# โหลดไฟล์ออกแบบ KV
Builder.load_file('style.kv')

class PenguinDashApp(App):
    def build(self):
        DatabaseManager().init_db()  # เตรียมฐานข้อมูลก่อนเริ่มเกม
        # ตั้งค่าขนาดหน้าจอให้เหมาะกับการทดสอบบน Desktop
        Window.size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # ใส่ตัวจัดการหน้าจอ (State Machine)
        sm = ScreenManager()
        
        # เพิ่มหน้าจอต่างๆ
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GamePlayScreen(name='gameplay'))
        sm.add_widget(GameOverScreen(name='gameover'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(ShopScreen(name='shop'))
        sm.add_widget(PauseScreen(name='pause'))
        
        logger.info("เริ่มเปิดเข้าสู่เกม Penguin Dash")
        return sm

if __name__ == '__main__':
    PenguinDashApp().run()
