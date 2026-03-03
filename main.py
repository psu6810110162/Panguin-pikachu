import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder

# โหลดค่าคอนฟิกขนาดหน้าจอ
from core.config import WINDOW_WIDTH, WINDOW_HEIGHT
from core.logger import logger

# โหลด Screens
from screens.gameplay import GamePlayScreen

# โหลดไฟล์ออกแบบ KV
Builder.load_file('style.kv')

class PenguinDashApp(App):
    def build(self):
        # ตั้งค่าขนาดหน้าจอให้เหมาะกับการทดสอบบน Desktop
        Window.size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # ใส่ตัวจัดการหน้าจอ (State Machine)
        sm = ScreenManager()
        
        # เพิ่มหน้าจอต่างๆ
        sm.add_widget(GamePlayScreen(name='gameplay'))
        
        logger.info("เริ่มเปิดเข้าสู่เกม Penguin Dash")
        return sm

if __name__ == '__main__':
    PenguinDashApp().run()
