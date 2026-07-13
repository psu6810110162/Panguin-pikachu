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

