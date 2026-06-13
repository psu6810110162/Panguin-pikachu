"""
Automated scene capture for report figures 7.3–7.8.
Boots the real game, walks the ScreenManager through every scene,
triggers the quiz popup and game-over, and saves a screenshot of each.

Run:  python scripts/capture_scenes.py
Output: assets/report_figures/captures/<scene>.png
"""
import os, sys, glob, threading, time

os.environ['KIVY_NO_ARGS'] = '1'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from kivy.config import Config
Config.set('graphics', 'width', '1280')
Config.set('graphics', 'height', '720')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.lang import Builder

from core.database import DatabaseManager
from core import i18n
from ui.components import HoverButton, AnimatedSkin  # noqa: F401  (registers .kv Factory classes)
from screens.gameplay import GamePlayScreen
from screens.menu import MenuScreen
from screens.gameover import GameOverScreen
from screens.history import HistoryScreen
from screens.shop import ShopScreen
from screens.learning_path import LearningPathScreen

Builder.load_file('style.kv')

OUT = os.path.join('assets', 'report_figures', 'captures')
os.makedirs(OUT, exist_ok=True)


class CaptureApp(App):
    def build(self):
        DatabaseManager().init_db()
        i18n.load()
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GamePlayScreen(name='gameplay'))
        sm.add_widget(GameOverScreen(name='gameover'))
        sm.add_widget(HistoryScreen(name='history'))
        sm.add_widget(ShopScreen(name='shop'))
        sm.add_widget(LearningPathScreen(name='learning_path'))
        self.sm = sm
        self._pending = None
        Clock.schedule_once(self._begin, 1.5)
        # hard watchdog: force quit after 40 s no matter what
        threading.Thread(target=self._watchdog, daemon=True).start()
        return sm

    def _watchdog(self):
        time.sleep(40)
        os._exit(0)

    def _shot(self, tag):
        # Kivy appends a frame counter; we rename afterwards
        Window.screenshot(name=os.path.join(OUT, f'{tag}__.png'))
        print(f'  shot: {tag}')

    def _begin(self, *_):
        # chain of (action, delay_after) steps
        self._queue = [
            (self._cap_menu,        1.0),
            (self._cap_shop,        1.0),
            (self._cap_report,      1.0),
            (self._cap_gameplay,    3.5),   # let it render + move
            (self._cap_quiz,        1.2),
            (self._cap_gameover,    1.5),
            (self._finish,          0.5),
        ]
        self._next()

    def _next(self, *_):
        if not self._queue:
            return
        action, delay = self._queue.pop(0)
        action()
        Clock.schedule_once(self._next, delay)

    # ---- individual scenes ----
    def _cap_menu(self):
        self.sm.current = 'menu'
        Clock.schedule_once(lambda *_: self._shot('menu'), 0.6)

    def _cap_shop(self):
        self.sm.current = 'shop'
        Clock.schedule_once(lambda *_: self._shot('shop'), 0.6)

    def _cap_report(self):
        self.sm.current = 'learning_path'
        Clock.schedule_once(lambda *_: self._shot('climate_report'), 0.6)

    def _cap_gameplay(self):
        self.sm.current = 'gameplay'
        # let the update loop run ~2.5s so penguin advances & tiles fill
        Clock.schedule_once(lambda *_: self._shot('gameplay'), 2.6)

    def _cap_quiz(self):
        gp = self.sm.get_screen('gameplay')
        try:
            gp._show_quiz_popup()
        except Exception as e:
            print('  quiz trigger failed:', e)
        Clock.schedule_once(lambda *_: self._shot('quiz_popup'), 0.7)

    def _cap_gameover(self):
        gp = self.sm.get_screen('gameplay')
        try:
            gp._go_gameover()
        except Exception as e:
            print('  gameover trigger failed:', e)
            self.sm.current = 'gameover'
        Clock.schedule_once(lambda *_: self._shot('gameover'), 0.9)

    def _finish(self):
        Clock.schedule_once(lambda *_: os._exit(0), 0.5)


if __name__ == '__main__':
    CaptureApp().run()
