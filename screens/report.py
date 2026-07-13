"""Systemic Report Card — renders the DAG projection from core/scoring/dag.py.

This screen is a pure renderer: all the "did the player understand cause and
effect" logic lives in core/scoring/dag.py (GraphProjection) and
core/scoring/stealth.py (Net Impact Score + rank) — see docs/adr/011.
On enter, it reads the current gameplay session's event log, builds the
projection, and animates it in one edge at a time (GAME_DESIGN.md §5.2:
"วาดแผนภาพความสัมพันธ์ ... ขึ้นมาทีละเส้น").

Node layout is a simple circle (nodes have no x/y in balance/v1/dag.json —
positions are computed here, not authored data) — good enough for a 22-node/
13-edge summary graph without needing a real force-directed layout engine.

Incorrect edges also get their tooltip listed below the graph as plain text,
rather than an on-hover tooltip anchored to the line itself — hit-testing
proximity to line segments would add real complexity for a results screen
that's read once at the end of a run.
"""

import math

from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from core.audio import AudioManager
from core.logger import logger
from core.scoring import stealth
from core.scoring.dag import GraphProjection, build_projection
from ui.components import HoverButton

_STATUS_COLORS = {
    "correct": (0.25, 0.85, 0.4, 1),
    "incorrect": (0.95, 0.3, 0.3, 1),
    "unplayed": (0.45, 0.45, 0.5, 0.4),
}


class DAGGraphWidget(Widget):
    """Canvas renderer for one GraphProjection — nodes on a circle, edges revealed
    incrementally via set_revealed()."""

    def __init__(self, projection: GraphProjection | None = None, **kwargs):
        super().__init__(**kwargs)
        self.projection = projection or build_projection([])
        self.revealed = 0
        self._label_cache: dict[tuple[str, tuple[float, float, float, float]], object] = {}
        self.bind(pos=self._redraw, size=self._redraw)

    def update_projection(self, projection: GraphProjection) -> None:
        self.projection = projection
        self.revealed = 0
        self._redraw()

    def set_revealed(self, count: int) -> None:
        self.revealed = count
        self._redraw()

    def _node_xy(self, index: int, total: int) -> tuple[float, float]:
        angle = 2 * math.pi * index / total - math.pi / 2
        radius = min(self.width, self.height) * 0.42
        cx, cy = self.center
        return cx + radius * math.cos(angle), cy + radius * math.sin(angle)

    def _label_texture(self, text: str, color: tuple[float, float, float, float]):
        key = (text, color)
        if key not in self._label_cache:
            core_label = CoreLabel(text=text, font_size=13, color=color)
            core_label.refresh()
            self._label_cache[key] = core_label.texture
        return self._label_cache[key]

    def _draw_arrowhead(self, x1: float, y1: float, x2: float, y2: float) -> None:
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy) or 1.0
        ux, uy = dx / dist, dy / dist
        tip_x, tip_y = x2 - ux * 12, y2 - uy * 12
        back_x, back_y = tip_x - ux * 8, tip_y - uy * 8
        px, py = -uy, ux  # perpendicular unit vector
        left = (back_x + px * 4, back_y + py * 4)
        right = (back_x - px * 4, back_y - py * 4)
        Line(points=[left[0], left[1], tip_x, tip_y, right[0], right[1]], width=1.6)

    def _redraw(self, *_args) -> None:
        self.canvas.clear()
        if not self.projection.nodes or self.width <= 0 or self.height <= 0:
            return

        node_ids = [n.id for n in self.projection.nodes]
        total = len(node_ids)
        positions = {node_id: self._node_xy(i, total) for i, node_id in enumerate(node_ids)}

        with self.canvas:
            for edge in self.projection.edges[: self.revealed]:
                if edge.from_node not in positions or edge.to_node not in positions:
                    continue
                x1, y1 = positions[edge.from_node]
                x2, y2 = positions[edge.to_node]
                Color(*_STATUS_COLORS[edge.status])
                Line(points=[x1, y1, x2, y2], width=1.8)
                self._draw_arrowhead(x1, y1, x2, y2)

            for node in self.projection.nodes:
                x, y = positions[node.id]
                Color(0.15, 0.18, 0.24, 1)
                Ellipse(pos=(x - 5, y - 5), size=(10, 10))
                Color(1, 1, 1, 1)
                tex = self._label_texture(node.label, (1, 1, 1, 1))
                Rectangle(texture=tex, pos=(x - tex.width / 2, y - 20), size=tex.size)


class ReportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reveal_event = None
        self._revealed = 0
        self.projection = build_projection([])

        self.dag_widget = DAGGraphWidget(size_hint=(1, 1))
        self.add_widget(self.dag_widget)

        header = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=140,
            pos_hint={"top": 1},
            padding=[20, 16, 20, 8],
            spacing=4,
        )
        self.title_label = Label(
            text="SYSTEMIC REPORT CARD",
            font_size="30sp",
            bold=True,
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(0.6, 0.9, 1.0, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 1),
            size_hint_y=None,
            height=44,
        )
        self.summary_label = Label(
            text="",
            font_size="20sp",
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(1, 1, 1, 0.95),
            size_hint_y=None,
            height=34,
        )
        self.edge_count_label = Label(
            text="",
            font_size="15sp",
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            color=(1, 1, 1, 0.75),
            size_hint_y=None,
            height=26,
        )
        header.add_widget(self.title_label)
        header.add_widget(self.summary_label)
        header.add_widget(self.edge_count_label)
        self.add_widget(header)

        self.tooltip_scroll = ScrollView(
            size_hint=(0.9, 0.28),
            pos_hint={"center_x": 0.5, "y": 0.14},
        )
        self.tooltip_box = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=4, padding=[10, 6, 10, 6]
        )
        self.tooltip_box.bind(minimum_height=self.tooltip_box.setter("height"))
        self.tooltip_scroll.add_widget(self.tooltip_box)
        self.add_widget(self.tooltip_scroll)

        button_row = BoxLayout(
            orientation="horizontal",
            size_hint=(0.6, None),
            height=60,
            spacing=20,
            pos_hint={"center_x": 0.5, "y": 0.02},
        )
        btn_again = HoverButton(
            text="RUN AGAIN",
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            font_size="20sp",
            background_normal="assets/Component_UI/PNG/Blue/Default/button_rectangle_depth_gradient.png",
            background_down="assets/Component_UI/PNG/Blue/Default/button_rectangle_gradient.png",
            border=(10, 10, 10, 10),
        )
        btn_again.bind(on_release=lambda _: self.run_again())
        btn_home = HoverButton(
            text="HOME",
            font_name="assets/Component_UI/Font/Kenney Future.ttf",
            font_size="20sp",
            background_normal="assets/Component_UI/PNG/Blue/Default/button_rectangle_depth_flat.png",
            background_down="assets/Component_UI/PNG/Blue/Default/button_rectangle_flat.png",
            border=(10, 10, 10, 10),
        )
        btn_home.bind(on_release=lambda _: self.go_home())
        button_row.add_widget(btn_again)
        button_row.add_widget(btn_home)
        self.add_widget(button_row)

    def on_enter(self) -> None:
        logger.info("เข้าสู่หน้า Report Card")
        events = self._current_run_events()

        self.projection = build_projection(events)
        self.dag_widget.update_projection(self.projection)

        run_c = stealth.run_reduction_c(events)
        cog_c = stealth.cognitive_score_c(events)
        net_c = stealth.net_impact_score_c(events)
        rank = stealth.rank_for(net_c)

        rank_text = rank if rank is not None else "-"
        self.summary_label.text = f"อุณหภูมิที่กอบกู้ได้: {net_c:.1f}°C  |  Rank: {rank_text}"
        self.edge_count_label.text = (
            f"ถูก {self.projection.correct_count}/13  ·  "
            f"ผิด {self.projection.incorrect_count}  ·  "
            f"ยังไม่เจอ {self.projection.unplayed_count}  "
            f"(วิ่ง {run_c:.1f}°C + บอส {cog_c:.1f}°C)"
        )

        self._populate_tooltips()
        self._start_reveal_animation()

    def on_leave(self) -> None:
        if self._reveal_event:
            self._reveal_event.cancel()
            self._reveal_event = None

    def _current_run_events(self) -> list:
        """RunRecord events ของรอบเล่นล่าสุด — คืน [] ถ้าเรียกก่อนมี session (เช่น เปิดหน้านี้ตรง ๆ ตอน dev)"""
        try:
            gameplay = self.manager.get_screen("gameplay")
            return list(gameplay.session.run_record.events)
        except Exception as e:  # noqa: BLE001 — ยอมรับได้: หน้าจอนี้ต้อง render ได้แม้ session ยังไม่มี
            logger.error(f"ไม่พบ session ของ gameplay ตอนเข้า Report Card: {e}")
            return []

    def _populate_tooltips(self) -> None:
        self.tooltip_box.clear_widgets()
        incorrect = [e for e in self.projection.edges if e.status == "incorrect" and e.tooltip]
        if not incorrect:
            return
        for edge in incorrect:
            label = Label(
                text=f"[b]Decision {edge.decision}:[/b] {edge.tooltip}",
                markup=True,
                font_size="14sp",
                color=(1, 0.85, 0.85, 1),
                size_hint_y=None,
                halign="left",
                valign="top",
            )
            # wrap against the box's width only (height=None so Kivy computes
            # wrapped texture height), then grow the widget to fit — a fixed
            # height clips or overlaps long tooltips instead of wrapping cleanly
            label.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)))
            label.bind(texture_size=lambda inst, ts: setattr(inst, "height", ts[1] + 8))
            self.tooltip_box.add_widget(label)

    def _start_reveal_animation(self) -> None:
        if self._reveal_event:
            self._reveal_event.cancel()
        self._revealed = 0
        self._reveal_event = Clock.schedule_interval(self._reveal_step, 0.12)

    def _reveal_step(self, _dt: float) -> None:
        self._revealed += 1
        self.dag_widget.set_revealed(self._revealed)
        if self._revealed >= len(self.projection.edges) and self._reveal_event:
            self._reveal_event.cancel()
            self._reveal_event = None

    def run_again(self) -> None:
        AudioManager().play_sfx("click")
        Clock.schedule_once(lambda dt: setattr(self.manager, "current", "gameplay"), 0.2)

    def go_home(self) -> None:
        AudioManager().play_sfx("click")
        Clock.schedule_once(lambda dt: setattr(self.manager, "current", "menu"), 0.2)
