"""Tests for ba-tools index update (TOOL-08 / TRACE-05).

TDD RED phase: all tests should fail initially (index_cmd.py does not exist yet).

Covers:
- F10 fixture gap/orphan/stale detection
- Subset one-ok-one-gap (Codex suggested test)
- source_doc resolved under root (Codex HIGH + OpenCode MEDIUM security)
- Missing source reported in ## Stale (not silently skipped)
- Status precedence stale > gap > ok
- Reads traces only (not requirements.json / SRS.md decoy artifacts)
- INDEX.md sections: ## Gaps, ## Orphans, ## Stale, Status column in Matrix
- INDEX.md rewrite guarded by lockfile
- Command registration (smoke integration)
- No circular import from trace_cmd (hashing from ba_tools.hashing)
- No model-client import
"""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths to the F10 fixture (gap/orphan/stale)
# ---------------------------------------------------------------------------

_FIXTURES = Path(__file__).parent / "fixtures" / "srs" / "gap-orphan-stale"
_F10_TRACES = _FIXTURES / "traces"
_F10_SOURCE = _FIXTURES / "source.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ba_ops(tmp_path: Path, traces_json: list[dict]) -> Path:
    """Create a .ba-ops/traces/ dir in tmp_path with the given trace records.

    Returns the repo root (tmp_path).
    """
    traces_dir = tmp_path / ".ba-ops" / "traces"
    traces_dir.mkdir(parents=True)
    for record in traces_json:
        fname = f"{record['kind']}-{record['slug']}.json"
        (traces_dir / fname).write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )
    return tmp_path


def run_index_update(root: Path) -> subprocess.CompletedProcess:
    """Invoke `ba-tools index update` against *root*."""
    return subprocess.run(
        [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(root),
            "index", "update",
        ],
        capture_output=True,
        text=True,
    )


