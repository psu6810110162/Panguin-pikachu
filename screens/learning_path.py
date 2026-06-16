from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window

from core.audio import AudioManager
from core.database import DatabaseManager
from core import i18n
from game.quiz_manager import QUESTIONS


QUESTIONS_PER_BIOME = 5
THAI_FONT = i18n.FONT_THAI
KF_FONT   = i18n.FONT_KF

# ── Biome metadata ────────────────────────────────────────────
BIOME_META = [
    {
        'id':    'arctic',
        'name':  'Arctic Ice',
        'color': (0.55, 0.85, 1.00, 1),
        'bar':   (0.22, 0.60, 0.88, 1),
        'strip': (0.22, 0.60, 0.88, 1),
    },
    {
        'id':    'drought',
        'name':  'Drought Zone',
        'color': (1.00, 0.72, 0.30, 1),
        'bar':   (0.90, 0.55, 0.10, 1),
        'strip': (0.90, 0.55, 0.10, 1),
    },
    {
        'id':    'flood',
        'name':  'Flood Surge',
        'color': (0.40, 0.80, 1.00, 1),
        'bar':   (0.10, 0.50, 0.90, 1),
        'strip': (0.10, 0.50, 0.90, 1),
    },
    {
        'id':    'wildfire',
        'name':  'Wildfire',
        'color': (1.00, 0.50, 0.15, 1),
        'bar':   (0.85, 0.25, 0.05, 1),
        'strip': (0.85, 0.25, 0.05, 1),
    },
]

BIOME_FACTS = {
    'arctic': {
        'th': 'อาร์กติกร้อนขึ้นเร็วกว่าค่าเฉลี่ยโลกถึง 4 เท่า\nเพราะปรากฏการณ์ Arctic Amplification\nซึ่งกระตุ้นให้น้ำแข็งละลายเร็วขึ้นเป็นทวีคูณ',
        'en': 'The Arctic warms 4× faster than the global average\ndue to the Arctic Amplification effect,\nwhich accelerates ice melt in a runaway feedback loop.',
    },
    'drought': {
        'th': 'ภายในปี 2050 ประชากรกว่า 5 พันล้านคน\nอาจเผชิญกับการขาดแคลนน้ำ\nจากภัยแล้งที่รุนแรงขึ้นทั่วโลก',
        'en': 'By 2050, over 5 billion people\nmay face water shortages\ndue to worsening global drought conditions.',
    },
    'flood': {
        'th': 'ระดับน้ำทะเลอาจสูงขึ้น 1 เมตรภายในปี 2100\nคุกคามเมืองชายฝั่งและประชากร\nกว่า 1 พันล้านคนทั่วโลก',
        'en': 'Sea levels could rise 1 meter by 2100,\nthreatening coastal cities and\nover 1 billion people worldwide.',
    },
    'wildfire': {
        'th': 'ไฟป่าปล่อย CO₂ จำนวนมาก\nทำให้โลกร้อนเร็วขึ้น สร้างวงจรป้อนกลับ\nที่ทำให้ไฟป่าเกิดบ่อยและรุนแรงขึ้นอีก',
        'en': 'Wildfires release massive amounts of CO₂,\naccelerating climate change and creating\na feedback loop of more frequent, intense fires.',
    },
}


def _border_color(correct):
    if correct == 0:
        return (0.35, 0.35, 0.45, 0.35)
    if correct >= QUESTIONS_PER_BIOME:
        return (0.20, 0.95, 0.45, 1.00)
    return (1.00, 0.85, 0.20, 0.90)


# ─── Animated bar fill ───────────────────────────────────────
class _BarFill(Widget):
    def __init__(self, color4, **kwargs):
        super().__init__(**kwargs)
        self._color4 = color4
        with self.canvas:
            Color(*color4)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[7])
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self._rect.pos  = self.pos
        self._rect.size = self.size


