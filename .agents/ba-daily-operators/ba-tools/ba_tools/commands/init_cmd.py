"""ba-tools init <operator> — scaffold .ba-ops/ and return context JSON (TOOL-01, TRACE-01).

Design §5: `init <operator>` returns context JSON with:
  config       — contents of .ba-ops/config.json (empty dict if absent)
  routes       — list of valid routes for this operator
  default_route — the operator's default route (from DEFAULT_ROUTES)
  state        — summary of .ba-ops/STATE.md frontmatter (empty dict if absent)

Security (T-1-04): operator is validated against the static DEFAULT_ROUTES table.
Unknown operator -> BaToolsError UNKNOWN_OPERATOR (exit 2).
"""

from pathlib import Path

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json
from ba_tools.repo import resolve_repo_root
from ba_tools.scaffold import ensure_scaffold
from ba_tools.config import load_config
from ba_tools.state_store import _parse_state
from ba_tools.commands.resolve_route import DEFAULT_ROUTES

# Per-operator route lists (DESIGN §4 table).
# This is the canonical per-operator route registry — DEFAULT_ROUTES carries the
# *default* only; this dict carries the *full list*.
OPERATOR_ROUTES: dict[str, list[str]] = {
    "ba-uc":               ["deliver", "resume", "status", "iterate"],
    "ba-srs-analyze":      ["extract", "draft", "lint", "verify", "full", "iterate"],
    "ba-mermaid":          ["author", "render", "full"],
    "ba-mockup":           ["screen", "full"],
    "ba-make-diagram":     ["diagram", "export"],
    "ba-uc-delivery":      ["prepare", "analysis", "diagram", "export", "build", "full", "package"],
    "ba-backlog-grooming": ["split", "criteria", "order", "full"],
}


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "init",
        help="Scaffold .ba-ops/ directory and return operator context JSON (TOOL-01)",
    )
    p.add_argument("operator", help="Operator name (e.g. ba-uc, ba-srs-analyze)")
    p.set_defaults(func=run)


def run(args) -> None:
    """Validate operator, scaffold .ba-ops/, load config + state, emit context JSON."""
    operator = args.operator

    # Security: validate against static table (T-1-04)
    if operator not in DEFAULT_ROUTES:
        raise BaToolsError([{
            "code": "UNKNOWN_OPERATOR",
            "message": f"No default route defined for operator: {operator!r}",
            "operator": operator,
        }])

    root = resolve_repo_root(getattr(args, "repo_root", None))

    # Scaffold .ba-ops/ — idempotent, never overwrites existing files
    scaffold_result = ensure_scaffold(root)

    # Load config (absent → {}, never written on absence — TRACE-02)
    cfg = load_config(root)

    # Read STATE.md summary (frontmatter only — no judgement, pure file read)
    state_path = root / ".ba-ops" / "STATE.md"
    state_summary: dict = {}
    if state_path.exists():
        text = state_path.read_text(encoding="utf-8")
        fm, _ = _parse_state(text)
        state_summary = fm

    ok_json(
        operator=operator,
        default_route=DEFAULT_ROUTES[operator],
        routes=OPERATOR_ROUTES.get(operator, [DEFAULT_ROUTES[operator]]),
        config=cfg,
        state=state_summary,
        scaffold=scaffold_result,
    )
