# Quality Gate Contract — ba-srs-analyze

This document defines the authoritative gate contract for the ba-srs-analyze
operator. It governs the sequence of verification steps, escalation protocol,
and non-blocking WARN semantics.

---

## Gate sequence

```
ba-tools verify → ba-critic CoVe loop (≤3) → trace write + index update
```

Each gate must pass before the next runs. On convergence, the trace write and
index update execute. On non-convergence after loop 3, the workflow escalates
to human confirmation.

---

## Gate 1: ba-tools verify (hard gate)

**Command:** `ba-tools verify --reqs <path> --reqs-format json --source <path>`

**What it checks:**
- Every requirement with `status: "stated"` has a `source_trace.span` that
  appears verbatim (≥12 chars) in the cited source section.
- `source_trace.section` scopes the citation search. Empty string = document scope.
- Span shorter than 12 characters fails regardless of content.

**Pass:** Exit code 0. JSON envelope `{"ok": true, "failures": []}`.

**Fail:** Exit code 2. JSON envelope `{"ok": false, "failures": [...]}` where
each entry has `code` (e.g. `CITATION_NOT_FOUND`) and `req_id`.

**Blocking semantics:** Exit 2 = hard block. The CoVe loop does NOT start until
verify passes. Fold failures back to ba-srs-writer for re-draft, then re-verify.

**Note:** `derived` requirements are not checked by verify (no verbatim span
required). Only `stated` requirements are gated.

---

## Gate 2: ba-critic CoVe loop (≤3 iterations)

**Agent:** `.agents/ba-daily-operators/ba-core/agents/ba-critic.md`

**Payload to critic (paths only):**
```
source_path:            <path to source document>
requirements_json_path: <path to requirements.json>
```

Critic receives ONLY these two paths. `analysis.md`, `SRS.md`, and writer
working notes are NEVER passed to the critic (independence constraint, D-21).

**Critic emits:** JSON findings `{converged, findings[{req_id, severity, question, answer, verdict}]}`

**Convergence rule:** `converged = true` iff zero new `fail`-severity findings.
WARN findings are non-blocking.

**Loop protocol:**

```
n = 1
while n <= 3:
    run ba-critic(source_path, requirements_json_path)
    if converged:
        log "passed early"    # if n == 1
        log "passed after <n>" # if n > 1
        break → Gate 3
    if n < 3:
        pass FAIL findings to ba-srs-writer for re-draft
        re-run ba-tools verify; if exit 2, fold failures into re-draft
        n += 1
    else:
        log "non-convergence-escalation"
        run ba-tools confirm
        STOP — surface open FAILs to user
        do NOT proceed to Gate 3
```

**Loop is sequential.** Writer and critic NEVER run concurrently. This is a
single sequential agent loop (Codex v1 constraint).

**Convergence vocabulary (logged to STATE.md):**

| Log value | Meaning |
|-----------|---------|
| `passed early` | Converged on loop 1 — no revisions needed |
| `passed after <n>` | Converged on loop n (n > 1) — required n-1 revisions |
| `non-convergence-escalation` | Loop 3 still has FAIL findings — human required |

---

## Gate 3: trace write + index update (convergence only)

Only runs if Gate 2 converged.

**Commands:**

```
ba-tools trace write --kind srs --slug <slug>
    --artifact .ba-ops/srs/<slug>/SRS.md
    --source <source_path>
    --req-ids .ba-ops/srs/<slug>/requirements.json

ba-tools index update

ba-tools state advance
```

`state advance` is lockfile-guarded (FileLock timeout=10) per D-01/D-02.

**What these do:**
- `trace write` — records hash-provable link between source, requirements.json,
  and SRS.md in the trace registry.
- `index update` — rebuilds INDEX.md with gap/orphan/stale detection (D-13).
- `state advance` — records gate verdict in STATE.md.

**Hard rule:** Never invoke Gate 3 with open FAIL findings. Trace write on an
unverified requirements set creates a false provenance record.

---

## WARN semantics

WARN findings from ba-critic are advisory and non-blocking:
- Log WARN findings to analysis.md and STATE.md.
- Do NOT re-run the CoVe loop for WARN-only convergence.
- Do NOT gate trace write on WARN findings.
- Surface WARN findings to the BA as part of the completion output.

Examples of WARN findings: non-atomic statements, misclassified prefix,
weak wording, minor completeness suggestions.

---

## Escalation protocol

Triggered when CoVe loop 3 completes with `converged: false`.

1. Run `ba-tools confirm` to surface the situation.
2. Present the user with: open FAIL findings list, req_id, and verdict for each.
3. STOP. Do not write traces, update index, or advance state.
4. Resume instructions for the human:
   - Review the FAIL findings.
   - Either edit `requirements.json` manually to address the findings, or
     provide new guidance to ba-srs-writer.
   - Re-run the `iterate` route to re-enter the gate sequence.

---

## Prohibition summary

| Prohibition | Rule |
|-------------|------|
| Never pass `analysis.md` to ba-critic | D-21 / G3 |
| Never start CoVe loop before verify passes | Gate sequence |
| Never emit `converged: true` with open FAILs | G2 |
| Never write traces on unverified requirements | Gate 3 guard |
| Never run writer and critic concurrently | Codex v1 sequential |
| Never auto-proceed after loop 3 non-convergence | Escalation rule |

---

## Safety Gate Contract

**Scope:** Plugin-enforced. The spine (`ba-srs-analyze`, `ba-mermaid`, `ba-mockup`,
`ba-uc`) invokes no render CLI; therefore the conductor **never fires the Safety gate**.
This contract governs the deferred plugins: `ba-make-diagram`, `ba-uc-delivery`.

**Phase-5 status:** Contract defined. Enforcement deferred to plugin implementation
(PLUG-01..04). The spine is exempt.

---

### Clause 1 — Render CLI only

Any render/export step must invoke a real CLI:

```
draw.io -x -f png -o <output>
mmdc -i <file> -o <file>
```

No Pillow, no SVG-converter, no screenshot, no hand-pasted image. Synthetic render
is forbidden regardless of visual fidelity. (DESIGN §6, §11.)

### Clause 2 — Path-traversal and injection scan

Before any `.ba-ops/` write triggered by a plugin, validate all paths via
`resolve_under_root` + `is_within_root` (repo.py). Any path passed to a render
CLI must resolve under `--repo-root`. Advisory injection scan runs via:

```
ba-tools scan --file <artifact>
```

(TOOL-15, always advisory, always exit 0 — see WARN semantics above.)

### Clause 3 — Media extension check

A rendered media file must carry extension `.png` or `.svg` (raster/vector). For
export-only artifacts, `.pdf` is also valid. No other extension is acceptable for
embedded media. Plugins must reject writes with non-conforming extensions at write
time before any `.ba-ops/` state update.

### Clause 4 — Hash manifest (PLUG-04, deferred)

The render step writes a manifest JSON:

```json
{"rendered_sha256": "<hash>", "embedded_sha256": "<hash>"}
```

Pass condition: `rendered_sha256 == embedded_sha256`. A mismatch indicates the
embedded media was not the file the CLI produced. This clause is enforced only
when PLUG-04 is implemented — not this phase.

---

## Safety Gate — Prohibition summary

| Prohibition | Rule |
|-------------|------|
| Never use Pillow/SVG-converter/screenshot for render | DESIGN §6/§11 |
| Never write media with extension outside .png/.svg/.pdf | Clause 3 |
| Never pass paths outside --repo-root to a render CLI | Clause 2 |
| Never fire Safety gate from the spine | Scope marker |