# ─── Facts Popup ─────────────────────────────────────────────
class FactsPopupWidget(FloatLayout):
    """Popup แสดง 5 climate facts ของ biome ที่เลือก"""

    C_NAVY = (0.06, 0.12, 0.26, 0.97)
    C_GOLD = (1.00, 0.80, 0.20, 1.00)
    C_WHITE = (1.00, 1.00, 1.00, 1.00)
    C_ICE   = (0.70, 0.90, 1.00, 1.00)
    C_DIM   = (0.72, 0.85, 1.00, 0.85)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.opacity  = 0
        self.disabled = True
        self._build_ui()

    def _build_ui(self):
        with self.canvas.before:
            self._bg_color = Color(0, 0, 0, 0)
            self._bg_rect  = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._refresh_bg, size=self._refresh_bg)

        self._card = BoxLayout(
            orientation = 'vertical',
            spacing     = 10,
            padding     = [32, 24, 32, 24],
            size_hint   = (None, None),
            size        = (700, 560),
        )
        card = self._card
        with card.canvas.before:
            Color(*self.C_NAVY)
            self._card_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[20])
            Color(0.22, 0.60, 0.88, 0.4)
            self._card_line = Line(
                rounded_rectangle=(card.x, card.y, card.width, card.height, 20),
                width=1.5,
            )
        card.bind(pos=self._refresh_card, size=self._refresh_card)

        self._title_lbl = Label(
            text      = '',
            font_name = THAI_FONT,
            font_size = 22,
            bold      = True,
            color     = self.C_GOLD,
            size_hint_y = None,
            height    = 44,
            halign    = 'center',
            valign    = 'middle',
        )
        self._title_lbl.bind(size=lambda w, _: setattr(w, 'text_size', w.size))
        card.add_widget(self._title_lbl)

        self._fact_labels = []
        for _ in range(5):
            lbl = Label(
                text      = '',
                font_name = THAI_FONT,
                font_size = 17,
                color     = self.C_DIM,
                size_hint_y = None,
                height    = 62,
                halign    = 'left',
                valign    = 'middle',
            )
            lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
            self._fact_labels.append(lbl)
            card.add_widget(lbl)

        # spacer
        card.add_widget(Widget(size_hint_y=1))

        close_btn = Button(
            text             = 'CLOSE',
            font_name        = KF_FONT,
            font_size        = 18,
            color            = (0.70, 0.92, 1.0, 1),
            background_color = (0, 0, 0, 0),
            background_normal= '',
            background_down  = '',
            size_hint_y      = None,
            height           = 48,
        )
        with close_btn.canvas.before:
            Color(0.10, 0.22, 0.42, 0.95)
            self._close_bg = RoundedRectangle(pos=close_btn.pos, size=close_btn.size, radius=[12])
        close_btn.bind(
            pos=lambda w, _: setattr(self._close_bg, 'pos', w.pos),
            size=lambda w, _: setattr(self._close_bg, 'size', w.size),
        )
        close_btn.bind(on_press=lambda _: self._close())
        card.add_widget(close_btn)

        self.add_widget(card)

    def _refresh_bg(self, *_):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    def _refresh_card(self, card, _):
        self._card_rect.pos  = card.pos
        self._card_rect.size = card.size
        self._card_line.rounded_rectangle = (card.x, card.y, card.width, card.height, 20)

    def show(self, biome_id: str, biome_name: str, biome_color):
        lang   = i18n.get_language()
        is_en  = (lang == 'en')
        label  = i18n.t('climate_facts')

        self._title_lbl.text  = f"{biome_name}  —  {label}"
        self._title_lbl.color = biome_color

        questions = QUESTIONS.get(biome_id, [])
        for idx, lbl in enumerate(self._fact_labels):
            if idx < len(questions):
                q = questions[idx]
                fact = q.get('fact_en', q.get('fact', '')) if is_en else q.get('fact', '')
                lbl.text  = f"  {idx+1}.  {fact}"
                lbl.color = self.C_DIM
            else:
                lbl.text = ''

        self.disabled = False
        self.opacity  = 1
        self._bg_color.rgba = (0, 0, 0, 0)
        Animation(a=0.65, duration=0.25).start(self._bg_color)

        cw, ch = self._card.size
        self._card.pos = ((Window.width - cw) / 2, Window.height + ch)
        cy = (Window.height - ch) / 2
        Animation(y=cy, duration=0.35, t='out_back').start(self._card)

    def _close(self):
        slide = Animation(y=-(self._card.height + 50), duration=0.22, t='in_back')
        slide.bind(on_complete=lambda *_: self._finish())
        slide.start(self._card)
        Animation(a=0, duration=0.22).start(self._bg_color)

    def on_touch_down(self, touch):
        if self.opacity == 0:
            return False
        super().on_touch_down(touch)
        return self.collide_point(*touch.pos)

    def _finish(self):
        self.disabled = True
        self.opacity  = 0


