# Pitfalls Research

**Domain:** Deterministic-CLI + LLM agent suite — grounded requirements generation, Mermaid diagramming, UI mockups, REQ-ID traceability (BA Daily Operators)
**Researched:** 2026-06-17
**Confidence:** HIGH (derived directly from DESIGN.md v0.2.2 and PROJECT.md; domain-specific failure modes extracted from design invariants and stated non-negotiables)

---

## Critical Pitfalls

### Pitfall 1: Citation-Exists Check Defeated by Substring Gaming

**What goes wrong:**
`ba-tools verify` confirms `source_trace.span` is a real ≥12-char substring of `source_trace.doc`, but the LLM learns to quote a safe generic passage (e.g., "The system shall") that exists in the source but does not actually justify the specific requirement written. The check passes; the grounding is false.

**Why it happens:**
The verbatim-substring gate is a *presence* check, not a *relevance* check. The agent, under revision pressure from `ba-critic`, anchors to a quote it knows is in the source rather than the quote that legitimately supports the claim. This is the "≥12-char span" version of a hash collision: structurally valid, semantically empty.

**How to avoid:**
- `ba-critic` must evaluate whether the cited span *semantically supports* the requirement, not just confirm the span exists. The CoVe step must independently re-derive the requirement from the source and compare, not just echo the span.
- Add a lint flag in `ba-tools lint-requirements`: warn when `source_trace.span` is a boilerplate phrase (short, non-specific, appears more than N times in the document).
- Enforce minimum span specificity: spans that are generic clauses (`shall`, `the system`, `user can`) below a uniqueness threshold should trigger a `WARN_GENERIC_CITATION` flag.

**Warning signs:**
- Multiple requirements sharing the same `source_trace.span` verbatim.
- Span is a header or section title rather than a content sentence.
- `ba-critic` revisions converge quickly (1 loop) — genuine grounding usually requires more re-derivation effort.
- Span length exactly equals the 12-char minimum.

**Phase to address:**
`ba-tools` CLI build (Phase 1) — add the generic-citation lint. `ba-srs-analyze` + `ba-critic` wiring (Phase 2) — specify the CoVe instruction to compare re-derived claim vs cited span, not merely verify span presence.

---

### Pitfall 2: CoVe Loop Converging to False Confidence

**What goes wrong:**
`ba-critic` runs ≤3 revision loops. On loop 2 or 3, the critic generates verification questions, then answers them from context already primed by the draft. The loop "converges" (no new failures found) not because the requirements are good but because the critic's verification questions are contaminated by the draft's framing. The Quality gate passes; the SRS is wrong.

**Why it happens:**
The Codex v1 runtime runs `ba-uc` as a single sequential agent loop — true fresh-context subagent spawn is the v2 Claude/Task model (DESIGN §1, §9). In Codex v1, `ba-critic` re-derives from source by instruction, not by architectural isolation. If the workflow or system prompt includes the draft in the critic's context window, the critic cannot be genuinely independent.

**How to avoid:**
- The `ba-critic` agent prompt must receive: the original source document only + the requirements JSON to critique. It must NOT receive the SRS prose or prior critic rounds as positive examples.
- Critic verification questions must be generated *before* the critic reads the requirements JSON (generate-then-evaluate, not evaluate-while-reading).
- Mark in `AGENTS.md` guardrails: "ba-critic receives source + requirements only; do not pass prior SRS draft."
- In v2 (Task subagents), isolate ba-critic as a genuinely fresh context — no shared conversation history.

**Warning signs:**
- Critic loop exits on revision 1 with no changes.
- Critic findings are purely stylistic (phrasing, grammar) with no substantive grounding issues flagged.
- All requirements pass citation-exists AND critic with zero `WARN` flags on first pass — statistically unlikely for a real SRS.

**Phase to address:**
`ba-srs-analyze` + `ba-critic` wiring (Phase 2). Agent prompt design must explicitly sequence: source-only context → generate questions → load requirements JSON → answer questions independently.

---

### Pitfall 3: Determinism Boundary Erosion — Judgement Leaking into CLI

