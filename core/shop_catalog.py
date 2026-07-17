"""Loader + pure state matrix for balance/v1/shop.json — the character-skin shop.

Content (skin id, display name, price, preview sprite, default flag) lives in
JSON, the single source of truth — a price change or new skin never touches
this module or screens/shop.py's rendering logic. ``skin.id`` must match
``game.penguin.Penguin.SKIN_ASSETS`` keys exactly: it flows straight into
``players.equipped_skin`` (core/database.py) and ``StateManager.selected_skin``
(core/state.py) with no translation layer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path

BALANCE_DIR = Path(__file__).resolve().parent.parent / "balance" / "v1"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class SkinDefinition:
    id: str
    display_name: str
    price: int
    preview_sheet: str
    is_default: bool


@dataclass(frozen=True)
class ShopCatalog:
    skins: tuple[SkinDefinition, ...]

    def get(self, skin_id: str) -> SkinDefinition | None:
        for skin in self.skins:
            if skin.id == skin_id:
                return skin
        return None

    @property
    def default_skin_id(self) -> str:
        for skin in self.skins:
            if skin.is_default:
                return skin.id
        # load_shop_catalog() already validates exactly-one-default before
        # this object is ever constructed — reaching here means that
        # invariant was bypassed (e.g. hand-built ShopCatalog in a test).
        raise ValueError("ShopCatalog has no default skin")


class ShopItemState(Enum):
    """Card state per docs/adr plan §7 — see resolve_item_state for the matrix."""

    LOCKED = "locked"
    BUY = "buy"
    EQUIP = "equip"
    EQUIPPED = "equipped"


def resolve_item_state(
    skin: SkinDefinition, *, owned: bool, equipped_id: str | None, gem_balance: int
) -> ShopItemState:
    """Pure card-state matrix — never touches the DB, only decides *what to show*.

    - owned and currently equipped -> EQUIPPED (no action)
    - owned but not equipped -> EQUIP (switch to it)
    - not owned, affordable -> BUY
    - not owned, not affordable -> LOCKED (disabled, shows price)
    """
    if owned:
        return ShopItemState.EQUIPPED if skin.id == equipped_id else ShopItemState.EQUIP
    return ShopItemState.BUY if gem_balance >= skin.price else ShopItemState.LOCKED


def is_action_enabled(state: ShopItemState) -> bool:
    """LOCKED and EQUIPPED are terminal display states — no tap action."""
    return state in (ShopItemState.BUY, ShopItemState.EQUIP)


def action_label(skin: SkinDefinition, state: ShopItemState) -> str:
    if state is ShopItemState.EQUIPPED:
        return "EQUIPPED"
    if state is ShopItemState.EQUIP:
        return "EQUIP"
    if state is ShopItemState.BUY:
        return f"BUY {skin.price}"
    return f"LOCKED {skin.price}"


def _require_str(entry: dict[str, object], key: str, *, skin_id: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"shop skin {skin_id!r} requires non-empty {key!r}")
    return value


@lru_cache(maxsize=1)
def load_shop_catalog() -> ShopCatalog:
    raw = json.loads((BALANCE_DIR / "shop.json").read_text(encoding="utf-8"))
    if raw.get("version") != 1:
        raise ValueError("shop.json version must be 1")
    entries = raw.get("skins")
    if not isinstance(entries, list) or not entries:
        raise ValueError("shop.json requires a non-empty skins list")

    skins: list[SkinDefinition] = []
    seen_ids: set[str] = set()
    default_count = 0
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("shop.json skin entry must be an object")
        skin_id = entry.get("id")
        if not isinstance(skin_id, str) or not skin_id.strip():
            raise ValueError("shop.json skin requires a non-empty id")
        if skin_id in seen_ids:
            raise ValueError(f"Duplicate shop skin id {skin_id!r}")
        seen_ids.add(skin_id)

        display_name = _require_str(entry, "display_name", skin_id=skin_id)
        preview_sheet = _require_str(entry, "preview_sheet", skin_id=skin_id)
        if not (PROJECT_ROOT / preview_sheet).exists():
            raise ValueError(f"shop skin {skin_id!r} preview_sheet not found: {preview_sheet}")

        price = entry.get("price")
        if not isinstance(price, int) or isinstance(price, bool) or price < 0:
            raise ValueError(f"shop skin {skin_id!r} requires a nonnegative integer price")

        is_default = bool(entry.get("is_default", False))
        if is_default:
            default_count += 1

        skins.append(
            SkinDefinition(
                id=skin_id,
                display_name=display_name,
                price=price,
                preview_sheet=preview_sheet,
                is_default=is_default,
            )
        )

    if default_count != 1:
        raise ValueError(f"shop.json must have exactly one default skin, found {default_count}")

    return ShopCatalog(skins=tuple(skins))
