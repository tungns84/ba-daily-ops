"""Integration test: mockup req_ids → INDEX.md mockup column, no orphans (MOCK-02 / criterion 2+3).

Covers:
- TestReqIdsAppearInIndexMockupColumn.test_req_ids_appear_in_index_mockup_column:
    After trace write --kind mockup + index update, a cited REQ-ID (FR-001)
    has status=ok in INDEX.md (not gap), and the Orphans section does NOT list FR-001.
- TestNoOrphansForRealIds.test_no_orphans_for_real_ids:
    With all cited IDs present in requirements.json, the INDEX ## Orphans section
    is "(none)" — no orphan introduced (criterion 2).
- TestInventedIdSurfacesAsOrphan.test_invented_id_surfaces_as_orphan:
    When the mockup trace cites an ID absent from requirements.json (FR-999),
    index update lists FR-999 under ## Orphans (D-06 downstream validation).

Design contract:
- This test CONSUMES trace write + index update as-is (no mocks, no edits to trace_cmd.py /
  index_cmd.py). Per D-06 (orphan): validation is downstream only — trace write records
  whatever it is given; index update flags orphans.
- Column header: "| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |"
  (from index_cmd.py line 213)
- Orphans section: "## Orphans" marker; body is "- {id}" per orphan or "(none)" if empty
  (from index_cmd.py lines 188-192)
- Status values: ok | gap | stale (from index_cmd.py req_status classification)
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixture file
# ---------------------------------------------------------------------------

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mockup"
_INDEX_REQS_FIXTURE = _FIXTURE_DIR / "mockup_requirements.json"

# Column / section markers read from index_cmd.py — do NOT hard-code guesses
_MATRIX_HEADER = "| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |"
_ORPHANS_SECTION = "## Orphans"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PYTHON = sys.executable


def _run(*args: str, root: Path) -> subprocess.CompletedProcess:
    """Run ba-tools with --repo-root set to *root*."""
    return subprocess.run(
        [PYTHON, "-m", "ba_tools", "--repo-root", str(root), *args],
        capture_output=True,
        text=True,
    )


def _read_index(root: Path) -> str:
    return (root / ".ba-ops" / "INDEX.md").read_text(encoding="utf-8")


def _orphans_body(index_md: str) -> str:
    """Return the text between ## Orphans and the next ## heading (or end of file)."""
    parts = index_md.split(_ORPHANS_SECTION, 1)
    assert len(parts) == 2, f"## Orphans section not found in INDEX.md:\n{index_md}"
    after = parts[1]
    # Trim to the next ## heading (or EOF)
    next_section = after.find("\n##")
    if next_section != -1:
        return after[:next_section]
    return after


def _matrix_rows(index_md: str) -> list[str]:
    """Return the data rows of the Matrix table (excluding header and separator)."""
    rows = []
    in_matrix = False
    for line in index_md.splitlines():
        if _MATRIX_HEADER in line:
            in_matrix = True
            continue
        if in_matrix:
            stripped = line.strip()
            if not stripped or not stripped.startswith("|"):
                # End of table
                in_matrix = False
                continue
            # Skip separator row (contains dashes)
            if all(c in "|- " for c in stripped):
                continue
            rows.append(stripped)
    return rows


# ---------------------------------------------------------------------------
# Fixture: build a tmp repo with SRS trace + mockup screen artifact
# ---------------------------------------------------------------------------


@pytest.fixture()
def trace_index_env(tmp_path):
    """Minimal repo for mockup trace → index integration tests.

    Layout:
      tmp_path/
        .ba-ops/
          srs/test-diagram/        (SRS directory)
            requirements.json      (copied from fixtures/mockup/mockup_requirements.json)
            requirements.md        (SRS artifact for trace write --kind srs)
          mockup/test-diagram/     (mockup artifact directory)
            screen.html            (html-fidelity mockup with req_ids comment first line)
        source.md                  (source document for SRS trace)
    """
    slug = "test-diagram"

    # SRS directories
    srs_dir = tmp_path / ".ba-ops" / "srs" / slug
    srs_dir.mkdir(parents=True)

    # Copy requirements fixture
    reqs_dst = srs_dir / "requirements.json"
    shutil.copy(_INDEX_REQS_FIXTURE, reqs_dst)

    # Source document (sha256-anchored to track SRS state)
    source_doc = tmp_path / "source.md"
    source_doc.write_text(
        "# Source\n\nFR-001: The system shall record artifact provenance via trace records.\n"
        "FR-002: The system shall detect stale artifacts via source_hash comparison.\n",
        encoding="utf-8",
    )

    # Mockup html artifact with req_ids comment on first line (citing FR-001 only)
    mockup_dir = tmp_path / ".ba-ops" / "mockup" / slug
    mockup_dir.mkdir(parents=True)
    mockup_artifact = mockup_dir / "screen.html"
    mockup_artifact.write_text(
        "<!-- req_ids: [FR-001] -->\n"
        "<!DOCTYPE html>\n"
        "<html lang='en'><head><title>Screen</title></head>"
        "<body><main><p>Test screen</p></main></body></html>\n",
        encoding="utf-8",
    )

    # SRS artifact file (needed by trace write --artifact)
    srs_artifact = srs_dir / "requirements.md"
    srs_artifact.write_text("# SRS\n", encoding="utf-8")

    return {
        "root": tmp_path,
        "slug": slug,
        "reqs_file": reqs_dst,
        "source_doc": source_doc,
        "mockup_artifact": mockup_artifact,
        "srs_artifact": srs_artifact,
    }