**What goes wrong:**
Under time pressure, a developer adds logic to `ba-tools` that makes a judgement call: e.g., `lint-requirements` outputs a "suggested rewrite" for an ambiguous requirement, or `resolve-route` infers intent from the free-text argument when `--route` is absent. The CLI is no longer deterministic — its output depends on an LLM call or heuristic reasoning, not a file/command/hash.

**Why it happens:**
The boundary ("CLI does only what a file, command, or hash can prove") is a design principle, not enforced by the language. Python makes it easy to add a utility function that calls an LLM. The seduction is that it "simplifies the workflow" to put small judgements in the CLI rather than spawn an agent.

**How to avoid:**
- Hard rule in DESIGN §5 is the contract: `ba-tools` is pure file/hash/command work. Any proposed CLI addition that requires reasoning or heuristics goes to an agent.
- `resolve-route` may ONLY return the operator's static `DEFAULT_ROUTE` — never parse free text.
- Code review checklist: any PR touching `ba_tools.py` must confirm no subprocess call to an LLM, no regex-based intent inference, no "smart" fallback logic.
- `ba-tools` test suite: each command must be deterministically reproducible given the same inputs — run it twice, compare outputs byte-for-byte.

**Warning signs:**
- `ba-tools` command accepts a `--prompt` or `--context` argument.
- A CLI command outputs different results for identical inputs on repeated runs.
- `resolve-route` returns values not present in the operator's static route table.
- A CLI command's JSON output includes a `suggestion` or `recommended` field populated with prose.

**Phase to address:**
`ba-tools` CLI build (Phase 1) — establish the determinism test harness before any workflow integration.

---

### Pitfall 4: Determinism Boundary Erosion — Verification Leaking into Agents

**What goes wrong:**
The inverse of Pitfall 3: an agent workflow begins performing its own hash checks, citation-exists logic, or state writes inline rather than delegating to `ba-tools verify` and `ba-tools state update`. State diverges because two code paths manage `.ba-ops/STATE.md`, and one of them does not hold the lockfile.

**Why it happens:**
Agents are LLMs — they will naturally "try to help" by doing verification inline if the workflow instruction is ambiguous. A poorly written workflow step like "check that the requirements are grounded" can be interpreted by the agent as instructions to open the source file and search for spans itself, bypassing `ba-tools verify`.

**How to avoid:**
- Workflow `.md` files must phrase verification steps as explicit CLI calls: "Run `ba-tools verify --config <cfg>` and report the JSON result." Never "check that X is valid."
- STATE.md writes are ONLY via `ba-tools state update|patch|advance`. Workflow instructions must never ask the agent to write `.ba-ops/STATE.md` directly.
- Lockfile guard (`STATE.md.lock`, `O_EXCL`, 10s stale) is non-optional — implement it before writing any workflow that calls `state update`.

**Warning signs:**
- Agent output contains a manually constructed JSON object that mirrors `ba-tools verify` output.
- STATE.md has content written outside a `ba-tools state` call (check git blame).
- Two concurrent operator runs produce inconsistent STATE.md (lockfile race symptom).

**Phase to address:**
`ba-tools` CLI build (Phase 1, lockfile) and workflow layer (Phase 2+) — gate wording review before any agent integration.

---

### Pitfall 5: Codex Byte Budget Silent Truncation

**What goes wrong:**
AGENTS.md or an eagerly-loaded reference file grows past 32,768 bytes. Codex silently truncates it mid-instruction. The skill fires, appears to work, but is operating on incomplete guardrails. The truncation point may fall in the middle of a "non-negotiables" section, silently disabling the Safety gate instruction.

**Why it happens:**
Byte budgets are not enforced at authoring time — there is no pre-commit hook or CI check. Files grow gradually as requirements are added to AGENTS.md. The 32,768-byte limit is a Codex runtime behavior, not a file-system error, so it produces no warning.

