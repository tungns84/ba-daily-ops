---
phase: BAOPS-01
slug: harness-foundation
status: draft
surface: terminal
shadcn_initialized: false
preset: none
created: 2026-07-21
---

# Phase BAOPS-01 — UI Design Contract

> Visual and interaction contract for the Phase 1 terminal surfaces: PowerShell/POSIX installers, generated repo-root launchers, `ba-tools` structured output, diagnostics, consent, and safe initialization. No web or graphical frontend is in scope.

---

## Scope and Surface Model

| Surface | Audience | Rendering contract |
|---------|----------|--------------------|
| `install.ps1` / `install.sh` | Human BA or operator | Plain terminal prose, ordered stage labels, one explicit network-consent prompt, OS-specific remediation |
| `.\ba-tools.ps1` / `./ba-tools` | Human and automation | Transparent argument/stream forwarding; structured fallback error only when the local runtime cannot start |
| `ba-tools` CLI | Automation first; human-inspectable | Exactly one compact UTF-8 JSON object on one stream; no banners, progress animation, ANSI, logs, or traceback |
| `doctor` diagnostics | Human and automation | Stable ordered check collection using `pass`, `warning`, `fail`, and `skipped`, with actionable remediation |
| `init` / `init --repair` | Human and automation | Explicit state transition result; no inferred business content and no overwrite prompt because overwrite is forbidden |

The installer is the only interactive and potentially network-capable surface. The runtime CLI never prompts and remains zero-network. Generated launchers do not modify `PATH`, activate a shell environment, clear the terminal, or add presentation around the CLI response.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | None — terminal-native contract |
| Preset | Not applicable |
| Component library | None |
| Icon library | None; use ASCII labels such as `[1/4]`, `[WARN]`, and `[FAIL]` only in installer prose |
| Font | Host terminal monospace; the product must not install, select, or assume a font |
| Styling | Progressive ANSI color in the interactive installer only; no ANSI in JSON or non-TTY output |

No React, Next.js, Vite, Tailwind, `components.json`, or existing UI source was found. The shadcn initialization gate is therefore not applicable.

---

## Spacing Scale

The declared 4-point scale is nominal. Terminal adapters map one 4px unit to one character cell; they never attempt pixel positioning.

| Token | Value | Terminal equivalent | Usage |
|-------|-------|---------------------|-------|
| xs | 4px | 1 column | Space between a stage marker and its label |
| sm | 8px | 2 columns | Installer continuation indent |
| md | 16px | 4 columns | Remediation line indent; maximum nesting depth |
| lg | 24px | 6 columns | Reserved; not used in Phase 1 terminal output |
| xl | 32px | 8 columns | Reserved; not used in Phase 1 terminal output |
| 2xl | 48px | 12 columns | Reserved; not used in Phase 1 terminal output |
| 3xl | 64px | 16 columns | Reserved; not used in Phase 1 terminal output |

Exceptions:

- `ba-tools` JSON uses compact separators, no indentation, no leading/trailing spaces, and exactly one trailing LF.
- Installer output uses at most one blank line between the prerequisite summary, consent prompt, and final result.
- Do not center text, draw boxes, or align columns with padding; paths and translated text make such layouts brittle.
- Human prose may wrap naturally at the host width. JSON bytes remain one physical line even when the terminal visually wraps them.

---

## Typography

These are exact semantic tokens for documentation and snapshot review. A terminal implementation inherits the host size and expresses hierarchy structurally; it must not emit font-control sequences. Exactly two weights are permitted: regular `400` and semibold `600`.

| Role | Nominal Size | Weight | Line Height | Terminal expression |
|------|--------------|--------|-------------|---------------------|
| Machine JSON | 12px | 400 | 1.0 | One unstyled physical line |
| Installer body | 14px | 400 | 1.5 | Plain sentence on its own line |
| Prompt label | 16px | 600 | 1.2 | Complete question followed by `[y/N]` |
| Installer heading/result | 20px | 600 | 1.2 | Short line such as `BA Tools installer` or `BA Tools is ready.` |

