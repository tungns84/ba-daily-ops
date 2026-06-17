# Stack Research

**Domain:** CodexApp-first BA operator suite (Python CLI + Codex skills)
**Researched:** 2026-06-17
**Confidence:** MEDIUM — Codex skill/openai.yaml fields verified via official OpenAI docs; python-docx version verified via PyPI; mmdc version verified via npm search results; draw.io CLI flags verified via community sources + official issue tracker; byte-budget constant verified via GitHub source + issue reports. No native `replace_image()` in python-docx — see DESIGN flag below.

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | `ba-tools` CLI runtime | 3.11 is the minimum that exposes `hashlib.file_digest()` (streaming hash, avoids loading full binary into memory). 3.12/3.13 also fine. Use `sys.executable` to resolve — never hard-code path. |
| python-docx | 1.2.0 | DOCX read/write (deferred plugin only) | Latest stable (PyPI, released 2025-06-16). Sole maintained library for OOXML manipulation in Python. Exposes `InlineShape` for traversal and `run.add_picture()` for adding images. Media-replacement requires direct OOXML rId swap — no native `replace_image()` exists. See DESIGN flag. |
| hashlib (stdlib) | stdlib (3.11+) | SHA-256 hashes of source/rendered/embedded media | Zero-dependency; `hashlib.sha256()` available in all Python versions. Use `hashlib.file_digest(f, "sha256")` (3.11+ only) for streaming large binaries. Fallback: chunked manual update for Python <3.11. |
| json (stdlib) | stdlib | UTF-8 JSON → stdout CLI output contract | Every `ba-tools` success prints `json.dumps(result)` to stdout; every `BaToolsError` exits `2`. No external dependency. |
| @mermaid-js/mermaid-cli | 11.15.0 (latest, 2026-06) | `mmdc` — render `.mmd` → PNG/SVG/PDF | Only maintained CLI renderer for Mermaid. Required for `ba-mermaid --route render/export` and `ba-make-diagram` plugin. Bundles Chromium via Puppeteer (~300 MB install). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| filelock | 3.x | Cross-platform lockfile for `STATE.md.lock` | Wrap `STATE.md` writes. Abstracts `O_EXCL` reliably on Windows, Linux, macOS. Use instead of raw `os.open(..., O_EXCL)`. |
| python-docx | 1.2.0 | Read/write DOCX, access inline shapes | Only in `ba-uc-delivery` (deferred plugin). Not on the daily spine. Import only inside the plugin command module. |
| argparse (stdlib) | stdlib | `ba-tools` CLI argument parsing | Sufficient for all `ba-tools` subcommands. Zero external deps. Use click only if dispatch complexity grows past ~10 subcommands with nested option inheritance. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Node.js 18+ / npm | Required to install `@mermaid-js/mermaid-cli` | `mmdc` is a Node binary. Must be on PATH or reachable via `npx`. Node LTS required per mermaid-cli docs. |
| draw.io Desktop App | Export `.drawio` → PNG/SVG (deferred plugin) | Install the desktop app for the OS. The export CLI is built into the app — not a separate install. See flags below. |
| pytest | Python test runner for `ba-tools` | Standard choice. No alternatives needed at this scale. |

---

## Installation

