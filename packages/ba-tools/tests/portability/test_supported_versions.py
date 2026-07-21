"""Exact supported-version boundary contracts."""
from __future__ import annotations

from collections import namedtuple

import pytest

from ba_tools import doctor

WindowsVersion = namedtuple("WindowsVersion", "major minor build")
Uname = namedtuple("Uname", "sysname nodename release version machine")


def _os_observation(
    monkeypatch: pytest.MonkeyPatch,
    *,
    platform: str,
    version: tuple[int, int, int],
):
    monkeypatch.setattr(doctor.sys, "platform", platform)
    if platform == "win32":
        monkeypatch.setattr(doctor.sys, "getwindowsversion", lambda: WindowsVersion(*version))
    else:
        release = ".".join(map(str, version))
        monkeypatch.setattr(
            doctor.os,
            "uname",
            lambda: Uname("Darwin", "host", release, release, "arm64"),
            raising=False,
        )
    return doctor._os_probe(None)


def test_exact_minimum_versions_are_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    windows = _os_observation(monkeypatch, platform="win32", version=(10, 0, 0))
    macos = _os_observation(monkeypatch, platform="darwin", version=(12, 0, 0))

    assert windows.ok and windows.observed == {"system": "Windows", "release": "10.0.0"}
    assert macos.ok and macos.observed == {"system": "Darwin", "release": "12.0.0"}
    assert (3, 11, 0) >= (3, 11, 0)


@pytest.mark.parametrize(
    ("platform", "version", "guidance"),
    [
        ("win32", (9, 0, 0), "Windows 10+"),
        ("darwin", (11, 0, 0), "macOS 12+"),
    ],
)
def test_below_minimum_versions_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    platform: str,
    version: tuple[int, int, int],
    guidance: str,
) -> None:
    observation = _os_observation(monkeypatch, platform=platform, version=version)

    assert not observation.ok
    assert observation.summary == "The operating system is unsupported."
    assert guidance in observation.remediation[0]
    assert not ((3, 10, 99) >= (3, 11, 0))


@pytest.mark.parametrize(
    ("windows_version", "macos_version"),
    [
        ((10, 10, 12345), (12, 10, 12345)),
        ((11, 0, 0), (13, 0, 0)),
        ((99, 100, 101), (99, 100, 101)),
    ],
)
def test_newer_multi_digit_versions_are_supported(
    monkeypatch: pytest.MonkeyPatch,
    windows_version: tuple[int, int, int],
    macos_version: tuple[int, int, int],
) -> None:
    windows = _os_observation(monkeypatch, platform="win32", version=windows_version)
    macos = _os_observation(monkeypatch, platform="darwin", version=macos_version)

    assert windows.ok
    assert macos.ok


@pytest.mark.parametrize("text", ["", "version unknown", "vNext", "one.two.three"])
def test_malformed_versions_are_rejected(text: str) -> None:
    assert doctor._version_tuple(text) is None


def test_version_comparison_uses_integer_tuples() -> None:
    assert doctor._version_tuple("10.0.26200") == (10, 0, 26200)
    assert doctor._version_tuple("12.10") == (12, 10, 0)
    assert doctor._version_tuple("Python 3.11.9") == (3, 11, 9)
    assert doctor._version_tuple("Python 3.9.99") < doctor._version_tuple("Python 3.11.0")
    assert doctor._version_tuple("macOS 12.10") > doctor._version_tuple("macOS 12.9")
