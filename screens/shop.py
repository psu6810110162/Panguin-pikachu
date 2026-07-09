from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from core.database import DatabaseManager
from core.state import StateManager
from kivy.clock import Clock

class ShopScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ Shop")
        self.update_balance_label()
        
    def update_balance_label(self):
        db = DatabaseManager()
        balance = db.get_gem_balance("Penguin")
        if 'gem_label' in self.ids:
            self.ids.gem_label.text = f"GEMS: 💎 {balance}"
        
        # อัปเดตสถานะปุ่มสกิน
        state = StateManager()
        current_skin = state.selected_skin
        
        skins = ['Ninja Frog', 'Mask Dude', 'Pink Man', 'Virtual Guy']
        for s_name in skins:
            btn_id = s_name.lower().replace(' ', '_') + "_btn"
            btn = self.ids.get(btn_id)
            if not btn: continue
            
            is_owned = db.is_skin_owned("Penguin", s_name)
            
            if s_name == current_skin:
                btn.text = "EQUIPPED"
                btn.background_color = (0.2, 0.8, 0.2, 1) # เขียว (ใส่อยู่)
            elif is_owned:
                btn.text = "EQUIP"
                btn.background_color = (1, 1, 1, 1) # ขาว (มีแล้วแต่ไม่ได้ใส่)
            else:
                btn.text = "BUY 💎 10"
                btn.background_color = (1, 1, 1, 1)

    def buy_item(self, item_name):
        db = DatabaseManager()
        state = StateManager()
        
        # ราคาพื้นฐาน (สมมติว่า 10 Gem ยกเว้นตัวเริ่มต้น)
        price = 10 if item_name != 'Ninja Frog' else 0
        
        # ถ้ามีอยู่แล้วให้แค่สวมใส่
        if db.is_skin_owned("Penguin", item_name):
            state.selected_skin = item_name
            AudioManager().play_sfx('tab')
            logger.info(f"สวมใส่สกิน {item_name}")
            self.update_balance_label()
            return

        # ถ้ายังไม่มีให้หักเงินและบันทึก
        if db.deduct_gems("Penguin", price):
            db.add_owned_skin("Penguin", item_name)
            state.selected_skin = item_name
            AudioManager().play_sfx('tab')
            logger.info(f"ซื้อสกิน {item_name} สำเร็จ! หัก {price} Gems")
            self.update_balance_label()
        else:
            logger.warning("Gems ไม่พอ!")
            AudioManager().play_sfx('down') # เสียงเตือนเงินไม่พอ

    def go_back(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_menu(self):
        self.manager.current = 'menu'
