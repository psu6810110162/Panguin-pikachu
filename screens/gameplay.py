from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

from core.logger import logger
from core.config import TARGET_FPS
from game.grid import GridManager
from game.penguin import Penguin

class KivyRenderer(Widget):
    """ตัวรับหน้าที่วาดภาพ Grid ลงหน้าจอ (แยกต่างหากจากการคำนวณ)"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def draw(self, grid_manager, penguin):
        self.canvas.clear()
        with self.canvas:
            # พื้นหลังชั่วคราว (สีท้องฟ้า)
            Color(0.2, 0.6, 0.8, 1)
            Rectangle(pos=self.pos, size=self.size)

            # วาดเส้นทางเดิน (จำลองด้วยฟังก์ชันพิกัด Isometric ง่ายๆ)
            Color(0.2, 0.8, 0.2, 1) # พื้นสี่เหลี่ยมสีเขียว
            for col, row in grid_manager.path:
                x, y = self.iso_to_screen(col, row)
                Rectangle(pos=(x, y), size=(80, 40))
                
            # วาดตัวละครเพนกวิน
            if not penguin.is_dead:
                Color(0, 0, 0, 1) # วาดเป็นกล่องสีดำแทนตัวเพนกวินชั่วคราว
                px, py = self.iso_to_screen(penguin.col, penguin.row)
                Rectangle(pos=(px + 20, py + 10), size=(40, 40))

    def iso_to_screen(self, col, row):
        """แปลงพิกัดตารางให้กลายเป็นมุมมองเฉียง 45 องศาบนหน้าจอ"""
        # ลดหลั่นค่าวาดให้ภาพลอยอยู่กลางจอ
        offset_x = Window.width / 2
        offset_y = 100
        
        # สูตร Isometric พื้นฐาน 
        screen_x = (col - row) * 40 + offset_x
        screen_y = (col + row) * 20 + offset_y
        return screen_x, screen_y


class GamePlayScreen(Screen):
    """หน้าจอหลักตอนวิ่ง หน้าที่คือเชื่อมการกดปุ่ม ขยับภาพ และวาดลูป"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid = GridManager()
        self.penguin = Penguin()
        
        # สร้างเส้นทางตั้งต้น
        self.grid.reset()
        
        self.renderer = KivyRenderer()
        self.add_widget(self.renderer)

        # ผูกอีเวนต์คีย์บอร์ด
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def on_enter(self):
        """เริ่มเกมตอนผู้เล่นเข้ามาหน้านี้"""
        logger.info("เข้าสู่หน้า GamePlay")
        # เรียกอัปเดตเกมที่ 60 FPS
        self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)

    def on_leave(self):
        """หยุดเกมเมื่อหนีจากหน้านี้"""
        if self.game_event:
            self.game_event.cancel()

    def update(self, dt):
        """Game Loop 60 เฟรมต่อวินาที"""
        if not self.penguin.is_dead:
            # เช็คว่าเดินตกแมพหรือยัง
            if not self.grid.is_on_path(self.penguin.col, self.penguin.row):
                self.penguin.die()
                logger.info(f"Game Over! วิ่งได้ {self.grid.get_distance_m()} เมตร")
                
        # วาดภาพใหม่ทุกเฟรม
        self.renderer.draw(self.grid, self.penguin)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.penguin.is_dead:
            return False
            
        # ควบคุมตัวละครเปลี่ยนเลนซ้ายขวาตามที่ Doc กำหนด 
        if keycode[1] == 'left':
            self.penguin.turn_left()
            self.penguin.move_forward() # ขยับทิศเลี้ยว
            self.grid.step_forward()    # แจ้งว่าเกมเคลื่อนไป 1 ช่อง
            return True
        elif keycode[1] == 'right':
            self.penguin.turn_right()
            self.penguin.move_forward()
            self.grid.step_forward()
            return True
        elif keycode[1] == 'up':
             # สมมุติปุ่มขึ้นคือวิ่งตรงไม่ได้เลี้ยว
            self.penguin.move_forward()
            self.grid.step_forward()
            return True
            
        return False
