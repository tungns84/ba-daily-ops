"""ba-tools template fill — scaffold artifacts from ba-core/templates (TOOL-11).

Fills a named Markdown template from ba-core/templates using Python's
string.Template substitution (${VAR} syntax), then writes the result to --out.

Security:
  PATH_ESCAPE — --out must resolve under repo root (T-1-09).
  TEMPLATE_NOT_FOUND — requested template name does not exist in ba-core/templates.
"""

import string
from pathlib import Path

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import is_within_root, resolve_repo_root, resolve_under_root


def _templates_dir(repo_root: Path) -> Path:
    """Return the path to ba-core/templates relative to repo root."""
    return repo_root / ".agents" / "ba-daily-operators" / "ba-tools" / "ba-core" / "templates"


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "template",
        help="Fill and write an artifact template",
    )
    sub = p.add_subparsers(dest="template_action", required=True)
    fill_p = sub.add_parser("fill", help="Fill a named template with provided fields")
    fill_p.add_argument("name", help="Template name (e.g. srs, requirements)")
    fill_p.add_argument(
        "--out",
        required=True,
        help="Output file path (must be under repo-root)",
    )
    fill_p.add_argument(
        "--var",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Template variable substitution (repeatable)",
    )
    fill_p.set_defaults(func=run)
    p.set_defaults(func=run)


def run(args) -> None:
    repo_root = resolve_repo_root(getattr(args, "repo_root", None))

    action = getattr(args, "template_action", None)
    if action != "fill":
        raise BaToolsError([{"code": "UNKNOWN_ACTION", "action": action}])

    # Resolve --out via the shared helper, then guard path traversal (T-1-09, WR-04)
    out_path = resolve_under_root(args.out, repo_root)

    if not is_within_root(out_path, repo_root):
        raise BaToolsError([{
            "code": "PATH_ESCAPE",
            "out": args.out,
            "reason": "--out path escapes repo root",
        }])

    # Locate template file (try <name>.md then bare <name>)
    tpl_dir = _templates_dir(repo_root)
    tpl_file = tpl_dir / f"{args.name}.md"
    if not tpl_file.exists():
        tpl_file = tpl_dir / args.name
    if not tpl_file.exists():
        raise BaToolsError([{
            "code": "TEMPLATE_NOT_FOUND",
            "name": args.name,
            "templates_dir": str(tpl_dir),
        }])

    tpl_text = tpl_file.read_text(encoding="utf-8")

    # Parse --var KEY=VALUE pairs
    variables: dict[str, str] = {}
    for var_spec in args.var:
        if "=" not in var_spec:
            raise BaToolsError([{
                "code": "BAD_VAR",
                "var": var_spec,
                "reason": "expected KEY=VALUE format",
            }])
        key, _, value = var_spec.partition("=")
        variables[key.strip()] = value

    # Substitute — use safe_substitute so unknown ${vars} remain as-is
    tpl = string.Template(tpl_text)
    filled = tpl.safe_substitute(variables)

    # Ensure parent directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(filled, encoding="utf-8")

    ok_json(out=str(out_path))
