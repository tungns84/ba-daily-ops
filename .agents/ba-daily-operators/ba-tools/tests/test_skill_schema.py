"""SKILL.md / openai.yaml schema validator tests (Phase-2 Wave-0 scaffold).

These tests validate that skill metadata files conform to the documented
contract (CLAUDE.md "Codex Skill Contract"):
  - SKILL.md frontmatter has exactly {name, description} — no extra keys
  - agents/openai.yaml has nested interface.* keys + policy.allow_implicit_invocation
  - default_prompt uses skill-native wording and does NOT contain a fake CLI literal

Skill-path tests were skipped (plan 01) until skill files landed in plan 04 — now live.
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Skill file paths (resolved relative to repo root)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent  # .agents/ba-daily-operators/ba-tools/../../../..
_AGENTS_ROOT = Path(__file__).parent.parent.parent.parent  # .agents/ba-daily-operators

# Expected skill directories (plan 04 creates these)
_SKILL_DIRS = [
    _REPO_ROOT / ".agents" / "skills",
]
# openai.yaml lives per-skill: .agents/skills/<skill>/agents/openai.yaml
# We check the ba-srs-analyze skill specifically
_BA_SRS_SKILL_DIR = _REPO_ROOT / ".agents" / "skills" / "ba-srs-analyze"
_OPENAI_YAML = _BA_SRS_SKILL_DIR / "agents" / "openai.yaml"


# ---------------------------------------------------------------------------
# Helpers: parsers for skill metadata formats
# ---------------------------------------------------------------------------


def parse_skill_md_frontmatter(skill_md_path: Path) -> dict:
    """Parse YAML frontmatter from a SKILL.md file.

    Returns a dict of key: value pairs from the --- block.
    Handles block scalars (> and |) so continuation lines are NOT treated as keys.
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
                # If value is a block scalar indicator, all following indented lines belong to it
                if value in (">", "|", ">-", "|-", ">+", "|+"):
                    in_block_scalar = True
        # Indented lines: skip if inside a block scalar (continuation of previous key)
        # Also skip lines that are pure continuation of a multi-line value
    return result


def parse_openai_yaml_structure(yaml_path: Path) -> dict:
    """Parse agents/openai.yaml into a nested dict using stdlib (no PyYAML).

    Parses only the fields relevant to the schema contract:
      - interface.display_name
      - interface.short_description
      - interface.default_prompt
      - policy.allow_implicit_invocation

    Returns a dict with top-level keys 'interface' and 'policy'.
    Raises ValueError if required structure is missing.
    """
    text = yaml_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    result: dict = {}
    current_section: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Detect top-level section headers (no leading spaces)
        if not line.startswith(" ") and stripped.endswith(":"):
            current_section = stripped[:-1]
            result[current_section] = {}
            continue

        # Detect nested key: value pairs (with leading spaces)
        if line.startswith(" ") and ":" in stripped and current_section:
            key, _, value = stripped.partition(":")
            result[current_section][key.strip()] = value.strip()

    return result


def read_openai_yaml_full(yaml_path: Path) -> str:
    """Return the full text of the openai.yaml for substring assertions."""
    return yaml_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# SKILL.md frontmatter schema tests (live — plan 04 skill files exist)
# ---------------------------------------------------------------------------


def test_skill_md_frontmatter_keys_only_name_description():
    """SKILL.md frontmatter must contain exactly {name, description} — no extra keys.

    Per CLAUDE.md 'Codex Skill Contract': "Do not include any other fields in
    YAML frontmatter." (confirmed from openai/skills SKILL.md official repo).
    """
    for skill_dir in _SKILL_DIRS:
        for skill_md in skill_dir.glob("*/SKILL.md"):
            fm = parse_skill_md_frontmatter(skill_md)
            allowed = {"name", "description"}
            extra = set(fm.keys()) - allowed
            missing = allowed - set(fm.keys())
            assert not extra, (
                f"{skill_md}: SKILL.md frontmatter has extra keys {extra}; "
                f"only {allowed} are permitted."
            )
            assert not missing, (
                f"{skill_md}: SKILL.md frontmatter missing required keys {missing}."
            )


# ---------------------------------------------------------------------------
# agents/openai.yaml nesting schema tests (live — plan 04 skill files exist)
# ---------------------------------------------------------------------------