```bash
# Python CLI dependencies (spine: stdlib only; plugin path adds these)
pip install python-docx==1.2.0
pip install filelock

# mermaid CLI (global install so mmdc is on PATH)
npm install -g @mermaid-js/mermaid-cli
# OR use npx fallback — -p flag required because package name != command name:
npx -p @mermaid-js/mermaid-cli mmdc -h

# draw.io: install the desktop app for your OS (exposes CLI automatically)
# macOS: /Applications/draw.io.app/Contents/MacOS/draw.io
# Linux:  drawio (via snap / apt / flatpak)
# Windows: "C:\Program Files\draw.io\draw.io.exe"
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| python-docx 1.2.0 | python-docx-ng (fork) | Only if you need features not in mainline (TOC update, floating images). For rId-based media-replacement, mainline 1.2.0 is sufficient. |
| hashlib (stdlib) | cryptography / pyca | Never for SHA-256 digests — stdlib covers this completely. |
| argparse (stdlib) | click 8.x | When subcommand dispatch grows past ~10 commands with complex option inheritance or grouped `--help` generation at subgroup level. |
| filelock (PyPI) | `os.open(path, O_EXCL \| O_CREAT)` | Raw `O_EXCL` works on POSIX but has known edge cases on Windows network shares and some virtual filesystems. `filelock` handles these correctly and is battle-tested. |
| mmdc (mermaid-cli) | mermaid-py, node-mermaid | mermaid-py is an unofficial wrapper that shells out to `mmdc` anyway. Go direct. |
| draw.io desktop CLI | docker drawio-desktop-headless | Docker adds a hard dependency not acceptable for a portable local tool. Use the desktop app CLI directly. Docker approach valid only for CI. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `python` or `python3` as subprocess call | Breaks in venvs; wrong interpreter on multi-Python machines; forbidden by DESIGN §11 (no hard-coded paths) | `sys.executable` always resolves the active interpreter |
| Pillow / SVG converter / screenshot for diagram render | Explicitly forbidden in DESIGN §11 non-negotiables; produces synthetic (not CLI-verified) renders | draw.io desktop CLI (`-x -f png`) or `mmdc` only |
| Hard-coded machine paths in config | Breaks portability; forbidden by DESIGN §11 | All paths relative to `--repo-root` (git root / cwd); CLI paths from env vars or PATH search |
| `markdown-extract` PyPI package | Unmaintained; adds a dependency for what is 5 lines of stdlib regex | Parse headings with `re.match(r'^#{1,6}\s+', line)` over `Path.read_text().splitlines()` |
| `python-docx` on the daily spine | The spine is text-only (MD/JSON); DOCX is plugin-only | Only import python-docx inside `ba_tools/commands/update_docx.py` (plugin stub) |
| Global `npm install -g @mermaid-js/mermaid-cli` as hard requirement | May not be available on all machines | Resolution chain: `--mermaid-cli` flag → `$MERMAID_CLI` env → PATH `mmdc` → `npx -p @mermaid-js/mermaid-cli mmdc`. Hard-fail only when none found. |

---

## Codex Skill Contract (verified)

### SKILL.md frontmatter

Verified via official OpenAI Codex docs (developers.openai.com/codex/skills) and confirmed via skill-creator SKILL.md in openai/skills repo ("Do not include any other fields in YAML frontmatter"):

```yaml
---
name: ba-uc
description: |
  Deliver ONE use case end-to-end (srs-analyze → mermaid → mockup → index).
  Routes: deliver | resume | status | iterate. Use $ba-uc --route <route>.
---
```

**Only `name` and `description` are read by Codex for routing and skill selection.** No other frontmatter fields are defined or used. The official docs state: "These are the only fields that Codex reads to determine when the skill gets used."

**Encoding caveat:** The Codex skill loader fails to detect valid YAML frontmatter in SKILL.md files saved as UTF-8 with BOM (GitHub issue #13918). Save all SKILL.md files as UTF-8 without BOM.

### agents/openai.yaml contract (verified)

Verified via official Codex docs. Complete field structure:

```yaml
interface:
  display_name: "BA UC Delivery"
  short_description: "Route BA UC delivery operator with explicit --route."
  icon_small: ""         # optional path to SVG asset
  icon_large: ""         # optional path to PNG asset
  brand_color: ""        # optional hex color e.g. "#3B82F6"
  default_prompt: "$ba-uc --route deliver --uc \"<file>: ## UC-001. <name>\""
policy:
  allow_implicit_invocation: false   # explicit $-mention only; default is true
dependencies:
  tools: []              # optional MCP tool declarations
