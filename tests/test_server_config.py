from server.config import DEFAULT_DATABASE_URI, DEFAULT_PORT, DEFAULT_SYNC_SECRET, load_config


def test_load_config_uses_defaults_when_env_vars_are_absent(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SYNC_SECRET", raising=False)
    monkeypatch.delenv("PORT", raising=False)

    config = load_config()

    assert config.database_uri == DEFAULT_DATABASE_URI
    assert config.sync_secret == DEFAULT_SYNC_SECRET
    assert config.port == DEFAULT_PORT


def test_load_config_uses_env_vars_when_present(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@postgres:5432/penguin_dash")
    monkeypatch.setenv("SYNC_SECRET", "a-real-secret")
    monkeypatch.setenv("PORT", "8080")

    config = load_config()

    assert config.database_uri == "postgresql://user:pass@postgres:5432/penguin_dash"
    assert config.sync_secret == b"a-real-secret"
    assert config.port == 8080
