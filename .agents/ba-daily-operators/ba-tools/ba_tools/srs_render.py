"""Deterministic JSON → Markdown renderer for IEEE-830 SRS and REQUIREMENTS registry.

Exported:
    render_srs(reqs_doc: dict, template_text: str) -> str
        Pure function. Renders one slug's requirements.json into a full IEEE-830 SRS.md.

    render_registry(reqs_docs: list[dict]) -> str
        Pure function. Takes the LIST of ALL slugs' docs and renders the UNION of every
        requirement as REQUIREMENTS.md (D-08 — single-slug render is forbidden).

Design:
    - Both functions are pure: no I/O, no nondeterminism, no model-client imports.
    - Requirements are grouped by id prefix: FR-* → §3.1, NFR-* → §3.2, BR-* → §3.3,
      others (EI-*, CON-*, etc.) → §3.4 / §3.5.
    - Output is deterministic: requirements are sorted by id (lexicographic) within
      each group; no timestamps, no random UUIDs in requirement rows.
    - Template substitution uses string.Template.safe_substitute — unknown ${vars}
      remain as-is in the rendered output (consistent with template_cmd.py pattern).

Determinism boundary (D-05, DESIGN §5):
    - NO import of openai, anthropic, or any model client.
    - No random or time-based content in rendered requirement rows.
    - Rendering the same requirements.json twice always produces byte-identical output.
"""

import string
from typing import Any


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_reqs_list(reqs_doc: dict) -> list[dict]:
    """Extract the flat list of requirements from a reqs_doc dict.

    Accepts:
      - {"requirements": [...]}  (standard shape)
      - a plain list passed directly (for internal use)
    """
    if isinstance(reqs_doc, list):
        return list(reqs_doc)
    return list(reqs_doc.get("requirements", []))


def _group_requirements(reqs_list: list[dict]) -> dict[str, list[dict]]:
    """Group requirements by their id prefix for IEEE-830 §3 subsections.

    Groups:
        "fr"  → FR-* (3.1 Functional Requirements)
        "nfr" → NFR-* (3.2 Non-Functional Requirements)
        "br"  → BR-* (3.3 Business Rules)
        "ei"  → EI-* (3.4 External Interfaces)
        "con" → CON-* (3.5 Constraints)
        "other" → everything else (appended to the nearest applicable section)

    Within each group, requirements are sorted by id (case-insensitive lexicographic).
    """
    groups: dict[str, list[dict]] = {
        "fr": [],
        "nfr": [],
        "br": [],
        "ei": [],
        "con": [],
        "other": [],
    }
    for req in reqs_list:
        rid = str(req.get("id", "")).upper()
        if rid.startswith("FR-"):
            groups["fr"].append(req)
        elif rid.startswith("NFR-"):
            groups["nfr"].append(req)
        elif rid.startswith("BR-"):
            groups["br"].append(req)
        elif rid.startswith("EI-"):
            groups["ei"].append(req)
        elif rid.startswith("CON-"):
            groups["con"].append(req)
        else:
            groups["other"].append(req)

    for key in groups:
        groups[key].sort(key=lambda r: str(r.get("id", "")).upper())

    return groups


def _req_to_md_row(req: dict) -> str:
    """Render a single requirement as a Markdown table row.

    Format: | ID | Statement | Status |
    """
    req_id = str(req.get("id", "")).strip()
    statement = str(req.get("statement", "")).strip()
    status = str(req.get("status", "stated")).strip()
    return f"| {req_id} | {statement} | {status} |"


