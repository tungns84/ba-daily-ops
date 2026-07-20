# Pitfalls Research

**Domain:** BA workflow harness (`ba-daily-ops`) — LLM skills + deterministic CLI + REQ-ID trace spine
**Researched:** 2026-07-20
**Confidence:** HIGH (grounded in BRD v1.0 §14 risks R-1…R-12, §11 acceptance criteria, SRS-SPEC N-1…N-5, and agent-harness audit literature)

## Critical Pitfalls

### Pitfall 1: LLM Gate Bypass (Prose-as-Proof)

**What goes wrong:**
The agent declares "citation gate passed" or "SRS complete" in chat without invoking `ba-tools`. Downstream routes start on unverified candidates. Handoff looks green in conversation but INDEX would show gap/stale if anyone ran the CLI.

**Why it happens:**
Skill prompts optimize for helpful completion. LLMs treat natural-language assertions as sufficient. Without an executable runner owning state transitions, the cheapest path is to skip subprocess calls and narrate success (BRD R-1).

**How to avoid:**
- Executable workflow runner (BRD-027) is the **only** component that promotes candidate → canonical.
- Skill workflows MUST call `ba-tools` and parse exit code + JSON; route advance blocked on non-zero exit.
- Gate evidence stored in `runs/<run-id>/journal.jsonl` — not in chat transcript.
- Integration tests: inject a candidate that fails citation gate; assert canonical hash unchanged and downstream routes never open (AC-BRD-027-02).

**Warning signs:**
- Chat says "passed" but `$ba-deliver status` shows route blocked or gate evidence missing.
- `journal.jsonl` has no gate subprocess record for a step marked complete.
- Skill SKILL.md describes gates in prose only — no mandatory CLI invocation sequence.

**Phase to address:**
Phase 3 — Executable Runner & Conductor (must land before any skill claims end-to-end delivery)

---

### Pitfall 2: False-Green RTM (INDEX Says OK, Coverage Isn't)

**What goes wrong:**
`INDEX.md` marks REQ-IDs `ok` when mandatory artifacts are missing, stale, or only exist as un-promoted candidates. BA Lead approves handoff; dev discovers missing mockup or orphan REQ-ID mid-sprint.

**Why it happens:**
Teams implement INDEX as "file exists" check instead of profile-aware coverage policy. Partial progress (SRS + flow present) gets averaged into green. Waivers get mislabeled as `ok`. Conformance corpus never seeded (BRD R-2, OBJ-6).

**How to avoid:**
- Coverage policy in `.ba-ops/coverage-policy.json` is machine-readable; INDEX derives status from policy + trace, never from agent opinion (BRD-026).
- Enforce semantic distinction: `ok` vs `waived` vs `gap` vs `stale` vs `orphan` — never collapse `waived` → `ok` (AC-BRD-026-02, BR-006).
- Conformance corpus ≥ 50 seeded mutations; **false-green = 0 is a release blocker** (§13.4).
- Candidate artifacts explicitly excluded from coverage (BR-007).

**Warning signs:**
- REQ with only SRS shows `ok` when policy requires flow + mockup (AC-BRD-026-01 scenario).
- INDEX hand-edited or treated as source of truth instead of regenerated view (BRD-003).
- No automated test where mockup deleted but INDEX still green.

**Phase to address:**
Phase 5 — Coverage Policy & Drift Detection (INDEX logic must not ship before policy engine)

---

### Pitfall 3: Markdown-Only SRS Drift (Dual Sources of Truth)

**What goes wrong:**
BA or agent edits `SRS.md` directly for speed. `requirements.json` lags. Flow/mockup reference REQ-IDs that exist in Markdown but not registry — or vice versa. Trace spine breaks silently until orphan/stale surfaces late.

**Why it happens:**
Markdown is familiar; JSON registry feels heavy. Render step skipped. Agents "fix" prose in the derived view because it is visible in preview (SRS-SPEC N-1…N-3).

**How to avoid:**
- `requirements.json` canonical; `SRS.md` only via `ba-tools render` (BRD-006, SRS-SPEC N-1).
- Gate fails if SRS.md contains REQ-ID absent from registry (N-2).
- Hand-edit of `SRS.md` overwritten on next render — document this loudly in BA-facing guides.
- Citation-exists gate operates on registry `source_trace`, not Markdown prose.

