import random
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.animation import Animation
from kivy.core.window import Window

from core import i18n
from game.quiz_manager import QUESTIONS

KF_FONT   = i18n.FONT_KF
THAI_FONT = i18n.FONT_THAI
_BTN_COLOR   = (0.18, 0.38, 0.72, 1)
_CLOSE_DELAY = 2.5


def _pick_question(biome_id: str) -> dict:
    pool = QUESTIONS.get(biome_id)
    if not pool:
        all_q = [q for qs in QUESTIONS.values() for q in qs]
        return random.choice(all_q)
    return random.choice(pool)


def _card_bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        widget._bg_rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[20])
    widget.bind(pos=lambda w, v: setattr(w._bg_rect, 'pos', v),
                size=lambda w, v: setattr(w._bg_rect, 'size', v))


def _header_bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        widget._hdr_rect = RoundedRectangle(pos=widget.pos, size=widget.size,
                                             radius=[20, 20, 0, 0])
    widget.bind(pos=lambda w, v: setattr(w._hdr_rect, 'pos', v),
                size=lambda w, v: setattr(w._hdr_rect, 'size', v))


class QuizPopup(FloatLayout):

    def __init__(self, on_close, biome_id="arctic", biome_name="❄  ARCTIC ICE", **kwargs):
        super().__init__(**kwargs)
        self._on_close = on_close
        self._answered = False

        lang        = i18n.get_language()
        q_data      = _pick_question(biome_id)
        question    = q_data.get('q_en' if lang == 'en' else 'q', q_data.get('q', ''))
        raw_choices = q_data.get('choices_en' if lang == 'en' else 'choices',
                                  q_data.get('choices', []))
        self._fact  = q_data.get('fact_en' if lang == 'en' else 'fact',
                                  q_data.get('fact', ''))

        correct_orig = q_data['answer']
        choices = list(enumerate(raw_choices))
        random.shuffle(choices)
        self._correct_btn_idx = next(
            i for i, (orig, _) in enumerate(choices) if orig == correct_orig
        )
        self._btns = []

        # ── Dim overlay ───────────────────────────────────────────────────────
        with self.canvas.before:
            Color(0, 0, 0, 0.72)
            self._bg = Rectangle(pos=(0, 0), size=Window.size)

        # ── Card (60% × 62% of window, centered) ─────────────────────────────
        anchor = AnchorLayout(
            anchor_x='center', anchor_y='center',
            size_hint=(1, 1),
        )
        self.add_widget(anchor)

        card = BoxLayout(
            orientation='vertical',
            size_hint=(0.60, 0.62),
            spacing=0,
        )
        _card_bg(card, (0.08, 0.14, 0.28, 0.96))
        anchor.add_widget(card)

        font      = THAI_FONT if lang == 'th' else KF_FONT
        biome_clean = biome_name.split('  ', 1)[-1] if '  ' in biome_name else biome_name
        header_text = f"{i18n.t('challenge')} — {biome_clean}"

        # ── Header ────────────────────────────────────────────────────────────
        header = BoxLayout(size_hint_y=None, height=64)
        _header_bg(header, (0.3, 0.7, 1.0, 0.65))
        header.add_widget(Label(
            text=header_text,
            font_name=KF_FONT, font_size='20sp', bold=True,
            color=(1, 1, 1, 1),
            halign='center', valign='middle',
            text_size=(None, None),
        ))
        card.add_widget(header)

        # ── Question ──────────────────────────────────────────────────────────
        q_box = BoxLayout(size_hint_y=1, padding=[28, 20, 28, 20])
        q_lbl = Label(
            text=question,
            font_name=font, font_size='24sp',
            color=(0.9, 0.95, 1, 1),
            halign='center', valign='middle',
        )
        q_lbl.bind(size=lambda w, v: setattr(w, 'text_size', v))
        q_box.add_widget(q_lbl)
        card.add_widget(q_box)

        # ── Choices ───────────────────────────────────────────────────────────
        n   = min(len(choices), 4)
        gap = 12

        if n <= 3:
            btn_row = BoxLayout(
                orientation='horizontal',
                size_hint_y=None, height=72,
                spacing=gap, padding=[gap, 0, gap, 0],
            )
            for i, (_, text) in enumerate(choices[:n]):
                btn = self._make_btn(text, font, i)
                btn_row.add_widget(btn)
            card.add_widget(btn_row)
        else:
            grid_box = BoxLayout(
                orientation='vertical',
                size_hint_y=None, height=160,
                spacing=gap, padding=[gap, 0, gap, 0],
            )
            for row in range(2):
                row_box = BoxLayout(orientation='horizontal', spacing=gap)
                for col in range(2):
                    idx = row * 2 + col
                    if idx < n:
                        btn = self._make_btn(choices[idx][1], font, idx)
                        row_box.add_widget(btn)
                grid_box.add_widget(row_box)
            card.add_widget(grid_box)

        # ── Fact label ───────────────────────────────────────────────────────
        self._fact_label = Label(
            text='',
            font_name=font, font_size='18sp',
            color=(0.7, 1.0, 0.7, 0),
            size_hint_y=None, height=100,
            halign='center', valign='middle',
            padding=[28, 8],
        )
        self._fact_label.bind(size=lambda w, v: setattr(w, 'text_size', v))
        card.add_widget(self._fact_label)

    def _make_btn(self, text, font, idx):
        btn = Button(
            text=text,
            font_name=font, font_size='17sp',
            background_normal='', background_color=_BTN_COLOR,
            color=(1, 1, 1, 1),
            halign='center', valign='middle',
        )
        btn.bind(size=lambda w, v: setattr(w, 'text_size', v))
        btn.bind(on_release=lambda b, i=idx: self._on_answer(i))
        self._btns.append(btn)
        return btn

    def _on_answer(self, idx):
        if self._answered:
            return
        self._answered = True

        correct = (idx == self._correct_btn_idx)
        gems    = 10 if correct else 0

        for i, btn in enumerate(self._btns):
            if i == self._correct_btn_idx:
                btn.background_color = (0.1, 0.7, 0.2, 1)
            elif i == idx and not correct:
                btn.background_color = (0.8, 0.1, 0.1, 1)
            btn.disabled = True

        prefix = i18n.t('quiz_correct_prefix', gems=gems) if correct else i18n.t('quiz_wrong_prefix')
        self._fact_label.text = prefix + self._fact
        fact_color = (0.7, 1.0, 0.7, 1) if correct else (1, 0.7, 0.7, 1)
        Animation(color=fact_color, duration=0.3).start(self._fact_label)

        Clock.schedule_once(lambda dt: self._on_close(gems), _CLOSE_DELAY)
