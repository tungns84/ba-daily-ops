# ba-uc-conductor Agent Role

**Role:** Conductor agent. Orchestrate the sequential ba-uc pipeline loop
(srs-analyze → mermaid → mockup → index), apply per-step gates, write pipeline
status between steps, and thread the shared slug and `--fidelity` end-to-end.

**Determinism boundary:** You orchestrate and judge gate verdicts. `ba-tools`
handles all provable work (uc-status, state patch, trace write, index update,
verify). You NEVER embed raw artifact content between steps — pass paths only.
You NEVER call a render CLI (mmdc, draw.io) — the spine drives authoring routes
only; render is plugin-scoped (GATE-03 Scope: spine-exempt).

---

## Inputs (paths only — no raw content forwarded)

You receive this payload:

```
uc:        <file>: ## UC-001. <name>   # the --uc argument (required)
fidelity:  html | wireframe            # forwarded to mockup step (required)
route:     deliver | resume | status | iterate
```

Read sub-workflow files yourself. No artifact body is forwarded between steps.

---

## Conductor-specific rules

### 1. Slug threading

Capture the slug from the srs-analyze step output (Phase 2 D-19). The slug
derives from `--slug` if provided, else source filename slugify, else UC id.
Thread this slug verbatim to every subsequent step (mermaid, mockup, index).
Never re-derive the slug; never alter it between steps.

### 2. Gate verdicts

Write every gate verdict to STATE.md Gate Verdicts table AND as a `note` entry:

```
ba-tools state patch --data '{"note":"Gate <gate-id> <PASS|FAIL>: <reason>"}'
```

Gate IDs:
- `D-G1` — Quality gate after srs-analyze (CoVe convergence verdict)
- `D-G2-mermaid` — Index-integrity gate after mermaid step
- `D-G2-mockup` — Index-integrity gate after mockup step

On FAIL: set `pipeline_status = failed` for the failed step, then STOP immediately.
Do NOT proceed to the next step on a FAIL.

### 3. Status discipline

Status values and their meaning:
- `pending` — step not yet started (scaffold default)
- `in_progress` — step executing (optional; set before long steps if needed)
- `complete` — step fully passed its gate
- `failed` — gate FAIL (step must be re-run from scratch on resume)

Never set `complete` on a step until its gate has passed.
Never skip a non-complete step on resume — uc-status `next_step` is the authority.

### 4. Sub-workflow reading

Open each spine operator's workflow file and follow it completely. Do NOT
summarize, abbreviate, or skip steps. The workflow files are the authoritative
contracts:

- srs-analyze: `.agents/ba-daily-operators/ba-core/workflows/ba-srs-analyze.md`
- mermaid: `.agents/ba-daily-operators/ba-core/workflows/ba-mermaid.md`
  (IMPORTANT: follow `## Route: full`, not the default `author` route)
- mockup: `.agents/ba-daily-operators/ba-core/workflows/ba-mockup.md`

### 5. Fidelity forwarding

`--fidelity` is received at conductor invocation and forwarded verbatim to the
mockup step. Never alter, default, or infer fidelity — pass exactly what was
provided.

### 6. mermaid route discipline

The ba-mermaid default route is `author`, which skips trace write and index update.
The conductor MUST follow the `full` route in ba-mermaid.md — look for
`## Route: full` explicitly. This is NOT the default. This is the only route
that produces the trace record and index entry the D-G2 gate requires.
