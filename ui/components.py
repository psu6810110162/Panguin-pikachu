from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class HoverButton(Button):
    """
    ปุ่มกดที่ขยายขนาดขึ้นเล็กน้อยเมื่อเอาเมาส์ไปวาง (Hover Effect)
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
        if inside and not self.hovering:
            self.on_enter()
        elif not inside and self.hovering:
            self.on_leave()

    def on_enter(self):
        if self.hovering:
            return
        self.hovering = True

        from infrastructure.audio import AudioManager

        AudioManager().play_sfx("switch")

        if self.size_hint_x is None or self.size_hint_y is None:
            if self.original_size is None:
                self.original_size = (self.width, self.height)
            Animation(
                size=(self.original_size[0] * 1.05, self.original_size[1] * 1.05),
                duration=0.1,
                t="out_quad",
            ).start(self)
        else:
            if self.original_size_hint is None:
                self.original_size_hint = (self.size_hint_x, self.size_hint_y)
            Animation(
                size_hint=(self.original_size_hint[0] * 1.05, self.original_size_hint[1] * 1.05),
                duration=0.1,
                t="out_quad",
            ).start(self)

    def on_leave(self):
        if not self.hovering:
            return
        self.hovering = False

        if self.size_hint_x is None or self.size_hint_y is None:
            if self.original_size:
                Animation(size=self.original_size, duration=0.1, t="out_quad").start(self)
        else:
            if self.original_size_hint:
                Animation(size_hint=self.original_size_hint, duration=0.1, t="out_quad").start(self)


class MeterBar(Widget):
    """แถบสถานะ (D1-B4) — วาดด้วย canvas ล้วน ไม่ต้องใช้ asset

    ยาวเต็ม width ตามสัดส่วน value/max_value; กะพริบเมื่อค่าเกิน warn_threshold
    เพื่อเตือนก่อนถึง game_over_at (ค่าจริงมาจาก RunMetrics ไม่ hardcode ในนี้)
    """

    value = NumericProperty(0.0)
    max_value = NumericProperty(100.0)
    warn_threshold = NumericProperty(80.0)
    bar_color = ListProperty([0.8, 0.2, 0.2, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._warning = False
        self._flash_anim = None
        with self.canvas:
            self._bg_color = Color(0, 0, 0, 0.45)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            self._fill_color = Color(*self.bar_color)
            self._fill_rect = Rectangle(pos=self.pos, size=(0, self.height))
        self.bind(pos=self._redraw, size=self._redraw, value=self._redraw)
        self.bind(max_value=self._redraw, bar_color=self._redraw)

    def _redraw(self, *_args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        ratio = 0.0 if self.max_value <= 0 else max(0.0, min(1.0, self.value / self.max_value))
        self._fill_rect.pos = self.pos
        self._fill_rect.size = (self.width * ratio, self.height)
        if not self._warning:
            self._fill_color.rgba = self.bar_color

        warning = self.value >= self.warn_threshold
        if warning and not self._warning:
            self._warning = True
            self._flash_anim = Animation(a=0.35, duration=0.35) + Animation(a=1.0, duration=0.35)
            self._flash_anim.repeat = True
            self._flash_anim.start(self._fill_color)
        elif not warning and self._warning:
            self._warning = False
            if self._flash_anim:
                self._flash_anim.cancel(self._fill_color)
                self._flash_anim = None
            self._fill_color.rgba = self.bar_color


class HudRail(BoxLayout):
    """Shared telemetry rail for distance, hearts, meters, and inventory."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.02, 0.05, 0.12, 0.88)
            self._panel = RoundedRectangle(pos=self.pos, size=self.size, radius=[14])
            Color(0.25, 0.75, 1.0, 0.6)
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 14),
                width=1.2,
            )
        self.bind(pos=self._redraw_panel, size=self._redraw_panel)

    def _redraw_panel(self, instance, _value):
        self._panel.pos = instance.pos
        self._panel.size = instance.size
        self._border.rounded_rectangle = (
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            14,
        )