**How to avoid:**
- Add a byte-budget check to the build/lint pipeline: `wc -c` on AGENTS.md and all eagerly-referenced files, fail if ≥ 32,768 bytes.
- The strict rule from DESIGN §7: eager refs (loaded unconditionally) < 32,768 B; DEFAULT workflow < 38,000 B; LARGE workflow < 54,000 B.
- When a workflow exceeds its tier: extract per-route bodies to `workflows/<operator>/routes/<route>.md` and Read only the needed route file (no `@`-import behind a conditional — see Pitfall 6).
- Track file sizes in CI as a regression gate, not just a one-time check.

**Warning signs:**
- AGENTS.md or a workflow file approaching 28,000 bytes (20% headroom warning threshold).
- A skill appears to run but ignores a gate or constraint documented in the latter half of AGENTS.md.
- Behavior changes between runs when Codex context window varies.

**Phase to address:**
Skill/workflow authoring (all phases) — byte check must be wired into the build pipeline in Phase 1, before the first skill is authored.

---

### Pitfall 6: Eager @-Import Behind a Conditional

**What goes wrong:**
A workflow file uses a Codex `@`-import (eager file reference) inside a conditional block (e.g., `if --route == "full": @workflows/ba-uc-delivery/routes/full.md`). Codex resolves `@`-imports at load time, not at execution time — all referenced files are loaded regardless of the branch taken. The effective document size is the sum of all eagerly-imported files.

**Why it happens:**
Developers familiar with programming languages assume `@`-imports are evaluated lazily when inside a conditional. Codex does not work that way.

**How to avoid:**
- DESIGN §7 explicitly states: "no eager `@`-import behind a conditional." Use explicit `Read` tool calls inside route branches instead of `@`-imports.
- Audit every `@` reference in workflow files: if it appears inside an `if`/`when`/`route ==` block, convert it to a `Read` call.
- Byte-budget check (Pitfall 5) catches the symptom; this pitfall addresses the cause.

**Warning signs:**
- Workflow file with `@`-imports and route-conditional logic.
- Unexpected large effective size when the route taken should be small.
- Skills that only use one route still load all route files.

**Phase to address:**
Workflow authoring (Phase 2+) — establish the `@`-vs-`Read` convention in the workflow template before writing any multi-route workflow.

---

### Pitfall 7: Implicit Invocation Firing the Analysis Path Unintentionally

**What goes wrong:**
`allow_implicit_invocation: true` (or absent, defaulting to permissive) on a spine or conductor skill causes Codex to auto-fire `ba-srs-analyze` or `ba-uc` when the user mentions a use case in passing, without explicitly invoking `$ba-srs-analyze`. The analysis path runs, overwrites `.ba-ops/srs/<slug>/`, and the Quality gate fires — all from a conversational mention.

**Why it happens:**
`allow_implicit_invocation` defaults to permissive in Codex. Developers who focus on the SKILL.md body forget to author the `agents/openai.yaml` for every spine skill.

**How to avoid:**
- DESIGN §3 is explicit: `allow_implicit_invocation: false` on the conductor (`ba-uc`), all spine skills (`ba-srs-analyze`, `ba-mermaid`, `ba-mockup`), and the DOCX/backlog plugins.
- The `agents/openai.yaml` file is mandatory for every skill — its absence is a build error, not a graceful default.
- Only `ba-make-diagram` (pure generator, no STATE.md writes) may allow implicit invocation.
- Build checklist: verify `allow_implicit_invocation: false` in every `agents/openai.yaml` before shipping.

**Warning signs:**
- A skill fires without the user typing `$ba-<operator>`.
- STATE.md is updated during a casual conversation about requirements.
- `agents/openai.yaml` missing from a skill directory.

**Phase to address:**
Skill layout authoring (Phase 1/2) — `agents/openai.yaml` with explicit `allow_implicit_invocation: false` must be created alongside every SKILL.md.

---

### Pitfall 8: Route Inferred from Free Text

**What goes wrong:**
When `--route` is absent, the workflow (or `resolve-route`) tries to parse the user's message to infer which route was intended. "I want to just do a quick diagram" becomes `route=diagram`. The inferred route bypasses the default-route contract and introduces non-determinism into the CLI layer.

**Why it happens:**
`resolve-route` is a simple CLI command that returns a static string; the temptation is to make it "smarter" by adding NLP to handle common phrasings. DESIGN §2 explicitly forbids this: "Operators still never infer intent from free text — they only fall back to a known-safe default route."

