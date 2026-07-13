"""DAG projection — the Learning Analytics concern (ADR-011).

Turns the 13-decision event log (10 Y-Junction choices + 3 boss waves) into a
serializable graph projection: a node list plus an edge list, where each edge
carries a `status` ("correct" | "incorrect" | "unplayed") and a `tooltip`
(populated only when incorrect, per GAME_DESIGN.md §5.2 — the tooltip is the
answer key shown on a mistake, not shown otherwise).

This is domain data, not UI: build_projection() returns a plain, serializable
GraphProjection. screens/report.py (Kivy renderer) draws from it — it doesn't
compute anything — and a future server-side renderer could reuse the exact
same projection. Per ADR-012 build_projection() must be deterministic: the
same events always produce the same projection.

Edge decision -> source mapping (fixed by balance/v1/dag.json's own layout):
  decision 1-10 (phase="run")  -> zone 1-10 in balance/v1/junctions.json
  decision 11-13 (phase="boss") -> boss wave (decision - 10) in balance/v1/boss.json

Graph content (node labels, edge relationships, tooltips) lives in
balance/v1/dag.json — the single source of truth — never hardcoded here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from core.events import BossPhaseEvent, GameEvent, PolicyChoiceEvent
from core.junction_data import option_for_policy_id, parse_policy_id

BALANCE_DIR = Path(__file__).resolve().parent.parent.parent / "balance" / "v1"

EdgeStatus = Literal["correct", "incorrect", "unplayed"]
Phase = Literal["run", "boss"]


@dataclass(frozen=True)
class Node:
    id: str
    label: str


@dataclass(frozen=True)
class Edge:
    decision: int
    phase: Phase
    from_node: str
    to_node: str
    tooltip: str


@dataclass(frozen=True)
class GraphData:
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]


@dataclass(frozen=True)
class EdgeResult:
    """One evaluated edge, ready to render."""

    decision: int
    phase: Phase
    from_node: str
    to_node: str
    status: EdgeStatus
    tooltip: str | None  # populated only when status == "incorrect"


@dataclass(frozen=True)
class GraphProjection:
    nodes: tuple[Node, ...]
    edges: tuple[EdgeResult, ...]

    @property
    def correct_count(self) -> int:
        return sum(1 for e in self.edges if e.status == "correct")

    @property
    def incorrect_count(self) -> int:
        return sum(1 for e in self.edges if e.status == "incorrect")

    @property
    def unplayed_count(self) -> int:
        return sum(1 for e in self.edges if e.status == "unplayed")

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [{"id": n.id, "label": n.label} for n in self.nodes],
            "edges": [
                {
                    "decision": e.decision,
                    "phase": e.phase,
                    "from": e.from_node,
                    "to": e.to_node,
                    "status": e.status,
                    "tooltip": e.tooltip,
                }
                for e in self.edges
            ],
        }


@lru_cache(maxsize=1)
def load_graph_data() -> GraphData:
    """Read balance/v1/dag.json (cached — static content)."""
    raw = json.loads((BALANCE_DIR / "dag.json").read_text(encoding="utf-8"))
    nodes = tuple(Node(id=n["id"], label=n["label"]) for n in raw["nodes"])
    edges = tuple(
        Edge(
            decision=e["decision"],
            phase=e["phase"],
            from_node=e["from"],
            to_node=e["to"],
            tooltip=e["tooltip"],
        )
        for e in raw["edges"]
    )
    return GraphData(nodes=nodes, edges=edges)


def _zone_choice_status(events: list[GameEvent], zone: int) -> EdgeStatus | None:
    """None ถ้ายังไม่มี PolicyChoiceEvent ของโซนนี้เลย (ยังไม่ถึง หรือรอบเล่นจบก่อนถึง)"""
    for e in events:
        if isinstance(e, PolicyChoiceEvent):
            event_zone, _ = parse_policy_id(e.policy_id)
            if event_zone == zone:
                return "correct" if option_for_policy_id(e.policy_id).systemic else "incorrect"
    return None


def _boss_wave_status(events: list[GameEvent], wave: int) -> EdgeStatus | None:
    """None ถ้ายังไม่มี BossPhaseEvent ของเวฟนี้เลย"""
    for e in events:
        if isinstance(e, BossPhaseEvent) and e.phase == wave:
            if e.outcome == "damage_dealt":
                return "correct"
            if e.outcome == "damaged":
                return "incorrect"
    return None


def build_projection(events: list[GameEvent], *, graph: GraphData | None = None) -> GraphProjection:
    """สร้าง GraphProjection จาก event log — event log เดียวกันต้องได้ projection เดิมเสมอ (ADR-012)"""
    data = graph or load_graph_data()
    results = []
    for edge in data.edges:
        if edge.phase == "run":
            status = _zone_choice_status(events, zone=edge.decision)
        else:
            status = _boss_wave_status(events, wave=edge.decision - 10)

        resolved: EdgeStatus = status if status is not None else "unplayed"
        results.append(
            EdgeResult(
                decision=edge.decision,
                phase=edge.phase,
                from_node=edge.from_node,
                to_node=edge.to_node,
                status=resolved,
                tooltip=edge.tooltip if resolved == "incorrect" else None,
            )
        )
    return GraphProjection(nodes=data.nodes, edges=tuple(results))
