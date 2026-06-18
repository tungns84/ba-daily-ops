<!-- GSD:project-start source:PROJECT.md -->

## Project

**BA Daily Operators**

A GSD-grade operator suite for Business Analysts that turns each repeated daily
deliverable loop (use case → requirements/SRS → process diagram → UI mockup →
traceability index) into a reproducible **operator**: a skill backed by a
deterministic CLI and verified by gates. Output is hash-provable, inspectable,
and portable across machines and runtimes. Built CodexApp-first (v1), with a
Claude Code transform on the v2 roadmap.

**Core Value:** **REQ-ID traceability across artifacts** — one requirement seen consistently
across SRS, diagram, mockup, and backlog, so drift surfaces the moment it
appears. If everything else fails, the traceability spine must work.

### Constraints

- **Runtime**: CodexApp-first (v1) — author Codex-native (`.agents/skills/`, AGENTS.md Read-by-skills not root-auto-loaded, `agents/openai.yaml`). Claude Code is v2 roadmap. — DESIGN §9 ordering, confirmed.
- **Tech stack**: `ba-tools` in **Python** (`python-docx`, Markdown extraction, hashing already Python in the harness); resolve Python via `sys.executable`. Render shells out to draw.io desktop CLI + `mmdc` (plugins/optional only in v1).
- **Determinism boundary**: `ba-tools` does ONLY file/command/hash-provable work; agents own all analysis/authoring/judgement. Hard line — DESIGN §5.
- **Byte budgets**: AGENTS.md/eager refs < 32,768 B (Codex truncates beyond); DEFAULT workflow < 38,000 B; LARGE < 54,000 B.
- **Portability**: no hard-coded machine paths in committed config; all paths resolve relative to `--repo-root` (git root / cwd).
- **Determinism of CLI output**: every success prints UTF-8 JSON to stdout; every `BaToolsError` exits `2`.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

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

## Installation

# Python CLI dependencies (spine: stdlib only; plugin path adds these)

# mermaid CLI (global install so mmdc is on PATH)

# OR use npx fallback — -p flag required because package name != command name:

# draw.io: install the desktop app for your OS (exposes CLI automatically)

# macOS: /Applications/draw.io.app/Contents/MacOS/draw.io

# Linux:  drawio (via snap / apt / flatpak)

# Windows: "C:\Program Files\draw.io\draw.io.exe"

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| python-docx 1.2.0 | python-docx-ng (fork) | Only if you need features not in mainline (TOC update, floating images). For rId-based media-replacement, mainline 1.2.0 is sufficient. |
| hashlib (stdlib) | cryptography / pyca | Never for SHA-256 digests — stdlib covers this completely. |
| argparse (stdlib) | click 8.x | When subcommand dispatch grows past ~10 commands with complex option inheritance or grouped `--help` generation at subgroup level. |
| filelock (PyPI) | `os.open(path, O_EXCL \| O_CREAT)` | Raw `O_EXCL` works on POSIX but has known edge cases on Windows network shares and some virtual filesystems. `filelock` handles these correctly and is battle-tested. |
| mmdc (mermaid-cli) | mermaid-py, node-mermaid | mermaid-py is an unofficial wrapper that shells out to `mmdc` anyway. Go direct. |
| draw.io desktop CLI | docker drawio-desktop-headless | Docker adds a hard dependency not acceptable for a portable local tool. Use the desktop app CLI directly. Docker approach valid only for CI. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `python` or `python3` as subprocess call | Breaks in venvs; wrong interpreter on multi-Python machines; forbidden by DESIGN §11 (no hard-coded paths) | `sys.executable` always resolves the active interpreter |
| Pillow / SVG converter / screenshot for diagram render | Explicitly forbidden in DESIGN §11 non-negotiables; produces synthetic (not CLI-verified) renders | draw.io desktop CLI (`-x -f png`) or `mmdc` only |
| Hard-coded machine paths in config | Breaks portability; forbidden by DESIGN §11 | All paths relative to `--repo-root` (git root / cwd); CLI paths from env vars or PATH search |
| `markdown-extract` PyPI package | Unmaintained; adds a dependency for what is 5 lines of stdlib regex | Parse headings with `re.match(r'^#{1,6}\s+', line)` over `Path.read_text().splitlines()` |
| `python-docx` on the daily spine | The spine is text-only (MD/JSON); DOCX is plugin-only | Only import python-docx inside `ba_tools/commands/update_docx.py` (plugin stub) |
| Global `npm install -g @mermaid-js/mermaid-cli` as hard requirement | May not be available on all machines | Resolution chain: `--mermaid-cli` flag → `$MERMAID_CLI` env → PATH `mmdc` → `npx -p @mermaid-js/mermaid-cli mmdc`. Hard-fail only when none found. |

## Codex Skill Contract (verified)

### SKILL.md frontmatter

### agents/openai.yaml contract (verified)

### Skill discovery (verified)

## Byte Budget (verified)

## Render CLI Invocations (verified)

### mermaid CLI (mmdc)

# Convert .mmd to SVG

# Convert .mmd to PNG

# Convert .mmd to PNG with dark theme + transparent background

# With puppeteer config (e.g., Linux --no-sandbox workaround)

# npx fallback — -p flag REQUIRED because package name != binary name

### draw.io desktop CLI

# Short flags

# Long flags (equivalent)

# With page selection

# With scale (2x resolution)

# With transparent background (PNG only)

# With border

- `-x` / `--export` — export mode (non-interactive)
- `-f` / `--format` — output format: `png`, `svg`, `pdf` (default: `pdf`)
- `-o` / `--output` — output file path
- `--page-index` — 0-based page selector (default: first page for image formats)
- `-s` / `--scale` — scale factor
- `-b` / `--border` — border width in pixels
- `-t` / `--transparent` — transparent PNG background

## Lockfile Pattern (O_EXCL vs filelock)

# Recommended: filelock (cross-platform, handles Windows edge cases)

## CLI Output Convention (verified pattern)

## Stack Patterns by Variant

- Python 3.11+ + stdlib only (`hashlib`, `json`, `argparse`, `re`, `pathlib`, `subprocess`)
- Zero external Python deps for the spine
- `mmdc` not invoked on the spine (`ba-mermaid --route author` outputs inline MD ```` ```mermaid ```` block)
- Add `python-docx==1.2.0` and `filelock`
- Invoke draw.io CLI via `subprocess` for `.drawio` → PNG
- Invoke `mmdc` via `subprocess` for `.mmd` → PNG/SVG when exporting
- Media-replacement uses direct OOXML rId manipulation (see DESIGN flag below)
- Install draw.io via `xvfb-run draw.io -x ...` or Docker `rlespinasse/drawio-desktop-headless`
- `mmdc` runs headlessly via bundled Puppeteer/Chromium — no Xvfb needed for mermaid

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| python-docx 1.2.0 | Python 3.9+ | lxml ≥4.9.4 required (pulled automatically by pip) |
| @mermaid-js/mermaid-cli 11.15.0 | Node 18+ LTS | Bundles Chromium via Puppeteer (~300 MB). Pin major version to avoid breaking diagram syntax changes. |
| filelock 3.x | Python 3.8+ | No sub-dependencies; actively maintained |
| hashlib.file_digest | Python 3.11+ only | Use `hashlib.sha256(data).hexdigest()` if targeting Python 3.10 or below; chunk manually for large files |

## DESIGN.md Verification Flags

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

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

- **Spike findings for ba-daily-ops** (implementation patterns, constraints, gotchas — esp. `ba-make-diagram` BPMN/draw.io + ELK layout) → `Skill("spike-findings-ba-daily-ops")`
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
