from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.properties import BooleanProperty, StringProperty, NumericProperty

class HoverButton(Button):
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
        if inside and not self.hovering:
            self.on_enter()
        elif not inside and self.hovering:
            self.on_leave()

    def on_enter(self):
        if self.hovering: return
        self.hovering = True

        if self.size_hint_x is None or self.size_hint_y is None:
            if self.original_size is None:
                self.original_size = (self.width, self.height)
            Animation(
                size=(self.original_size[0] * 1.05, self.original_size[1] * 1.05),
                duration=0.1, t='out_quad'
            ).start(self)
        else:
            if self.original_size_hint is None:
                self.original_size_hint = (self.size_hint_x, self.size_hint_y)
            Animation(
                size_hint=(self.original_size_hint[0] * 1.05, self.original_size_hint[1] * 1.05),
                duration=0.1, t='out_quad'
            ).start(self)

    def on_leave(self):
        if not self.hovering: return
        self.hovering = False

        # ✅ เอาจาก feat/ui/menuscreen — รองรับทั้ง size และ size_hint
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


# ✅ เอาจาก develop — เก็บ AnimatedSkin ไว้ด้วย
class AnimatedSkin(Image):
    frame_index = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True
        Clock.schedule_interval(self.update_animation, 1.0 / 12.0)

    def on_source(self, instance, value):
        self.update_texture()

    def update_animation(self, dt):
        self.frame_index = (self.frame_index + 1) % 11
        self.update_texture()

    def update_texture(self):
        if not self.source:
            return
        try:
            from kivy.core.image import Image as CoreImage
            full_texture = CoreImage(self.source).texture
            self.texture = full_texture.get_region(self.frame_index * 32, 0, 32, 32)
        except Exception as e:
            print(f"Error updating animated skin texture: {e}")