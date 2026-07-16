from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from core.audio import AudioManager
from core.database import DatabaseManager
from core.logger import logger
from core.shop_catalog import ShopItemState, load_shop_catalog, resolve_item_state
from core.state import StateManager
from ui.components import HoverButton, ShopCard
from ui.responsive import compute_layout, grid_columns, is_compact

KENNEY_FONT = "assets/Component_UI/Font/Kenney Future.ttf"
BUTTON_NORMAL = "assets/Component_UI/PNG/Blue/Default/button_rectangle_depth_flat.png"
BUTTON_DOWN = "assets/Component_UI/PNG/Blue/Default/button_rectangle_flat.png"

# Below this available width, two 's cards would be squeezed under a
# readable minimum — the catalog grid falls back to a single column instead.
_MIN_CARD_WIDTH_DP = 240.0


class ShopScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._busy = False
        # Real value resolved in on_enter (needs the DB, not available this
        # early); only used as a display-safe default if update_balance_label
        # is ever called before the first on_enter.
        self.player_name = "Penguin"
        self.cards: dict[str, ShopCard] = {}

        self.root_layout = BoxLayout(orientation="vertical", size_hint=(1, 1))
        self.add_widget(self.root_layout)

        self.header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56))
        self.title_label = Label(
            text="SHOP",
            font_name=KENNEY_FONT,
            font_size="30sp",
            bold=True,
            size_hint_x=0.6,
            halign="left",
            valign="middle",
        )
        self.title_label.bind(size=lambda inst, _v: setattr(inst, "text_size", inst.size))

        gem_box = BoxLayout(orientation="horizontal", size_hint_x=0.4, spacing=dp(8))
        gem_tex = CoreImage("assets/Gem/Coin_Gems/spr_coin_strip4.png").texture.get_region(
            0, 0, 16, 16
        )
        self.gem_icon = Image(texture=gem_tex, size_hint=(None, None), size=(dp(28), dp(28)))
        self.gem_label = Label(
            text="GEMS: --",
            font_name=KENNEY_FONT,
            font_size="20sp",
            color=(0.2, 0.8, 1, 1),
            halign="right",
            valign="middle",
        )
        self.gem_label.bind(size=lambda inst, _v: setattr(inst, "text_size", inst.size))
        gem_box.add_widget(BoxLayout())  # spacer — pushes icon+label to the right edge
        gem_box.add_widget(self.gem_icon)
        gem_box.add_widget(self.gem_label)

        self.header.add_widget(self.title_label)
        self.header.add_widget(gem_box)
        self.root_layout.add_widget(self.header)

        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.grid = GridLayout(cols=2, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.scroll.add_widget(self.grid)
        self.root_layout.add_widget(self.scroll)

        self.back_button = HoverButton(
            text="BACK",
            font_name=KENNEY_FONT,
            font_size="18sp",
            size_hint=(1, None),
            height=dp(52),
            background_normal=BUTTON_NORMAL,
            background_down=BUTTON_DOWN,
            border=(10, 10, 10, 10),
        )
        self.back_button.bind(on_release=lambda _instance: self.go_back())
        self.root_layout.add_widget(self.back_button)

        for skin in load_shop_catalog().skins:
            card = ShopCard(skin=skin)
            card.bind(on_action=self._make_buy_handler(skin.id))
            self.cards[skin.id] = card
            self.grid.add_widget(card)

        # ShopScreen is constructed once and lives for the app's lifetime
        # (main.py adds exactly one instance to the ScreenManager) — bind
        # once here, same as HowToPlayOverlay, never unbind.
        Window.bind(size=self._apply_responsive_layout)
        self._apply_responsive_layout()

    def _make_buy_handler(self, skin_id: str):
        return lambda _instance: self.buy_item(skin_id)

    def _apply_responsive_layout(self, *_args):
        layout = compute_layout(Window.width, Window.height)
        compact = is_compact(layout.breakpoint)
        insets = layout.safe_area

        padding_h = dp(16) if compact else dp(48)
        padding_v = dp(12) if compact else dp(32)
        self.root_layout.padding = [
            padding_h + insets.left,
            padding_v + insets.top,
            padding_h + insets.right,
            padding_v + insets.bottom,
        ]
        self.root_layout.spacing = dp(10) if compact else dp(18)

        self.header.height = dp(48) * layout.scale
        self.title_label.font_size = f"{30 * layout.scale:.0f}sp"
        self.gem_label.font_size = f"{20 * layout.scale:.0f}sp"
        self.gem_icon.size = (dp(28) * layout.scale, dp(28) * layout.scale)

        grid_spacing = dp(12) if compact else dp(20)
        self.grid.spacing = (grid_spacing, grid_spacing)
        self.grid.padding = [dp(4), dp(4), dp(4), dp(4)]

        available_width = max(
            Window.width - self.root_layout.padding[0] - self.root_layout.padding[2], 1.0
        )
        # Catalog only ever needs up to 2 columns worth of breathing room —
        # clamp so a very wide desktop window doesn't stretch into 3+ tiny
        # columns instead of 2 comfortably-sized ones.
        self.grid.cols = min(
            2,
            grid_columns(
                available_width, min_cell_width_dp=_MIN_CARD_WIDTH_DP, spacing_dp=grid_spacing
            ),
        )

        for card in self.cards.values():
            card.apply_scale(layout.scale)

        self.back_button.height = max(dp(44), dp(52) * layout.scale)

    def on_enter(self):
        logger.info("เข้าสู่หน้าจอ Shop")
        # Single fallback point (core/database.py.get_last_player_name) —
        # never re-hardcode "Penguin" here, that duplication is exactly what
        # let Shop drift from History/GameOver's player resolution before.
        self.player_name = DatabaseManager().get_last_player_name()
        self._busy = False
        self.update_balance_label()

    def update_balance_label(self):
        db = DatabaseManager()
        catalog = load_shop_catalog()
        balance = db.get_gem_balance(self.player_name)
        self.gem_label.text = f"GEMS: {balance}"

        equipped_id = db.get_equipped_skin(self.player_name)
        for skin in catalog.skins:
            card = self.cards.get(skin.id)
            if card is None:
                continue
            owned = db.is_skin_owned(self.player_name, skin.id)
            state = resolve_item_state(
                skin, owned=owned, equipped_id=equipped_id, gem_balance=balance
            )
            card.apply_state(state)

    def buy_item(self, skin_id: str):
        # Guards a real risk (two on_release events landing in back-to-back
        # frames before the first purchase re-renders card state) even though
        # purchase_skin() is itself atomic/idempotent at the DB layer — this
        # only prevents redundant work/sfx, correctness never depends on it.
        if self._busy:
            return

        db = DatabaseManager()
        catalog = load_shop_catalog()
        skin = catalog.get(skin_id)
        if skin is None:
            logger.warning(f"ไม่พบสกิน {skin_id!r} ใน shop.json")
            return

        self._busy = True
        try:
            balance = db.get_gem_balance(self.player_name)
            equipped_id = db.get_equipped_skin(self.player_name)
            owned = db.is_skin_owned(self.player_name, skin_id)
            state = resolve_item_state(
                skin, owned=owned, equipped_id=equipped_id, gem_balance=balance
            )

            if state is ShopItemState.EQUIP:
                db.set_equipped_skin(self.player_name, skin_id)
                StateManager().selected_skin = skin_id
                AudioManager().play_sfx("tab")
                logger.info(f"สวมใส่สกิน {skin_id}")
            elif state is ShopItemState.BUY:
                if db.purchase_skin(self.player_name, skin_id, skin.price):
                    db.set_equipped_skin(self.player_name, skin_id)
                    StateManager().selected_skin = skin_id
                    AudioManager().play_sfx("tab")
                    logger.info(f"ซื้อสกิน {skin_id} สำเร็จ! หัก {skin.price} Gems")
                else:
                    logger.warning("Gems ไม่พอ!")
                    AudioManager().play_sfx("down")
            else:
                # LOCKED (can't afford) or EQUIPPED (already active) — no
                # state-changing action, just an audible "can't do that".
                AudioManager().play_sfx("down")
        finally:
            self._busy = False

        self.update_balance_label()

    def go_back(self):
        AudioManager().play_sfx("click")
        Clock.schedule_once(lambda dt: self._go_menu(), 0.2)

    def _go_menu(self):
        self.manager.current = "menu"