Semibold is a semantic intent, not a requirement to force terminal bold. Plain-text fallbacks use line isolation and labels rather than ANSI weight.

---

## Color

The 60/30/10 split applies only to an interactive installer on a positively detected ANSI-capable TTY. Values are reference colors; the host theme remains authoritative.

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | Host background; dark reference `#0C0C0C` | Unmodified terminal background |
| Secondary (30%) | Host foreground; dark reference `#CCCCCC` | Headings, stage copy, remediation, and success text |
| Accent (10%) | ANSI bright blue; reference `#3B82F6` | Installer stage markers and the `[y/N]` consent token only |
| Destructive | ANSI bright red; reference `#EF4444` | `[FAIL]` on fatal installer errors only |

Accent reserved for: installer stage markers and the network-consent choice token. It is not used for every command, path, or interactive element.

Color rules:

- Never emit ANSI from `ba-tools`, generated launcher fallback JSON, redirected output, CI, or when `NO_COLOR` is present.
- Color is never the only status cue; `[WARN]`, `[FAIL]`, and the JSON `status` value carry the meaning.
- Do not force a background color. If ANSI capability is uncertain, use plain text.

---

## Copywriting Contract

CLI flags, JSON keys, error codes, and status values are stable English tokens. Human messages use concise English in Phase 1; user-provided Vietnamese text and paths remain UTF-8 and must not be ASCII-escaped.

| Element | Exact copy |
|---------|------------|
| Primary CTA | `Run doctor` |
| Installer heading | `BA Tools installer` |
| Installer success | `BA Tools is ready.` |
| Windows next action | `Next: .\ba-tools.ps1 doctor` |
| POSIX next action | `Next: ./ba-tools doctor` |
| Empty state heading | `No business goals are configured.` |
| Empty state body | `The empty registry is valid; initialization does not infer or create sample goals.` |
| Generic error state | `BA Tools could not complete the command. Retry after checking the reported diagnostic code.` |
| Existing invalid state | `Existing state is invalid and was preserved.` |
| Invalid-state remediation | `Correct the reported fields, then retry.` |
| Partial-state remediation | `Required workspace files are missing. Run init --repair to create missing files only.` |
| Lock timeout | `Another workspace writer did not finish in time.` |
| Lock remediation | `Retry after the other ba-tools command completes.` |
| Destructive confirmation | Not applicable in Phase 1: `init` and `init --repair` never replace an existing canonical file |

### Network Consent

Use this prompt immediately before the first network-capable dependency operation:

`Download and install locked project dependencies? This requires network access. [y/N]`

Interaction rules:

- Default is **No**. Accept case-insensitive `y` or `yes`; accept `n`, `no`, empty input, or EOF as refusal.
- For any other interactive input, print `Enter y or n.` and ask again.
- Refusal copy: `Installation cancelled before network access. No launcher or active environment was changed.`
- In non-interactive mode, never wait for input. Fail before network access with: `Network consent is required. Re-run with --yes or provide an offline wheelhouse.`
- `--yes` is explicit consent for this installer invocation only; it is not persisted.
- An approved offline wheelhouse requires no network prompt.

### Prerequisite and Failure Copy

| Condition | Message | Required next-step form |
|-----------|---------|-------------------------|
| Python missing/old | `Python 3.11 or newer is required.` | Name the OS-specific official installation route, then say `Rerun the installer after Python is available.` |
| Git missing | `Git is required.` | Name the OS-specific official installation route, then say `Rerun the installer after Git is available.` |
| Runtime not activated | `The project-local BA Tools runtime is not ready.` | `Rerun the repository installer, then retry this command.` |
| Path rejected | `The requested path is outside the repository or uses a disallowed form.` | `Use a repository-relative POSIX path without .., a drive, UNC prefix, or backslashes.` |
| Unexpected CLI failure | `BA Tools could not complete the command.` | `Retry after checking the reported diagnostic code.` |

