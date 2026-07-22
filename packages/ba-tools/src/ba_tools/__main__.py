"""Single process emission and exit boundary for ba-tools."""

from __future__ import annotations

import sys

import click

from ba_tools.cli import invoke_cli
from ba_tools.contracts import emit_json, error_envelope
from ba_tools.errors import BaToolsError


def _command_name(arguments: list[str]) -> str:
    if "--version" in arguments:
        return "version"
    if not arguments or "--help" in arguments:
        return "help"
    idx = 0
    while idx < len(arguments):
        token = arguments[idx]
        if token in {"--repo-root", "--repair", "--all"}:
            idx += 2 if token == "--repo-root" else 1
            continue
        if token in {"init", "doctor"}:
            return token
        idx += 1
    return "unknown"


def entrypoint(argv: list[str] | None = None) -> int:
    """Invoke the command and emit exactly one safe JSON document."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    command = _command_name(arguments)

    try:
        payload = invoke_cli(arguments)
    except BaToolsError as error:
        emit_json(sys.stderr, error_envelope(command, error))
        return 2
    except click.ClickException:
        error = BaToolsError(
            code="CLI_USAGE_ERROR",
            message="The command arguments are invalid.",
            remediation=("Run ba-tools --help and retry with valid arguments.",),
        )
        emit_json(sys.stderr, error_envelope(command, error))
        return 2
    except (click.Abort, KeyboardInterrupt):
        error = BaToolsError(
            code="COMMAND_INTERRUPTED",
            message="The command was interrupted.",
            remediation=("Retry the command when ready.",),
        )
        emit_json(sys.stderr, error_envelope(command, error))
        return 2
    except Exception:
        error = BaToolsError(
            code="INTERNAL_ERROR",
            message="BA Tools could not complete the command.",
            remediation=("Retry after checking the reported diagnostic code.",),
        )
        emit_json(sys.stderr, error_envelope(command, error))
        return 2

    emit_json(sys.stdout, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(entrypoint())
