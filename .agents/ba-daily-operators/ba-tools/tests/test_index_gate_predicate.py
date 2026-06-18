"""D-G2 index-integrity predicate tests (UC-03, GATE-03).

Tests the index gate predicate that the ba-uc conductor applies after each
mermaid and mockup step (D-G2 from CONTEXT.md + RESEARCH.md Q2):

  FAIL if:
    len(index_update_output["orphans"]) > 0          # new orphan from this step
    OR
    any(rid in index_update_output["gaps"]            # step's own req_ids not covered
        for rid in step_trace_req_ids)

These tests drive `ba-tools index update` via subprocess and parse the JSON output.
They rely ONLY on the emitted `orphans` and `gaps` fields — NOT on any `covered_by`
field (RESEARCH confirms covered_by is computed internally and NOT emitted in ok_json).

All scaffold helpers are written inline (no cross-module imports).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers — inline (no cross-module imports)
# ---------------------------------------------------------------------------


def _make_trace_records(tmp_path: Path, records: list[dict]) -> Path:
    """Create .ba-ops/traces/ with the given trace records.

    Returns tmp_path (repo root).
    """
    traces_dir = tmp_path / ".ba-ops" / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        fname = f"{record['kind']}-{record['slug']}.json"
        (traces_dir / fname).write_text(
            json.dumps(record, indent=2), encoding="utf-8"
        )
    return tmp_path


def _run_index_update(root: Path) -> subprocess.CompletedProcess:
    """Invoke `ba-tools index update` against *root*."""
    return subprocess.run(
        [
            sys.executable, "-m", "ba_tools",
            "--repo-root", str(root),
            "index", "update",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _make_source(root: Path, rel_path: str = "source.md") -> tuple[Path, str]:
    """Write a minimal source.md under root and return (path, sha256_hex).

    Imports _sha256_file from ba_tools.hashing (same pattern as test_index.py).
    """
    from ba_tools.hashing import _sha256_file

    source = root / rel_path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Source\n\nFR-001: The system shall trace.\nFR-002: The system shall index.\n", encoding="utf-8")
    return source, _sha256_file(source)


# ---------------------------------------------------------------------------
# D-G2 predicate helper — encode the exact predicate from RESEARCH Q2
# ---------------------------------------------------------------------------


def _d_g2_passes(index_json: dict, step_req_ids: list[str]) -> bool:
    """Return True iff the D-G2 index-integrity predicate PASSes.

    PASS condition:
      orphans == []  AND  none of step_req_ids appear in gaps

    FAIL condition (any one is enough):
      len(orphans) > 0  OR  any(rid in gaps for rid in step_req_ids)

    This is the exact predicate from RESEARCH.md Q2.
    Reads ONLY 'orphans' and 'gaps' from the index update JSON output.
    Does NOT rely on 'covered_by' (not emitted by index_cmd.py ok_json).
    """
    orphans = index_json.get("orphans", [])
    gaps = index_json.get("gaps", [])
    return len(orphans) == 0 and not any(rid in gaps for rid in step_req_ids)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIndexGateNoOrphans:
    """test_index_gate_no_orphans_after_mermaid_trace.

    Seed:
      - SRS trace: req_ids = [FR-001, FR-002]
      - Mermaid trace: req_ids = [FR-001]

    Expected after index update:
      - orphans == [] (FR-001 is in srs traces; XX-* not cited)
      - FR-001 NOT in gaps (mermaid covers it)
      - D-G2 PASSes for mermaid step (step_req_ids=[FR-001])
    """

    @pytest.fixture()
    def clean_root(self, tmp_path):
        source, live_hash = _make_source(tmp_path)

        srs_record = {
            "kind": "srs",
            "slug": "uc001",
            "artifact_path": "srs-uc001.md",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [
                {"id": "FR-001", "statement_hash": "aaa"},
                {"id": "FR-002", "statement_hash": "bbb"},
            ],
        }
        mermaid_record = {
            "kind": "mermaid",
            "slug": "uc001",
            "artifact_path": "mermaid-uc001.mmd",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [
                {"id": "FR-001", "statement_hash": "aaa"},
            ],
        }
        return _make_trace_records(tmp_path, [srs_record, mermaid_record])

    def test_no_orphans(self, clean_root):
        """After srs + mermaid trace, orphans must be empty."""
        result = _run_index_update(clean_root)
        assert result.returncode == 0, f"index update exited {result.returncode}: {result.stderr}"
        payload = json.loads(result.stdout)
        assert payload["ok"] is True
        assert payload["orphans"] == [], (
            f"No orphans expected after valid mermaid trace, got: {payload['orphans']}"
        )

    def test_fr001_not_in_gaps(self, clean_root):
        """FR-001, covered by mermaid trace, must NOT appear in gaps."""
        result = _run_index_update(clean_root)
        assert result.returncode == 0, f"index update exited {result.returncode}: {result.stderr}"
        payload = json.loads(result.stdout)
        assert "FR-001" not in payload["gaps"], (
            f"FR-001 is covered by the mermaid trace — must not be in gaps. "
            f"gaps={payload['gaps']}"
        )

    def test_d_g2_passes_for_mermaid_step(self, clean_root):
        """D-G2 predicate PASSes for the mermaid step (step_req_ids=[FR-001])."""
        result = _run_index_update(clean_root)
        assert result.returncode == 0, f"index update exited {result.returncode}: {result.stderr}"
        payload = json.loads(result.stdout)

        step_req_ids = ["FR-001"]  # req_ids written by the mermaid trace
        assert _d_g2_passes(payload, step_req_ids), (
            f"D-G2 must PASS for mermaid step. "
            f"orphans={payload['orphans']}, gaps={payload['gaps']}, "
            f"step_req_ids={step_req_ids}"
        )


class TestIndexGateOrphanDetected:
    """test_index_gate_orphan_detected.

    Seed:
      - SRS trace: req_ids = [FR-001, FR-002]
      - Mermaid trace: req_ids = [XX-999] (absent from srs traces)

    Expected after index update:
      - 'XX-999' in orphans (cited by non-srs but not in srs req_ids)
      - D-G2 FAILs for the mermaid step (step_req_ids=[XX-999])
    """

    @pytest.fixture()
    def orphan_root(self, tmp_path):
        source, live_hash = _make_source(tmp_path)

        srs_record = {
            "kind": "srs",
            "slug": "uc001",
            "artifact_path": "srs-uc001.md",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [
                {"id": "FR-001", "statement_hash": "aaa"},
                {"id": "FR-002", "statement_hash": "bbb"},
            ],
        }
        mermaid_record = {
            "kind": "mermaid",
            "slug": "uc001-bad",
            "artifact_path": "mermaid-uc001-bad.mmd",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [
                {"id": "XX-999", "statement_hash": "000"},
            ],
        }
        return _make_trace_records(tmp_path, [srs_record, mermaid_record])

    def test_orphan_detected(self, orphan_root):
        """XX-999 is cited by mermaid but absent from srs traces — must appear in orphans."""
        result = _run_index_update(orphan_root)
        assert result.returncode == 0, f"index update exited {result.returncode}: {result.stderr}"
        payload = json.loads(result.stdout)
        assert payload["ok"] is True
        assert "XX-999" in payload["orphans"], (
            f"XX-999 cited by mermaid trace but absent from srs — must be in orphans. "
            f"orphans={payload['orphans']}"
        )

    def test_d_g2_fails_on_orphan(self, orphan_root):
        """D-G2 predicate FAILs because the mermaid step introduced an orphan."""
        result = _run_index_update(orphan_root)
        assert result.returncode == 0, f"index update exited {result.returncode}: {result.stderr}"
        payload = json.loads(result.stdout)

        step_req_ids = ["XX-999"]  # what the mermaid trace wrote
        assert not _d_g2_passes(payload, step_req_ids), (
            f"D-G2 must FAIL because XX-999 is an orphan. "
            f"orphans={payload['orphans']}, gaps={payload['gaps']}"
        )


class TestIndexGateSelfCoveragePredicate:
    """test_index_gate_self_coverage_predicate.

    Encodes the FAIL path for the second clause of D-G2:
      any(rid in gaps for rid in step_req_ids)

    Seed: SRS trace with FR-001 + FR-002, NO mermaid trace at all.
    Step req_ids claimed by the mermaid step = [FR-001, FR-002].
    Expected: both appear in gaps → D-G2 FAILs (step's req_ids not covered).

    Also tests the PASS path with the covered fixture from TestIndexGateNoOrphans.
    """

    @pytest.fixture()
    def gaps_root(self, tmp_path):
        """SRS trace only — no mermaid trace → FR-001, FR-002 will be in gaps."""
        source, live_hash = _make_source(tmp_path)

        srs_record = {
            "kind": "srs",
            "slug": "uc001",
            "artifact_path": "srs-uc001.md",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [
                {"id": "FR-001", "statement_hash": "aaa"},
                {"id": "FR-002", "statement_hash": "bbb"},
            ],
        }
        return _make_trace_records(tmp_path, [srs_record])

    @pytest.fixture()
    def covered_root(self, tmp_path):
        """SRS + mermaid traces where mermaid covers FR-001."""
        source, live_hash = _make_source(tmp_path)

        srs_record = {
            "kind": "srs",
            "slug": "uc001",
            "artifact_path": "srs-uc001.md",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [
                {"id": "FR-001", "statement_hash": "aaa"},
            ],
        }
        mermaid_record = {
            "kind": "mermaid",
            "slug": "uc001",
            "artifact_path": "mermaid-uc001.mmd",
            "source_doc": "source.md",
            "source_hash": live_hash,
            "req_ids": [
                {"id": "FR-001", "statement_hash": "aaa"},
            ],
        }
        return _make_trace_records(tmp_path, [srs_record, mermaid_record])

    def test_self_coverage_predicate_fail_on_gaps(self, gaps_root):
        """D-G2 FAILs when step's own req_ids appear in gaps (no downstream trace)."""
        result = _run_index_update(gaps_root)
        assert result.returncode == 0, f"index update exited {result.returncode}: {result.stderr}"
        payload = json.loads(result.stdout)

        # Mermaid step claims to have covered FR-001 + FR-002 but wrote no trace
        step_req_ids = ["FR-001", "FR-002"]

        # Verify the gaps list contains both (precondition for the predicate test)
        for rid in step_req_ids:
            assert rid in payload["gaps"], (
                f"{rid} must be in gaps (no mermaid trace written), got gaps={payload['gaps']}"
            )

        # The predicate must FAIL — step req_ids ARE in gaps
        assert not _d_g2_passes(payload, step_req_ids), (
            f"D-G2 must FAIL when step's req_ids are in gaps. "
            f"orphans={payload['orphans']}, gaps={payload['gaps']}, "
            f"step_req_ids={step_req_ids}"
        )

    def test_self_coverage_predicate_pass_on_covered(self, covered_root):
        """D-G2 PASSes when step's own req_ids are covered (not in gaps) and no orphans."""
        result = _run_index_update(covered_root)
        assert result.returncode == 0, f"index update exited {result.returncode}: {result.stderr}"
        payload = json.loads(result.stdout)

        step_req_ids = ["FR-001"]  # what the mermaid step wrote to its trace

        # Precondition: no orphans and FR-001 is not in gaps
        assert payload["orphans"] == [], f"No orphans expected, got {payload['orphans']}"
        assert "FR-001" not in payload["gaps"], (
            f"FR-001 covered by mermaid trace must not be in gaps, got {payload['gaps']}"
        )

        # The predicate must PASS
        assert _d_g2_passes(payload, step_req_ids), (
            f"D-G2 must PASS when orphans==[] and step req_ids are covered. "
            f"orphans={payload['orphans']}, gaps={payload['gaps']}, "
            f"step_req_ids={step_req_ids}"
        )