**How to avoid:**
- `ba-tools resolve-route <operator>` returns exactly one value: the `DEFAULT_ROUTE` constant for that operator. No arguments, no context, no parsing.
- The SKILL.md route-resolution step must read: "If `--route` is absent, call `ba-tools resolve-route <operator>` and use that value. Do not parse the user message."
- Test: call `resolve-route` with no `--route` for every operator; assert deterministic output across different user message phrasings passed as env context.

**Warning signs:**
- `resolve-route` accepts more than one argument.
- Different `--route`-absent invocations of the same operator produce different routes.
- Workflow instruction says "determine the route from the user's intent."

**Phase to address:**
`ba-tools` CLI build (Phase 1) — `resolve-route` implementation + SKILL.md template (Phase 2).

---

### Pitfall 9: Lockfile Race on STATE.md

**What goes wrong:**
Two concurrent `ba-uc` runs (e.g., the user re-invokes before the first completes, or two terminal sessions) both read STATE.md, both see no lock, both write their updates. The second write overwrites the first. The pipeline resumes from the wrong state; `uc-status` reports inconsistent next_step.

**Why it happens:**
Lockfile implementation is often deferred as "nice to have." In Codex, multiple chat sessions can share a filesystem. Python's default file-write is not atomic.

**How to avoid:**
- STATE.md writes MUST use `O_EXCL` (exclusive create) on `STATE.md.lock`. This is a non-optional implementation requirement from DESIGN §8.
- 10-second stale-lock timeout: if `STATE.md.lock` exists and is older than 10 seconds, treat as abandoned and acquire.
- All three `state update|patch|advance` subcommands must acquire the lock before reading STATE.md and release after writing.
- Test: spawn two concurrent `ba-tools state update` calls with overlapping timing; assert only one succeeds, the other returns a lock-conflict error.

**Warning signs:**
- STATE.md written without a corresponding `.lock` file being created and deleted.
- STATE.md `last_updated` timestamp regresses (older than the previous value).
- `uc-status` reports `next_step` that does not match the last gate verdict in STATE.md.

**Phase to address:**
`ba-tools` CLI build (Phase 1) — lockfile is part of the `state` command family, not an afterthought.

---

### Pitfall 10: Stale Render Embedded When Source Changed

**What goes wrong:**
A Mermaid or draw.io source file is updated after the last render. The workflow embeds the previously-rendered PNG (still on disk, path unchanged). The DOCX deliverable or SRS contains a diagram that does not match the current source. `ba-tools verify` does not catch it because the hash check compares `rendered_sha256` to `embedded_sha256` — not to the source hash at render time.

**Why it happens:**
The manifest records the hash of the rendered artifact and the embedded artifact to confirm they match each other. It does not record the hash of the source at render time. Source drift is a separate check that must be explicitly wired.

**How to avoid:**
- The manifest must record `source_sha256_at_render` in addition to `rendered_sha256` and `embedded_sha256`.
- `ba-tools verify` must compare current `sha256(source_file)` against `source_sha256_at_render`. Mismatch → `STALE_RENDER` failure.
- `ba-tools index update` already flags `stale` (source hash changed → re-run needed). The same stale check must be in `ba-tools verify` at the manifest level.
- DESIGN §11 non-negotiable: "Embed a stale render when the source changed" is explicitly forbidden.

**Warning signs:**
- Manifest `source_sha256_at_render` field absent or null.
- `ba-tools index update` reports `stale` for a slug but `ba-tools verify` reports `ok: true`.
- Rendered PNG modification timestamp older than source `.mmd` or `.drawio` modification timestamp.

**Phase to address:**
`ba-tools` CLI build (Phase 1 — manifest schema) and plugin authoring (Phase 7 — `export-diagram`, `render-mermaid`, `update-docx`).

---

### Pitfall 11: Synthetic/Fallback Diagram Generation

**What goes wrong:**
When `mmdc` or the draw.io CLI is not found, the workflow falls back to generating a PNG via Pillow, an SVG-to-PNG converter, or a screenshot of rendered HTML. The manifest records `diagram_source = "synthetic"`. The deliverable is accepted because it looks correct. The no-synthetic invariant is violated; future audits cannot distinguish CLI-rendered from hand-crafted images.