**Warning signs:**
- Git diff shows SRS.md requirement changes without matching `requirements.json` diff.
- Agent workflow writes to both files in one step.
- `$ba-srs` skill lacks explicit "render only after JSON gate pass" ordering.

**Phase to address:**
Phase 2 — REQ-ID Spine & SRS Pair (registry + render before downstream artifacts)

---

### Pitfall 4: Hash = Correctness Fallacy

**What goes wrong:**
Stakeholders treat green INDEX as proof requirements are **semantically correct** for the business. Wrong REQ statements, invented citations that pass substring match, or mis-scoped NFRs ship because "hash matched."

**Why it happens:**
Harness metrics (hash, gate pass) are objective and visible; semantic review is subjective and skipped under time pressure. Marketing oversells determinism (BRD R-10, BR-008, NFR-006).

**How to avoid:**
- Document explicitly: hash proves **provenance + drift detection**, not business truth (OBJ-4, BRD §6.2).
- Human sign-off required for `strict` publish; UAT checkbox in DoD at every tier (Appendix C).
- Citation-exists catches fabricated spans ≥ 12 chars but not wrong interpretation — keep blind critic at `standard`+.
- Never expose "semantic correctness" in CLI exit codes.

**Warning signs:**
- Pilot KPIs only track INDEX green, not paired rework-after-UAT counts.
- BA skips reading artifacts because "INDEX is ok."
- Docs or demos imply byte-reproducible LLM prose (confuses R-12).

**Phase to address:**
Phase 7 — Pilot & Release Discipline (measure rework, not just mechanical green)

---

### Pitfall 5: Candidate Treated as Canonical

**What goes wrong:**
Agent-written files land directly in `.ba-ops/srs/<slug>/` or mockup paths. INDEX counts them before gate pass. A failed run leaves poisoned "canonical" files that block resume or mask gaps.

**Why it happens:**
Staging vs production paths not separated. Skills write to final paths for convenience. Runner promotion step omitted in MVP rush (BRD-027, BR-007).

**How to avoid:**
- Candidates live under `runs/<run-id>/candidates/<step-id>/` only.
- Atomic promotion after gate pass; failed gate leaves canonical hash unchanged (AC-BRD-027-02).
- INDEX and trace update **only** post-promotion.
- `$ba-deliver status` distinguishes candidate vs canonical explicitly.

**Warning signs:**
- Artifact mtime updates without matching journal promotion event.
- Resume re-promotes already accepted step (AC-BRD-027-03 failure).
- No `candidates/` directory in `.ba-ops/runs/` layout.

**Phase to address:**
Phase 3 — Executable Runner & Conductor (same phase as gate bypass — shared root cause)

---

### Pitfall 6: Doc–Code–Help Drift

**What goes wrong:**
SKILL.md, BRD, and DESIGN describe routes, flags, or exit codes that differ from `ba-tools --help`. BA follows docs; CLI rejects command. Trust erodes; workarounds bypass gates.

**Why it happens:**
Docs edited manually; CLI evolves independently. Skill names drift (`$ba-tools` vs `ba-tools`). No CI check comparing generated help to committed docs (BRD R-3).

**How to avoid:**
- Single source of truth: generate reference docs from CLI `--help` where possible.
- Release gate: doc-vs-help check must pass (§15.3).
- Canonical namespace rules enforced in review checklist (BRD §17.1 — no `$ba-tools`, no `ba-srs` without `$`).
- SemVer MAJOR bump on CLI I/O contract changes with migration notes.

**Warning signs:**
- Onboarding BA hits exit code 2 on documented command.
- SKILL.md route list ≠ `ba-tools deliver plan` output.
- Multiple names for same profile tier in docs (`tier` vs `profile` without stating equivalence).

**Phase to address:**
Phase 1 — Harness Foundation (establish doc generation + CI hook early)

---

### Pitfall 7: Ceremony Sneak-Back into `light` Tier

