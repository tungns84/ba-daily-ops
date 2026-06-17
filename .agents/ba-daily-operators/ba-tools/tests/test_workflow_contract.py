"""Workflow contract tests for ba-srs-analyze operator (Phase-2 Plan-04).

Verifies:
  1. Workflow YAML frontmatter schema (operator, default_route, routes keys present)
  2. ba-tools resolve-route ba-srs-analyze returns default_route: full (live CLI)
  3. Workflow route list matches init_cmd.OPERATOR_ROUTES registration
  4. ba-critic payload manifest excludes analysis.md (CoVe independence — F11 fixture)
  5. Workflow body uses sequential step wording, not parallel subagent spawn language
"""

import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent  # 5 levels up = repo root
_BA_TOOLS_DIR = _REPO_ROOT / ".agents" / "ba-daily-operators" / "ba-tools"
_WORKFLOW_PATH = (
    _REPO_ROOT / ".agents" / "ba-daily-operators" / "ba-core" / "workflows" / "ba-srs-analyze.md"
)
_FIXTURE_DIR = _BA_TOOLS_DIR / "tests" / "fixtures" / "srs" / "critic-independence"
_FIXTURE_REQUIREMENTS = _FIXTURE_DIR / "requirements.json"
_FIXTURE_ANALYSIS = _FIXTURE_DIR / "analysis.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_workflow_frontmatter(workflow_path: Path) -> dict:
    """Parse YAML frontmatter from workflow file.

    Handles:
      - Scalar values (key: value)
      - Block sequences (routes:\n  - item)

    Returns dict with string or list values.
    Raises ValueError if no frontmatter found.
    """
    text = workflow_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"No frontmatter '---' opening found in {workflow_path}")

    fm_lines: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        fm_lines.append(line)

    result: dict = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in fm_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Top-level key (no leading whitespace)
        if not line[0].isspace() and ":" in line:
            # Flush pending list
            if current_key is not None and current_list is not None:
                result[current_key] = current_list
                current_list = None

            key, _, value = line.partition(":")
            current_key = key.strip()
            value = value.strip()

            if value == "":
                # Start of a block sequence or multi-line value
                current_list = []
                result[current_key] = current_list
            else:
                result[current_key] = value
                current_list = None
            continue

        # List item (leading whitespace + "- ")
        if line.startswith(" ") and stripped.startswith("- ") and current_list is not None:
            item = stripped[2:].strip()
            current_list.append(item)
            continue

    return result


# ---------------------------------------------------------------------------
# Test 1: Workflow YAML frontmatter schema
# ---------------------------------------------------------------------------


def test_workflow_frontmatter_schema():
    """Workflow frontmatter must contain operator, default_route, and routes keys.

    Per PLAN.md: YAML frontmatter block with keys operator, default_route, routes.
    The routes list must be non-empty and contain at least the 6 registered routes.
    """
    assert _WORKFLOW_PATH.exists(), (
        f"Workflow file not found: {_WORKFLOW_PATH}. Expected created by plan 04."
    )

    fm = parse_workflow_frontmatter(_WORKFLOW_PATH)

    required_keys = {"operator", "default_route", "routes"}
    missing = required_keys - set(fm.keys())
    assert not missing, (
        f"Workflow frontmatter missing keys: {missing}. Got: {list(fm.keys())}"
    )

    assert fm["operator"] == "ba-srs-analyze", (
        f"Workflow operator must be 'ba-srs-analyze'; got: {fm['operator']!r}"
    )
    assert fm["default_route"] == "full", (
        f"Workflow default_route must be 'full'; got: {fm['default_route']!r}"
    )
    assert isinstance(fm["routes"], list), (
        f"Workflow routes must be a YAML list; got type: {type(fm['routes'])}"
    )
    assert len(fm["routes"]) >= 1, "Workflow routes list must be non-empty."


# ---------------------------------------------------------------------------
# Test 2: ba-tools resolve-route ba-srs-analyze returns default_route: full
# ---------------------------------------------------------------------------


