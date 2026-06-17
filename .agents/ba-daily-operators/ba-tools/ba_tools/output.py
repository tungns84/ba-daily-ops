"""
Flat JSON output envelope helpers (D-03, D-04, TOOL-13, CDX-05).

Contract:
- Every success prints UTF-8 JSON to stdout: {"ok": true, "failures": [], ...fields}
- Every error prints UTF-8 JSON to stderr + sys.exit(2): {"ok": false, "failures": [...]}
- The envelope is FLAT — no nested "data" wrapper key (D-03).
"""

import json
import sys


def ok_json(**fields) -> None:
    """Print a success response envelope to stdout and return.

    Builds {"ok": True, "failures": []} and merges caller-supplied fields
    at the top level (flat envelope — never a nested "data" key per D-03).

    Args:
        **fields: arbitrary keyword fields merged into the top-level envelope.
    """
    payload: dict = {"ok": True, "failures": []}
    payload.update(fields)
    print(json.dumps(payload, ensure_ascii=False))


def fail_json(failures: list[dict]) -> None:
    """Print a failure response envelope to stderr, then exit with code 2.

    This function never returns — it always calls sys.exit(2).

    Args:
        failures: list of failure dicts (same shape as BaToolsError.failures).
    """
    payload: dict = {"ok": False, "failures": failures}
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
    sys.exit(2)