**What goes wrong:**
Each release adds critic, readiness, intake, or extra confirmation to default `light` path. Golden path grows from 1 command to "run deliver, then critic, then fix, then status, then…" Adoption drops; BA returns to raw ChatGPT (BRD R-11).

**Why it happens:**
Developers dogfood on `strict`; defaults copy their workflow. Feature flags accumulate without profile gating. Regression tests missing for light command count.

**How to avoid:**
- Profile tier = single control plane (BRD-028); new ceremony MUST be gated by `standard` or `strict`.
- CI regression: `light` golden path = exactly 1 user command (`$ba-deliver run --uc <slug>`).
- Appendix D matrix is normative — new artifact kinds need explicit tier column before merge.

**Warning signs:**
- `$ba-deliver run` doc mentions optional steps BA must remember.
- Default config or skill auto-invokes critic without profile check.
- Pilot KPI "golden path command count" > 1 on light tier.

**Phase to address:**
Phase 4 — Golden Path Artifacts (lock light profile behavior when conductor ships)

---

### Pitfall 8: Windows / UTF-8 Friction Kills Pilot Before Value

**What goes wrong:**
Setup exceeds 30 minutes on Windows: wrong Python on PATH, console mojibake for Vietnamese, draw.io path with spaces fails, `PYTHONUTF8` unset. BA abandons before first green INDEX.

**Why it happens:**
Development on macOS/Linux only. Paths hard-coded. Subprocess encoding assumed UTF-8. Installer not tested on corporate Windows images (BRD R-5, NFR-003/008).

**How to avoid:**
- `ba-tools doctor` as mandatory preflight with actionable fixes (BRD-019).
- PowerShell installer; `PYTHONUTF8=1` default; test matrix Win/macOS/Linux each release (§15.3).
- All paths via `--repo-root`; `sys.executable` for subprocess — no author machine paths in committed config (NFR-004).
- Vietnamese UTF-8 in conformance fixtures, not just ASCII tests.

**Warning signs:**
- Doctor not in setup docs or skipped in pilot onboarding.
- CI only runs on Ubuntu.
- Bug reports show `` or `?` in SRS output on Windows.

**Phase to address:**
Phase 1 — Harness Foundation (doctor + installer before pilot)

---

### Pitfall 9: Unreadable Source → Fabricated Citations

**What goes wrong:**
Agent intake from scanned PDF, image-only DOCX, or binary blob. Citation gate should fail but agent paraphrases or invents 12+ char "quotes." REQ statements look grounded; UAT finds no source span.

**Why it happens:**
OCR out of scope but not enforced at intake. Doctor doesn't warn on non-extractable source. Agent pressure to complete UC (BRD R-7).

**How to avoid:**
- OCR/extraction is **pre-intake** responsibility — explicit in docs and `$ba-intake` preflight.
- Doctor warns when source file lacks extractable text.
- Citation-exists hard-fails exit 2 with REQ-ID list (AC-BRD-007-02); never auto-repair citation.
- Pilot includes 5 "messy source" UCs — track citation integrity KPI (= 0 stated REQs without valid span).

**Warning signs:**
- Citations are suspiciously paraphrased vs source tone.
- Source files in repo are `.pdf` without companion `.md` extract.
- Agent workflow has "fix citation" step that rewrites quote without human confirm.

**Phase to address:**
Phase 2 — REQ-ID Spine (citation gate before flow/mockup routes)

---

### Pitfall 10: Parallel BA State Corruption (Team Mode)

**What goes wrong:**
Two BAs write same owner folder or cross owner boundaries. Trace journal interleaves; canonical overwrite; INDEX shows inconsistent hashes. Git merge conflicts in `.ba-ops/` are resolved by hand, breaking trace.

**Why it happens:**
Team mode added without owner guard. `filelock` missing or stale-lock not handled. Lead runs mutating command against owner root (BRD R-8).

**How to avoid:**
- Owner-folder model: one canonical owner per REQ (BRD-023).
- Cross-owner write fails **before first byte** (AC-BRD-024-01).
- `filelock` on `STATE.md`; atomic replace on all writes (NFR-010).
- Team report is read-only aggregation only (BRD-025).
- Conductor auto-resolves `owner_id` from config so golden path stays one command (§16.2).

