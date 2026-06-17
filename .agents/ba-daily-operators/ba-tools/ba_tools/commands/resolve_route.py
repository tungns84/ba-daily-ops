"""ba-tools resolve-route — return the default route for an operator (TOOL-02).

DESIGN §11 non-negotiable: the route value is read ONLY from the static
DEFAULT_ROUTES dict. No parsing, normalization, fuzzy-matching, or inference
of the route from the operator string beyond the exact dict key lookup.
Unknown operator -> BaToolsError UNKNOWN_OPERATOR (exit 2).
"""

from ba_tools.errors import BaToolsError
from ba_tools.output import ok_json

# Static table — NEVER derive from free text (DESIGN §4, T-1-04)
DEFAULT_ROUTES: dict[str, str] = {
    "ba-uc":               "deliver",
    "ba-srs-analyze":      "full",
    "ba-mermaid":          "author",
    "ba-mockup":           "full",
    "ba-make-diagram":     "diagram",
    "ba-uc-delivery":      "full",
    "ba-backlog-grooming": "full",
}


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "resolve-route",
        help="Return the default route for a named operator (TOOL-02)",
    )
    p.add_argument("operator", help="Operator name (e.g. ba-mermaid)")
    p.set_defaults(func=run)


def run(args) -> None:
    operator = args.operator
    if operator not in DEFAULT_ROUTES:
        raise BaToolsError([{
            "code": "UNKNOWN_OPERATOR",
            "message": f"No default route defined for operator: {operator!r}",
            "operator": operator,
        }])
    ok_json(operator=operator, default_route=DEFAULT_ROUTES[operator])