# ---------------------------------------------------------------------------
# Helper: write SRS trace first (required for index update to know valid REQ-IDs)
# ---------------------------------------------------------------------------


def _write_srs_trace(env: dict, *, force: bool = False) -> subprocess.CompletedProcess:
    """Run trace write --kind srs to establish the valid REQ-ID set for index update."""
    root = env["root"]
    args = [
        "trace", "write",
        "--kind", "srs",
        "--slug", env["slug"],
        "--artifact", str(env["srs_artifact"]),
        "--source-doc", str(env["source_doc"]),
        "--requirements", str(env["reqs_file"]),
    ]
    if force:
        args.append("--force")
    return _run(*args, root=root)


def _write_mockup_trace(
    env: dict,
    req_ids: str,
    *,
    force: bool = False,
) -> subprocess.CompletedProcess:
    """Run trace write --kind mockup with the given comma-separated req_ids.

    Note: --source-doc is requirements.json (NOT the mockup artifact itself).
    This pins source_hash to the SRS for drift detection (D-06 / ba-mermaid.md Step 2 note).
    """
    root = env["root"]
    args = [
        "trace", "write",
        "--kind", "mockup",
        "--slug", env["slug"],
        "--artifact", str(env["mockup_artifact"]),
        "--source-doc", str(env["reqs_file"]),
        "--requirements", str(env["reqs_file"]),
        "--req-ids", req_ids,
    ]
    if force:
        args.append("--force")
    return _run(*args, root=root)


def _run_index_update(env: dict) -> subprocess.CompletedProcess:
    """Run index update."""
    return _run("index", "update", root=env["root"])


# ---------------------------------------------------------------------------
# Test 1: req_ids appear in INDEX mockup column (status=ok) — criterion 2
# ---------------------------------------------------------------------------


class TestReqIdsAppearInIndexMockupColumn:
    """After trace write --kind mockup + index update, cited REQ-IDs have status=ok."""

    def test_req_ids_appear_in_index_mockup_column(self, trace_index_env):
        """FR-001 cited in mockup trace → status=ok in INDEX.md; NOT in ## Orphans.

        Steps:
          1. Write SRS trace (establishes valid REQ-ID set: FR-001, FR-002).
          2. Write mockup trace --req-ids FR-001.
          3. Run index update.
          4. Assert: FR-001's Matrix row has status=ok (mockup trace covers it).
          5. Assert: ## Orphans section does NOT contain FR-001.
        """
        env = trace_index_env

        # Step 1: SRS trace
        r_srs = _write_srs_trace(env)
        assert r_srs.returncode == 0, f"SRS trace failed: {r_srs.stderr}"

        # Step 2: mockup trace for FR-001 only
        r_mock = _write_mockup_trace(env, "FR-001")
        assert r_mock.returncode == 0, f"Mockup trace failed: {r_mock.stderr}"

        # Step 3: index update
        r_idx = _run_index_update(env)
        assert r_idx.returncode == 0, f"Index update failed: {r_idx.stderr}"

        # Step 4: FR-001 Matrix row must be status=ok
        index_md = _read_index(env["root"])
        assert _MATRIX_HEADER in index_md, (
            f"Matrix header not found in INDEX.md:\n{index_md[:500]}"
        )
        rows = _matrix_rows(index_md)
        fr001_rows = [r for r in rows if "FR-001" in r]
        assert fr001_rows, f"FR-001 not found in INDEX Matrix rows: {rows}"
        fr001_row = fr001_rows[0]
        assert "ok" in fr001_row.lower(), (
            f"FR-001 expected status=ok after mockup trace; got: {fr001_row}"
        )
        assert "gap" not in fr001_row.lower(), (
            f"FR-001 must not be gap when mockup trace covers it; got: {fr001_row}"
        )

        # Step 5: Orphans section must NOT contain FR-001
        orphans = _orphans_body(index_md)
        assert "FR-001" not in orphans, (
            f"FR-001 (a real ID) must not appear in ## Orphans; orphans body:\n{orphans}"
        )


# ---------------------------------------------------------------------------
# Test 2: no orphans introduced when all cited IDs are real — criterion 2
# ---------------------------------------------------------------------------


