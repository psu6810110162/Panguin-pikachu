import math
import random

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.graphics import Color as GColor
from kivy.graphics import Rectangle as GRect
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from core.audio import AudioManager
from core.config import TARGET_FPS, TILE_H, TILE_IMG_H, TILE_W
from core.interaction import YJunctionInteraction
from core.boss_data import load_boss_data
from core.junction_data import get_junction
from core.logger import logger
from core.session import GameSession
from core.state import RunMetrics, RunState
from game.grid import GridManager
from game.particles import ParticleSystem
from game.penguin import Penguin
from ui.components import HoverButton

GRASS_TILES = [
    "assets/isometric-nature-pack/grass1.png",
    "assets/isometric-nature-pack/grass2.png",
    "assets/isometric-nature-pack/grass3.png",
    "assets/isometric-nature-pack/grass4.png",
    "assets/isometric-nature-pack/grass5.png",
    "assets/isometric-nature-pack/grass6.png",
    "assets/isometric-nature-pack/grass7.png",
    "assets/isometric-nature-pack/grass8.png",
    "assets/isometric-nature-pack/grass9.png",
    "assets/isometric-nature-pack/grass10.png",
]

ARROW_RIGHT_IMG = "assets/Component_UI/Vector/arrow_right_normal.png"
ARROW_LEFT_IMG = "assets/Component_UI/Vector/arrow_left_normal.png"

