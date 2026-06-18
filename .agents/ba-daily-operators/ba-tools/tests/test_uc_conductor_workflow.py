"""Static-check tests for the ba-uc conductor workflow contract (Phase 05 Plan 03).

Tests verify WITHOUT running an agent or LLM:
  1. ba-uc.md frontmatter routes match init_cmd.OPERATOR_ROUTES['ba-uc']
  2. SKILL.md frontmatter has exactly {name, description} and name == 'ba-uc'
  3. openai.yaml policy.allow_implicit_invocation is False (CDX-02)
  4. deliver route drives ba-mermaid full route (not the default author)
  5. No render CLI step command (mmdc / draw.io export) in ba-uc.md (criterion 4 / GATE-03)
"""

import re
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Path constants (same convention as test_workflow_contract.py + test_skill_schema.py)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent  # 5 levels up = repo root
_BA_TOOLS_DIR = _REPO_ROOT / ".agents" / "ba-daily-operators" / "ba-tools"

_WORKFLOW_PATH = (
    _REPO_ROOT / ".agents" / "ba-daily-operators" / "ba-core" / "workflows" / "ba-uc.md"
)
_SKILL_MD_PATH = _REPO_ROOT / ".agents" / "skills" / "ba-uc" / "SKILL.md"
_OPENAI_YAML_PATH = _REPO_ROOT / ".agents" / "skills" / "ba-uc" / "agents" / "openai.yaml"


# ---------------------------------------------------------------------------
# Frontmatter helpers (copied from test_workflow_contract.py — no cross-module import)
# ---------------------------------------------------------------------------


