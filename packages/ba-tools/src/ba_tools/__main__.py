"""Importable process seam for the ba-tools command."""

from __future__ import annotations


def entrypoint(argv: list[str] | None = None) -> int:
    """Enter the application boundary before command behavior is implemented."""

    del argv
    return 2


if __name__ == "__main__":
    raise SystemExit(entrypoint())
