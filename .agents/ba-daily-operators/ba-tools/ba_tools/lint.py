"""
Deterministic requirements quality heuristics (TOOL-04, TOOL-05).

All checks are pattern-based (regex/word-set) — no ML/NLP imports.
Heuristics are tunable constants; agents own all judgement calls.

Exports:
- WEASEL_WORDS: list of ambiguity signal words
- normalize_statement(text) -> set[str]: lowercase word-set for Jaccard
- MATERIAL_CHANGE_THRESHOLD: float constant (Jaccard threshold)
- is_material_change(old, new) -> bool: True when similarity < threshold
- check_ambiguity(req_id, statement) -> dict | None: WARN finding or None
- check_verifiability(req_id, statement) -> dict | None: FAIL finding or None
- check_atomicity(req_id, statement) -> dict | None: FAIL finding or None
- check_grounding(req_id, row) -> dict | None: FAIL finding or None
- detect_reqid_issues(old_reqs, new_reqs) -> list[dict]: FAIL findings
"""

import re

# ---------------------------------------------------------------------------
# Weasel words — ambiguity signal list (tunable, RESEARCH Assumption A2)
# WARN severity only (D-07). Use word-boundary (\b) to avoid false positives
# inside compound terms (RESEARCH Pitfall 4).
# ---------------------------------------------------------------------------

WEASEL_WORDS: list[str] = [
    "flexible",
    "fast",
    "quick",
    "slow",
    "easy",
    "simple",
    "intuitive",
    "user-friendly",
    "friendly",
    "efficient",
    "effectively",
    "effectively",
    "appropriate",
    "adequate",
    "reasonable",
    "sufficient",
    "robust",
    "reliable",
    "scalable",
    "seamless",
    "smooth",
    "nice",
    "good",
    "better",
    "best",
    "minimal",
    "maximum",
    "optimized",
    "optimal",
    "high",
    "low",
    "various",
    "several",
    "many",
    "some",
    "often",
    "usually",
    "typically",
    "quickly",
    "slowly",
    "easily",
    "as needed",
    "where possible",
    "if necessary",
    "up-to-date",
    "state-of-the-art",
]

# ---------------------------------------------------------------------------
# Measurable/verifiable cues — if ANY of these appear, the statement is
# considered verifiable. This list is intentionally permissive to avoid
# over-flagging (RESEARCH Pitfall 4 spirit applied to verifiability).
# ---------------------------------------------------------------------------

_VERIFIABLE_PATTERNS: list[re.Pattern] = [
    re.compile(r'\b\d+\s*(ms|milliseconds?|seconds?|minutes?|hours?|days?)\b', re.IGNORECASE),
    re.compile(r'\b\d+\s*%\b'),                           # percentage threshold
    re.compile(r'\b\d+\s*(bytes?|kb|mb|gb|tb)\b', re.IGNORECASE),  # byte size
    re.compile(r'\b(within|less than|at most|no more than|at least|greater than|more than|exactly)\s+\d+', re.IGNORECASE),
    re.compile(r'\b\d+\b'),                                # any integer (measurable quantity)
    re.compile(r'\bshall\b', re.IGNORECASE),              # normative language
    re.compile(r'\bmust\b', re.IGNORECASE),               # normative language
    re.compile(r'\b(return|output|print|write|read|create|delete|update|validate|reject|accept|log|emit)\b', re.IGNORECASE),
    re.compile(r'\b(exit|code|json|utf-8|utf8|ascii|iso)\b', re.IGNORECASE),
    re.compile(r'\b(true|false|null|zero|empty|none)\b', re.IGNORECASE),
    re.compile(r'`[^`]+`'),                               # backtick-quoted identifier (concrete)
]

# ---------------------------------------------------------------------------
# Conjunction patterns for atomicity detection (FAIL-class per D-07).
# Detect "shall do X and Y" / "shall do X or Y" patterns.
# These signal two distinct testable clauses joined in one requirement.
# ---------------------------------------------------------------------------