Messages must not include traceback text, secrets, environment dumps, home directories, or absolute repository paths.

---

## Interaction Contract

### Installer Stages

The interactive installer reports these four stages in order and does not show percentage or time estimates:

1. `[1/4] Checking prerequisites`
2. `[2/4] Preparing the project-local environment`
3. `[3/4] Installing locked dependencies`
4. `[4/4] Verifying the repo-root launcher`

A stage that does not apply is reported as `[SKIP] <stage>: <reason>`. A failed stage is reported as `[FAIL] <stage>: <problem>`, followed by exactly one indented `Next: <action>` line. The installer must verify the new environment before switching the active pointer or reporting success.

### CLI Stream and Envelope

- Success, including a `doctor` result whose highest severity is `warning`: exit `0`, exactly one JSON object on stdout, stderr empty.
- Failure, including a core `doctor` failure: exit `2`, stdout empty, exactly one JSON error object on stderr.
- The single-emission rule applies to no arguments, `--help`, `--version`, invalid options, unknown commands, expected failures, keyboard interruption, and unexpected failures.
- Serialize compact UTF-8 with `ensure_ascii=false`, no BOM, no ANSI, no logging prefix, deterministic key/list ordering, and one trailing LF.
- Runtime warning summaries use the top-level `warnings` array; `doctor` check details use `data.checks`. They are never additional terminal prose.

Success envelope:

`{"schema_version":1,"ok":true,"command":"<command>","data":{...},"warnings":[]}`

Error envelope:

`{"schema_version":1,"ok":false,"command":"<command>","error":{"code":"<STABLE_CODE>","message":"<problem>","details":[],"remediation":["<next action>"]}}`

The semantic top-level fields are fixed. Consumers must parse by key rather than rely on visual key order.

### Doctor Diagnostics

Each check has a stable `id`, `status`, `summary`, `observed`, and `remediation` array. A skipped check also names the failed prerequisite IDs. Checks remain in registry order across platforms.

| Status | Meaning | Overall effect |
|--------|---------|----------------|
| `pass` | Required fact was observed | No severity increase |
| `warning` | Optional, disabled-plugin dependency is unavailable or a recoverable condition exists | Overall `warning`, exit `0` |
| `fail` | Core/current-profile requirement is unavailable or invalid | Overall `fail`, exit `2` |
| `skipped` | The check cannot run because a declared prerequisite failed | Does not hide the prerequisite failure |

Independent checks continue after a failure. No check, observed value, or remediation may be truncated, collapsed into a count, or hidden behind a verbose flag. `doctor --all` adds every known optional check using the same schema.

### Initialization States

| State | Command response | Mutation rule |
|-------|------------------|---------------|
| Fresh | Success with `changed: true` and all created repo-relative paths | Create minimal valid `.ba-ops/` state |
| Complete and valid | Success with `changed: false` and an empty created list | Write zero bytes and preserve mtimes |
| Partial + plain `init` | `STATE_INCOMPLETE` error with `init --repair` remediation | Write zero bytes |
| Partial + `init --repair` | Success with `changed: true` and only missing paths listed | Create missing files only |
| Any existing invalid JSON | `STATE_SCHEMA_INVALID` with all stable, field-addressed diagnostics | Preserve every existing byte; create nothing |
| Lock wait timeout | `WORKSPACE_LOCK_TIMEOUT` with retry remediation | Write zero bytes |
| Abandoned atomic temp found | Preserve canonical, quarantine temp, and report its repo-relative quarantine identity | Never promote automatically |

`business-goals.json` contains `business_goals: []` inside its versioned object. This is a valid populated file containing an intentionally empty collection, not a failure or a prompt to infer sample content.

### Launcher Behavior

