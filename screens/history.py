from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock

from kivy.uix.label import Label
from core.database import DatabaseManager

class HistoryScreen(Screen):
    """ คลาสหน้าจอประวัติการเล่น (History Screen) """
    def on_enter(self):
        """ ทำงานเมื่อเข้าสู่หน้าจอประวัติ """
        logger.info("เข้าสู่หน้าจอ History")
        self.load_history() # โหลดข้อมูลประวัติจาก Database
        
    def load_history(self):
        """ ฟังก์ชันดึงประวัติการเล่นมาแสดงผลบน ScrollView """
        # 1. เคลียร์ข้อมูลเก่าออกจากรายการก่อน (Reset List)
        self.ids.history_list.clear_widgets()
        
        db = DatabaseManager()
        # ดึงประวัติการเล่นของผู้เล่น (Default 100 รายการล่าสุด)
        history = db.get_history(db.get_last_player_name())
        
        # 2. กรณีไม่มีข้อมูลประวัติเลย
        if not history:
            self.ids.history_list.add_widget(Label(
                text="NO HISTORY YET",
                font_name='assets/Component_UI/Font/Kenney Future.ttf',
                size_hint_y=None, height=50
            ))
            return

        # 3. นำข้อมูลแต่ละรอบการเล่นมาสร้างเป็น Label และเพิ่มลงในลิสต์
        for i, row in enumerate(history, 1):
            # แยกเอาเฉพาะวันที่ (ตัดเวลาออก)
            date_str = row['played_at'].split(' ')[0]
            dist = row['distance_m']
            gems = row['gems_collected']
            
            # ทำเครื่องหมายถ้วยทอง (Award) ให้กับรายการแรก (คะแนนสูงสุดในลิสต์ที่ดึงมา)
            award = " 🏆" if i == 1 else ""
            
            label_text = f"{i}. {date_str}: {dist} m ({gems} Gems){award}"
            
            self.ids.history_list.add_widget(Label(
                text=label_text,
                font_name='assets/Component_UI/Font/Kenney Future.ttf',
                font_size='18sp',
                size_hint_y=None,
                height=50,
                color=(1, 1, 1, 0.9)
            ))

    def go_back(self):
        """ ฟังก์ชันกลับหน้าเมนูหลัก """
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_menu(self):
        """ เปลี่ยนสถานะหน้าแอปเป็นหน้าเมนู """
        self.manager.current = 'menu'
