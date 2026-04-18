from kivy.uix.button import Button
from kivy.core.window import Window
from core.logger import logger
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.properties import BooleanProperty, StringProperty, NumericProperty

class HoverButton(Button):
    """
    ปุ่มกดพิเศษที่จะขยายขนาดขึ้นเล็กน้อยเมื่อนำเมาส์ไปวางทับ (Hover Effect)
    เพื่อเพิ่มความรู้สึก Interactive ให้กับผู้เล่น
    """
    hovering = BooleanProperty(False) # สถานะว่าเมาส์กำลังวางทับอยู่หรือไม่

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.original_size_hint = None # เก็บค่าขนาดดั้งเดิม (แบบ Ratio)
        self.original_size = None      # เก็บค่าขนาดดั้งเดิม (แบบ Pixels)
        # Binding is managed by on_parent to avoid memory leaks

    def on_parent(self, widget, parent):
        """ Bind/unbind mouse tracking with the widget tree lifecycle """
        if parent is None:
            Window.unbind(mouse_pos=self.on_mouse_pos)
        else:
            Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, window, pos):
        """ ทำงานทุกครั้งที่เมาส์ขยับ เพื่อตรวจสอบว่าทับปุ่มหรือไม่ """
        if not self.get_root_window(): # ถ้าปุ่มไม่ได้ถูกแสดงผลอยู่ ให้ข้ามไป
            return
        # ตรวจสอบว่าตำแหน่งเมาส์ (pos) อยู่ภายในขอบเขตของ Widget หรือไม่
        inside = self.collide_point(*self.to_widget(*pos))
        if inside and not self.hovering:
            self.on_enter() # เมาส์เพิ่งเข้ามาทับ
        elif not inside and self.hovering:
            self.on_leave() # เมาส์เพิ่งออกไป

    def on_enter(self):
        """ เหตุการณ์เมื่อเมาส์เริ่มวางทับปุ่ม """
        if self.hovering: return
        self.hovering = True
        
        # เล่นเสียงสั้นๆ เมื่อเมาส์รูดผ่านปุ่ม
        from core.audio import AudioManager
        AudioManager().play_sfx('switch')

        # ขยายขนาดปุ่มให้ใหญ่ขึ้น 5% (1.05 เท่า)
        if self.size_hint_x is None or self.size_hint_y is None:
            # กรณีปุ่มระบุขนาดเป็น Pixels (Fixed Size)
            if self.original_size is None:
                self.original_size = (self.width, self.height)
            Animation(
                size=(self.original_size[0] * 1.05, self.original_size[1] * 1.05),
                duration=0.1, t='out_quad'
            ).start(self)
        else:
            # กรณีปุ่มระบุขนาดเป็น Ratio (Size Hint)
            if self.original_size_hint is None:
                self.original_size_hint = (self.size_hint_x, self.size_hint_y)
            Animation(
                size_hint=(self.original_size_hint[0] * 1.05, self.original_size_hint[1] * 1.05),
                duration=0.1, t='out_quad'
            ).start(self)

    def on_leave(self):
        """ เหตุการณ์เมื่อเมาส์ออกจากขอบเขตปุ่ม """
        if not self.hovering: return
        self.hovering = False

        # ปรับขนาดกลับสู่ค่าเริ่มต้น
        if self.size_hint_x is None or self.size_hint_y is None:
            if self.original_size:
                Animation(
                    size=self.original_size,
                    duration=0.1, t='out_quad'
                ).start(self)
        else:
            if self.original_size_hint:
                Animation(
                    size_hint=self.original_size_hint,
                    duration=0.1, t='out_quad'
                ).start(self)


class AnimatedSkin(Image):
    """
    Widget สำหรับแสดงภาพสกินตัวละครที่ขยับได้ (เช่น หน้า Shop)
    รองรับ Spritesheet แบบมาตรฐาน (11 เฟรมเรียงในแนวนอน)
    """
    frame_index = NumericProperty(0) # เฟรมปัจจุบันที่กำลังแสดง
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True
        self._cached_texture = None  # cache texture เพื่อไม่ต้องโหลดจาก disk ทุกเฟรม
        # ตั้งเวลาให้เปลี่ยนเฟรมแอนิเมชันทุกๆ 1/12 วินาที (12 FPS)
        Clock.schedule_interval(self.update_animation, 1.0 / 12.0)

    def on_source(self, instance, value):
        """ เมื่อมีการเปลี่ยนไฟล์ภาพต้นฉบับ ให้ล้าง cache และรีเซ็ตการแสดงผล """
        self._cached_texture = None  # clear cache เมื่อ source เปลี่ยน
        self.update_texture()

    def update_animation(self, dt):
        """ วนลูปเฟรมจาก 0 ถึง 10 (รวม 11 เฟรม) """
        self.frame_index = (self.frame_index + 1) % 11
        self.update_texture()

    def update_texture(self):
        """ สั่งดึงเฉพาะส่วนของภาพ (Texture Region) จากสไปร์ทชีทมาแสดงผล """
        if not self.source:
            return

        try:
            from kivy.core.image import Image as CoreImage
            # โหลด Texture ครั้งแรกเท่านั้น แล้ว cache ไว้ (ไม่โหลดซ้ำทุกเฟรม)
            if self._cached_texture is None:
                self._cached_texture = CoreImage(self.source).texture
            # ตัดเฉพาะช่อง (32x32 Pixels) ตามตำแหน่งเฟรมปัจจุบัน
            self.texture = self._cached_texture.get_region(self.frame_index * 32, 0, 32, 32)
        except Exception as e:
            logger.error(f"Error updating animated skin texture: {e}")
