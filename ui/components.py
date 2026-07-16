from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from core.shop_catalog import ShopItemState, SkinDefinition, action_label, is_action_enabled

KENNEY_FONT = "assets/Component_UI/Font/Kenney Future.ttf"
_SHOP_BUTTON_NORMAL = "assets/Component_UI/PNG/Blue/Default/button_rectangle_depth_gradient.png"
_SHOP_BUTTON_DOWN = "assets/Component_UI/PNG/Blue/Default/button_rectangle_gradient.png"


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

        from core.audio import AudioManager

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


class PassiveOverlay(Widget):
    """Full-screen decorative widget that never participates in touch dispatch.

    Kivy's default ``Widget.on_touch_down`` consumes any touch that collides
    with a ``disabled`` widget regardless of ``opacity`` (see
    ``kivy.uix.widget.Widget.on_touch_down``). A full-screen dimmer/scrim built
    from a plain ``disabled=True`` ``Widget`` therefore silently swallows every
    touch anywhere on screen — including buttons added earlier in the tree —
    even while it is invisible. Decorative overlays that never need to gate
    interaction (e.g. the decision-phase dim backdrop, which must let the
    left/right choice buttons underneath keep working) must use this class
    instead of relying on ``disabled`` for hit testing.
    """

    def on_touch_down(self, touch):
        return False

    def on_touch_move(self, touch):
        return False

    def on_touch_up(self, touch):
        return False


class FocusableIconButton(FocusBehavior, HoverButton):
    """Icon-only (or icon+caption) button with an explicit semantic contract.

    Kivy has no ARIA/accessibility tree, so ``aria-label`` has no Kivy
    equivalent to set. ``accessibility_label`` is the hook a future
    mobile/screen-reader bridge would read instead: it always carries a
    human-readable description even when ``text`` is empty (e.g. a
    pause-icon-only button). ``FocusBehavior`` adds Tab focus traversal, and
    ``keyboard_on_key_down`` maps Enter/Space to activation, matching native
    button semantics as closely as Kivy allows for mouse/touch-first UI.

    ``keyboard_mode="managed"`` is required on gameplay HUD buttons: the
    default ``"auto"`` mode calls ``Window.request_keyboard`` on focus,
    which releases whatever owns the keyboard (GamePlayScreen's arrow
    bindings) and leaves movement dead until the next ``on_enter``.
    Managed mode still allows Tab focus and Enter/Space via
    ``show_keyboard()`` if a screen explicitly wants that — it just never
    steals the exclusive keyboard on its own.
    """

    accessibility_label = StringProperty("")

    def __init__(self, **kwargs):
        # Default FocusBehavior keyboard_mode is "auto", which steals the
        # exclusive Window keyboard on focus and breaks GamePlayScreen arrow
        # bindings. Force managed mode before super() so FocusBehavior never
        # auto-requests a keyboard for these icon buttons.
        kwargs.setdefault("keyboard_mode", "managed")
        super().__init__(**kwargs)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if keycode[1] in ("enter", "numpadenter", "spacebar"):
            self.dispatch("on_press")
            self.dispatch("on_release")
            return True
        return super().keyboard_on_key_down(window, keycode, text, modifiers)


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
    """Reusable full-screen state message (respawn/victory/game-over).

    Gates touch consumption on ``opacity`` explicitly (same contract as
    :class:`PauseOverlay`/``HowToPlayOverlay``) instead of ``disabled`` +
    hit-testing, so a hidden overlay never blocks buttons underneath while an
    active one still absorbs touch-through for the message it is showing.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.01, 0.03, 0.08, 0.78)
            self._panel = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._redraw_panel, size=self._redraw_panel)

    def _redraw_panel(self, instance, _value):
        self._panel.pos = instance.pos
        self._panel.size = instance.size

    def on_touch_down(self, touch):
        if self.opacity == 0:
            return False
        super().on_touch_down(touch)
        return True

    def on_touch_move(self, touch):
        if self.opacity == 0:
            return False
        super().on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        if self.opacity == 0:
            return False
        super().on_touch_up(touch)
        return True


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


class ShopCard(BoxLayout):
    """Renders one catalog skin's current state (preview/name/price/action).

    Pure presentation: it renders whatever :class:`~core.shop_catalog.ShopItemState`
    it is given via :meth:`apply_state` and dispatches ``on_action`` on tap —
    it never reads or writes the database or ``StateManager`` itself. Replaces
    the 4 hand-duplicated card blocks that used to live in style.kv, one per
    skin, so a catalog change (add/remove/reprice a skin) never touches KV.
    """

    __events__ = ("on_action",)

    def __init__(self, skin: SkinDefinition, **kwargs: object) -> None:
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("padding", [dp(14), dp(14), dp(14), dp(12)])
        kwargs.setdefault("spacing", dp(8))
        super().__init__(**kwargs)
        self.skin = skin

        with self.canvas.before:
            Color(0.2, 0.2, 0.3, 0.9)
            self._panel = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
        self.bind(pos=self._redraw_panel, size=self._redraw_panel)
        self.bind(minimum_height=self.setter("height"))

        self.preview = AnimatedSkin(source=skin.preview_sheet, size_hint_y=None, height=dp(96))
        self.title_label = Label(
            text=skin.display_name,
            font_name=KENNEY_FONT,
            font_size="14sp",
            size_hint_y=None,
            height=dp(22),
        )
        self.action_button = HoverButton(
            font_name=KENNEY_FONT,
            font_size="14sp",
            size_hint=(1, None),
            height=dp(44),
            background_normal=_SHOP_BUTTON_NORMAL,
            background_down=_SHOP_BUTTON_DOWN,
            border=(10, 10, 10, 10),
        )
        self.action_button.bind(on_release=lambda _instance: self.dispatch("on_action"))

        self.add_widget(self.preview)
        self.add_widget(self.title_label)
        self.add_widget(self.action_button)

    def _redraw_panel(self, instance: object, _value: object) -> None:
        self._panel.pos = self.pos
        self._panel.size = self.size

    def apply_state(self, state: ShopItemState) -> None:
        """Update button label/enabled-ness/tint for the resolved card state.

        Colors mirror the pre-existing Shop palette (green = equipped, grey =
        locked, white = actionable) — not new art-direction colors.
        """
        self.action_button.text = action_label(self.skin, state)
        self.action_button.disabled = not is_action_enabled(state)
        if state is ShopItemState.EQUIPPED:
            self.action_button.background_color = (0.2, 0.8, 0.2, 1)
        elif state is ShopItemState.LOCKED:
            self.action_button.background_color = (0.55, 0.55, 0.55, 1)
        else:
            self.action_button.background_color = (1, 1, 1, 1)

    def apply_scale(self, scale: float) -> None:
        """Shrink preview/title/button proportionally on compact breakpoints
        while keeping the button no shorter than the 44dp minimum touch
        target regardless of how small ``scale`` gets."""
        self.preview.height = dp(96) * scale
        self.title_label.height = dp(22) * scale
        self.title_label.font_size = f"{max(12, 14 * scale):.0f}sp"
        self.action_button.height = max(dp(44), dp(44) * scale)
        self.action_button.font_size = f"{max(12, 14 * scale):.0f}sp"

    def on_action(self) -> None:
        """Default handler for the ``on_action`` event — intentionally a
        no-op; the screen binds its own listener via ``card.bind(on_action=...)``."""
