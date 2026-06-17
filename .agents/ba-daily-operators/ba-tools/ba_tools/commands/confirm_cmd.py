"""ba-tools confirm — confirm gate before irreversible/outward steps (GATE-02).

In v1 this is a pass-through that always exits 0 (the confirm decision is an
agent-level judgement in Codex chat, not a CLI stdin prompt).  The --yes flag
is present for future non-interactive use.
"""

from ba_tools.errors import BaToolsError


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "confirm",
        help="Confirm gate (pass-through in v1; always exits 0)",
    )
    p.add_argument("--yes", action="store_true", help="Bypass prompt (non-interactive)")
    p.add_argument("--message", default="", help="Confirm prompt text (informational)")
    p.set_defaults(func=run)


def run(args) -> None:
    raise BaToolsError([{"code": "NOT_IMPLEMENTED", "command": "confirm"}])
