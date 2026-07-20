<!-- gsd-project-start source:PROJECT.md -->

## Project

**BA Daily Ops**

**BA Daily Ops** (`ba-daily-ops`) biến vòng lặp giao phẩm hằng ngày của Business Analyst — use case → SRS/yêu cầu → sơ đồ quy trình → mockup UI → chỉ mục truy vết — thành quy trình lặp lại được, kiểm chứng được và truy vết được. Mỗi bước là skill hướng người dùng (`$ba-*`) được hậu thuẫn bởi lớp deterministic `ba-tools` và chặn bởi cổng chất lượng. BA chỉ cần một lệnh — `$ba-deliver run --uc <slug>` — và conductor điều phối toàn bộ chuỗi từ đầu đến cuối.

Sản phẩm **harness-first**: không cạnh tranh tốc độ soạn nháp với LLM đơn lẻ (~70% giá trị ở harness, ~30% ở soạn thảo). Giá trị nằm ở file-state xác định, hash, gate, truy vết REQ-ID và tính di động — những thứ phiên chat LLM không giữ lại.

**Core Value:** **Truy vết REQ-ID xuyên suốt các giao phẩm.** Xương sống: SRS → flow → mockup → (tùy chọn) backlog → INDEX. Một yêu cầu phải nhất quán trên mọi artifact; drift lộ ra ngay khi xuất hiện. Nếu mọi thứ khác thất bại, xương sống truy vết vẫn phải hoạt động.

### Constraints

- **Tech stack**: Python 3.11+ (`ba-tools`), chat skill runtime, Node 18+ (Mermaid/draw.io khi cần), git 2.x+
- **Determinism boundary**: `ba-tools` chỉ provable ops; agent sở hữu judgement/authoring
- **CLI contract**: success → 1 JSON UTF-8 stdout; error → JSON stderr + exit 2
- **Render**: draw.io Desktop CLI (BPMN), `@mermaid-js/mermaid-cli` (Mermaid) — cấm screenshot fallback
- **Portability**: cấm absolute path trong config commit; mọi path resolve `--repo-root`
- **Security**: `ba-tools` zero-network; path containment trong repo root
- **Scale**: ≤ 500 REQ, ≤ 50 UC/milestone, ≤ 5 BA (team mode)

<!-- gsd-project-end -->

<!-- gsd-stack-start source:research/STACK.md -->

