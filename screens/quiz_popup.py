import random
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.animation import Animation
from kivy.core.window import Window

# ── Constants ────────────────────────────────────────────────────────────────
_FONT       = 'assets/Component_UI/Font/Kenney Future.ttf'
_CARD_W     = 680
_CARD_H     = 420
_HEADER_H   = 54
_BTN_H      = 68
_BTN_COLOR  = (0.18, 0.38, 0.72, 1)
_CLOSE_DELAY = 2.2   # วิ — หน่วงก่อนปิด popup หลังตอบ

QUIZ_QUESTIONS = [
    {
        "q": "แก๊สเรือนกระจกหลักที่ทำให้น้ำแข็งขั้วโลกละลายคืออะไร?",
        "choices": ["CO₂", "O₂", "N₂", "Ar"],
        "answer": 0,
        "fact": "CO₂ จากการเผาเชื้อเพลิงฟอสซิลคือสาเหตุหลักของภาวะโลกร้อน",
    },
    {
        "q": "อุณหภูมิเฉลี่ยโลกเพิ่มขึ้นเท่าไหร่ในช่วง 100 ปีที่ผ่านมา?",
        "choices": ["~1.1°C", "~0.1°C", "~5°C", "~10°C"],
        "answer": 0,
        "fact": "IPCC รายงานว่าอุณหภูมิโลกสูงขึ้น ~1.1°C ตั้งแต่ยุคก่อนอุตสาหกรรม",
    },
    {
        "q": "SDG เป้าหมายข้อ 13 เกี่ยวข้องกับเรื่องใด?",
        "choices": ["การรับมือสภาพภูมิอากาศ", "ลดความยากจน", "การศึกษา", "พลังงานสะอาด"],
        "answer": 0,
        "fact": "SDG 13 เรียกร้องให้ทุกประเทศดำเนินการเร่งด่วนเพื่อรับมือกับการเปลี่ยนแปลงสภาพภูมิอากาศ",
    },
    {
        "q": "น้ำแข็งทะเลอาร์กติกหดตัวลงเฉลี่ยกี่เปอร์เซ็นต์ต่อทศวรรษ?",
        "choices": ["~13%", "~2%", "~30%", "~1%"],
        "answer": 0,
        "fact": "ตั้งแต่ปี 1979 น้ำแข็งทะเลอาร์กติกหดลงประมาณ 13% ต่อทศวรรษ",
    },
    {
        "q": "ภัยแล้งรุนแรงส่งผลกระทบต่อภาคใดของไทยมากที่สุด?",
        "choices": ["เกษตรกรรม", "การท่องเที่ยว", "อุตสาหกรรม", "บริการ"],
        "answer": 0,
        "fact": "ภาคเกษตรไทยใช้น้ำมากกว่า 70% และเสี่ยงต่อภัยแล้งมากที่สุด",
    },
    {
        "q": "การปลูกป่าช่วยลดโลกร้อนได้อย่างไร?",
        "choices": ["ดูดซับ CO₂", "ผลิต O₃", "ลด N₂O", "เพิ่ม CH₄"],
        "answer": 0,
        "fact": "ต้นไม้ 1 ต้นดูดซับ CO₂ ได้ประมาณ 21 กิโลกรัมต่อปี",
    },
    {
        "q": "ระดับน้ำทะเลสูงขึ้นเฉลี่ยกี่มิลลิเมตรต่อปีในปัจจุบัน?",
        "choices": ["~3.7 mm", "~0.1 mm", "~20 mm", "~50 mm"],
        "answer": 0,
        "fact": "ระดับน้ำทะเลสูงขึ้นเฉลี่ย 3.7 mm/ปี และเร่งเร็วขึ้นทุกทศวรรษ",
    },
    {
        "q": "ไฟป่าที่รุนแรงขึ้นจากโลกร้อนส่งผลต่อบรรยากาศอย่างไร?",
        "choices": ["ปล่อย CO₂ มหาศาล", "ดูดซับ CO₂", "ผลิต O₂ เพิ่ม", "ลดอุณหภูมิ"],
        "answer": 0,
        "fact": "ไฟป่าในอะเมซอน 2023 ปล่อย CO₂ มากกว่า 1 พันล้านตันในปีเดียว",
    },
    {
        "q": "ข้อตกลงปารีสตั้งเป้าควบคุมอุณหภูมิโลกให้ต่ำกว่าเท่าไหร่?",
        "choices": ["1.5°C", "3°C", "0.5°C", "5°C"],
        "answer": 0,
        "fact": "ข้อตกลงปารีส ค.ศ. 2015 กำหนดเป้าหมายไม่เกิน 1.5°C เหนือระดับก่อนอุตสาหกรรม",
    },
    {
        "q": "น้ำแข็งบนเกาะกรีนแลนด์ละลายหมด จะทำให้ระดับทะเลสูงขึ้นเท่าใด?",
        "choices": ["~7 เมตร", "~0.5 เมตร", "~50 เมตร", "~1 เซนติเมตร"],
        "answer": 0,
        "fact": "น้ำแข็งกรีนแลนด์มีปริมาณน้ำเพียงพอจะทำให้ระดับทะเลสูงขึ้น ~7 เมตรหากละลายทั้งหมด",
    },
]


