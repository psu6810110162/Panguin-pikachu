import pytest

from core.shop_catalog import (
    ShopItemState,
    action_label,
    is_action_enabled,
    load_shop_catalog,
    resolve_item_state,
)


def test_load_shop_catalog_has_exactly_one_default_skin():
    catalog = load_shop_catalog()
    defaults = [skin for skin in catalog.skins if skin.is_default]
    assert len(defaults) == 1
    assert catalog.default_skin_id == defaults[0].id


def test_load_shop_catalog_ids_are_unique():
    catalog = load_shop_catalog()
    ids = [skin.id for skin in catalog.skins]
    assert len(ids) == len(set(ids))


def test_load_shop_catalog_prices_are_nonnegative():
    catalog = load_shop_catalog()
    for skin in catalog.skins:
        assert skin.price >= 0


def test_load_shop_catalog_preview_sheet_paths_exist_on_disk():
    from core.shop_catalog import PROJECT_ROOT

    catalog = load_shop_catalog()
    for skin in catalog.skins:
        assert (PROJECT_ROOT / skin.preview_sheet).exists(), skin.preview_sheet


def test_default_skin_is_free():
    catalog = load_shop_catalog()
    default_skin = catalog.get(catalog.default_skin_id)
    assert default_skin is not None
    assert default_skin.price == 0


def test_catalog_get_returns_none_for_unknown_id():
    catalog = load_shop_catalog()
    assert catalog.get("Not A Real Skin") is None


def test_penguin_skin_assets_cover_every_catalog_skin():
    """game.penguin.Penguin.SKIN_ASSETS keys must match shop.json ids exactly —
    otherwise equipping a purchased skin silently falls back to the default."""
    from game.penguin import Penguin

    catalog = load_shop_catalog()
    penguin = Penguin()
    for skin in catalog.skins:
        assert skin.id in penguin.SKIN_ASSETS


@pytest.mark.parametrize(
    ("owned", "equipped_id", "gem_balance", "price", "expected"),
    [
        (True, "Mask Dude", 0, 10, ShopItemState.EQUIPPED),
        (True, "Ninja Frog", 0, 10, ShopItemState.EQUIP),
        (False, None, 10, 10, ShopItemState.BUY),
        (False, None, 9, 10, ShopItemState.LOCKED),
        (False, None, 0, 0, ShopItemState.BUY),
    ],
)
def test_resolve_item_state_matrix(owned, equipped_id, gem_balance, price, expected):
    catalog = load_shop_catalog()
    skin = (
        next(s for s in catalog.skins if s.price == price)
        if price
        else catalog.get(catalog.default_skin_id)
    )
    assert skin is not None
    state = resolve_item_state(skin, owned=owned, equipped_id=equipped_id, gem_balance=gem_balance)
    assert state is expected


def test_locked_and_equipped_have_no_action_but_buy_and_equip_do():
    assert is_action_enabled(ShopItemState.BUY) is True
    assert is_action_enabled(ShopItemState.EQUIP) is True
    assert is_action_enabled(ShopItemState.LOCKED) is False
    assert is_action_enabled(ShopItemState.EQUIPPED) is False


def test_action_label_reflects_price_and_state():
    catalog = load_shop_catalog()
    priced_skin = next(s for s in catalog.skins if s.price > 0)

    assert action_label(priced_skin, ShopItemState.BUY) == f"BUY {priced_skin.price}"
    assert action_label(priced_skin, ShopItemState.LOCKED) == f"LOCKED {priced_skin.price}"
    assert action_label(priced_skin, ShopItemState.EQUIP) == "EQUIP"
    assert action_label(priced_skin, ShopItemState.EQUIPPED) == "EQUIPPED"