**Why it happens:**
Render CLI not installed is a common early-phase condition. Developers add a fallback to "unblock" themselves, intending to remove it later. The removal never happens.

**How to avoid:**
- DESIGN §5 render backend resolution: "Not found → hard fail. No fallback renderer." This is absolute.
- `ba-tools export-diagram` and `ba-tools render-mermaid` must exit `2` with a clear error when the CLI is not found. They must never call Pillow, subprocess screenshot, or any other renderer.
- The Safety gate checks `diagram_source == "draw.io CLI" | "mermaid CLI"` — any other value is a gate failure.
- Add a manifest policy flag check to `ba-tools verify`: `no_synthetic_diagram_fallback: true` must be present and the `diagram_source` must be one of the two approved values.

**Warning signs:**
- `diagram_source` in manifest is anything other than `"draw.io CLI"` or `"mermaid CLI"`.
- `no_synthetic_diagram_fallback` key absent from manifest.
- PNG file size unusually small or large compared to CLI-rendered output.
- Import of `PIL`, `cairosvg`, `selenium`, or `playwright` in `ba_tools.py`.

**Phase to address:**
`ba-tools` CLI build (Phase 1 — hard-fail on missing CLI) and Safety gate wiring (Phase 7 plugins).

---

### Pitfall 12: DOCX Media Append Instead of Replace

**What goes wrong:**
`update-docx` adds a new image relationship to the DOCX XML instead of replacing the existing placeholder image relationship in-place. The DOCX now contains two images: the old placeholder and the new diagram. Word renders whichever appears first in the relationship index. Reviewers see the stale placeholder; the delivered document is wrong.

**Why it happens:**
`python-docx` makes it easier to add a new image (one API call) than to replace an existing one (requires manipulating the OOXML relationships directly). Developers use the add path because it works at first glance.

**How to avoid:**
- DESIGN §11 non-negotiable: "Append a new image to the DOCX instead of replacing the placeholder media" is explicitly forbidden.
- `update-docx` must locate the placeholder by its relationship ID (stored in the manifest), open the OOXML zip, overwrite the binary in `word/media/`, and leave the relationship ID unchanged.
- After the replace: `embedded_sha256` in the manifest must equal `sha256(extracted_media_from_docx)` — re-extract and verify, do not trust the write succeeded.
- The Safety gate checks the extension: `.png` or `.svg` only. Any other extension is a gate failure before the replace is attempted.

**Warning signs:**
- DOCX file size grows by approximately the image size on each `update-docx` run (append symptom).
- Two images with the same caption in the DOCX.
- `embedded_sha256 != rendered_sha256` in the manifest after `update-docx`.

**Phase to address:**
Plugin authoring (Phase 7 — `ba-uc-delivery`, `update-docx` implementation).

---

### Pitfall 13: REQ-ID Churn Breaking Traceability

**What goes wrong:**
REQ-IDs are re-assigned between analysis iterations (e.g., `REQ-003` becomes `REQ-007` after a requirements re-numbering pass). Every downstream artifact (diagram, mockup, story) that cited `REQ-003` now holds an orphan ID. `ba-tools index update` floods with orphan warnings; the traceability matrix is meaningless.

**Why it happens:**
Analysts re-order requirements for readability or logical flow, renumbering sequentially. This feels natural in a document but breaks the identifier contract that the entire suite depends on.

**How to avoid:**
- REQ-IDs are permanent identifiers, not sequence numbers. Once assigned, a REQ-ID must never be reassigned to a different requirement.
- Deprecated requirements get a `status: deprecated` field — they are never deleted and their IDs are never reused.
- `ba-tools lint-requirements` must flag any REQ-ID that existed in the previous version of REQUIREMENTS.md and has changed its `statement` content by more than a diff threshold — that is a disguised renumber.
- `ba-tools index update` orphan count is a lagging indicator; add a `ba-tools verify --check-id-stability` gate that compares the current REQUIREMENTS.md REQ-ID set against the prior committed version.