## Technology Stack

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| **Python** | **3.12.x** (min **3.11+**) | Run `ba-tools` deterministic harness | BRD requires 3.11+ for `hashlib.file_digest()` streaming SHA-256 (NFR-005). Pin **3.12** as primary dev/CI target; keep 3.11 in release matrix per BRD §15.3. | HIGH |
| **Typer** | **0.27.0** | `ba-tools` CLI framework | De-facto standard for typed Python CLIs in 2025–2026: subcommands, `--help` generation, Click compatibility, Rich output to stderr. Fits multi-command surface (`doctor`, `init`, `verify`, `index`, `deliver` runner). | HIGH |
| **jsonschema** | **4.26.0** | Validate `.ba-ops/` JSON against Draft 2020-12 schemas | Industry-standard JSON Schema validator; supports URN-based schemas (`requirements.json` uses external URN per SRS-SPEC). Separates **schema proof** (CLI) from **judgment** (agent). | HIGH |
| **stdlib `json` + `hashlib`** | Python 3.11+ | Canonical JSON serialization + SHA-256 | Deterministic hashing requires controlled serialization (`sort_keys=True`, `ensure_ascii=False`, compact separators) and `hashlib.file_digest()` — no third-party hash/JSON libs needed. Keeps zero-network surface minimal. | HIGH |
| **filelock** | **≥3.20.3**, pin **3.29.6** | Cross-platform lock for atomic writes | BRD-mandated (§12.3). Versions `<3.20.3` have known TOCTOU CVEs (CVE-2025-68146, CVE-2026-22701). Required for NFR-010 crash-safe promotion. | HIGH |
| **python-frontmatter** | **1.3.0** | Parse `req_ids` from Markdown artifact frontmatter | Mermaid flow + wireframe mockups carry machine-readable REQ metadata in YAML frontmatter (BRD-002, BRD-008). Mature, minimal, UTF-8 safe. | HIGH |
| **python-docx** | **1.2.0** | Strict-tier DOCX bundle assembly | BRD-mandated for `$ba-docx` (§12.3). Stable OpenXML manipulation; supports media placeholder replacement by relationship ID (BR-003). | HIGH |
| **Cursor Agent Skills** | Host current (2026) | Chat skill runtime for `$ba-*` | v1 ships on Cursor: project skills in `.cursor/skills/<skill>/SKILL.md` with YAML frontmatter (`name`, `description`). Runtime-neutral contract allows future port without changing `ba-tools` or `.ba-ops/`. | HIGH |
| **Git** | **2.x+** (CLI via subprocess) | Repo root detection, portability checks | BRD-mandated. `.ba-ops/` commits into project Git. Use **subprocess** to invoke `git` — not GitPython — to avoid extra dependency, resource-leak risk in long sessions, and keep determinism boundary thin. | HIGH |
| **Node.js** | **22.x LTS** (min **18+**) | Host `@mermaid-js/mermaid-cli` | BRD requires Node 18+ for Mermaid/BPMN render paths. **22.23.x** is Maintenance LTS (EOL 2027-04-30) — satisfies BRD floor with longer support runway than 18.x. | HIGH |
| **@mermaid-js/mermaid-cli** (`mmdc`) | **11.16.0** (min **11.15+**) | Official Mermaid PNG/SVG export | BRD-mandated official renderer (§12.1, BR-002). No Python wrapper — `ba-tools` invokes `mmdc` as local subprocess with path containment gate. | HIGH |
| **draw.io Desktop** | **30.3.14+** (stable channel) | Official BPMN/DOCX diagram export | BRD-mandated for `$ba-bpmn` and embedded diagrams in `$ba-docx`. CLI: `drawio -x -f <format> -o <out> <in>`. Pin minimum in `doctor`; allow newer stable — Electron app auto-updates. Linux CI needs `xvfb-run` wrapper. | MEDIUM |

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| **Pydantic** | **2.13.4** | Internal CLI I/O models (`BaToolsResult`, error envelopes) | Parse/emit the stdout JSON contract and gate evidence structs. **Not** for business judgment, MoSCoW, or semantic correctness — that stays in agent layer (NFR-006). | HIGH |
| **PyYAML** | **6.0.2** | YAML frontmatter backend | Transitive via `python-frontmatter`; pin explicitly for reproducible installs and security patch control. | MEDIUM |
| **beautifulsoup4** | **4.13.4** | Parse HTML mockup metadata / comments | When `$ba-mockup` fidelity is `html`: extract `req_ids` from structured comments or data attributes for trace gate. | MEDIUM |
| **Jinja2** | **3.1.6** | Render `SRS.md` from `requirements.json` | Derived-view generation (IEEE-830 layout) from canonical registry. Template owns **layout only** — no REQ invention (SRS-SPEC N-1). | HIGH |
| **platformdirs** | **4.3.8** | Resolve OS-local config/cache paths | Installer and `doctor` only — for machine-local renderer paths **not** committed to repo (NFR-004). Business paths stay `--repo-root` relative. | MEDIUM |
| **rich** | **14.0.0** | stderr UX for interactive commands | Human-readable `doctor` / confirmation-gate prompts on stderr. **Never** on stdout — stdout reserved for single JSON document (BRD-022). | HIGH |

### Development Tools

