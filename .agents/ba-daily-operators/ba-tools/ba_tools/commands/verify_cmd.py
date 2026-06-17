"""ba-tools verify — verbatim citation-exists gate, REQ-ID coverage, hash-match (TOOL-06)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "verify",
        help="Run the verification gate (citation-exists, REQ coverage, hash-match)",
    )
    p.add_argument("--reqs", required=True, help="Requirements file path")
    p.add_argument("--source", required=True, help="Source document to cite from")
    p.add_argument(
        "--cite-scope",
        choices=["section", "document"],
        default="section",
        help="Citation search scope (default: section)",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "verify"}])
