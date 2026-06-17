"""ba-tools init — scaffold .ba-ops/ and return context JSON (TOOL-01, TRACE-01)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "init",
        help="Scaffold .ba-ops/ directory and return operator context JSON",
    )
    p.add_argument("operator", help="Operator name (e.g. ba-uc, ba-srs-analyze)")
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "init"}])