| Tool | Version | Purpose | Notes | Confidence |
|------|---------|---------|-------|------------|
| **uv** | **0.11.29** | Project/venv/deps lockfile | Fast Rust-based package manager from Astral; handles Python version pinning, lockfiles, and `uv run ba-tools`. Ideal for greenfield harness with reproducible CI. | HIGH |
| **hatchling** | **1.27.0** | Build backend (`pyproject.toml`) | PEP 517 standard; simple src-layout packaging for `ba-tools` console script entry point. | HIGH |
| **ruff** | **0.15.22** | Lint + format | Replaces flake8/isort/black in one fast tool. Enforce UTF-8, import order, and no-network guard patterns in CI. | HIGH |
| **pytest** | **9.1.1** | Unit + integration tests | Standard for CLI contract tests, conformance corpus (≥50 mutations), and gate exit-code assertions. Use `pytest-subprocess` or `monkeypatch` for renderer mocks. | HIGH |
| **mypy** | **1.16.0** | Static type checking | Typer + Pydantic benefit from typed CLI modules; catches JSON schema drift at compile time. | MEDIUM |

## Installation

# ── System prerequisites (installer / doctor validates) ──

# Python 3.12+, Git 2.x+, Node 22.x LTS

# draw.io Desktop (optional — required for bpmn/docx plugins)

# Mermaid CLI (optional — required for PNG/SVG export)

# ── Python toolchain ──

# ── Core runtime dependencies (pyproject.toml) ──

# ── Dev dependencies ──

# ── Node render toolchain (project-local, not global if possible) ──

# Invoke via: npx -p @mermaid-js/mermaid-cli mmdc ...

# ── draw.io Desktop (platform installers — not npm) ──

# Windows: draw.io-30.3.14-windows-installer.exe

# macOS:   draw.io-universal-30.3.14.dmg

# Linux:   drawio-amd64-30.3.14.deb (+ xvfb for headless CI)

# ── Environment (Windows UTF-8 — NFR-008) ──

# set PYTHONUTF8=1

# set PYTHONIOENCODING=utf-8

### Suggested `pyproject.toml` skeleton

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **Typer 0.27** | Click 8.2.x directly | Only if you need Click plugins Typer cannot wrap — otherwise Typer gives typed subcommands with less boilerplate |
| **jsonschema 4.26** | Pydantic-only validation | Never for external `.ba-ops/` schemas — Pydantic models drift from URN schemas; use jsonschema for registry/policy, Pydantic for CLI envelopes only |
| **uv + hatchling** | Poetry 2.x | Poetry works but uv is faster for CI matrix (Win/macOS/Linux per BRD §15.3) and manages Python versions natively |
| **subprocess git** | GitPython 3.1.x | GitPython if you need deep object graph traversal — overkill for `doctor`/`--repo-root` checks; adds leak risk in long agent sessions |
| **python-frontmatter** | Custom regex frontmatter parser | Never — regex breaks on UTF-8 Vietnamese content and nested YAML |
| **stdlib json** | orjson 3.10.x | orjson is faster but key order requires explicit opt-in; stdlib `json.dumps` with `sort_keys=True` is simpler to prove deterministic across platforms |
| **Cursor Skills** | Custom MCP server | MCP adds network/process complexity; skills match BA chat UX and stay runtime-neutral via SKILL.md contract |
| **Node 22 LTS** | Node 24 Active LTS | Node 24 if greenfield org standard already on 24.x — both exceed BRD 18+ floor; 22.x has longer track record with mmdc |
| **@mermaid-js/mermaid-cli** | mermaid.ink / Kroki HTTP | Never — violates zero-network `ba-tools` policy (NFR-009); BRD forbids synthetic render fallbacks |

## What NOT to Use

