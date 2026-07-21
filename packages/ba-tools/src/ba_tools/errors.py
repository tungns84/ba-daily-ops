"""Typed, safe failures for the ba-tools process boundary."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BaToolsError(Exception):
    """An expected failure whose fields are safe to expose to callers."""

    code: str
    message: str
    details: tuple[object, ...] = field(default_factory=tuple)
    remediation: tuple[str, ...] = field(default_factory=tuple)

    def __str__(self) -> str:
        return self.message