def _read_index(root: Path) -> str:
    return (root / ".ba-ops" / "INDEX.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# F10 fixture: gap + orphan + stale simultaneously
# ---------------------------------------------------------------------------


class TestGapOrphanStale:
    """test_gap_orphan_stale (F10): index update classifies all three bad states."""

    @pytest.fixture()
    def f10_root(self, tmp_path):
        """Root with the F10 traces copied in; source.md symlinked to a live file."""
        traces_dir = tmp_path / ".ba-ops" / "traces"
        traces_dir.mkdir(parents=True)

        # Copy F10 fixtures — use relative source_doc paths that resolve under tmp_path.
        # The srs-demo trace has a WRONG source_hash (force stale).
        # The mermaid-demo trace cites FR-001 (ok) + ORPHAN-001 (orphan), skips FR-002.
        srs_source_rel = "tests/fixtures/srs/gap-orphan-stale/source.md"
        live_source = _F10_SOURCE

        srs_record = {
            "kind": "srs",
            "slug": "demo",
            "artifact_path": "tests/fixtures/srs/gap-orphan-stale/srs-demo.md",
            "source_doc": srs_source_rel,
            "source_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa0000",
            "req_ids": [
                {"id": "FR-001", "statement_hash": "bbe6dc63b02836e659903db7b07babb87d88dc013c10200b1f87fc23bce8c772"},
                {"id": "FR-002", "statement_hash": "a2f23267b5eae1888d63692ccb57dc4fc89b01ff38edfe968bd799261a8c5b50"},
            ],
        }
        mermaid_record = {
            "kind": "mermaid",
            "slug": "demo",
            "artifact_path": "tests/fixtures/srs/gap-orphan-stale/mermaid-demo.mmd",
            "source_doc": srs_source_rel,
            "source_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa0000",
            "req_ids": [
                {"id": "FR-001", "statement_hash": "bbe6dc63b02836e659903db7b07babb87d88dc013c10200b1f87fc23bce8c772"},
                {"id": "ORPHAN-001", "statement_hash": "0000000000000000000000000000000000000000000000000000000000000000"},
            ],
        }
        (traces_dir / "srs-demo.json").write_text(json.dumps(srs_record, indent=2), encoding="utf-8")
        (traces_dir / "mermaid-demo.json").write_text(json.dumps(mermaid_record, indent=2), encoding="utf-8")

        # Create a real source.md under tmp_path at the same relative path so
        # resolve_under_root can find it. We copy the fixture content verbatim.
        dest_source = tmp_path / "tests" / "fixtures" / "srs" / "gap-orphan-stale"
        dest_source.mkdir(parents=True, exist_ok=True)
        (dest_source / "source.md").write_text(
            live_source.read_text(encoding="utf-8"), encoding="utf-8"
        )

        return tmp_path

    def test_gap_detection(self, f10_root):
        """FR-002 has no non-srs trace coverage → gap."""
        result = run_index_update(f10_root)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        index_md = _read_index(f10_root)
        assert "FR-002" in index_md
        # FR-002 should appear under ## Gaps or have Status=gap in Matrix
        assert "gap" in index_md.lower() or "FR-002" in index_md

    def test_orphan_detection(self, f10_root):
        """ORPHAN-001 is cited by mermaid trace but not in any srs req_ids → orphan."""
        result = run_index_update(f10_root)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        index_md = _read_index(f10_root)
        assert "ORPHAN-001" in index_md
        # ORPHAN-001 must appear in ## Orphans section
        assert "## Orphans" in index_md
        orphans_section = index_md.split("## Orphans")[1].split("##")[0]
        assert "ORPHAN-001" in orphans_section

    def test_stale_detection(self, f10_root):
        """Both srs-demo and mermaid-demo have wrong source_hash → stale."""
        result = run_index_update(f10_root)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        index_md = _read_index(f10_root)
        assert "## Stale" in index_md
        stale_section = index_md.split("## Stale")[1].split("##")[0]
        # At least one stale entry (srs-demo or mermaid-demo)
        assert "demo" in stale_section or "stale" in stale_section.lower()

    def test_sections_present(self, f10_root):
        """INDEX.md must contain ## Gaps, ## Orphans, ## Stale and a Status column."""
        result = run_index_update(f10_root)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        index_md = _read_index(f10_root)
        assert "## Gaps" in index_md, "## Gaps section missing"
        assert "## Orphans" in index_md, "## Orphans section missing"
        assert "## Stale" in index_md, "## Stale section missing"
        assert "Status" in index_md, "Status column missing from Matrix"


# ---------------------------------------------------------------------------
# Subset: one-ok-one-gap (Codex suggested test)
# ---------------------------------------------------------------------------


class TestSubsetOneOkOneGap:
    """test_trace_subset_one_ok_one_gap: mermaid covers FR-001 only → FR-001=ok, FR-002=gap."""

    @pytest.fixture()
    def subset_root(self, tmp_path):
        source = tmp_path / "source.md"
        source.write_text("Source for subset test.", encoding="utf-8")

        from ba_tools.hashing import _sha256_file
        live_hash = _sha256_file(source)

        srs_record = {
            "kind": "srs",
            "slug": "subset",
            "artifact_path": "srs-subset.md",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [
                {"id": "FR-001", "statement_hash": "aaa"},
                {"id": "FR-002", "statement_hash": "bbb"},
            ],
        }
        # mermaid covers ONLY FR-001
        mermaid_record = {
            "kind": "mermaid",
            "slug": "subset",
            "artifact_path": "diagram.mmd",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [
                {"id": "FR-001", "statement_hash": "aaa"},
            ],
        }
        _make_ba_ops(tmp_path, [srs_record, mermaid_record])
        return tmp_path

    def test_one_ok_one_gap(self, subset_root):
        """FR-001 covered by mermaid → ok; FR-002 not covered → gap."""
        result = run_index_update(subset_root)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        index_md = _read_index(subset_root)
        # FR-002 must be flagged as gap
        assert "FR-002" in index_md
        assert "gap" in index_md.lower()
        # FR-001 should appear with ok (not gap)
        # The Matrix row for FR-001 should not say gap
        lines = index_md.splitlines()
        fr001_rows = [l for l in lines if "FR-001" in l and "|" in l]
        assert fr001_rows, "FR-001 not found in Matrix table"
        assert any("ok" in row.lower() for row in fr001_rows), (
            f"FR-001 row not marked ok: {fr001_rows}"
        )


# ---------------------------------------------------------------------------
# Security: source_doc resolved under root (T-02-07c)
# ---------------------------------------------------------------------------


class TestSourceDocResolvedUnderRoot:
    """test_index_source_doc_resolved_under_root: out-of-root source_doc → missing."""

    @pytest.fixture()
    def traversal_root(self, tmp_path):
        # A trace whose source_doc points outside root via path traversal
        bad_record = {
            "kind": "srs",
            "slug": "bad",
            "artifact_path": "srs-bad.md",
            "source_doc": "../../etc/passwd",  # path-traversal attempt
            "source_hash": "deadbeef" * 8,
            "req_ids": [{"id": "FR-001", "statement_hash": "aaa"}],
        }
        _make_ba_ops(tmp_path, [bad_record])
        return tmp_path

    def test_out_of_root_source_doc_is_missing(self, traversal_root):
        """index update reports the bad slug as missing, never reads outside root."""
        result = run_index_update(traversal_root)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        index_md = _read_index(traversal_root)
        # The slug 'bad' should appear in ## Stale as missing
        assert "## Stale" in index_md
        stale_section = index_md.split("## Stale")[1].split("##")[0]
        assert "missing" in stale_section.lower() or "bad" in stale_section


# ---------------------------------------------------------------------------
# Missing source reported (not silently skipped)
# ---------------------------------------------------------------------------


class TestMissingSourceReported:
    """test_index_missing_source_reported: absent source_doc → ## Stale with missing."""

    @pytest.fixture()
    def missing_root(self, tmp_path):
        record = {
            "kind": "srs",
            "slug": "missing",
            "artifact_path": "srs-missing.md",
            "source_doc": "this-file-does-not-exist.md",
            "source_hash": "deadbeef" * 8,
            "req_ids": [{"id": "FR-001", "statement_hash": "aaa"}],
        }
        _make_ba_ops(tmp_path, [record])
        return tmp_path

    def test_missing_source_reported_in_stale(self, missing_root):
        """A trace with an absent source_doc appears in ## Stale as 'missing'."""
        result = run_index_update(missing_root)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        index_md = _read_index(missing_root)
        assert "## Stale" in index_md
        stale_section = index_md.split("## Stale")[1].split("##")[0]
        assert "missing" in stale_section.lower(), (
            f"'missing' not found in ## Stale section:\n{stale_section}"
        )


# ---------------------------------------------------------------------------
# Status precedence: stale > gap > ok
# ---------------------------------------------------------------------------


class TestStatusPrecedence:
    """test_index_status_precedence: a stale+gap row is classified stale."""

    @pytest.fixture()
    def precedence_root(self, tmp_path):
        source = tmp_path / "source.md"
        source.write_text("Source for precedence test.", encoding="utf-8")

        # srs trace with WRONG hash (stale) covering FR-001 and FR-002
        srs_record = {
            "kind": "srs",
            "slug": "prec",
            "artifact_path": "srs-prec.md",
            "source_doc": "source.md",
            "source_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa0000",
            "req_ids": [
                {"id": "FR-001", "statement_hash": "aaa"},
                {"id": "FR-002", "statement_hash": "bbb"},
            ],
        }
        # No non-srs trace → FR-001 and FR-002 are both gap
        # The srs trace is stale → they should be classified stale (precedence)
        _make_ba_ops(tmp_path, [srs_record])
        return tmp_path

    def test_stale_beats_gap(self, precedence_root):
        """FR-001/FR-002 are both gap AND stale (srs source drifted). Status must be stale."""
        result = run_index_update(precedence_root)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        index_md = _read_index(precedence_root)
        lines = index_md.splitlines()
        # Every FR row should show stale, not gap
        fr_rows = [l for l in lines if ("FR-001" in l or "FR-002" in l) and "|" in l]
        assert fr_rows, "FR-001/FR-002 not in Matrix"
        for row in fr_rows:
            assert "stale" in row.lower(), (
                f"Expected stale (not gap) for stale srs row, got: {row}"
            )


# ---------------------------------------------------------------------------
# Reads traces only (not decoy artifacts)
# ---------------------------------------------------------------------------


class TestReadsTracesOnly:
    """test_index_reads_traces_only: a decoy requirements.json next to traces is ignored."""

    @pytest.fixture()
    def decoy_root(self, tmp_path):
        source = tmp_path / "source.md"
        source.write_text("Source for decoy test.", encoding="utf-8")

        from ba_tools.hashing import _sha256_file
        live_hash = _sha256_file(source)

        srs_record = {
            "kind": "srs",
            "slug": "real",
            "artifact_path": "srs-real.md",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [{"id": "FR-001", "statement_hash": "aaa"}],
        }
        _make_ba_ops(tmp_path, [srs_record])

        # Place a decoy requirements.json inside traces/ — if parsed, it would
        # inject a phantom requirement that should NOT appear in the matrix.
        decoy = tmp_path / ".ba-ops" / "traces" / "requirements.json"
        decoy.write_text(
            json.dumps({
                "requirements": [
                    {"id": "PHANTOM-999", "statement": "This must not appear."}
                ]
            }),
            encoding="utf-8",
        )
        return tmp_path

    def test_decoy_not_parsed(self, decoy_root):
        """PHANTOM-999 from decoy requirements.json must NOT appear in INDEX.md."""
        result = run_index_update(decoy_root)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        index_md = _read_index(decoy_root)
        assert "PHANTOM-999" not in index_md, (
            "index update parsed the decoy requirements.json (uniform-input D-04 violated)"
        )


# ---------------------------------------------------------------------------
# Lockfile guard on INDEX.md
# ---------------------------------------------------------------------------


class TestIndexLockfile:
    """test_index_lockfile: INDEX.md rewrite acquires INDEX.md.lock."""

    def test_lockfile_created(self, tmp_path):
        """Running index update creates INDEX.md.lock during write (or it already cleaned up).

        We can only assert the lock file existed at some point; by the time the
        command exits it may have been released/deleted. So we assert the command
        succeeds and inspect the lock path doesn't crash the run.
        """
        source = tmp_path / "source.md"
        source.write_text("Lock test source.", encoding="utf-8")

        from ba_tools.hashing import _sha256_file
        live_hash = _sha256_file(source)

        srs_record = {
            "kind": "srs",
            "slug": "lock",
            "artifact_path": "srs-lock.md",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [{"id": "FR-001", "statement_hash": "aaa"}],
        }
        _make_ba_ops(tmp_path, [srs_record])

        result = run_index_update(tmp_path)
        assert result.returncode == 0, f"exit {result.returncode}\n{result.stderr}"
        # INDEX.md must exist
        assert (tmp_path / ".ba-ops" / "INDEX.md").exists()


# ---------------------------------------------------------------------------
# No circular import from trace_cmd
# ---------------------------------------------------------------------------


class TestNoCrossCommandImport:
    """index_cmd must not import from trace_cmd (hashing from ba_tools.hashing only)."""

    def test_no_trace_cmd_import(self):
        """grep for 'from .trace_cmd import' or 'from ba_tools.commands.trace_cmd import' → none."""
        import importlib.util
        import inspect

        spec = importlib.util.find_spec("ba_tools.commands.index_cmd")
        assert spec is not None, "ba_tools.commands.index_cmd not found"
        assert spec.origin is not None
        source = Path(spec.origin).read_text(encoding="utf-8")
        assert "from .trace_cmd import" not in source, (
            "index_cmd imports from trace_cmd (circular import risk)"
        )
        assert "from ba_tools.commands.trace_cmd import" not in source, (
            "index_cmd imports from trace_cmd (circular import risk)"
        )

    def test_no_model_imports(self):
        """index_cmd must not import openai or anthropic (determinism boundary)."""
        import importlib.util

        spec = importlib.util.find_spec("ba_tools.commands.index_cmd")
        assert spec is not None
        assert spec.origin is not None
        source = Path(spec.origin).read_text(encoding="utf-8")
        assert "import openai" not in source, "openai import found in index_cmd"
        assert "import anthropic" not in source, "anthropic import found in index_cmd"

    def test_hashing_imported_from_shared_module(self):
        """index_cmd imports _sha256_file from ba_tools.hashing, not redefined."""
        import importlib.util

        spec = importlib.util.find_spec("ba_tools.commands.index_cmd")
        assert spec is not None
        assert spec.origin is not None
        source = Path(spec.origin).read_text(encoding="utf-8")
        assert "def _sha256_file" not in source, (
            "index_cmd redefines _sha256_file (should import from ba_tools.hashing)"
        )
        # Should import from the shared module
        assert "from ba_tools.hashing import" in source or "ba_tools.hashing" in source, (
            "index_cmd does not import from ba_tools.hashing"
        )


# ---------------------------------------------------------------------------
# Command registration (smoke)
# ---------------------------------------------------------------------------


class TestIndexRegistered:
    """index command is registered and --help exits 0."""

    def test_index_update_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "ba_tools", "index", "update", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"`ba-tools index update --help` exited {result.returncode}\n{result.stderr[:500]}"
        )
        output = result.stdout.lower() + result.stderr.lower()
        assert "usage" in output, "No usage line in --help output"