**Warning signs:**
- Git conflicts in `requirements.json` or `journal.jsonl`.
- Mutations succeed with mismatched `--owner`.
- No lock file or stale lock after crash.

**Phase to address:**
Phase 6 — Team Mode & Strict Tier (do not enable multi-BA until guards proven)

---

### Pitfall 11: Fake Render / Screenshot Fallback

**What goes wrong:**
BPMN or Mermaid export "works" via screenshot, Pillow, or manual paste. DOCX embeds images appended at end instead of rId replacement. Manifest hash matches wrong binary; customer deliverable unusable.

**Why it happens:**
draw.io not installed; developer adds convenient fallback. Plugin silently degrades to keep demo green (BRD R-4, BR-002, BR-003).

**How to avoid:**
- Official renderers only: draw.io Desktop CLI, `@mermaid-js/mermaid-cli` (BRD-012, constraints §12.1).
- Missing renderer → hard-fail early with install instructions, not fallback.
- DOCX gate verifies placeholder/rId replacement — reject append-at-end pattern.
- `strict` publish requires manifest reproducibility on second machine (§13.3).

**Warning signs:**
- PNG in export folder without corresponding CLI invocation in journal.
- DOCX file size jumps from appended images.
- CI skips draw.io because "optional."

**Phase to address:**
Phase 6 — Plugins (BPMN/DOCX) — opt-in but no fake render when enabled

---

### Pitfall 12: Byte-Reproducible LLM Expectation Mismatch

**What goes wrong:**
Stakeholders expect identical SRS prose across runs. Team builds flaky tests comparing full Markdown output. False failures erode confidence; or team weakens gates to make tests pass.

**Why it happens:**
Confusion between CLI determinism and LLM authoring. Sales/demo implies "same input → same document" (BRD R-12, NFR-005).

**How to avoid:**
- Communicate OBJ-4: integrity via hash/trace, not LLM byte replay.
- Tests hash **canonical frozen** artifacts after accept + promote, not mid-generation stream.
- Regression suite uses fixed conformance corpus inputs, separate from exploratory LLM runs.

**Warning signs:**
- Tests diff full SRS.md without normalizing or without freeze step.
- Stakeholder asks "why did wording change?" treated as harness bug.
- Agent re-run overwrites canonical without confirmation gate (BRD-015).

