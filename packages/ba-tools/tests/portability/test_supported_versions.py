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


def test_exact_minimum_windows_version_is_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    windows = _os_observation(monkeypatch, platform="win32", version=(10, 0, 0))

    assert windows.ok and windows.observed == {"system": "Windows", "release": "10.0.0"}


def test_macos_is_unsupported_in_current_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    macos = _os_observation(monkeypatch, platform="darwin", version=(12, 0, 0))

    assert not macos.ok
    assert macos.observed == {"system": "Darwin", "release": "12.0.0"}
    assert "Windows 10+" in macos.remediation[0]


@pytest.mark.parametrize(
    ("platform", "version", "guidance"),
    [
        ("win32", (9, 0, 0), "Windows 10"),
        ("darwin", (12, 0, 0), "Windows 10+"),
        ("linux", (6, 0, 0), "Windows 10+"),
    ],
)
def test_below_minimum_or_out_of_scope_os_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    platform: str,
    version: tuple[int, int, int],
    guidance: str,
) -> None:
    if platform == "linux":
        monkeypatch.setattr(doctor.sys, "platform", "linux")
        monkeypatch.setattr(
            doctor.os,
            "uname",
            lambda: Uname("Linux", "host", ".".join(map(str, version)), "", "x86_64"),
            raising=False,
        )
        observation = doctor._os_probe(None)
    else:
        observation = _os_observation(monkeypatch, platform=platform, version=version)

    assert not observation.ok
    assert observation.summary == "The operating system is unsupported."
    assert guidance in observation.remediation[0]


@pytest.mark.parametrize(
    "windows_version",
    [
        (10, 10, 12345),
        (11, 0, 0),
        (99, 100, 101),
    ],
)
def test_newer_multi_digit_windows_versions_are_supported(
    monkeypatch: pytest.MonkeyPatch,
    windows_version: tuple[int, int, int],
) -> None:
    windows = _os_observation(monkeypatch, platform="win32", version=windows_version)

    assert windows.ok


@pytest.mark.parametrize(
    "macos_version",
    [
        (12, 10, 12345),
        (13, 0, 0),
        (99, 100, 101),
    ],
)
def test_newer_macos_versions_remain_unsupported_in_current_scope(
    monkeypatch: pytest.MonkeyPatch,
    macos_version: tuple[int, int, int],
) -> None:
    macos = _os_observation(monkeypatch, platform="darwin", version=macos_version)

    assert not macos.ok
    assert "Windows 10+" in macos.remediation[0]


@pytest.mark.parametrize("text", ["", "version unknown", "vNext", "one.two.three"])
def test_malformed_versions_are_rejected(text: str) -> None:
    assert doctor._version_tuple(text) is None


def test_version_comparison_uses_integer_tuples() -> None:
    assert doctor._version_tuple("10.0.26200") == (10, 0, 26200)
    assert doctor._version_tuple("12.10") == (12, 10, 0)
    assert doctor._version_tuple("Python 3.14.0") == (3, 14, 0)
    assert doctor._version_tuple("Python 3.13.99") < doctor._version_tuple("Python 3.14.0")
    assert doctor._version_tuple("macOS 12.10") > doctor._version_tuple("macOS 12.9")


def test_exact_minimum_python_version_is_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor.sys, "version_info", (3, 14, 0))

    observation = doctor._python_probe(None)

    assert observation.ok
    assert observation.observed == {"version": "3.14.0", "minimum": "3.14"}


def test_python_below_minimum_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor.sys, "version_info", (3, 13, 9))

    observation = doctor._python_probe(None)

    assert not observation.ok
    assert observation.summary == "Python 3.14 or newer is required."
    assert "3.14" in observation.remediation[0]
