from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.clock import Clock
from core.audio import AudioManager
from core.logger import logger
from core import i18n

class MenuScreen(Screen):
    """ คลาสหน้าจอเมนูหลัก (Main Menu) """

    KF_FONT = 'assets/Component_UI/Font/Kenney Future.ttf'

    def on_enter(self):
        """ ทำงานเมื่อเข้าสู่หน้าจอเมนู """
        logger.info("เข้าสู่หน้าจอ MenuScreen")
        Clock.schedule_once(lambda dt: AudioManager().play_bgm('Bgm.gameplay.mp3'), 0.5)
        Clock.schedule_once(lambda dt: self._sync_sound_button(), 0.1)
        self._ensure_lang_btn()

    def _ensure_lang_btn(self):
        """สร้างปุ่มสลับภาษาครั้งแรกที่เข้า menu"""
        if hasattr(self, '_lang_btn'):
            self._lang_btn.text = i18n.t('toggle_lang')
            return
        self._lang_btn = Button(
            text             = i18n.t('toggle_lang'),
            font_name        = self.KF_FONT,
            font_size        = 13,
            bold             = True,
            color            = (0.20, 0.95, 0.55, 1),
            background_color = (0, 0, 0, 0),
            background_normal= '',
            background_down  = '',
            size_hint        = (None, None),
            size             = (68, 30),
            pos_hint         = {'right': 0.99, 'top': 0.98},
        )
        with self._lang_btn.canvas.before:
            Color(0.08, 0.22, 0.16, 0.90)
            self._lang_bg = RoundedRectangle(
                pos=self._lang_btn.pos, size=self._lang_btn.size, radius=[7]
            )
            Color(0.20, 0.70, 0.45, 0.55)
            self._lang_line = Line(
                rounded_rectangle=(
                    self._lang_btn.x, self._lang_btn.y,
                    self._lang_btn.width, self._lang_btn.height, 7
                ),
                width=1.0,
            )
        self._lang_btn.bind(pos=self._refresh_lang_btn, size=self._refresh_lang_btn)
        self._lang_btn.bind(on_press=self._toggle_language)
        self.add_widget(self._lang_btn)

    def _refresh_lang_btn(self, *_):
        self._lang_bg.pos   = self._lang_btn.pos
        self._lang_bg.size  = self._lang_btn.size
        self._lang_line.rounded_rectangle = (
            self._lang_btn.x, self._lang_btn.y,
            self._lang_btn.width, self._lang_btn.height, 7
        )

    def _toggle_language(self, *_):
        AudioManager().play_sfx('click')
        lang = 'en' if i18n.get_language() == 'th' else 'th'
        i18n.set_language(lang)
        self._lang_btn.text = i18n.t('toggle_lang')

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

    def go_to_climate_report(self):
        """ ฟังก์ชันไปหน้า Climate Report (Learning Path) """
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_climate_report(), 0.2)

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

    def _go_climate_report(self):
        self.manager.current = 'learning_path'

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

    