**Phase to address:**
Phase 7 — Pilot & Release Discipline (set expectations in pilot readout)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Agent writes directly to canonical paths (skip staging) | Faster first demo | Unrecoverable false-green, resume bugs | **Never** |
| INDEX maintained by hand for "quick fix" | Instant green row | Drift from registry; orphan IDs hidden | **Never** |
| Screenshot/Pillow render fallback | Demo works without draw.io | Invalid strict deliverables; audit failure | **Never** |
| Gate checks in prompt only (no CLI) | Less Python code | LLM bypass; no audit trail | **Never** |
| Single global pipeline ignoring profile tier | Simpler routing logic | light tier bloat; wrong ceremony | **Never** for tier-aware product |
| Skip conformance corpus until "later" | Ship MVP faster | False-green reaches pilot undetected | Only before **any** handoff claim — must exist before Phase 7 |
| Markdown-first SRS (JSON secondary) | Familiar BA workflow | Trace spine collapse | **Never** |
| Hard-code Windows paths in sample config | Local dev convenience | Breaks portability (OBJ-5) | **Never** in committed config |
| Waive stale artifacts to `ok` for demo | Clean INDEX screenshot | BR-006 violation; dev trust loss | **Never** — use `waived` with expiry |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| draw.io Desktop CLI | Assume installed; fallback to manual export | Plugin opt-in; doctor detects; hard-fail with install steps (R-4) |
| `@mermaid-js/mermaid-cli` | Require mmdc for light tier inline flow | Inline Mermaid in Markdown is valid without render; PNG/SVG optional per tier |
| python-docx | Append images to end of document | rId/placeholder replacement per BR-003; manifest hash last |
| Chat skill runtime | Skill logic coupled to one host API | Runtime-neutral SKILL.md contract; `.ba-ops/` agnostic (R-9) |
| Git / `.ba-ops/` | Binary merge conflict resolution by guess | Text/JSON state; atomic writes; owner lock; teach BA conflict workflow |
| Node.js for mmdc | Global npm path breaks on Windows | Doctor checks; env/flag override; no committed absolute paths |
| filelock | Stale lock after kill | Stale detection + recovery in resume (NFR-010, AC-BRD-027-03) |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| INDEX rebuild scans entire repo | `status` > 3s at 200 REQ | Scope to `.ba-ops/` + traced paths only; no renderer in verify path (NFR-001) | ~500 REQ without indexing strategy |
| Hash entire UC tree per status call | Linear slowdown as artifacts grow | Incremental trace records; hash only implicated artifacts on change | Multi-UC repos in one milestone |
| Re-run full deliver chain on resume | Duplicate LLM cost; overwrite risk | Resume skips completed routes when input hash unchanged (AC-BRD-010-03) | Any interrupted run |
| Regenerate all SRS.md on single REQ edit | Slow feedback loop | Render per slug; gate scoped to changed REQ where possible | Large registries |
| Conformance corpus run in dev loop | Developers skip tests | Run corpus on release only; subset in CI PR | Skipped → false-green escapes |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| `ba-tools` calls cloud LLM or telemetry | Violates zero-network; data exfil (NFR-009) | Static check: no HTTP in ba-tools; network only in installer |
| Path traversal via `--repo-root` or artifact paths | Read/write outside repo | Containment checks on all I/O (NFR-009) |
| Error JSON leaks absolute paths or secrets | Info disclosure on shared logs | Structured errors; redact paths (BRD-022, AC-BRD-024-01) |
| Treating tool exposure as authorization | Agent invokes mutating CLI with wrong args | Runner validates concrete args; confirmation gate before canonical overwrite (BRD-015) |
| Cloud LLM on sensitive source without disclosure | Compliance breach | Runtime policy explicit; product doesn't claim air-gap when using cloud LLM (NFR-009) |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Expose `ba-tools` in golden path docs | BA anxiety; wrong commands | BA-facing: only `$ba-deliver run`; CLI for CI/lead (R-6) |
| Hide gap/orphan/stale remediation loop | Feels broken when INDEX not green | Assumption §12.2 #7: embrace read INDEX → fix → re-run |
| Tier jargon without persona mapping | Wrong profile selected | Map light/standard/strict to personas (§7.3) |
| No `doctor` before first run | Long opaque failures | Setup one-off: doctor + init documented separately from golden path |
| Overloading one command with silent strict gates | light users hit unexpected blocks | Profile from `config.json`; conductor passes profile to runner |
| INDEX wall of red without next action | Paralysis | Status JSON names missing artifact kind and route to fix |

## "Looks Done But Isn't" Checklist

- [ ] **Golden path:** `$ba-deliver run` completes in chat but `$ba-deliver status` still shows blockers — verify status JSON, not chat summary
- [ ] **SRS pair:** `SRS.md` looks complete — verify every REQ-ID in Markdown exists in `requirements.json` and citations pass gate
- [ ] **INDEX green:** No `gap`/`orphan`/`stale` — verify against **profile policy**, not existence of files alone
- [ ] **Flow/mockup trace:** Diagrams render — verify `req_ids` in frontmatter/metadata resolve to registry
- [ ] **Gate evidence:** Step marked done — verify `journal.jsonl` contains subprocess exit 0 + evidence hash
- [ ] **Resume:** Process killed mid-run — verify `$ba-deliver resume` does not re-promote completed routes (AC-BRD-027-03)
- [ ] **Strict bundle:** DOCX exists — verify `MANIFEST.json` hash matches on second machine; human sign-off recorded
- [ ] **Team mode:** Lead sees aggregated report — verify no cross-owner writes occurred
- [ ] **Conformance:** Drift detection claimed — verify ≥ 49/50 mutations caught; false-green = 0
- [ ] **Windows pilot:** Works on dev Mac — verify doctor pass + Vietnamese UTF-8 on Windows 10+

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| LLM gate bypass | MEDIUM | Invalidate affected run; reset canonical from last promoted journal entry; re-run from failed route with runner-only promotion |
| False-green INDEX | HIGH | Fix coverage engine; regenerate INDEX; re-audit all pilot UCs; block release until conformance passes |
| Markdown-only SRS drift | MEDIUM | Treat SRS.md as disposable; rebuild `requirements.json` from source + re-render; re-trace downstream artifacts |
| Candidate → canonical confusion | MEDIUM | Move un promoted files to candidates; restore canonical from git; replay promotion from journal |
| Doc-code drift | LOW | Regenerate docs from `--help`; semver bump if CLI contract wrong in field |
| State corruption (team) | HIGH | Restore `.ba-ops/` from git; identify last good journal; re-run resume per owner |
| Fake render artifacts | MEDIUM | Delete invalid exports; re-run official CLI render; update manifest |
| Windows encoding damage | LOW | Set `PYTHONUTF8=1`; re-run render/verify; fix source files if mojibake committed |