**Warning signs:**
- `ba-tools index update` reports orphan count spike after a requirements revision.
- A REQ-ID appears in INDEX.md as both an orphan and a gap simultaneously (the old ID became orphan; the new ID has no coverage yet).
- REQUIREMENTS.md diff shows IDs being renumbered rather than new IDs appended.

**Phase to address:**
`ba-tools` CLI build (Phase 1 — lint-requirements ID stability check) and traceability matrix (Phase 3 — index update + gap/orphan/stale flags).

---

### Pitfall 14: Orphan/Gap Drift Going Undetected Between Index Rebuilds

**What goes wrong:**
`ba-tools index update` is only called at the end of the `ba-uc` conductor run. Between runs, a developer edits a mockup or diagram directly (outside the operator), adding or removing `req_ids` fields. The INDEX.md traceability matrix becomes stale. Orphans and gaps accumulate silently until the next `index update`, which may be days later.

**Why it happens:**
INDEX.md is a derived artifact — it is only as fresh as the last `index update` call. There is no continuous watch mode in v1.

**How to avoid:**
- `ba-tools index update` must be callable standalone (not only from the conductor) and should be fast enough to run on every git pre-commit.
- Recommend in the USER-GUIDE: always run `ba-tools index update` after any manual edit to `.ba-ops/` artifacts.
- Add a `stale_since` timestamp to INDEX.md header: the timestamp of the last `index update`. If the delta exceeds a configurable threshold (default 24h), `ba-tools verify` emits a `WARN_INDEX_STALE`.
- The Quality gate must check `index_stale: false` as part of `ba-tools verify`.

**Warning signs:**
- INDEX.md `stale_since` timestamp is more than 24 hours old.
- A mockup `.html` file has `req_ids` that are not in the current INDEX.md.
- `ba-tools index update` run produces a materially different orphan/gap count than the current INDEX.md shows.

**Phase to address:**
Traceability matrix (Phase 3) and Quality gate wiring (Phase 2+).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip `agents/openai.yaml`, rely on Codex default invocation behavior | Faster skill authoring | Implicit invocation fires the analysis path unexpectedly; pipeline contamination | Never |
| Write STATE.md from agent inline (no lockfile) | One less CLI dependency early on | Race conditions corrupt pipeline state when two sessions run | Never |
| Use `@`-import for all route files unconditionally | Simpler workflow file | All route files loaded regardless of route taken; blows byte budget silently | Never |
| Add a synthetic render fallback when CLI unavailable | Unblocks demo/review | `no_synthetic_diagram_fallback` invariant broken; manifests become untrustworthy | Never |
| Re-number REQ-IDs for clarity | Cleaner document | Entire downstream traceability matrix orphaned | Never |
| Call `ba-tools lint-requirements` but skip `ba-critic` loop | Faster iteration | LLM self-grounding not independently verified; false confidence from CoVe convergence | Never for `stated` reqs; acceptable for `inferred` reqs with low risk |
| Run `index update` only at end of conductor run | Simpler orchestration | Gap/orphan drift undetected for hours; Quality gate works on stale matrix | Acceptable in Phase 1; must be addressed by Phase 3 |
| Hard-code absolute paths in config during development | Removes path-resolution complexity | Config non-portable; fails on any other machine or CI | Never in committed config |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `mmdc` (Mermaid CLI) | Assume `mmdc` is on PATH; swallow the not-found error and return empty PNG | Probe all resolution paths (`$MERMAID_CLI` → PATH `mmdc` → `npx @mermaid-js/mermaid-cli`); hard-fail with exit `2` and a clear message if none found |
| `draw.io` desktop CLI | Use `drawio` only; miss `draw.io` and `diagrams.net` binary names on different OS/install paths | Try all three names + common install paths; hard-fail if none resolved |
| `python-docx` OOXML media replace | Call `Document.add_picture()` to update diagram | Directly overwrite the binary in the OOXML zip's `word/media/` directory; keep the existing relationship ID |
| Codex `@`-import | Use `@`-import inside route conditionals expecting lazy evaluation | `@`-imports are eager (load time); use `Read` tool calls inside route branches |
| `.ba-ops/STATE.md` concurrent writes | Write STATE.md with standard `open(..., 'w')` | Use `O_EXCL` lock file (`STATE.md.lock`) before any read-modify-write on STATE.md |
| `ba-tools verify` citation check | Pass `source_trace.span` as a regex pattern | The check is a literal verbatim substring search — no regex, no case folding, exact bytes |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `ba-tools index update` full-rebuild on every call | Noticeable lag (>2s) for large `.ba-ops/` trees | Incremental update: only re-scan artifacts whose file mtime changed since last index timestamp | At ~50+ UC slugs with multiple artifacts each |
| `ba-critic` ≤3 loop hard limit not enforced | Critic loops indefinitely on a pathological requirement set, consuming context | Enforce the loop counter in the workflow instruction: exit after 3 revisions regardless; emit `MAX_REVISIONS_REACHED` flag | Any SRS with genuinely ambiguous source material |
| Loading all reference files into agent context at once | Agent context window saturated; later instructions ignored or truncated | Read only the reference file needed for the current step (DESIGN §1 principle 7: "lazy references") | Any agent with >3 reference files loaded simultaneously |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Writing user-supplied `--uc` argument directly into a shell command without sanitization | Shell injection via UC argument (e.g., `"; rm -rf .ba-ops/"`) | Pass all arguments as list elements in `subprocess.run([...])`, never `shell=True`; `ba-tools scan` advisory prompt-injection check |
| Storing absolute machine paths in committed `.ba-ops/config.json` | Config leaks developer machine layout; fails CI and other machines | All paths relative to `--repo-root`; `ba-tools init` resolves at runtime via `sys.executable` and `git rev-parse --show-toplevel` |
| `ba-tools scan` result ignored by workflow | Prompt injection in a UC source document goes undetected | Scan output is advisory (not a hard gate in v1) — but the Safety gate must log the scan result in the manifest; a `WARN_INJECTION` finding must be surfaced in the chat output |
| DOCX media path traversal | A malicious `source_trace.doc` path points outside `.ba-ops/` | `ba-tools` must validate all file paths are under the repo root before opening; reject any path containing `..` or absolute segments |

