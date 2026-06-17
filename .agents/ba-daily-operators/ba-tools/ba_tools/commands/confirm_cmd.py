"""ba-tools confirm — confirm gate before irreversible/outward steps (GATE-02).

In v1 this is a pass-through that always exits 0 (the confirm decision is an
agent-level judgement in Codex chat, not a CLI stdin prompt).  The --yes flag
is present for future non-interactive use.

Per RESEARCH Open Question 2: ba-tools confirm is a pass-through that always
exits 0 in v1; the confirm is an agent-level judgement in Codex chat, not a
CLI stdin prompt.

Does NOT read stdin or block.
"""

from ba_tools.output import ok_json


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "confirm",
        help="Confirm gate (pass-through in v1; always exits 0)",
    )
    p.add_argument(
        "--yes",
        action="store_true",
        help="Bypass prompt (non-interactive, reserved for future use)",
    )
    p.add_argument(
        "--message",
        default="",
        help="Confirm prompt text (informational only)",
    )
    p.set_defaults(func=run)


def run(args) -> None:
    # v1 pass-through: always confirmed, never blocks, never reads stdin (Open Question 2)
    ok_json(confirmed=True, gate="confirm")
