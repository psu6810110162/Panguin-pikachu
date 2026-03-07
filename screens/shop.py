from kivy.uix.screenmanager import Screen
from core.logger import logger
from core.audio import AudioManager
from kivy.clock import Clock

class ShopScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ Shop")
        self.update_balance_label()
        
    def update_balance_label(self):
        from core.database import DatabaseManager
        balance = DatabaseManager().get_gem_balance("Penguin")
        self.ids.gem_label.text = f"Gems: 💎 {balance}"

    def buy_item(self, item_id):
        from core.state import StateManager
        from core.database import DatabaseManager
        
        # ราคาพื้นฐาน (สมมติว่า 10 Gem ยกเว้นตัวเริ่มต้น)
        price = 10 if item_id != 'Ninja Frog' else 0
        
        db = DatabaseManager()
        balance = db.get_gem_balance("Penguin")
        
        if balance < price:
            logger.warning(f"Gem ไม่พอ! ต้องการ {price} แต่มี {balance}")
            AudioManager().play_sfx('down') # เสียงเตือนเงินไม่พอ
            return

        # ทำการหักลบ Gem
        if price > 0:
            if db.deduct_gems("Penguin", price):
                logger.info(f"ซื้อสกิน {item_id} สำเร็จ! หัก {price} Gems")
                AudioManager().play_sfx('tab')
                self.update_balance_label()
            else:
                logger.error("เกิดข้อผิดพลาดในการหัก Gem")
                return
        else:
            logger.info(f"เลือกใช้สกินฟรี: {item_id}")
            AudioManager().play_sfx('tab')

        # อัปเดต StateManager
        StateManager().selected_skin = item_id

    def go_back(self):
        from core.audio import AudioManager
        from kivy.clock import Clock
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_menu(self):
        self.manager.current = 'menu'
