"""ba-tools extract-uc — extract a UC section and parsed identity from a document (TOOL-10).

UC spec format: "<file>: ## UC-001. <name>"
  - <file>    path to the Markdown document (resolved under repo root — T-1-01)
  - ## UC-001 the heading prefix that identifies the heading level (count of #)
  - UC-001    the UC identifier (REQ-ID pattern: UC-\d+)
  - <name>    the UC name (rest of heading after the UC-NNN prefix)

Errors:
  BAD_SPEC        — spec string does not match expected format
  UC_NOT_FOUND    — heading is not present in the referenced file
  FILE_NOT_FOUND  — the source file does not exist or is outside repo root
"""

import re
from pathlib import Path

from ba_tools.errors import BaToolsError
from ba_tools.markdown_sections import extract
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root

# UC spec:  "<file>: ## UC-NNN. <name>"
# Groups:   (file_part)   (level_hashes)  (uc_id)            (uc_name)
_SPEC_RE = re.compile(
    r"^(.+?):\s*(#{1,6})\s+(UC-\d+)\.\s+(.+)$"
)


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "extract-uc",
        help="Extract a UC section and identity from a Markdown document",
    )
    p.add_argument(
        "--uc",
        required=True,
        help="UC spec string: '<file>: ## UC-NNN. <name>'",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    repo_root = resolve_repo_root(getattr(args, "repo_root", None))
    spec = args.uc.strip()

    m = _SPEC_RE.match(spec)
    if not m:
        raise BaToolsError([{
            "code": "BAD_SPEC",
            "spec": spec,
            "expected": "<file>: ## UC-NNN. <name>",
        }])

    file_part, hashes, uc_id, uc_name = m.group(1).strip(), m.group(2), m.group(3), m.group(4).strip()
    heading_level = len(hashes)

    # Full heading text as it appears after the hashes (e.g. "UC-001. My Use Case")
    heading_text = f"{uc_id}. {uc_name}"

    # Resolve the source file under repo root (T-1-01)
    candidate = Path(file_part)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    candidate = candidate.resolve()

    if not is_within_root(candidate, repo_root):
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "file": file_part,
            "reason": "path escapes repo root",
        }])

    if not candidate.exists():
        raise BaToolsError([{
            "code": "FILE_NOT_FOUND",
            "file": file_part,
        }])

    doc_text = candidate.read_text(encoding="utf-8")
    section_body = extract(doc_text, heading_text, level=heading_level)

    if section_body is None:
        raise BaToolsError([{
            "code": "UC_NOT_FOUND",
            "uc_id": uc_id,
            "heading": heading_text,
            "file": file_part,
        }])

    ok_json(
        uc_id=uc_id,
        uc_name=uc_name,
        section=section_body,
        source_file=file_part,
    )