def test_resolve_route_full():
    """ba-tools resolve-route ba-srs-analyze must return default_route: full.

    Verifies live CLI integration: the Python module is importable and the
    resolve-route subcommand returns the registered default.
    """
    result = subprocess.run(
        [sys.executable, "-m", "ba_tools", "resolve-route", "ba-srs-analyze"],
        capture_output=True,
        text=True,
        cwd=str(_BA_TOOLS_DIR),
    )
    assert result.returncode == 0, (
        f"ba-tools resolve-route ba-srs-analyze exited {result.returncode}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"resolve-route stdout is not valid JSON: {result.stdout!r}"
        ) from exc

    assert data.get("default_route") == "full", (
        f"resolve-route JSON must contain default_route: 'full'; got: {data}"
    )


# ---------------------------------------------------------------------------
# Test 3: Workflow route list matches OPERATOR_ROUTES registration
# ---------------------------------------------------------------------------


def test_workflow_routes_match_registration():
    """Workflow routes list must match init_cmd.OPERATOR_ROUTES['ba-srs-analyze'].

    Phase-1 code registers the canonical route list in init_cmd.OPERATOR_ROUTES.
    The workflow frontmatter routes must exactly match this registration (no
    extra routes, no missing routes).
    """
    assert _WORKFLOW_PATH.exists(), f"Workflow file not found: {_WORKFLOW_PATH}"

    from ba_tools.commands.init_cmd import OPERATOR_ROUTES  # noqa: PLC0415

    registered_routes = set(OPERATOR_ROUTES.get("ba-srs-analyze", []))
    assert registered_routes, (
        "OPERATOR_ROUTES['ba-srs-analyze'] is empty or missing — "
        "check init_cmd.py Phase-1 registration."
    )

    fm = parse_workflow_frontmatter(_WORKFLOW_PATH)
    workflow_routes = set(fm.get("routes", []))

    missing_from_workflow = registered_routes - workflow_routes
    extra_in_workflow = workflow_routes - registered_routes

    assert not missing_from_workflow, (
        f"Workflow frontmatter routes missing (registered but not in workflow): "
        f"{missing_from_workflow}"
    )
    assert not extra_in_workflow, (
        f"Workflow frontmatter routes extra (in workflow but not registered): "
        f"{extra_in_workflow}"
    )


# ---------------------------------------------------------------------------
# Test 4: ba-critic payload manifest excludes analysis.md (F11 fixture)
# ---------------------------------------------------------------------------


