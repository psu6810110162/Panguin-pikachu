from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from core.audio import AudioManager
from core.logger import logger

class MenuScreen(Screen):
    """ คลาสหน้าจอเมนูหลัก (Main Menu) """
    def on_enter(self):
        """ ทำงานเมื่อเข้าสู่หน้าจอเมนู """
        logger.info("เข้าสู่หน้าจอ MenuScreen")
        # เล่นเพลงประกอบ (BGM) หลังจากผ่านไป 0.5 วินาที
        Clock.schedule_once(lambda dt: AudioManager().play_bgm('Bgm.gameplay.mp3'), 0.5)
        # ตรวจสอบสถานะปุ่มเสียงให้ตรงกับความจริง
        Clock.schedule_once(lambda dt: self._sync_sound_button(), 0.1)

    def start_game(self):
        """ ฟังก์ชันเมื่อกดปุ่มเริ่มเกม """
        AudioManager().play_sfx('click')
        # รอเวลาสั้นๆ ก่อนเปลี่ยนหน้าเพื่อให้เสียง Effect เล่นจบ
        Clock.schedule_once(lambda dt: self._go_gameplay(), 0.2)

    def go_to_shop(self):
        """ ฟังก์ชันไปหน้าเลือกสกิน (Shop) """
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_shop(), 0.2)

    def go_to_history(self):
        """ ฟังก์ชันไปหน้าประวัติการเล่น (History) """
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_history(), 0.2)

    def exit_game(self):
        """ ฟังก์ชันปิดเกม """
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._exit(), 0.2)

    # ฟังก์ชันเสริม (Private Methods) สำหรับเปลี่ยนหน้าจอ
    def _go_gameplay(self):
        logger.info("กำลังเริ่มต้นเกม...")
        self.manager.current = 'gameplay' # เปลี่ยนหน้าจอ Kivy เป็น Gameplay

    def _go_shop(self):
        self.manager.current = 'shop'

    def _go_history(self):
        self.manager.current = 'history'

    def _exit(self):
        from kivy.app import App
        App.get_running_app().stop() # สั่งปิดแอปพลิเคชัน

    def toggle_sound(self):
        """ ฟังก์ชันเปิด/ปิดเสียง (Mute/Unmute) """
        AudioManager().play_sfx('click')
        bgm_muted = AudioManager().toggle_mute() # สลับสถานะ Mute ใน AudioManager
        logger.info( f"เสียง {'ปิด' if bgm_muted else 'เปิด'}แล้ว")
        self._sync_sound_button() # อัปเดตรูปไอคอนปุ่มเสียง

    def _sync_sound_button(self):
        """ ฟังก์ชันเปลี่ยนรูปปุ่มเสียงตามสถานะปัจจุบัน """
        sound_btn = self.ids.get('sound_btn') # ค้นหา Widget จาก ID
        if sound_btn:
            if AudioManager().bgm_muted:
                # กรณีปิดเสียง: ใช้รูป Volume Down
                sound_btn.background_normal = 'assets/Component_UI/Button Sounds/volume_down.png'
                sound_btn.background_down   = 'assets/Component_UI/Button Sounds/volume_down.png'
            else:
                # กรณีเปิดเสียง: ใช้รูป Volume Up
                sound_btn.background_normal = 'assets/Component_UI/Button Sounds/volume_up.png'
                sound_btn.background_down   = 'assets/Component_UI/Button Sounds/volume_up.png'

    
