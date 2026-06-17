"""
Level-aware Markdown heading section extractor (TOOL-10, Pitfall 5).

Extracts the body of a named heading section from a Markdown document.
Stops only at a heading at the SAME or HIGHER level (fewer or equal '#'),
never at a deeper subsection — this is the Pitfall-5 fix.

Reused by extract-uc and any other command that needs section-scoped text.
"""

import re

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)", re.MULTILINE)


def extract(doc_text: str, heading: str, level: int | None = None) -> str | None:
    """Extract the body of a section identified by its heading text.

    Iterates the document lines, finds the heading whose normalised title
    matches ``heading`` (case-insensitive strip), records its ``#``-count as
    ``found_level``, then captures every subsequent line until a heading at
    ``found_level`` or HIGHER (i.e. fewer or equal ``#`` characters) is seen.
    Deeper headings (more ``#``) are included in the captured body (Pitfall 5).

    Args:
        doc_text: raw Markdown document text.
        heading: the heading text to search for (without leading ``#`` marks).
                 Compared after stripping whitespace, case-insensitively.
        level:   if provided, only match a heading at exactly this ``#``-count.
                 Pass ``None`` to match any level.

    Returns:
        The section body string (lines after the heading, up to but NOT
        including the stop-heading line), or ``None`` if the heading is not
        found.
    """
    lines = doc_text.splitlines(keepends=True)
    found_level: int | None = None
    body_lines: list[str] = []
    in_section = False

    heading_normalised = heading.strip().lower()

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            hashes, title = m.group(1), m.group(2).strip()
            h_level = len(hashes)

            if in_section:
                # Stop if this heading is at the same or higher level (fewer #)
                if h_level <= found_level:
                    break
                # Deeper heading — include it in the body
                body_lines.append(line)
            else:
                # Check whether this heading matches our search target
                title_normalised = title.lower()
                level_match = (level is None) or (h_level == level)
                if level_match and title_normalised == heading_normalised:
                    found_level = h_level
                    in_section = True
                    # Do NOT include the heading line itself in the body
        else:
            if in_section:
                body_lines.append(line)

    if not in_section:
        return None

    return "".join(body_lines)
