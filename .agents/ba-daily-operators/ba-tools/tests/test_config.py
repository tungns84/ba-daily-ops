"""Tests for .ba-ops/config.json feature-flag defaults (TRACE-02)."""

import json
from pathlib import Path

import pytest

from ba_tools.config import flag, load_config


def test_missing_config_flag_defaults_to_true(tmp_path):
    """When config.json is absent, all feature flags default to True (absent = enabled)."""
    # No .ba-ops/config.json created
    cfg = load_config(tmp_path)
    assert flag(cfg, "render_enabled") is True
    assert flag(cfg, "any_missing_flag") is True


def test_explicit_false_flag_respected(tmp_path):
    """When config.json sets a flag to false, the flag is treated as disabled."""
    ba_ops = tmp_path / ".ba-ops"
    ba_ops.mkdir()
    config_path = ba_ops / "config.json"
    config_path.write_text(json.dumps({"render_enabled": False}), encoding="utf-8")

    cfg = load_config(tmp_path)
    assert flag(cfg, "render_enabled") is False


def test_absent_config_not_written_to_disk(tmp_path):
    """Reading an absent config.json must not create the file on disk."""
    cfg = load_config(tmp_path)
    # Access a flag (this must NOT write anything)
    _ = flag(cfg, "render_enabled")

    config_path = tmp_path / ".ba-ops" / "config.json"
    assert not config_path.exists(), "load_config must not create config.json when absent"


def test_explicit_true_flag_respected(tmp_path):
    """When config.json explicitly sets a flag to true, the flag is enabled."""
    ba_ops = tmp_path / ".ba-ops"
    ba_ops.mkdir()
    config_path = ba_ops / "config.json"
    config_path.write_text(json.dumps({"render_enabled": True}), encoding="utf-8")

    cfg = load_config(tmp_path)
    assert flag(cfg, "render_enabled") is True


def test_flag_with_empty_config_file(tmp_path):
    """Empty config.json is treated as empty dict — all flags default to True."""
    ba_ops = tmp_path / ".ba-ops"
    ba_ops.mkdir()
    config_path = ba_ops / "config.json"
    config_path.write_text("{}", encoding="utf-8")

    cfg = load_config(tmp_path)
    assert flag(cfg, "render_enabled") is True


def test_config_not_mutated_on_absent_flag(tmp_path):
    """config.json content is not modified when a flag is merely read (absent = enabled)."""
    ba_ops = tmp_path / ".ba-ops"
    ba_ops.mkdir()
    config_path = ba_ops / "config.json"
    original_content = json.dumps({"export_png": False})
    config_path.write_text(original_content, encoding="utf-8")

    cfg = load_config(tmp_path)
    # Access a flag that is NOT in the file
    _ = flag(cfg, "render_enabled")

    # File must not have been modified
    after = config_path.read_text(encoding="utf-8")
    assert after == original_content, "config.json must not be modified when reading an absent flag"
