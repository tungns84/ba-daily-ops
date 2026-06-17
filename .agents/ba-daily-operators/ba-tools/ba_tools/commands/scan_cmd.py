"""ba-tools scan — advisory prompt-injection scan (TOOL-15, D-07/D-08)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "scan",
        help="Run an advisory prompt-injection scan on a file (never blocks, exit 0)",
    )
    p.add_argument("--file", required=True, dest="scan_file", help="File to scan")
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "scan"}])
