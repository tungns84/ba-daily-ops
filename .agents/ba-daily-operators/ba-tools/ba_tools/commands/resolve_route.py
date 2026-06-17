"""ba-tools resolve-route — return the default route for an operator (TOOL-02)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "resolve-route",
        help="Return the default route for a named operator",
    )
    p.add_argument("operator", help="Operator name (e.g. ba-mermaid)")
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "resolve-route"}])
