from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window

from core.i18n import get_language

BIOME_HEADER = {
    'arctic':   'Arctic Challenge!',
    'drought':  'Drought Challenge!',
    'flood':    'Flood Challenge!',
    'wildfire': 'Wildfire Challenge!',
}


# ─── colour palette ──────────────────────────────────────────
C_NAVY    = (0.06, 0.12, 0.26, 0.95)
C_ICE     = (0.22, 0.60, 0.88, 1.00)
C_GOLD    = (1.00, 0.80, 0.20, 1.00)
C_WHITE   = (1.00, 1.00, 1.00, 1.00)
C_GREEN   = (0.20, 0.80, 0.35, 1.00)
C_RED     = (0.90, 0.25, 0.20, 1.00)
C_DIM     = (0.70, 0.70, 0.70, 1.00)

QUIZ_TIMEOUT  = 10
THAI_FONT     = 'assets/Component_UI/Font/Thonburi.ttc'


class _ChoiceButton(Button):
    def __init__(self, label_text: str, **kwargs):
        super().__init__(**kwargs)
        self.text             = label_text
        self.font_name        = THAI_FONT
        self.font_size        = 18
        self.color            = C_WHITE
        self.background_color = (0, 0, 0, 0)
        self.size_hint_y      = None
        self.height           = 52
        self._normal_color    = C_ICE
        self._draw_bg(C_ICE)

    def _draw_bg(self, col):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*col)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self._refresh, size=self._refresh)
        self._current_color = col

    def _refresh(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._current_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

    def highlight(self, correct: bool):
        col = C_GREEN if correct else C_RED
        self._current_color = col
        self._refresh()

    def reset_color(self):
        self._current_color = self._normal_color
        self._refresh()


class QuizPopupWidget(FloatLayout):
    """
    Popup แสดง Quiz ระหว่างเล่น
    - ซ้อนบน gameplay renderer (opacity toggle)
    - ใช้ show(question, biome_id, callback) เพื่อเปิด
    - callback(correct: bool, question: dict, biome_id: str)
    - รองรับ 2 ภาษา ผ่าน core.i18n
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.opacity       = 0
        self.disabled      = True
        self._callback     = None
        self._question     = None
        self._biome_id     = None
        self._answered     = False
        self._timer_event  = None
        self._seconds_left = QUIZ_TIMEOUT

        self._build_ui()

    def _build_ui(self):
        with self.canvas.before:
            self._bg_color = Color(0, 0, 0, 0)
            self._bg_rect  = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._refresh_bg, size=self._refresh_bg)

        card = BoxLayout(
            orientation   = 'vertical',
            spacing       = 14,
            padding       = [30, 24, 30, 24],
            size_hint     = (None, None),
            size          = (640, 510),
        )
        self._card = card
        with card.canvas.before:
            Color(*C_NAVY)
            self._card_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[20])
            Color(0.22, 0.60, 0.88, 0.4)
            self._card_line = Line(
                rounded_rectangle=(card.x, card.y, card.width, card.height, 20),
                width=1.5,
            )
        card.bind(pos=self._refresh_card, size=self._refresh_card)

        # ── header row ────────────────────────────────────────
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)

        self._icon_lbl = Label(
            text      = 'Climate Challenge!',
            font_name = THAI_FONT,
            font_size = 20,
            color     = C_GOLD,
            bold      = True,
            size_hint = (1, 1),
            halign    = 'left',
            valign    = 'middle',
        )
        self._icon_lbl.bind(size=lambda w, _: setattr(w, 'text_size', w.size))

        self._timer_lbl = Label(
            text      = str(QUIZ_TIMEOUT),
            font_name = THAI_FONT,
            font_size = 22,
            color     = C_ICE,
            bold      = True,
            size_hint = (None, 1),
            width     = 48,
            halign    = 'right',
            valign    = 'middle',
        )
        self._timer_lbl.bind(size=lambda w, _: setattr(w, 'text_size', w.size))

        header.add_widget(self._icon_lbl)
        header.add_widget(self._timer_lbl)

        # ── question label ────────────────────────────────────
        self._q_lbl = Label(
            text       = '',
            font_name  = THAI_FONT,
            font_size  = 20,
            color      = C_WHITE,
            halign     = 'center',
            valign     = 'middle',
            size_hint  = (1, None),
            height     = 80,
        )
        self._q_lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))

        # ── choice buttons ────────────────────────────────────
        self._btns = []
        for i in range(3):
            btn = _ChoiceButton(label_text='', size_hint_x=1)
            btn.bind(on_press=lambda b, idx=i: self._on_choice(idx))
            self._btns.append(btn)

        # ── feedback label ─────────────────────────────────────
        self._fact_lbl = Label(
            text      = '',
            font_name = THAI_FONT,
            font_size = 16,
            color     = C_DIM,
            halign    = 'center',
            valign    = 'top',
            size_hint = (1, None),
            height    = 80,
        )
        self._fact_lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))

        card.add_widget(header)
        card.add_widget(self._q_lbl)
        for btn in self._btns:
            card.add_widget(btn)
        card.add_widget(self._fact_lbl)

        self.add_widget(card)

    def _refresh_bg(self, *_):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    def _refresh_card(self, card, _):
        self._card_rect.pos  = card.pos
        self._card_rect.size = card.size
        self._card_line.rounded_rectangle = (
            card.x, card.y, card.width, card.height, 20
        )

    # ─── public API ─────────────────────────────────────────────

    def show(self, question: dict, biome_id: str, callback):
        self._question    = question
        self._biome_id    = biome_id
        self._callback    = callback
        self._answered    = False
        self._seconds_left = QUIZ_TIMEOUT

        lang = get_language()
        is_en = (lang == 'en')

        # biome header
        self._icon_lbl.text = BIOME_HEADER.get(biome_id, 'Climate Challenge!')

        # question text
        self._q_lbl.text = question.get('q_en', question['q']) if is_en else question['q']

        # choice buttons
        choices = question.get('choices_en', question['choices']) if is_en else question['choices']
        for i, btn in enumerate(self._btns):
            btn.text = f"  {chr(65+i)}.  {choices[i]}"
            btn.reset_color()
            btn.disabled = False

        self._fact_lbl.text  = ''
        self._timer_lbl.text = str(QUIZ_TIMEOUT)
        self._timer_lbl.color = C_ICE

        # slide-in animation
        self.disabled = False
        self.opacity  = 1
        self._bg_color.rgba = (0, 0, 0, 0)
        Animation(a=0.65, duration=0.30).start(self._bg_color)

        cw, ch = self._card.size
        self._card.pos = ((Window.width - cw) / 2, Window.height + ch)
        cy_target = (Window.height - ch) / 2
        Animation(y=cy_target, duration=0.38, t='out_back').start(self._card)

        self._timer_event = Clock.schedule_interval(self._tick, 1.0)

    def _tick(self, dt):
        self._seconds_left -= 1
        self._timer_lbl.text = str(max(0, self._seconds_left))
        if self._seconds_left <= 3:
            self._timer_lbl.color = C_RED
        if self._seconds_left <= 0:
            self._on_timeout()

    def _on_choice(self, idx: int):
        if self._answered:
            return
        self._answered = True
        self._stop_timer()

        correct = (idx == self._question['answer'])
        self._btns[idx].highlight(correct)
        if not correct:
            self._btns[self._question['answer']].highlight(True)
        for btn in self._btns:
            btn.disabled = True

        lang = get_language()
        is_en = (lang == 'en')
        fact = self._question.get('fact_en', self._question.get('fact', '')) if is_en else self._question.get('fact', '')

        if correct:
            prefix = 'Correct!  ' if is_en else 'ถูกต้อง!  '
            self._fact_lbl.color = C_GREEN
        else:
            prefix = 'Wrong  ' if is_en else 'ไม่ถูกต้อง  '
            self._fact_lbl.color = C_RED

        self._fact_lbl.text = prefix + fact
        Clock.schedule_once(lambda dt: self._close(correct), 2.0)

    def _on_timeout(self):
        if self._answered:
            return
        self._answered = True
        self._stop_timer()
        for btn in self._btns:
            btn.disabled = True
        self._btns[self._question['answer']].highlight(True)

        lang = get_language()
        is_en = (lang == 'en')
        fact = self._question.get('fact_en', self._question.get('fact', '')) if is_en else self._question.get('fact', '')
        prefix = 'Time Up!  ' if is_en else 'หมดเวลา!  '
        self._fact_lbl.text  = prefix + fact
        self._fact_lbl.color = C_RED
        Clock.schedule_once(lambda dt: self._close(False), 2.0)

    def _close(self, correct: bool):
        slide_out = Animation(y=-(self._card.height + 50), duration=0.25, t='in_back')
        slide_out.bind(on_complete=lambda *_: self._finish(correct))
        slide_out.start(self._card)
        Animation(a=0, duration=0.25).start(self._bg_color)

    def _finish(self, correct: bool):
        self.disabled = True
        self.opacity  = 0
        if self._callback:
            self._callback(correct, self._question, self._biome_id)

    def _stop_timer(self):
        if self._timer_event:
            self._timer_event.cancel()
            self._timer_event = None
