import random
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation

from core.audio import AudioManager
from core.logger import logger
from core.config import TARGET_FPS, TILE_W, TILE_H, TILE_IMG_H
from game.grid import GridManager
from game.penguin import Penguin

# ============================
# ภาพทางเดิน
# ============================
GRASS_TILES = [
    'assets/isometric-nature-pack/grass1.png',
    'assets/isometric-nature-pack/grass2.png',
    'assets/isometric-nature-pack/grass3.png',
    'assets/isometric-nature-pack/grass4.png',
    'assets/isometric-nature-pack/grass5.png',
    'assets/isometric-nature-pack/grass6.png',
    'assets/isometric-nature-pack/grass7.png',
    'assets/isometric-nature-pack/grass8.png',
    'assets/isometric-nature-pack/grass9.png',
    'assets/isometric-nature-pack/grass10.png',
]

ARROW_RIGHT_IMG = 'assets/Component_UI/Vector/arrow_right.png'  
ARROW_LEFT_IMG  = 'assets/Component_UI/Vector/arrow_left.png'

DIR_LEFT  = (0, 1)   # iso ซ้าย
DIR_RIGHT = (1, 0)   # iso ขวา


class KivyRenderer(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tile_textures = {}
        self._grass_textures = [CoreImage(p).texture for p in GRASS_TILES]

        # ── FIX 1: ตั้ง cam เป็น None
        # เฟรมแรกจะ snap ทันที ไม่ lerp จาก (0,0)
        # ซึ่งเป็นสาเหตุที่กล้องวิ่งหนีไปขวาตอนเริ่ม
        self.cam_x = None
        self.cam_y = None

    def _get_tile_texture(self, col, row):
        key = (col, row)
        if key not in self.tile_textures:
            self.tile_textures[key] = random.choice(self._grass_textures)
        return self.tile_textures[key]

    def grid_to_screen(self, col, row):
        x = (col - row) * (TILE_W // 2)
        y = (col + row) * (TILE_H // 2)
        return x, y

    def draw(self, grid_manager, penguin, path_index):
        target_x, target_y = self.grid_to_screen(penguin.col, penguin.row)

        # snap เฟรมแรก
        if self.cam_x is None:
            self.cam_x = target_x
            self.cam_y = target_y

        # smooth follow
        self.cam_x += (target_x - self.cam_x) * 0.15
        self.cam_y += (target_y - self.cam_y) * 0.15

        # ── FIX 1: ใช้ /2 ทั้งสองแกน → เพนกวินอยู่กลางจอ
        ox = Window.width  / 2 - self.cam_x
        oy = Window.height / 2 - self.cam_y

        self.canvas.clear()
        with self.canvas:
            # กำหนดระยะมองเห็นรอบตัว (รัศมีการมองเห็น)
            view_radius = 15
            visible_tiles = []
            
            # ค้นหาแผ่นกระเบื้องที่อยู่ในรัศมีการมองเห็นจาก path_set
            for col, row in grid_manager.path_set:
                if (penguin.col - view_radius <= col <= penguin.col + view_radius) and \
                   (penguin.row - view_radius <= row <= penguin.row + view_radius):
                    visible_tiles.append((col, row))

            # Painter's Algorithm: col+row มาก = วาดก่อน (ข้างหลัง)
            visible_tiles.sort(key=lambda t: t[0] + t[1], reverse=True)

            Color(1, 1, 1, 1)
            for col, row in visible_tiles:
                # เช็คว่าเป็น fork tile หรือไม่ เพื่อ render สีต่าง
                if grid_manager.is_fork_tile(col, row):
                    Color(1, 0.9, 0.4, 1) # สีทอง/เหลืองอ่อน
                else:
                    Color(1, 1, 1, 1)

                tex    = self._get_tile_texture(col, row)
                sx, sy = self.grid_to_screen(col, row)
                draw_x = sx + ox - (TILE_W // 2)
                draw_y = sy + oy - (TILE_IMG_H - TILE_H // 2)
                Rectangle(texture=tex, pos=(draw_x, draw_y), size=(TILE_W, TILE_IMG_H))

            # เพนกวิน placeholder
            if not penguin.is_dead:
                px, py = self.grid_to_screen(penguin.col, penguin.row)
                pw, ph = 40, 50
                Color(0.15, 0.15, 0.2, 1)
                Rectangle(pos=(px + ox - pw // 2, py + oy - 5), size=(pw, ph))
                Color(0.95, 0.95, 0.95, 1)
                Rectangle(pos=(px + ox - 10, py + oy + 15), size=(20, 20))


class ArrowButton(ButtonBehavior, Image):

    def __init__(self, move_callback=None, **kwargs):
        super().__init__(**kwargs)
        self._move_callback = move_callback      # รับ callback ผ่าน __init__
        self.bind(on_press=self.handle_press)
        self.bind(on_release=self.handle_release)

    def handle_press(self, *args):
        Animation(
            size=(600, 600),
            duration=0.08,
            t='out_back'
        ).start(self)
        if self._move_callback: # เรียก callback เอง ไม่ผูกกับ on_press ใน GamePlayScreen
            self._move_callback()

    def handle_release(self, *args):
        Animation(
            size=(120, 120),
            duration=0.1,
            t='out_quad'
        ).start(self)


class GamePlayScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid       = GridManager()
        self.penguin    = Penguin()
        self.game_event = None
        self.path_index = 0

        self.grid.reset()
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]

        # Renderer — cam_x/cam_y = None → snap อัตโนมัติ
        self.renderer = KivyRenderer()
        self.add_widget(self.renderer)

        # HUD
        self.hud_label = Label(
            text="0 m", font_size='28sp', bold=True,
            pos_hint={'right': 0.98, 'top': 0.98},
            size_hint=(0.2, 0.05), color=(1, 1, 1, 1),
        )
        self.add_widget(self.hud_label)

        # ปุ่ม
        OFFSET = 0.2
        self.btn_left = ArrowButton(
            move_callback=lambda: self._move(DIR_LEFT),  # ส่ง callback ผ่าน __init__
            source=ARROW_LEFT_IMG, size_hint=(None, None),
            size=(120, 120), pos_hint={'center_x': 0.5 - OFFSET, 'center_y': 0.08},
        )
        self.add_widget(self.btn_left)

        self.btn_right = ArrowButton(
            move_callback=lambda: self._move(DIR_RIGHT), # ส่ง callback ผ่าน __init__
            source=ARROW_RIGHT_IMG, size_hint=(None, None),
            size=(120, 120), pos_hint={'center_x': 0.5 + OFFSET, 'center_y': 0.08},
        )
        self.add_widget(self.btn_right)

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)

    def on_enter(self):
        logger.info("เข้าสู่หน้า GamePlay")
        self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)
        AudioManager().play_bgm('Bgm.gameplay.mp3')

    def on_leave(self):
        if self.game_event:
            self.game_event.cancel()

    def update(self, dt):
        dist = self.grid.get_distance_m()
        self.hud_label.text = f"{dist / 1000:.1f} km" if dist >= 1000 else f"{dist} m"
        self.renderer.draw(self.grid, self.penguin, self.path_index)

    def _move(self, direction):
        """
        ── FIX 2: เดินในทิศที่กดเสมอ ไม่ว่าจะอยู่บน path หรือไม่
        เดิม: กดผิด → is_stuck = True → หยุดทุกอย่าง (ไม่ใช่ตาย)
        ใหม่: กดผิด → เดินออกนอก path → ตาย (penguin.is_dead = True)
        """
        if self.penguin.is_dead:
            return

        new_col = self.penguin.col + direction[0]
        new_row = self.penguin.row + direction[1]

        # ย้ายก่อนเลย ไม่ว่าจะถูกหรือผิด
        self.penguin.col = new_col
        self.penguin.row = new_row

        if self.grid.is_on_path(new_col, new_row):
            # ถูกทาง: นับระยะ + อัปเดต index
            self.grid.step_forward()
            idx = self.grid.get_path_index(new_col, new_row)
            if idx >= 0:
                self.path_index = idx
                self.grid.extend_if_needed(self.path_index)
                AudioManager().play_sfx('Jump')
            
            # เช็คว่าเดินไปถึงจุดสุดท้ายของแผนที่แล้วหรือยัง
            if self.path_index == len(self.grid.path) - 1:
                logger.info(f"ชนะแล้ว! วิ่งถึงเส้นชัยด้วยระยะ {self.grid.get_distance_m()} m")
                self.manager.current = 'gameover'
        else:
            # ผิดทาง: เดินออกนอก path → ตาย
            self.penguin.is_dead = True
            AudioManager().play_sfx('Down')
            logger.info(f"ตก! ระยะ {self.grid.get_distance_m()} m")
            # เปลี่ยนไป GameOver
            self.manager.current = 'gameover'

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.penguin.is_dead:
            return False
        if keycode[1] == 'left':
            self.btn_left.handle_press()
            return True
        elif keycode[1] == 'right':
            self.btn_right.handle_press()
            return True
        return False
    

    def _on_keyboard_up(self, keyboard, keycode):
        if keycode[1] == 'left':
            self.btn_left.handle_release()
            return True
        elif keycode[1] == 'right':
            self.btn_right.handle_release()
            return True
        return False