"""ba-tools scan — advisory prompt-injection scan (TOOL-15, D-07/D-08).

Runs a fixed list of advisory prompt-injection patterns against a file.
NEVER blocks: always exits 0 regardless of findings.
A missing file is the only error path (FILE_NOT_FOUND, exit 2).

Per Open Decision #2 (RESEARCH): WARN_INJECTION is advisory in v1.
Per D-07/D-08: subjective/injection signals WARN, never gate (no exit 2 on content).
Per T-1-02: findings flagged WARN, never auto-fed back into agent prompts.

Output on match:
  ok_json(findings=[{"severity": "warn", "pattern": <pattern>, "line": <n>}], blocked=False)
Output on clean:
  ok_json(findings=[], blocked=False)
"""

import re

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import resolve_repo_root, resolve_under_root

# Advisory prompt-injection patterns (never block — always WARN only)
# Each tuple: (human-readable name, compiled pattern)
_INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("ignore previous instructions",
     re.compile(r"ignore\s+previous\s+instructions?", re.IGNORECASE)),
    ("disregard the above",
     re.compile(r"disregard\s+the\s+above", re.IGNORECASE)),
    ("disregard previous",
     re.compile(r"disregard\s+previous", re.IGNORECASE)),
    ("system prompt",
     re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE)),
    ("forget your instructions",
     re.compile(r"forget\s+your\s+instructions?", re.IGNORECASE)),
    ("you are now",
     re.compile(r"\byou\s+are\s+now\b", re.IGNORECASE)),
    ("act as",
     re.compile(r"\bact\s+as\s+(?:a|an)\b", re.IGNORECASE)),
    ("new role",
     re.compile(r"\bnew\s+role\b", re.IGNORECASE)),
    ("override instructions",
     re.compile(r"\boverride\s+instructions?\b", re.IGNORECASE)),
    ("pretend you are",
     re.compile(r"\bpretend\s+you\s+are\b", re.IGNORECASE)),
]


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "scan",
        help="Run an advisory prompt-injection scan on a file (never blocks, exit 0)",
    )
    p.add_argument("--file", required=True, dest="scan_file", help="File to scan")
    p.set_defaults(func=run)


def run(args) -> None:
    repo_root = resolve_repo_root(getattr(args, "repo_root", None))

    # Resolve file path under repo root (T-1-01) via the shared helper (WR-04)
    candidate = resolve_under_root(args.scan_file, repo_root)

    if not candidate.exists():
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "file": args.scan_file,
        }])

    # Read file content — file content is untrusted (prompt-injection surface)
    content = candidate.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    findings: list[dict] = []
    for lineno, line_text in enumerate(lines, start=1):
        for pattern_name, pattern in _INJECTION_PATTERNS:
            if pattern.search(line_text):
                findings.append({
                    "severity": "warn",
                    "pattern": pattern_name,
                    "line": lineno,
                })

    # Advisory only — ALWAYS exit 0, never raise BaToolsError on content (D-07/D-08)
    ok_json(findings=findings, blocked=False)