class TestNoOrphansForRealIds:
    """With only real IDs cited, ## Orphans section is (none) — criterion 2."""

    def test_no_orphans_for_real_ids(self, trace_index_env):
        """FR-001 and FR-002 are both in requirements.json → no orphans after index update."""
        env = trace_index_env

        # SRS trace
        r_srs = _write_srs_trace(env)
        assert r_srs.returncode == 0, f"SRS trace failed: {r_srs.stderr}"

        # Mockup trace citing BOTH FR-001 and FR-002 (all real IDs)
        r_mock = _write_mockup_trace(env, "FR-001,FR-002")
        assert r_mock.returncode == 0, f"Mockup trace failed: {r_mock.stderr}"

        # Index update
        r_idx = _run_index_update(env)
        assert r_idx.returncode == 0, f"Index update failed: {r_idx.stderr}"

        # ## Orphans section must be (none)
        index_md = _read_index(env["root"])
        orphans = _orphans_body(index_md)
        assert "(none)" in orphans, (
            f"Expected ## Orphans to contain '(none)' when all IDs are real; "
            f"orphans body:\n{orphans}"
        )
        # Double-check: neither ID appears as orphan
        assert "FR-001" not in orphans, "FR-001 must not be an orphan"
        assert "FR-002" not in orphans, "FR-002 must not be an orphan"


# ---------------------------------------------------------------------------
# Test 3: invented ID surfaces as orphan (D-06 downstream validation)
# ---------------------------------------------------------------------------


class TestInventedIdSurfacesAsOrphan:
    """An invented REQ-ID (FR-999) cited in the mockup trace → listed under ## Orphans."""

    def test_invented_id_surfaces_as_orphan(self, trace_index_env):
        """FR-999 is absent from requirements.json → index update lists it under ## Orphans.

        D-06 contract: trace write accepts any ID without validation; index update is the
        reconciliation point that flags unknown IDs as orphans.
        """
        env = trace_index_env

        # SRS trace (FR-001, FR-002 are the valid set)
        r_srs = _write_srs_trace(env)
        assert r_srs.returncode == 0, f"SRS trace failed: {r_srs.stderr}"

        # Mockup trace citing FR-001 (real) + FR-999 (invented — not in requirements.json)
        r_mock = _write_mockup_trace(env, "FR-001,FR-999")
        assert r_mock.returncode == 0, (
            f"Mockup trace write must succeed (trace records what it receives, no "
            f"validation per D-06): {r_mock.stderr}"
        )

        # Index update
        r_idx = _run_index_update(env)
        assert r_idx.returncode == 0, f"Index update failed: {r_idx.stderr}"

        # FR-999 must appear under ## Orphans
        index_md = _read_index(env["root"])
        assert _ORPHANS_SECTION in index_md, (
            f"## Orphans section not found in INDEX.md:\n{index_md[:500]}"
        )
        orphans = _orphans_body(index_md)
        assert "FR-999" in orphans, (
            f"FR-999 (invented ID) must appear in ## Orphans section; "
            f"orphans body:\n{orphans}"
        )
        assert "(none)" not in orphans, (
            "## Orphans must not be (none) when FR-999 is an orphan"
        )

        # FR-001 (real ID, covered) must NOT be in Orphans
        assert "FR-001" not in orphans, (
            "FR-001 is real and must not appear in ## Orphans"
        )


# ---------------------------------------------------------------------------
# Structural: verify INDEX.md column markers match index_cmd.py contract
# ---------------------------------------------------------------------------


class TestIndexMdStructure:
    """Verify the literal column/section markers used in this test match index_cmd.py."""

    def test_matrix_header_in_index_cmd(self):
        """The Matrix header string matches the one emitted by index_cmd.py."""
        index_cmd_path = (
            Path(__file__).parent.parent / "ba_tools" / "commands" / "index_cmd.py"
        )
        assert index_cmd_path.exists(), f"index_cmd.py not found: {index_cmd_path}"
        source = index_cmd_path.read_text(encoding="utf-8")
        # The header row must appear verbatim in index_cmd.py
        assert _MATRIX_HEADER in source, (
            f"Matrix header {_MATRIX_HEADER!r} not found in index_cmd.py — "
            "test string is out of sync with implementation"
        )

    def test_orphans_section_marker_in_index_cmd(self):
        """The ## Orphans section marker matches index_cmd.py output."""
        index_cmd_path = (
            Path(__file__).parent.parent / "ba_tools" / "commands" / "index_cmd.py"
        )
        assert index_cmd_path.exists(), f"index_cmd.py not found: {index_cmd_path}"
        source = index_cmd_path.read_text(encoding="utf-8")
        assert _ORPHANS_SECTION in source, (
            f"Section marker {_ORPHANS_SECTION!r} not found in index_cmd.py — "
            "test string is out of sync with implementation"
        )

    def test_fixture_has_required_ids(self):
        """The fixture mockup_requirements.json has FR-001 and FR-002."""
        assert _INDEX_REQS_FIXTURE.exists(), (
            f"Fixture not found: {_INDEX_REQS_FIXTURE}"
        )
        payload = json.loads(_INDEX_REQS_FIXTURE.read_text(encoding="utf-8"))
        reqs = payload.get("requirements", [])
        ids = {r["id"] for r in reqs if isinstance(r, dict) and "id" in r}
        assert "FR-001" in ids, f"FR-001 not in fixture requirements: {ids}"
        assert "FR-002" in ids, f"FR-002 not in fixture requirements: {ids}"
