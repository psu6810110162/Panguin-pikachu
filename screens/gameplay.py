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
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color as GColor, Rectangle as GRect

from core.audio import AudioManager
from core.logger import logger
from core.config import (
    TARGET_FPS, TILE_W, TILE_H, TILE_IMG_H,
    CAMERA_LERP, SHAKE_DECAY, SHAKE_STOP, MAX_IDLE_TIME,
    DIR_LEFT, DIR_RIGHT,
    BOX_FRAME_W, BOX_FRAME_H, BOX_DRAW_W, BOX_DRAW_H,
    GEM_FRAME_W, GEM_FRAME_H, GEM_DRAW_W, GEM_DRAW_H, GEM_FLOAT_OFFSET,
    PENGUIN_DRAW_SIZE, PENGUIN_SPRITE_W, VIEW_RADIUS,
)
from game.grid import GridManager
from game.penguin import Penguin
from game.chaser import ChaserBlock
from game.biome import BiomeManager, BIOMES

# รายการรูปภาพแผ่นน้ำแข็งสำหรับพื้น (The Great Melt)
ICE_TILES = [
    'assets/great_melt/tiles/ice_tile_1.png',
    'assets/great_melt/tiles/ice_tile_2.png',
    'assets/great_melt/tiles/ice_tile_3.png',
    'assets/great_melt/tiles/ice_tile_4.png',
    'assets/great_melt/tiles/ice_tile_5.png',
    'assets/great_melt/tiles/ice_tile_6.png',
    'assets/great_melt/tiles/ice_tile_7.png',
    'assets/great_melt/tiles/ice_tile_8.png',
    'assets/great_melt/tiles/ice_tile_9.png',
    'assets/great_melt/tiles/ice_tile_10.png',
]

ARROW_RIGHT_IMG = 'assets/Component_UI/Vector/arrow_right_normal.png'  
ARROW_LEFT_IMG  = 'assets/Component_UI/Vector/arrow_left_normal.png'