def parse_workflow_frontmatter(workflow_path: Path) -> dict:
    """Parse YAML frontmatter from workflow file.

    Handles scalar values and block sequences (routes:\\n  - item).
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


def parse_skill_md_frontmatter(skill_md_path: Path) -> dict:
    """Parse YAML frontmatter from a SKILL.md file.

    Handles block scalars (> and |) so continuation lines are NOT treated as keys.
    Returns a dict of top-level key: value pairs from the --- block.
    Raises ValueError if no frontmatter found.
    """
    text = skill_md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"No frontmatter opening '---' found in {skill_md_path}")

    fm_lines = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        fm_lines.append(line)

    result = {}
    in_block_scalar = False
    for line in fm_lines:
        # A top-level key must start at column 0 (no leading whitespace)
        if line and not line[0].isspace():
            in_block_scalar = False
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                result[key] = value
                if value in (">", "|", ">-", "|-", ">+", "|+"):
                    in_block_scalar = True
        # Indented continuation lines of a block scalar — skip, already captured under key
    return result


def parse_openai_yaml_structure(yaml_path: Path) -> dict:
    """Parse agents/openai.yaml into a nested dict using stdlib (no PyYAML).

    Parses the fields relevant to the schema contract:
      - interface.display_name, interface.short_description, interface.default_prompt
      - policy.allow_implicit_invocation

    Returns a dict with top-level keys 'interface' and 'policy'.
    """
    text = yaml_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    result: dict = {}
    current_section: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Top-level section headers (no leading spaces, ends with ':')
        if not line.startswith(" ") and stripped.endswith(":"):
            current_section = stripped[:-1]
            result[current_section] = {}
            continue

        # Nested key: value pairs (with leading spaces)
        if line.startswith(" ") and ":" in stripped and current_section:
            key, _, value = stripped.partition(":")
            result[current_section][key.strip()] = value.strip()

    return result


# ---------------------------------------------------------------------------
# Test 1: ba-uc.md frontmatter routes match OPERATOR_ROUTES registration
# ---------------------------------------------------------------------------


def test_ba_uc_workflow_frontmatter_matches_registered_routes():
    """ba-uc.md frontmatter operator/default_route/routes must match init_cmd.OPERATOR_ROUTES.

    Single source of truth: OPERATOR_ROUTES['ba-uc'] in init_cmd.py.
    Workflow frontmatter routes must be exactly equal — no extra, none missing.
    """
    assert _WORKFLOW_PATH.exists(), (
        f"Workflow file not found: {_WORKFLOW_PATH}. Expected created by plan 03."
    )

    from ba_tools.commands.init_cmd import OPERATOR_ROUTES  # noqa: PLC0415

    registered_routes = set(OPERATOR_ROUTES.get("ba-uc", []))
    assert registered_routes, (
        "OPERATOR_ROUTES['ba-uc'] is empty or missing — check init_cmd.py registration."
    )

    fm = parse_workflow_frontmatter(_WORKFLOW_PATH)

    assert fm.get("operator") == "ba-uc", (
        f"Workflow frontmatter operator must be 'ba-uc'; got {fm.get('operator')!r}"
    )
    assert fm.get("default_route") == "deliver", (
        f"Workflow frontmatter default_route must be 'deliver'; got {fm.get('default_route')!r}"
    )
    assert isinstance(fm.get("routes"), list), (
        f"Workflow frontmatter routes must be a YAML list; got {type(fm.get('routes'))}"
    )

    workflow_routes = set(fm["routes"])
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
# Test 2: SKILL.md frontmatter has exactly {name, description} and name == 'ba-uc'
# ---------------------------------------------------------------------------


def test_ba_uc_skill_frontmatter_name_description_only():
    """SKILL.md frontmatter must contain exactly {name, description} — no extra keys.

    CDX constraint (CLAUDE.md): 'Do not include any other fields in YAML frontmatter.'
    name must be 'ba-uc'.
    """
    assert _SKILL_MD_PATH.exists(), (
        f"SKILL.md not found: {_SKILL_MD_PATH}. Expected created by plan 03."
    )

    fm = parse_skill_md_frontmatter(_SKILL_MD_PATH)
    allowed = {"name", "description"}
    extra = set(fm.keys()) - allowed
    missing = allowed - set(fm.keys())

    assert not extra, (
        f"SKILL.md frontmatter has extra keys {extra}; only {allowed} are permitted."
    )
    assert not missing, (
        f"SKILL.md frontmatter missing required keys {missing}."
    )
    assert fm.get("name") == "ba-uc", (
        f"SKILL.md name must be 'ba-uc'; got {fm.get('name')!r}"
    )


# ---------------------------------------------------------------------------
# Test 3: openai.yaml policy.allow_implicit_invocation is False (CDX-02)
# ---------------------------------------------------------------------------


def test_ba_uc_openai_yaml_policy_implicit_false():
    """openai.yaml must have interface.display_name and policy.allow_implicit_invocation == False.

    CDX-02: allow_implicit_invocation MUST be false on the conductor, nested under policy:.
    Flat-level allow_implicit_invocation is WRONG per the official contract.
    """
    assert _OPENAI_YAML_PATH.exists(), (
        f"openai.yaml not found: {_OPENAI_YAML_PATH}. Expected created by plan 03."
    )

    structure = parse_openai_yaml_structure(_OPENAI_YAML_PATH)

    assert "interface" in structure, (
        f"openai.yaml missing 'interface:' top-level section; got: {list(structure.keys())}"
    )
    assert structure["interface"].get("display_name"), (
        "openai.yaml interface.display_name must be present and non-empty."
    )

    assert "policy" in structure, (
        f"openai.yaml missing 'policy:' top-level section; got: {list(structure.keys())}"
    )
    assert "allow_implicit_invocation" in structure["policy"], (
        "openai.yaml 'policy:' section missing 'allow_implicit_invocation'; "
        "must be nested under policy:, not at flat top level (CDX-02)."
    )

    raw_value = structure["policy"]["allow_implicit_invocation"]
    assert raw_value.lower() in ("false", "no", "0"), (
        f"openai.yaml policy.allow_implicit_invocation must be false (CDX-02); got: {raw_value!r}"
    )


# ---------------------------------------------------------------------------
# Test 4: deliver route drives mermaid full route (not default author)
# ---------------------------------------------------------------------------


def test_deliver_route_drives_mermaid_full_not_author():
    """ba-uc.md deliver route must explicitly drive ba-mermaid full route, not default author.

    Per RESEARCH Q1: ba-mermaid default route is 'author' — the conductor must
    explicitly drive 'full' (which adds trace write + index update). The workflow
    body must reference 'ba-mermaid.md' and contain 'full' near the mermaid step,
    and must mark that this is NOT the default author route.
    """
    assert _WORKFLOW_PATH.exists(), f"Workflow file not found: {_WORKFLOW_PATH}"
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")

    # Must reference ba-mermaid.md
    assert "ba-mermaid.md" in text, (
        "ba-uc.md must reference ba-mermaid.md (the mermaid sub-workflow path)."
    )

    # Must instruct the full route (case-insensitive)
    # Look for "full" appearing in close proximity to "mermaid"
    lower_text = text.lower()
    mermaid_idx = lower_text.find("ba-mermaid.md")
    assert mermaid_idx >= 0, "ba-mermaid.md not found in workflow text."

    # Extract 500 chars after the first ba-mermaid.md reference
    mermaid_section = lower_text[mermaid_idx:mermaid_idx + 500]
    assert "full" in mermaid_section, (
        "ba-uc.md mermaid step must instruct the 'full' route (within 500 chars of "
        "ba-mermaid.md reference)."
    )

    # Must explicitly note NOT the default author route
    # Accept either "not" near "author" or "not the default" near mermaid section
    not_author_markers = ["not the default", "not default", "not author", "not `author`"]
    found_not_author = any(marker in lower_text for marker in not_author_markers)
    assert found_not_author, (
        "ba-uc.md must explicitly state that the mermaid step drives the 'full' route "
        "and NOT the default 'author' route. Expected one of: "
        f"{not_author_markers}"
    )


# ---------------------------------------------------------------------------
# Test 5: No render CLI step command in ba-uc.md (criterion 4 / GATE-03 spine-exempt)
# ---------------------------------------------------------------------------


def test_no_render_cli_invoked_on_spine():
    """ba-uc.md must NOT instruct invoking a render CLI as a step command.

    The spine drives authoring routes only (D-SAFE, GATE-03 Scope: spine-exempt).
    mmdc and draw.io export are plugin-only. This test asserts that no render-CLI
    invocation appears as a step command in the conductor workflow.

    Specifically: no line in the workflow body should instruct running mmdc or
    draw.io -x / --export as a step. Informational references in prohibitions are
    excluded by checking for negative-context markers.
    """
    assert _WORKFLOW_PATH.exists(), f"Workflow file not found: {_WORKFLOW_PATH}"
    text = _WORKFLOW_PATH.read_text(encoding="utf-8")

    # Patterns that indicate a render-CLI is being INVOKED as a step instruction.
    # These patterns look for command invocations, not informational mentions.
    render_cli_patterns = [
        # mmdc invocation as step command: "run mmdc", "mmdc -i", etc.
        r"\bmmdc\s+-i\b",
        r"\bmmdc\s+--input\b",
        r"run\s+mmdc\b",
        r"`mmdc\s",
        # draw.io export as step command: "draw.io -x", "drawio --export", etc.
        r"\bdraw\.io\s+-x\b",
        r"\bdraw\.io\s+--export\b",
        r"\bdrawio\s+-x\b",
        r"\bdrawio\s+--export\b",
        r"run\s+draw\.io\b",
        r"`draw\.io\s",
    ]

    found_patterns = []
    for pattern in render_cli_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found_patterns.extend(matches)

    assert not found_patterns, (
        "ba-uc.md contains render-CLI step command(s) — the spine must NOT invoke "
        "mmdc or draw.io export directly (GATE-03 Scope: spine-exempt; authoring routes only). "
        f"Found: {found_patterns}"
    )