def test_openai_yaml_nesting_structure():
    """agents/openai.yaml must nest display_name/short_description/default_prompt under interface:
    and allow_implicit_invocation under policy: (CLAUDE.md 'CONFIRMED with structural note').

    Flat-level allow_implicit_invocation (as shown in DESIGN §3) is WRONG per the
    official contract — it must be nested under policy:.
    """
    assert _OPENAI_YAML.exists(), (
        f"agents/openai.yaml not found at {_OPENAI_YAML}; "
        "expected to be created by plan 04."
    )
    structure = parse_openai_yaml_structure(_OPENAI_YAML)

    # interface section must exist with the three display fields
    assert "interface" in structure, (
        f"agents/openai.yaml missing 'interface:' top-level section; got: {list(structure.keys())}"
    )
    interface_keys = set(structure["interface"].keys())
    required_interface = {"display_name", "short_description", "default_prompt"}
    missing_interface = required_interface - interface_keys
    assert not missing_interface, (
        f"agents/openai.yaml 'interface:' section missing keys: {missing_interface}"
    )

    # policy section must exist with allow_implicit_invocation
    assert "policy" in structure, (
        f"agents/openai.yaml missing 'policy:' top-level section; got: {list(structure.keys())}"
    )
    assert "allow_implicit_invocation" in structure["policy"], (
        "agents/openai.yaml 'policy:' section missing 'allow_implicit_invocation'; "
        "must be nested under policy:, not at flat top level."
    )

    # allow_implicit_invocation must be false (never true)
    raw_value = structure["policy"]["allow_implicit_invocation"]
    assert raw_value.lower() in ("false", "no", "0"), (
        f"agents/openai.yaml 'policy.allow_implicit_invocation' must be false; got: {raw_value!r}"
    )


def test_openai_yaml_default_prompt_no_fake_cli():
    """default_prompt must NOT contain the fake CLI pattern 'ba-srs-analyze --route'.

    Per PLAN review (Codex HIGH): the default_prompt must use skill-native wording
    ('use the workflow, route full') and must NEVER look like a runnable shell
    command ('ba-srs-analyze --route full ...' — no such binary exists).
    It MAY reference 'ba-tools resolve-route ba-srs-analyze' (the real CLI).
    """
    assert _OPENAI_YAML.exists(), (
        f"agents/openai.yaml not found at {_OPENAI_YAML}"
    )
    full_text = read_openai_yaml_full(_OPENAI_YAML)

    # The fake CLI pattern: 'ba-srs-analyze --route' (with a space before --)
    # This is the forbidden form — it implies ba-srs-analyze is a shell binary.
    fake_cli_pattern = "ba-srs-analyze --route"
    assert fake_cli_pattern not in full_text, (
        f"agents/openai.yaml default_prompt contains the fake CLI literal "
        f"{fake_cli_pattern!r}. Use skill-native wording instead "
        f"(e.g. 'Use the ba-srs-analyze workflow, route full'). "
        f"The skill is not a shell binary — there is no ba-srs-analyze command on PATH."
    )


# ---------------------------------------------------------------------------
# Helpers are always exercisable (no skill files needed)
# ---------------------------------------------------------------------------


def test_parse_skill_md_frontmatter_helper():
    """parse_skill_md_frontmatter correctly extracts name and description from a string fixture."""
    import tempfile
    import os

    skill_content = "---\nname: test-skill\ndescription: A test skill for unit testing.\n---\n# Body\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(skill_content)
        tmp_path = f.name

    try:
        fm = parse_skill_md_frontmatter(Path(tmp_path))
        assert fm.get("name") == "test-skill", f"Expected 'test-skill'; got {fm.get('name')}"
        assert fm.get("description") == "A test skill for unit testing.", (
            f"Expected description; got {fm.get('description')}"
        )
        assert set(fm.keys()) == {"name", "description"}, (
            f"Expected only name+description keys; got {set(fm.keys())}"
        )
    finally:
        os.unlink(tmp_path)


def test_parse_skill_md_frontmatter_no_frontmatter_raises():
    """parse_skill_md_frontmatter raises ValueError when no frontmatter block exists."""
    import tempfile
    import os

    skill_content = "# No frontmatter here\nJust body text.\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(skill_content)
        tmp_path = f.name

    try:
        with pytest.raises(ValueError, match="frontmatter"):
            parse_skill_md_frontmatter(Path(tmp_path))
    finally:
        os.unlink(tmp_path)