class KivyRenderer(Widget):
    """
    คลาสสำหรับวาดภาพกราฟิก (Renderer)
    - จัดการระบบกล้อง (Camera) กระตุก (Shake) และเลื่อนตามตัวละคร
    - วาดแผ่นพื้น (Tiles), สิ่งกีดขวาง (Obstacles), ไอเทม (Gems) และแพนกวิน
    - แปลงพิกัดจากตาราง (Grid) เป็นพิกัดบนหน้าจอ (Screen) แบบ Isometric
    """
    def on_touch_down(self, touch): return False # ปิดการรับ Event สัมผัสบนตัว Widget นี้
    def on_touch_move(self, touch): return False
    def on_touch_up(self, touch):   return False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tile_textures = {}    # tile ice texture cache
        self.penguin_frame_cache = {}  # penguin animation frame cache
        self.anim_frame = 0
        self._anim_dt = 0          # dt ล่าสุดที่ส่งมาจาก update loop
        self._biome_textures = {}
        self._prev_biome_id = None
        # preload all biome tile sets
        for _b in BIOMES:
            self._biome_textures[_b.id] = [CoreImage(p).texture for p in _b.tile_paths]
        # โหลด Texture ของก้อนน้ำแข็งอุปสรรคตามสถานะต่างๆ
        self.box_assets = {
            'Idle':  CoreImage('assets/great_melt/obstacles/ice_idle.png').texture,
            'Hit':   CoreImage('assets/great_melt/obstacles/ice_hit.png').texture,
            'Break': CoreImage('assets/great_melt/obstacles/ice_break.png').texture,
        }
        # โหลด Texture ของ Ice Crystal Gem
        self.gem_texture = CoreImage('assets/great_melt/gems/ice_crystal_strip4.png').texture
        self.cam_x = None # ตัวแปรเก็บตำแหน่งกล้องแกน X
        self.cam_y = None # ตัวแปรเก็บตำแหน่งกล้องแกน Y
        self.shake_amount = 0 # ความแรงของการสั่นของกล้อง

    def trigger_shake(self, amount=10):
        """ สั่งให้กล้องสั่นเมื่อเกิดเหตุการณ์สำคัญ (เช่น พื้นถล่ม) """
        self.shake_amount = amount

    def _get_tile_texture(self, col, row, textures):
        """ ดึง Texture ของแผ่นพื้นตามพิกัด (ถ้าไม่มีจะสุ่มขึ้นมาใหม่) """
        key = (col, row)
        if key not in self.tile_textures:
            if len(self.tile_textures) > 500:  # ป้องกัน memory leak — ลบ entry เก่าออก
                for k in list(self.tile_textures)[:200]:
                    del self.tile_textures[k]
            self.tile_textures[key] = random.choice(textures)
        return self.tile_textures[key]

    def grid_to_screen(self, col, row):
        """ แปลงพิกัด Grid (Logical) เป็นพิกัดหน้าจอ (Pixel) แบบมุมมอง Isometric """
        x = (col - row) * (TILE_W // 2)
        y = (col + row) * (TILE_H // 2)
        return x, y

    def draw(self, grid_manager, penguin, path_index, chaser=None, is_shaking_floor=False, dt=0, biome=None):
        """ ฟังก์ชันหลักในการวาดทุกอย่างลงบน Canvas """
        self._anim_dt = dt
        # 1. คำนวณหาตำแหน่งที่กล้องควรจะหันไป (ศูนย์กลางคือแแพนกวิน)
        target_x, target_y = self.grid_to_screen(penguin.col, penguin.row)

        if self.cam_x is None:
            self.cam_x = target_x
            self.cam_y = target_y

        # 2. ระบบกล้องเคลื่อนที่แบบนุ่มนวล (Lerp) ให้ไหลตามตัวละคร
        self.cam_x += (target_x - self.cam_x) * CAMERA_LERP
        self.cam_y += (target_y - self.cam_y) * CAMERA_LERP

        # คำนวณหาค่า Offset เพื่อให้จัดกิ่งกลางหน้าจอ
        ox = Window.width  / 2 - self.cam_x
        oy = Window.height / 2 - self.cam_y
        
        # 3. ตรรกะการสั่นของกล้อง (Camera Shake)
        if self.shake_amount > 0:
            ox += random.uniform(-self.shake_amount, self.shake_amount)
            oy += random.uniform(-self.shake_amount, self.shake_amount)
            self.shake_amount *= SHAKE_DECAY
            if self.shake_amount < SHAKE_STOP: self.shake_amount = 0

        # Biome texture cache: clear if biome changed
        if biome and biome.id != self._prev_biome_id:
            self.tile_textures.clear()
            self._prev_biome_id = biome.id
            self._cur_biome = biome

        # Resolve current texture list
        if biome:
            cur_textures = self._biome_textures.get(biome.id, list(self._biome_textures.values())[0])
        else:
            cur_textures = self._biome_textures.get('arctic', list(self._biome_textures.values())[0])

        self.canvas.clear() # เคลียร์ภาพเก่าออกก่อนวาดใหม่
        with self.canvas:
            view_radius = VIEW_RADIUS
            visible_tiles = []
            visible_set = set()
            for col, row in grid_manager.path_set:
                if (penguin.col - view_radius <= col <= penguin.col + view_radius) and \
                   (penguin.row - view_radius <= row <= penguin.row + view_radius):
                    visible_tiles.append((col, row))
                    visible_set.add((col, row))

            # ใส่ตำแหน่งผู้เล่น
            p_pos = (penguin.col, penguin.row)
            if p_pos not in visible_set:
                visible_tiles.append(p_pos)
                visible_set.add(p_pos)

            # ใส่ตำแหน่ง Chaser (ถ้า active และอยู่ในระยะ)
            if chaser and chaser.active:
                c_pos = (chaser.col, chaser.row)
                if c_pos not in visible_set:
                    if (penguin.col - view_radius <= chaser.col <= penguin.col + view_radius) and \
                       (penguin.row - view_radius <= chaser.row <= penguin.row + view_radius):
                        visible_tiles.append(c_pos)
                        visible_set.add(c_pos)

            # 4. เรียงลำดับ Z-order (col+row สูง = ไกล = วาดก่อน)
            visible_tiles.sort(key=lambda t: t[0] + t[1], reverse=True)

            Color(1, 1, 1, 1)
            for col, row in visible_tiles:
                is_chaser_here = chaser and chaser.active and col == chaser.col and row == chaser.row

                if (col, row) in grid_manager.path_set:
                    # สีกระเบื้อง: แดงถ้า chaser อยู่, biome fork สีถ้า fork, biome tint ปกติ
                    if is_chaser_here:
                        Color(1, 0.18, 0.0, 1)
                    elif grid_manager.is_fork_tile(col, row):
                        if biome:
                            Color(*biome.fork_color)
                        else:
                            Color(1, 0.9, 0.4, 1)
                    else:
                        if biome:
                            Color(*biome.tile_tint)
                        else:
                            Color(1, 1, 1, 1)

                    tex    = self._get_tile_texture(col, row, cur_textures)
                    sx, sy = self.grid_to_screen(col, row)
                    draw_x = sx + ox - (TILE_W // 2)
                    draw_y = sy + oy - (TILE_IMG_H - TILE_H // 2)
                    Rectangle(texture=tex, pos=(draw_x, draw_y), size=(TILE_W, TILE_IMG_H))

                    if is_chaser_here:
                        # วาด Chaser block ทับไปเลย ไม่วาด obstacle/gem ตรงนั้น
                        self._draw_chaser(draw_x, draw_y + (TILE_IMG_H // 2), chaser.pulse_alpha())
                    else:
                        # วาดสิ่งกีดขวางและ Gem ปกติ
                        obs = grid_manager.get_obstacle_at(col, row)
                        if obs and obs.active:
                            self._draw_obstacle(obs, draw_x, draw_y + (TILE_IMG_H // 2), ox, oy)
                        gem = grid_manager.get_gem_at(col, row)
                        if gem and gem.active:
                            self._draw_gem(gem, draw_x, draw_y + (TILE_IMG_H // 2), ox, oy)

                # 5. วาดแพนกวินในลำดับ Z ที่ถูกต้อง
                if col == penguin.col and row == penguin.row:
                    p_ox, p_oy = ox, oy
                    if is_shaking_floor:
                        p_ox += random.uniform(-3, 3)
                        p_oy += random.uniform(-3, 3)
                    self._draw_penguin(penguin, p_ox, p_oy)

            # Atmosphere overlay (biome tint over full screen)
            if biome and biome.atmo_tint[3] > 0:
                r2, g2, b2, a2 = biome.atmo_tint
                Color(r2, g2, b2, a2)
                Rectangle(pos=(0, 0), size=(Window.width, Window.height))
                Color(1, 1, 1, 1)

    def _draw_penguin(self, penguin, ox, oy):
        """ วาดแพนกวินพร้อมจัดการแอนิเมชันและสกิน """
        if penguin.is_dead:
            # กรณีแพนกวินตาย (เช่น ตกหลุม)
            px, py = self.grid_to_screen(penguin.col, penguin.row)
            skin_path = penguin.get_skin_path(action='Fall')
            if skin_path not in self.penguin_frame_cache:
                self.penguin_frame_cache[skin_path] = CoreImage(skin_path).texture
            skin_tex = self.penguin_frame_cache[skin_path]
            # พลิกรูปถ้าหันหน้าซ้าย (PENGUIN_SPRITE_W=32 คือความกว้างจริงของ frame ใน spritesheet)
            if penguin.facing_left:
                skin_tex = skin_tex.get_region(PENGUIN_SPRITE_W, 0, -PENGUIN_SPRITE_W, PENGUIN_SPRITE_W)
            pw, ph = PENGUIN_DRAW_SIZE, PENGUIN_DRAW_SIZE
            Color(1, 1, 1, 1)
            Rectangle(texture=skin_tex, pos=(px + ox - pw // 2, py + oy), size=(pw, ph))
        else:
            # กรณีแพนกวินกำลังวิ่ง (Idle/Run State)
            px, py = self.grid_to_screen(penguin.col, penguin.row)
            self.anim_frame = (self.anim_frame + self._anim_dt * 12) % 11  # 12 FPS คงที่
            frame_idx = int(self.anim_frame)
            skin_path = penguin.get_skin_path(action='Idle')

            # ดึงเฉพาะส่วน (Region) จาก Spritesheet — ใช้ PENGUIN_SPRITE_W=32 สำหรับ spritesheet frame
            cache_key = f"{skin_path}_{frame_idx}_{'L' if penguin.facing_left else 'R'}"
            if cache_key not in self.penguin_frame_cache:
                if skin_path not in self.penguin_frame_cache:
                    self.penguin_frame_cache[skin_path] = CoreImage(skin_path).texture
                full_tex = self.penguin_frame_cache[skin_path]
                if penguin.facing_left:
                    self.penguin_frame_cache[cache_key] = full_tex.get_region(
                        (frame_idx + 1) * PENGUIN_SPRITE_W, 0, -PENGUIN_SPRITE_W, PENGUIN_SPRITE_W)
                else:
                    self.penguin_frame_cache[cache_key] = full_tex.get_region(
                        frame_idx * PENGUIN_SPRITE_W, 0, PENGUIN_SPRITE_W, PENGUIN_SPRITE_W)

            skin_tex = self.penguin_frame_cache[cache_key]
            pw, ph = PENGUIN_DRAW_SIZE, PENGUIN_DRAW_SIZE
            Color(1, 1, 1, 1)
            Rectangle(texture=skin_tex, pos=(px + ox - pw // 2, py + oy), size=(pw, ph))

    def _draw_obstacle(self, obs, tx, ty, ox, oy):
        """ วาดสิ่งกีดขวางแบบซ้อนทับกันตามขนาด (Stacking) """
        state = obs.state
        frame = int(obs.anim_frame)
        full_tex = self.box_assets.get(state)
        tex = full_tex.get_region(frame * BOX_FRAME_W, 0, BOX_FRAME_W, BOX_FRAME_H)
        bw, bh = BOX_DRAW_W, BOX_DRAW_H
        Color(1, 1, 1, 1)
        for i in range(obs.size): # วาดซ้อนกันเป็นชั้นๆ ตาม Size (1-5)
            y_offset = i * (bh * 0.6)
            Rectangle(texture=tex, pos=(tx + (TILE_W - bw) // 2, ty + y_offset), size=(bw, bh))

    def _draw_gem(self, gem, tx, ty, ox, oy):
        """ วาด Gem พร้อมเอฟเฟกต์ลอยนิ่่งๆ และหมุนได้ """
        frame_idx = gem.anim_frame
        tex = self.gem_texture.get_region(frame_idx * GEM_FRAME_W, 0, GEM_FRAME_W, GEM_FRAME_H)
        float_offset = GEM_FLOAT_OFFSET
        gw, gh = GEM_DRAW_W, GEM_DRAW_H
        Color(1, 1, 1, 1)
        Rectangle(texture=tex, pos=(tx + (TILE_W - gw) // 2, ty + float_offset), size=(gw, gh))

    def _draw_chaser(self, tx, ty, pulse_a):
        """ วาด Chaser — บล็อกยักษ์สีแดงที่ไล่ตามผู้เล่น พร้อม pulse glow """
        bw = int(BOX_DRAW_W * 2.4)
        bh = int(BOX_DRAW_H * 2.4)
        cx = tx + (TILE_W - bw) // 2

        # Danger glow — use biome chaser_glow if available
        cur_biome = getattr(self, '_cur_biome', None)
        if cur_biome:
            gr, gg, gb = cur_biome.chaser_glow
        else:
            gr, gg, gb = 1.0, 0.05, 0.0
        Color(gr, gg, gb, pulse_a * 0.55)
        Rectangle(pos=(cx - 14, ty - 8), size=(bw + 28, bh + 16))

        # Chaser block — red-tinted oversized ice block
        full_tex = self.box_assets['Idle']
        tex = full_tex.get_region(0, 0, BOX_FRAME_W, BOX_FRAME_H)
        Color(1, 0.12, 0.0, 1)
        Rectangle(texture=tex, pos=(cx, ty), size=(bw, bh))

        # White hot core highlight
        Color(1, 0.85, 0.80, pulse_a * 0.35)
        Rectangle(pos=(cx + bw // 4, ty + bh // 3), size=(bw // 2, bh // 3))

        Color(1, 1, 1, 1)  # reset


class PauseOverlay(FloatLayout):
    """ คลาสสำหรับจัดการ Overlay ตอนกดหยุดเกม (ป้องกันการสัมผัสพื้นหลัง) """
    def on_touch_down(self, touch):
        if self.opacity == 0: return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.opacity == 0: return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.opacity == 0: return False
        return super().on_touch_up(touch)


class IconButton(ButtonBehavior, Image):
    """ ปุ่มที่เป็นรูปภาพและมีพฤติกรรมเหมือนปุ่มมาตรฐาน """
    pass


class ArrowButton(ButtonBehavior, Image):
    """ ปุ่มลูกศรควบคุมทิศทาง พร้อมระบบแอนิเมชันตอบสนองการกด """
    def __init__(self, move_callback=None, **kwargs):
        super().__init__(**kwargs)
        self._move_callback = move_callback
        self.bind(on_press=self.handle_press)
        self.bind(on_release=self.handle_release)
    
    def collide_point(self, x, y):
        # ตรวจสอบการสัมผัสภายในขอบเขตของปุ่ม
        return (self.x <= x <= self.right and self.y <= y <= self.top)

    def handle_press(self, *args):
        # แอนิเมชันปุ่มขยายตัวเล็กน้อยเมื่อกด
        Animation(size=(150, 150), duration=0.08, t='out_back').start(self)
        if self._move_callback:
            self._move_callback()

    def handle_release(self, *args):
        # แอนิเมชันปุ่มกลับสู่ขนาดเดิมเมื่อปล่อย
        Animation(size=(120, 120), duration=0.1, t='out_quad').start(self)


class GamePlayScreen(Screen):
    """
    คลาสหน้าจอหลักของการเล่นเกม (Gameplay Screen)
    - ควบคุมตรรกะของเกม (Game Engine), จัดการ Input จากผู้เล่น
    - อัปเดตสถานะของตัวละคร และตรวจสอบเงื่อนไขแพ้-ชนะ
    - จัดการ UI (HUD, ปุ่มกด) และการเปลี่ยนหน้าจอ (Pause, GameOver)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid       = GridManager() # จัดการแผนที่และเส้นทาง
        self.penguin    = Penguin()     # จัดการตัวละครแพนกวิน
        self.game_event = None          # ตัวแปรเก็บตารางเวลา (Schedule) ของ Game Loop
        self.path_index = 0             # ตำแหน่งปัจจุบันบนเส้นทาง (Index)
        self.gems_collected = 0         # จำนวน Gem ที่เก็บได้ในรอบนี้
        
        # รีเซ็ตแผนที่และตั้งตำแหน่งเริ่มต้น
        self.grid.reset()
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]
        
        self.idle_timer = 0             # ตัวนับเวลาที่ห้ามยืนนิ่งเฉยๆ
        self.MAX_IDLE_TIME = MAX_IDLE_TIME
        self.game_started = False       # สถานะว่าเริ่มวิ่งก้าวแรกหรือยัง
        self.chaser = ChaserBlock()     # บล็อกไล่ตามที่ตามมาเรื่อยๆ

        # สร้าง Renderer สำหรับวาดภาพ
        self.renderer = KivyRenderer()
        self.add_widget(self.renderer)

        # สร้างส่วนแสดงผลคะแนน (HUD)
        self.hud_label = Label(
            text="🌡 0 m  💎 0", font_size='24sp', bold=True,
            font_name='assets/Component_UI/Font/Kenney Future.ttf',
            pos_hint={'right': 0.98, 'top': 0.98},
            size_hint=(0.3, 0.05), color=(1, 1, 1, 1),
            halign='right'
        )
        self.hud_label.bind(size=self.hud_label.setter('text_size'))
        self.add_widget(self.hud_label)

        # สร้างปุ่มควบคุมการเลี้ยว (ซ้าย/ขวา)
        OFFSET = 0.2
        self.btn_left = ArrowButton(
            move_callback=lambda: self._move(DIR_LEFT),
            source=ARROW_LEFT_IMG, size_hint=(None, None),
            size=(120, 120), allow_stretch=True, keep_ratio=True,
            pos_hint={'center_x': 0.5 - OFFSET, 'center_y': 0.08},
        )
        self.add_widget(self.btn_left)

        self.btn_right = ArrowButton(
            move_callback=lambda: self._move(DIR_RIGHT),
            source=ARROW_RIGHT_IMG, size_hint=(None, None),
            size=(120, 120), allow_stretch=True, keep_ratio=True,
            pos_hint={'center_x': 0.5 + OFFSET, 'center_y': 0.08},
        )
        self.add_widget(self.btn_right)

        # ปุ่มหยุดเกมชั่วคราว (Pause)
        self.pause_btn = Button(
            size_hint=(None, None), size=(60, 60),
            pos_hint={'x': 0.02, 'top': 0.98},
            background_normal='assets/Component_UI/Stop/pause_on.png',
            background_down='assets/Component_UI/Stop/pause_down.png',
            background_color=(1, 1, 1, 1), border=(0, 0, 0, 0),
        )
        self.pause_btn.bind(on_release=lambda _: self.pause_game())
        self.add_widget(self.pause_btn)

        # Biome manager and announcement label
        self.biome_mgr = BiomeManager()
        self.biome_label = Label(
            text='', font_size='30sp', bold=True,
            font_name='assets/Component_UI/Font/Kenney Future.ttf',
            pos_hint={'center_x': 0.5, 'center_y': 0.60},
            size_hint=(0.9, 0.12),
            color=(1, 1, 1, 0),
            halign='center',
        )
        self.add_widget(self.biome_label)

        # หน้าต่างเมนูตอนกดหยุด (Pause Overlay)
        self.pause_overlay = PauseOverlay(opacity=0, disabled=True)
        with self.pause_overlay.canvas.before:
            GColor(0, 0, 0, 0.6) # สีดำโปร่งแสงเป็นพื้นหลัง
            self._overlay_bg = GRect(pos=self.pause_overlay.pos, size=self.pause_overlay.size)
        self.pause_overlay.bind(
            pos=lambda o, v: setattr(self._overlay_bg, 'pos', v),
            size=lambda o, v: setattr(self._overlay_bg, 'size', v),
        )

        # กล่องรวมปุ่มเมนูในหน้า Pause (Back, Reset, Resume)
        btn_box = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None), size=(360, 100),
            pos_hint={'center_x': 0.5, 'center_y': 0.35},
            spacing=20,
        )
        for img_n, img_d, cb in [
            ('assets/Component_UI/Backtomanu/backtomenu.png',
             'assets/Component_UI/Backtomanu/backtomenu_down.png', self.go_home),
            ('assets/Component_UI/Reset/reset_up.png',
             'assets/Component_UI/Reset/reset_down.png',           self.restart_game),
            ('assets/Component_UI/Resume/resume_on.png',
             'assets/Component_UI/Resume/resume_down.png',         self.resume_game),
        ]:
            b = IconButton(
                source=img_n, size_hint=(None, None), size=(100, 100),
                allow_stretch=True, keep_ratio=True,
            )
            b.bind(
                on_press=lambda x, d=img_d: setattr(x, 'source', d),
                on_release=lambda x, n=img_n, c=cb: (setattr(x, 'source', n), c()),
            )
            btn_box.add_widget(b)

        self.pause_overlay.add_widget(btn_box)
        self.add_widget(self.pause_overlay)
        self._keyboard = None 

    def on_enter(self):
        """ ทำงานเมื่อเข้าสู่หน้าจอนี้ (เริ่มเล่นรอบใหม่/เข้าสู่รอบถัดไป) """
        from core.state import StateManager
        logger.info("เข้าสู่หน้า GamePlay")
        
        # เชื่อมต่อคีย์บอร์ดเพื่อรับคำสั่ง (ลูกศรซ้าย/ขวา)
        if not self._keyboard:
            self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
            self._keyboard.bind(on_key_down=self._on_keyboard_down)
            self._keyboard.bind(on_key_up=self._on_keyboard_up)

        # โหลดสกินที่ผู้เล่นเลือกไว้ และเริ่มเสียงเพลงประกอบ
        self.penguin.equip_skin(StateManager().selected_skin)
        self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS) # เริ่มเกมลูป
        AudioManager().play_bgm('Bgm.gameplay.mp3')
        
        # รีเซ็ตพิกัดและข้อมูลทุกอย่างให้พร้อมสำหรับเกมรอบใหม่
        self.grid.reset()
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]
        self.penguin.is_dead = False
        self.path_index = 0
        self.gems_collected = 0
        self.idle_timer = 0
        self.game_started = False
        self.chaser.reset()
        self.renderer.cam_x = None # รีเซ็ตกล้อง
        self.biome_mgr.reset()

    def on_leave(self):
        """ ทำงานเมื่อเดินออกจากหน้าจอนี้ (หยุดเกมลูปและเสียง) """
        if self.game_event:
            self.game_event.cancel()
            self.game_event = None
        
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard.unbind(on_key_up=self._on_keyboard_up)
            self._keyboard = None

    def update(self, dt):
        """ ฟังก์ชัน Game Loop หลักที่รันทุกเฟรม """
        # 1. อัปเดตระยะทางบนหน้าจอ (HUD)
        dist = self.grid.get_distance_m()
        dist_str = f"{dist / 1000:.1f} km" if dist >= 1000 else f"{dist} m"
        self.hud_label.text = f"🌡 {dist_str}  💎 {self.gems_collected}"

        # Update biome and HUD color
        biome, biome_changed = self.biome_mgr.update(dist)
        self.hud_label.color = list(biome.hud_color)
        if biome_changed:
            Animation.cancel_all(self.biome_label)
            self.biome_label.text = biome.name
            self.biome_label.color = list(biome.hud_color[:3]) + [1.0]
            Animation(color=list(biome.hud_color[:3]) + [0.0], duration=2.5, t='out_quad').start(self.biome_label)

        # 2. สั่งให้อุปสรรคและแผ่นพื้นหลังผู้เล่นอัปเดต/ทำลายทิ้งเพื่อประหยัด Memory
        self.grid.update_obstacles(dt, view_radius=VIEW_RADIUS, penguin_pos=(self.penguin.col, self.penguin.row))
        self.grid.cleanup_behind(self.path_index)

        # 3. อัปเดต Chaser และตรวจว่าตามทันผู้เล่นหรือยัง
        if not self.penguin.is_dead:
            dist = self.grid.get_distance_m()
            # Spawn chaser หลังจากผู้เล่นมีระยะนำหน้าพอแล้ว
            if not self.chaser.active and self.path_index >= ChaserBlock.ACTIVATE_AFTER:
                self.chaser.activate(self.path_index - ChaserBlock.START_GAP, self.grid.path)
            if self.chaser.active:
                caught = self.chaser.update(dt, self.path_index, dist, self.grid.path)
                if caught:
                    self.penguin.is_dead = True
                    AudioManager().play_sfx('down')
                    self.renderer.trigger_shake(20)
                    Clock.schedule_once(lambda dt: self._go_gameover(), 0.8)

        # 4. ตรวจสอบการยืนนิ่งถล่มของพื้น
        if not self.penguin.is_dead and self.game_started:
            self.idle_timer += dt
            is_shaking = self.idle_timer > (self.MAX_IDLE_TIME - 1.0)

            if self.idle_timer >= self.MAX_IDLE_TIME:
                logger.warning(f"พื้นถล่ม! ยืนนิ่งนานเกินไปที่ ({self.penguin.col}, {self.penguin.row})")
                self.grid.remove_tile(self.penguin.col, self.penguin.row)
                self.penguin.is_dead = True
                AudioManager().play_sfx('down')
                Clock.schedule_once(lambda dt: self._go_gameover(), 0.8)

            self.renderer.draw(self.grid, self.penguin, self.path_index,
                               chaser=self.chaser, is_shaking_floor=is_shaking, dt=dt, biome=biome)
        else:
            self.renderer.draw(self.grid, self.penguin, self.path_index,
                               chaser=self.chaser, dt=dt, biome=biome)

    def _move(self, direction):
        """ ฟังก์ชันจัดการการเคลื่อนที่เมื่อกดปุ่มลูกศร (รับเวกเตอร์ทิศทาง) """
        if self.penguin.is_dead:
            return

        # ปรับหน้าตาแพนกวินให้หันไปตามทิศที่กด
        if direction == DIR_LEFT:
            self.penguin.facing_left = True
        elif direction == DIR_RIGHT:
            self.penguin.facing_left = False

        # คำนวณพิกัดใหม่ที่กำลังจะเดินไป
        new_col = self.penguin.col + direction[0]
        new_row = self.penguin.row + direction[1]

        # 1. ตรวจสอบว่ามีสิ่งกีดขวาง (Obstacle) ขวางทางอยู่หรือไม่
        obs = self.grid.get_obstacle_at(new_col, new_row)
        if obs and obs.active:
            if obs.hit():  # ทุบบล็อก (เสียงเล่นใน hit() แล้ว)
                self.idle_timer = 0
                self.game_started = True
                return  # ยังเดินผ่านไม่ได้ รอ animation จบก่อน
            else:
                return

        # 2. ตรวจสอบว่ามี Gem ในช่องนั้นหรือไม่
        gem = self.grid.get_gem_at(new_col, new_row)
        if gem and gem.active:
            val = gem.collect() # เก็บไอเทม
            self.gems_collected += val
            AudioManager().play_sfx('coin') # เสียงเก็บเหรียญ
            self.grid.gems.pop((new_col, new_row), None)

        # 3. ขยับตัวละครไปยังพิกัดใหม่
        self.penguin.col = new_col
        self.penguin.row = new_row
        self.game_started = True

        # 4. ตรวจสอบว่าเหยียบอยู่บนเส้นทางที่ถูกต้องหรือไม่
        if self.grid.is_on_path(new_col, new_row):
            self.grid.step_forward()
            idx = self.grid.get_path_index(new_col, new_row)
            if idx >= 0:
                self.path_index = idx
                self.grid.extend_if_needed(self.path_index) # ขยายแผนที่ข้างหน้าถ้าเดินมาไกลแล้ว
                AudioManager().play_sfx('jump') # เสียงกระโดด
                self.renderer.trigger_shake(5)  # กล้องสั่นเล็กน้อยเพิ่มความมันส์
                self.idle_timer = 0 
            
            # ถ้าถึงปลายทางของ Array แผนที่ (กรณีมีลิมิต)
            if self.path_index == len(self.grid.path) - 1:
                logger.info(f"ชนะแล้ว! วิ่งถึงเส้นชัยด้วยระยะ {self.grid.get_distance_m()} m")
                self.manager.current = 'gameover'
        else:
            # ตกพื้น/ออกนอกเส้นทาง
            self.penguin.is_dead = True
            AudioManager().play_sfx('down')
            logger.info(f"ตก! ระยะ {self.grid.get_distance_m()} m")
            Clock.schedule_once(lambda dt: self._go_gameover(), 0.5)

    def _go_gameover(self):
        """ เปลี่ยนหน้าจอไปหน้าจบเกม (Game Over) """
        self.manager.current = 'gameover'

    def pause_game(self):
        """ หยุดเกมชั่วคราว """
        if self.game_event:
            self.game_event.cancel() # หยุด Game Loop
            self.game_event = None
        self.pause_overlay.opacity = 1 # แสดงเมนู Pause
        self.pause_overlay.disabled = False
        AudioManager().play_sfx('click')

    def resume_game(self):
        """ กลับมาเล่นเกมต่อจากที่หยุดไว้ """
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True
        if not self.game_event:
            self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS) # เริ่มลูปใหม่อีกครั้ง
        AudioManager().play_sfx('click')

    def restart_game(self):
        """ เริ่มเล่นเกมใหม่ทันที (Reset ทุกอย่าง) """
        AudioManager().play_sfx('click')
        self.grid.reset()
        self.penguin.is_dead = False
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]
        self.path_index = 0
        self.gems_collected = 0
        self.idle_timer = 0
        self.game_started = False
        self.chaser.reset()
        self.renderer.cam_x = None
        self.renderer.cam_y = None
        self.biome_mgr.reset()
        Animation.cancel_all(self.biome_label)
        self.biome_label.color = (1, 1, 1, 0)
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True
        if not self.game_event:
            self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)

    def go_home(self):
        """ ออกจากการเล่นกลับไปยังหน้าเมนูหลัก """
        AudioManager().play_sfx('click')
        if self.game_event:
            self.game_event.cancel()
            self.game_event = None
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'menu'), 0.2)

    def _keyboard_closed(self):
        """ เรียกเมื่อคีย์บอร์ดถูกปิด """
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard.unbind(on_key_up=self._on_keyboard_up)
            self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """ จัดการคำสั่งจากคีย์บอร์ด (กดปุ่มลง) """
        if self.penguin.is_dead:
            return False
        if not self.game_event:
            return False
        if keycode[1] == 'left':
            self.btn_left.handle_press() # จำลองการกดปุ่มซ้ายบนจอ
            return True
        elif keycode[1] == 'right':
            self.btn_right.handle_press() # จำลองการกดปุ่มขวาบนจอ
            return True
        return False

    def _on_keyboard_up(self, keyboard, keycode):
        """ จัดการคำสั่งจากคีย์บอร์ด (ปล่อยปุ่ม) """
        if not self.game_event:
            return False
        if keycode[1] == 'left':
            self.btn_left.handle_release()
            return True
        elif keycode[1] == 'right':
            self.btn_right.handle_release()
            return True
        return False