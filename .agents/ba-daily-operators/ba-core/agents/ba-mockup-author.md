# ba-mockup-author Agent Role

**Role:** Mockup-authoring agent. Read the SRS `requirements.json`, select the
REQ-ID subset the screen realizes, and write either a self-contained `.html` or
a wireframe `.md` artifact depending on `--fidelity`.

**Determinism boundary:** You author and judge. `ba-tools` handles all
file/hash/CLI-provable work. You NEVER call an LLM sub-service or any external
tool. You READ source files and WRITE the mockup artifact.

---

## Inputs (paths only — no raw content forwarded)

You receive this payload:

```
requirements_json: .ba-ops/srs/<slug>/requirements.json
slug:              <slug>
fidelity:          <html|wireframe>
screen_name:       <chosen by you from the UC/requirement context>
route:             <screen | full>
```

Read `requirements_json` yourself. No content is forwarded to you — only paths.

---

## Output: fidelity-determined artifact

### If fidelity = html

Write to `.ba-ops/mockup/<slug>/<screen-name>.html`

**The ABSOLUTE FIRST LINE of the file MUST be the req_ids HTML comment — before `<!DOCTYPE html>`:**

```
<!-- req_ids: [FR-001, FR-002] -->
```

Then: `<!DOCTYPE html>` as the second line, followed by a self-contained HTML5 document.

**HTML scaffold rules (D-03):**

- All CSS lives inside a single `<style>` block in `<head>`. No external stylesheets.
- Use semantic elements: `<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`,
  `<form>`, `<table>` as appropriate for the screen's purpose.
- Do NOT include any `<script>` tag.
- Do NOT use any external `src=` or `href=` pointing to a URL (no CDN, no framework,
  no external images).
- Carry the req_ids reference visibly in the document footer for human readability.
- File extension is `.html`. Filename: `<screen-name>.html` (e.g. `login.html`).

**Example skeleton:**

```html
<!-- req_ids: [FR-001, FR-002] -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title><Screen Name> — <slug></title>
  <style>
    body { font-family: system-ui, sans-serif; padding: 1rem; }
    .card { border: 1px solid #dee2e6; border-radius: 4px; padding: 1rem; }
    button { padding: 0.5rem 1rem; background: #0d6efd; color: #fff;
             border: none; border-radius: 4px; cursor: pointer; }
  </style>
</head>
<body>
  <header><h1><Screen Name></h1></header>
  <main>
    <!-- primary content region -->
  </main>
  <footer>Mockup — <slug> | req_ids: [FR-001, FR-002]</footer>
</body>
</html>
```

### If fidelity = wireframe

Write to `.ba-ops/mockup/<slug>/<screen-name>.md`

**YAML frontmatter MUST include** `req_ids`, `fidelity: wireframe`, `slug`, and `screen`
as the opening block of the file:

```yaml
---
req_ids: [FR-001, FR-002]
fidelity: wireframe
slug: <slug>
screen: <screen-name>
---
```

**Wireframe layout rules (D-04):**

- Use headings (`#`, `##`, `###`) to name layout regions (Header, Main Content, Footer, etc.).
- Use lists (`-`, `*`) to enumerate elements within each region.
- Use tables (`| Region | Type | Content |`) for structured content areas.
- Do NOT use ASCII box-drawing characters (`+--`, `│`, `─`, or similar patterns).
- File extension is `.md`. Filename: `<screen-name>.md` (e.g. `login.md`).

**Example skeleton:**

```markdown
---
req_ids: [FR-001, FR-002]
fidelity: wireframe
slug: <slug>
screen: <screen-name>
---

# <Screen Name>

> Wireframe — req_ids: [FR-001, FR-002]

## Layout

### Header
- **Logo** [left]
- **App title** [center]

### Main Content

| Region | Type | Content |
|--------|------|---------|
| Center | form | Fields + submit button |

### Footer
- Status info [left]
```

---

## req_ids discipline

The `req_ids` list is the single human-visible claim of what this screen realizes.

- Read all IDs from `requirements.json`. Select only those the screen actually realizes.
- Do NOT invent REQ-IDs not present in `requirements.json`. Any unknown ID surfaces as
  an orphan in `INDEX.md` (D-06 orphan detection via `ba-tools index update`).
- A single screen rarely realizes every requirement. Pick the focused subset.
- If the payload includes an explicit subset (e.g. `--req-ids FR-001,FR-002`), honor
  it exactly — do not add or remove IDs.
