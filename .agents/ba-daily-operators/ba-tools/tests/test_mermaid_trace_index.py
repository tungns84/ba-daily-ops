"""Integration test: mermaid req_ids → INDEX.md mermaid column, no orphans (MMD-02 / criterion 2).

Covers:
- test_req_ids_appear_in_index_mermaid_column:
    After trace write --kind mermaid + index update, a cited REQ-ID (FR-001)
    has status=ok in INDEX.md (not gap), and the Orphans section does NOT list FR-001.
- test_no_orphans_for_real_ids:
    With all cited IDs present in requirements.json, the INDEX ## Orphans section
    is "(none)" — no orphan introduced (criterion 2).
- test_invented_id_surfaces_as_orphan:
    When the mermaid trace cites an ID absent from requirements.json (FR-999),
    index update lists FR-999 under ## Orphans (D-05 downstream validation).

Design contract:
- This test CONSUMES trace write + index update as-is (no mocks, no edits to trace_cmd.py /
  index_cmd.py). Per D-05 (orphan): validation is downstream only — trace write records
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

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "mermaid"
_INDEX_REQS_FIXTURE = _FIXTURE_DIR / "index_requirements.json"

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
# Fixture: build a tmp repo with SRS trace + mermaid diagram
# ---------------------------------------------------------------------------


@pytest.fixture()
def trace_index_env(tmp_path):
    """Minimal repo for mermaid trace → index integration tests.

    Layout:
      tmp_path/
        .ba-ops/
          srs/test-diagram/        (SRS directory)
            requirements.json      (copied from fixtures/mermaid/index_requirements.json)
          mermaid/test-diagram/    (mermaid artifact directory)
            diagram.md             (inline mermaid block + req_ids frontmatter)
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

    # Mermaid diagram .md artifact with req_ids frontmatter (citing FR-001 only)
    mermaid_dir = tmp_path / ".ba-ops" / "mermaid" / slug
    mermaid_dir.mkdir(parents=True)
    diagram_md = mermaid_dir / "diagram.md"
    diagram_md.write_text(
        "---\n"
        "req_ids: [FR-001]\n"
        "diagram_type: flowchart\n"
        f"slug: {slug}\n"
        "---\n\n"
        "# Order Processing\n\n"
        "```mermaid\n"
        "flowchart TD\n"
        "    A[Start] --> B[End]\n"
        "```\n",
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
        "diagram_md": diagram_md,
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


def _write_mermaid_trace(
    env: dict,
    req_ids: str,
    *,
    force: bool = False,
) -> subprocess.CompletedProcess:
    """Run trace write --kind mermaid with the given comma-separated req_ids."""
    root = env["root"]
    args = [
        "trace", "write",
        "--kind", "mermaid",
        "--slug", env["slug"],
        "--artifact", str(env["diagram_md"]),
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
# Test 1: req_ids appear in INDEX mermaid column (status=ok) — criterion 2
# ---------------------------------------------------------------------------


class TestReqIdsAppearInIndexMermaidColumn:
    """After trace write --kind mermaid + index update, cited REQ-IDs have status=ok."""

    def test_req_ids_appear_in_index_mermaid_column(self, trace_index_env):
        """FR-001 cited in mermaid trace → status=ok in INDEX.md; NOT in ## Orphans.

        Steps:
          1. Write SRS trace (establishes valid REQ-ID set: FR-001, FR-002).
          2. Write mermaid trace --req-ids FR-001.
          3. Run index update.
          4. Assert: FR-001's Matrix row has status=ok (mermaid trace covers it).
          5. Assert: ## Orphans section does NOT contain FR-001.
        """
        env = trace_index_env

        # Step 1: SRS trace
        r_srs = _write_srs_trace(env)
        assert r_srs.returncode == 0, f"SRS trace failed: {r_srs.stderr}"

        # Step 2: mermaid trace for FR-001 only
        r_mmd = _write_mermaid_trace(env, "FR-001")
        assert r_mmd.returncode == 0, f"Mermaid trace failed: {r_mmd.stderr}"

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
            f"FR-001 expected status=ok after mermaid trace; got: {fr001_row}"
        )
        assert "gap" not in fr001_row.lower(), (
            f"FR-001 must not be gap when mermaid trace covers it; got: {fr001_row}"
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

        # Mermaid trace citing BOTH FR-001 and FR-002 (all real IDs)
        r_mmd = _write_mermaid_trace(env, "FR-001,FR-002")
        assert r_mmd.returncode == 0, f"Mermaid trace failed: {r_mmd.stderr}"

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
# Test 3: invented ID surfaces as orphan (D-05 downstream validation)
# ---------------------------------------------------------------------------


class TestInventedIdSurfacesAsOrphan:
    """An invented REQ-ID (FR-999) cited in the mermaid trace → listed under ## Orphans."""

    def test_invented_id_surfaces_as_orphan(self, trace_index_env):
        """FR-999 is absent from requirements.json → index update lists it under ## Orphans.

        D-05 contract: trace write accepts any ID without validation; index update is the
        reconciliation point that flags unknown IDs as orphans.
        """
        env = trace_index_env

        # SRS trace (FR-001, FR-002 are the valid set)
        r_srs = _write_srs_trace(env)
        assert r_srs.returncode == 0, f"SRS trace failed: {r_srs.stderr}"

        # Mermaid trace citing FR-001 (real) + FR-999 (invented — not in requirements.json)
        r_mmd = _write_mermaid_trace(env, "FR-001,FR-999")
        assert r_mmd.returncode == 0, (
            f"Mermaid trace write must succeed (trace records what it receives, no "
            f"validation per D-05): {r_mmd.stderr}"
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
        """The fixture requirements.json has FR-001 and FR-002."""
        assert _INDEX_REQS_FIXTURE.exists(), (
            f"Fixture not found: {_INDEX_REQS_FIXTURE}"
        )
        payload = json.loads(_INDEX_REQS_FIXTURE.read_text(encoding="utf-8"))
        reqs = payload.get("requirements", [])
        ids = {r["id"] for r in reqs if isinstance(r, dict) and "id" in r}
        assert "FR-001" in ids, f"FR-001 not in fixture requirements: {ids}"
        assert "FR-002" in ids, f"FR-002 not in fixture requirements: {ids}"