```

All `interface.*` fields are optional. `policy.allow_implicit_invocation` defaults to `true`; set `false` on spine, conductor, and DOCX/backlog plugin skills so they only fire on explicit `$` mention.

**DESIGN.md note:** DESIGN §3 shows `allow_implicit_invocation` at the top level of the YAML. The correct nesting per official docs is `policy.allow_implicit_invocation`. This is a minor structural correction; the field name and semantics are correct.

### Skill discovery (verified)

Codex scans upward from cwd through parent directories to repo root, checking `.agents/skills/` at each level. Also checks `$HOME/.agents/skills`, `/etc/codex/skills`, and system built-ins. This is recursive upward scanning — a flat layout under `<repo>/.agents/skills/` is always discoverable.

---

## Byte Budget (verified)

Verified from Codex source code (`src/config/mod.rs`, reported in GitHub issue #7138) and official AGENTS.md guide (developers.openai.com/codex/guides/agents-md):

```
PROJECT_DOC_MAX_BYTES: usize = 32 * 1024;  // = 32,768 bytes
```

**Behavior from source:** Files are **silently truncated** at this limit — no warning in the TUI (issue #7138 was closed as "not planned"). Official docs describe behavior as: "stops adding files once the combined size reaches the limit." In practice, individual files exceeding the limit are silently cut mid-content.

**Configurable:** Set `project_doc_max_bytes = 65536` (or other value) in `~/.codex/config.toml` to raise the limit.

**DESIGN §7 confirmed accurate:** The 32,768 B limit for AGENTS.md and eager refs is correct and critical. The DESIGN tiers (DEFAULT < 38,000 B, LARGE < 54,000 B) apply to workflow files loaded on-demand, not to the eager-load budget.

---

## Render CLI Invocations (verified)

### mermaid CLI (mmdc)

Package: `@mermaid-js/mermaid-cli` — latest: **11.15.0** (npm, as of 2026-06, per search results)

```bash
# Convert .mmd to SVG
mmdc -i input.mmd -o output.svg

# Convert .mmd to PNG
mmdc -i input.mmd -o output.png

# Convert .mmd to PNG with dark theme + transparent background
mmdc -i input.mmd -o output.png -t dark -b transparent

# With puppeteer config (e.g., Linux --no-sandbox workaround)
mmdc -i input.mmd -o output.png -p puppeteer-config.json

# npx fallback — -p flag REQUIRED because package name != binary name
npx -p @mermaid-js/mermaid-cli mmdc -i input.mmd -o output.png
```

**Headless:** mmdc uses Puppeteer + bundled Chromium — headless by default. On Linux CI, if Chromium sandbox fails: create `puppeteer-config.json` with `{"args": ["--no-sandbox"]}` and pass via `-p`.

Resolution order for `ba-tools render-mermaid`:
1. `--mermaid-cli` flag
2. `$MERMAID_CLI` env var
3. PATH `mmdc`
4. `npx -p @mermaid-js/mermaid-cli mmdc`

Hard-fail if none found — no synthetic fallback.

### draw.io desktop CLI

Not a separate package — installed with the desktop app. Verified flags (from official issue tracker + community sources):

```bash
# Short flags
draw.io -x -f png -o output.png input.drawio

# Long flags (equivalent)
draw.io --export --format png --output output.png input.drawio

# With page selection
draw.io --export --format png --output output.png --page-index 0 input.drawio

# With scale (2x resolution)
draw.io -x -f png -s 2 -o output.png input.drawio

# With transparent background (PNG only)
draw.io --export --format png --transparent --output output.png input.drawio

# With border
draw.io -x -f png -b 10 -o output.png input.drawio
```

**Key flags:**
- `-x` / `--export` — export mode (non-interactive)
- `-f` / `--format` — output format: `png`, `svg`, `pdf` (default: `pdf`)
- `-o` / `--output` — output file path
- `--page-index` — 0-based page selector (default: first page for image formats)
- `-s` / `--scale` — scale factor
- `-b` / `--border` — border width in pixels
- `-t` / `--transparent` — transparent PNG background

**Headless:** On Linux/macOS, `-x` runs headlessly. On Windows, it briefly spawns the Electron window to render. Xvfb is only needed in headless Linux CI environments (not desktop machines).

[Inference] Flag documentation is sourced from community usage and GitHub issue discussions, not from an official draw.io CLI reference page. The flags above have broad community confirmation but the complete `--help` output should be verified against the installed version at build time.

Resolution order for `ba-tools export-diagram`:
1. `--drawio-cli` flag
2. `$DRAWIO_CLI` env var
3. PATH search: `drawio` / `draw.io` / `diagrams.net`
4. Common OS install paths

Hard-fail if none found — no fallback renderer.

---

## Lockfile Pattern (O_EXCL vs filelock)

DESIGN §8 specifies `STATE.md.lock` with `O_EXCL` and 10-second stale-lock timeout. Implementation:

```python
# Recommended: filelock (cross-platform, handles Windows edge cases)
from filelock import FileLock, Timeout