def _reqs_to_md_table(reqs: list[dict]) -> str:
    """Render a list of requirements as a Markdown table.

    Returns an empty string if the list is empty.
    """
    if not reqs:
        return "_No requirements in this category._"
    header = "| ID | Statement | Status |\n|----|-----------|--------|\n"
    rows = "\n".join(_req_to_md_row(r) for r in reqs)
    return header + rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_srs(reqs_doc: dict, template_text: str) -> str:
    """Render one slug's requirements.json into an IEEE-830 SRS Markdown document.

    Args:
        reqs_doc: The parsed requirements.json content (top-level dict with
                  {"requirements": [...]} or a plain list).
        template_text: The full IEEE-830 template text (string.Template format,
                       ${...} placeholders). Usually read from ba-core/templates/srs.md.

    Returns:
        A rendered Markdown string. Deterministic: same inputs → byte-identical output.

    Notes:
        - Nondeterministic fields (${title}, ${date}, ${author}, ${slug}, etc.) are left
          as-is via safe_substitute — the caller or render_cmd may supply them.
        - Requirement rows are sorted by id within each §3 subsection.
        - No model-client imports; no I/O side effects.
    """
    reqs_list = _extract_reqs_list(reqs_doc)
    groups = _group_requirements(reqs_list)

    # Build section content strings
    fr_table = _reqs_to_md_table(groups["fr"])
    nfr_table = _reqs_to_md_table(groups["nfr"])
    br_table = _reqs_to_md_table(groups["br"])

    # External interfaces: EI-* + anything labeled "interface" (fallback: other)
    ei_table = _reqs_to_md_table(groups["ei"])
    con_table = _reqs_to_md_table(groups["con"])

    # Traceability: render as a table mapping each req.id to its source_trace.doc+section
    traceability_rows = []
    all_sorted = sorted(reqs_list, key=lambda r: str(r.get("id", "")).upper())
    for req in all_sorted:
        req_id = str(req.get("id", "")).strip()
        st = req.get("source_trace", {})
        if isinstance(st, dict):
            doc = str(st.get("doc", "") or "").strip()
            section = str(st.get("section", "") or "").strip()
        else:
            doc = str(st).strip() if st else ""
            section = ""
        traceability_rows.append(f"| {req_id} | {doc} | {section} |")

    if traceability_rows:
        trace_table = (
            "| ID | Source Document | Section |\n"
            "|----|----------------|---------|\n"
        ) + "\n".join(traceability_rows)
    else:
        trace_table = "_No traceability data available._"

    variables = {
        "functional_requirements": fr_table,
        "nonfunctional_requirements": nfr_table,
        "business_rules": br_table,
        "external_interfaces": ei_table,
        "constraints": con_table,
        "traceability": trace_table,
    }

    tpl = string.Template(template_text)
    return tpl.safe_substitute(variables)


def render_registry(reqs_docs: list[dict]) -> str:
    """Render the REQUIREMENTS.md registry as the UNION of all slugs' requirements.

    CRITICAL (D-08, review Codex HIGH):
        This function ALWAYS takes a list of ALL slugs' docs. Passing a single slug's
        doc is a programming error — use render_srs() for per-slug SRS rendering.
        A single-slug render_registry call would silently drop all other slugs' reqs.

    Args:
        reqs_docs: List of parsed requirements.json dicts, one per slug. May be empty.

    Returns:
        A Markdown string for REQUIREMENTS.md containing ALL requirements from ALL
        slugs, sorted deterministically by id (lexicographic, case-insensitive).
        Byte-identical output for the same inputs (no timestamps, no random content).
    """
    # Union: gather all requirements from all docs
    all_reqs: list[dict] = []
    for doc in reqs_docs:
        all_reqs.extend(_extract_reqs_list(doc))

    # Sort deterministically: by id (case-insensitive lexicographic)
    all_reqs_sorted = sorted(all_reqs, key=lambda r: str(r.get("id", "")).upper())

    # Build the registry Markdown
    lines = [
        "# Requirements Registry",
        "",
        "This file is the union of all slugs' `requirements.json` files.",
        "It is rendered deterministically by `ba-tools render registry`.",
        "**Do not edit manually** — edit the canonical `requirements.json` and re-render.",
        "",
    ]

    if not all_reqs_sorted:
        lines.append("_No requirements found across all slugs._")
    else:
        lines.append("| ID | Statement | Status | Source Document |")
        lines.append("|----|-----------|--------|----------------|")
        for req in all_reqs_sorted:
            req_id = str(req.get("id", "")).strip()
            statement = str(req.get("statement", "")).strip()
            status = str(req.get("status", "stated")).strip()
            st = req.get("source_trace", {})
            if isinstance(st, dict):
                doc = str(st.get("doc", "") or "").strip()
            else:
                doc = str(st).strip() if st else ""
            lines.append(f"| {req_id} | {statement} | {status} | {doc} |")

    return "\n".join(lines) + "\n"
