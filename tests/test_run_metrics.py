from core.state import RunMetrics


def test_run_metrics_initialization():
    metrics = RunMetrics()
    assert metrics.heat_meter == 50.0  # From JSON or default
    assert metrics.capitalist_anger == 50.0
    assert metrics.hearts == 5
    assert not metrics.is_game_over
    assert not metrics.needs_respawn
    assert not metrics.is_invincible


def test_run_metrics_update_safe():
    metrics = RunMetrics(heat_meter=50.0, capitalist_anger=50.0)
    # 0 คือปลอดภัยที่สุด, ค่าไม่ลดต่ำกว่า 0
    metrics.update_meters(-100.0, -100.0)
    assert metrics.heat_meter == 0.0
    assert metrics.capitalist_anger == 0.0
    assert not metrics.is_game_over

    # อัปเดตค่าปกติ
    metrics.update_meters(50.5, 60.5)
    assert metrics.heat_meter == 50.5
    assert metrics.capitalist_anger == 60.5
    assert not metrics.is_game_over


def test_run_metrics_game_over_at_100():
    metrics = RunMetrics(heat_meter=50.0, capitalist_anger=50.0)
    # ถ้าค่าแตะ 100 แล้วพัง
    metrics.update_meters(50.0, 0.0)
    assert metrics.heat_meter == 100.0
    assert metrics.is_game_over


def test_run_metrics_game_over_anger_at_100():
    metrics = RunMetrics(heat_meter=50.0, capitalist_anger=50.0)
    metrics.update_meters(0.0, 150.0)
    assert metrics.capitalist_anger == 100.0  # clamped to 100
    assert metrics.is_game_over


def test_decrease_heart_flags():
    metrics = RunMetrics(hearts=5)
    metrics.decrease_heart()
    assert metrics.hearts == 4
    assert not metrics.is_game_over
    assert metrics.needs_respawn
    assert metrics.is_invincible

    # Test invincible frame prevents another decrease
    metrics.decrease_heart()
    assert metrics.hearts == 4


def test_heart_game_over():
    metrics = RunMetrics(hearts=5)
    for _ in range(5):
        metrics.is_invincible = False
        metrics.decrease_heart()
    assert metrics.hearts == 0
    assert metrics.is_game_over


def test_run_metrics_game_over_callback():
    triggered = False

    def cb():
        nonlocal triggered
        triggered = True

    metrics = RunMetrics(heat_meter=50.0, capitalist_anger=50.0, on_game_over=cb)
    metrics.update_meters(100.0, 0.0)
    assert metrics.is_game_over
    assert triggered


def test_increase_heart():
    metrics = RunMetrics(hearts=4)
    metrics.increase_heart()
    assert metrics.hearts == 5
    metrics.increase_heart()
    assert metrics.hearts == 5  # capped at 5


def test_respawn_seconds_loaded_from_difficulty():
    # balance/v1/difficulty.json: hearts.respawn_seconds = 3.0
    metrics = RunMetrics()
    assert metrics.respawn_seconds == 3.0


def test_decrease_heart_without_respawn_keeps_flags_clear():
    """โหมดบอส (ตอบผิด): เสียหัวใจตรง ๆ ห้ามตั้ง needs_respawn/is_invincible
    ไม่งั้น invincible ค้างถาวรเพราะไม่มี respawn cycle มาเคลียร์"""
    metrics = RunMetrics(hearts=5)
    metrics.decrease_heart(allow_respawn=False)
    assert metrics.hearts == 4
    assert not metrics.needs_respawn
    assert not metrics.is_invincible

    # เสียซ้ำได้ทันที (ไม่มี invincible frame)
    metrics.decrease_heart(allow_respawn=False)
    assert metrics.hearts == 3


def test_decrease_heart_without_respawn_still_triggers_game_over_at_zero():
    metrics = RunMetrics(hearts=1)
    metrics.decrease_heart(allow_respawn=False)
    assert metrics.hearts == 0
    assert metrics.is_game_over