# ─── Confirm Dialog ──────────────────────────────────────────
class ConfirmDialogWidget(FloatLayout):
    """ยืนยัน/ยกเลิก — ใช้กับ Reset Progress"""

    C_NAVY = (0.06, 0.12, 0.26, 0.97)
    C_RED  = (0.90, 0.25, 0.20, 1.00)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.opacity  = 0
        self.disabled = True
        self._on_confirm = None
        self._build_ui()

    def _build_ui(self):
        with self.canvas.before:
            self._bg_color = Color(0, 0, 0, 0)
            self._bg_rect  = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._refresh_bg, size=self._refresh_bg)

        self._card = BoxLayout(
            orientation = 'vertical',
            spacing     = 20,
            padding     = [40, 32, 40, 32],
            size_hint   = (None, None),
            size        = (480, 220),
        )
        card = self._card
        with card.canvas.before:
            Color(*self.C_NAVY)
            self._card_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[18])
            Color(0.90, 0.25, 0.20, 0.5)
            self._card_line = Line(
                rounded_rectangle=(card.x, card.y, card.width, card.height, 18),
                width=1.5,
            )
        card.bind(pos=self._refresh_card, size=self._refresh_card)

        self._msg_lbl = Label(
            text      = '',
            font_name = THAI_FONT,
            font_size = 18,
            color     = (1.0, 0.85, 0.85, 1.0),
            size_hint_y = None,
            height    = 60,
            halign    = 'center',
            valign    = 'middle',
        )
        self._msg_lbl.bind(size=lambda w, _: setattr(w, 'text_size', w.size))
        card.add_widget(self._msg_lbl)

        btn_row = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=52)

        confirm_btn = Button(
            font_name        = THAI_FONT,
            font_size        = 17,
            color            = (1.0, 1.0, 1.0, 1),
            background_color = (0, 0, 0, 0),
            background_normal= '',
            background_down  = '',
        )
        with confirm_btn.canvas.before:
            Color(0.70, 0.15, 0.10, 1.0)
            self._conf_bg = RoundedRectangle(pos=confirm_btn.pos, size=confirm_btn.size, radius=[10])
        confirm_btn.bind(
            pos=lambda w, _: setattr(self._conf_bg, 'pos', w.pos),
            size=lambda w, _: setattr(self._conf_bg, 'size', w.size),
        )
        confirm_btn.bind(on_press=self._do_confirm)
        self._confirm_btn = confirm_btn

        cancel_btn = Button(
            font_name        = THAI_FONT,
            font_size        = 17,
            color            = (0.70, 0.92, 1.0, 1),
            background_color = (0, 0, 0, 0),
            background_normal= '',
            background_down  = '',
        )
        with cancel_btn.canvas.before:
            Color(0.10, 0.22, 0.42, 0.95)
            self._cancel_bg = RoundedRectangle(pos=cancel_btn.pos, size=cancel_btn.size, radius=[10])
        cancel_btn.bind(
            pos=lambda w, _: setattr(self._cancel_bg, 'pos', w.pos),
            size=lambda w, _: setattr(self._cancel_bg, 'size', w.size),
        )
        cancel_btn.bind(on_press=lambda _: self._close())
        self._cancel_btn = cancel_btn

        btn_row.add_widget(confirm_btn)
        btn_row.add_widget(cancel_btn)
        card.add_widget(btn_row)

        self.add_widget(card)

    def _refresh_bg(self, *_):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    def _refresh_card(self, card, _):
        self._card_rect.pos  = card.pos
        self._card_rect.size = card.size
        self._card_line.rounded_rectangle = (card.x, card.y, card.width, card.height, 18)

    def show(self, on_confirm):
        self._on_confirm = on_confirm
        self._msg_lbl.text   = i18n.t('reset_confirm')
        self._confirm_btn.text = i18n.t('confirm')
        self._cancel_btn.text  = i18n.t('cancel')

        self.disabled = False
        self.opacity  = 1
        self._bg_color.rgba = (0, 0, 0, 0)
        Animation(a=0.55, duration=0.20).start(self._bg_color)

        cw, ch = self._card.size
        self._card.pos = ((Window.width - cw) / 2, (Window.height - ch) / 2)
        self._card.opacity = 0
        Animation(opacity=1, duration=0.20).start(self._card)

    def _do_confirm(self, *_):
        self._close()
        if self._on_confirm:
            Clock.schedule_once(lambda dt: self._on_confirm(), 0.25)

    def _close(self):
        Animation(opacity=0, duration=0.18).start(self._card)
        anim = Animation(a=0, duration=0.18)
        anim.bind(on_complete=lambda *_: self._finish())
        anim.start(self._bg_color)

    def on_touch_down(self, touch):
        if self.opacity == 0:
            return False
        super().on_touch_down(touch)
        return self.collide_point(*touch.pos)

    def _finish(self):
        self.disabled = True
        self.opacity  = 0


