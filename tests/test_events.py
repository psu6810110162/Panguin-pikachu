import pytest

from core.events import CollectEvent, RespawnEvent, event_from_dict, event_to_dict


def test_event_to_dict_includes_the_discriminator():
    event = CollectEvent(timestamp=1.0, distance_m=50, item_type="gem", col=3, row=1, value=1)
    data = event_to_dict(event)
    assert data["event_type"] == "collect"
    assert data["item_type"] == "gem"


def test_event_from_dict_reconstructs_the_right_type():
    data = {
        "event_type": "respawn",
        "timestamp": 2.0,
        "distance_m": 120,
        "checkpoint_col": 3,
        "checkpoint_row": 0,
        "respawn_count": 1,
        "score_penalty": 0.1,
    }
    event = event_from_dict(data)
    assert isinstance(event, RespawnEvent)
    assert event.respawn_count == 1


def test_event_round_trips_through_dict():
    original = CollectEvent(
        timestamp=1.0, distance_m=50, item_type="scientific_item", col=2, row=2, value=1
    )
    restored = event_from_dict(event_to_dict(original))
    assert restored == original


def test_event_from_dict_rejects_unknown_event_type():
    with pytest.raises(ValueError, match="not_a_real_event"):
        event_from_dict({"event_type": "not_a_real_event"})
