from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from core.database import DatabaseManager
from core.state import StateManager
from kivy.clock import Clock

class ShopScreen(Screen):
    """ คลาสหน้าจอร้านค้า/เลือกสกิน (Shop/Skin Selection) """
    def on_enter(self):
        """ ทำงานเมื่อเข้าสู่หน้าร้านค้า """
        logger.info("เข้าสู่หน้าจอ Shop")
        self.update_balance_label() # อัปเดตยอดเงินและสถานะปุ่ม
        
    def update_balance_label(self):
        """ อัปเดตการแสดงผลยอด Gems และสถานะของแต่ละปุ่มสกิน """
        db = DatabaseManager()
        player_name = db.get_last_player_name()
        # ดึงยอด Gem ปัจจุบันมาแสดง
        balance = db.get_gem_balance(player_name)
        if 'gem_label' in self.ids:
            self.ids.gem_label.text = f"GEMS: 💎 {balance}"

        # อัปเดตสถานะปุ่มของแต่ละสกิน (EQUIPPED, EQUIP, หรือ BUY)
        state = StateManager()
        current_skin = state.selected_skin

        skins = ['Ninja Frog', 'Mask Dude', 'Pink Man', 'Virtual Guy']
        for s_name in skins:
            btn_id = s_name.lower().replace(' ', '_') + "_btn"
            btn = self.ids.get(btn_id)
            if not btn: continue

            is_owned = db.is_skin_owned(player_name, s_name)
            
            if s_name == current_skin:
                btn.text = "EQUIPPED"
                btn.background_color = (0.2, 0.8, 0.2, 1) # สีเขียว: กำลังสวมใส่
            elif is_owned:
                btn.text = "EQUIP"
                btn.background_color = (1, 1, 1, 1) # สีขาว: มีในครอบครองแล้ว
            else:
                btn.text = "BUY 💎 10"
                btn.background_color = (1, 1, 1, 1) # สีขาว: ยังไม่เป็นเจ้าของ

    def buy_item(self, item_name):
        """ ฟังก์ชันสำหรับซื้อหรือสวมใส่ไอเทมสกิน """
        db = DatabaseManager()
        state = StateManager()
        player_name = db.get_last_player_name()

        # ราคาพื้นฐานของสกิน (สมมติว่าตัวละ 10 Gem ยกเว้นตัว Ninja Frog ที่เป็นตัวเริ่มต้นฟรี)
        price = 10 if item_name != 'Ninja Frog' else 0

        # 1. ถ้าผู้เล่นมีสกินนี้อยู่แล้ว -> แค่สวมใส่และเปลี่ยน State ของแอป
        if db.is_skin_owned(player_name, item_name):
            state.selected_skin = item_name
            AudioManager().play_sfx('tab')
            logger.info(f"สวมใส่สกิน {item_name}")
            self.update_balance_label()
            return

        # 2. ถ้าผู้เล่นยังไม่มี -> ตรวจสอบ Gem และทำการหักเงินเพื่อซื้อ
        if db.deduct_gems(player_name, price):
            db.add_owned_skin(player_name, item_name) # เพิ่มรายชื่อสกินที่เจ้าของมี
            state.selected_skin = item_name
            AudioManager().play_sfx('tab')
            logger.info(f"ซื้อสกิน {item_name} สำเร็จ! หัก {price} Gems")
            self.update_balance_label()
        else:
            # กรณี Gems ไม่เพียงพอ
            logger.warning("Gems ไม่พอ!")
            AudioManager().play_sfx('down') # เล่นเสียงเตือน

    def go_back(self):
        """ ฟังก์ชันกลับหน้าเมนูหลัก """
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_menu(self):
        """ ค้นหาสั่งเปลี่ยนสถานะหน้าจอเป็นเมนู """
        self.manager.current = 'menu'