- Preserve every user argument and the child process exit code.
- Forward stdout/stderr without banners, activation messages, path echoes, or formatting.
- Resolve from the launcher's own directory; invocation CWD does not change the repo root.
- If the runtime cannot be started, emit one compact UTF-8 `LAUNCHER_NOT_READY` error envelope to stderr and exit `2`.
- Show only repo-relative paths in errors. Never reveal the resolved interpreter, home directory, or active-environment absolute path.

---

## Terminal Accessibility and Portability

- Status is always conveyed by words/codes, never color or cursor position.
- Do not clear the screen, redraw lines, animate a spinner, ring the terminal bell, or require a mouse.
- Keep installer prose understandable in source order for screen readers.
- Put the complete consent question before the input cursor; default-No is visible as `[y/N]`.
- Do not use Unicode box drawing, emoji, or ambiguous single-glyph icons. Vietnamese content remains valid Unicode.
- Target readable prose at 80 columns, but never truncate or ellipsize commands, diagnostic text, JSON, or paths. Let the host wrap.
- Quote commands containing paths in OS-specific remediation examples. Never insert a line break inside a command token.
- PowerShell and POSIX installers use equivalent stage names, consent semantics, error meaning, and next-step ordering.
- Ctrl+C or EOF during installation leaves the active launcher/environment unchanged and returns a non-zero result.

---

## UI Considerations

Applicable state considerations resolved: **8 covered, 0 backstop, 0 unresolved**.

| Category | Element(s) | Status | Resolution / Reason |
|----------|------------|--------|---------------------|
| empty | `business_goals` list collection | ✅ covered | The Copywriting Contract defines the intentional empty-state meaning; canonical JSON uses `business_goals: []` without sample data |
| loading | installer form; CLI command | ✅ covered | Installer shows four ordered stages; synchronous `ba-tools` stays silent until its single final JSON emission and never uses a spinner |
| error | installer, launcher, CLI | ✅ covered | The Copywriting Contract and stream rules require a problem plus next action, stable code, safe details, and no traceback/absolute path |
| populated | `doctor` check collection | ✅ covered | Every applicable check is emitted in stable registry order with status, observed value, and remediation |
| partial | `doctor` checks; `.ba-ops/` state | ✅ covered | Dependency-blocked checks are `skipped`; partial init fails without mutation and points to explicit repair |
| overflow | diagnostics and JSON static content | ✅ covered | No truncation, pagination, ellipsis, or fixed table width; host visual wrapping does not alter bytes |
| zero-one-many | warnings, checks, details, remediation arrays | ✅ covered | Arrays remain arrays at every cardinality; machine consumers do not depend on singular/plural prose |
| long-text | messages, paths, help, observed values | ✅ covered | Preserve full UTF-8 content, use repo-relative paths, natural wrap, and no semantic truncation |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | None | Not applicable — no React-family stack and no `components.json`; repository scan passed 2026-07-21 |
| Third-party UI registries | None | No registry content declared or permitted for this phase; verified 2026-07-21 |

Python package legitimacy is a separate dependency-supply-chain checkpoint in `01-RESEARCH.md`; it is not a UI registry approval.

---

## Source Traceability

| Source | Contract decisions used |
|--------|-------------------------|
| `01-CONTEXT.md` | D-01–D-19: project-local install, root launchers, explicit consent, doctor severity, safe init/repair, lock/recovery behavior |
| `REQUIREMENTS.md` | FOUND-01–FOUND-06 and NFR-02–NFR-05: stream contract, diagnostics, portability, file-state, containment, crash safety, UTF-8, zero-network |
| `01-RESEARCH.md` | Single JSON gateway, deterministic envelopes, four doctor statuses, compact serialization, launcher and installer boundaries |
| `ROADMAP.md` | Phase goal and five success criteria |
| User phase objective | Terminal-first scope; no invented web or graphical frontend |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
