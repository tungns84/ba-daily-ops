"""D-07 through D-10 doctor registry, snapshot, safety, and launcher contracts."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_ROOT = PROJECT_ROOT / "packages" / "ba-tools"

PRE_INIT_IDS = [
    "os.supported",
    "python.version",
    "python.utf8",
    "git.version",
    "repo.root",
    "install.version",
    "install.lock_digest",
    "install.active_generation",
    "launcher.current",
]
POST_INIT_IDS = [
    *PRE_INIT_IDS,
    "state.config",
    "state.coverage_policy",
    "state.business_goals",
    "state.schemas",
    "state.profile_policy",
    "state.abandoned_temps",
]
OPTIONAL_IDS = ["optional.node", "optional.mmdc", "optional.drawio"]


def doctor_module():
    """Import lazily so the RED module still collects every test."""

    return importlib.import_module("ba_tools.doctor")


def parse_document(raw: bytes) -> dict[str, Any]:
    assert raw.endswith(b"\n")
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.count(b"\n") == 1
    payload = json.loads(raw.decode("utf-8"))
    assert isinstance(payload, dict)
    return payload


def snapshot_tree(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        path.relative_to(root).as_posix(): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def make_definition(
    module,
    check_id: str,
    *,
    ok: bool = True,
    required: bool = True,
    prerequisites: tuple[str, ...] = (),
):
    def probe(_context):
        return module.ProbeObservation(
            ok=ok,
            summary=f"{check_id} {'available' if ok else 'unavailable'}",
            observed={"value": f"observed-{check_id}"},
            remediation=() if ok else (f"Remediate {check_id}.",),
        )

    return module.CheckDefinition(
        id=check_id,
        scope=module.CheckScope.CORE if required else module.CheckScope.OPTIONAL,
        required_when=required,
        prerequisites=prerequisites,
        probe=probe,
        timeout=1.0,
    )


def context_for(module, repo: Path):
    from ba_tools.paths import resolve_repo_root

    return module.DoctorContext(
        root=resolve_repo_root(repo),
        initialized=(repo / ".ba-ops").is_dir(),
        profile="light",
        enabled_plugins=(),
    )


def result_ids(result) -> list[str]:
    return [check.id for check in result.checks]


def test_empty_core_registry_is_rejected(temp_repo: Path) -> None:
    module = doctor_module()

    with pytest.raises(ValueError, match="core registry.*empty"):
        module.validate_registry(())


def test_duplicate_check_ids_are_rejected(temp_repo: Path) -> None:
    module = doctor_module()
    duplicate = (
        make_definition(module, "duplicate"),
        make_definition(module, "duplicate"),
    )

    with pytest.raises(ValueError, match="duplicate.*duplicate"):
        module.validate_registry(duplicate)


def test_duplicate_prerequisites_are_rejected() -> None:
    module = doctor_module()
    registry = (
        make_definition(module, "root"),
        make_definition(module, "child", prerequisites=("root", "root")),
    )

    with pytest.raises(ValueError, match="duplicate prerequisite.*child"):
        module.validate_registry(registry)


def test_unknown_or_cyclic_prerequisites_are_rejected() -> None:
    module = doctor_module()
    unknown = (make_definition(module, "child", prerequisites=("missing",)),)
    cycle = (
        make_definition(module, "a", prerequisites=("b",)),
        make_definition(module, "b", prerequisites=("a",)),
    )

    with pytest.raises(ValueError, match="unknown prerequisite.*missing"):
        module.validate_registry(unknown)
    with pytest.raises(ValueError, match="cycle"):
        module.validate_registry(cycle)


def test_every_selected_check_produces_one_equal_order_result(temp_repo: Path) -> None:
    module = doctor_module()
    registry = tuple(make_definition(module, check_id) for check_id in ("z", "a", "m"))

    result = module.execute_check_registry(registry, context_for(module, temp_repo))

    assert result_ids(result) == ["z", "a", "m"]
    assert [check.status.value for check in result.checks] == ["pass", "pass", "pass"]


def test_default_and_all_scopes_are_ordered(temp_repo: Path) -> None:
    module = doctor_module()
    context = context_for(module, temp_repo)

    default = module.run_doctor(context.root, include_all=False)
    complete = module.run_doctor(context.root, include_all=True)

    assert result_ids(default) == PRE_INIT_IDS
    assert result_ids(complete) == [*PRE_INIT_IDS, *OPTIONAL_IDS]


def test_pre_and_post_init_scopes_are_exact(
    temp_repo: Path,
    run_cli_bytes,
) -> None:
    module = doctor_module()
    pre = module.run_doctor(context_for(module, temp_repo).root)

    initialized = run_cli_bytes(
        "--repo-root",
        str(temp_repo),
        "init",
        cwd=PROJECT_ROOT,
    )
    assert initialized.returncode == 0
    post = module.run_doctor(context_for(module, temp_repo).root)

    assert result_ids(pre) == PRE_INIT_IDS
    assert result_ids(post) == POST_INIT_IDS


def test_required_failure_exits_two(temp_repo: Path, run_cli_bytes) -> None:
    result = run_cli_bytes(
        "--repo-root",
        str(temp_repo),
        "doctor",
        cwd=PROJECT_ROOT,
    )

    assert result.returncode == 2
    assert result.stdout == b""
    payload = parse_document(result.stderr)
    assert payload["command"] == "doctor"
    assert payload["error"]["code"] == "DOCTOR_FAILED"
    snapshot = payload["error"]["details"][0]
    assert snapshot["status"] == "fail"
    assert [check["id"] for check in snapshot["checks"]] == PRE_INIT_IDS


def test_optional_absence_is_warning(temp_repo: Path) -> None:
    module = doctor_module()
    registry = (
        make_definition(module, "core"),
        make_definition(module, "optional", ok=False, required=False),
    )

    result = module.execute_check_registry(registry, context_for(module, temp_repo))

    assert result.status.value == "warning"
    assert [check.status.value for check in result.checks] == ["pass", "warning"]


def test_failed_prerequisites_skip_only_descendants(temp_repo: Path) -> None:
    module = doctor_module()
    registry = (
        make_definition(module, "failed", ok=False),
        make_definition(module, "child", prerequisites=("failed",)),
        make_definition(module, "grandchild", prerequisites=("child",)),
        make_definition(module, "independent"),
    )

    result = module.execute_check_registry(registry, context_for(module, temp_repo))

    assert [check.status.value for check in result.checks] == [
        "fail",
        "skipped",
        "skipped",
        "pass",
    ]
    assert result.checks[1].blocked_by == ("failed",)
    assert result.checks[2].blocked_by == ("child",)
    assert result.checks[3].observed == {"value": "observed-independent"}


def test_malformed_state_returns_complete_safe_diagnostics(
    temp_repo: Path,
    run_cli_bytes,
) -> None:
    initialized = run_cli_bytes(
        "--repo-root",
        str(temp_repo),
        "init",
        cwd=PROJECT_ROOT,
    )
    assert initialized.returncode == 0
    (temp_repo / ".ba-ops" / "config.json").write_bytes(b"{not-json")

    result = run_cli_bytes(
        "--repo-root",
        str(temp_repo),
        "doctor",
        cwd=PROJECT_ROOT,
    )

    assert result.returncode == 2
    payload = parse_document(result.stderr)
    raw = result.stderr.decode("utf-8")
    assert "Traceback" not in raw
    assert str(temp_repo) not in raw
    snapshot = payload["error"]["details"][0]
    checks = {check["id"]: check for check in snapshot["checks"]}
    assert checks["state.config"]["status"] == "fail"
    assert checks["state.config"]["observed"]["diagnostics"] == [
        {
            "message": "File is not valid UTF-8 JSON.",
            "path": ".ba-ops/config.json",
            "pointer": "",
            "validator": "parse",
        }
    ]
    assert checks["state.config"]["remediation"]
    assert [check["id"] for check in snapshot["checks"]] == POST_INIT_IDS


def test_doctor_is_read_only_and_zero_network(
    temp_repo: Path,
    run_cli_bytes,
    deny_network: dict[str, str],
) -> None:
    state = run_cli_bytes(
        "--repo-root",
        str(temp_repo),
        "init",
        cwd=PROJECT_ROOT,
    )
    assert state.returncode == 0
    before = snapshot_tree(temp_repo)

    result = run_cli_bytes(
        "--repo-root",
        str(temp_repo),
        "doctor",
        "--all",
        cwd=PROJECT_ROOT,
        env=deny_network,
    )

    assert result.returncode == 2
    assert snapshot_tree(temp_repo) == before
    payload = parse_document(result.stderr)
    snapshot = payload["error"]["details"][0]
    assert [check["id"] for check in snapshot["checks"]] == [*POST_INIT_IDS, *OPTIONAL_IDS]


def test_parallel_doctor_snapshots_are_independent(
    temp_repo: Path,
    run_cli_bytes,
    process_barrier,
) -> None:
    initialized = run_cli_bytes(
        "--repo-root",
        str(temp_repo),
        "init",
        cwd=PROJECT_ROOT,
    )
    assert initialized.returncode == 0
    before = snapshot_tree(temp_repo)
    arguments = ["--repo-root", str(temp_repo), "doctor", "--all"]

    results = process_barrier([arguments] * 4, cwd=PROJECT_ROOT)

    assert all(result.returncode == 2 for result in results)
    snapshots = [parse_document(result.stderr)["error"]["details"][0] for result in results]
    assert snapshots[1:] == snapshots[:-1]
    assert all(
        [check["id"] for check in snapshot["checks"]] == [*POST_INIT_IDS, *OPTIONAL_IDS]
        for snapshot in snapshots
    )
    assert snapshot_tree(temp_repo) == before


def test_probe_processes_are_fixed_bounded_and_shell_free() -> None:
    module = doctor_module()
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "shell=False" in source
    assert "timeout=" in source
    assert "shell=True" not in source
    assert "os.system" not in source
    assert "Popen(" not in source
    for forbidden in ("pip install", "npm view", "http://", "https://", "socket", "urllib"):
        assert forbidden not in source


def test_observed_values_are_allowlisted_complete_and_untruncated(temp_repo: Path) -> None:
    module = doctor_module()
    long_value = "Tiếng Việt — " + ("chi tiết " * 300)

    def probe(_context):
        return module.ProbeObservation(
            ok=False,
            summary=long_value,
            observed={"value": long_value, "empty": "", "items": []},
            remediation=(long_value,),
        )

    definition = module.CheckDefinition(
        id="complete",
        scope=module.CheckScope.CORE,
        required_when=True,
        prerequisites=(),
        probe=probe,
        timeout=1.0,
    )
    result = module.execute_check_registry((definition,), context_for(module, temp_repo))
    encoded = json.dumps(result.as_dict(), ensure_ascii=False)

    assert long_value in encoded
    assert "..." not in encoded
    assert result.checks[0].observed == {"value": long_value, "empty": "", "items": []}


def test_generated_launcher_exposes_complete_doctor_snapshot(
    tmp_path: Path,
    dev_python: Path,
) -> None:
    from test_installer import load_bootstrap

    bootstrap = load_bootstrap()
    repo = tmp_path / "Dự án doctor launcher"
    repo.mkdir()
    shutil.copytree(PROJECT_ROOT / "installer", repo / "installer")
    runtime = repo / ".ba-tools-runtime"
    generation = runtime / "envs" / "doctor-generation"
    scripts = generation / ("Scripts" if sys.platform == "win32" else "bin")
    scripts.mkdir(parents=True)
    interpreter = scripts / ("python.exe" if sys.platform == "win32" else "python")
    shutil.copy2(dev_python, interpreter)
    source_cfg = dev_python.parents[1] / "pyvenv.cfg"
    if source_cfg.exists():
        shutil.copy2(source_cfg, generation / "pyvenv.cfg")
    (runtime / "current-env.txt").write_text(
        "doctor-generation\n",
        encoding="utf-8",
        newline="\n",
    )
    bootstrap.publish_launchers(repo)
    launcher = repo / ("ba-tools.ps1" if sys.platform == "win32" else "ba-tools")
    command = (
        ["powershell.exe", "-NoProfile", "-File", str(launcher), "doctor", "--all"]
        if sys.platform == "win32"
        else [str(launcher), "doctor", "--all"]
    )
    site_packages = next(path for path in map(Path, sys.path) if path.name == "site-packages")

    result = subprocess.run(
        command,
        cwd=tmp_path,
        capture_output=True,
        check=False,
        timeout=30,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join((str(PACKAGE_ROOT / "src"), str(site_packages))),
        },
    )

    assert result.returncode == 2
    assert result.stdout == b""
    snapshot = parse_document(result.stderr)["error"]["details"][0]
    assert [check["id"] for check in snapshot["checks"]] == [*PRE_INIT_IDS, *OPTIONAL_IDS]


def test_core_registry_contract_covers_d07_through_d10() -> None:
    module = doctor_module()

    assert [definition.id for definition in module.CORE_CHECKS] == PRE_INIT_IDS
    assert [definition.id for definition in module.PROFILE_CHECKS] == POST_INIT_IDS[len(PRE_INIT_IDS) :]
    assert [definition.id for definition in module.OPTIONAL_CHECKS] == OPTIONAL_IDS
    assert hashlib.sha256(
        "|".join([*POST_INIT_IDS, *OPTIONAL_IDS]).encode("utf-8")
    ).hexdigest()
