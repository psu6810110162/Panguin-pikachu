import pytest

from server.config import (
    DEFAULT_DATABASE_URI,
    DEFAULT_PORT,
    DEFAULT_RATE_LIMIT,
    DEFAULT_SYNC_SECRET,
    load_config,
)


def test_load_config_uses_defaults_when_env_vars_are_absent(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SYNC_SECRET", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("RATE_LIMIT", raising=False)
    monkeypatch.setenv("FLASK_DEBUG", "1")  # default secret ใช้ได้เฉพาะโหมด debug

    config = load_config()

    assert config.database_uri == DEFAULT_DATABASE_URI
    assert config.sync_secret == DEFAULT_SYNC_SECRET
    assert config.port == DEFAULT_PORT
    assert config.rate_limit == DEFAULT_RATE_LIMIT
    assert config.debug is True


def test_load_config_uses_env_vars_when_present(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@postgres:5432/penguin_dash")
    monkeypatch.setenv("SYNC_SECRET", "a-real-secret")
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setenv("RATE_LIMIT", "10 per minute")
    monkeypatch.delenv("FLASK_DEBUG", raising=False)

    config = load_config()

    assert config.database_uri == "postgresql://user:pass@postgres:5432/penguin_dash"
    assert config.sync_secret == b"a-real-secret"
    assert config.port == 8080
    assert config.rate_limit == "10 per minute"
    assert config.debug is False  # debug ต้อง opt-in เท่านั้น


def test_load_config_refuses_the_default_secret_outside_debug(monkeypatch):
    # guard rail สำคัญที่สุดของไฟล์นี้: default secret อยู่ใน public repo — ถ้า
    # FLASK_DEBUG ปิด (ตั้งใจรันแบบ deploy/ngrok) ต้อง refuse ไม่ใช่รันต่อเงียบ ๆ
    monkeypatch.delenv("SYNC_SECRET", raising=False)
    monkeypatch.delenv("FLASK_DEBUG", raising=False)

    with pytest.raises(RuntimeError, match="SYNC_SECRET"):
        load_config()


def test_load_config_accepts_a_real_secret_outside_debug(monkeypatch):
    monkeypatch.setenv("SYNC_SECRET", "a-real-secret")
    monkeypatch.setenv("FLASK_DEBUG", "0")

    config = load_config()

    assert config.debug is False
    assert config.sync_secret == b"a-real-secret"