class ChoiceCard(Label):
    """A single left/right decision card; emits no gameplay side effects."""

    accent = ListProperty([0.25, 0.85, 1.0, 1])

    def __init__(self, accent=None, **kwargs):
        if accent is not None:
            self.accent = accent
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.03, 0.08, 0.16, 0.96)
            self._panel = RoundedRectangle(pos=self.pos, size=self.size, radius=[18])
            self._accent = Color(*self.accent, 0.9)
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 18),
                width=1.5,
            )
        self.bind(pos=self._redraw_panel, size=self._redraw_panel, accent=self._redraw_accent)

    def _redraw_panel(self, instance, _value):
        self._panel.pos = instance.pos
        self._panel.size = instance.size
        self._border.rounded_rectangle = (
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            18,
        )

    def _redraw_accent(self, _instance, value):
        self._accent.rgba = (*value[:3], 0.9)


class DecisionCard(Label):
    """Centre card for one policy or boss question.

    The component only renders supplied text; the screen controller owns
    countdowns, input, and state transitions.
    """

    accent = ListProperty([0.35, 0.82, 1.0, 1])

    def __init__(self, accent=None, **kwargs):
        if accent is not None:
            self.accent = accent
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.03, 0.08, 0.16, 0.96)
            self._panel = RoundedRectangle(pos=self.pos, size=self.size, radius=[22])
            self._accent = Color(*self.accent, 0.75)
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 22),
                width=1.5,
            )
        self.bind(pos=self._redraw_panel, size=self._redraw_panel, accent=self._redraw_accent)

    def _redraw_panel(self, instance, _value):
        self._panel.pos = instance.pos
        self._panel.size = instance.size
        self._border.rounded_rectangle = (
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            22,
        )

    def _redraw_accent(self, _instance, value):
        self._accent.rgba = (*value[:3], 0.75)


class FeedbackToast(Label):
    """Short-lived post-choice explanation, visually distinct from telemetry."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.02, 0.08, 0.14, 0.92)
            self._panel = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
            Color(0.35, 0.9, 0.75, 0.7)
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 12),
                width=1.0,
            )
        self.bind(pos=self._redraw_panel, size=self._redraw_panel)

    def _redraw_panel(self, instance, _value):
        self._panel.pos = instance.pos
        self._panel.size = instance.size
        self._border.rounded_rectangle = (
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            12,
        )


class BossBanner(Label):
    """Stateful Carbon Baron banner; wave color is set by the screen controller."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.06, 0.03, 0.10, 0.9)
            self._panel = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._redraw_panel, size=self._redraw_panel)

    def _redraw_panel(self, instance, _value):
        self._panel.pos = instance.pos
        self._panel.size = instance.size


class StateOverlay(Label):
    """Reusable full-screen state message (respawn/victory/game-over)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.01, 0.03, 0.08, 0.78)
            self._panel = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._redraw_panel, size=self._redraw_panel)

    def _redraw_panel(self, instance, _value):
        self._panel.pos = instance.pos
        self._panel.size = instance.size


class ProgressRing(Widget):
    """Small code-native progress ring for protected recovery states."""

    progress = NumericProperty(0.0)
    ring_color = ListProperty([0.35, 0.9, 1.0, 1.0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._track_color = Color(0.15, 0.25, 0.35, 0.8)
            self._track = Line(width=3.0)
            self._progress_color = Color(*self.ring_color)
            self._progress = Line(width=5.0)
        self.bind(pos=self._redraw, size=self._redraw, progress=self._redraw)
        self.bind(ring_color=self._redraw_color)
        self._redraw()

    def _redraw_color(self, _instance, value):
        self._progress_color.rgba = value

    def _redraw(self, *_args):
        radius = max(1.0, min(self.width, self.height) * 0.42)
        center = (self.center_x, self.center_y)
        self._track.circle = (*center, radius, 0.0, 360.0)
        end_angle = -90.0 + max(0.0, min(1.0, self.progress)) * 360.0
        self._progress.circle = (*center, radius, -90.0, end_angle)


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