lock = FileLock(".ba-ops/STATE.md.lock", timeout=10)
try:
    with lock:
        # read/write STATE.md
        pass
except Timeout:
    raise BaToolsError("STATE.md lock timeout — another ba-tools process running")
```

`O_EXCL` via `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)` is POSIX-correct but has known reliability issues on Windows network shares and some virtual filesystems. `filelock` wraps this portably. Both support stale-lock detection.

---

## CLI Output Convention (verified pattern)

Every `ba-tools` success: `print(json.dumps(result))` to stdout, `sys.exit(0)`.
Every `BaToolsError`: print error JSON to stderr, `sys.exit(2)`.

```python
import json, sys

def main():
    try:
        result = run_command()
        print(json.dumps(result))
        sys.exit(0)
    except BaToolsError as e:
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        sys.exit(2)
```

Exit code `2` for `BaToolsError` is distinguishable from exit `1` (general OS error) and aligns with the argparse/grep POSIX convention for "misuse / invalid arguments."

---

## Stack Patterns by Variant

**Daily spine (no render, no DOCX):**
- Python 3.11+ + stdlib only (`hashlib`, `json`, `argparse`, `re`, `pathlib`, `subprocess`)
- Zero external Python deps for the spine
- `mmdc` not invoked on the spine (`ba-mermaid --route author` outputs inline MD ```` ```mermaid ```` block)

**Plugin path (render + DOCX, deferred v1):**
- Add `python-docx==1.2.0` and `filelock`
- Invoke draw.io CLI via `subprocess` for `.drawio` → PNG
- Invoke `mmdc` via `subprocess` for `.mmd` → PNG/SVG when exporting
- Media-replacement uses direct OOXML rId manipulation (see DESIGN flag below)

**CI/headless Linux:**
- Install draw.io via `xvfb-run draw.io -x ...` or Docker `rlespinasse/drawio-desktop-headless`
- `mmdc` runs headlessly via bundled Puppeteer/Chromium — no Xvfb needed for mermaid

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| python-docx 1.2.0 | Python 3.9+ | lxml ≥4.9.4 required (pulled automatically by pip) |
| @mermaid-js/mermaid-cli 11.15.0 | Node 18+ LTS | Bundles Chromium via Puppeteer (~300 MB). Pin major version to avoid breaking diagram syntax changes. |
| filelock 3.x | Python 3.8+ | No sub-dependencies; actively maintained |
| hashlib.file_digest | Python 3.11+ only | Use `hashlib.sha256(data).hexdigest()` if targeting Python 3.10 or below; chunk manually for large files |

---

## DESIGN.md Verification Flags

The following DESIGN.md claims were checked against current documentation. Items marked CORRECTION require a change to DESIGN.md or implementation guidance.

