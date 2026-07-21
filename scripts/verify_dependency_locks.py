"""Verify universal dependency locks against the approved Phase 1 contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PIN_RE = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[^\s;]+)$")
HASH_RE = re.compile(r"--hash=sha256:([0-9a-fA-F]{64})(?=\s|$)")
MARKER_ATOM_RE = re.compile(
    r"""^(python_version|sys_platform|platform_system|platform_machine)\s*"""
    r"""(==|!=)\s*(['"])(.*?)\3$"""
)


class LockVerificationError(ValueError):
    """Raised when a lock differs from the human-approved contract."""


@dataclass(frozen=True)
class LockEntry:
    name: str
    version: str
    marker: str | None
    hashes: frozenset[str]

    @property
    def pin(self) -> str:
        return f"{self.name}=={self.version}"


@dataclass(frozen=True)
class Target:
    scope: str
    python_version: str
    pip_platform: str
    abi: str
    expected_set_name: str
    expected: frozenset[str]

    @property
    def identifier(self) -> str:
        return f"{self.scope.lower()}-cp{self.python_version.replace('.', '')}-{self.pip_platform}"

    @property
    def environment(self) -> dict[str, str]:
        if self.pip_platform == "win_amd64":
            return {
                "python_version": self.python_version,
                "sys_platform": "win32",
                "platform_system": "Windows",
                "platform_machine": "AMD64",
            }
        if self.pip_platform.startswith("macosx_"):
            machine = "arm64" if self.pip_platform.endswith("_arm64") else "x86_64"
            return {
                "python_version": self.python_version,
                "sys_platform": "darwin",
                "platform_system": "Darwin",
                "platform_machine": machine,
            }
        if self.pip_platform == "manylinux_2_17_x86_64":
            return {
                "python_version": self.python_version,
                "sys_platform": "linux",
                "platform_system": "Linux",
                "platform_machine": "x86_64",
            }
        raise LockVerificationError(f"Unapproved target platform: {self.pip_platform}")


def normalize_name(name: str) -> str:
    """Apply the packaging-name normalization needed by the approved tables."""

    return re.sub(r"[-_.]+", "-", name).lower()


def _parse_pin_list(raw: str) -> frozenset[str]:
    pins: set[str] = set()
    for value in raw.split(","):
        pin = value.strip()
        match = PIN_RE.fullmatch(pin)
        if not match:
            raise LockVerificationError(f"Malformed approved pin: {pin}")
        pins.add(f"{normalize_name(match.group('name'))}=={match.group('version')}")
    return frozenset(pins)


def _section(text: str, heading: str, next_heading: str) -> str:
    try:
        return text.split(heading, 1)[1].split(next_heading, 1)[0]
    except IndexError as exc:
        raise LockVerificationError(f"Approval summary section missing: {heading}") from exc


def _artifact_pin(filename: str, approved_pins: frozenset[str]) -> str:
    lowered_filename = filename.lower()
    matches = []
    for pin in approved_pins:
        name, version = pin.split("==", 1)
        prefixes = {
            f"{name}-{version}-",
            f"{name.replace('-', '_')}-{version}-",
        }
        if any(lowered_filename.startswith(prefix) for prefix in prefixes):
            matches.append(pin)
    if len(matches) != 1:
        raise LockVerificationError(
            f"Could not map approved wheel to exactly one package pin: {filename}; "
            f"approved={sorted(approved_pins)}"
        )
    return matches[0]


def parse_approval_summary(path: str | Path) -> dict[str, Any]:
    """Parse the exact closure, target, and wheel contract from Plan 01-01."""

    text = Path(path).read_text(encoding="utf-8")

    direct_section = _section(text, "## Direct Pins", "## Approved Substitutions")
    direct_rows = re.findall(
        r"^\|\s*(Runtime and development|Development only)\s*\|\s*`([^`]+)`\s*\|$",
        direct_section,
        flags=re.MULTILINE,
    )
    if len(direct_rows) != 6:
        raise LockVerificationError(
            f"Expected six approved direct pins, found {len(direct_rows)}"
        )
    runtime_direct = {
        f"{normalize_name(match.group('name'))}=={match.group('version')}"
        for scope, raw_pin in direct_rows
        if scope == "Runtime and development"
        for match in [PIN_RE.fullmatch(raw_pin)]
        if match is not None
    }
    development_direct = {
        f"{normalize_name(match.group('name'))}=={match.group('version')}"
        for _, raw_pin in direct_rows
        for match in [PIN_RE.fullmatch(raw_pin)]
        if match is not None
    }
    if len(runtime_direct) != 4 or len(development_direct) != 6:
        raise LockVerificationError("Approved direct-pin scopes are incomplete")

    substitutions = _section(
        text, "## Approved Substitutions", "## Target Matrix"
    ).strip()
    if "None." not in substitutions or "SUBSTITUTIONS: none" not in substitutions:
        raise LockVerificationError("Approval substitution contract is not exactly none")

    runtime_section = _section(text, "## Runtime Closure", "## Development Closure")
    development_section = _section(
        text, "## Development Closure", "### Environment Marker Treatment"
    )
    runtime_posix_match = re.search(
        r"\*\*R-POSIX \(\d+ packages\):\*\*\s*`([^`]+)`", runtime_section
    )
    development_posix_match = re.search(
        r"\*\*D-POSIX \(\d+ packages\):\*\*[^`]*`([^`]+)`", development_section
    )
    if runtime_posix_match is None or development_posix_match is None:
        raise LockVerificationError("Approved closure lists are missing")
    runtime_posix = _parse_pin_list(runtime_posix_match.group(1))
    development_additions = _parse_pin_list(development_posix_match.group(1))
    development_posix = runtime_posix | development_additions
    colorama = "colorama==0.4.6"
    closure_sets = {
        "R-POSIX": runtime_posix,
        "R-WIN": runtime_posix | {colorama},
        "D-POSIX": development_posix,
        "D-WIN": development_posix | {colorama},
    }

    target_section = _section(text, "## Target Matrix", "## Runtime Closure")
    targets: list[Target] = []
    for line in target_section.splitlines():
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 7 or cells[0] not in {"Runtime", "Development"}:
            continue
        scope, python_version, _, pip_platform, abi, set_name, _ = cells
        if set_name not in closure_sets:
            raise LockVerificationError(f"Unknown approved closure name: {set_name}")
        targets.append(
            Target(
                scope=scope,
                python_version=python_version,
                pip_platform=pip_platform,
                abi=abi,
                expected_set_name=set_name,
                expected=closure_sets[set_name],
            )
        )
    expected_target_count = 16
    if len(targets) != expected_target_count:
        raise LockVerificationError(
            f"Expected {expected_target_count} approved target rows, found {len(targets)}"
        )
    identifiers = {target.identifier for target in targets}
    if len(identifiers) != expected_target_count:
        raise LockVerificationError("Approved target rows contain duplicates")

    approved_union = closure_sets["D-WIN"]
    artifact_section = _section(
        text, "## Binary-Only Evidence", "## Package Legitimacy Approval"
    )
    artifact_hashes: dict[str, set[str]] = {}
    artifact_names: dict[str, list[str]] = {}
    artifact_rows = re.findall(
        r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|$",
        artifact_section,
        flags=re.MULTILINE,
    )
    if len(artifact_rows) != 27:
        raise LockVerificationError(
            f"Expected 27 approved wheel artifacts, found {len(artifact_rows)}"
        )
    for filename, _, artifact_hash in artifact_rows:
        if not filename.endswith(".whl"):
            raise LockVerificationError(f"Source-only artifact is not allowed: {filename}")
        pin = _artifact_pin(filename, approved_union)
        artifact_hashes.setdefault(pin, set()).add(artifact_hash)
        artifact_names.setdefault(pin, []).append(filename)
    if set(artifact_hashes) != set(approved_union):
        raise LockVerificationError("Approved wheel table does not cover the approved union")

    return {
        "runtime_direct": frozenset(runtime_direct),
        "development_direct": frozenset(development_direct),
        "closure_sets": closure_sets,
        "targets": tuple(targets),
        "artifact_hashes": {
            pin: frozenset(hashes) for pin, hashes in artifact_hashes.items()
        },
        "artifact_names": {
            pin: tuple(filenames) for pin, filenames in artifact_names.items()
        },
    }


def _logical_requirement_lines(text: str) -> list[str]:
    logical_lines: list[str] = []
    pending = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith("\\"):
            pending += line[:-1].rstrip() + " "
            continue
        logical_lines.append((pending + line).strip())
        pending = ""
    if pending:
        raise LockVerificationError("Lock ends with an incomplete continuation")
    return logical_lines


def parse_lock(path: str | Path) -> dict[str, LockEntry]:
    """Parse a pip hash lock and reject non-exact or unsupported declarations."""

    text = Path(path).read_text(encoding="utf-8")
    logical_lines = _logical_requirement_lines(text)
    options = {line for line in logical_lines if line.startswith("--") and "--hash=" not in line}
    required_options = {"--only-binary=:all:", "--require-hashes"}
    if options != required_options:
        raise LockVerificationError(
            f"{path}: lock options must be exactly {sorted(required_options)}, got {sorted(options)}"
        )

    entries: dict[str, LockEntry] = {}
    for line in logical_lines:
        if line in required_options:
            continue
        first_hash = line.find(" --hash=sha256:")
        if first_hash < 0:
            raise LockVerificationError(f"{path}: unhashed requirement line: {line}")
        declaration = line[:first_hash].strip()
        hash_options = line[first_hash:]
        if "@" in declaration or "://" in declaration:
            raise LockVerificationError(f"{path}: URL requirements are forbidden: {declaration}")
        requirement, separator, marker = declaration.partition(";")
        pin_match = PIN_RE.fullmatch(requirement.strip())
        if pin_match is None:
            raise LockVerificationError(f"{path}: requirement is not exact-pinned: {declaration}")
        name = normalize_name(pin_match.group("name"))
        version = pin_match.group("version")
        if name in entries:
            prior = entries[name]
            kind = "conflicting" if prior.version != version else "duplicate"
            raise LockVerificationError(f"{path}: {kind} pin for {name}")
        hashes = frozenset(value.lower() for value in HASH_RE.findall(hash_options))
        residue = HASH_RE.sub("", hash_options).strip()
        if not hashes or residue:
            raise LockVerificationError(f"{path}: malformed or absent SHA-256 hash: {line}")
        entries[name] = LockEntry(
            name=name,
            version=version,
            marker=marker.strip() if separator else None,
            hashes=hashes,
        )
    if not entries:
        raise LockVerificationError(f"{path}: lock contains no requirements")
    return entries


def _evaluate_marker_atom(atom: str, environment: dict[str, str]) -> bool:
    match = MARKER_ATOM_RE.fullmatch(atom.strip())
    if match is None:
        raise LockVerificationError(f"Unsupported target marker: {atom}")
    variable, operator, _, expected = match.groups()
    actual = environment[variable]
    return actual == expected if operator == "==" else actual != expected


def _evaluate_marker(marker: str | None, environment: dict[str, str]) -> bool:
    if marker is None:
        return True
    # Locks intentionally use only equality markers; this small evaluator remains auditable.
    return any(
        all(_evaluate_marker_atom(atom, environment) for atom in clause.split(" and "))
        for clause in marker.split(" or ")
    )


def evaluate_target_markers(
    entries: dict[str, LockEntry], target: Target
) -> frozenset[str]:
    """Return the exact pins active for one approved target environment."""

    return frozenset(
        entry.pin
        for entry in entries.values()
        if _evaluate_marker(entry.marker, target.environment)
    )


def _verify_lock(
    label: str,
    entries: dict[str, LockEntry],
    approved_union: frozenset[str],
    approved_direct: frozenset[str],
    artifact_hashes: dict[str, frozenset[str]],
) -> None:
    actual_union = frozenset(entry.pin for entry in entries.values())
    missing = approved_union - actual_union
    extra = actual_union - approved_union
    if missing or extra:
        raise LockVerificationError(
            f"{label} union mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    absent_direct = approved_direct - actual_union
    if absent_direct:
        raise LockVerificationError(
            f"{label} lock is missing direct packages: {sorted(absent_direct)}"
        )
    for entry in entries.values():
        expected_hashes = artifact_hashes.get(entry.pin)
        if expected_hashes is None:
            raise LockVerificationError(f"{label} contains unapproved pin: {entry.pin}")
        if entry.hashes != expected_hashes:
            raise LockVerificationError(
                f"{label} hash mismatch for {entry.pin}; "
                f"missing={sorted(expected_hashes - entry.hashes)}, "
                f"extra={sorted(entry.hashes - expected_hashes)}"
            )


def verify_exact_lock_sets(
    approval: dict[str, Any],
    runtime_entries: dict[str, LockEntry],
    development_entries: dict[str, LockEntry],
) -> dict[str, Any]:
    """Compare every target closure and both normalized unions for exact equality."""

    closures = approval["closure_sets"]
    artifact_hashes = approval["artifact_hashes"]
    _verify_lock(
        "runtime",
        runtime_entries,
        closures["R-WIN"],
        approval["runtime_direct"],
        artifact_hashes,
    )
    _verify_lock(
        "development",
        development_entries,
        closures["D-WIN"],
        approval["development_direct"],
        artifact_hashes,
    )

    target_results: list[dict[str, Any]] = []
    for target in approval["targets"]:
        entries = runtime_entries if target.scope == "Runtime" else development_entries
        actual = evaluate_target_markers(entries, target)
        missing = target.expected - actual
        extra = actual - target.expected
        if missing or extra:
            raise LockVerificationError(
                f"{target.identifier} mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
            )
        target_results.append(
            {
                "target": target.identifier,
                "closure": target.expected_set_name,
                "packages": len(actual),
                "missing": 0,
                "extra": 0,
            }
        )

    return {
        "ok": True,
        "targets_verified": len(target_results),
        "runtime_union_packages": len(runtime_entries),
        "development_union_packages": len(development_entries),
        "approved_wheel_artifacts": sum(
            len(values) for values in approval["artifact_names"].values()
        ),
        "missing": 0,
        "extra": 0,
        "targets": target_results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval", required=True, type=Path)
    parser.add_argument("--runtime-lock", required=True, type=Path)
    parser.add_argument("--dev-lock", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        approval = parse_approval_summary(args.approval)
        runtime_entries = parse_lock(args.runtime_lock)
        development_entries = parse_lock(args.dev_lock)
        result = verify_exact_lock_sets(approval, runtime_entries, development_entries)
    except (OSError, LockVerificationError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
