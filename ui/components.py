from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.properties import BooleanProperty, StringProperty, NumericProperty

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

class AnimatedSkin(Image):
    """
    Widget แสดงผล Skin ตัวละครแบบแอนิเมชัน (Idle)
    รองรับ Spritesheet 11 เฟรม (352x32)
    """
    frame_index = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True
        # เริ่มต้นแอนิเมชัน
        Clock.schedule_interval(self.update_animation, 1.0 / 12.0)

    def on_source(self, instance, value):
        # เมื่อเปลี่ยนรูป ให้รีเซ็ตเฟรม
        self.update_texture()

    def update_animation(self, dt):
        self.frame_index = (self.frame_index + 1) % 11
        self.update_texture()

    def update_texture(self):
        if not self.source:
            return
        
        # ตัดรูป (Region) จาก Spritesheet หลัก
        # สมมติว่าเฟรมละ 32x32
        try:
            from kivy.core.image import Image as CoreImage
            # โหลด texture หลัก
            full_texture = CoreImage(self.source).texture
            # ตัดเฉพาะเฟรมปัจจุบัน
            self.texture = full_texture.get_region(self.frame_index * 32, 0, 32, 32)
        except Exception as e:
            print(f"Error updating animated skin texture: {e}")