DIR_LEFT = (0, 1)
DIR_RIGHT = (1, 0)


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
            "Idle": CoreImage("assets/pixelAdventure/Free/Items/Boxes/Box2/Idle.png").texture,
            "Hit": CoreImage("assets/pixelAdventure/Free/Items/Boxes/Box2/Hit (28x24).png").texture,
            "Break": CoreImage("assets/pixelAdventure/Free/Items/Boxes/Box2/Break.png").texture,
        }
        self.gem_texture = CoreImage("assets/Gem/Coin_Gems/spr_coin_strip4.png").texture
        self.cam_x = None
        self.cam_y = None
        self.shake_amount = 0

    def trigger_shake(self, amount=10):
        self.shake_amount = amount

    def _get_tile_texture(self, col, row):
        key = (col, row)
        if key not in self.tile_textures:
            self.tile_textures[key] = random.choice(self._grass_textures)
        return self.tile_textures[key]

    def grid_to_screen(self, col, row):
        return GridManager.to_isometric(col, row, TILE_W, TILE_H)

    def draw(self, grid_manager, penguin, path_index, is_shaking_floor=False):
        target_x, target_y = self.grid_to_screen(penguin.col, penguin.row)

        if self.cam_x is None:
            self.cam_x = target_x
            self.cam_y = target_y

        self.cam_x += (target_x - self.cam_x) * 0.15
        self.cam_y += (target_y - self.cam_y) * 0.15

        ox = Window.width / 2 - self.cam_x
        oy = Window.height / 2 - self.cam_y

        if self.shake_amount > 0:
            ox += random.uniform(-self.shake_amount, self.shake_amount)
            oy += random.uniform(-self.shake_amount, self.shake_amount)
            self.shake_amount *= 0.8
            if self.shake_amount < 0.5:
                self.shake_amount = 0

        self.canvas.clear()
        with self.canvas:
            view_radius = 15
            render_queue = []

            for col, row in list(grid_manager.path_set.keys()):
                tile = grid_manager.path_set.get((col, row))
                if not tile or tile.state == "destroyed":
                    continue

                if (penguin.col - view_radius <= col <= penguin.col + view_radius) and (
                    penguin.row - view_radius <= row <= penguin.row + view_radius
                ):
                    render_queue.append(
                        {
                            "col": col,
                            "row": row,
                            "z_index": -(col + row),
                            "sub_layer": 0,
                            "type": "tile",
                            "obj": tile,
                        }
                    )

                    obs = grid_manager.get_obstacle_at(col, row)
                    if obs and obs.active:
                        render_queue.append(
                            {
                                "col": col,
                                "row": row,
                                "z_index": -(col + row),
                                "sub_layer": 1,
                                "type": "obstacle",
                                "obj": obs,
                            }
                        )

                    gem = grid_manager.get_gem_at(col, row)
                    if gem and gem.active:
                        render_queue.append(
                            {
                                "col": col,
                                "row": row,
                                "z_index": -(col + row),
                                "sub_layer": 1,
                                "type": "gem",
                                "obj": gem,
                            }
                        )

            render_queue.append(
                {
                    "col": penguin.col,
                    "row": penguin.row,
                    "z_index": -(penguin.col + penguin.row),
                    "sub_layer": 2,
                    "type": "penguin",
                    "obj": penguin,
                }
            )
            render_queue.sort(key=lambda x: (x["z_index"], x["sub_layer"]))

            for item in render_queue:
                col, row, itype, obj = item["col"], item["row"], item["type"], item["obj"]

                tile = grid_manager.path_set.get((col, row))
                y_off = tile.offset_y if tile else 0

                if itype == "tile":
                    if obj.is_fork:
                        Color(1, 0.9, 0.4, 1)
                    else:
                        Color(1, 1, 1, 1)
                    tex = self._get_tile_texture(col, row)
                    sx, sy = self.grid_to_screen(col, row)
                    draw_x = sx + ox - (TILE_W // 2)
                    draw_y = sy + oy - (TILE_IMG_H - TILE_H // 2) + y_off
                    Rectangle(texture=tex, pos=(draw_x, draw_y), size=(TILE_W, TILE_IMG_H))
                elif itype == "obstacle":
                    Color(1, 1, 1, 1)
                    sx, sy = self.grid_to_screen(col, row)
                    draw_x = sx + ox - (TILE_W // 2)
                    draw_y = sy + oy - (TILE_IMG_H - TILE_H // 2) + y_off
                    self._draw_obstacle(obj, draw_x, draw_y + (TILE_IMG_H // 2), ox, oy)
                elif itype == "gem":
                    Color(1, 1, 1, 1)
                    sx, sy = self.grid_to_screen(col, row)
                    draw_x = sx + ox - (TILE_W // 2)
                    draw_y = sy + oy - (TILE_IMG_H - TILE_H // 2) + y_off
                    self._draw_gem(obj, draw_x, draw_y + (TILE_IMG_H // 2), ox, oy)
                elif itype == "penguin":
                    Color(1, 1, 1, 1)
                    p_ox, p_oy = ox, oy
                    p_oy += y_off
                    if is_shaking_floor:
                        p_ox += random.uniform(-3, 3)
                        p_oy += random.uniform(-3, 3)
                    self._draw_penguin(obj, p_ox, p_oy)

            # Draw particle shards on top with alpha fade and variable size
            if hasattr(self.parent, "particle_system"):
                for p in self.parent.particle_system.particles:
                    alpha = getattr(p, "alpha", 1.0)
                    sz = getattr(p, "size", 6)
                    Color(0.8, 0.6, 0.4, alpha)  # wooden color with fade
                    Rectangle(pos=(p.x + ox, p.y + oy), size=(sz, sz))

    def _draw_penguin(self, penguin, ox, oy):
        if penguin.is_dead:
            penguin.action = "Fall"
            px, py = self.grid_to_screen(penguin.col, penguin.row)
            if penguin.visual_x is not None:
                px, py = penguin.visual_x, penguin.visual_y

            skin_path = penguin.get_skin_path()
            if skin_path not in self.tile_textures:
                self.tile_textures[skin_path] = CoreImage(skin_path).texture
            skin_tex = self.tile_textures[skin_path]
            if penguin.facing_left:
                skin_tex = skin_tex.get_region(32, 0, -32, 32)
            pw, ph = 64, 64
            Color(1, 1, 1, 1)
            Rectangle(
                texture=skin_tex,
                pos=(px + ox - pw // 2, py + oy + penguin.anim_offset_y),
                size=(pw, ph),
            )
        else:
            target_px, target_py = self.grid_to_screen(penguin.col, penguin.row)
            if penguin.visual_x is None:
                penguin.visual_x = target_px
                penguin.visual_y = target_py

            # smooth follow
            penguin.visual_x += (target_px - penguin.visual_x) * 0.4
            penguin.visual_y += (target_py - penguin.visual_y) * 0.4

            px, py = penguin.visual_x, penguin.visual_y

            # Action frame cycling
            frames_count = penguin.ACTION_FRAMES.get(penguin.action, 1)
            self.anim_frame = (self.anim_frame + 0.3) % max(1, frames_count)
            frame_idx = int(self.anim_frame) % max(1, frames_count)

            skin_path = penguin.get_skin_path()
            cache_key = f"{skin_path}_{frame_idx}_{'L' if penguin.facing_left else 'R'}"
            if cache_key not in self.tile_textures:
                if skin_path not in self.tile_textures:
                    self.tile_textures[skin_path] = CoreImage(skin_path).texture
                full_tex = self.tile_textures[skin_path]
                if penguin.facing_left:
                    self.tile_textures[cache_key] = full_tex.get_region(
                        (frame_idx + 1) * 32, 0, -32, 32
                    )
                else:
                    self.tile_textures[cache_key] = full_tex.get_region(frame_idx * 32, 0, 32, 32)
            skin_tex = self.tile_textures[cache_key]
            pw, ph = 64, 64
            Color(1, 1, 1, 1)
            Rectangle(
                texture=skin_tex,
                pos=(px + ox - pw // 2, py + oy + penguin.anim_offset_y),
                size=(pw, ph),
            )

    def _draw_obstacle(self, obs, tx, ty, ox, oy):
        """
        Draw stacked crate layers using stack_height for visual degradation.
        When hit, the top layer is removed visually before the hit animation plays.
        """
        state = obs.state
        frame = int(obs.anim_frame)
        full_tex = self.box_assets.get(state)
        tex = full_tex.get_region(frame * 28, 0, 28, 24)
        bw, bh = 56, 48
        Color(1, 1, 1, 1)
        # Use stack_height (not hp) for number of layers to render
        layers = max(1, obs.stack_height) if obs.active else max(1, obs.hp)
        for i in range(layers):
            y_offset = i * (bh * 0.6)
            Rectangle(texture=tex, pos=(tx + (TILE_W - bw) // 2, ty + y_offset), size=(bw, bh))

    def _draw_gem(self, gem, tx, ty, ox, oy):
        frame_idx = gem.anim_frame
        tex = self.gem_texture.get_region(frame_idx * 16, 0, 16, 16)
        float_offset = 12
        gw, gh = 32, 32
        Color(1, 1, 1, 1)
        Rectangle(texture=tex, pos=(tx + (TILE_W - gw) // 2, ty + float_offset), size=(gw, gh))


# ═══════════════════════════════════════════════════════════════
#  PAUSE OVERLAY — Fantasy UI with reused Main Menu components
# ═══════════════════════════════════════════════════════════════


class PauseOverlay(FloatLayout):
    """
    Centered modal overlay displayed when the game is paused.
    Reuses the blue rectangular flat button style from Main Menu/Shop/History
    and the icon-styled Sound Button from the Main Menu layout.
    """

    def __init__(self, game_screen=None, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen

        # Semi-transparent dark background covering the full screen
        with self.canvas.before:
            GColor(0, 0, 0, 0.65)
            self._fullscreen_bg = GRect(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda o, v: setattr(self._fullscreen_bg, "pos", v),
            size=lambda o, v: setattr(self._fullscreen_bg, "size", v),
        )

        # ── Center container with styled background ──
        self.container = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(380, 480),
            padding=[35, 35, 35, 35],
            spacing=22,
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        # Container background — dark panel with rounded corners and subtle border
        with self.container.canvas.before:
            GColor(0.08, 0.08, 0.14, 0.95)
            self._container_bg = RoundedRectangle(
                pos=self.container.pos, size=self.container.size, radius=[22]
            )
            GColor(0.3, 0.6, 0.9, 0.35)
            self._container_border = Line(
                rounded_rectangle=(
                    self.container.x,
                    self.container.y,
                    self.container.width,
                    self.container.height,
                    22,
                ),
                width=1.5,
            )
        self.container.bind(pos=self._update_container_bg, size=self._update_container_bg)

        # ── "PAUSED" title ──
        title = Label(
            text="PAUSED",
            font_size="38sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(0.6, 0.9, 1.0, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            size_hint_y=None,
            height=55,
        )
        self.container.add_widget(title)

        # ── Spacer ──
        from kivy.uix.widget import Widget as SpacerWidget

        self.container.add_widget(SpacerWidget(size_hint_y=None, height=8))

        # ── RESUME button — blue flat style matching Main Menu START GAME ──
        btn_resume = HoverButton(
            text="RESUME",
            font_size="24sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            background_normal="assets/Component_UI/PNG/Blue/Default/button_rectangle_depth_flat.png",
            background_down="assets/Component_UI/PNG/Blue/Default/button_rectangle_flat.png",
            border=(20, 20, 20, 20),
            size_hint_y=None,
            height=60,
            color=(1, 1, 1, 1),
        )
        btn_resume.bind(
            on_release=lambda x: self.game_screen.resume_game() if self.game_screen else None
        )
        self.container.add_widget(btn_resume)

        # ── RESTART button — same blue flat style ──
        btn_restart = HoverButton(
            text="RESTART",
            font_size="24sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            background_normal="assets/Component_UI/PNG/Blue/Default/button_rectangle_depth_flat.png",
            background_down="assets/Component_UI/PNG/Blue/Default/button_rectangle_flat.png",
            border=(20, 20, 20, 20),
            size_hint_y=None,
            height=60,
            color=(1, 1, 1, 1),
        )
        btn_restart.bind(
            on_release=lambda x: self.game_screen.restart_game() if self.game_screen else None
        )
        self.container.add_widget(btn_restart)

        # ── Spacer before sound ──
        self.container.add_widget(SpacerWidget(size_hint_y=None, height=5))

        # ── SOUND toggle — reuses the exact icon-styled Sound Button from Main Menu ──
        sound_box = BoxLayout(orientation="vertical", spacing=6, size_hint_y=None, height=120)
        self.btn_sound = HoverButton(
            size_hint=(None, None),
            size=(90, 90),
            pos_hint={"center_x": 0.5},
            background_color=(1, 1, 1, 1),
            border=(0, 0, 0, 0),
        )
        self.btn_sound.bind(on_release=self.toggle_sound)

        sound_label = Label(
            text="SOUND",
            font_size="16sp",
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(0.7, 0.85, 1.0, 0.9),
            size_hint_y=None,
            height=25,
        )
        sound_box.add_widget(self.btn_sound)
        sound_box.add_widget(sound_label)
        self.container.add_widget(sound_box)

        self.add_widget(self.container)
        Clock.schedule_once(lambda dt: self.sync_sound_button(), 0.1)

    def _update_container_bg(self, instance, value):
        """Keep background rect and border line in sync with container layout."""
        self._container_bg.pos = instance.pos
        self._container_bg.size = instance.size
        self._container_border.rounded_rectangle = (
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            22,
        )

    def sync_sound_button(self):
        from core.audio import AudioManager

        if AudioManager().bgm_muted:
            self.btn_sound.background_normal = "assets/Component_UI/Button Sounds/volume_down.png"
            self.btn_sound.background_down = "assets/Component_UI/Button Sounds/volume_down.png"
        else:
            self.btn_sound.background_normal = "assets/Component_UI/Button Sounds/volume_up.png"
            self.btn_sound.background_down = "assets/Component_UI/Button Sounds/volume_up.png"

    def toggle_sound(self, *args):
        from core.audio import AudioManager

        am = AudioManager()
        am.toggle_mute()
        self.sync_sound_button()

    def on_touch_down(self, touch):
        if self.opacity == 0:
            return False
        super().on_touch_down(touch)
        return True  # Absorb touch when active

    def on_touch_move(self, touch):
        if self.opacity == 0:
            return False
        super().on_touch_move(touch)
        return True

    def on_touch_up(self, touch):
        if self.opacity == 0:
            return False
        super().on_touch_up(touch)
        return True


class ArrowButton(ButtonBehavior, Image):
    def __init__(self, move_callback=None, **kwargs):
        super().__init__(**kwargs)
        self._move_callback = move_callback
        self.bind(on_press=self.handle_press)
        self.bind(on_release=self.handle_release)

    def collide_point(self, x, y):
        return self.x <= x <= self.right and self.y <= y <= self.top

    def handle_press(self, *args):
        Animation(size=(150, 150), duration=0.08, t="out_back").start(self)
        if self._move_callback:
            self._move_callback()

    def handle_release(self, *args):
        Animation(size=(120, 120), duration=0.1, t="out_quad").start(self)


class GamePlayScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid = GridManager()
        self.penguin = Penguin()
        self.game_over = False
        self.game_event = None
        self._keyboard = None
        self.path_index = 0

        self.session = GameSession()
        self.metrics = RunMetrics(on_game_over=self._trigger_gameover_from_metrics)
        self.junction_interaction = YJunctionInteraction(self.metrics, self.session)
        self.last_checkpoint_col = self.grid.path[0][0]
        self.last_checkpoint_row = self.grid.path[0][1]
        self.is_respawning = False
        self.grid.reset()
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]
        self.idle_timer = 0
        self.MAX_IDLE_TIME = 2.0
        self.game_started = False
        self.particle_system = ParticleSystem()
        self.boss_wave_index = 0
        self.boss_hp = 0
        self.boss_start_time = 0

        self.renderer = KivyRenderer()
        self.add_widget(self.renderer)

        self.hud_bg = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            height=60,
            spacing=30,
            padding=[20, 10, 20, 10],
            pos_hint={"right": 0.98, "top": 0.98},
        )
        self.hud_bg.bind(minimum_width=self.hud_bg.setter("width"))

        with self.hud_bg.canvas.before:
            GColor(0, 0, 0, 0.6)
            self.hud_rect = RoundedRectangle(radius=[15])
        self.hud_bg.bind(pos=self._update_hud_rect, size=self._update_hud_rect)

        self.score_label = Label(
            text="SCORE: 0",
            font_size="26sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            size_hint_x=None,
        )
        self.score_label.bind(texture_size=self.score_label.setter("size"))

        gem_box = BoxLayout(orientation="horizontal", size_hint=(None, None), height=40, spacing=10)
        gem_box.bind(minimum_width=gem_box.setter("width"))

        gem_tex = CoreImage("assets/Gem/Coin_Gems/spr_coin_strip4.png").texture.get_region(
            0, 0, 16, 16
        )
        gem_icon = Image(texture=gem_tex, size_hint=(None, None), size=(40, 40))

        self.gem_label = Label(
            text="x 0",
            font_size="26sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            size_hint_x=None,
        )
        self.gem_label.bind(texture_size=self.gem_label.setter("size"))

        gem_box.add_widget(gem_icon)
        gem_box.add_widget(self.gem_label)

        self.hud_bg.add_widget(self.score_label)
        self.hud_bg.add_widget(gem_box)
        self.hearts_label = Label(
            text=f"Hearts: {self.metrics.hearts}",
            font_size="20sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
        )
        self.heat_label = Label(
            text=f"Heat: {self.metrics.heat_meter:.0f}",
            font_size="20sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(1, 0.5, 0.5, 1),
        )
        self.anger_label = Label(
            text=f"Anger: {self.metrics.capitalist_anger:.0f}",
            font_size="20sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(0.8, 0.2, 0.2, 1),
        )
        self.hud_bg.add_widget(self.hearts_label)
        self.hud_bg.add_widget(self.heat_label)
        self.hud_bg.add_widget(self.anger_label)

        self.add_widget(self.hud_bg)

        OFFSET = 0.2
        self.btn_left = ArrowButton(
            move_callback=lambda: self._move(DIR_LEFT),
            source=ARROW_LEFT_IMG,
            size_hint=(None, None),
            size=(120, 120),
            allow_stretch=True,
            keep_ratio=True,
            pos_hint={"center_x": 0.5 - OFFSET, "center_y": 0.08},
        )
        self.add_widget(self.btn_left)

        self.btn_right = ArrowButton(
            move_callback=lambda: self._move(DIR_RIGHT),
            source=ARROW_RIGHT_IMG,
            size_hint=(None, None),
            size=(120, 120),
            allow_stretch=True,
            keep_ratio=True,
            pos_hint={"center_x": 0.5 + OFFSET, "center_y": 0.08},
        )
        self.add_widget(self.btn_right)

        # ── Pause button at top-left corner ──
        self.pause_btn = Button(
            size_hint=(None, None),
            size=(80, 80),
            pos_hint={"x": 0.02, "top": 0.98},
            background_normal="assets/Component_UI/Stop/pause_on.png",
            background_down="assets/Component_UI/Stop/pause_down.png",
            background_color=(1, 1, 1, 1),
            border=(0, 0, 0, 0),
        )
        self.pause_btn.bind(on_release=lambda _: self.pause_game())
        self.add_widget(self.pause_btn)

        # ── Pause overlay modal ──
        self.pause_overlay = PauseOverlay(game_screen=self, opacity=0, disabled=True)
        self.add_widget(self.pause_overlay)

        # Checkpoint popup label
        self.checkpoint_label = Label(
            text="",
            font_size="30sp",
            color=(1, 1, 1, 0),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "center_y": 0.75},
        )
        self.add_widget(self.checkpoint_label)

        # Boss UI
        self.boss_wall_label = Label(
            text="",
            font_size="24sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(1, 0.2, 0.2, 1),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.85},
            outline_width=2,
            outline_color=(0, 0, 0, 1),
        )
        self.add_widget(self.boss_wall_label)
        
        self.boss_choices_label = Label(
            text="",
            font_size="20sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(0.9, 0.9, 0.2, 1),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.78},
            outline_width=2,
            outline_color=(0, 0, 0, 1),
        )
        self.add_widget(self.boss_choices_label)


    def show_checkpoint_message(self, message: str):
        """Display a temporary non-blocking message when a checkpoint is reached.
        The label fades in, stays for 1.5 seconds, then fades out.
        """
        self.checkpoint_label.text = message
        # Fade in
        anim = (
            Animation(color=(1, 1, 1, 1), duration=0.3)
            + Animation(duration=1.5)
            + Animation(color=(1, 1, 1, 0), duration=0.5)
        )
        anim.start(self.checkpoint_label)

    def _update_hud_rect(self, instance, value):
        self.hud_rect.pos = instance.pos
        self.hud_rect.size = instance.size

    def _trigger_gameover_from_metrics(self):
        self.penguin.is_dead = True
        Clock.schedule_once(lambda dt: self._go_gameover(), 0.8)

    def _respawn_penguin(self, dt=None):
        self.penguin.is_dead = False
        self.is_respawning = False
        self.penguin.col = self.last_checkpoint_col
        self.penguin.row = self.last_checkpoint_row
        self.metrics.is_invincible = False
        self.renderer.trigger_shake(0)

    def _handle_fall(self):
        if self.is_respawning or self.penguin.is_dead:
            return
        self.penguin.is_dead = True
        self.metrics.decrease_heart()
        self.hearts_label.text = f"Hearts: {self.metrics.hearts}"
        if self.metrics.needs_respawn:
            self.metrics.needs_respawn = False
            self.is_respawning = True
            Clock.schedule_once(self._respawn_penguin, 3.0)

    def _start_new_session(self):
        """เริ่ม RunRecord รอบใหม่ (LOBBY → RUNNING) — เรียกทุกครั้งที่เริ่ม/รีสตาร์ทเกม"""
        self.session = GameSession()
        self.session.start()

    def on_enter(self):
        from core.state import StateManager

        logger.info("เข้าสู่หน้า GamePlay")

        if not self._keyboard:
            self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
            self._keyboard.bind(on_key_down=self._on_keyboard_down)
            self._keyboard.bind(on_key_up=self._on_keyboard_up)

        self.penguin.equip_skin(StateManager().selected_skin)
        self.metrics = RunMetrics(on_game_over=self._trigger_gameover_from_metrics)
        self.junction_interaction = YJunctionInteraction(self.metrics, self.session)
        self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)
        AudioManager().play_bgm("Bgm.gameplay.mp3")

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
        self._start_new_session()
        self.boss_wave_index = 0
        self.boss_hp = 0
        self.boss_start_time = 0
        self.boss_wall_label.text = ""
        self.boss_choices_label.text = ""

    def on_leave(self):
        if self.game_event:
            self.game_event.cancel()
            self.game_event = None  # ✅ fix

        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard.unbind(on_key_up=self._on_keyboard_up)
            self._keyboard = None

    def update(self, dt):
        dist = self.grid.get_distance_m()
        dist_str = f"{dist / 1000:.1f} km" if dist >= 1000 else f"{dist} m"
        self.score_label.text = f"SCORE: {dist_str}"
        self.gem_label.text = f"x {self.gems_collected}"

        self.grid.update_obstacles(
            dt, view_radius=15, penguin_pos=(self.penguin.col, self.penguin.row)
        )
        self.grid.cleanup_behind(self.path_index)

        # Physics update
        if self.penguin.is_dead:
            self.penguin.anim_offset_y -= 800.0 * dt
        elif self.penguin.action_timer > 0:
            self.penguin.action_timer -= dt

            if self.penguin.action == "Jump":
                t = 1.0 - max(0.0, self.penguin.action_timer / 0.25)
                self.penguin.anim_offset_y = math.sin(t * math.pi) * 30.0
            elif self.penguin.action == "Hit":
                t = 1.0 - max(0.0, self.penguin.action_timer / 0.2)
                self.penguin.anim_offset_y = math.sin(t * math.pi) * 15.0

            if self.penguin.action_timer <= 0:
                self.penguin.action = "Idle"
                self.penguin.anim_offset_y = 0.0

        self.particle_system.update(dt)

        if not self.penguin.is_dead and not self.is_respawning and self.game_started:
            self.grid.update_tiles(dt, (self.penguin.col, self.penguin.row))

            # Check if penguin's tile is falling
            current_tile = self.grid.path_set.get((self.penguin.col, self.penguin.row))
            if current_tile and current_tile.state == "falling":
                AudioManager().play_sfx("Down")
                self._handle_fall()

            self.idle_timer += dt
            is_shaking = current_tile and current_tile.state == "triggered"

            if self.idle_timer >= self.MAX_IDLE_TIME:
                logger.warning(f"พื้นถล่ม! ยืนนิ่งนานเกินไปที่ ({self.penguin.col}, {self.penguin.row})")
                if current_tile and not current_tile.is_safe:
                    current_tile.state = "falling"
                    current_tile.fall_velocity = 0.0
                AudioManager().play_sfx("Down")
                self._handle_fall()

            self.renderer.draw(
                self.grid, self.penguin, self.path_index, is_shaking_floor=is_shaking
            )
        else:
            self.grid.update_tiles(dt, (self.penguin.col, self.penguin.row))
            self.renderer.draw(self.grid, self.penguin, self.path_index)

    def _move(self, direction):
        """
        Handle player movement with ice-block style collision.

        COLLISION RULES:
        - Penguin is COMPLETELY BLOCKED at current position when hitting a crate with hp > 0
        - No bounce, push, or recoil backward
        - Each hit decrements obstacle hp by 1 and visually removes one crate layer
        - Final hit (hp → 0): full explosion, obstacle deactivated, path cleared
        """
        if self.penguin.is_dead:
            return

        if direction == DIR_LEFT:
            self.penguin.facing_left = True
        elif direction == DIR_RIGHT:
            self.penguin.facing_left = False

        new_col = self.penguin.col + direction[0]
        new_row = self.penguin.row + direction[1]

        # ── Obstacle collision check ──
        obs = self.grid.get_obstacle_at(new_col, new_row)
        if obs and obs.active and obs.state != obs.STATE_BREAK:
            # Hit the obstacle — penguin stays at CURRENT position (no movement)
            result = obs.hit()
            AudioManager().play_sfx("Hit")
            self.idle_timer = 0
            self.game_started = True
            self.session.obstacle_hit(
                col=new_col,
                row=new_row,
                damage=1,
                destroyed=result["destroyed"],
                distance_m=self.grid.get_distance_m(),
            )

            # Particle effects at the obstacle's screen position
            px, py = self.renderer.grid_to_screen(new_col, new_row)

            if result["destroyed"]:
                # Full crate shattering explosion — path is now clear
                self.particle_system.spawn_explosion(px, py + TILE_IMG_H // 2, count=10)
                self.renderer.trigger_shake(8)
            else:
                # Partial hit — small top-layer shard burst at the old top layer position
                shard_y = py + TILE_IMG_H // 2 + (result["old_hp"] * 28)
                self.particle_system.spawn_shards(px, shard_y, count=3)
                self.renderer.trigger_shake(4)

            # Penguin plays hit animation but does NOT move
            self.penguin.action = "Hit"
            self.penguin.action_timer = 0.2
            self.renderer.anim_frame = 0
            return  # ← CRITICAL: penguin stays at current grid position

        # ── Gem collection ──
        gem = self.grid.get_gem_at(new_col, new_row)
        if gem and gem.active:
            val = gem.collect()
            self.gems_collected += val
            AudioManager().play_sfx("Coin")
            tile_type = "FORK" if self.grid.is_fork_tile(new_col, new_row) else "NORMAL"
            logger.info(
                f"[COLLECT] Gem ที่ ({new_col}, {new_row}) ชนิด {tile_type} | รวม: {self.gems_collected}"
            )
            self.grid.gems.pop((new_col, new_row), None)
            self.session.collect(
                item_type="gem",
                col=new_col,
                row=new_row,
                value=val,
                distance_m=self.grid.get_distance_m(),
            )

        # ── Boss item collection ──
        boss_item = self.grid.get_boss_item_at(new_col, new_row)
        if boss_item:
            wave_num, item_id = boss_item
            boss_data = load_boss_data()
            wave_data = boss_data.waves.get(wave_num)
            is_correct = (item_id == wave_data.correct_item) if wave_data else False
            
            if is_correct:
                AudioManager().play_sfx("Coin")
                self.boss_hp -= 1
                self.session.boss_phase(
                    phase=wave_num,
                    outcome="damage_dealt",
                    distance_m=self.grid.get_distance_m(),
                )
                self.show_checkpoint_message("CORRECT!")
                if wave_data:
                    self.metrics.update_meters(
                        heat_delta=wave_data.on_correct.get("heat", 0),
                        anger_delta=wave_data.on_correct.get("anger", 0)
                    )
            else:
                AudioManager().play_sfx("Down")
                self.metrics.hearts -= 1
                self.hearts_label.text = f"Hearts: {self.metrics.hearts}"
                self.session.boss_phase(
                    phase=wave_num,
                    outcome="damaged",
                    distance_m=self.grid.get_distance_m(),
                )
                self.show_checkpoint_message("WRONG FACT!")
                if wave_data:
                    self.metrics.update_meters(
                        heat_delta=wave_data.on_wrong.get("heat", 0),
                        anger_delta=wave_data.on_wrong.get("anger", 0)
                    )
                
            self.heat_label.text = f"Heat: {self.metrics.heat_meter:.0f}"
            self.anger_label.text = f"Anger: {self.metrics.capitalist_anger:.0f}"

            self.boss_wave_index = wave_num + 1
            self.grid.boss_items.pop((new_col, new_row), None)
            
            if self.boss_hp <= 0:
                self.session.boss_victory(
                    total_time_s=self.session.elapsed() - self.boss_start_time,
                    distance_m=self.grid.get_distance_m(),
                )
                self.show_checkpoint_message("BOSS DEFEATED!")
                self.boss_wall_label.text = ""
                self.boss_choices_label.text = ""
                self.session.finish()
                Clock.schedule_once(lambda dt: self._go_report(), 2.0)
            elif self.metrics.hearts <= 0 or self.boss_wave_index > 3:
                self.show_checkpoint_message("FAILED TO DEFEAT BOSS!")
                self.boss_wall_label.text = ""
                self.boss_choices_label.text = ""
                self.metrics.trigger_game_over()
            else:
                self._update_boss_ui()
                
            return

        # ── Move penguin to new position ──
        self.penguin.col = new_col
        self.penguin.row = new_row
        self.game_started = True

        self.penguin.action = "Jump"
        self.penguin.action_timer = 0.25
        self.renderer.anim_frame = 0

        self.grid.check_fork_resolution(new_col, new_row)
        resolved_fork = self.grid.pop_resolved_fork()
        if resolved_fork:
            zone_id, side = resolved_fork
            junction = get_junction(zone_id)
            if junction:
                self.junction_interaction.handle_choice(junction, side)

        if self.grid.is_on_path(new_col, new_row):
            self.grid.step_forward()
            idx = self.grid.get_path_index(new_col, new_row)
            if idx >= 0:
                self.path_index = idx
                self.grid.extend_if_needed(self.path_index)
                AudioManager().play_sfx("Jump")
                self.renderer.trigger_shake(5)
                self.idle_timer = 0
                self.renderer.shake_amount = 5
                # Checkpoint notification
                dist_m = self.grid.get_distance_m()
                if self.grid.forward_tiles % 100 == 0:
                    self.show_checkpoint_message(f"{dist_m}M REACHED!")
                    self.last_checkpoint_col = self.penguin.col
                    self.last_checkpoint_row = self.penguin.row
                    self.session.checkpoint_reached(
                        checkpoint_index=self.grid.forward_tiles // 100,
                        distance_m=dist_m,
                    )
                if dist_m == 980:
                    self.show_checkpoint_message("WARNING: CARBON BARON APPROACHING!")
                elif dist_m == 1000 and self.session.run_record.state == RunState.RUNNING:
                    self.session.enter_boss(distance_m=1000)
                    self.show_checkpoint_message("BOSS PHASE STARTED!")
                    self.boss_wave_index = 1
                    self.boss_hp = load_boss_data().armor
                    self.boss_start_time = self.session.elapsed()
                    self._update_boss_ui()

            if self.path_index == len(self.grid.path) - 1:
                logger.info(f"ชนะแล้ว! วิ่งถึงเส้นชัยด้วยระยะ {self.grid.get_distance_m()} m")
                self.manager.current = "gameover"
        else:
            self.penguin.is_dead = True
            AudioManager().play_sfx("Down")
            logger.info(f"ตก! ระยะ {self.grid.get_distance_m()} m")
            Clock.schedule_once(lambda dt: self._go_gameover(), 0.5)

    def _go_gameover(self):
        self.manager.current = "gameover"
        
    def _go_report(self):
        self.manager.current = "report"

    def _update_boss_ui(self):
        wave = load_boss_data().waves.get(self.boss_wave_index)
        if not wave:
            self.boss_wall_label.text = ""
            self.boss_choices_label.text = ""
            return
            
        self.boss_wall_label.text = wave.wall_text
        
        items = [
            (pos, data[1]) for pos, data in self.grid.boss_items.items() 
            if data[0] == self.boss_wave_index
        ]
        items.sort(key=lambda x: x[0][0] + x[0][1])
        
        if len(items) >= 2:
            item1, item2 = items[0], items[1]
            if item1[0][0] < item2[0][0]:
                left_item, right_item = item1[1], item2[1]
            else:
                left_item, right_item = item2[1], item1[1]
            self.boss_choices_label.text = f"LEFT: {left_item}  |  RIGHT: {right_item}"

    def pause_game(self):
        """Pause: unschedule game loop, show overlay, sync sound button."""
        if self.game_event:
            self.game_event.cancel()
            self.game_event = None
        self.pause_overlay.opacity = 1
        self.pause_overlay.disabled = False
        self.pause_overlay.sync_sound_button()
        AudioManager().play_sfx("click")

    def resume_game(self):
        """Resume: hide overlay, re-schedule game loop."""
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True
        if not self.game_event:
            self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)
        AudioManager().play_sfx("click")

    def restart_game(self):
        """Full restart: clear grid, reset scores/gems, generate fresh 4x4 platform."""
        AudioManager().play_sfx("click")
        self.grid.reset()
        self.penguin.is_dead = False
        self.penguin.action = "Idle"
        self.penguin.action_timer = 0.0
        self.penguin.anim_offset_y = 0.0
        self.penguin.visual_x = None
        self.penguin.visual_y = None
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]
        self.path_index = 0
        self.gems_collected = 0
        self.idle_timer = 0
        self.game_started = False
        self.particle_system.particles.clear()
        self.renderer.cam_x = None
        self.renderer.cam_y = None
        self.renderer.tile_textures.clear()
        self._start_new_session()
        self.metrics = RunMetrics(on_game_over=self._trigger_gameover_from_metrics)
        self.junction_interaction = YJunctionInteraction(self.metrics, self.session)
        self.boss_wave_index = 0
        self.boss_hp = 0
        self.boss_start_time = 0
        self.boss_wall_label.text = ""
        self.boss_choices_label.text = ""
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True
        if not self.game_event:
            self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)

    def go_home(self):
        AudioManager().play_sfx("click")
        if self.game_event:
            self.game_event.cancel()
            self.game_event = None
        Clock.schedule_once(lambda dt: setattr(self.manager, "current", "menu"), 0.2)

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
        if keycode[1] == "left":
            self.btn_left.handle_press()
            return True
        elif keycode[1] == "right":
            self.btn_right.handle_press()
            return True
        return False

    def _on_keyboard_up(self, keyboard, keycode):
        if not self.game_event:
            return False
        if keycode[1] == "left":
            self.btn_left.handle_release()
            return True
        elif keycode[1] == "right":
            self.btn_right.handle_release()
            return True
        return False
