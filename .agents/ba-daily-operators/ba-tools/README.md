# ba-tools

Deterministic CLI for the BA Daily Operators suite. Every command emits UTF-8 JSON on
stdout (success) or stderr (error) and exits 0 or 2 respectively — no mixed output, no
stack traces (D-03, D-04, T-1-07).

---

## Running the CLI

```sh
# From any directory — resolve the interpreter via sys.executable / PATH
python -m ba_tools --help

# General form
python -m ba_tools [--repo-root <path>] <subcommand> [args...]
```

`--repo-root` defaults to the git repository root, then the current working directory.
Every path argument is resolved relative to `--repo-root` and checked for path-traversal
before use (T-1-01).

### Available subcommands

| Subcommand | Purpose |
|---|---|
| `init <operator>` | Scaffold `.ba-ops/` and return operator context JSON |
| `resolve-route <operator>` | Return the default route for a named operator |
| `state <action> --data <json>` | Update `.ba-ops/STATE.md` with a FileLock guard |
| `uc-status [--uc <id>]` | Return pipeline steps + next_step for a use-case |
| `lint-requirements <file>` | Lint requirements for ambiguity, atomicity, grounding |
| `verify --reqs <file>` | Run the citation-exists gate (exits 2 on any FAIL finding) |
| `extract-uc --uc <spec>` | Extract a UC section from a Markdown document |
| `template fill <name> --out <path>` | Fill an artifact template from `ba-core/templates/` |
| `discovery add --note <text>` | Append a discovery to `.ba-ops/discoveries.jsonl` |
| `discovery list` | List all captured discoveries |
| `byte-check <file...>` | Fail if any listed file is >= 32768 B (GATE-04, CDX-04) |
| `scan --file <file>` | Advisory prompt-injection scan (always exits 0) |
| `confirm` | Confirm gate pass-through (always exits 0 in v1) |

### Output envelope contract

Every success emits a flat JSON object to **stdout**:

```json
{"ok": true, "failures": [], ...fields}
```

Every error emits a flat JSON object to **stderr** and exits 2:

```json
{"ok": false, "failures": [{"code": "...", "message": "...", ...}]}
```

No nested `"data"` wrapper. No Python tracebacks in output.

---

## Running tests

```sh
# From the ba-tools directory
cd .agents/ba-daily-operators/ba-tools

# Run the full test suite
python -m pytest tests/ -v

# Run only the integration contract tests
python -m pytest tests/test_output_contract.py tests/test_paths.py -v

# Run a specific test file
python -m pytest tests/test_byte_check.py -v
```

The test suite requires the package to be installed in editable mode:

```sh
pip install -e ".[test]"
```

---

## Installing the git pre-commit hook

The pre-commit hook calls `ba-tools byte-check` on staged `AGENTS.md` files and blocks
the commit if any eager-loaded doc is >= 32768 bytes (the Codex silent-truncation limit,
GATE-04 layer 2).

**Copy (simple):**

```sh
cp .agents/ba-daily-operators/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Symlink (stays up to date with repo changes):**

```sh
ln -sf ../../.agents/ba-daily-operators/hooks/pre-commit .git/hooks/pre-commit
```

The hook degrades gracefully when `ba_tools` is not importable — it prints a skip notice
and exits 0 rather than hard-blocking (D-06). Install ba_tools first:

```sh
pip install -e ".agents/ba-daily-operators/ba-tools[test]"
```

---

## Path and interpreter contract (DESIGN §11)

- **No hard-coded machine paths** — all paths are resolved relative to `--repo-root`
  (git toplevel or cwd fallback). No `C:\Users\...` or `/home/...` literals appear
  anywhere in the package source.

- **No bare `python` or `python3` subprocess calls** — all subprocess self-calls use
  `sys.executable` to resolve the active interpreter. This ensures correct behavior in
  virtualenvs and on multi-Python machines.

- **Path-traversal guard** — every path argument is checked via `is_within_root()` before
  the file is accessed. Paths that resolve outside `--repo-root` exit 2 with
  `{"code": "PATH_ESCAPE"}`.

These invariants are verified by `tests/test_paths.py` on every test run.

---

## Architecture overview

```
ba_tools/
  __main__.py       — argparse dispatcher; all subcommands register via register(subs)
  errors.py         — BaToolsError(failures) → stderr JSON + exit 2
  output.py         — ok_json(**fields) → stdout; fail_json(failures) → stderr + exit 2
  repo.py           — resolve_repo_root(), is_within_root() path-safety helpers
  state_store.py    — STATE.md read/write with FileLock guard (TOOL-03)
  scaffold.py       — ensure_scaffold() — idempotent .ba-ops/ directory creation
  lint.py           — requirement heuristics (ambiguity, atomicity, grounding, verifiability)
  citation.py       — citation_exists() — verbatim span lookup scoped to section
  markdown_sections.py — extract() — section body extraction by heading level
  config.py         — load_config() — reads .ba-ops/config.json
  commands/         — one module per subcommand, each with register() + run()
```

For design rationale, see `DESIGN.md` in the repository root.
