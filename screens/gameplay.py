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

from core.asset_contract import (
    BOSS_REVIEW_SHEET,
    DRONE_REVIEW_SHEET,
    ENVIRONMENT_TILE_ATLAS,
    OBSTACLE_REVIEW_SHEET,
    PLAYER_REVIEW_SHEET,
)
from core.config import BOSS_DISTANCE_M, TARGET_FPS, TILE_H, TILE_IMG_H, TILE_W
from core.interaction import junction_prompt_text
from core.items import ItemType
from core.junction_data import get_junction
from core.messages import death_cause_text
from core.state import (
    DeathCause,
    DecisionPhase,
    GameOverReason,
    RunState,
    load_difficulty,
)
from game.controller import GameplayController, GameplayViewState
from game.grid import VISIBLE_BUFFER, GridManager
from game.particles import ParticleSystem
from game.penguin import Penguin
from infrastructure.audio import AudioManager
from infrastructure.logging_config import logger
from ui.components import (
    BossBanner,
    ChoiceCard,
    DecisionCard,
    FeedbackToast,
    HoverButton,
    HudRail,
    MeterBar,
    ProgressRing,
    StateOverlay,
)

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
        self.player_sheet_texture = CoreImage(
            "assets/generated/character/penguin_sheet_v2.png"
        ).texture
        self.obstacle_sheet_texture = CoreImage(
            "assets/generated/obstacles/obstacle_sheet_v1.png"
        ).texture
        self.gem_texture = CoreImage("assets/Gem/Coin_Gems/spr_coin_strip4.png").texture
        self.background_texture = CoreImage(
            "assets/generated/background/gameplay_background_v1.png"
        ).texture
        self.boss_sheet_texture = CoreImage(
            "assets/generated/boss/carbon_baron_sheet_v1.png"
        ).texture
        self.drone_sheet_texture = CoreImage(
            "assets/generated/characters/penguin_guide_drone_v1.png"
        ).texture
        tile_atlas = CoreImage("assets/generated/tiles/environment_tiles_v1.png").texture
        tile_names = {
            "cool": "cool_moss_ice",
            "frozen": "frozen_ice",
            "neon": "neon_pivot",
            "warning": "amber_warning",
            "thawed": "thawed_smog",
            "boss_safe": "boss_safe",
        }
        self._environment_textures = {
            key: tile_atlas.get_region(
                *ENVIRONMENT_TILE_ATLAS.cell_origin(frame_name),
                ENVIRONMENT_TILE_ATLAS.frame_width,
                ENVIRONMENT_TILE_ATLAS.frame_height,
            )
            for key, frame_name in tile_names.items()
        }
        self.cam_x = None
        self.cam_y = None
        self.shake_amount = 0
        self.background_time = 0.0

    def advance_visual(self, dt):
        """Advance presentation-only animation even while simulation is paused."""
        self.background_time += dt

    def trigger_shake(self, amount=10):
        self.shake_amount = amount

    def _get_tile_texture(self, col, row, grid_manager):
        tile = grid_manager.path_set.get((col, row))
        parent = self.parent
        heat = getattr(getattr(parent, "metrics", None), "heat_meter", 50.0)
        if tile and tile.is_safe:
            return self._environment_textures["boss_safe"]
        if tile and tile.state == "triggered":
            return self._environment_textures["warning"]
        if (col, row) in grid_manager.turn_points:
            return self._environment_textures["neon"]
        if heat >= 75:
            return self._environment_textures["thawed"]
        if tile and tile.is_fork:
            return self._environment_textures["frozen"]
        # Stable variation avoids per-frame random changes while keeping the
        # generated tile language visible throughout the run.
        variant = "cool" if (col * 7 + row * 11) % 4 else "frozen"
        return self._environment_textures[variant]

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

        # D1-A5: neon tint at turn points + chevron warning on the 3 tiles leading
        # into the nearest upcoming turn (visual scaffolding — no new assets,
        # reuses grid_manager.turn_points already recorded by _build_corner)
        turn_point_set = set(grid_manager.turn_points)
        chevron_positions = set()
        if path_index >= 0:
            lookahead = grid_manager.path[path_index + 1 : path_index + 11]
            for i, pos in enumerate(lookahead):
                if pos in turn_point_set:
                    chevron_positions.update(lookahead[max(0, i - 3) : i])
                    break

        self.canvas.clear()
        with self.canvas:
            distance = grid_manager.get_distance_m()
            heat = getattr(getattr(self.parent, "metrics", None), "heat_meter", 50.0)
            distance_tint = min(1.0, distance / 1000.0)
            heat_tint = max(0.0, min(1.0, (heat - 50.0) / 50.0))
            sky_r = 0.04 + 0.18 * distance_tint + 0.16 * heat_tint
            sky_g = 0.10 - 0.04 * distance_tint
            sky_b = 0.20 - 0.08 * distance_tint
            Color(1, 1, 1, 1)
            Rectangle(texture=self.background_texture, pos=(0, 0), size=Window.size)
            Color(sky_r, max(0.03, sky_g), max(0.04, sky_b), 0.58)
            Rectangle(pos=(0, 0), size=Window.size)
            Color(0.08 + 0.15 * distance_tint, 0.25, 0.32, 0.42)
            ridge_y = Window.height * (0.28 + 0.015 * math.sin(self.background_time * 0.4))
            Rectangle(pos=(-40, ridge_y), size=(Window.width + 80, Window.height * 0.32))
            Color(0.02, 0.05, 0.10, 0.55 + 0.18 * heat_tint)
            Rectangle(pos=(-40, 0), size=(Window.width + 80, ridge_y))
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
                    if (col, row) in turn_point_set:
                        Color(0.2, 1, 1, 1)  # neon pivot tile
                    elif (col, row) in chevron_positions:
                        Color(1, 0.6, 0.1, 1)  # chevron warning lead-in
                    elif obj.is_fork:
                        Color(1, 0.9, 0.4, 1)
                    else:
                        Color(1, 1, 1, 1)
                    tex = self._get_tile_texture(col, row, grid_manager)
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
                    # Floor warnings may animate the tile, but the player sprite
                    # stays anchored to its tile. Applying a random offset here
                    # made normal running look like a broken/stuttering sprite.
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

            skin_tex = self.player_sheet_texture.get_region(
                *PLAYER_REVIEW_SHEET.cell_origin(penguin.get_generated_frame_name()),
                PLAYER_REVIEW_SHEET.frame_width,
                PLAYER_REVIEW_SHEET.frame_height,
            )
            pw, ph = 96, 128
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

            skin_tex = self.player_sheet_texture.get_region(
                *PLAYER_REVIEW_SHEET.cell_origin(penguin.get_generated_frame_name()),
                PLAYER_REVIEW_SHEET.frame_width,
                PLAYER_REVIEW_SHEET.frame_height,
            )
            pw, ph = 96, 128
            Color(1, 1, 1, 1)
            Rectangle(
                texture=skin_tex,
                pos=(px + ox - pw // 2, py + oy + penguin.anim_offset_y),
                size=(pw, ph),
            )

    def _draw_obstacle(self, obs, tx, ty, ox, oy):
        """
        Draw stacked ice/carbon hazard layers using stack_height for degradation.
        Gameplay still owns hit/deactivation; this method only selects the
        matching generated visual state.
        """
        if obs.state == obs.STATE_HIT:
            frame_name = "hit"
        elif obs.state == obs.STATE_BREAK:
            frame_name = "breaking"
        elif obs.stack_height <= 1 and obs.size > 1:
            frame_name = "almost_destroyed"
        elif obs.stack_height < obs.size:
            frame_name = "damaged"
        else:
            frame_name = "idle"
        tex = self.obstacle_sheet_texture.get_region(
            *OBSTACLE_REVIEW_SHEET.cell_origin(frame_name),
            OBSTACLE_REVIEW_SHEET.frame_width,
            OBSTACLE_REVIEW_SHEET.frame_height,
        )
        bw, bh = 100, 100
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
        from infrastructure.audio import AudioManager

        if AudioManager().bgm_muted:
            self.btn_sound.background_normal = "assets/Component_UI/Button Sounds/volume_down.png"
            self.btn_sound.background_down = "assets/Component_UI/Button Sounds/volume_down.png"
        else:
            self.btn_sound.background_normal = "assets/Component_UI/Button Sounds/volume_up.png"
            self.btn_sound.background_down = "assets/Component_UI/Button Sounds/volume_up.png"

    def toggle_sound(self, *args):
        from infrastructure.audio import AudioManager

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
    @property
    def session(self):
        """Read-only view of the current run session owned by the controller."""
        return self.controller.session

    @property
    def metrics(self):
        """Read-only view of the current run metrics owned by the controller."""
        return self.controller.metrics

    @property
    def junction_interaction(self):
        """Read-only view of the current interaction service."""
        return self.controller.interaction

    @property
    def inventory(self):
        """Read-only view of the current run inventory."""
        return self.controller.inventory

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.controller = GameplayController(
            grid=GridManager(),
            difficulty=load_difficulty(),
            on_game_over=self._trigger_gameover_from_metrics,
        )
        self.grid = self.controller.grid
        self.penguin = Penguin()
        self.game_over = False
        self.game_event = None
        self._keyboard = None
        self.path_index = 0
        self.active_prompt_zone = None
        self.decision_phase: DecisionPhase | None = None
        self.decision_zone: int | None = None
        self.decision_ready = False
        self.decision_intro_remaining = 0.0
        self.decision_remaining = 0.0
        self.decision_grace_active = False
        self.pending_policy_zone: int | None = None
        self.handled_policy_zones: set[int] = set()

        self.is_respawning = False
        self.respawn_count = 0
        self.decision_grace_active = False
        self._respawn_event = None
        self._respawn_remaining = 0.0
        self._nav_event = None
        self._boss_warning_shown = False
        self.grid.reset()
        self.last_checkpoint_col = self.grid.path[0][0]
        self.last_checkpoint_row = self.grid.path[0][1]
        start = self.grid.path[0]
        self.penguin.col = start[0]
        self.penguin.row = start[1]
        self.idle_timer = 0
        self.MAX_IDLE_TIME = 2.0
        self.game_started = False
        self.particle_system = ParticleSystem()

        self.renderer = KivyRenderer()
        self.add_widget(self.renderer)

        self.hud_bg = HudRail(
            orientation="horizontal",
            size_hint=(0.90, None),
            height=64,
            spacing=8,
            padding=[14, 8, 14, 8],
            pos_hint={"center_x": 0.53, "top": 0.975},
        )

        self.score_label = Label(
            text="SCORE: 0",
            font_size="22sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            size_hint=(None, None),
            size=(220, 40),
            halign="left",
            valign="middle",
            text_size=(220, 40),
        )

        gem_box = BoxLayout(
            orientation="horizontal", size_hint=(None, None), size=(108, 40), spacing=4
        )

        gem_tex = CoreImage("assets/Gem/Coin_Gems/spr_coin_strip4.png").texture.get_region(
            0, 0, 16, 16
        )
        gem_icon = Image(texture=gem_tex, size_hint=(None, None), size=(40, 40))

        self.gem_label = Label(
            text="GEMS 0",
            font_size="15sp",
            bold=True,
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            size_hint=(None, None),
            size=(66, 40),
            halign="left",
            valign="middle",
            text_size=(66, 40),
        )

        gem_box.add_widget(gem_icon)
        gem_box.add_widget(self.gem_label)

        self.hud_bg.add_widget(self.score_label)
        self.hud_bg.add_widget(gem_box)
        self.hearts_label = Label(
            text=f"♥ {self.metrics.hearts}",
            font_size="20sp",
            bold=True,
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
            color=(1.0, 0.55, 0.75, 1.0),
            size_hint=(None, None),
            size=(92, 40),
            halign="center",
            valign="middle",
            text_size=(92, 40),
        )
        self.heat_bar = MeterBar(
            value=self.metrics.heat_meter,
            max_value=self.metrics.max_meter,
            warn_threshold=0.8 * self.metrics.max_meter,
            bar_color=[1, 0.5, 0.2, 1],
            size_hint=(None, None),
            size=(126, 14),
        )
        self.anger_bar = MeterBar(
            value=self.metrics.capitalist_anger,
            max_value=self.metrics.max_meter,
            warn_threshold=0.8 * self.metrics.max_meter,
            bar_color=[0.8, 0.2, 0.2, 1],
            size_hint=(None, None),
            size=(126, 14),
        )

        def _meter_column(caption, bar):
            column = BoxLayout(
                orientation="vertical", size_hint=(None, None), size=(126, 42), spacing=2
            )
            column.add_widget(
                Label(
                    text=caption,
                    font_size="11sp",
                    bold=True,
                    font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
                    color=(0.9, 0.95, 1.0, 1.0),
                    size_hint=(1, None),
                    height=20,
                    halign="center",
                    valign="middle",
                    text_size=(126, 20),
                )
            )
            column.add_widget(bar)
            return column

        self.hud_bg.add_widget(self.hearts_label)
        self.hud_bg.add_widget(_meter_column("HEAT · โลก", self.heat_bar))
        self.hud_bg.add_widget(_meter_column("ANGER · เศรษฐกิจ", self.anger_bar))
        self.meter_hint_label = Label(
            text="แตะ 100 = แพ้",
            font_size="12sp",
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
            color=(0.8, 0.9, 1.0, 0.9),
            size_hint=(None, None),
            size=(112, 42),
            halign="center",
            valign="middle",
            text_size=(112, 42),
        )
        self.hud_bg.add_widget(self.meter_hint_label)
        self.inventory_label = Label(
            text="Items: -",
            font_size="14sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            size_hint=(None, None),
            size=(270, 40),
            halign="left",
            valign="middle",
            text_size=(270, 40),
            shorten=True,
            shorten_from="right",
        )
        self.hud_bg.add_widget(self.inventory_label)

        self.add_widget(self.hud_bg)

        drone_origin = DRONE_REVIEW_SHEET.cell_origin("idle_hover")
        self.guide_drone = Image(
            texture=self.renderer.drone_sheet_texture.get_region(
                *drone_origin,
                DRONE_REVIEW_SHEET.frame_width,
                DRONE_REVIEW_SHEET.frame_height,
            ),
            size_hint=(None, None),
            size=(96, 96),
            pos_hint={"right": 0.97, "center_y": 0.24},
            allow_stretch=True,
            keep_ratio=True,
            opacity=0.92,
        )
        self.add_widget(self.guide_drone)

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
        self.checkpoint_label = FeedbackToast(
            text="",
            font_size="30sp",
            color=(1, 1, 1, 1),
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "center_y": 0.75},
            text_size=(min(Window.width * 0.58, 900), None),
            halign="center",
            valign="middle",
            opacity=0,
        )
        self.checkpoint_label.bind(texture_size=self.checkpoint_label.setter("size"))
        self.add_widget(self.checkpoint_label)
        self.respawn_overlay = StateOverlay(
            text="RESPAWNING...\nกำลังสร้างเส้นทางปลอดภัย",
            font_size="30sp",
            color=(0.65, 0.9, 1.0, 1),
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
            text_size=(Window.width, Window.height),
            halign="center",
            valign="middle",
            opacity=0,
            disabled=True,
        )
        self.add_widget(self.respawn_overlay)
        self.respawn_ring = ProgressRing(
            size_hint=(None, None),
            size=(96, 96),
            pos_hint={"center_x": 0.5, "center_y": 0.42},
            opacity=0,
        )
        self.add_widget(self.respawn_ring)
        self.respawn_grace_label = Label(
            text="",
            font_size="18sp",
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
            color=(0.55, 0.95, 1.0, 1),
            size_hint=(None, None),
            size=(520, 36),
            pos_hint={"center_x": 0.5, "center_y": 0.32},
            halign="center",
            valign="middle",
            opacity=0,
        )
        self.add_widget(self.respawn_grace_label)

        # Boss UI
        self.boss_wall_label = Label(
            text="",
            font_size="24sp",
            bold=True,
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",  # wall_text เป็นภาษาไทย
            color=(1, 0.2, 0.2, 1),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.69},
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            text_size=(700, None),
            halign="center",
            valign="middle",
        )
        self.boss_wall_label.bind(texture_size=self.boss_wall_label.setter("size"))
        self.add_widget(self.boss_wall_label)

        self.boss_choices_label = Label(
            text="",
            font_size="20sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(0.9, 0.9, 0.2, 1),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.64},
            outline_width=2,
            outline_color=(0, 0, 0, 1),
        )
        self.add_widget(self.boss_choices_label)

        self.boss_status_label = BossBanner(
            text="",
            font_size="16sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(1, 0.45, 0.25, 1),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.91},
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            opacity=0,
        )
        self.boss_status_label.bind(texture_size=self.boss_status_label.setter("size"))
        self.add_widget(self.boss_status_label)

        self.boss_portrait = Image(
            texture=self.renderer.boss_sheet_texture.get_region(
                *BOSS_REVIEW_SHEET.cell_origin("idle_hover"),
                BOSS_REVIEW_SHEET.frame_width,
                BOSS_REVIEW_SHEET.frame_height,
            ),
            size_hint=(None, None),
            size=(224, 190),
            pos_hint={"right": 0.95, "top": 0.60},
            allow_stretch=True,
            keep_ratio=True,
            opacity=0,
        )
        self.add_widget(self.boss_portrait)

        self.junction_banner = Label(
            text="",
            font_size="18sp",
            bold=True,
            # situation/left.label/right.label ใน junctions.json เป็นภาษาไทยทั้งหมด —
            # Kenney Future เป็นฟอนต์ Latin-only ไม่มี glyph ไทย ต้องใช้ฟอนต์นี้แทน
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
            color=(0.7, 0.9, 1, 1),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "top": 0.72},
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            text_size=(700, None),
            halign="center",
            valign="middle",
        )
        self.junction_banner.bind(texture_size=self.junction_banner.setter("size"))
        self.add_widget(self.junction_banner)

        self.decision_dim = Widget(size_hint=(1, 1), opacity=0, disabled=True)
        with self.decision_dim.canvas:
            GColor(0.02, 0.04, 0.10, 0.72)
            self._decision_dim_rect = GRect(pos=self.decision_dim.pos, size=self.decision_dim.size)
        self.decision_dim.bind(
            pos=lambda obj, value: setattr(self._decision_dim_rect, "pos", value),
            size=lambda obj, value: setattr(self._decision_dim_rect, "size", value),
        )
        self.add_widget(self.decision_dim)

        self.decision_left = self._build_decision_choice(
            "LEFT", {"center_x": 0.27, "center_y": 0.30}, (0.25, 0.85, 1.0, 1)
        )
        self.decision_right = self._build_decision_choice(
            "RIGHT", {"center_x": 0.73, "center_y": 0.30}, (0.65, 0.45, 1.0, 1)
        )

        self.decision_card = DecisionCard(
            text="",
            font_size="24sp",
            bold=True,
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "center_y": 0.52},
            text_size=(900, None),
            halign="center",
            valign="middle",
            opacity=0,
        )
        self.decision_card.bind(texture_size=self.decision_card.setter("size"))
        self.add_widget(self.decision_card)
        self.decision_countdown = Label(
            text="",
            font_size="30sp",
            bold=True,
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
            color=(1, 0.85, 0.2, 1),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "center_y": 0.27},
            opacity=0,
        )
        self.add_widget(self.decision_countdown)

        # Keep the boss portrait above the decision dimmer so the character is
        # readable during every wave instead of becoming a dark silhouette.
        self.remove_widget(self.boss_portrait)
        self.add_widget(self.boss_portrait)

    def _build_decision_choice(self, title, pos_hint, accent):
        """Create one keyboard-mapped choice card without owning game logic."""
        card = ChoiceCard(
            text=title,
            font_size="18sp",
            bold=True,
            font_name="assets/Component_UI/Font/NotoSansThai-Regular.ttf",
            color=(1, 1, 1, 1),
            size_hint=(0.40, None),
            height=112,
            pos_hint=pos_hint,
            text_size=(Window.width * 0.36, 92),
            halign="center",
            valign="middle",
            opacity=0,
            accent=accent,
        )
        self.add_widget(card)
        return card

    def _set_drone_pose(self, frame_name: str) -> None:
        origin = DRONE_REVIEW_SHEET.cell_origin(frame_name)
        self.guide_drone.texture = self.renderer.drone_sheet_texture.get_region(
            *origin,
            DRONE_REVIEW_SHEET.frame_width,
            DRONE_REVIEW_SHEET.frame_height,
        )

    def show_checkpoint_message(self, message: str):
        """Display a temporary non-blocking message when a checkpoint is reached.
        The label fades in, stays for 1.5 seconds, then fades out.
        """
        Animation.cancel_all(self.checkpoint_label)
        self.checkpoint_label.text = message
        self.checkpoint_label.opacity = 1
        anim = (
            Animation(opacity=1, duration=0.2)
            + Animation(duration=1.5)
            + Animation(opacity=0, duration=0.5)
        )
        anim.start(self.checkpoint_label)

    def _open_policy_decision(self, zone_id: int):
        junction = get_junction(zone_id)
        cfg = load_difficulty().get("decision", {})
        AudioManager().play_sfx("quiz_open")
        self.decision_phase = DecisionPhase.POLICY
        self._set_drone_pose("point_forward")
        self.decision_zone = zone_id
        self.decision_ready = False
        self.decision_intro_remaining = float(cfg.get("intro_seconds", 1.5))
        self.decision_remaining = float(cfg.get("policy_seconds", 15.0))
        self.decision_card.text = f"ZONE {zone_id}\n{junction.situation}"
        self.decision_left.text = f"←  {junction.left.label}"
        self.decision_right.text = f"{junction.right.label}  →"
        self.decision_card.opacity = 1
        self.decision_left.opacity = 1
        self.decision_right.opacity = 1
        self.decision_dim.opacity = 1
        self.junction_banner.opacity = 0
        self.decision_countdown.text = "เตรียมคำถาม..."
        self.decision_countdown.opacity = 1

    def _open_boss_decision(self, wave_no: int):
        cfg = load_difficulty().get("decision", {})
        AudioManager().play_sfx("boss_alert")
        sides = {
            placement.side: placement.item_id
            for placement in self.grid.boss_items.values()
            if placement.wave == wave_no
        }
        self.decision_phase = DecisionPhase.BOSS
        self._set_drone_pose("warning")
        self.decision_zone = wave_no
        self.decision_ready = False
        self.decision_intro_remaining = float(cfg.get("intro_seconds", 1.5))
        self.decision_remaining = float(cfg.get("boss_seconds", 12.0))
        self.decision_card.text = f"BOSS WAVE {wave_no}\nเลือกหลักฐานที่หักล้างกำแพงนี้"
        self.decision_left.text = f"←  {sides.get('left', '?')}"
        self.decision_right.text = f"{sides.get('right', '?')}  →"
        self.decision_card.opacity = 1
        self.decision_left.opacity = 1
        self.decision_right.opacity = 1
        self.decision_dim.opacity = 1
        self.junction_banner.opacity = 0
        self.decision_countdown.text = "เตรียมคำถาม..."
        self.decision_countdown.opacity = 1

    def _close_decision(self):
        self.decision_phase = None
        self.decision_zone = None
        self.decision_ready = False
        self.decision_card.opacity = 0
        self.decision_left.opacity = 0
        self.decision_right.opacity = 0
        self.decision_countdown.opacity = 0
        self.decision_dim.opacity = 0
        self._set_drone_pose("idle_hover")
        self.junction_banner.opacity = 0

    def _update_decision(self, dt: float):
        if self.decision_phase is None:
            return
        if self.decision_intro_remaining > 0:
            self.decision_intro_remaining = max(0.0, self.decision_intro_remaining - dt)
            if self.decision_intro_remaining == 0:
                self.decision_ready = True
        elif self.decision_ready:
            self.decision_remaining -= dt
            self.decision_countdown.text = f"เวลาเหลือ {max(0.0, self.decision_remaining):.1f}s"
            if self.decision_remaining <= 0:
                self._resolve_decision_timeout()

    def _resolve_decision_timeout(self):
        if self.decision_phase is DecisionPhase.POLICY and self.decision_zone is not None:
            zone_id = self.decision_zone
            self.handled_policy_zones.add(zone_id)
            penalty = float(load_difficulty().get("decision", {}).get("timeout_meter_penalty", 5.0))
            try:
                self.controller.resolve_timeout(
                    get_junction(zone_id), self.grid.get_distance_m(), penalty
                )
            except KeyError:
                logger.warning("No junction data for timeout zone %s", zone_id)
            self.pending_policy_zone = None
            self.show_checkpoint_message("TIMEOUT — ไม่มีการเลือก")
        elif self.decision_phase is DecisionPhase.BOSS:
            AudioManager().play_sfx("wrong")
            self.show_checkpoint_message("TIMEOUT — เลือกเลนขวาอัตโนมัติ")
            self._close_decision()
            self._move(DIR_RIGHT)
            return
        self._stabilize_after_decision()
        self._close_decision()

    def _stabilize_after_decision(self):
        """Give the player a stable tile after reading/answering a quiz."""
        self.decision_grace_active = True
        self.idle_timer = 0.0
        tile = self.grid.path_set.get((self.penguin.col, self.penguin.row))
        if tile and not tile.is_safe:
            tile.state = "normal"
            tile.trigger_timer = self.grid.trigger_seconds_for_distance()
            tile.offset_y = 0.0
            tile.fall_velocity = 0.0

    def _blocked_in_decision_corridor(self, new_col: int, new_row: int) -> bool:
        """Block an invalid input in the corridor after a policy quiz.

        The quiz chooses policy semantics only; it never chooses the movement
        lane.  Until the physical split is reached, a wrong-direction input is
        ignored rather than silently redirected or treated as a fall.
        """
        return self.pending_policy_zone is not None and not self.grid.is_on_path(new_col, new_row)

    def _cancel_pending_events(self) -> None:
        """Cancel callbacks owned by this screen before replacing a run."""
        for attr in ("_respawn_event", "_nav_event"):
            event = getattr(self, attr)
            if event is not None:
                event.cancel()
                setattr(self, attr, None)

    def _trigger_gameover_from_metrics(self):
        self.penguin.is_dead = True
        if self._nav_event is None:
            self._nav_event = Clock.schedule_once(self._go_gameover, 0.8)

    def _respawn_penguin(self, dt=None):
        self._respawn_event = None
        self.penguin.is_dead = False
        self.is_respawning = False
        self.penguin.col = self.last_checkpoint_col
        self.penguin.row = self.last_checkpoint_row
        self.penguin.visual_x = None
        self.penguin.visual_y = None
        self.penguin.anim_offset_y = 0.0
        self.penguin.action = "Idle"
        self.penguin.action_timer = 0.0
        self.idle_timer = 0.0
        self.decision_grace_active = False
        self.pending_policy_zone = None
        checkpoint_index = self.grid.get_path_index(
            self.last_checkpoint_col, self.last_checkpoint_row
        )
        if checkpoint_index >= 0:
            self.path_index = checkpoint_index
        # ทางเดินช่วงที่เดินผ่านไปแล้วอาจละลาย/หายไปหมดระหว่างรอ respawn 3 วิ —
        # แช่แข็งกลับให้เดินต่อได้จริง กัน respawn แล้วตกซ้ำวนไม่จบ
        self.grid.repair_path_ahead_of_checkpoint(
            self.last_checkpoint_col,
            self.last_checkpoint_row,
            tiles_ahead=VISIBLE_BUFFER,
        )
        self.controller.complete_respawn()
        if self.metrics.last_death_cause is not None:
            self.show_checkpoint_message(death_cause_text(self.metrics.last_death_cause))
        self.renderer.trigger_shake(0)
        self.renderer.cam_x = None
        self.renderer.cam_y = None
        self.active_prompt_zone = None
        self.junction_banner.text = ""
        self.respawn_overlay.opacity = 0
        self.respawn_overlay.disabled = True
        self.respawn_ring.opacity = 0
        self.respawn_grace_label.opacity = 1
        self._close_decision()
        # RESPAWNING → RUNNING ตาม state machine (ADR-010 / state-machines.md §3)
        self.controller.resume_after_respawn()

    def _handle_fall(self, cause: DeathCause) -> bool:
        if self.is_respawning or self.penguin.is_dead:
            return False
        if not self.controller.request_death(cause):
            current_tile = self.grid.path_set.get((self.penguin.col, self.penguin.row))
            if current_tile and current_tile.state == "falling":
                current_tile.state = "normal"
                current_tile.trigger_timer = 0.0
                current_tile.fall_velocity = 0.0
            self.idle_timer = 0.0
            return False
        self.penguin.is_dead = True
        self._refresh_status_hud()
        if self.metrics.needs_respawn:
            self.is_respawning = True
            self.respawn_count += 1
            # ADR-002/010: RUNNING → RESPAWNING + RespawnEvent (respawn_count,
            # score_penalty 10%) — การหักคะแนนจริงเป็นหน้าที่ scoring ฝั่ง server
            self.controller.begin_respawn()
            self.controller.record_respawn(
                checkpoint_col=self.last_checkpoint_col,
                checkpoint_row=self.last_checkpoint_row,
                respawn_count=self.respawn_count,
                distance_m=self.grid.get_distance_m(),
            )
            # The full-screen StateOverlay is the single respawn composition;
            # do not show a second toast carrying the same message underneath.
            Animation.cancel_all(self.checkpoint_label)
            self.checkpoint_label.opacity = 0
            self.respawn_overlay.opacity = 1
            self.respawn_overlay.disabled = False
            self._respawn_remaining = self.metrics.respawn_seconds
            self.respawn_ring.progress = 0.0
            self.respawn_ring.opacity = 1
            self.respawn_grace_label.opacity = 0
            AudioManager().play_sfx("respawn")
            self._respawn_event = Clock.schedule_once(
                self._respawn_penguin, self.metrics.respawn_seconds
            )
        return True

    def _start_new_session(self):
        """Create the session, metrics, and junction interaction as one run unit.

        Call only after ``grid.reset()``: all three objects must reference this run,
        otherwise policy events are silently written to an obsolete session
        (interaction holds a reference to session — if not rebound here, the new
        run's PolicyChoiceEvents land in the discarded RunRecord and the Report
        Card shows everything as "unplayed"). Checkpoint reset also depends on
        grid.reset() having run first, since it reads grid.path[0].
        """
        self.controller.start_run()
        self.grid = self.controller.grid
        self._cancel_pending_events()
        self.is_respawning = False
        self.respawn_count = 0
        self._boss_warning_shown = False
        self.active_prompt_zone = None
        self.pending_policy_zone = None
        self.handled_policy_zones.clear()
        self.junction_banner.text = ""
        self.respawn_overlay.opacity = 0
        self.respawn_overlay.disabled = True
        self.respawn_ring.opacity = 0
        self.respawn_grace_label.opacity = 0
        self.checkpoint_label.opacity = 0
        start = self.grid.path[0]
        self.last_checkpoint_col, self.last_checkpoint_row = start
        self._refresh_status_hud()
        self._update_inventory_hud()

    def _refresh_status_hud(self):
        """Sync hearts label + heat/anger bars กับ RunMetrics ปัจจุบัน — จุดเดียวใช้ทุก path"""
        snapshot = self._view_state()
        self.hearts_label.text = f"♥ {snapshot.hearts}"
        self.heat_bar.value = snapshot.heat
        self.anger_bar.value = snapshot.anger

    def _view_state(self) -> GameplayViewState:
        """Create a fresh immutable presentation snapshot for this update cycle."""
        self.controller.set_view_context(
            gems=self.gems_collected, decision_phase=self.decision_phase
        )
        return self.controller.view_state()

    def _update_inventory_hud(self):
        names = [item.value.replace("_", " ").title() for item in self.inventory.get_items()]
        self.inventory_label.text = f"Items: {' | '.join(names) if names else '-'}"

    def _show_policy_feedback(self, junction, side: str, before: tuple[float, float]) -> None:
        option = junction.option(side)
        heat_delta = self.metrics.heat_meter - before[0]
        anger_delta = self.metrics.capitalist_anger - before[1]
        reason = option.note or "ผลกระทบเกิดจาก trade-off ของนโยบายนี้"
        self.show_checkpoint_message(
            f"เลือกแล้ว\nHeat {heat_delta:+.0f} | Anger {anger_delta:+.0f}\n{reason}"
        )

    def on_enter(self):
        from core.state import StateManager

        logger.info("เข้าสู่หน้า GamePlay")

        if not self._keyboard:
            self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
            self._keyboard.bind(on_key_down=self._on_keyboard_down)
            self._keyboard.bind(on_key_up=self._on_keyboard_up)

        self.penguin.equip_skin(StateManager().selected_skin)
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
        self.respawn_overlay.opacity = 0
        self.respawn_overlay.disabled = True
        self.boss_wall_label.text = ""
        self.boss_choices_label.text = ""
        self.boss_status_label.text = ""
        self.boss_status_label.opacity = 0
        self.boss_portrait.opacity = 0
        self.checkpoint_label.opacity = 0

    def on_leave(self):
        if self.game_event:
            self.game_event.cancel()
            self.game_event = None  # ✅ fix

        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard.unbind(on_key_up=self._on_keyboard_up)
            self._keyboard = None

    def update(self, dt):
        snapshot = self._view_state()
        dist = snapshot.distance_m
        dist_str = f"{dist / 1000:.1f} km" if dist >= 1000 else f"{dist} m"
        self.score_label.text = f"SCORE: {dist_str}"
        self.gem_label.text = f"GEMS {snapshot.gems}"

        # Decision and respawn states pause the simulation clock. Presentation
        # animation still advances below, but obstacles and cleanup do not.
        if self.decision_phase is None and not self.is_respawning:
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
        self.renderer.advance_visual(dt)
        if self.decision_phase is None:
            self.controller.tick(dt)
        self._update_decision(dt)

        if self.is_respawning:
            duration = max(0.001, self.metrics.respawn_seconds)
            self._respawn_remaining = max(0.0, self._respawn_remaining - dt)
            self.respawn_ring.progress = min(1.0, 1.0 - (self._respawn_remaining / duration))
        elif self.metrics.grace_active:
            self.respawn_grace_label.text = (
                f"ปลอดภัยชั่วคราว · ขยับต่อได้ ({self.metrics.grace_remaining:.1f}s)"
            )
            self.respawn_grace_label.opacity = 1
        else:
            self.respawn_grace_label.opacity = 0

        if self.decision_phase is not None:
            self.renderer.draw(self.grid, self.penguin, self.path_index)
            return

        if (
            not self.penguin.is_dead
            and not self.is_respawning
            and not self.decision_grace_active
            and self.game_started
        ):
            self.grid.update_tiles(
                dt,
                (self.penguin.col, self.penguin.row),
                suppress_current_tile_trigger=self.metrics.grace_active,
            )

            # Check if penguin's tile is falling
            current_tile = self.grid.path_set.get((self.penguin.col, self.penguin.row))
            if current_tile and current_tile.state == "falling":
                AudioManager().play_sfx("Down")
                if self._handle_fall(DeathCause.MELT):
                    self.renderer.draw(self.grid, self.penguin, self.path_index)
                    return

            self.idle_timer += dt
            is_shaking = current_tile and current_tile.state == "triggered"

            if self.idle_timer >= self.MAX_IDLE_TIME:
                logger.warning(f"พื้นถล่ม! ยืนนิ่งนานเกินไปที่ ({self.penguin.col}, {self.penguin.row})")
                if current_tile and not current_tile.is_safe:
                    current_tile.state = "falling"
                    current_tile.fall_velocity = 0.0
                    AudioManager().play_sfx("Down")
                    if self._handle_fall(DeathCause.IDLE):
                        self.renderer.draw(self.grid, self.penguin, self.path_index)
                        return

            self.renderer.draw(
                self.grid, self.penguin, self.path_index, is_shaking_floor=is_shaking
            )
        else:
            # Respawn pauses gameplay simulation; rendering and presentation still
            # run, but no additional tiles may decay while the player is away.
            if not self.is_respawning and not self.decision_grace_active:
                self.grid.update_tiles(
                    dt,
                    (self.penguin.col, self.penguin.row),
                    suppress_current_tile_trigger=self.metrics.grace_active,
                )
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

        if self.decision_phase is not None:
            if not self.decision_ready:
                return
            decision_phase = self.decision_phase
            selected_side = "left" if direction == DIR_LEFT else "right"
            AudioManager().play_sfx(f"choice_{selected_side}")
            if decision_phase is DecisionPhase.POLICY and self.decision_zone is not None:
                zone_id = self.decision_zone
                # A quiz answer is a semantic choice, not a movement command.
                # Keep the penguin on the prompt tile; the selected side is
                # not a movement command and does not own a lane.
                self.pending_policy_zone = zone_id
                self.handled_policy_zones.add(zone_id)
                try:
                    junction = get_junction(zone_id)
                    before = (self.metrics.heat_meter, self.metrics.capitalist_anger)
                    self.controller.choose_policy(
                        junction, selected_side, self.grid.get_distance_m()
                    )
                    self._refresh_status_hud()
                    self._show_policy_feedback(junction, selected_side, before)
                except KeyError:
                    logger.warning("No junction data for choice zone %s", zone_id)
                self._stabilize_after_decision()
            self._close_decision()
            if decision_phase is DecisionPhase.POLICY:
                return
            self._move(direction)
            return

        if self.decision_grace_active:
            self.decision_grace_active = False

        if direction == DIR_LEFT:
            self.penguin.facing_left = True
        elif direction == DIR_RIGHT:
            self.penguin.facing_left = False

        new_col = self.penguin.col + direction[0]
        new_row = self.penguin.row + direction[1]
        if self._blocked_in_decision_corridor(new_col, new_row):
            self.idle_timer = 0.0
            return

        # ── Obstacle collision check ──
        obs = self.grid.get_obstacle_at(new_col, new_row)
        if obs and obs.active and obs.state != obs.STATE_BREAK:
            # Hit the obstacle — penguin stays at CURRENT position (no movement)
            result = obs.hit()
            AudioManager().play_sfx("Hit")
            self.idle_timer = 0
            self.game_started = True
            self.controller.record_obstacle_hit(
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
            self.controller.collect(
                item_type="gem",
                col=new_col,
                row=new_row,
                value=val,
                distance_m=self.grid.get_distance_m(),
            )

        item = self.grid.get_scientific_item_at(new_col, new_row)
        if item:
            self.grid.scientific_items.pop((new_col, new_row), None)
            if self.controller.add_inventory_item(item):
                self.controller.collect(
                    item_type="scientific_item",
                    col=new_col,
                    row=new_row,
                    value=1,
                    distance_m=self.grid.get_distance_m(),
                )
                self._update_inventory_hud()

        # ── Boss item collection ──
        placement = self.grid.get_boss_item_at(new_col, new_row)
        if placement:
            from core.boss_data import load_boss_data

            boss_data = load_boss_data()
            wave_data = boss_data.waves.get(placement.wave)
            is_correct = placement.item_id == wave_data.correct_item if wave_data else False

            # ผลของแต่ละเวฟอ่านจาก balance/v1/boss.json (on_correct/on_wrong ใช้
            # key "boss_armor"/"hearts") — ไม่ hardcode เพื่อให้ balance pass แก้ data ได้
            if is_correct:
                AudioManager().play_sfx("correct")
                if wave_data:
                    self.boss_hp += wave_data.on_correct.get("boss_armor", -1)
                self.controller.record_boss_phase(
                    phase=placement.wave,
                    outcome="damage_dealt",
                    distance_m=self.grid.get_distance_m(),
                )
                self.show_checkpoint_message("CORRECT!")
            else:
                AudioManager().play_sfx("wrong")
                hearts_delta = wave_data.on_wrong.get("hearts", -1) if wave_data else -1
                # ในบอสไม่มี fall-respawn (state-machines.md §3) — เสียหัวใจตรง ๆ
                for _ in range(-hearts_delta):
                    self.controller.request_death(None, allow_respawn=False)
                self.controller.record_boss_phase(
                    phase=placement.wave,
                    outcome="damaged",
                    distance_m=self.grid.get_distance_m(),
                )
                self.show_checkpoint_message("WRONG FACT!")

            self._refresh_status_hud()

            self.boss_wave_index = placement.wave + 1
            self.grid.pop_boss_wave(placement.wave)

            if self.boss_hp <= 0:
                self._set_drone_pose("report_celebration")
                self.controller.record_boss_victory(
                    total_time_s=self.session.elapsed() - self.boss_start_time,
                    distance_m=self.grid.get_distance_m(),
                )
                self.show_checkpoint_message("BOSS DEFEATED!")
                AudioManager().play_sfx("victory")
                self.boss_wall_label.text = ""
                self.boss_choices_label.text = ""
                self.boss_status_label.text = ""
                self.boss_status_label.opacity = 0
                self.boss_portrait.opacity = 0
                self.controller.finish()
                self._nav_event = Clock.schedule_once(self._go_report, 2.0)
                return
            elif self.boss_wave_index > 3:
                self.show_checkpoint_message("FAILED TO DEFEAT BOSS!")
                self.boss_wall_label.text = ""
                self.boss_choices_label.text = ""
                self.boss_status_label.text = ""
                self.boss_status_label.opacity = 0
                self.boss_portrait.opacity = 0
                # trigger_game_over → callback ปิด record (BOSS → FINISHED) ให้เอง
                self.controller.trigger_game_over(GameOverReason.BOSS)
                return
            else:
                self._update_boss_ui(self.boss_wave_index)
                self._open_boss_decision(self.boss_wave_index)

        # ── Move penguin to new position ──
        self.penguin.col = new_col
        self.penguin.row = new_row
        self.game_started = True

        self.penguin.action = "Jump"
        self.penguin.action_timer = 0.25
        self.renderer.anim_frame = 0

        prompt_zone = self.grid.get_junction_prompt(new_col, new_row)
        if prompt_zone != self.active_prompt_zone:
            self.active_prompt_zone = prompt_zone
            if prompt_zone is not None:
                try:
                    self.junction_banner.text = junction_prompt_text(get_junction(prompt_zone))
                    self._open_policy_decision(prompt_zone)
                except KeyError:
                    logger.warning("No junction prompt data for zone %s", prompt_zone)

        self.grid.check_fork_resolution(new_col, new_row)
        resolved_fork = self.grid.pop_resolved_fork()
        if resolved_fork:
            zone_id, side = resolved_fork
            self.active_prompt_zone = None
            self.junction_banner.text = ""
            if zone_id not in self.handled_policy_zones:
                try:
                    junction = get_junction(zone_id)
                    self.controller.choose_policy(
                        junction, side, distance_m=self.grid.get_distance_m()
                    )
                    self._refresh_status_hud()
                except KeyError:
                    logger.warning("No junction data for resolved zone %s", zone_id)
            if zone_id == self.pending_policy_zone:
                self.pending_policy_zone = None

        if self.grid.is_on_path(new_col, new_row):
            self.grid.step_forward()
            # A fork tile has no centreline index; boss entry is crossing the
            # distance threshold, not landing on one exact centreline position.
            dist_m = self.grid.get_distance_m()
            idx = self.grid.get_path_index(new_col, new_row)
            if idx >= 0:
                self.path_index = idx
                self.grid.extend_if_needed(self.path_index)
                AudioManager().play_sfx("step")
                # Normal movement is intentionally stable; camera shake is
                # reserved for collisions/falls so the first run does not feel
                # like the player sprite is vibrating continuously.
                self.renderer.shake_amount = 0
                self.idle_timer = 0
                # Checkpoint notification
                if self.grid.forward_tiles % 100 == 0:
                    self.show_checkpoint_message(f"{dist_m}M REACHED!")
                    self.last_checkpoint_col = self.penguin.col
                    self.last_checkpoint_row = self.penguin.row
                    self.controller.record_checkpoint(
                        checkpoint_index=self.grid.forward_tiles // 100,
                        distance_m=dist_m,
                    )
                if (
                    BOSS_DISTANCE_M - 20 <= dist_m < BOSS_DISTANCE_M - 10
                    and not self._boss_warning_shown
                ):
                    self.show_checkpoint_message("WARNING: CARBON BARON APPROACHING!")
                    self._boss_warning_shown = True

            if dist_m >= BOSS_DISTANCE_M and self.session.run_record.state == RunState.RUNNING:
                self.controller.enter_boss(distance_m=dist_m)
                self.show_checkpoint_message("BOSS PHASE STARTED!")
                self.boss_wave_index = 1
                from core.boss_data import load_boss_data

                self.boss_hp = load_boss_data().armor
                self.boss_start_time = self.session.elapsed()
                self._update_boss_ui(self.boss_wave_index)
                self._open_boss_decision(self.boss_wave_index)

        else:
            # ตกนอกเส้นทาง = เสียหัวใจ + respawn ที่ checkpoint (ADR-010)
            # ไม่ game over ตรง ๆ — หัวใจหมดค่อยจบผ่าน callback ของ RunMetrics
            AudioManager().play_sfx("Down")
            logger.info(f"ตกนอกเส้นทาง! ระยะ {self.grid.get_distance_m()} m")
            self._handle_fall(DeathCause.FALL)

    def _go_gameover(self, _dt=None):
        self._nav_event = None
        self.manager.current = "gameover"

    def _go_report(self, _dt=None):
        self._nav_event = None
        self.manager.current = "report"

    def _update_boss_ui(self, wave_no=None):
        from core.boss_data import load_boss_data

        wave_no = self.boss_wave_index if wave_no is None else wave_no
        wave = load_boss_data().waves.get(wave_no)
        if not wave:
            self.boss_wall_label.text = ""
            self.boss_choices_label.text = ""
            self.boss_status_label.text = ""
            self.boss_status_label.opacity = 0
            self.boss_portrait.opacity = 0
            return

        self.boss_wall_label.text = wave.wall_text
        frame_name = {
            1: "wave_1_red_pulse",
            2: "wave_2_methane_heat",
            3: "wave_3_overheat",
        }.get(wave_no)
        if frame_name:
            origin = BOSS_REVIEW_SHEET.cell_origin(frame_name)
            self.boss_portrait.texture = self.renderer.boss_sheet_texture.get_region(
                *origin,
                BOSS_REVIEW_SHEET.frame_width,
                BOSS_REVIEW_SHEET.frame_height,
            )
        self.boss_portrait.opacity = 1
        self.boss_status_label.color = {
            1: (1, 0.35, 0.25, 1),
            2: (1, 0.62, 0.18, 1),
            3: (0.85, 0.35, 1.0, 1),
        }.get(wave_no, (0.4, 0.9, 1.0, 1))
        self.boss_status_label.text = (
            f"CARBON BARON  //  WAVE {wave_no}/3  //  ARMOR {max(0, self.boss_hp)}"
        )
        self.boss_status_label.opacity = 1
        Animation.cancel_all(self.boss_portrait)
        self.boss_portrait.opacity = 0
        Animation(opacity=1, duration=0.25, t="out_quad").start(self.boss_portrait)

        sides = {
            placement.side: placement.item_id
            for placement in self.grid.boss_items.values()
            if placement.wave == wave_no
        }
        self.boss_choices_label.text = (
            f"LEFT: {sides.get('left', '?')}  |  RIGHT: {sides.get('right', '?')}"
        )

    def pause_game(self):
        """Pause: unschedule game loop, show overlay, sync sound button."""
        self.controller.pause()
        if self.game_event:
            self.game_event.cancel()
            self.game_event = None
        self.pause_overlay.opacity = 1
        self.pause_overlay.disabled = False
        self.pause_overlay.sync_sound_button()
        AudioManager().play_sfx("click")

    def resume_game(self):
        """Resume: hide overlay, re-schedule game loop."""
        self.controller.resume()
        self.pause_overlay.opacity = 0
        self.pause_overlay.disabled = True
        if not self.game_event:
            self.game_event = Clock.schedule_interval(self.update, 1.0 / TARGET_FPS)
        AudioManager().play_sfx("click")

    def restart_game(self):
        """Full restart: clear grid, reset scores/gems, generate fresh 4x4 platform."""
        AudioManager().play_sfx("click")
        self._start_new_session()
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
        self.boss_wall_label.text = ""
        self.boss_choices_label.text = ""
        self.boss_status_label.text = ""
        self.boss_status_label.opacity = 0
        self.boss_portrait.opacity = 0
        self.checkpoint_label.opacity = 0
        self.respawn_overlay.disabled = True
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
        elif keycode[1] == "spacebar" and self.inventory.has_item(ItemType.ECO_SEED):
            if self.controller.use_eco_seed():
                eco_seed = load_difficulty().get("eco_seed", {})
                if eco_seed.get("repairs_blocks", False):
                    for (col, row), tile in self.grid.path_set.items():
                        if abs(col - self.penguin.col) <= 1 and abs(row - self.penguin.row) <= 1:
                            tile.state = "normal"
                            tile.trigger_timer = 1.2
                            tile.fall_velocity = 0.0
                self._update_inventory_hud()
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