# ─── BiomeCard ───────────────────────────────────────────────
class BiomeCard(BoxLayout):
    """Card แสดง progress + fact + action buttons"""

    def __init__(self, meta: dict, correct: int, total: int,
                 on_view_facts=None, **kwargs):
        super().__init__(
            orientation = 'vertical',
            spacing     = 8,
            padding     = [20, 14, 20, 14],
            **kwargs,
        )
        self._meta         = meta
        self._correct      = correct
        self._total        = total
        self._on_view_facts = on_view_facts
        self._fill_w       = None
        self._fill_ratio   = 0.0

        bc = _border_color(correct)
        with self.canvas.before:
            Color(0.06, 0.12, 0.26, 0.92)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[16])
            Color(*bc)
            self._border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, 16),
                width=2.0 if correct >= QUESTIONS_PER_BIOME else 1.5,
            )
        self.bind(pos=self._refresh_bg, size=self._refresh_bg)
        self._build()

    def _refresh_bg(self, *_):
        self._bg.pos    = self.pos
        self._bg.size   = self.size
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, 16)

    def _build(self):
        meta      = self._meta
        correct   = self._correct
        is_master = correct >= QUESTIONS_PER_BIOME
        lang      = i18n.get_language()
        is_en     = (lang == 'en')

        # Kivy BoxLayout vertical: first add_widget → top, last → bottom

        # 1. Header row → TOP
        header_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)

        strip = Widget(size_hint=(None, 1), width=8)
        with strip.canvas:
            Color(*meta['strip'])
            _strip_rect = RoundedRectangle(pos=strip.pos, size=strip.size, radius=[4])
        strip.bind(pos=lambda w, _: setattr(_strip_rect, 'pos', w.pos),
                   size=lambda w, _: setattr(_strip_rect, 'size', w.size))
        header_row.add_widget(strip)

        name_lbl = Label(
            text      = meta['name'],
            font_name = THAI_FONT,
            font_size = 23,
            bold      = True,
            color     = meta['color'],
            size_hint = (1, 1),
            halign    = 'left',
            valign    = 'middle',
        )
        name_lbl.bind(size=lambda w, _: setattr(w, 'text_size', w.size))
        header_row.add_widget(name_lbl)

        if self._total > 0:
            pct = int(correct * 100 / self._total) if self._total > 0 else 0
            acc_lbl = Label(
                text      = i18n.t('accuracy', pct=pct),
                font_name = THAI_FONT,
                font_size = 15,
                color     = (0.70, 0.90, 0.70, 0.85),
                size_hint = (None, 1),
                width     = 100,
                halign    = 'right',
                valign    = 'middle',
            )
            acc_lbl.bind(size=lambda w, _: setattr(w, 'text_size', w.size))
            header_row.add_widget(acc_lbl)

        self.add_widget(header_row)

        # 2. Fact preview → fills flexible space
        fact_text = BIOME_FACTS.get(meta['id'], {}).get('en' if is_en else 'th', '')
        fact_lbl = Label(
            text      = fact_text,
            font_name = THAI_FONT,
            font_size = 17,
            color     = (0.68, 0.88, 1.0, 0.72),
            size_hint_y = 1,
            halign    = 'left',
            valign    = 'top',
        )
        fact_lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))
        self.add_widget(fact_lbl)

        # 3. Stats row
        asked_str = i18n.t('asked_n', n=self._total) if self._total > 0 else i18n.t('not_asked')
        correct_str = i18n.t('correct_of', c=correct, t=QUESTIONS_PER_BIOME)
        stats_lbl = Label(
            text      = f"{correct_str}   •   {asked_str}",
            font_name = THAI_FONT,
            font_size = 16,
            color     = (0.65, 0.82, 1.0, 0.9),
            size_hint_y = None,
            height    = 30,
            halign    = 'left',
            valign    = 'middle',
        )
        stats_lbl.bind(size=lambda w, _: setattr(w, 'text_size', w.size))
        self.add_widget(stats_lbl)

        # 4. Progress bar
        bar_fl = FloatLayout(size_hint_y=None, height=14)

        track = Widget(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        with track.canvas:
            Color(0.15, 0.25, 0.40, 1)
            trk = RoundedRectangle(pos=track.pos, size=track.size, radius=[7])
        track.bind(pos=lambda w, _: setattr(trk, 'pos', w.pos),
                   size=lambda w, _: setattr(trk, 'size', w.size))
        bar_fl.add_widget(track)

        fill_ratio = min(correct / QUESTIONS_PER_BIOME, 1.0)
        self._fill_w = _BarFill(
            meta['bar'],
            pos_hint={'x': 0, 'center_y': 0.5},
            size_hint=(None, 1),
            width=0,
        )
        bar_fl.add_widget(self._fill_w)
        self._fill_ratio = fill_ratio
        bar_fl.bind(width=self._start_bar_anim)

        self.add_widget(bar_fl)

        # 5. Action row → BOTTOM
        action_row = BoxLayout(orientation='horizontal', spacing=12,
                               size_hint_y=None, height=50)

        facts_btn = Button(
            text             = i18n.t('view_facts'),
            font_name        = THAI_FONT,
            font_size        = 17,
            color            = (0.70, 0.92, 1.0, 1),
            background_color = (0, 0, 0, 0),
            background_normal= '',
            background_down  = '',
            size_hint_x      = 1,
        )
        with facts_btn.canvas.before:
            Color(0.12, 0.28, 0.50, 0.9)
            _fb_bg = RoundedRectangle(pos=facts_btn.pos, size=facts_btn.size, radius=[10])
        facts_btn.bind(
            pos=lambda w, _: setattr(_fb_bg, 'pos', w.pos),
            size=lambda w, _: setattr(_fb_bg, 'size', w.size),
        )
        if self._on_view_facts:
            facts_btn.bind(on_press=lambda _: self._on_view_facts(meta))
        action_row.add_widget(facts_btn)

        if is_master:
            badge_lbl = Label(
                text      = '  MASTER',
                font_name = THAI_FONT,
                font_size = 16,
                bold      = True,
                color     = (1.00, 0.85, 0.10, 1),
                size_hint_x = None,
                width     = 110,
                halign    = 'center',
                valign    = 'middle',
            )
            badge_lbl.bind(size=lambda w, _: setattr(w, 'text_size', w.size))
            pulse = (
                Animation(color=[0.20, 1.00, 0.45, 1], duration=0.75, t='in_out_sine') +
                Animation(color=[1.00, 0.85, 0.10, 1], duration=0.75, t='in_out_sine')
            )
            pulse.repeat = True
            pulse.start(badge_lbl)
            action_row.add_widget(badge_lbl)

        self.add_widget(action_row)

    def _start_bar_anim(self, bar_fl, width):
        if width <= 0:
            return
        bar_fl.unbind(width=self._start_bar_anim)
        target = width * self._fill_ratio
        Clock.schedule_once(
            lambda dt: Animation(width=target, duration=0.85, t='out_quad').start(self._fill_w),
            0.25,
        )


# ─── LearningPathScreen ──────────────────────────────────────
class LearningPathScreen(Screen):
    """หน้า Climate Report — แสดง Quiz progress แยกตาม Biome"""

    def on_enter(self):
        AudioManager().play_sfx('click')
        self._load_stats()
        self._refresh_static_text()
        self._ensure_overlays()

    def _ensure_overlays(self):
        """สร้าง overlay widgets ถ้ายังไม่มี (สร้างครั้งแรกเท่านั้น)"""
        if not hasattr(self, '_facts_popup'):
            self._facts_popup = FactsPopupWidget(size_hint=(1, 1))
            self.add_widget(self._facts_popup)

        if not hasattr(self, '_confirm_dialog'):
            self._confirm_dialog = ConfirmDialogWidget(size_hint=(1, 1))
            self.add_widget(self._confirm_dialog)

        if not hasattr(self, '_lang_btn'):
            self._lang_btn = Button(
                text             = i18n.t('toggle_lang'),
                font_name        = i18n.FONT_KF,
                font_size        = 14,
                bold             = True,
                color            = (0.20, 0.95, 0.55, 1),
                background_color = (0, 0, 0, 0),
                background_normal= '',
                background_down  = '',
                size_hint        = (None, None),
                size             = (70, 32),
                pos_hint         = {'right': 0.99, 'top': 0.99},
            )
            with self._lang_btn.canvas.before:
                Color(0.08, 0.22, 0.16, 0.90)
                self._lang_bg = RoundedRectangle(
                    pos=self._lang_btn.pos, size=self._lang_btn.size, radius=[8]
                )
                Color(0.20, 0.70, 0.45, 0.6)
                self._lang_line = Line(
                    rounded_rectangle=(
                        self._lang_btn.x, self._lang_btn.y,
                        self._lang_btn.width, self._lang_btn.height, 8
                    ),
                    width=1.0,
                )
            self._lang_btn.bind(
                pos=self._refresh_lang_btn,
                size=self._refresh_lang_btn,
            )
            self._lang_btn.bind(on_press=self._toggle_language)
            self.add_widget(self._lang_btn)

        if not hasattr(self, '_reset_btn'):
            self._reset_btn = Button(
                text             = i18n.t('reset'),
                font_name        = THAI_FONT,
                font_size        = 14,
                color            = (1.0, 0.55, 0.55, 1),
                background_color = (0, 0, 0, 0),
                background_normal= '',
                background_down  = '',
                size_hint        = (None, None),
                size             = (80, 32),
                pos_hint         = {'x': 0.01, 'top': 0.99},
            )
            with self._reset_btn.canvas.before:
                Color(0.25, 0.06, 0.06, 0.85)
                self._reset_bg = RoundedRectangle(
                    pos=self._reset_btn.pos, size=self._reset_btn.size, radius=[8]
                )
            self._reset_btn.bind(
                pos=lambda w, _: setattr(self._reset_bg, 'pos', w.pos),
                size=lambda w, _: setattr(self._reset_bg, 'size', w.size),
            )
            self._reset_btn.bind(on_press=self._on_reset_press)
            self.add_widget(self._reset_btn)

    def _refresh_lang_btn(self, *_):
        self._lang_bg.pos   = self._lang_btn.pos
        self._lang_bg.size  = self._lang_btn.size
        self._lang_line.rounded_rectangle = (
            self._lang_btn.x, self._lang_btn.y,
            self._lang_btn.width, self._lang_btn.height, 8
        )

    def _toggle_language(self, *_):
        lang = 'en' if i18n.get_language() == 'th' else 'th'
        i18n.set_language(lang)
        self._lang_btn.text = i18n.t('toggle_lang')
        self._refresh_static_text()
        self._load_stats()

    def _refresh_static_text(self):
        """อัปเดตข้อความ static ที่อยู่ใน style.kv ตาม language ปัจจุบัน"""
        font = i18n.get_font()
        subtitle = self.ids.get('subtitle_lbl')
        if subtitle:
            subtitle.text      = i18n.t('subtitle')
            subtitle.font_name = font
        back = self.ids.get('back_btn')
        if back:
            back.text      = i18n.t('back')
            back.font_name = font
        if hasattr(self, '_reset_btn'):
            self._reset_btn.text      = i18n.t('reset')
            self._reset_btn.font_name = font

    def _load_stats(self):
        db    = DatabaseManager()
        name  = db.get_last_player_name()
        stats = db.get_quiz_stats(name)

        # ── Global score label ─────────────────────────────
        score_lbl = self.ids.get('global_score_lbl')
        if score_lbl:
            total_correct  = sum(d.get('correct', 0) for d in stats.values())
            total_asked    = sum(d.get('total',   0) for d in stats.values())
            total_possible = len(BIOME_META) * QUESTIONS_PER_BIOME
            if total_asked == 0:
                score_lbl.text  = i18n.t('no_quiz')
                score_lbl.color = (0.6, 0.6, 0.7, 0.8)
            else:
                pct = total_correct * 100 // total_possible
                score_lbl.text  = i18n.t('total_score', c=total_correct, t=total_possible, pct=pct)
                r = max(0.2, 1.0 - pct / 100)
                g = min(1.0, 0.3 + pct / 100)
                score_lbl.color = (r, g, 0.3, 1.0)

        # ── Biome cards ────────────────────────────────────
        grid = self.ids.get('biome_grid')
        if not grid:
            return
        grid.clear_widgets()
        for meta in BIOME_META:
            biome_data = stats.get(meta['id'], {'correct': 0, 'total': 0})
            correct    = biome_data.get('correct', 0)
            total      = biome_data.get('total',   0)
            card = BiomeCard(
                meta          = meta,
                correct       = correct,
                total         = total,
                size_hint     = (1, 1),
                on_view_facts = self._show_facts,
            )
            grid.add_widget(card)

    def _show_facts(self, meta: dict):
        AudioManager().play_sfx('click')
        self._facts_popup.show(meta['id'], meta['name'], meta['color'])

    def _on_reset_press(self, *_):
        self._confirm_dialog.show(on_confirm=self._do_reset)

    def _do_reset(self):
        db   = DatabaseManager()
        name = db.get_last_player_name()
        db.reset_quiz_progress(name)
        self._load_stats()

    def go_back(self):
        AudioManager().play_sfx('click')
        self.manager.current = 'menu'
