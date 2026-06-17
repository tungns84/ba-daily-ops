"""
BaToolsError — structured error carrying a failures list.

No stack trace content or credentials are ever stored on this exception.
The failures list is a sequence of dicts; each dict should have at least
a "code" key (T-1-07: no stack traces, no secrets in error JSON).
"""


class BaToolsError(Exception):
    """Raised by any ba-tools command when it cannot complete successfully.

    Args:
        failures: list of failure dicts, each containing at minimum
                  {"code": "<CODE>", ...optional fields...}.
                  No traceback content and no credential values may appear
                  in any failure dict.
    """

    def __init__(self, failures: list[dict]) -> None:
        self.failures = failures
        # Terse message — the structured data is in self.failures
        codes = ", ".join(f.get("code", "?") for f in failures)
        super().__init__(f"BaToolsError: {codes}")
