import random
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage

from core.logger import logger
from core.config import TARGET_FPS, INITIAL_SPEED, SPEED_MULTIPLIER, MAX_SPEED
from game.grid import GridManager
from game.penguin import Penguin

# ============================
# ตั้งค่าขนาดบล็อกตามภาพจริง
# ============================
TILE_IMG_SIZE = 128
TILE_HALF_W   = TILE_IMG_SIZE // 2   # 64
TILE_HALF_H   = TILE_IMG_SIZE // 4   # 32

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
    """ตัววาดภาพ Grid ลงหน้าจอโดยใช้ Asset จริง พร้อมกล้องไล่ตาม"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tile_textures = {}
        # โหลด texture ล่วงหน้าเพื่อลดภาระ CPU
        self._grass_textures = [CoreImage(p).texture for p in GRASS_TILES]
        self._stone_textures = [CoreImage(p).texture for p in STONE_TILES]
        self._dirt_textures  = [CoreImage(p).texture for p in DIRT_TILES]

        # ตำแหน่งกล้อง (เลื่อนตามตัวละคร)
        self.cam_x = 0
        self.cam_y = 0

    def _get_tile_texture(self, col, row):
        """ดึง texture ที่เคยสุ่มไว้ หรือสุ่มใหม่ถ้ายังไม่มี"""
        key = (col, row)
        if key not in self.tile_textures:
            self.tile_textures[key] = random.choice(self._grass_textures)
        return self.tile_textures[key]

    def draw(self, grid_manager, penguin, path_index):
        # คำนวณตำแหน่งกล้องให้ตามตัวเพนกวิน
        target_x, target_y = self.iso_to_screen_raw(penguin.col, penguin.row)
        self.cam_x += (target_x - self.cam_x) * 0.1  # Smooth camera
        self.cam_y += (target_y - self.cam_y) * 0.1

        # Offset = จุดศูนย์กลางหน้าจอ - ตำแหน่งกล้อง
        ox = Window.width / 2 - self.cam_x
        oy = Window.height / 2 - self.cam_y

        self.canvas.clear()
        with self.canvas:
            # === พื้นหลังท้องฟ้า ===
            Color(0.53, 0.81, 0.92, 1)
            Rectangle(pos=(0, 0), size=Window.size)

            # === วาดบล็อกทางเดิน (เฉพาะที่อยู่ใกล้กล้อง) ===
            Color(1, 1, 1, 1)
            visible_range = 30  # จำนวน tile รอบตัวละครที่จะวาด
            start_idx = max(0, path_index - visible_range)
            end_idx = min(len(grid_manager.path), path_index + visible_range)

            for i in range(start_idx, end_idx):
                col, row = grid_manager.path[i]
                tex = self._get_tile_texture(col, row)
                sx, sy = self.iso_to_screen_raw(col, row)
                Rectangle(
                    texture=tex,
                    pos=(sx + ox - TILE_HALF_W, sy + oy - TILE_HALF_H),
                    size=(TILE_IMG_SIZE, TILE_IMG_SIZE),
                )

            # === วาดตัวละครเพนกวิน ===
            if not penguin.is_dead:
                Color(0.1, 0.1, 0.1, 1)
                px, py = self.iso_to_screen_raw(penguin.col, penguin.row)
                Rectangle(
                    pos=(px + ox - 20, py + oy),
                    size=(40, 50),
                )
                # หัวเพนกวินสีขาว
                Color(1, 1, 1, 1)
                Rectangle(
                    pos=(px + ox - 10, py + oy + 30),
                    size=(20, 20),
                )
            else:
                # แสดงข้อความ Game Over
                pass

    def iso_to_screen_raw(self, col, row):
        """แปลงพิกัดตาราง → Isometric (ไม่รวม offset กล้อง)"""
        screen_x = (col - row) * TILE_HALF_W
        screen_y = (col + row) * TILE_HALF_H
        return screen_x, screen_y


class GamePlayScreen(Screen):
    """หน้าจอหลักตอนวิ่ง: เพนกวินวิ่งอัตโนมัติ ผู้เล่นกด ← → เลี้ยวตามทาง"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid = GridManager()
        self.penguin = Penguin()
        self.game_event = None

        # ตำแหน่งปัจจุบันของเพนกวินใน path (index)
        self.path_index = 0

        # ความเร็ว (ก้าว/วินาที) เริ่มต้น
        self.speed = INITIAL_SPEED
        self.move_timer = 0.0

        # สร้างเส้นทาง
        self.grid.reset()

        # ตั้งเพนกวินที่จุดเริ่มต้นของ path
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]

        self.renderer = KivyRenderer()
        self.add_widget(self.renderer)

        # HUD แสดงระยะทาง
        self.hud_label = Label(
            text="0 m",
            font_size='24sp',
            bold=True,
            pos_hint={'right': 0.98, 'top': 0.98},
            size_hint=(0.2, 0.05),
            color=(1, 1, 1, 1),
        )
        self.add_widget(self.hud_label)

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
        """Game Loop: เพนกวินวิ่งอัตโนมัติไปข้างหน้าตามเส้นทาง"""
        if self.penguin.is_dead:
            self.renderer.draw(self.grid, self.penguin, self.path_index)
            return

        # จำกัด dt เพื่อป้องกันเกมเร็วผิดปกติตอน lag
        dt = min(dt, 0.05)

        # นับเวลาเพื่อขยับตัวละครตามความเร็ว
        self.move_timer += dt
        step_interval = 1.0 / self.speed  # เช่น speed=2 → ขยับทุก 0.5 วินาที

        while self.move_timer >= step_interval:
            self.move_timer -= step_interval
            self._auto_move()

        # อัปเดต HUD
        dist = self.grid.get_distance_m()
        if dist >= 1000:
            self.hud_label.text = f"{dist / 1000:.1f} km"
        else:
            self.hud_label.text = f"{dist} m"

        # วาดภาพ
        self.renderer.draw(self.grid, self.penguin, self.path_index)

    def _auto_move(self):
        """ขยับเพนกวินไปตำแหน่งถัดไปใน path โดยอัตโนมัติ"""
        next_idx = self.path_index + 1

        if next_idx >= len(self.grid.path):
            # หมดทาง → สร้างเพิ่ม
            self.grid.generate_path(num_segments=20)

        if next_idx < len(self.grid.path):
            next_pos = self.grid.path[next_idx]
            self.penguin.col = next_pos[0]
            self.penguin.row = next_pos[1]
            self.path_index = next_idx
            self.grid.step_forward()

            # เพิ่มความเร็วตามระยะทาง
            self.speed = min(MAX_SPEED, INITIAL_SPEED + (self.grid.forward_tiles * 0.01))

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.penguin.is_dead:
            return False

        # ในตอนนี้เพนกวินวิ่งอัตโนมัติตามเส้นทาง
        # ปุ่ม ← → จะใช้เพิ่มเติมเมื่อมีระบบเลี้ยวแบบเลือกทางแยก
        if keycode[1] == 'escape':
            # Pause placeholder
            return True

        return False
