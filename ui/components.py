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
        self.original_size = None

    def on_mouse_pos(self, window, pos):
        if not self.get_root_window():
            return
        
        inside = self.collide_point(*self.to_widget(*pos))
            
        # ตรวจสอบว่าเมาส์อยู่ในอาณาเขตของปุ่มหรือไม่
        if inside and not self.hovering:
            if not self.hovering:
                self.on_enter()
        else:
            if self.hovering:
                self.on_leave()

    def on_enter(self):
        if self.hovering: return
        self.hovering = True

        if self.size_hint_x is None or self.size_hint_y is None: # ปุ่มที่ใช้ size ปกติ → animate ด้วย size
            if self.original_size is None:
                self.original_size = (self.width, self.height)
            Animation(
                size=(self.original_size[0] * 1.05, self.original_size[1] * 1.05),
                duration=0.1, t='out_quad'
            ).start(self)
        else: # ปุ่มที่ใช้ size_hint → animate ด้วย size_hint
            if self.original_size_hint is None:
                self.original_size_hint = (self.size_hint_x, self.size_hint_y)
            Animation(
                size_hint=(self.original_size_hint[0] * 1.05, self.original_size_hint[1] * 1.05),
                duration=0.1, t='out_quad'
            ).start(self)

    def on_leave(self):
        if not self.hovering: return
        self.hovering = False
        
        if self.size_hint_x is None or self.size_hint_y is None:
            if self.original_size:
                Animation(
                    size=self.original_size,   # กลับขนาดที่เก็บไว้
                    duration=0.1, t='out_quad'
                ).start(self)
        else:
            if self.original_size_hint:
                Animation(
                    size_hint=self.original_size_hint,
                    duration=0.1, t='out_quad'
                ).start(self)