def test_critic_payload_excludes_analysis():
    """Workflow must never include analysis.md in the ba-critic payload.

    F11 fixture: requirements.json + analysis.md with a planted WRITER_RATIONALE_MARKER.

    The critic independence contract (D-21, G3) requires that the critic step
    receives ONLY {source_path, requirements_json_path}. The workflow text must
    not reference analysis.md as a payload item for the critic step.

    This test verifies the static contract by:
    1. Confirming the F11 fixture files exist.
    2. Scanning the workflow text for patterns that would pass analysis.md to
       the critic: e.g., 'analysis.md' appearing in a list of critic payload items.
    3. Confirming the planted marker string is NOT in the requirements.json fixture
       (marker belongs only in analysis.md — cross-contamination guard).
    """
    assert _FIXTURE_REQUIREMENTS.exists(), (
        f"F11 fixture requirements.json not found: {_FIXTURE_REQUIREMENTS}"
    )
    assert _FIXTURE_ANALYSIS.exists(), (
        f"F11 fixture analysis.md not found: {_FIXTURE_ANALYSIS}"
    )

    # Verify planted marker is in analysis.md (fixture integrity check)
    analysis_text = _FIXTURE_ANALYSIS.read_text(encoding="utf-8")
    assert "WRITER_RATIONALE_MARKER" in analysis_text, (
        "F11 fixture analysis.md missing the WRITER_RATIONALE_MARKER sentinel. "
        "Fixture may have been corrupted."
    )

    # Verify planted marker is NOT in requirements.json (no cross-contamination)
    reqs_text = _FIXTURE_REQUIREMENTS.read_text(encoding="utf-8")
    assert "WRITER_RATIONALE_MARKER" not in reqs_text, (
        "F11 fixture requirements.json contains WRITER_RATIONALE_MARKER — "
        "the writer rationale leaked into the requirements file."
    )

    # Verify workflow text does NOT pass analysis.md to the critic step.
    # The forbidden pattern: analysis.md appearing in the critic payload block.
    # We check the critic payload block specifically (lines between "critic" and
    # the next "###" or end-of-section) for any analysis.md reference.
    assert _WORKFLOW_PATH.exists(), f"Workflow file not found: {_WORKFLOW_PATH}"
    workflow_text = _WORKFLOW_PATH.read_text(encoding="utf-8")

    # Check that analysis.md does NOT appear in the critic payload code block.
    # The payload block is the fenced code block (``` ... ```) immediately after
    # the critic step instruction. Only the contents of that fenced block matter —
    # prohibition prose ("Do NOT pass analysis.md") is allowed and expected.
    #
    # Strategy: find all fenced code blocks that appear near a "ba-critic" mention
    # and check none of them list "analysis.md" as a payload key.
    fenced_block_pattern = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
    for fenced_match in fenced_block_pattern.finditer(workflow_text):
        block_content = fenced_match.group(1)
        block_start = fenced_match.start()

        # Only inspect fenced blocks that appear within 600 chars of a "ba-critic" mention
        nearby_critic = workflow_text.rfind("ba-critic", max(0, block_start - 600), block_start)
        if nearby_critic < 0:
            continue

        # In the payload block, analysis.md should NOT appear as a key
        if "analysis.md" in block_content:
            raise AssertionError(
                "A fenced code block near the ba-critic step contains 'analysis.md'. "
                "The critic payload must contain ONLY {source_path, requirements_json_path} "
                "(D-21, G3). Remove analysis.md from the critic payload block.\n"
                f"Block content: {block_content[:200]!r}"
            )


# ---------------------------------------------------------------------------
# Test 5: No fake subagent spawn language in workflow
# ---------------------------------------------------------------------------


def test_no_fake_subagent_spawn():
    """Workflow must not instruct parallel subagent spawn for writer/critic steps.

    Codex v1 is a single sequential agent loop. Patterns like 'spawn a subagent',
    'start a parallel agent', 'run concurrently' are prohibited — they describe
    a Codex v2 multi-agent capability that does not exist in v1.

    The workflow must use sequential step wording: 'run', 'call', 'invoke', etc.
    """
    assert _WORKFLOW_PATH.exists(), f"Workflow file not found: {_WORKFLOW_PATH}"
    workflow_text = _WORKFLOW_PATH.read_text(encoding="utf-8").lower()

    # Prescriptive parallel-spawn patterns: instructions TO do something in parallel.
    # Prohibition prose ("there is no autonomous parallel subagent spawn",
    # "not a parallel spawn", "do not run concurrently") is expected and allowed.
    # We check for prescriptive forms by requiring the pattern to NOT be immediately
    # preceded by "no ", "not a ", "do not", "never", "avoid", or similar negation.
    prescriptive_patterns = [
        # Matches "spawn a subagent" / "spawn subagent" not preceded by negation
        r"(?<!no )(?<!not a )(?<!do not )(?<!never )(?<!avoid )spawn (?:a )?subagent",
        r"(?<!no )(?<!not a )(?<!do not )(?<!never )start a parallel",
        r"(?<!do not )(?<!never )run (?:writer and critic )?(?:in )?parallel",
        r"(?<!do not )(?<!never )(?:launch|fork) (?:a )?new agent",
        # "concurrently" in an instruction (not in a prohibition)
        r"(?<!do not )(?<!never )run .{0,40}concurrently",
        r"(?<!do not )(?<!never )simultaneously invoke",
    ]

    found = []
    for pattern in prescriptive_patterns:
        matches = re.findall(pattern, workflow_text)
        if matches:
            found.extend(matches)

    assert not found, (
        f"Workflow contains prescriptive parallel/spawn language (Codex v1 is sequential): "
        f"{found}. Use sequential step wording: 'Run the ba-srs-writer step', "
        "'Run the ba-critic step'. Prohibitions ('not a parallel spawn') are allowed."
    )
