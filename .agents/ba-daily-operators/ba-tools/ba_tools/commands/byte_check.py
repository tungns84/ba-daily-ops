"""ba-tools byte-check — fail if any eager-loaded doc >= 32768 B (GATE-04, CDX-04)."""

from ba_tools.errors import BaToolsError


CODEX_LIMIT = 32768  # bytes — DESIGN §7 hard limit


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "byte-check",
        help="Fail if any listed file is >= byte limit (default: 32768 B)",
    )
    p.add_argument("paths", nargs="+", help="Files to check (relative to --repo-root)")
    p.add_argument(
        "--limit",
        type=int,
        default=CODEX_LIMIT,
        help=f"Byte limit (default: {CODEX_LIMIT})",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "byte-check"}])
