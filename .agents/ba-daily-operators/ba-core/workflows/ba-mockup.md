---
operator: ba-mockup
default_route: full
routes:
  - screen
  - full
---

# ba-mockup Workflow

Turn requirements into a UI mockup at `--fidelity html` or `--fidelity wireframe`,
writing the artifact to `.ba-ops/mockup/<slug>/`, with req_ids citing the REQ-IDs
the screen realizes.

**Determinism boundary:** `ba-tools` commands do ONLY file/command/hash-provable
work. All fidelity selection, REQ-ID subset selection, and mockup authoring is
agent-owned. The CLI never calls an LLM.

**Sequential execution:** This is a Codex v1 operator — there is no autonomous
parallel subagent spawn. Each step runs sequentially; each step must complete
before the next begins.

**Pass paths, not content:** The workflow hands the agent the slug and
`requirements.json` path. The agent reads the file and writes the mockup artifact.

---

## Route: screen

Author the mockup artifact only. No CLI invocation, no trace write.

**Steps:**

1. Run `ba-tools resolve-route ba-mockup` to confirm default route = `full`.
2. Validate `--fidelity`: must be `html` or `wireframe`. If absent or invalid, stop
   with error message: "`--fidelity` is required and must be `html` or `wireframe`."
   Do NOT proceed to authoring until a valid fidelity value is provided.
3. Run `ba-tools init ba-mockup` for scaffold context.
4. Open `.agents/ba-daily-operators/ba-core/agents/ba-mockup-author.md` and follow
   the author role contract.
5. Pass this payload (paths only):
   ```
   requirements_json: .ba-ops/srs/<slug>/requirements.json
   slug:              <slug>
   fidelity:          <html|wireframe>
   screen_name:       <chosen by agent from UC/requirement context>
   route:             screen
   ```
6. Agent writes `.ba-ops/mockup/<slug>/<screen-name>.html` (html fidelity) or
              `.ba-ops/mockup/<slug>/<screen-name>.md` (wireframe fidelity).

**Output:** `.ba-ops/mockup/<slug>/<screen-name>.<ext>`

---

## Route: full

End-to-end: author → trace write → index update.

### Step 1 — Author screen

Follow the **screen route** steps above (steps 1–6).

### Step 2 — Extract req_ids

Read the authored artifact.

- **html fidelity:** First line of the file contains `<!-- req_ids: [FR-001, FR-002] -->`.
  Scan the first line for the pattern `<!-- req_ids: [...] -->` and extract the
  bracketed list, split on `,`, strip whitespace.
- **wireframe fidelity:** YAML frontmatter (between `---` delimiters) contains
  `req_ids: [FR-001, FR-002]` as an inline list. Scan the frontmatter block for
  `req_ids: [...]` and extract the bracketed list, split on `,`, strip whitespace.

### Step 3 — Trace write

Run:
```
ba-tools trace write \
  --kind mockup \
  --slug <slug> \
  --artifact .ba-ops/mockup/<slug>/<screen-name>.<ext> \
  --source-doc .ba-ops/srs/<slug>/requirements.json \
  --requirements .ba-ops/srs/<slug>/requirements.json \
  --req-ids <comma-separated req_ids from Step 2>
```

Note: `--source-doc` is the SRS `requirements.json` — NOT the mockup artifact itself.
This records `source_hash` = SHA-256 of the requirements current when the screen was
authored, enabling drift detection (D-06). The mockup artifact is passed as `--artifact`.

### Step 4 — Index update

Run `ba-tools index update`
(populates INDEX.md Mockup column; flags orphans if any REQ-ID from the trace record
is absent from `requirements.json`).

**Output:** `<screen-name>.<ext>` + trace record `.ba-ops/traces/mockup-<slug>.json` + updated `INDEX.md`
