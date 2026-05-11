import random
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from core.logger import logger
from core.audio import AudioManager
from core.database import DatabaseManager
from core.config import DEFAULT_PLAYER_NAME
from core import i18n

THAI_FONT = i18n.FONT_THAI
KF_FONT   = i18n.FONT_KF

CLIMATE_FACTS = [
    "Arctic sea ice has declined ~13% per decade since 1979.",
    "The Arctic warms 4× faster than the global average.",
    "2023 was Earth's hottest year in 125,000 years.",
    "Sea ice loss exposes darker ocean, absorbing more heat.",
    "Emperor penguins may be extinct by 2100 without action.",
    "Greenland loses ~280 billion tonnes of ice per year.",
    "Every 0.5°C of warming doubles the chance of ice-free summers.",
    "Permafrost thaw releases CO₂ trapped for thousands of years.",
    "Ocean heat content reached a record high in 2023.",
    "Limiting warming to 1.5°C saves 70% of coral reefs.",
    "Renewable energy is now cheaper than fossil fuels globally.",
    "1 billion people face water scarcity from glacier retreat.",
    "Antarctica lost 150 billion tonnes of ice per year in the 2010s.",
    "Arctic shipping routes open as sea ice retreats — a double-edged change.",
    "Planting trees and reducing meat consumption can cut emissions 30%.",
]

CLIMATE_FACTS_TH = [
    "น้ำแข็งทะเลอาร์กติกลดลง ~13% ต่อทศวรรษตั้งแต่ปี 1979",
    "อาร์กติกร้อนขึ้นเร็วกว่าค่าเฉลี่ยโลกถึง 4 เท่า",
    "ปี 2023 ร้อนที่สุดในรอบ 125,000 ปีของโลก",
    "น้ำแข็งที่ละลายเปิดพื้นผิวมหาสมุทรดูดซับความร้อนมากขึ้น",
    "เพนกวิน Emperor อาจสูญพันธุ์ภายในปี 2100 หากไม่มีการแก้ไข",
    "กรีนแลนด์สูญเสียน้ำแข็ง ~280 พันล้านตันต่อปี",
    "ทุก 0.5°C ของอุณหภูมิที่สูงขึ้นทำให้โอกาสฤดูร้อนไร้น้ำแข็งเพิ่มเป็นสองเท่า",
    "การละลายของดินเยือกแข็งปล่อย CO₂ ที่สะสมมานับพันปี",
    "ความร้อนในมหาสมุทรสูงเป็นประวัติการณ์ในปี 2023",
    "จำกัดอุณหภูมิที่ 1.5°C จะช่วยรักษาแนวปะการัง 70% ของโลก",
    "พลังงานหมุนเวียนตอนนี้ถูกกว่าเชื้อเพลิงฟอสซิลทั่วโลกแล้ว",
    "ประชากร 1,000 ล้านคนเผชิญกับการขาดแคลนน้ำจากธารน้ำแข็งละลาย",
    "แอนตาร์กติกาสูญเสียน้ำแข็ง 150 พันล้านตันต่อปีในช่วงทศวรรษ 2010",
    "เส้นทางเดินเรือในอาร์กติกเปิดขึ้นตามการละลายของน้ำแข็ง — ผลกระทบสองด้าน",
    "การปลูกต้นไม้และลดการบริโภคเนื้อสัตว์ช่วยลดการปล่อยก๊าซ 30%",
]