---

## "Looks Done But Isn't" Checklist

- [ ] **Citation-exists gate:** Verify the gate rejects a span that is present in the source but not in the claimed section (section-scoped substring, not whole-doc substring).
- [ ] **Lockfile:** Verify `STATE.md.lock` is created before the STATE.md read and deleted after the write — not just before the write.
- [ ] **Manifest stale-render check:** Verify `source_sha256_at_render` is in the manifest schema and populated on every render call, not just when the `--check-stale` flag is passed.
- [ ] **Byte budget CI check:** Verify the check runs on every commit that touches `.agents/`, not just on release builds.
- [ ] **`allow_implicit_invocation: false`:** Verify the `agents/openai.yaml` file exists for every skill, not just the conductor.
- [ ] **Hard-fail on missing render CLI:** Verify `ba-tools render-mermaid` with no `mmdc` available exits `2` — not `0` with an empty output file.
- [ ] **Media-replace vs append:** Verify DOCX file size does not grow on repeated `update-docx` calls with the same source image.
- [ ] **REQ-ID stability:** Verify `ba-tools lint-requirements` catches a requirements file where an existing REQ-ID's `statement` has been replaced with a different requirement.
- [ ] **Index stale warning:** Verify `ba-tools verify` emits `WARN_INDEX_STALE` when INDEX.md was last rebuilt more than the configured threshold ago.
- [ ] **`resolve-route` determinism:** Verify `ba-tools resolve-route ba-srs-analyze` returns the same value regardless of what is in the current chat session or environment.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Generic citation span accepted, SRS shipped | HIGH | Re-run `ba-srs-analyze` with explicit CoVe instruction to reject boilerplate spans; diff new requirements JSON against shipped version; notify stakeholders of revision |
| STATE.md corrupted by lockfile race | MEDIUM | Delete `STATE.md.lock` (stale); run `ba-tools uc-status` to reconstruct state from artifact presence on disk; manually set `current_step` and `last_gate_verdict` |
| Byte budget exceeded, skill silently truncated | MEDIUM | Split workflow: extract per-route bodies to `routes/<route>.md`; measure effective size after split; redeploy skill |
| Stale render embedded in delivered DOCX | MEDIUM | Re-run `ba-tools export-diagram` or `ba-tools render-mermaid`; re-run `ba-tools update-docx`; re-verify manifest; issue corrected deliverable with changelog entry |
| REQ-ID churn, orphan flood | HIGH | Do NOT re-number to fix; add `status: deprecated` to old IDs; create new IDs for reworded requirements; re-run `ba-tools index update`; manually update downstream `req_ids` fields in artifacts |
| Synthetic diagram shipped in deliverable | HIGH | Identify which manifests have `diagram_source != "draw.io CLI"\|"mermaid CLI"`; install the correct render CLI; re-run `export` route for affected slugs; reissue deliverables |
| CoVe false convergence, low-quality SRS accepted | HIGH | Re-run `ba-critic` with source-only context (no draft in critic window); treat any existing gate-passed SRS as unverified until re-run; flag to stakeholders |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Citation-exists substring gaming | Phase 1 (`ba-tools lint`) + Phase 2 (`ba-critic` prompt) | `WARN_GENERIC_CITATION` flag fires on boilerplate spans in test fixtures |
| CoVe false confidence | Phase 2 (`ba-critic` agent prompt design) | Critic receives source-only context; verified by agent prompt review |
| Judgement leaking into CLI | Phase 1 (`ba-tools` implementation) | Deterministic repeatability test: identical inputs → identical outputs byte-for-byte |
| Verification leaking into agents | Phase 1 (lockfile) + Phase 2+ (workflow wording) | Workflow instruction review checklist before any agent integration |
| Codex byte budget silent truncation | Phase 1 (build pipeline) | CI byte-check gate on all `.agents/` files |
| Eager `@`-import behind conditional | Phase 2+ (workflow authoring) | `@`-import audit: no `@` inside route-conditional blocks |
| Implicit invocation firing analysis path | Phase 1/2 (skill layout) | Verify `allow_implicit_invocation: false` in every `agents/openai.yaml` |
| Route inferred from free text | Phase 1 (`resolve-route` impl) + Phase 2 (SKILL.md template) | `resolve-route` unit test: identical output for all user-message phrasings |
| STATE.md lockfile race | Phase 1 (`state` command family) | Concurrent-write test: two overlapping state updates; assert one succeeds, one errors |
| Stale render embedded | Phase 1 (manifest schema) + Phase 7 (plugins) | `source_sha256_at_render` present in manifest; stale-render test fixture |
| Synthetic diagram fallback | Phase 1 (hard-fail impl) + Phase 7 (Safety gate) | `render-mermaid` with no `mmdc`: must exit `2`, not produce output |
| DOCX media append vs replace | Phase 7 (`update-docx` implementation) | DOCX byte-size stability test on repeated renders |
| REQ-ID churn | Phase 1 (lint) + Phase 3 (index) | ID-stability lint rejects renumbered requirements in test fixture |
| Orphan/gap drift undetected | Phase 3 (index) + Phase 2+ (Quality gate) | `WARN_INDEX_STALE` fires when index is stale in `ba-tools verify` |

---

## Sources

- DESIGN.md v0.2.2 (repo root) — §1 principles, §5 determinism boundary, §6 gates, §7 byte budgets, §8 `.ba-ops/` traceability, §11 non-negotiables
- PROJECT.md — confirmed requirements, constraints, key decisions, out-of-scope boundaries
- Codex documentation — `allow_implicit_invocation`, `@`-import eager-load behavior, `project_doc_max_bytes` = 32,768 B
- GSD Core architecture (`FIS_GSARCHITECTURE.md` referenced in DESIGN.md) — five-layer model, determinism boundary, gate patterns

---
*Pitfalls research for: BA Daily Operators — deterministic-CLI + LLM agent suite for grounded requirements, Mermaid diagramming, UI mockups, REQ-ID traceability*
*Researched: 2026-06-17*