| Claim | Status | Notes |
|-------|--------|-------|
| `project_doc_max_bytes = 32,768` (DESIGN §7) | CONFIRMED | Verified from Codex source `src/config/mod.rs` and official AGENTS.md guide. Truncation is silent. |
| SKILL.md frontmatter: `name` + `description` only (DESIGN §3) | CONFIRMED | Official docs: "Do not include any other fields in YAML frontmatter." |
| `agents/openai.yaml` fields `display_name`, `short_description`, `default_prompt`, `allow_implicit_invocation` (DESIGN §3) | CONFIRMED with structural note | All four fields exist and work as described. Correct nesting: `interface.display_name`, `interface.short_description`, `interface.default_prompt`, `policy.allow_implicit_invocation`. DESIGN §3 shows `allow_implicit_invocation` at a flat level in YAML — should be nested under `policy:`. |
| Codex recursive skill loader from `.agents/skills/` upward (DESIGN §3) | CONFIRMED | Verified via official Codex docs. Flat layout under repo root is always discoverable. |
| `python-docx` for DOCX "media-replacement" (DESIGN §5) | PARTIAL — CORRECTION NEEDED | python-docx 1.2.0 has NO native `replace_image()` / `InlineShape.replace_image()` method (feature request #192 open since 2015, not shipped). Media-replacement requires direct OOXML manipulation: traverse `InlineShape._inline.graphic.graphicData.pic.blipFill.blip`, read the `r:embed` rId, call `part.drop_rel(rId)` and `part.relate_to(image_descriptor, RT.IMAGE)`, update `blip.rId`. This is valid but is raw XML surgery, not a high-level API. DESIGN §5 wording ("media-replacement") is accurate as a technique; the implementation note should not imply a named method exists. |
| `mmdc` PATH → `npx @mermaid-js/mermaid-cli` fallback (DESIGN §5) | CONFIRMED with correction | Correct. The exact npx invocation is `npx -p @mermaid-js/mermaid-cli mmdc` — the `-p` flag is required because the package name differs from the binary name. DESIGN shows it without `-p`. |
| draw.io CLI invocation (DESIGN §5) | CONFIRMED | Both short (`-x -f png -o`) and long (`--export --format png --output`) forms confirmed via community + official issue tracker. `--page-index` is the correct flag for page selection. |
| `O_EXCL` lockfile (DESIGN §8) | CONFIRMED with recommendation | `O_EXCL` works on POSIX. `filelock` is recommended over raw `O_EXCL` for Windows compatibility. The 10-second stale threshold is a convention; implement via `FileLock(timeout=10)`. |
| `sys.executable` for Python resolution (DESIGN §5) | CONFIRMED | Standard Python pattern for subprocess self-calls. Always correct in venv and multi-Python environments. |
| Byte budget tiers DEFAULT < 38,000 B, LARGE < 54,000 B (DESIGN §7) | UNVERIFIED (no official source) | [Inference] These appear to be GSD-inherited conventions, not Codex-imposed limits. Only the 32,768 B eager-load truncation is a Codex hard limit. The workflow tier values are design targets from GSD Core — treat as guidance, not constraints enforced by the runtime. |

---

## Sources

- [Agent Skills – Codex | OpenAI Developers](https://developers.openai.com/codex/skills) — SKILL.md frontmatter (name+description only), openai.yaml complete field structure, skill discovery behavior. Confidence: HIGH (official docs).
- [Custom instructions with AGENTS.md – Codex](https://developers.openai.com/codex/guides/agents-md) — project_doc_max_bytes default 32 KiB, file loading behavior, config.toml override. Confidence: HIGH (official docs).
- [openai/skills skill-creator SKILL.md](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md) — "Do not include any other fields in YAML frontmatter." Confidence: HIGH (official repo).
- [AGENTS.md silently truncated · openai/codex #7138](https://github.com/openai/codex/issues/7138) — 32,768 B constant from `src/config/mod.rs`; confirmed silent truncation. Confidence: MEDIUM (source code, closed as not-planned).
- [python-docx · PyPI](https://pypi.org/project/python-docx/) — version 1.2.0, released 2025-06-16, Python >=3.9. Confidence: HIGH.
- [python-docx readthedocs InlineShape API](https://python-docx.readthedocs.io/en/latest/) — InlineShape traversal, blip access path. Confidence: HIGH (official docs).
- [InlineShape.replace_image() feature request #192](https://github.com/python-openxml/python-docx/issues/192) — No native replace_image(); still open since 2015. Confidence: HIGH (confirms absence).
- [@mermaid-js/mermaid-cli npm](https://www.npmjs.com/package/@mermaid-js/mermaid-cli) — version 11.15.0 latest. Confidence: MEDIUM (search-confirmed, page 403'd).
- [mermaid-cli README](https://github.com/mermaid-js/mermaid-cli/blob/master/README.md) — mmdc flags (-i, -o, -t, -b, --cssFile), npx `-p` requirement, output formats SVG/PNG/PDF, linux-sandbox issue. Confidence: HIGH (official repo).
- [How I use draw.io at the command line](https://tomd.xyz/how-i-use-drawio/) — `-x -f png -s -o` flags. Confidence: MEDIUM (community).
- [Draw.io export all tabs CLI](https://www.codegenes.net/blog/draw-io-how-to-export-all-tabs-to-images-using-command-line/) — `--export --format --output --page-index` long flags. Confidence: MEDIUM (community).
- [draw.io/drawio-desktop GitHub issues](https://github.com/jgraph/drawio-desktop/issues) — headless behavior, PNG export flags confirmed in issue discussions. Confidence: MEDIUM.

---
*Stack research for: BA Daily Operators (CodexApp-first, Python CLI)*
*Researched: 2026-06-17*