class GameOverScreen(Screen):
    """หน้าจอจบเกม — แสดงคะแนน, เกร็ดความรู้, และตัวเลือกถัดไป"""

    def on_enter(self):
        """ดึงข้อมูลจาก gameplay และแสดงผล"""
        logger.info("เข้าสู่หน้าจอ GameOver")
        db = DatabaseManager()

        # Auto-fill ชื่อผู้เล่นล่าสุด
        if 'name_input' in self.ids:
            self.ids.name_input.text = db.get_last_player_name()

        # ดึงคะแนนจาก gameplay screen
        self.distance, self.gems = self._get_gameplay_score()

        self._refresh_static_text()
        self._saved = False

    def _refresh_static_text(self):
        """อัปเดต label และปุ่มตามภาษาปัจจุบัน"""
        lang = i18n.get_language()
        font = THAI_FONT if lang == 'th' else KF_FONT

        if 'score_label' in self.ids:
            lbl = self.ids.score_label
            lbl.text      = f"{i18n.t('distance_prefix')}{self.distance} m"
            lbl.font_name = font

        if 'climate_fact_label' in self.ids:
            lbl = self.ids.climate_fact_label
            lbl.text      = self._pick_fact()
            lbl.font_name = font

        if 'name_input' in self.ids:
            self.ids.name_input.hint_text = i18n.t('enter_name')

        _btn_map = {
            'retry_btn':      'play_again',
            'go_history_btn': 'history',
            'home_btn':       'home',
        }
        for widget_id, key in _btn_map.items():
            w = self.ids.get(widget_id)
            if w:
                w.text      = i18n.t(key)
                w.font_name = font

    # ── ฟังก์ชันช่วย (Private Helpers) ─────────────────────────────────────

    def _get_gameplay_score(self):
        """ดึงระยะทางและเพชรจาก gameplay screen"""
        try:
            gameplay = self.manager.get_screen('gameplay')
            return int(gameplay.grid.get_distance_m()), gameplay.gems_collected
        except Exception as e:
            logger.error(f"Error getting gameplay data: {e}")
            return 0, 0

    def _pick_fact(self):
        """เลือกเกร็ดความรู้ตาม biome + ภาษาปัจจุบัน"""
        lang = i18n.get_language()
        try:
            gameplay = self.manager.get_screen('gameplay')
            biome_id = gameplay.biome_mgr.current.id
            # ใช้ข้อมูลจาก learning_path BIOME_FACTS ถ้ามี
            from screens.learning_path import BIOME_FACTS
            facts_dict = BIOME_FACTS.get(biome_id, {})
            if facts_dict:
                return random.choice(facts_dict.get(lang, facts_dict.get('en', '')).split('\n'))
        except Exception:
            pass
        # fallback — global facts
        return random.choice(CLIMATE_FACTS_TH if lang == 'th' else CLIMATE_FACTS)

    def _save_data(self):
        """บันทึก session ลง SQLite — ป้องกันการบันทึกซ้ำด้วย _saved flag"""
        if getattr(self, '_saved', False):
            return

        name = DEFAULT_PLAYER_NAME
        if 'name_input' in self.ids:
            name = self.ids.name_input.text.strip() or DEFAULT_PLAYER_NAME

        try:
            db = DatabaseManager()
            db.save_game_session(name, distance=self.distance, gems=self.gems)
            # บันทึก Quiz answers ที่สะสมไว้ระหว่างเล่น (ถ้ามี)
            try:
                gameplay = self.manager.get_screen('gameplay')
                for biome_id, q_idx, correct in gameplay._pending_quiz_answers:
                    db.save_quiz_answer(name, biome_id, q_idx, correct)
                gameplay._pending_quiz_answers = []
            except Exception:
                pass
            logger.info(f"บันทึก: {name} — {self.distance}m, {self.gems} gems")
            self._saved = True
        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def _navigate(self, target: str):
        """บันทึกคะแนน → เล่นเสียง → เปลี่ยนหน้าจอ"""
        self._save_data()
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', target), 0.2)

    # ── Action handlers (เรียกจาก KV หรือปุ่ม) ──────────────────────────────

    def retry_game(self):
        """บันทึก → reset gameplay → กลับไปเล่นใหม่"""
        self._save_data()
        AudioManager().play_sfx('click')
        self.manager.get_screen('gameplay').restart_game()
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'gameplay'), 0.2)

    def view_history(self):
        """ไปหน้าประวัติคะแนน"""
        self._navigate('history')

    def go_home(self):
        """กลับเมนูหลัก"""
        self._navigate('menu')
