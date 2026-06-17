"""ba-tools uc-status — return single-UC pipeline state and next_step (TOOL-09)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "uc-status",
        help="Return pipeline state and next_step for a use-case",
    )
    p.add_argument("--uc", required=True, help="Use-case ID (e.g. UC-001)")
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "uc-status"}])