| Avoid | Why | Use Instead | Confidence |
|-------|-----|-------------|------------|
| **LangChain / LlamaIndex / CrewAI** | Pull in network runtimes, opaque agent loops, and judgment inside "tools" — violates determinism boundary and zero-network CLI | Cursor `$ba-*` skills for judgment; `ba-tools` for provable ops only | HIGH |
| **FastAPI / Flask / Django** | v1 is local-first, no SaaS backend (Out of Scope §7.1) | File-state in `.ba-ops/` + Git | HIGH |
| **SQLite / Postgres for state** | BRD specifies text/JSON file-state inspectable and committable (BRD-021) | `.ba-ops/` JSON + Markdown views | HIGH |
| **GitPython** | Extra dependency; documented resource leaks in long processes; subprocess is faster for simple invocations | `subprocess.run(["git", ...])` with typed wrapper | HIGH |
| **Pillow / Playwright screenshots for diagrams** | BRD explicitly forbids screenshot/synthetic render fallbacks (§12.1, BR-002) | Official `mmdc` + draw.io CLI; hard-fail if missing | HIGH |
| **typer-cli package** | Deprecated since Typer 0.27 — empty metapackage only | `pip install typer==0.27.0` | HIGH |
| **Poetry + pip mixed** | Dual lockfiles cause CI drift across 3 OS targets | uv exclusively for deps and lockfile | MEDIUM |
| **orjson for canonical hash** | Key ordering and float serialization differ from stdlib unless carefully configured | stdlib `json.dumps(..., sort_keys=True, ensure_ascii=False, separators=(',', ':'))` | HIGH |
| **Pydantic for gate business rules** | Encodes judgment in CLI — MoSCoW, stakeholder impact, semantic quality belong to agent (NFR-006) | jsonschema for structural gates; agent stores judgment as evidence files | HIGH |
| **Auto-GPT / OpenDevin-style autonomous agents** | Unbounded tool loops bypass executable runner; cannot enforce promotion atomicity (R-1) | Executable workflow runner owns route order + promotion (BRD-027) | HIGH |
| **Cloud render APIs (mermaid.live, etc.)** | Network egress from `ba-tools` forbidden; breaks air-gapped BA laptops | Local `mmdc` / draw.io processes | HIGH |
| **Absolute paths in committed config** | Breaks cross-machine portability (OBJ-5, NFR-004) | `--repo-root` relative paths + local-only overrides via env/flags | HIGH |

## Stack Patterns by Variant

- Python stack only + Git — no Node, no draw.io required
- Mermaid stays inline text; mockup as HTML/wireframe Markdown
- Because BRD-008 allows shipping Mermaid source without CLI render
- Add Node 22 + `@mermaid-js/mermaid-cli@11.16.0`
- Optionally add draw.io Desktop for basic BPMN
- Because export gates need official renderers but plugins remain opt-in per coverage policy
- Full render stack: Node + mmdc + draw.io Desktop + python-docx
- Add Jinja2 SRS render + DOCX media placeholder pipeline
- Because BR-003 / BR-004 require rendered binaries with manifest hash and human sign-off
- Same Python stack; add `filelock` on `.ba-ops/STATE.md` and owner_id checks in every mutating command
- No shared database — lead uses `ba-tools report team` (read-only JSON)
- Set `PYTHONUTF8=1` by default in installer (NFR-008, R-5)
- Resolve draw.io via `"C:\Program Files\draw.io\draw.io.exe"` from local config, never committed
- PowerShell installer script alongside POSIX shell (BRD-020)
- Wrap draw.io: `xvfb-run -a drawio -x -f png -o out.png in.drawio --no-sandbox`
- Because draw.io Desktop is Electron and requires virtual framebuffer even in CLI export mode

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `typer==0.27.0` | `click>=8.0` (transitive) | Typer 0.27 dropped `typer-cli`/`typer-slim` packages — install only `typer` |
| `jsonschema==4.26.0` | Draft 2020-12, Draft 7 | Use `$schema` in each `.ba-ops/*.json`; CLI rejects unknown `schema_version` |
| `filelock>=3.20.3` | Python 3.11–3.13 | Required security floor; 3.29.x needs Python ≥3.10 |
| `python-docx==1.2.0` | Python 3.11–3.13 | Dropped 3.8 support; tested through 3.13 |
| `pydantic==2.13.4` | Python 3.11–3.13 | v1 namespace available as `pydantic.v1` if needed |
| `@mermaid-js/mermaid-cli@11.16.0` | Node 18+ / 22 LTS | Pulls Puppeteer + Chromium; first install is network-heavy — installer action, not runtime |
| `draw.io Desktop 30.3.x` | Electron 42–43 | CLI flags stable (`-x`, `-f`, `-o`); doctor checks `--version` not exact patch |
| `mmdc 11.16` + `mermaid 11.16` | Bundled internally | Let mmdc manage its Mermaid version — do not pin separate `mermaid` npm package |
| `ba-tools` Python | `git 2.x` | No GitPython — subprocess only; Git required for `.ba-ops/` workflow but not imported at runtime for trace/hash ops |

