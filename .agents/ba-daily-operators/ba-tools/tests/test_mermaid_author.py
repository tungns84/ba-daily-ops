"""Author-route no-CLI proof tests (Phase 3, MMD-01 + ROADMAP criterion 1).

Tests cover:
  - test_author_artifact_has_inline_fence: an authored diagram .md (fixture)
    contains a ```mermaid opening fence, a matching closing fence, and YAML
    frontmatter with a non-empty req_ids list.
  - test_author_route_invokes_no_render_cli: the author route section of
    ba-mermaid.md contains neither a mermaid-render invocation nor an mmdc call
    (criterion 1 — no Mermaid CLI on the author route).
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent  # 5 levels up = repo root
_FIXTURE = (
    Path(__file__).parent / "fixtures" / "mermaid" / "authored_diagram.md"
)
_WORKFLOW_PATH = (
    _REPO_ROOT / ".agents" / "ba-daily-operators" / "ba-core" / "workflows" / "ba-mermaid.md"
)


# ---------------------------------------------------------------------------
# Test 1: authored artifact has inline mermaid fence + req_ids frontmatter
# ---------------------------------------------------------------------------


def test_author_artifact_has_inline_fence():
    """An authored diagram .md contains a ```mermaid opening fence, closing fence,
    and a non-empty req_ids list in YAML frontmatter.

    This proves the ba-diagrammer output schema (criterion 1 — the inline block exists).
    """
    assert _FIXTURE.exists(), (
        f"Fixture not found: {_FIXTURE}. Expected to be created by Task 3."
    )
    text = _FIXTURE.read_text(encoding="utf-8")
    lines = text.splitlines()

    # --- Assert frontmatter has a non-empty req_ids list ---
    # Simple line scan: look for "req_ids:" in the frontmatter block (between --- delimiters)
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
        "authored_diagram.md frontmatter missing 'req_ids:' key. "
        "The ba-diagrammer must write req_ids to the .md YAML frontmatter."
    )
    # req_ids value must be a non-empty YAML list — at minimum "[" present and not "[]"
    assert req_ids_value and req_ids_value != "[]", (
        f"authored_diagram.md frontmatter 'req_ids' is empty or blank: {req_ids_value!r}. "
        "The diagram must cite at least one REQ-ID."
    )
    # Confirm it looks like a YAML inline list
    assert req_ids_value.startswith("[") and req_ids_value.endswith("]"), (
        f"req_ids value does not look like a YAML inline list: {req_ids_value!r}. "
        "Expected form: [FR-001, FR-002]"
    )
    # Extract items and assert non-empty
    items_str = req_ids_value[1:-1]  # strip [ ]
    items = [item.strip() for item in items_str.split(",") if item.strip()]
    assert items, (
        f"req_ids list parsed as empty from value: {req_ids_value!r}. "
        "At least one REQ-ID must be present."
    )

    # --- Assert opening ```mermaid fence ---
    opening_fence_found = any(
        line.strip() == "```mermaid" or line.strip().startswith("```mermaid")
        for line in lines
    )
    assert opening_fence_found, (
        "authored_diagram.md does not contain an opening '```mermaid' fence. "
        "The ba-diagrammer must write an inline mermaid block."
    )

    # --- Assert closing ``` fence ---
    # Count fence markers: there must be at least one closing ``` after the opening one
    fence_count = sum(1 for line in lines if line.strip() == "```")
    assert fence_count >= 1, (
        f"authored_diagram.md has {fence_count} closing '```' fences after the frontmatter. "
        "Expected at least one closing fence for the mermaid block."
    )


# ---------------------------------------------------------------------------
# Test 2: author route section contains no render CLI invocations
# ---------------------------------------------------------------------------


def test_author_route_invokes_no_render_cli():
    """The ## Route: author section of ba-mermaid.md contains neither 'mermaid-render'
    nor 'mmdc' (criterion 1 — no Mermaid CLI on the author route).

    Slices the workflow file between '## Route: author' and the next '## Route:'
    heading, then asserts the forbidden tokens are absent from that slice.
    """
    assert _WORKFLOW_PATH.exists(), (
        f"Workflow file not found: {_WORKFLOW_PATH}. Expected created by Task 2."
    )
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    # --- Find the author route section ---
    author_start = None
    author_end = len(lines)

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "## Route: author":
            author_start = i
            continue
        if author_start is not None and stripped.startswith("## Route:") and i > author_start:
            author_end = i
            break

    assert author_start is not None, (
        "ba-mermaid.md does not contain a '## Route: author' heading. "
        "The author route section is required by the plan."
    )

    author_section = "\n".join(lines[author_start:author_end])

    # NOTE: The substring checks below test the route *body* for CLI invocations.
    # The test name appears in this file's module docstring and comments — those
    # are deliberately outside the author_section slice and do not affect the assertion.

    assert "mermaid-render" not in author_section, (
        "The ## Route: author section of ba-mermaid.md contains 'mermaid-render'. "
        "The author route must NOT invoke any render CLI (criterion 1). "
        "Move render invocations to the ## Route: render section only."
    )

    assert "mmdc" not in author_section, (
        "The ## Route: author section of ba-mermaid.md contains 'mmdc'. "
        "The author route must NOT invoke the Mermaid CLI (criterion 1). "
        "Move mmdc invocations to the ## Route: render section only."
    )
