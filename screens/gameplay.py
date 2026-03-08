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

ARROW_RIGHT_IMG = 'assets/Component_UI/Vector/arrow_right_normal.png'  
ARROW_LEFT_IMG  = 'assets/Component_UI/Vector/arrow_left_normal.png'

DIR_LEFT  = (0, 1)   # iso ซ้าย
DIR_RIGHT = (1, 0)   # iso ขวา


class KivyRenderer(Widget):

    def on_touch_down(self, touch):
        return False
    def on_touch_move(self, touch):
        return False
    def on_touch_up(self, touch):
        return False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tile_textures = {}
        self.anim_frame = 0  
        self._grass_textures = [CoreImage(p).texture for p in GRASS_TILES]
        
        self.box_assets = {
            'Idle': CoreImage('assets/pixelAdventure/Free/Items/Boxes/Box2/Idle.png').texture,
            'Hit': CoreImage('assets/pixelAdventure/Free/Items/Boxes/Box2/Hit (28x24).png').texture,
            'Break': CoreImage('assets/pixelAdventure/Free/Items/Boxes/Box2/Break.png').texture
        }
        self.gem_texture = CoreImage('assets/Gem/Coin_Gems/spr_coin_strip4.png').texture

        # ── FIX 1: ตั้ง cam เป็น None
        # เฟรมแรกจะ snap ทันที ไม่ lerp จาก (0,0)
        # ซึ่งเป็นสาเหตุที่กล้องวิ่งหนีไปขวาตอนเริ่ม
        self.cam_x = None
        self.cam_y = None
        
        # สำหรับ Screen Shake
        self.shake_amount = 0

    def trigger_shake(self, amount=10):
        self.shake_amount = amount

    def _get_tile_texture(self, col, row):
        key = (col, row)
        if key not in self.tile_textures:
            self.tile_textures[key] = random.choice(self._grass_textures)
        return self.tile_textures[key]

    def grid_to_screen(self, col, row):
        x = (col - row) * (TILE_W // 2)
        y = (col + row) * (TILE_H // 2)
        return x, y

    def draw(self, grid_manager, penguin, path_index, is_shaking_floor=False):
        target_x, target_y = self.grid_to_screen(penguin.col, penguin.row)

        if self.cam_x is None:
            self.cam_x = target_x
            self.cam_y = target_y

        self.cam_x += (target_x - self.cam_x) * 0.15
        self.cam_y += (target_y - self.cam_y) * 0.15

        ox = Window.width  / 2 - self.cam_x
        oy = Window.height / 2 - self.cam_y
        
        # Apply Screen Shake
        if self.shake_amount > 0:
            ox += random.uniform(-self.shake_amount, self.shake_amount)
            oy += random.uniform(-self.shake_amount, self.shake_amount)
            self.shake_amount *= 0.8
            if self.shake_amount < 0.5: self.shake_amount = 0

        self.canvas.clear()
        with self.canvas:
            view_radius = 15
            visible_tiles = []
            
            # รวบรวม Tiles ที่อยู่ในระยะมองเห็น
            for col, row in grid_manager.path_set:
                if (penguin.col - view_radius <= col <= penguin.col + view_radius) and \
                   (penguin.row - view_radius <= row <= penguin.row + view_radius):
                    visible_tiles.append((col, row))

            # [FIX] เพื่อให้วาดตัวละครได้แม้พื้นจะถล่มไปแล้ว (แต่ยังตกอยู่)
            # เพิ่มพิกัดที่ตัวละครยืนอยู่เข้าไปในลิสต์เพื่อวาด Penguin ในลำดับการวาด (isometric sorting)
            p_pos = (penguin.col, penguin.row)
            if p_pos not in visible_tiles:
                visible_tiles.append(p_pos)

            visible_tiles.sort(key=lambda t: t[0] + t[1], reverse=True)

            Color(1, 1, 1, 1)
            for col, row in visible_tiles:
                # วาดพื้น เฉพาะตัวที่มีอยู่ใน path_set
                if (col, row) in grid_manager.path_set:
                    if grid_manager.is_fork_tile(col, row):
                        Color(1, 0.9, 0.4, 1) 
                    else:
                        Color(1, 1, 1, 1)

                    tex    = self._get_tile_texture(col, row)
                    sx, sy = self.grid_to_screen(col, row)
                    draw_x = sx + ox - (TILE_W // 2)
                    draw_y = sy + oy - (TILE_IMG_H - TILE_H // 2)
                    Rectangle(texture=tex, pos=(draw_x, draw_y), size=(TILE_W, TILE_IMG_H))

                    obs = grid_manager.get_obstacle_at(col, row)
                    if obs and obs.active:
                        self._draw_obstacle(obs, draw_x, draw_y + (TILE_IMG_H // 2), ox, oy)

                    gem = grid_manager.get_gem_at(col, row)
                    if gem and gem.active:
                        self._draw_gem(gem, draw_x, draw_y + (TILE_IMG_H // 2), ox, oy)

                # วาด Penguin เสมอเมื่อถึงตำแหน่งพิกัดของมัน (ไม่ว่าจะยังมีพื้นหรือไม่)
                # เพื่อให้ Z-index ถูกต้อง (อยู่หลังแผ่นที่อยู่ถัดไป)
                if col == penguin.col and row == penguin.row:
                    p_ox, p_oy = ox, oy
                    if is_shaking_floor:
                        p_ox += random.uniform(-3, 3)
                        p_oy += random.uniform(-3, 3)
                    self._draw_penguin(penguin, p_ox, p_oy)

    def _draw_penguin(self, penguin, ox, oy):
        """วาดตัวละคร (Animated Skin)"""
        if penguin.is_dead:
            px, py = self.grid_to_screen(penguin.col, penguin.row)
            skin_path = penguin.get_skin_path(action='Fall')
            
            if skin_path not in self.tile_textures:
                self.tile_textures[skin_path] = CoreImage(skin_path).texture
            
            skin_tex = self.tile_textures[skin_path]
            if penguin.facing_left:
                skin_tex = skin_tex.get_region(32, 0, -32, 32)
            
            pw, ph = 64, 64
            Color(1, 1, 1, 1)
            Rectangle(texture=skin_tex, pos=(px + ox - pw // 2, py + oy), size=(pw, ph))
        else:
            px, py = self.grid_to_screen(penguin.col, penguin.row)
            self.anim_frame = (self.anim_frame + 0.2) % 11
            frame_idx = int(self.anim_frame)
            
            skin_path = penguin.get_skin_path(action='Idle')
            cache_key = f"{skin_path}_{frame_idx}_{'L' if penguin.facing_left else 'R'}"
            
            if cache_key not in self.tile_textures:
                if skin_path not in self.tile_textures:
                    self.tile_textures[skin_path] = CoreImage(skin_path).texture
                full_tex = self.tile_textures[skin_path]
                
                if penguin.facing_left:
                    self.tile_textures[cache_key] = full_tex.get_region((frame_idx + 1) * 32, 0, -32, 32)
                else:
                    self.tile_textures[cache_key] = full_tex.get_region(frame_idx * 32, 0, 32, 32)
            
            skin_tex = self.tile_textures[cache_key]
            pw, ph = 64, 64
            Color(1, 1, 1, 1)
            Rectangle(texture=skin_tex, pos=(px + ox - pw // 2, py + oy), size=(pw, ph))

    def _draw_obstacle(self, obs, tx, ty, ox, oy):
        """วาดกล่อง Box2 พร้อมแอนิเมชันและซ้อนกันตาม Size"""
        state = obs.state
        frame = int(obs.anim_frame)
        full_tex = self.box_assets.get(state)
        
        # ตัดเฟรม (Box2 ขนาด 28x24)
        # Spritesheet แนวนอน
        tex = full_tex.get_region(frame * 28, 0, 28, 24)
        
        bw, bh = 56, 48 # ขยายขนาดจาก 28x24
        
        Color(1, 1, 1, 1)
        # วาดซ้อนกันตาม Size
        for i in range(obs.size):
            y_offset = i * (bh * 0.6) # ซ้อนเหลื่อมกันเล็กน้อย
            Rectangle(
                texture=tex,
                pos=(tx + (TILE_W - bw) // 2, ty + y_offset),
                size=(bw, bh)
            )

    def _draw_gem(self, gem, tx, ty, ox, oy):
        """วาด Gem แบบอนิเมชัน"""
        # คำนวณ Region จากเฟรมปัจจุบัน (16x16 ต่อเฟรม)
        frame_idx = gem.anim_frame
        tex = self.gem_texture.get_region(frame_idx * 16, 0, 16, 16)
        
        # วาด Gem ให้ลอยอยู่เหนือพื้นนิดหน่อย
        float_offset = 12 
        gw, gh = 32, 32 # ขยายจาก 16x16
        
        Color(1, 1, 1, 1)
        Rectangle(
            texture=tex, 
            pos=(tx + (TILE_W - gw) // 2, ty + float_offset), 
            size=(gw, gh)
        )


class PauseOverlay(FloatLayout):
    def on_touch_down(self, touch):
        if self.opacity == 0: return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.opacity == 0: return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.opacity == 0: return False
        return super().on_touch_up(touch)

class ArrowButton(ButtonBehavior, Image):

    def __init__(self, move_callback=None, **kwargs):
        super().__init__(**kwargs)
        self._move_callback = move_callback      # รับ callback ผ่าน __init__
        self.bind(on_press=self.handle_press)
        self.bind(on_release=self.handle_release)
    
    def collide_point(self, x, y):
        return (self.x <= x <= self.right and self.y <= y <= self.top)

    def handle_press(self, *args):
        Animation(
            size=(150, 150),
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
        self.gems_collected = 0
        self.grid.reset()
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]
        self.idle_timer = 0
        self.MAX_IDLE_TIME = 2.0 
        self.game_started = False # จะเริ่มจับเวลาถล่มเมื่อก้าวแรกเดิน

        # Renderer — cam_x/cam_y = None → snap อัตโนมัติ
        self.renderer = KivyRenderer()
        self.add_widget(self.renderer)

        # HUD
        self.hud_label = Label(
            text="0 m | 💎 0", font_size='24sp', bold=True,
            font_name='assets/Component_UI/Font/Kenney Future.ttf',
            pos_hint={'right': 0.98, 'top': 0.98},
            size_hint=(0.3, 0.05), color=(1, 1, 1, 1),
            halign='right'
        )
        self.hud_label.bind(size=self.hud_label.setter('text_size'))
        self.add_widget(self.hud_label)

        # ปุ่ม
        OFFSET = 0.2
        self.btn_left = ArrowButton(
            move_callback=lambda: self._move(DIR_LEFT),  # ส่ง callback ผ่าน __init__
            source=ARROW_LEFT_IMG, size_hint=(None, None),
            size=(120, 120), allow_stretch=True, keep_ratio=True, pos_hint={'center_x': 0.5 - OFFSET, 'center_y': 0.08},
        )
        self.add_widget(self.btn_left)

        self.btn_right = ArrowButton(
            move_callback=lambda: self._move(DIR_RIGHT), # ส่ง callback ผ่าน __init__
            source=ARROW_RIGHT_IMG, size_hint=(None, None),
            size=(120, 120), allow_stretch=True, keep_ratio=True, pos_hint={'center_x': 0.5 + OFFSET, 'center_y': 0.08},
        )
        self.add_widget(self.btn_right)

        self.pause_btn = Button(
            size_hint=(None, None),
            size=(60, 60),
            pos_hint={'x': 0.02, 'top': 0.98},
            background_normal='assets/Component_UI/Stop/pause_on.png',
            background_down='assets/Component_UI/Stop/pause_down.png',
            background_color=(1, 1, 1, 1),
            border=(0, 0, 0, 0),
        )
        self.pause_btn.bind(on_release=lambda _: self.pause_game())
        self.add_widget(self.pause_btn)

        # ── Pause Overlay ──
        self.pause_overlay = PauseOverlay(opacity=0, disabled=True)
        with self.pause_overlay.canvas.before:
            GColor(0, 0, 0, 0.6)
            self._overlay_bg = GRect(
                pos=self.pause_overlay.pos,
                size=self.pause_overlay.size
            )
        self.pause_overlay.bind(
            pos=lambda o, v: setattr(self._overlay_bg, 'pos', v),
            size=lambda o, v: setattr(self._overlay_bg, 'size', v),
        )

        # ── 3 ปุ่มใน Overlay ──
        btn_box = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(400, 90),
            pos_hint={'center_x': 0.5, 'center_y': 0.35},
            spacing=20,
        )
        class IconButton(ButtonBehavior, Image):
            pass

        for img_n, img_d, cb in [
            ('assets/Component_UI/Backtomanu/backtomenu.png',
             'assets/Component_UI/Backtomanu/backtomenu_down.png', self.go_home),
            ('assets/Component_UI/Reset/reset_up.png',
             'assets/Component_UI/Reset/reset_down.png',           self.restart_game),
            ('assets/Component_UI/Resume/resume_on.png',
             'assets/Component_UI/Resume/resume_down.png',         self.resume_game),
        ]:
            b = IconButton(
                source=img_n,
                size_hint=(None, None),
                size=(100, 100),
                allow_stretch=True,
                keep_ratio=True,
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
        from core.state import StateManager
        logger.info("เข้าสู่หน้า GamePlay")
        
        # ขอคีย์บอร์ดทุกครั้งที่เข้าหน้าจอ (ป้องกันอาการค้าง/กดไม่ติด)
        if not self._keyboard:
            self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
            self._keyboard.bind(on_key_down=self._on_keyboard_down)
            self._keyboard.bind(on_key_up=self._on_keyboard_up)

        # อัปเดต Skin ก่อนเริ่มเล่น
        self.penguin.equip_skin(StateManager().selected_skin)
        
        self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)
        AudioManager().play_bgm('Bgm.gameplay.mp3')
        
        # [FIX] บังคับ Reset ทุกครั้งที่เข้าหน้า Gameplay จากเมนู (เพื่อให้ Start Game เริ่มจุดใหม่)
        self.grid.reset()
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]
        self.penguin.is_dead = False
        self.path_index = 0
        self.gems_collected = 0
        self.idle_timer = 0
        self.game_started = False
        self.renderer.cam_x = None 

    def on_leave(self):
        if self.game_event:
            self.game_event.cancel()
        
        # ปล่อยคีย์บอร์ดเมื่อออก
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard.unbind(on_key_up=self._on_keyboard_up)
            self._keyboard = None

    def update(self, dt):
        dist = self.grid.get_distance_m()
        dist_str = f"{dist / 1000:.1f} km" if dist >= 1000 else f"{dist} m"
        self.hud_label.text = f"{dist_str} | 💎 {self.gems_collected}"
        
        # อัปเดตแอนิเมชันของอุปสรรคในรัศมีการมองเห็น
        self.grid.update_obstacles(dt, view_radius=15, penguin_pos=(self.penguin.col, self.penguin.row))
        
        # [CLEANUP] ลบวัตถุที่ผ่านไปแล้ว
        self.grid.cleanup_behind(self.path_index)
        
        # [FALLING FLOOR]
        if not self.penguin.is_dead and self.game_started:
            self.idle_timer += dt
            
            # สั่นเตือนเมื่อเหลือ 1 วินาที
            is_shaking = self.idle_timer > (self.MAX_IDLE_TIME - 1.0)
            
            if self.idle_timer >= self.MAX_IDLE_TIME:
                logger.warning(f"พื้นถล่ม! ยืนนิ่งนานเกินไปที่ ({self.penguin.col}, {self.penguin.row})")
                self.grid.remove_tile(self.penguin.col, self.penguin.row)
                self.penguin.is_dead = True
                AudioManager().play_sfx('Down') 
                Clock.schedule_once(lambda dt: self._go_gameover(), 0.8) # ให้เวลาเห็นท่าตกหน่อย
            
            self.renderer.draw(self.grid, self.penguin, self.path_index, is_shaking_floor=is_shaking)
        else:
            self.renderer.draw(self.grid, self.penguin, self.path_index)

    def _move(self, direction):
        """
        ── FIX 2: เดินในทิศที่กดเสมอ ไม่ว่าจะอยู่บน path หรือไม่
        เดิม: กดผิด → is_stuck = True → หยุดทุกอย่าง (ไม่ใช่ตาย)
        ใหม่: กดผิด → เดินออกนอก path → ตาย (penguin.is_dead = True)
        """
        if self.penguin.is_dead:
            return

        # ตั้งค่าทิศทางหันหน้า
        if direction == DIR_LEFT:
            self.penguin.facing_left = True
        elif direction == DIR_RIGHT:
            self.penguin.facing_left = False

        new_col = self.penguin.col + direction[0]
        new_row = self.penguin.row + direction[1]

        # เช็คการชนอุปสรรค
        obs = self.grid.get_obstacle_at(new_col, new_row)
        if obs and obs.active:
            # ชน! เล่นอนิเมชันแตก แต่ยังไม่ให้ผ่าน (หยุดประมวลผลการเดิน)
            if obs.hit():
                AudioManager().play_sfx('Hit') 
                # [FIX] นำกล่องออกจาก Dictionary ทันทีตามที่ขอให้หายไปเลย
                self.grid.obstacles.pop((new_col, new_row), None)
                self.idle_timer = 0 # รีเซ็ตเวลาเมื่อมีการทำลายกล่อง (มีกิจกรรม)
                self.game_started = True 
                return
            else:
                return

        # เช็คการเก็บ Gem
        gem = self.grid.get_gem_at(new_col, new_row)
        if gem and gem.active:
            val = gem.collect()
            self.gems_collected += val
            AudioManager().play_sfx('Coin')
            tile_type = "FORK" if self.grid.is_fork_tile(new_col, new_row) else "NORMAL"
            logger.info(f"[COLLECT] Gem ที่ ({new_col}, {new_row}) ชนิด {tile_type} | รวม: {self.gems_collected}")
            # [FIX] นำเพชรออกจาก Dictionary ทันทีเพื่อให้หายไปจากจอแน่นอน
            self.grid.gems.pop((new_col, new_row), None)

        # ย้ายเพนกวิน
        self.penguin.col = new_col
        self.penguin.row = new_row
        self.game_started = True # เริ่มเกมจริงจังหลังจากมีการขยับครั้งแรก

        if self.grid.is_on_path(new_col, new_row):
            # ถูกทาง: นับระยะ + อัปเดต index
            self.grid.step_forward()
            idx = self.grid.get_path_index(new_col, new_row)
            if idx >= 0:
                self.path_index = idx
                self.grid.extend_if_needed(self.path_index)
                AudioManager().play_sfx('Jump')
                self.renderer.trigger_shake(5) # สั่นพองามตอนกระโดด
                
                # [FIX] รีเซ็ตเวลาและหยุดสั่น (จากพื้นถล่ม) ทันทีเมื่อก้าวไปบล็อกใหม่
                self.idle_timer = 0 
                self.renderer.shake_amount = 5 # ให้กระตุกตอนโดดแทนการสั่นรัวๆ ของพื้นถล่ม
            
            # เช็คว่าเดินไปถึงจุดสุดท้ายของแผนที่แล้วหรือยัง
            if self.path_index == len(self.grid.path) - 1:
                logger.info(f"ชนะแล้ว! วิ่งถึงเส้นชัยด้วยระยะ {self.grid.get_distance_m()} m")
                self.manager.current = 'gameover'
        else:
            # ผิดทาง: เดินออกนอก path → ตาย
            self.penguin.is_dead = True
            AudioManager().play_sfx('Down')
            logger.info(f"ตก! ระยะ {self.grid.get_distance_m()} m")
            # ดีเลย์นิดนึงให้เห็นท่าตก
            Clock.schedule_once(lambda dt: self._go_gameover(), 0.5)

    def _go_gameover(self):
        self.manager.current = 'gameover'
    

    def pause_game(self): #หยุด game loop + แสดง overlay
        if self.game_event:
            self.game_event.cancel()
            self.game_event = None
        self.pause_overlay.opacity = 1
        self.pause_overlay.disabled = False
        AudioManager().play_sfx('click')


    def resume_game(self): # ซ่อน overlay + เล่นต่อ
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True
        if not self.game_event:
            self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)
        AudioManager().play_sfx('click')


    def restart_game(self): # รีเซ็ต stateทั้งหมดกลับเป็นค่าเริ่มต้นเหมือนตอนเข้าเกม
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
        self.renderer.cam_x = None
        self.renderer.cam_y = None
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True
        if not self.game_event:
            self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)


    def go_home(self): #กลับหน้าเมนู + หยุด game loop
        AudioManager().play_sfx('click')
        if self.game_event:
            self.game_event.cancel()
            self.game_event = None
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'menu'), 0.2)


    def _keyboard_closed(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard.unbind(on_key_up=self._on_keyboard_up)
            self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if self.penguin.is_dead:
            return False
        if not self.game_event:
            return False
        if keycode[1] == 'left':
            self.btn_left.handle_press()
            return True
        elif keycode[1] == 'right':
            self.btn_right.handle_press()
            return True
        return False
    

    def _on_keyboard_up(self, keyboard, keycode):
        if not self.game_event:
            return False
        if keycode[1] == 'left':
            self.btn_left.handle_release()
            return True
        elif keycode[1] == 'right':
            self.btn_right.handle_release()
            return True
        return False