## Pitfall-to-Phase Mapping

Recommended vertical MVP phases (from PROJECT.md harness-first sequencing). Each pitfall should be **prevented** in its phase, not patched later.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Doc–code–help drift (P6) | Phase 1: Harness Foundation | CI doc-vs-help check; doctor + installer on Windows |
| Windows/UTF-8 friction (P8) | Phase 1: Harness Foundation | Test matrix; Vietnamese fixture in verify |
| Markdown-only SRS drift (P3) | Phase 2: REQ-ID Spine & SRS Pair | Gate N-2; render-only SRS.md |
| Unreadable source / fake citations (P9) | Phase 2: REQ-ID Spine | AC-BRD-007-02; messy-source pilot UCs |
| LLM gate bypass (P1) | Phase 3: Executable Runner & Conductor | AC-BRD-027-01/02; journal audit |
| Candidate as canonical (P5) | Phase 3: Executable Runner & Conductor | Promotion atomicity tests |
| Ceremony sneak-back (P7) | Phase 4: Golden Path Artifacts | light tier command-count regression = 1 |
| False-green RTM (P2) | Phase 5: Coverage & Drift Detection | AC-BRD-026 suite; conformance corpus |
| Hash = correctness fallacy (P4) | Phase 7: Pilot & Release | UAT rework metric; sign-off on strict |
| Byte-repro LLM mismatch (P12) | Phase 7: Pilot & Release | Stakeholder readout; hash-only regression tests |
| Fake render fallback (P11) | Phase 6: Plugins & Strict Tier | No fallback; DOCX rId gate |
| Team state corruption (P10) | Phase 6: Team Mode | AC-BRD-024-01; filelock recovery |

### Suggested phase ordering rationale

1. **Foundation before skills** — doctor, CLI contract, config portability prevent Windows and doc drift from poisoning everything downstream.
2. **Spine before conductor** — registry + citation gate must exist before `$ba-deliver` orchestrates routes.
3. **Runner before golden path** — gate bypass and candidate/canonical bugs are architectural; bolting runner on later forces rewrite.
4. **Coverage engine before pilot claims** — false-green destroys trust faster than missing mockup plugin.
5. **Plugins and team mode last** — optional complexity; strict deliverables depend on spine + coverage already correct.

## Sources

- `docs/BRD-v1.0.md` — §11 Acceptance Criteria, §13 KPIs, §14 Risks R-1…R-12, §15 Release gate, Appendix C DoD
- `docs/SRS-SPEC.md` — Part A N-1…N-5 (canonical vs derived SRS)
- `.planning/PROJECT.md` — harness-first positioning, determinism boundary, vertical MVP intent
- HarnessAudit / agent harness safety literature — task completion ≠ safe execution; enforce at tool-call boundary (MEDIUM confidence for generalization to BA domain)
- Atlan agent harness anti-patterns — silent failures, stale context, "looks done" outputs (MEDIUM confidence)
- Capability gates ≠ authorization — per-call deterministic enforcement before side effects (HIGH confidence for ba-tools design alignment)

---
*Pitfalls research for: ba-daily-ops (BA Daily Ops)*
*Researched: 2026-07-20*
