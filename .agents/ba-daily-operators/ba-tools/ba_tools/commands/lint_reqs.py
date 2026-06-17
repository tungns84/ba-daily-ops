"""ba-tools lint-requirements — flag ambiguity, atomicity, grounding, verifiability (TOOL-04, TOOL-05)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "lint-requirements",
        help="Lint a requirements document for quality issues",
    )
    p.add_argument("file", help="Path to requirements file (Markdown or JSON)")
    p.add_argument(
        "--baseline",
        default=None,
        metavar="FILE",
        help="Baseline requirements file for REQ-ID stability check (TOOL-05)",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "lint-requirements"}])
