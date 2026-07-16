"""Reusable, responsive How to Play modal for menu and gameplay."""

from __future__ import annotations

from collections.abc import Callable

from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from core.how_to_play import HelpRow, HowToPlayModel, HowToPlayPager, load_how_to_play
from ui.components import HoverButton

KENNEY_FONT = "assets/Component_UI/Font/Kenney Future.ttf"
THAI_FONT = "assets/Component_UI/Font/NotoSansThai-Regular.ttf"
BUTTON_NORMAL = "assets/Component_UI/PNG/Blue/Default/button_rectangle_depth_flat.png"
BUTTON_DOWN = "assets/Component_UI/PNG/Blue/Default/button_rectangle_flat.png"


class HowToPlayOverlay(FloatLayout):
    """Paginated modal that renders a pure ``HowToPlayModel``.

    The parent owns whether opening help should pause the simulation; this
    component only owns rendering, page navigation, and touch absorption.
    """

    is_open = BooleanProperty(False)

    def __init__(
        self,
        *,
        model: HowToPlayModel | None = None,
        on_close: Callable[[], None] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.model = model or load_how_to_play()
        self.pager = HowToPlayPager(self.model.pages)
        self.on_close_callback = on_close
        self.opacity = 0
        self.disabled = True

        with self.canvas.before:
            Color(0.01, 0.03, 0.08, 0.82)
            self._dim = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._redraw_dim, size=self._redraw_dim)

        self.panel = BoxLayout(
            orientation="vertical",
            spacing=12,
            padding=[28, 22, 28, 20],
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        with self.panel.canvas.before:
            Color(0.03, 0.08, 0.16, 0.98)
            self._panel_bg = RoundedRectangle(pos=self.panel.pos, size=self.panel.size, radius=[22])
            Color(0.25, 0.75, 1.0, 0.7)
            self._panel_border = Line(
                rounded_rectangle=(
                    self.panel.x,
                    self.panel.y,
                    self.panel.width,
                    self.panel.height,
                    22,
                ),
                width=1.5,
            )
        self.panel.bind(pos=self._redraw_panel, size=self._redraw_panel)

        self.title_label = Label(
            text=self.model.title.upper(),
            font_name=KENNEY_FONT,
            font_size="25sp",
            bold=True,
            color=(0.65, 0.9, 1.0, 1),
            size_hint_y=None,
            height=36,
            halign="center",
            valign="middle",
        )
        self.page_title_label = Label(
            font_name=THAI_FONT,
            font_size="22sp",
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=42,
            halign="center",
            valign="middle",
        )
        self.panel.add_widget(self.title_label)
        self.panel.add_widget(self.page_title_label)

        self.scroll = ScrollView(bar_width=8, do_scroll_x=False)
        self.body = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=[5, 4, 5, 4],
            size_hint_y=None,
        )
        self.body.bind(minimum_height=self.body.setter("height"))
        self.scroll.add_widget(self.body)
        self.panel.add_widget(self.scroll)

        footer = BoxLayout(orientation="horizontal", size_hint_y=None, height=48, spacing=12)
        self.previous_button = self._button("PREV")
        self.previous_button.bind(on_release=lambda _: self.previous_page())
        self.indicator_label = Label(
            font_name=KENNEY_FONT,
            font_size="15sp",
            color=(0.85, 0.92, 1.0, 1),
            size_hint_x=0.35,
            halign="center",
            valign="middle",
        )
        self.next_button = self._button("NEXT")
        self.next_button.bind(on_release=lambda _: self.next_page())
        self.close_button = self._button("CLOSE")
        self.close_button.bind(on_release=lambda _: self.close())
        footer.add_widget(self.previous_button)
        footer.add_widget(self.indicator_label)
        footer.add_widget(self.next_button)
        footer.add_widget(self.close_button)
        self.panel.add_widget(footer)

        self.add_widget(self.panel)
        Window.bind(size=self._resize)
        self._resize()
        self._render_page()

    def _button(self, text: str) -> HoverButton:
        return HoverButton(
            text=text,
            font_name=KENNEY_FONT,
            font_size="14sp",
            background_normal=BUTTON_NORMAL,
            background_down=BUTTON_DOWN,
            border=(10, 10, 10, 10),
        )

    def _resize(self, *_args: object) -> None:
        self.panel.size = (
            min(Window.width * 0.90, 1020),
            min(Window.height * 0.86, 780),
        )
        content_width = max(self.panel.width - 66, 1)
        self.title_label.text_size = (content_width, None)
        self.page_title_label.text_size = (content_width, None)
        self._render_page()

    def _redraw_dim(self, *_args: object) -> None:
        self._dim.pos = self.pos
        self._dim.size = self.size

    def _redraw_panel(self, *_args: object) -> None:
        self._panel_bg.pos = self.panel.pos
        self._panel_bg.size = self.panel.size
        self._panel_border.rounded_rectangle = (
            self.panel.x,
            self.panel.y,
            self.panel.width,
            self.panel.height,
            22,
        )

    def open(self, page_index: int = 0) -> None:
        self.pager.go_to(page_index)
        self.is_open = True
        self.opacity = 1
        self.disabled = False
        self._render_page()

    def close(self) -> None:
        if not self.is_open:
            return
        self.is_open = False
        self.opacity = 0
        self.disabled = True
        if self.on_close_callback:
            self.on_close_callback()

    def next_page(self) -> None:
        if self.pager.next_page():
            self._render_page()

    def previous_page(self) -> None:
        if self.pager.previous_page():
            self._render_page()

    def _render_page(self) -> None:
        page = self.pager.current
        self.page_title_label.text = page.title
        self.indicator_label.text = self.pager.indicator
        self.previous_button.disabled = not self.pager.can_go_previous
        self.next_button.disabled = not self.pager.can_go_next
        self.body.clear_widgets()

        if page.body:
            self.body.add_widget(self._body_label(page.body))
        for row in page.rows:
            self.body.add_widget(self._row_card(row))
        self.scroll.scroll_y = 1

    def _body_label(self, text: str) -> Label:
        label = Label(
            text=text,
            font_name=THAI_FONT,
            font_size="17sp",
            color=(0.92, 0.96, 1.0, 1),
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        label.bind(texture_size=label.setter("size"))
        label.text_size = (max(self.panel.width - 76, 1), None)
        return label

    def _row_card(self, row: HelpRow) -> BoxLayout:
        card = BoxLayout(
            orientation="vertical",
            spacing=3,
            padding=[12, 9, 12, 9],
            size_hint_y=None,
        )
        with card.canvas.before:
            Color(0.02, 0.05, 0.12, 0.92)
            panel = RoundedRectangle(pos=card.pos, size=card.size, radius=[12])
            Color(0.25, 0.75, 1.0, 0.28)
            border = Line(
                rounded_rectangle=(card.x, card.y, card.width, card.height, 12),
                width=1.0,
            )

        def redraw(*_args: object) -> None:
            panel.pos = card.pos
            panel.size = card.size
            border.rounded_rectangle = (card.x, card.y, card.width, card.height, 12)

        card.bind(pos=redraw, size=redraw, minimum_height=card.setter("height"))
        text_width = max(self.panel.width - 104, 1)
        title = Label(
            text=row.title,
            font_name=THAI_FONT,
            font_size="17sp",
            bold=True,
            color=(0.5, 0.86, 1.0, 1),
            size_hint_y=None,
            halign="left",
            valign="top",
            text_size=(text_width, None),
        )
        title.bind(texture_size=title.setter("size"))
        card.add_widget(title)
        body = Label(
            text=row.body,
            font_name=THAI_FONT,
            font_size="15sp",
            color=(1, 1, 1, 0.96),
            size_hint_y=None,
            halign="left",
            valign="top",
            text_size=(text_width, None),
        )
        body.bind(texture_size=body.setter("size"))
        card.add_widget(body)
        if row.detail:
            detail = Label(
                text=row.detail,
                font_name=THAI_FONT,
                font_size="13sp",
                color=(0.72, 0.92, 0.72, 1),
                size_hint_y=None,
                halign="left",
                valign="top",
                text_size=(text_width, None),
            )
            detail.bind(texture_size=detail.setter("size"))
            card.add_widget(detail)
        return card

    def on_touch_down(self, touch: object) -> bool:
        if not self.is_open:
            return False
        super().on_touch_down(touch)
        return True

    def on_touch_move(self, touch: object) -> bool:
        if not self.is_open:
            return False
        super().on_touch_move(touch)
        return True

    def on_touch_up(self, touch: object) -> bool:
        if not self.is_open:
            return False
        super().on_touch_up(touch)
        return True
