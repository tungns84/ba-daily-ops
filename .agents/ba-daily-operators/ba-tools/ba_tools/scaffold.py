"""
.ba-ops/ scaffold creation (TRACE-01, TOOL-01).

Provides:
  ensure_scaffold(root: Path) -> dict   — idempotent: creates .ba-ops/ and
      the five seed files only when absent. Never overwrites existing files.

Scaffold files (DESIGN §8):
  PROJECT.md        — BA engagement header stub
  REQUIREMENTS.md   — REQ-ID registry header
  INDEX.md          — Traceability matrix header
  STATE.md          — YAML frontmatter + Markdown body (pipeline state)
  config.json       — Empty object (absent flags default true — TRACE-02)

Subdirectories created (empty, for later operator use):
  srs/  mermaid/  mockup/  backlog/  plugins/
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Seed bodies — minimum useful content for a human inspecting the scaffold
# ---------------------------------------------------------------------------

_PROJECT_MD = """\
---
engagement: ""
product: ""
scope: ""
stakeholders: []
constraints: []
---

# Project

> Fill this file before running ba-srs-analyze for the first time.
> Fields: engagement name, product/system, scope description, stakeholders, constraints.

## Engagement

**Product / System:**

**Scope:**

## Stakeholders

| Role | Name | Notes |
|------|------|-------|
| | | |

## Constraints

- (none)
"""

_REQUIREMENTS_MD = """\
---
version: "0.0"
---

# Requirements

> REQ-ID registry. Add rows as requirements are extracted by ba-srs-analyze.
> Column meanings: ID (unique), Statement (atomic, verifiable), Source (SRS § or doc:span).

## Functional Requirements

| ID | Statement | Source |
|----|-----------|--------|

## Non-Functional Requirements

| ID | Statement | Source |
|----|-----------|--------|
"""

_INDEX_MD = """\
---
version: "0.0"
---

# Traceability Index

> REQ-ID → SRS § → Mermaid diagram → Mockup screen → Backlog story.
> Built by `ba-tools index update`. Orphans and gaps flagged automatically.

## Matrix

| REQ-ID | SRS § | Mermaid | Mockup | Story | Status |
|--------|-------|---------|--------|-------|--------|

## Gaps

(none)

## Orphans

(none)
"""

_STATE_MD = """\
---
step: 0
current_step:
status: init
operator:
uc_id:
uc_name:
phase:
started_at:
updated_at:
completed_at:
last_action:
next_step:
position:
iteration: 0
note:
---

# State

> Living memory for the active use-case pipeline.
> Written by `ba-tools state update|patch|advance`; guarded by STATE.md.lock.

## Pipeline Steps

| Step | Status | Completed At |
|------|--------|--------------|
| srs-analyze | pending | |
| mermaid | pending | |
| mockup | pending | |
| index | pending | |

## Gate Verdicts

| Gate | Verdict | Notes |
|------|---------|-------|

## Blockers

(none)
"""

_CONFIG_JSON = "{}\n"

# Ordered list of (relative-path, seed-content) pairs.
_SEED_FILES: list[tuple[str, str]] = [
    ("PROJECT.md",      _PROJECT_MD),
    ("REQUIREMENTS.md", _REQUIREMENTS_MD),
    ("INDEX.md",        _INDEX_MD),
    ("STATE.md",        _STATE_MD),
    ("config.json",     _CONFIG_JSON),
]

# Subdirectories to create (empty, for later operator writes).
_SUBDIRS: list[str] = ["srs", "mermaid", "mockup", "backlog", "plugins"]


def ensure_scaffold(root: Path) -> dict:
    """Create the .ba-ops/ scaffold under *root* if not already present.

    Idempotent: existing files are never overwritten, so hand-edited content
    is preserved across multiple `init` calls (TOOL-01 idempotency requirement).

    Args:
        root: resolved repository root Path (from resolve_repo_root).

    Returns:
        A dict with keys:
          - ``created``: list of file paths written (empty if all existed).
          - ``existing``: list of file paths that were already present.
    """
    ba_ops = root / ".ba-ops"
    ba_ops.mkdir(parents=True, exist_ok=True)

    # Create subdirectories (idempotent).
    for subdir in _SUBDIRS:
        (ba_ops / subdir).mkdir(exist_ok=True)

    created: list[str] = []
    existing: list[str] = []

    for rel_path, content in _SEED_FILES:
        target = ba_ops / rel_path
        if target.exists():
            existing.append(str(target))
        else:
            target.write_text(content, encoding="utf-8")
            created.append(str(target))

    return {"created": created, "existing": existing}
