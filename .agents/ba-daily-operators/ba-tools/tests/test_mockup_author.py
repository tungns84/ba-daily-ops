"""Fidelity-branch proof tests for ba-mockup operator (Phase 4, MOCK-01 + MOCK-03).

Tests cover:
  - test_html_artifact_has_req_ids_comment: the html-fidelity fixture authored_html.html
    has a HTML req_ids comment as its FIRST line, with a non-empty list (D-03 / MOCK-02
    carrier, MOCK-03).
  - test_html_artifact_has_doctype: authored_html.html contains <!DOCTYPE html>
    (MOCK-03 html shape).
  - test_wireframe_artifact_has_frontmatter: authored_wireframe.md YAML frontmatter
    has a non-empty req_ids inline list (D-04 / MOCK-03 wireframe shape).
  - test_wireframe_has_no_ascii_box_drawing: authored_wireframe.md body contains no
    '+--' ASCII box-drawing run (D-04).
  - test_screen_route_invokes_no_render_cli: the ## Route: screen section of ba-mockup.md
    contains none of 'render', 'mmdc', 'mermaid-render', 'drawio' (D-05 no-render).
  - test_workflow_rejects_missing_fidelity: ba-mockup.md contains fidelity enforcement
    text — 'fidelity', 'html', 'wireframe' all present in the workflow (D-05a).
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent  # 5 levels up = repo root
_FIXTURE_HTML = Path(__file__).parent / "fixtures" / "mockup" / "authored_html.html"
_FIXTURE_WF = Path(__file__).parent / "fixtures" / "mockup" / "authored_wireframe.md"
_WORKFLOW_PATH = (
    _REPO_ROOT / ".agents" / "ba-daily-operators" / "ba-core" / "workflows" / "ba-mockup.md"
)

# Regex for the HTML req_ids comment on the first line
_HTML_REQ_IDS_RE = re.compile(r'<!--\s*req_ids:\s*\[([^\]]*)\]\s*-->')


# ---------------------------------------------------------------------------
# Test 1: html fixture has req_ids comment as first line (MOCK-02/MOCK-03 carrier)
# ---------------------------------------------------------------------------


def test_html_artifact_has_req_ids_comment():
    """First line of authored_html.html matches <!-- req_ids: [...] --> with a non-empty list.

    This proves the D-03 contract: the html-fidelity artifact carries req_ids as
    an HTML comment on line 1 (before <!DOCTYPE html>).
    """
    assert _FIXTURE_HTML.exists(), (
        f"Fixture not found: {_FIXTURE_HTML}. Expected to be created by Task 1."
    )
    text = _FIXTURE_HTML.read_text(encoding="utf-8")
    first_line = text.splitlines()[0]
    m = _HTML_REQ_IDS_RE.match(first_line)
    assert m, (
        f"First line must be HTML req_ids comment matching "
        f"'<!-- req_ids: [...] -->'; got: {first_line!r}"
    )
    items = [x.strip() for x in m.group(1).split(",") if x.strip()]
    assert items, (
        f"req_ids comment must list at least one REQ-ID; got: {m.group(1)!r}"
    )


# ---------------------------------------------------------------------------
# Test 2: html fixture has DOCTYPE (MOCK-03 html shape)
# ---------------------------------------------------------------------------


def test_html_artifact_has_doctype():
    """authored_html.html contains <!DOCTYPE html> (MOCK-03 html shape).

    The DOCTYPE must be present so the artifact is a valid HTML5 document.
    """
    assert _FIXTURE_HTML.exists(), (
        f"Fixture not found: {_FIXTURE_HTML}. Expected to be created by Task 1."
    )
    text = _FIXTURE_HTML.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in text, (
        f"authored_html.html must contain '<!DOCTYPE html>'; "
        f"file starts with: {text[:200]!r}"
    )


# ---------------------------------------------------------------------------
# Test 3: wireframe fixture has frontmatter req_ids (MOCK-03 wireframe shape)
# ---------------------------------------------------------------------------


def test_wireframe_artifact_has_frontmatter():
    """authored_wireframe.md YAML frontmatter has a non-empty req_ids inline list (D-04).

    Scans lines between the opening and closing '---' delimiters for the 'req_ids:' key.
    """
    assert _FIXTURE_WF.exists(), (
        f"Fixture not found: {_FIXTURE_WF}. Expected to be created by Task 1."
    )
    text = _FIXTURE_WF.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_frontmatter = False
    req_ids_found = False
    req_ids_value = ""
    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                # Closing ---
                break
        if in_frontmatter and stripped.startswith("req_ids:"):
            req_ids_found = True
            req_ids_value = stripped[len("req_ids:"):].strip()
            break

    assert req_ids_found, (
        "authored_wireframe.md frontmatter missing 'req_ids:' key. "
        "The wireframe-fidelity artifact must write req_ids to YAML frontmatter (D-04)."
    )
    assert req_ids_value and req_ids_value != "[]", (
        f"authored_wireframe.md frontmatter 'req_ids' is empty or blank: {req_ids_value!r}. "
        "The wireframe must cite at least one REQ-ID."
    )
    assert req_ids_value.startswith("[") and req_ids_value.endswith("]"), (
        f"req_ids value does not look like a YAML inline list: {req_ids_value!r}. "
        "Expected form: [FR-001, FR-002]"
    )
    items_str = req_ids_value[1:-1]  # strip [ ]
    items = [item.strip() for item in items_str.split(",") if item.strip()]
    assert items, (
        f"req_ids list parsed as empty from value: {req_ids_value!r}. "
        "At least one REQ-ID must be present."
    )


# ---------------------------------------------------------------------------
# Test 4: wireframe fixture has no ASCII box-drawing (D-04)
# ---------------------------------------------------------------------------


def test_wireframe_has_no_ascii_box_drawing():
    """authored_wireframe.md body contains no '+--' ASCII box-drawing run (D-04).

    D-04 requires markdown-structural blocks (headings + lists + tables), NOT ASCII
    box-drawing characters. This test catches violations of that convention.
    """
    assert _FIXTURE_WF.exists(), (
        f"Fixture not found: {_FIXTURE_WF}. Expected to be created by Task 1."
    )
    text = _FIXTURE_WF.read_text(encoding="utf-8")
    assert "+--" not in text, (
        "authored_wireframe.md contains '+--' ASCII box-drawing characters. "
        "D-04 requires headings + lists + tables — not ASCII box-drawing. "
        "Remove all '+--' patterns from the fixture."
    )


# ---------------------------------------------------------------------------
# Test 5: screen route section contains no render CLI invocations (D-05)
# ---------------------------------------------------------------------------


def test_screen_route_invokes_no_render_cli():
    """The ## Route: screen section of ba-mockup.md contains none of
    'render', 'mmdc', 'mermaid-render', 'drawio' (D-05 no-render).

    Slices the workflow file between '## Route: screen' and the next '## Route:'
    heading, then asserts the forbidden tokens are absent from that slice.

    NOTE: This test reads ba-mockup.md, which is created by Plan 02. If the file
    does not yet exist, the test asserts explicitly (RED state until Plan 02 lands).
    """
    assert _WORKFLOW_PATH.exists(), (
        f"Workflow file not found: {_WORKFLOW_PATH}. "
        "Expected to be created by Plan 02. This test will go green once Plan 02 lands."
    )
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Find the ## Route: screen section
    screen_start = None
    screen_end = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "## Route: screen":
            screen_start = i
            continue
        if screen_start is not None and stripped.startswith("## Route:") and i > screen_start:
            screen_end = i
            break

    assert screen_start is not None, (
        "ba-mockup.md does not contain a '## Route: screen' heading. "
        "The screen route section is required by the plan."
    )

    screen_section = "\n".join(lines[screen_start:screen_end])

    assert "render" not in screen_section.lower(), (
        "The ## Route: screen section of ba-mockup.md contains 'render'. "
        "The screen route must NOT invoke any render CLI (D-05). "
        "Move render references to a separate route only."
    )
    assert "mmdc" not in screen_section, (
        "The ## Route: screen section of ba-mockup.md contains 'mmdc'. "
        "The screen route must NOT invoke the Mermaid CLI (D-05). "
        "Remove mmdc references from the screen route section."
    )
    assert "mermaid-render" not in screen_section, (
        "The ## Route: screen section of ba-mockup.md contains 'mermaid-render'. "
        "The screen route must NOT invoke any render CLI (D-05)."
    )
    assert "drawio" not in screen_section.lower(), (
        "The ## Route: screen section of ba-mockup.md contains 'drawio'. "
        "The screen route must NOT invoke any render CLI (D-05)."
    )


# ---------------------------------------------------------------------------
# Test 6: workflow contains fidelity enforcement text (D-05a)
# ---------------------------------------------------------------------------


def test_workflow_rejects_missing_fidelity():
    """ba-mockup.md contains fidelity enforcement text: 'fidelity', 'html', 'wireframe'
    all present in the workflow (D-05a fidelity gate text-presence assertion).

    NOTE: This test reads ba-mockup.md, created by Plan 02. If absent, it asserts
    explicitly (RED state until Plan 02 lands).
    """
    assert _WORKFLOW_PATH.exists(), (
        f"Workflow file not found: {_WORKFLOW_PATH}. "
        "Expected to be created by Plan 02. This test will go green once Plan 02 lands."
    )
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "fidelity" in text, (
        "ba-mockup.md must contain the word 'fidelity' (D-05a fidelity gate). "
        "The workflow must reference the --fidelity argument and enforcement."
    )
    assert "html" in text, (
        "ba-mockup.md must reference 'html' as a valid fidelity value (D-05a). "
        "The workflow must list accepted fidelity values."
    )
    assert "wireframe" in text, (
        "ba-mockup.md must reference 'wireframe' as a valid fidelity value (D-05a). "
        "The workflow must list accepted fidelity values."
    )
