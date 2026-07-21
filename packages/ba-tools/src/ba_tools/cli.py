"""Click routing whose callbacks return data without emitting product output."""

from __future__ import annotations

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
@click.pass_context
def init_command(ctx: click.Context) -> dict[str, object]:
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

    result = run_init(resolve_repo_root(repo_root_text))
    return success_envelope(
        "init",
        {
            "changed": result.changed,
            "created": list(result.created),
        },
    )


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
