"""Click routing whose callbacks return data without emitting product output."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import click

from ba_tools import __version__
from ba_tools.contracts import success_envelope
from ba_tools.errors import BaToolsError


@click.group(
    invoke_without_command=True,
    no_args_is_help=False,
    context_settings={"help_option_names": []},
)
@click.option("--repo-root", type=str, default=None, help="Repository root for business state.")
@click.option("--help", "help_requested", is_flag=True, is_eager=True)
@click.option("--version", "version_requested", is_flag=True, is_eager=True)
@click.pass_context
def cli(
    ctx: click.Context,
    repo_root: str | None,
    help_requested: bool,
    version_requested: bool,
) -> dict[str, object] | None:
    """Route ba-tools commands while leaving all emission to entrypoint."""

    if version_requested:
        assert __version__ == "0.1.0"
        return success_envelope("version", {"version": __version__})

    if help_requested or ctx.invoked_subcommand is None:
        return success_envelope("help", {"help": ctx.get_help()})

    ctx.ensure_object(dict)
    ctx.obj["repo_root"] = repo_root
    return None


@cli.command("init")
@click.option("--repair", is_flag=True, help="Create missing required state files only.")
@click.pass_context
def init_command(ctx: click.Context, repair: bool) -> dict[str, object]:
    """Create the minimal canonical workspace state."""

    from ba_tools.init_command import run_init
    from ba_tools.paths import resolve_repo_root

    repo_root_text = ctx.parent.params.get("repo_root") if ctx.parent is not None else None
    if repo_root_text is None:
        raise BaToolsError(
            code="REPO_ROOT_REQUIRED",
            message="A repository root is required.",
            remediation=("Pass --repo-root before the command.",),
        )

    result = run_init(resolve_repo_root(repo_root_text), repair=repair)
    data: dict[str, object] = {
        "changed": result.changed,
        "created": list(result.created),
    }
    if result.quarantined:
        data["quarantined"] = [asdict(record) for record in result.quarantined]
    return success_envelope(
        "init",
        data,
    )


@cli.command("doctor")
@click.option("--all", "include_all", is_flag=True, help="Include every known optional check.")
@click.pass_context
def doctor_command(ctx: click.Context, include_all: bool) -> dict[str, object]:
    """Return one complete ordered local diagnostic snapshot."""

    from ba_tools.doctor import CheckStatus, run_doctor
    from ba_tools.paths import resolve_repo_root

    repo_root_text = ctx.parent.params.get("repo_root") if ctx.parent is not None else None
    if repo_root_text is None:
        raise BaToolsError(
            code="REPO_ROOT_REQUIRED",
            message="A repository root is required.",
            remediation=("Pass --repo-root before the command.",),
        )

    result = run_doctor(
        resolve_repo_root(repo_root_text),
        include_all=include_all,
    )
    data = result.as_dict()
    if result.status is CheckStatus.FAIL:
        raise BaToolsError(
            code="DOCTOR_FAILED",
            message="One or more required local diagnostics failed.",
            details=(data,),
            remediation=("Apply the reported check remediation, then rerun doctor.",),
        )
    envelope = success_envelope("doctor", data)
    envelope["warnings"] = [
        check.summary
        for check in result.checks
        if check.status is CheckStatus.WARNING
    ]
    return envelope


def invoke_cli(arguments: list[str]) -> dict[str, Any]:
    """Invoke Click without allowing it to print, exit, or serialize."""

    result = cli.main(
        args=arguments,
        prog_name="ba-tools",
        standalone_mode=False,
    )
    if not isinstance(result, dict):
        raise RuntimeError("command returned no result")
    return result
