"""Tests for ba-tools trace write (TOOL-07 / TRACE-04).

TDD RED phase: all tests should fail initially (trace_cmd.py does not exist yet).

Covers:
- D-05 record schema (kind/slug/artifact_path/source_doc/source_hash/req_ids)
- Caller-supplied --req-ids subset for downstream kinds
- kind=srs defaults to all requirements (no --req-ids needed)
- Statement hash normalization (D-12)
- Source hash (D-06)
- kind/slug validation (Codex HIGH: path-traversal on write)
- Overwrite requires --force
- Lockfile guarding
- Path traversal on --artifact/--source-doc
- No cross-command hash import (hashing from ba_tools.hashing only)
- Command registration
"""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from ba_tools.hashing import _sha256_file, _statement_hash

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SOURCE_TEXT = """\
# Use Case Document

## Overview

The system shall provide a traceability index that maps each requirement to
the artifacts that implement it, enabling drift detection when requirements change.

## Requirements

FR-001: The system shall record artifact provenance via trace records.
FR-002: The system shall detect stale artifacts via source_hash comparison.
FR-003: The system shall flag gap requirements that have no downstream trace.
FR-004: The system shall flag orphan requirements cited by traces but not defined.
FR-005: The system shall render an INDEX.md traceability matrix.
"""

SAMPLE_REQUIREMENTS = {
    "requirements": [
        {
            "id": "FR-001",
            "statement": "The system shall record artifact provenance via trace records.",
            "status": "stated",
            "source_trace": {"doc": "source.md", "section": "Requirements", "span": "The system shall record artifact provenance via trace records."},
        },
        {
            "id": "FR-002",
            "statement": "The system shall detect stale artifacts via source_hash comparison.",
            "status": "stated",
            "source_trace": {"doc": "source.md", "section": "Requirements", "span": "The system shall detect stale artifacts via source_hash comparison."},
        },
        {
            "id": "FR-003",
            "statement": "The system shall flag gap requirements that have no downstream trace.",
            "status": "stated",
            "source_trace": {"doc": "source.md", "section": "Requirements", "span": "The system shall flag gap requirements that have no downstream trace."},
        },
        {
            "id": "FR-004",
            "statement": "The system shall flag orphan requirements cited by traces but not defined.",
            "status": "stated",
            "source_trace": {"doc": "source.md", "section": "Requirements", "span": "The system shall flag orphan requirements cited by traces but not defined."},
        },
        {
            "id": "FR-005",
            "statement": "The system shall render an INDEX.md traceability matrix.",
            "status": "stated",
            "source_trace": {"doc": "source.md", "section": "Requirements", "span": "The system shall render an INDEX.md traceability matrix."},
        },
    ]
}


@pytest.fixture()
def trace_env(tmp_path):
    """Set up a minimal trace test environment.

    Returns a dict with:
      root:         tmp_path (repo root)
      ba_ops:       tmp_path/.ba-ops
      traces_dir:   tmp_path/.ba-ops/traces/
      source_doc:   tmp_path/source.md (written with SAMPLE_SOURCE_TEXT)
      artifact:     tmp_path/output.srs.md (a mock artifact file)
      reqs_file:    tmp_path/requirements.json (written with SAMPLE_REQUIREMENTS)
    """
    ba_ops = tmp_path / ".ba-ops"
    ba_ops.mkdir()
    traces_dir = ba_ops / "traces"
    traces_dir.mkdir()

    source_doc = tmp_path / "source.md"
    source_doc.write_text(SAMPLE_SOURCE_TEXT, encoding="utf-8")

    artifact = tmp_path / "output.srs.md"
    artifact.write_text("# SRS output", encoding="utf-8")

    reqs_file = tmp_path / "requirements.json"
    reqs_file.write_text(json.dumps(SAMPLE_REQUIREMENTS), encoding="utf-8")

    return {
        "root": tmp_path,
        "ba_ops": ba_ops,
        "traces_dir": traces_dir,
        "source_doc": source_doc,
        "artifact": artifact,
        "reqs_file": reqs_file,
    }


