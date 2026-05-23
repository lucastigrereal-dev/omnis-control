from src.utils.dry_run import is_real_mode, resolve_dry_run


def test_explicit_dry_run_overrides_env(monkeypatch):
    monkeypatch.setenv("OMNIS_DRY_RUN", "false")

    assert resolve_dry_run(True) is True
    assert resolve_dry_run(False) is False


def test_env_false_values_enable_real_mode(monkeypatch):
    for value in ("false", "0", "no", "off"):
        monkeypatch.setenv("OMNIS_DRY_RUN", value)

        assert resolve_dry_run() is False
        assert is_real_mode() is True


def test_default_is_safe_dry_run(monkeypatch):
    monkeypatch.delenv("OMNIS_DRY_RUN", raising=False)

    assert resolve_dry_run() is True
    assert is_real_mode() is False
