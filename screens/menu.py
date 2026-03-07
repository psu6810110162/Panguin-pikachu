from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from core.audio import AudioManager
from core.logger import logger

class MenuScreen(Screen):
    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ MenuScreen")
        Clock.schedule_once(lambda dt: AudioManager().play_bgm('Bgm.gameplay.mp3'), 0.5)
        Clock.schedule_once(lambda dt: self._sync_sound_button(), 0.1)

    def start_game(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_gameplay(), 0.2)

    def go_to_shop(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_shop(), 0.2)

    def go_to_history(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._go_history(), 0.2)

    def exit_game(self):
        AudioManager().play_sfx('click')
        Clock.schedule_once(lambda dt: self._exit(), 0.2)

    # private methods เปลี่ยนหน้า
    def _go_gameplay(self):
        logger.info("กำลังเริ่มต้นเกม...")
        self.manager.current = 'gameplay'

    def _go_shop(self):
        self.manager.current = 'shop'

    def _go_history(self):
        self.manager.current = 'history'

    def _exit(self):
        from kivy.app import App
        App.get_running_app().stop()

    def toggle_sound(self):
        AudioManager().play_sfx('click')
        bgm_muted = AudioManager().toggle_mute()
        logger.info( f"เสียง {'ปิด' if bgm_muted else 'เปิด'}แล้ว")
        self._sync_sound_button()

    def _sync_sound_button(self):
        sound_btn = self.ids.get('sound_btn')
        if sound_btn:
            if AudioManager().bgm_muted:
                sound_btn.background_normal = 'assets/Component_UI/Button Sounds/volume_down.png'
                sound_btn.background_down   = 'assets/Component_UI/Button Sounds/volume_down.png'
            else:
                sound_btn.background_normal = 'assets/Component_UI/Button Sounds/volume_up.png'
                sound_btn.background_down   = 'assets/Component_UI/Button Sounds/volume_up.png'

    