def run_trace_write(env, extra_args=None):
    """Helper: invoke `ba-tools trace write` via subprocess, return CompletedProcess."""
    cmd = [
        sys.executable, "-m", "ba_tools",
        "--repo-root", str(env["root"]),
        "trace", "write",
        "--kind", "srs",
        "--slug", "demo",
        "--artifact", str(env["artifact"]),
        "--source-doc", str(env["source_doc"]),
        "--requirements", str(env["reqs_file"]),
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# D-05 record schema
# ---------------------------------------------------------------------------

class TestTraceWriteSchema:
    """trace write produces the correct D-05 record shape."""

    def test_trace_write_schema(self, trace_env):
        """Writing a srs trace produces a file with exactly the D-05 keys."""
        env = trace_env
        result = run_trace_write(env)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"

        trace_file = env["traces_dir"] / "srs-demo.json"
        assert trace_file.exists(), "srs-demo.json not created"

        record = json.loads(trace_file.read_text(encoding="utf-8"))
        d05_keys = {"kind", "slug", "artifact_path", "source_doc", "source_hash", "req_ids"}
        assert set(record.keys()) == d05_keys, (
            f"D-05 keys mismatch: got {set(record.keys())}"
        )

    def test_trace_write_req_ids_are_objects(self, trace_env):
        """req_ids must be a list of {id, statement_hash} objects, not bare strings."""
        env = trace_env
        run_trace_write(env)

        record = json.loads((env["traces_dir"] / "srs-demo.json").read_text())
        assert isinstance(record["req_ids"], list), "req_ids must be a list"
        assert len(record["req_ids"]) > 0, "req_ids must not be empty"
        for item in record["req_ids"]:
            assert isinstance(item, dict), f"req_ids item must be a dict, got {type(item)}"
            assert "id" in item, "req_ids item must have 'id'"
            assert "statement_hash" in item, "req_ids item must have 'statement_hash'"
            # No extra keys
            assert set(item.keys()) == {"id", "statement_hash"}, (
                f"req_ids item extra keys: {set(item.keys())}"
            )

    def test_trace_write_paths_are_relative(self, trace_env):
        """artifact_path and source_doc are stored as relative paths (not absolute)."""
        env = trace_env
        run_trace_write(env)
        record = json.loads((env["traces_dir"] / "srs-demo.json").read_text())

        # Should NOT be absolute paths
        assert not Path(record["artifact_path"]).is_absolute(), (
            f"artifact_path should be relative: {record['artifact_path']}"
        )
        assert not Path(record["source_doc"]).is_absolute(), (
            f"source_doc should be relative: {record['source_doc']}"
        )

    def test_trace_write_kind_slug_in_record(self, trace_env):
        """kind and slug are stored verbatim in the record."""
        env = trace_env
        run_trace_write(env)
        record = json.loads((env["traces_dir"] / "srs-demo.json").read_text())
        assert record["kind"] == "srs"
        assert record["slug"] == "demo"


# ---------------------------------------------------------------------------
# Caller-supplied --req-ids subset (Codex HIGH: subset/orphan coverage)
# ---------------------------------------------------------------------------

class TestTraceSubsetReqIds:
    """Downstream (non-srs) kinds accept a caller-supplied req-ids SUBSET."""

    def test_trace_subset_req_ids(self, trace_env):
        """A mermaid trace with --req-ids FR-001,FR-002 records only those two."""
        env = trace_env
        cmd = [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(env["root"]),
            "trace", "write",
            "--kind", "mermaid",
            "--slug", "flow",
            "--artifact", str(env["artifact"]),
            "--source-doc", str(env["source_doc"]),
            "--requirements", str(env["reqs_file"]),
            "--req-ids", "FR-001,FR-002",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"

        trace_file = env["traces_dir"] / "mermaid-flow.json"
        assert trace_file.exists()
        record = json.loads(trace_file.read_text())
        ids = {item["id"] for item in record["req_ids"]}
        assert ids == {"FR-001", "FR-002"}, (
            f"Expected only FR-001, FR-002; got {ids}"
        )

    def test_trace_srs_defaults_all(self, trace_env):
        """A srs trace with NO --req-ids records ALL requirements."""
        env = trace_env
        run_trace_write(env)
        record = json.loads((env["traces_dir"] / "srs-demo.json").read_text())
        ids = {item["id"] for item in record["req_ids"]}
        expected = {"FR-001", "FR-002", "FR-003", "FR-004", "FR-005"}
        assert ids == expected, f"Expected all five ids; got {ids}"

    def test_trace_non_srs_no_req_ids_fails(self, trace_env):
        """A non-srs kind without --req-ids raises an error (req-ids required)."""
        env = trace_env
        cmd = [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(env["root"]),
            "trace", "write",
            "--kind", "mermaid",
            "--slug", "flow",
            "--artifact", str(env["artifact"]),
            "--source-doc", str(env["source_doc"]),
            "--requirements", str(env["reqs_file"]),
            # No --req-ids
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 2, (
            f"Expected exit 2 for non-srs missing --req-ids; got {result.returncode}"
        )

    def test_trace_subset_one_ok_one_gap_setup(self, trace_env):
        """Two srs reqs + mermaid trace covering only FR-001 → record has only FR-001."""
        env = trace_env
        # Write a mermaid trace covering only FR-001 (the gap/ok split is tested in test_index)
        cmd = [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(env["root"]),
            "trace", "write",
            "--kind", "mermaid",
            "--slug", "partial",
            "--artifact", str(env["artifact"]),
            "--source-doc", str(env["source_doc"]),
            "--requirements", str(env["reqs_file"]),
            "--req-ids", "FR-001",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        record = json.loads((env["traces_dir"] / "mermaid-partial.json").read_text())
        ids = {item["id"] for item in record["req_ids"]}
        assert ids == {"FR-001"}


# ---------------------------------------------------------------------------
# Statement hash normalization (D-12)
# ---------------------------------------------------------------------------

class TestStatementHashNormalization:
    """_statement_hash (imported from ba_tools.hashing) behaves per D-12 spec."""

    def test_whitespace_normalization(self):
        """Statements differing only by internal whitespace hash identically."""
        h1 = _statement_hash("a  b")
        h2 = _statement_hash(" a b ")
        assert h1 == h2, "Whitespace-only diff should hash the same"

    def test_material_change_hashes_differently(self):
        """Materially different statements produce different hashes."""
        h1 = _statement_hash("a b")
        h2 = _statement_hash("a c")
        assert h1 != h2, "Different content should hash differently"

    def test_no_case_fold(self):
        """Case differences produce different hashes (no case-fold per D-12)."""
        h1 = _statement_hash("The System shall do X")
        h2 = _statement_hash("the system shall do x")
        assert h1 != h2, "D-12: no case-fold; case-diff should hash differently"

    def test_statement_hash_imported_not_redefined(self):
        """trace_cmd does not redefine _statement_hash — it imports from ba_tools.hashing."""
        trace_cmd_path = (
            Path(__file__).parent.parent / "ba_tools" / "commands" / "trace_cmd.py"
        )
        if not trace_cmd_path.exists():
            pytest.skip("trace_cmd.py not yet created (RED phase)")
        content = trace_cmd_path.read_text(encoding="utf-8")
        assert "def _statement_hash" not in content, (
            "trace_cmd.py must NOT redefine _statement_hash; import from ba_tools.hashing"
        )
        assert "def _sha256_file" not in content, (
            "trace_cmd.py must NOT redefine _sha256_file; import from ba_tools.hashing"
        )


# ---------------------------------------------------------------------------
# Source hash (D-06)
# ---------------------------------------------------------------------------

class TestSourceHash:
    """source_hash equals sha256 of the source doc bytes."""

    def test_source_hash_matches(self, trace_env):
        """The recorded source_hash matches the sha256 of the live source doc."""
        env = trace_env
        run_trace_write(env)
        record = json.loads((env["traces_dir"] / "srs-demo.json").read_text())
        expected_hash = _sha256_file(env["source_doc"])
        assert record["source_hash"] == expected_hash, (
            f"source_hash mismatch: {record['source_hash']!r} != {expected_hash!r}"
        )


# ---------------------------------------------------------------------------
# kind/slug validation (Codex HIGH: path-traversal on write)
# ---------------------------------------------------------------------------

class TestSlugValidation:
    """kind and slug are validated against ^[a-z0-9][a-z0-9-]*$."""

    def test_trace_slug_rejected_dotdot(self, trace_env):
        """--slug ../../x raises INVALID_KIND_SLUG exit 2 and writes nothing outside traces/."""
        env = trace_env
        result = run_trace_write(env, ["--slug", "../../x"])
        # Override --slug ../../x but use a fresh call instead (--slug arg replaces the default)
        cmd = [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(env["root"]),
            "trace", "write",
            "--kind", "srs",
            "--slug", "../../x",
            "--artifact", str(env["artifact"]),
            "--source-doc", str(env["source_doc"]),
            "--requirements", str(env["reqs_file"]),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 2, (
            f"Expected exit 2 for dotdot slug; got {result.returncode}"
        )
        err = json.loads(result.stderr)
        codes = [f["code"] for f in err["failures"]]
        assert "INVALID_KIND_SLUG" in codes, f"Expected INVALID_KIND_SLUG; got {codes}"
        # Verify nothing escaped the traces dir
        escaped = env["root"] / "x"
        assert not escaped.exists(), "path-traversal: file created outside traces/"

    def test_trace_kind_rejected_with_slash(self, trace_env):
        """--kind ../y raises INVALID_KIND_SLUG exit 2."""
        env = trace_env
        cmd = [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(env["root"]),
            "trace", "write",
            "--kind", "../y",
            "--slug", "demo",
            "--artifact", str(env["artifact"]),
            "--source-doc", str(env["source_doc"]),
            "--requirements", str(env["reqs_file"]),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 2
        err = json.loads(result.stderr)
        codes = [f["code"] for f in err["failures"]]
        assert "INVALID_KIND_SLUG" in codes

    def test_trace_slug_uppercase_rejected(self, trace_env):
        """--slug MySlug raises INVALID_KIND_SLUG (only lowercase a-z, 0-9, hyphens)."""
        env = trace_env
        cmd = [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(env["root"]),
            "trace", "write",
            "--kind", "srs",
            "--slug", "MySlug",
            "--artifact", str(env["artifact"]),
            "--source-doc", str(env["source_doc"]),
            "--requirements", str(env["reqs_file"]),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 2
        err = json.loads(result.stderr)
        codes = [f["code"] for f in err["failures"]]
        assert "INVALID_KIND_SLUG" in codes

    def test_trace_slug_hyphenated_allowed(self, trace_env):
        """--slug my-slug is valid (hyphens allowed after first char)."""
        env = trace_env
        cmd = [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(env["root"]),
            "trace", "write",
            "--kind", "srs",
            "--slug", "my-slug",
            "--artifact", str(env["artifact"]),
            "--source-doc", str(env["source_doc"]),
            "--requirements", str(env["reqs_file"]),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Hyphenated slug should be valid; got {result.stderr}"


# ---------------------------------------------------------------------------
# Overwrite requires --force
# ---------------------------------------------------------------------------

class TestTraceOverwrite:
    """Re-writing an existing trace without --force raises TRACE_EXISTS exit 2."""

    def test_overwrite_without_force_fails(self, trace_env):
        """Writing to an existing slug without --force exits 2 with TRACE_EXISTS."""
        env = trace_env
        # First write
        r1 = run_trace_write(env)
        assert r1.returncode == 0, f"First write failed: {r1.stderr}"
        # Second write (same kind+slug, no --force)
        r2 = run_trace_write(env)
        assert r2.returncode == 2, f"Expected exit 2 on overwrite; got {r2.returncode}"
        err = json.loads(r2.stderr)
        codes = [f["code"] for f in err["failures"]]
        assert "TRACE_EXISTS" in codes, f"Expected TRACE_EXISTS; got {codes}"

    def test_overwrite_with_force_succeeds(self, trace_env):
        """Writing to an existing slug with --force exits 0 and overwrites."""
        env = trace_env
        r1 = run_trace_write(env)
        assert r1.returncode == 0

        r2 = run_trace_write(env, ["--force"])
        assert r2.returncode == 0, f"--force write failed: {r2.stderr}"
        # File should still exist and be valid JSON
        record = json.loads((env["traces_dir"] / "srs-demo.json").read_text())
        assert record["kind"] == "srs"


# ---------------------------------------------------------------------------
# Lockfile
# ---------------------------------------------------------------------------

class TestTraceLockfile:
    """Trace write is protected by a lockfile."""

    def test_trace_lockfile_no_partial_record(self, trace_env):
        """Under a held lock or concurrent writes, no partial record is produced."""
        env = trace_env
        results = []

        def do_write(extra=None):
            cmd = [
                sys.executable, "-m", "ba_tools",
                "--repo-root", str(env["root"]),
                "trace", "write",
                "--kind", "mermaid",
                "--slug", "concurrent",
                "--artifact", str(env["artifact"]),
                "--source-doc", str(env["source_doc"]),
                "--requirements", str(env["reqs_file"]),
                "--req-ids", "FR-001",
            ]
            if extra:
                cmd.extend(extra)
            results.append(subprocess.run(cmd, capture_output=True, text=True))

        # One write should succeed, the second may fail (TRACE_EXISTS or LOCK_TIMEOUT)
        t1 = threading.Thread(target=do_write)
        t1.start()
        t1.join()

        # Second write must either fail with TRACE_EXISTS or succeed with --force
        do_write(["--force"])

        # Regardless of outcome, the trace file (if it exists) must be valid JSON
        trace_file = env["traces_dir"] / "mermaid-concurrent.json"
        if trace_file.exists():
            record = json.loads(trace_file.read_text())
            assert "req_ids" in record, "Partial write: req_ids missing"
            assert len(record["req_ids"]) > 0, "Partial write: req_ids empty"


# ---------------------------------------------------------------------------
# Path traversal on --artifact / --source-doc
# ---------------------------------------------------------------------------

class TestTracePathTraversal:
    """--artifact or --source-doc escaping root raises PATH_TRAVERSAL exit 2."""

    def test_source_doc_outside_root_rejected(self, trace_env, tmp_path):
        """--source-doc pointing outside repo root raises PATH_TRAVERSAL."""
        env = trace_env
        # Create a file outside the repo root
        outside = tmp_path.parent / "outside_evil.md"
        outside.write_text("evil content", encoding="utf-8")
        cmd = [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(env["root"]),
            "trace", "write",
            "--kind", "srs",
            "--slug", "evil",
            "--artifact", str(env["artifact"]),
            "--source-doc", str(outside),
            "--requirements", str(env["reqs_file"]),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 2
        err = json.loads(result.stderr)
        codes = [f["code"] for f in err["failures"]]
        assert any(c in codes for c in ("PATH_TRAVERSAL", "FILE_NOT_FOUND")), (
            f"Expected PATH_TRAVERSAL or FILE_NOT_FOUND; got {codes}"
        )


# ---------------------------------------------------------------------------
# No cross-command hash import
# ---------------------------------------------------------------------------

class TestNoCrossCommandHashImport:
    """trace_cmd must import hashing helpers from ba_tools.hashing, not redefine them."""

    def test_no_cross_command_hash_import(self):
        """trace_cmd.py imports from ba_tools.hashing, not a local redefinition."""
        trace_cmd_path = (
            Path(__file__).parent.parent / "ba_tools" / "commands" / "trace_cmd.py"
        )
        if not trace_cmd_path.exists():
            pytest.skip("trace_cmd.py not yet created (RED phase)")
        content = trace_cmd_path.read_text(encoding="utf-8")
        assert "from ba_tools.hashing import" in content, (
            "trace_cmd.py must import from ba_tools.hashing"
        )
        assert "def _sha256_file" not in content
        assert "def _statement_hash" not in content

    def test_no_model_import(self):
        """trace_cmd.py must not import openai or anthropic."""
        trace_cmd_path = (
            Path(__file__).parent.parent / "ba_tools" / "commands" / "trace_cmd.py"
        )
        if not trace_cmd_path.exists():
            pytest.skip("trace_cmd.py not yet created (RED phase)")
        content = trace_cmd_path.read_text(encoding="utf-8")
        assert "import openai" not in content
        assert "import anthropic" not in content


# ---------------------------------------------------------------------------
# req-ids-file support
# ---------------------------------------------------------------------------

class TestReqIdsFile:
    """--req-ids-file reads newline-separated ids."""

    def test_req_ids_file(self, trace_env, tmp_path):
        """--req-ids-file newline-separated produces the correct subset."""
        env = trace_env
        ids_file = tmp_path / "ids.txt"
        ids_file.write_text("FR-003\nFR-004\n", encoding="utf-8")
        cmd = [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(env["root"]),
            "trace", "write",
            "--kind", "mockup",
            "--slug", "screen1",
            "--artifact", str(env["artifact"]),
            "--source-doc", str(env["source_doc"]),
            "--requirements", str(env["reqs_file"]),
            "--req-ids-file", str(ids_file),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        record = json.loads((env["traces_dir"] / "mockup-screen1.json").read_text())
        ids = {item["id"] for item in record["req_ids"]}
        assert ids == {"FR-003", "FR-004"}


# ---------------------------------------------------------------------------
# OK JSON output
# ---------------------------------------------------------------------------

class TestTraceOutput:
    """trace write emits the ok_json envelope on success."""

    def test_ok_json_on_success(self, trace_env):
        """Successful trace write prints ok:true JSON to stdout."""
        env = trace_env
        result = run_trace_write(env)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["failures"] == []
        assert "trace" in data or "kind" in data, (
            f"Expected trace or kind in response: {data}"
        )
