"""
Section-scoped Markdown citation verification (TOOL-06).

Exports:
- extract_section(doc_text, section_name) -> str
- citation_exists(source_doc, span, section, cite_scope) -> bool

Source: RESEARCH Pattern 3 (section-scoped Markdown citation verification)
Pitfall 2: normalize section headings with lstrip('#').strip() on both sides.
Pitfall 5: level-aware stop — stop on same-or-higher-level heading only.
"""

import re
from pathlib import Path


def extract_section(doc_text: str, section_name: str) -> str:
    """Return the body text of a named Markdown heading section.

    Searches for a heading whose normalized title matches ``section_name``
    (after stripping leading ``#`` characters and whitespace from both sides —
    Pitfall 2 heading normalization).

    Captures body lines from that heading until a same-or-higher-level heading
    is encountered (level-aware stop — RESEARCH Pitfall 5 / Pattern 3).

    Args:
        doc_text: full text of the Markdown source document.
        section_name: heading title to search for (may include leading ``#``).

    Returns:
        The body text of the found section, or empty string if not found.
    """
    # Normalize the target: strip leading '#' and surrounding whitespace (Pitfall 2)
    target_norm = section_name.lstrip("#").strip().lower()

    heading_re = re.compile(r'^(#{1,6})\s+(.*)', re.MULTILINE)
    lines = doc_text.splitlines(keepends=True)

    target_level: int | None = None
    in_section = False
    body_lines: list[str] = []

    for line in lines:
        m = heading_re.match(line)
        if m:
            level = len(m.group(1))
            # Normalize the heading title the same way (Pitfall 2)
            title = m.group(2).strip().lower()

            if not in_section:
                if title == target_norm:
                    target_level = level
                    in_section = True
            else:
                # Stop at a same-or-higher-level heading (Pitfall 5: level-aware stop)
                if level <= target_level:
                    break
        elif in_section:
            body_lines.append(line)

    return "".join(body_lines)


def citation_exists(
    source_doc: Path,
    span: str,
    section: str | None,
    cite_scope: str = "section",
) -> bool:
    """Return True if ``span`` (>=12 chars) is a verbatim substring of the source doc.

    With ``cite_scope == "section"``, the search is scoped to the named section.
    With ``cite_scope == "document"`` (or no section), the whole document is searched.

    Args:
        source_doc: Path to the source document to search.
        span: verbatim text to find (must be >= 12 characters to be meaningful).
        section: heading name to scope the search to (normalized before lookup).
            If None or empty, searches the whole document regardless of cite_scope.
        cite_scope: "section" (default) or "document" (override, Open Decision #1).

    Returns:
        True if span is found in the appropriate scope; False otherwise.

    Security:
        The caller is responsible for ensuring source_doc is within the repo root
        (T-1-09, T-1-01). This function reads the file as-is.
    """
    # Guard: span too short is always False (RESEARCH Pattern 3)
    if len(span) < 12:
        return False

    doc_text = source_doc.read_text(encoding="utf-8")

    # Document-scope mode: search the whole file
    if cite_scope == "document" or not section or not section.strip():
        return span in doc_text

    # Section-scope mode (default): extract the section body first
    section_text = extract_section(doc_text, section)
    if not section_text:
        # Section not found — cannot verify → False
        return False

    return span in section_text