class QuizPopup(FloatLayout):
    """
    Active Learning Quiz Popup
    - หยุดเกมและแสดงคำถามสุ่มเกี่ยวกับสภาพภูมิอากาศ
    - เรียก on_close(gems_earned) เมื่อตอบแล้ว (ถูก = +10 💎)
    """

    def __init__(self, on_close, biome_name="Arctic Ice", **kwargs):
        super().__init__(**kwargs)
        self._on_close  = on_close
        self._answered  = False

        # สุ่มคำถามและสับตำแหน่ง choices
        q_data  = random.choice(QUIZ_QUESTIONS)
        choices = list(enumerate(q_data["choices"]))
        random.shuffle(choices)
        self._correct_btn_idx = next(
            i for i, (orig, _) in enumerate(choices) if orig == q_data["answer"]
        )
        self._fact = q_data["fact"]
        self._btns = []

        # คำนวณตำแหน่งกล่องคำถาม (จัดกึ่งกลางหน้าจอ)
        card_x = (Window.width  - _CARD_W) / 2
        card_y = (Window.height - _CARD_H) / 2

        self._build_background()
        self._build_card(card_x, card_y, biome_name)
        self._build_question(card_x, card_y, q_data["q"])
        self._build_choices(card_x, card_y, choices)
        self._build_fact_label(card_x, card_y)

    # ── Build helpers ────────────────────────────────────────────────────────

    def _build_background(self):
        """วาดพื้นหลังทึบ"""
        with self.canvas.before:
            Color(0, 0, 0, 0.72)
            self._bg = Rectangle(pos=(0, 0), size=Window.size)

    def _build_card(self, cx, cy, biome_name):
        """วาดกล่องคำถามและ header"""
        with self.canvas:
            Color(0.08, 0.14, 0.28, 0.96)
            RoundedRectangle(pos=(cx, cy), size=(_CARD_W, _CARD_H), radius=[20])
            Color(0.3, 0.7, 1.0, 0.6)
            RoundedRectangle(
                pos=(cx, cy + _CARD_H - _HEADER_H),
                size=(_CARD_W, _HEADER_H),
                radius=[20, 20, 0, 0],
            )

        self.add_widget(Label(
            text=f"❄  Quiz — {biome_name}",
            font_name=_FONT, font_size='18sp', bold=True,
            color=(1, 1, 1, 1),
            pos=(cx, cy + _CARD_H - _HEADER_H),
            size=(_CARD_W, _HEADER_H),
        ))

    def _build_question(self, cx, cy, question_text):
        """วาด label คำถาม"""
        self.add_widget(Label(
            text=question_text,
            font_name=_FONT, font_size='20sp',
            color=(0.9, 0.95, 1, 1),
            pos=(cx + 20, cy + 230),
            size=(_CARD_W - 40, 100),
            text_size=(_CARD_W - 40, None),
            halign='center', valign='middle',
        ))

    def _build_choices(self, cx, cy, choices):
        """สร้างปุ่มตัวเลือก 4 ข้อ (2 คอลัมน์)"""
        col_w = (_CARD_W - 60) // 2
        positions = [
            (cx + 20,          cy + 140),
            (cx + 40 + col_w,  cy + 140),
            (cx + 20,          cy + 60),
            (cx + 40 + col_w,  cy + 60),
        ]
        for i, (_, text) in enumerate(choices):
            btn = Button(
                text=text,
                font_name=_FONT, font_size='17sp',
                background_normal='', background_color=_BTN_COLOR,
                color=(1, 1, 1, 1),
                size=(col_w, _BTN_H),
                pos=positions[i],
                size_hint=(None, None),
            )
            btn.bind(on_release=lambda b, idx=i: self._on_answer(idx))
            self.add_widget(btn)
            self._btns.append(btn)

    def _build_fact_label(self, cx, cy):
        """สร้าง label สำหรับแสดง fact (ซ่อนไว้จนกว่าจะตอบ)"""
        self._fact_label = Label(
            text='', font_name=_FONT, font_size='15sp',
            color=(0.7, 1.0, 0.7, 0),
            pos=(cx + 20, cy + 12),
            size=(_CARD_W - 40, 44),
            text_size=(_CARD_W - 40, None),
            halign='center',
        )
        self.add_widget(self._fact_label)

    # ── Event handler ────────────────────────────────────────────────────────

    def _on_answer(self, idx):
        """ตอบคำถาม — ไฮไลท์ถูก/ผิด แสดง fact แล้วปิด popup"""
        if self._answered:
            return
        self._answered = True

        correct = (idx == self._correct_btn_idx)
        gems    = 10 if correct else 0

        # ไฮไลท์ปุ่มถูก (เขียว) / ปุ่มที่กดผิด (แดง)
        for i, btn in enumerate(self._btns):
            if i == self._correct_btn_idx:
                btn.background_color = (0.1, 0.7, 0.2, 1)
            elif i == idx and not correct:
                btn.background_color = (0.8, 0.1, 0.1, 1)
            btn.disabled = True

        # แสดง fact พร้อม fade in
        prefix = f"✓ ถูกต้อง! +{gems} 💎  " if correct else "✗ ผิด!  "
        self._fact_label.text = prefix + self._fact
        fact_color = (0.7, 1.0, 0.7, 1) if correct else (1, 0.7, 0.7, 1)
        Animation(color=fact_color, duration=0.3).start(self._fact_label)

        Clock.schedule_once(lambda dt: self._on_close(gems), _CLOSE_DELAY)
