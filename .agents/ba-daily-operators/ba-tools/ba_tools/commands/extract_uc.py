"""ba-tools extract-uc — extract a UC section and parsed identity from a document (TOOL-10)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "extract-uc",
        help="Extract a UC section and identity from a Markdown document",
    )
    p.add_argument("--uc", required=True, help="UC spec string: '<file>: ## UC-NNN. <name>'")
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "extract-uc"}])