## Architecture Stack Diagram

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Python CLI core | HIGH | Typer/jsonschema/filelock are proven PyPI standards; versions verified on PyPI 2026-07-20 |
| Render toolchain | HIGH | mmdc 11.16.0 and draw.io 30.3.14 verified on npm/GitHub releases; BRD-mandated |
| Skill runtime | MEDIUM | Cursor Skills are v1 host choice; SKILL.md contract is portable but host API may evolve (R-9) |
| DOCX / frontmatter | HIGH | python-docx 1.2.0 and python-frontmatter 1.3.0 stable on PyPI |
| Dev tooling | HIGH | uv/ruff/pytest versions verified; Astral stack is 2025–2026 Python standard |
| Git integration | HIGH | subprocess pattern aligns with BRD; GitPython rejection well-documented |

## Sources

- [BRD v1.0 §8.E, §12.1, §12.3](docs/BRD-v1.0.md) — authoritative stack constraints (HIGH)
- [PROJECT.md](.planning/PROJECT.md) — tech stack summary (HIGH)
- [Typer 0.27.0 on PyPI](https://pypi.org/project/typer/) — CLI framework version (HIGH)
- [jsonschema 4.26.0 on PyPI](https://pypi.org/project/jsonschema/) — schema validation (HIGH)
- [filelock 3.29.6 on PyPI](https://pypi.org/project/filelock/) — lock dependency + CVE floor (HIGH)
- [python-docx 1.2.0 on PyPI](https://pypi.org/project/python-docx/) — DOCX plugin (HIGH)
- [python-frontmatter 1.3.0 on PyPI](https://pypi.org/project/python-frontmatter/) — Markdown metadata (HIGH)
- [pydantic 2.13.4 on PyPI](https://pypi.org/project/pydantic/) — CLI envelope models (HIGH)
- [@mermaid-js/mermaid-cli 11.16.0 on npm](https://www.npmjs.com/package/@mermaid-js/mermaid-cli) — Mermaid render (HIGH)
- [draw.io Desktop v30.3.14 release](https://github.com/jgraph/drawio-desktop/releases/tag/v30.3.14) — BPMN export CLI (HIGH)
- [Node.js 22.23.1 LTS](https://nodejs.org/en/blog/release/v22.23.1) — Node baseline (HIGH)
- [Python hashlib.file_digest docs](https://docs.python.org/3/library/hashlib.html#hashlib.file_digest) — SHA-256 streaming (HIGH)
- [uv 0.11.29 on PyPI](https://pypi.org/project/uv/) — package manager (HIGH)
- [ruff 0.15.22 on PyPI](https://pypi.org/project/ruff/) — linter (HIGH)
- [pytest 9.1.1 on PyPI](https://pypi.org/project/pytest/) — test runner (HIGH)
- [Cursor Skills SKILL.md structure](C:\Users\TungNS\.cursor\skills-cursor\create-skill\SKILL.md) — skill runtime contract (MEDIUM)
- [GitPython resource leak note](https://github.com/gitpython-developers/GitPython) — subprocess preference (MEDIUM)

<!-- gsd-stack-end -->

<!-- gsd-conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- gsd-conventions-end -->

<!-- gsd-architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- gsd-architecture-end -->

<!-- gsd-skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.cursor/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- gsd-skills-end -->

<!-- gsd-workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- gsd-workflow-end -->

<!-- gsd-profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- gsd-profile-end -->
