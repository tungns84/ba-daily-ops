"""ba-tools template — scaffold artifacts from ba-core/templates (TOOL-11)."""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "template",
        help="Fill and write an artifact template",
    )
    sub = p.add_subparsers(dest="template_action", required=True)
    fill_p = sub.add_parser("fill", help="Fill a named template with provided fields")
    fill_p.add_argument("name", help="Template name (e.g. srs, requirements)")
    fill_p.add_argument("--out", required=True, help="Output file path (must be under repo-root)")
    fill_p.add_argument("--var", action="append", default=[], metavar="KEY=VALUE",
                        help="Template variable substitution (repeatable)")
    fill_p.set_defaults(func=run)
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "template"}])
