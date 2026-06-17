"""ba-tools discovery — capture and list iteration discoveries (TOOL-12).

Appends discovery entries to .ba-ops/discoveries.jsonl (created on first add).
Each entry is a JSON object: {"ts": "<ISO-8601>", "note": "<text>", "tag": "<tag or null>"}.

Subcommands:
  add  --note <text> [--tag <tag>]   Append a discovery entry.
  list [--uc <uc-id>]                List all discoveries (optionally filtered by tag/uc).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import resolve_repo_root


def _discoveries_path(repo_root: Path) -> Path:
    return repo_root / ".ba-ops" / "discoveries.jsonl"


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "discovery",
        help="Capture and list iteration discoveries",
    )
    sub = p.add_subparsers(dest="discovery_action", required=True)

    add_p = sub.add_parser("add", help="Append a discovery to .ba-ops/discoveries.jsonl")
    add_p.add_argument("--note", required=True, help="Discovery note text")
    add_p.add_argument("--tag", default=None, help="Optional tag (e.g. UC-001)")
    add_p.set_defaults(func=run)

    list_p = sub.add_parser("list", help="List all discoveries")
    list_p.add_argument(
        "--uc",
        default=None,
        dest="filter_tag",
        help="Filter by tag/UC ID (optional)",
    )
    list_p.set_defaults(func=run)

    p.set_defaults(func=run)


def run(args) -> None:
    repo_root = resolve_repo_root(getattr(args, "repo_root", None))
    action = getattr(args, "discovery_action", None)

    if action == "add":
        _add(args, repo_root)
    elif action == "list":
        _list(args, repo_root)
    else:
        raise BaToolsError([{"code": "UNKNOWN_ACTION", "action": action}])


def _add(args, repo_root: Path) -> None:
    discoveries_file = _discoveries_path(repo_root)
    discoveries_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "note": args.note,
        "tag": getattr(args, "tag", None),
    }
    with discoveries_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    ok_json(added=True, tag=entry["tag"])


def _list(args, repo_root: Path) -> None:
    discoveries_file = _discoveries_path(repo_root)

    if not discoveries_file.exists():
        ok_json(discoveries=[])
        return

    filter_tag = getattr(args, "filter_tag", None)
    entries: list[dict] = []
    for raw_line in discoveries_file.read_text(encoding="utf-8").splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            entry = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if filter_tag is None or entry.get("tag") == filter_tag:
            entries.append(entry)

    ok_json(discoveries=entries)
