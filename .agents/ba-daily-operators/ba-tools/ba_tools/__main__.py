"""
ba-tools CLI entry point — argparse dispatcher (TOOL-13, TOOL-14).

Every command module under ba_tools.commands exposes:
  register(subparsers) — adds its subparser and calls set_defaults(func=run)
  run(args)            — implements the command; raises BaToolsError on failure

The dispatcher catches BaToolsError and prints {"ok": false, "failures": [...]}
to stderr then exits 2 (D-04).  KeyboardInterrupt exits 130.
"""

import argparse
import json
import sys

from ba_tools.errors import BaToolsError
from ba_tools.commands import (
    init_cmd,
    resolve_route,
    state_cmd,
    lint_reqs,
    verify_cmd,
    uc_status,
    extract_uc,
    template_cmd,
    discovery_cmd,
    scan_cmd,
    byte_check,
    confirm_cmd,
)

_COMMAND_MODULES = [
    init_cmd,
    resolve_route,
    state_cmd,
    lint_reqs,
    verify_cmd,
    uc_status,
    extract_uc,
    template_cmd,
    discovery_cmd,
    scan_cmd,
    byte_check,
    confirm_cmd,
]


def build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="ba-tools",
        description="Deterministic BA operator CLI",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        metavar="PATH",
        help="Project root directory (default: git root or cwd)",
    )
    subs = parser.add_subparsers(dest="command", required=True)
    for mod in _COMMAND_MODULES:
        mod.register(subs)
    return parser


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command handler."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except BaToolsError as exc:
        print(
            json.dumps({"ok": False, "failures": exc.failures}, ensure_ascii=False),
            file=sys.stderr,
        )
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
