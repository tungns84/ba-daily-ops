"""
.ba-ops/config.json feature-flag loader (TRACE-02, DESIGN §1 principle 4).

Absent = enabled: a missing feature flag is treated as True.
Never write defaults to disk on absence — that would silently mask an intent to disable.

Anti-pattern explicitly forbidden (01-RESEARCH.md):
  Writing config.json or persisting a default when a key is merely absent.

Public API:
  load_config(root: Path) -> dict
      Read .ba-ops/config.json if present; return {} otherwise.
      Never creates or modifies the file.

  flag(cfg: dict, name: str) -> bool
      Return cfg.get(name, True).
      True  when key absent (absent = enabled — TRACE-02).
      False when key present and falsy (e.g. {"render_enabled": false}).
"""

import json
from pathlib import Path


def load_config(root: Path) -> dict:
    """Load .ba-ops/config.json from *root* if it exists.

    Returns an empty dict when the file is absent or empty.
    Never creates or modifies the config file (TRACE-02 anti-pattern guard).

    Args:
        root: resolved repository root Path (from resolve_repo_root).

    Returns:
        A dict of configuration keys read from config.json, or ``{}`` if
        the file does not exist or contains only whitespace.
    """
    config_path = root / ".ba-ops" / "config.json"
    if not config_path.exists():
        return {}
    text = config_path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    return json.loads(text)


def flag(cfg: dict, name: str) -> bool:
    """Return the boolean value of feature flag *name* from *cfg*.

    Implements DESIGN §1 principle 4 (absent = enabled):
    - If *name* is absent from *cfg* → return ``True`` (feature is ON).
    - If *name* is present and falsy → return ``False`` (feature is OFF).
    - If *name* is present and truthy → return ``True``.

    Never reads or writes disk — pure dict lookup.

    Args:
        cfg: configuration dict (from load_config).
        name: feature flag name.

    Returns:
        bool — True if enabled (absent or truthy), False if explicitly disabled.
    """
    return bool(cfg.get(name, True))
