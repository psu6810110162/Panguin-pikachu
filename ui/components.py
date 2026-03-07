from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.properties import BooleanProperty

class HoverButton(Button):
    """
    ปุ่มกดที่ขยายขนาดขึ้นเล็กน้อยเมื่อเอาเมาส์ไปวาง (Hover Effect)
    อย่างเสถียร โดยเก็บค่าขนาดเริ่มต้นไว้
    """
    hovering = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.original_size_hint = None

    def on_mouse_pos(self, window, pos):
        if not self.get_root_window():
            return
            
        # ตรวจสอบว่าเมาส์อยู่ในอาณาเขตของปุ่มหรือไม่
        if self.collide_point(*self.to_widget(*pos)):
            if not self.hovering:
                self.on_enter()
        else:
            if self.hovering:
                self.on_leave()

    def on_enter(self):
        if self.hovering: return
        self.hovering = True
        
        # เก็บค่าขนาดเดิมไว้ถ้าเป็นครั้งแรก
        if self.original_size_hint is None:
            self.original_size_hint = (self.size_hint_x, self.size_hint_y)
            
        # ขยายจากขนาดเริ่มต้นเสมอ (เพื่อความเท่ากัน)
        target_x = self.original_size_hint[0] * 1.05
        target_y = self.original_size_hint[1] * 1.05
        Animation(size_hint=(target_x, target_y), duration=0.1, t='out_quad').start(self)

    def on_leave(self):
        if not self.hovering: return
        self.hovering = False
        
        if self.original_size_hint:
            # กลับสู่ขนาดเริ่มต้นที่แท้จริง
            Animation(size_hint=self.original_size_hint, duration=0.1, t='out_quad').start(self)
