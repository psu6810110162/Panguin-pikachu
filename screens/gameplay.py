import random
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage

from core.logger import logger
from core.config import TARGET_FPS
from game.grid import GridManager
from game.penguin import Penguin

# ============================
# ตั้งค่าขนาดบล็อกตามภาพจริง
# ============================
TILE_IMG_SIZE = 128          # ขนาดภาพ (px) ของแต่ละบล็อก
TILE_HALF_W   = TILE_IMG_SIZE // 2   # 64
TILE_HALF_H   = TILE_IMG_SIZE // 4   # 32 (Isometric = กว้าง 2: สูง 1)

# ============================
# จับคู่ภาพกับหน้าที่ใช้งานในเกม
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

STONE_TILES = [
    'assets/isometric-nature-pack/stone1.png',
    'assets/isometric-nature-pack/stone2.png',
    'assets/isometric-nature-pack/stone3.png',
    'assets/isometric-nature-pack/stone4.png',
]

DIRT_TILES = [
    'assets/isometric-nature-pack/dirt1.png',
    'assets/isometric-nature-pack/dirt2.png',
    'assets/isometric-nature-pack/dirt3.png',
    'assets/isometric-nature-pack/dirt4.png',
]


class KivyRenderer(Widget):
    """ตัวรับหน้าที่วาดภาพ Grid ลงหน้าจอโดยใช้ Asset จริง"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # สุ่มเลือกภาพหญ้าให้แต่ละ tile ตอนเริ่มเกม เพื่อไม่ให้ซ้ำกันทุกช่อง
        self.tile_textures = {}

    def _get_tile_texture(self, col, row):
        """ดึง texture ที่เคยสุ่มไว้ หรือสุ่มใหม่ถ้ายังไม่มี"""
        key = (col, row)
        if key not in self.tile_textures:
            img_path = random.choice(GRASS_TILES)
            self.tile_textures[key] = CoreImage(img_path).texture
        return self.tile_textures[key]

    def draw(self, grid_manager, penguin, obstacles=None):
        self.canvas.clear()
        with self.canvas:
            # === พื้นหลัง (ท้องฟ้า) ===
            Color(0.53, 0.81, 0.92, 1)
            Rectangle(pos=(0, 0), size=Window.size)

            # === วาดบล็อกทางเดินด้วยภาพหญ้า (grass) ===
            Color(1, 1, 1, 1)  # รีเซ็ตสีเป็นขาว เพื่อให้ภาพแสดงสีจริง
            for col, row in grid_manager.path:
                tex = self._get_tile_texture(col, row)
                x, y = self.iso_to_screen(col, row)
                Rectangle(
                    texture=tex,
                    pos=(x, y),
                    size=(TILE_IMG_SIZE, TILE_IMG_SIZE),
                )

            # === วาดตัวละครเพนกวิน (กล่องสีดำชั่วคราว) ===
            if not penguin.is_dead:
                Color(0.1, 0.1, 0.1, 1)
                px, py = self.iso_to_screen(penguin.col, penguin.row)
                Rectangle(
                    pos=(px + 30, py + 40),
                    size=(60, 60),
                )

            # === วาด Obstacle ด้วยภาพหิน (stone) ===
            if obstacles:
                Color(1, 1, 1, 1)
                for obs in obstacles:
                    if obs.active:
                        stone_tex = CoreImage(random.choice(STONE_TILES)).texture
                        ox, oy = self.iso_to_screen(obs.col, obs.row)
                        # ซ้อนหินหลายก้อนตามขนาด (Size 1-5)
                        for layer in range(obs.size):
                            Rectangle(
                                texture=stone_tex,
                                pos=(ox, oy + layer * 20),
                                size=(TILE_IMG_SIZE, TILE_IMG_SIZE),
                            )

    def iso_to_screen(self, col, row):
        """แปลงพิกัดตาราง (col, row) ให้กลายเป็นพิกัดหน้าจอ Isometric"""
        offset_x = Window.width / 2
        offset_y = 100

        screen_x = (col - row) * TILE_HALF_W + offset_x
        screen_y = (col + row) * TILE_HALF_H + offset_y
        return screen_x, screen_y


class GamePlayScreen(Screen):
    """หน้าจอหลักตอนวิ่ง: เชื่อมการกดปุ่ม ขยับภาพ และวาดลูป"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid = GridManager()
        self.penguin = Penguin()
        self.game_event = None

        # สร้างเส้นทางตั้งต้น
        self.grid.reset()

        self.renderer = KivyRenderer()
        self.add_widget(self.renderer)

        # ผูกอีเวนต์คีย์บอร์ด
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def on_enter(self):
        """เริ่มเกมตอนผู้เล่นเข้ามาหน้านี้"""
        logger.info("เข้าสู่หน้า GamePlay")
        self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)

    def on_leave(self):
        """หยุดเกมเมื่อออกจากหน้านี้"""
        if self.game_event:
            self.game_event.cancel()

    def update(self, dt):
        """Game Loop ทำงานทุกเฟรม"""
        if not self.penguin.is_dead:
            if not self.grid.is_on_path(self.penguin.col, self.penguin.row):
                self.penguin.die()
                logger.info(f"Game Over! วิ่งได้ {self.grid.get_distance_m()} เมตร")

        # วาดภาพใหม่ทุกเฟรม
        self.renderer.draw(self.grid, self.penguin)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.penguin.is_dead:
            return False

        if keycode[1] == 'left':
            self.penguin.turn_left()
            self.penguin.move_forward()
            self.grid.step_forward()
            return True
        elif keycode[1] == 'right':
            self.penguin.turn_right()
            self.penguin.move_forward()
            self.grid.step_forward()
            return True
        elif keycode[1] == 'up':
            self.penguin.move_forward()
            self.grid.step_forward()
            return True

        return False
