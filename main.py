import kivy
# ตรวจสอบเวอร์ชันของ Kivy ที่จำเป็นต้องใช้
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder

# โหลดค่ากำหนดพื้นฐาน (Config) และระบบบันทึก (Logger)
from core.config import WINDOW_WIDTH, WINDOW_HEIGHT
from core.logger import logger
from ui.components import HoverButton, AnimatedSkin # noqa: F401

# นำเข้าคลาสหน้าจอ (Screens) ทั้งหมดของเกม
from screens.gameplay import GamePlayScreen
from screens.menu import MenuScreen
from screens.gameover import GameOverScreen
from screens.history import HistoryScreen
from screens.shop import ShopScreen
from core.database import DatabaseManager

# โหลดไฟล์ .kv ที่จัดเก็บดีไซน์และเลย์เอาต์ (Style Sheet)
Builder.load_file('style.kv')

class PenguinDashApp(App):
    """ คลาสหลักของแอปพลิเคชัน (Entry Point) """
    def build(self):
        # 1. เตรียมฐานข้อมูล SQLite (สร้าง Table ถ้ายังไม่มี)
        DatabaseManager().init_db()
        
        # 2. ตั้งขนาดหน้าต่างแอปตามที่กำหนดไว้ใน Config
        Window.size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # 3. สร้างตัวจัดการหน้าจอ (ScreenManager) เพื่อสลับระหว่างหน้าต่างๆ
        sm = ScreenManager()
        
        # 4. ลงทะเบียนหน้าจอต่างๆ เข้าสู่ระบบเพื่อเรียกใช้งานตามชื่อ (name)
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GamePlayScreen(name='gameplay'))
        sm.add_widget(GameOverScreen(name='gameover'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(ShopScreen(name='shop'))

        logger.info("เริ่มเปิดเข้าสู่เกม Penguin Dash")
        return sm

# ตรวจสอบว่าเป็นไฟล์หลักที่ถูกรันโดยตรงหรือไม่
if __name__ == '__main__':
    PenguinDashApp().run()
