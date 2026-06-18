---
operator: ba-mermaid
default_route: author
routes:
  - author
  - render
  - full
---

# ba-mermaid Workflow

Turn a use case or requirement into a Mermaid diagram authored as an inline
` ```mermaid ` block in `.ba-ops/mermaid/<slug>/diagram.md`, with YAML
frontmatter `req_ids` citing the depicted REQ-IDs.

**Determinism boundary:** `ba-tools` commands do ONLY file/command/hash-provable
work. All diagram-type selection, REQ-ID subset selection, and diagram authoring
is agent-owned. The CLI never calls an LLM.

**Sequential execution:** This is a Codex v1 operator — there is no autonomous
parallel subagent spawn. Each step runs sequentially; each step must complete
before the next begins.

**Pass paths, not content:** The workflow hands the agent the slug and
`requirements.json` path. The agent reads the file and writes the diagram `.md`.

---

## Route: author

Write the inline ` ```mermaid ` diagram `.md` artifact only. No CLI invocation, no trace write.

**Steps:**

1. Run `ba-tools resolve-route ba-mermaid` to confirm default route = `author`.
2. Run `ba-tools init ba-mermaid` for scaffold context.
3. Open `.agents/ba-daily-operators/ba-core/agents/ba-diagrammer.md` and follow
   the diagrammer role contract.
4. Pass this payload (paths only):
   ```
   requirements_json: .ba-ops/srs/<slug>/requirements.json
   slug:              <slug>
   diagram_type:      <optional --diagram-type override, or agent-chosen>
   route:             author
   ```
5. The diagrammer writes `.ba-ops/mermaid/<slug>/diagram.md` with YAML frontmatter
   + inline ` ```mermaid ` block.

**Output:** `.ba-ops/mermaid/<slug>/diagram.md`

---

## Route: full

End-to-end: author → trace write → index update.

**Steps:**

### Step 1 — Author diagram

Follow the **author route** steps above.

### Step 2 — Trace write

Read the `req_ids:` list from the YAML frontmatter of `.ba-ops/mermaid/<slug>/diagram.md`.

Run:
```
ba-tools trace write \
  --kind mermaid \
  --slug <slug> \
  --artifact .ba-ops/mermaid/<slug>/diagram.md \
  --source-doc .ba-ops/srs/<slug>/requirements.json \
  --requirements .ba-ops/srs/<slug>/requirements.json \
  --req-ids <comma-separated req_ids from frontmatter>
```

Note: `--source-doc` is the SRS `requirements.json` — not the diagram `.md` itself.
This records `source_hash` = SHA-256 of the requirements current when the diagram was
authored, enabling drift detection (D-06). The diagram `.md` is passed as `--artifact`.

### Step 3 — Index update

Run `ba-tools index update`
(populates INDEX.md mermaid column; flags orphans if any REQ-ID from the trace record
is absent from `requirements.json`).

**Output:** `diagram.md` + trace record `.ba-ops/traces/mermaid-<slug>.json` + updated `INDEX.md`

---

## Route: render

Export-only: run `ba-tools mermaid-render` from an existing `diagram.md`.
Never auto-invoked by `author` or `full`. Hard-fails exit 2 when `mmdc` is absent.

**Steps:**

1. Confirm `.ba-ops/mermaid/<slug>/diagram.md` exists (the `author` route must have
   run first).
2. Run:
   ```
   ba-tools mermaid-render --slug <slug> \
     --artifact .ba-ops/mermaid/<slug>/diagram.md \
     --format svg
   ```
3. On exit 2 with `NO_MERMAID_CLI`: install `mmdc`
   (`npm install -g @mermaid-js/mermaid-cli`) and retry.
   Do NOT generate a synthetic image.

**Output:** `.ba-ops/mermaid/<slug>/diagram.mmd` + `diagram.svg` (or `.png`)
