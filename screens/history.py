from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock

from kivy.uix.label import Label
from core.database import DatabaseManager
from core import i18n

KF_FONT   = i18n.FONT_KF
THAI_FONT = i18n.FONT_THAI

class HistoryScreen(Screen):
    """ คลาสหน้าจอประวัติการเล่น (History Screen) """
    def on_enter(self):
        """ ทำงานเมื่อเข้าสู่หน้าจอประวัติ """
        logger.info("เข้าสู่หน้าจอ History")
        self._refresh_static_text()
        self.load_history() # โหลดข้อมูลประวัติจาก Database

    def _refresh_static_text(self):
        """อัปเดต label/ปุ่มตามภาษา"""
        font = i18n.get_font()
        if 'leaderboard_lbl' in self.ids:
            self.ids.leaderboard_lbl.text      = i18n.t('leaderboard')
            self.ids.leaderboard_lbl.font_name = font
        if 'back_btn' in self.ids:
            self.ids.back_btn.text      = i18n.t('back')
            self.ids.back_btn.font_name = font
        
    def load_history(self):
        """ ฟังก์ชันดึงประวัติการเล่นมาแสดงผลบน ScrollView """
        # 1. เคลียร์ข้อมูลเก่าออกจากรายการก่อน (Reset List)
        self.ids.history_list.clear_widgets()
        
        db = DatabaseManager()
        # ดึงประวัติการเล่นของผู้เล่น (Default 100 รายการล่าสุด)
        history = db.get_history(db.get_last_player_name())
        
        # 2. กรณีไม่มีข้อมูลประวัติเลย
        if not history:
            lang = i18n.get_language()
            font = THAI_FONT if lang == 'th' else KF_FONT
            self.ids.history_list.add_widget(Label(
                text=i18n.t('no_history'),
                font_name=font,
                font_size='20sp',
                size_hint_y=None, height=60,
                color=(0.70, 0.90, 1.0, 0.55)
            ))
            return

        for i, row in enumerate(history, 1):
            date_str = row['played_at'].split(' ')[0]
            dist = row['distance_m']
            gems = row['gems_collected']
            award = "  TOP" if i == 1 else ""
            label_text = f"#{i}  {date_str}   {dist} m  +{gems}{award}"
            # Alternate row tint for readability
            row_alpha = 0.08 if i % 2 == 0 else 0.0
            lbl = Label(
                text=label_text,
                font_name=i18n.get_font(),
                font_size='17sp',
                size_hint_y=None,
                height=48,
                color=(1.0, 0.80, 0.20, 1) if i == 1 else (0.75, 0.90, 1.0, 0.92),
                halign='left',
                valign='middle',
            )
            lbl.bind(size=lambda l, v: setattr(l, 'text_size', v))
            self.ids.history_list.add_widget(lbl)

    def go_back(self):
        """ ฟังก์ชันกลับหน้าเมนูหลัก """
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_menu(self):
        """ เปลี่ยนสถานะหน้าแอปเป็นหน้าเมนู """
        self.manager.current = 'menu'