# Require a SECOND normative verb after the conjunction (WR-07). The previous
# final alternative `[a-z]{3,}` matched any lowercase word >=3 chars, so any
# normative sentence containing 'and'/'or' followed by almost any word was
# flagged ATOMICITY_COMPOUND — a FAIL-class gate. E.g. "shall log errors and
# warnings" / "shall accept JSON or YAML input" are single atomic requirements
# and must NOT fail. Demanding a second normative verb only flags genuine
# multi-obligation requirements ("shall X and shall Y").
_CONJUNCTION_PATTERN = re.compile(
    r'\b(shall|must|will|should)\b[^.]*?\b(and|or)\b[^.]*?\b(shall|must|will|should)\b',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Normalization + Jaccard similarity (TOOL-05)
# ---------------------------------------------------------------------------


def normalize_statement(text: str) -> set[str]:
    """Return a lowercase word-set suitable for Jaccard similarity.

    Strips punctuation (keeps only alpha words ≥ 2 chars).
    Source: RESEARCH Pattern 5.
    """
    return set(re.findall(r'\b[a-z]{2,}\b', text.lower()))


#: Jaccard similarity threshold; below = material change (RESEARCH Assumption A1)
MATERIAL_CHANGE_THRESHOLD: float = 0.75


def is_material_change(old_text: str, new_text: str) -> bool:
    """Return True when old and new statements differ materially.

    Uses Jaccard similarity on word-sets. Similarity below
    MATERIAL_CHANGE_THRESHOLD is considered a material change.

    Edge cases:
    - Both empty → False (no change)
    - One empty → True (total replacement)

    Source: RESEARCH Pattern 5.
    """
    old_words = normalize_statement(old_text)
    new_words = normalize_statement(new_text)
    if not old_words and not new_words:
        return False
    if not old_words or not new_words:
        return True  # total replacement
    intersection = old_words & new_words
    union = old_words | new_words
    similarity = len(intersection) / len(union)
    return similarity < MATERIAL_CHANGE_THRESHOLD


# ---------------------------------------------------------------------------
# Per-check heuristics
# ---------------------------------------------------------------------------


def check_ambiguity(req_id: str, statement: str) -> dict | None:
    """Return a WARN finding if the statement contains a weasel word.

    Uses \\b word-boundary anchors to prevent false matches inside compound
    terms (RESEARCH Pitfall 4). Severity is always 'warn' (D-07).
    """
    for word in WEASEL_WORDS:
        # Build a pattern that handles hyphenated weasel words too
        pattern = re.compile(
            r'\b' + re.escape(word) + r'\b',
            re.IGNORECASE,
        )
        if pattern.search(statement):
            return {
                "severity": "warn",
                "code": "AMBIGUITY_WEASEL",
                "req_id": req_id,
                "message": f"Ambiguous term '{word}' found — consider a measurable alternative.",
                "match": word,
            }
    return None


def check_verifiability(req_id: str, statement: str) -> dict | None:
    """Return a FAIL finding if the statement lacks any measurable/verifiable cue.

    A statement is considered verifiable if any of the _VERIFIABLE_PATTERNS
    match. This is a permissive check — only very vague statements fail.
    """
    for pattern in _VERIFIABLE_PATTERNS:
        if pattern.search(statement):
            return None  # verifiable
    return {
        "severity": "fail",
        "code": "VERIFIABILITY_MISSING",
        "req_id": req_id,
        "message": (
            "No measurable/verifiable cue found. "
            "Add a threshold, quantity, format, or normative verb."
        ),
    }


def check_atomicity(req_id: str, statement: str) -> dict | None:
    """Return a FAIL finding if the statement joins two distinct clauses.

    Detects 'shall ... and/or ... verb' patterns suggesting two testable
    obligations in one requirement.
    """
    if _CONJUNCTION_PATTERN.search(statement):
        return {
            "severity": "fail",
            "code": "ATOMICITY_COMPOUND",
            "req_id": req_id,
            "message": (
                "Requirement appears to contain multiple testable clauses joined by 'and'/'or'. "
                "Split into separate requirements."
            ),
        }
    return None


def check_grounding(req_id: str, row: dict) -> dict | None:
    """Return a FAIL finding if a 'stated' requirement lacks a source_trace / source citation.

    A requirement with status 'stated' (or blank status) must have a non-empty
    source value in either 'source_trace' or 'source' field.
    """
    status = row.get("status", "stated").strip().lower()
    # Only 'stated' requirements require grounding; 'derived'/'inferred' may not
    if status not in {"stated", ""}:
        return None

    source_trace = row.get("source_trace", "").strip()
    source = row.get("source", "").strip()

    if not source_trace and not source:
        return {
            "severity": "fail",
            "code": "GROUNDING_MISSING",
            "req_id": req_id,
            "message": (
                "Stated requirement lacks a source citation. "
                "Add a source_trace or source field referencing the originating document."
            ),
        }
    return None


def check_citation_present(req_id: str, row: dict) -> dict | None:
    """Return a FAIL finding if a requirement references a section but has no cited span.

    This is a structural check only — whether the span is verbatim in the source
    is verified by citation.citation_exists (the verify command).
    """
    source_trace = row.get("source_trace", {})
    if isinstance(source_trace, dict):
        span = source_trace.get("span", "").strip()
        doc = source_trace.get("doc", "").strip()
        if doc and not span:
            return {
                "severity": "fail",
                "code": "CITATION_SPAN_MISSING",
                "req_id": req_id,
                "message": (
                    "source_trace has a 'doc' reference but no 'span'. "
                    "Add a >=12-char verbatim span from the cited section."
                ),
            }
    return None


# ---------------------------------------------------------------------------
# REQ-ID stability: two-pass detector (TOOL-05, RESEARCH Pattern 5 + Pitfall 6)
# ---------------------------------------------------------------------------


def detect_reqid_issues(
    old_reqs: dict[str, str],
    new_reqs: dict[str, str],
) -> list[dict]:
    """Detect REQ-ID stability problems via two-pass comparison.

    Pass 1 — existing IDs with material statement changes:
        For each ID present in both old and new, flag if is_material_change.

    Pass 2 — new IDs that are silent renames of old IDs:
        For each ID in new_reqs that is NOT in old_reqs, compare its
        normalized statement to every old statement. If similarity is above
        threshold, flag REQ_ID_RENUMBERED.

    Args:
        old_reqs: {req_id: statement_text} from the baseline file.
        new_reqs: {req_id: statement_text} from the current file.

    Returns:
        List of FAIL-class findings (always severity='fail' per D-07).
    """
    findings = []

    # Pass 1: same ID, material statement change
    for req_id in new_reqs:
        if req_id in old_reqs:
            if is_material_change(old_reqs[req_id], new_reqs[req_id]):
                findings.append({
                    "severity": "fail",
                    "code": "REQ_ID_MATERIAL_CHANGE",
                    "req_id": req_id,
                    "message": (
                        f"Statement for {req_id} changed materially from the baseline. "
                        "Update the REQ-ID if the requirement has truly changed."
                    ),
                })

    # Pass 2: new IDs whose normalized statement closely matches an old statement
    new_only_ids = set(new_reqs.keys()) - set(old_reqs.keys())
    for new_id in new_only_ids:
        new_words = normalize_statement(new_reqs[new_id])
        if not new_words:
            continue
        for old_id, old_stmt in old_reqs.items():
            old_words = normalize_statement(old_stmt)
            if not old_words:
                continue
            intersection = new_words & old_words
            union = new_words | old_words
            similarity = len(intersection) / len(union) if union else 0.0
            # A similarity at or above threshold means this new ID looks like a rename
            if similarity >= MATERIAL_CHANGE_THRESHOLD:
                findings.append({
                    "severity": "fail",
                    "code": "REQ_ID_RENUMBERED",
                    "req_id": new_id,
                    "old_req_id": old_id,
                    "message": (
                        f"New ID {new_id} appears to be a silent renumber of {old_id} "
                        f"(statement similarity {similarity:.2f} >= threshold "
                        f"{MATERIAL_CHANGE_THRESHOLD}). "
                        "Explicitly document the renaming decision."
                    ),
                })
                break  # Report once per new ID

    return findings
