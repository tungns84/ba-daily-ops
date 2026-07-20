# SRS-SPEC

> **Version:** 1.0
> **Date:** 2026-07-20
> **Companion to:** `docs/BRD-v1.0.md` v1.0
> **Product:** `ba-daily-ops`

SRS-SPEC is the **authoring contract** for the SRS artifact pair: canonical `.ba-ops/srs/<slug>/requirements.json` and its deterministic rendered view `.ba-ops/srs/<slug>/SRS.md`. It defines what a valid SRS is, who may author each part, how REQ-IDs and citations are structured, and which gates must pass before handoff. Agents produce requirements through `$ba-srs`; delivery orchestration runs through `$ba-deliver` (with optional upstream `$ba-intake`). Deterministic enforcement is performed by `ba-tools` gates referenced in Parts B–D.

## Part A: Document contract & IEEE 830 profile

### A.0 Header block

| Field | Value |
|-------|-------|
| **Document** | SRS-SPEC — Part A (Document contract & IEEE 830 profile) |
| **Version** | 1.0 |
| **Status** | Normative — Product Contract |
| **Product slug (canonical)** | `ba-daily-ops` |
| **Upstream authority** | `docs/BRD-v1.0.md` — BRD-006 (SRS analyze), BRD-007 (citation-exists), BRD-016 (quality gates), Appendix D (Artifact × Tier matrix), Appendix E (IEEE 830 / ISO 29148 references) |
| **Owning skill** | `$ba-srs` (authoring); `$ba-deliver` (orchestration); `ba-tools render` (deterministic view) |
| **Applies to** | `.ba-ops/srs/<slug>/requirements.json` and its rendered `.ba-ops/srs/<slug>/SRS.md` |
| **Tiers** | `light` \| `standard` \| `strict` (BRD Appendix D) |

**Purpose of SRS-SPEC (Part A).** Tài liệu này là **hợp đồng tác giả** (authoring contract) cho artifact SRS của `ba-daily-ops`. Part A defines *what a valid SRS document looks like*, *who authors each section*, and *how the rendered `SRS.md` must be produced deterministically from `requirements.json`*. Part B specifies the canonical registry schema; Parts C–E cover optional ISO/IEC/IEEE 29148 extensions, workflow, and review checklists.

---

### A.1 Normative hierarchy — one source of truth

The SRS artifact is a **two-file pair** with a strict, non-negotiable ordering of authority (grounded in BRD-006):

1. **`.ba-ops/srs/<slug>/requirements.json` — CANONICAL.** This is the single source of truth for every requirement. Every REQ-ID, statement, status, `source_trace`, and `business_goal` linkage lives here. All downstream artifacts (flow, mockup, backlog, DOCX, INDEX) trace against this file, never against the Markdown.

2. **`.ba-ops/srs/<slug>/SRS.md` — DERIVED VIEW.** This is a **rendered projection** of `requirements.json` produced by the deterministic renderer (`ba-tools render` / `srs_render.py`). It is a read view, comparable to a report — not an editable source.

**Normative rules:**

- **N-1.** The agent (`$ba-srs`) SHALL author requirements **only** into `requirements.json`. Requirement content SHALL NOT be introduced, edited, or invented directly in `SRS.md`.
- **N-2.** `SRS.md` SHALL NOT contain any requirement whose REQ-ID is absent from `requirements.json`. A requirement visible in the Markdown but missing from the registry is a **contract violation**, not merely a lint warning.
- **N-3.** Hand-editing `SRS.md` as a way to change requirements is FORBIDDEN. Any manual edit to `SRS.md` is transient and SHALL be overwritten on the next render. `SRS.md` is regenerable; it MUST NOT be treated as a source of truth (mirrors BRD-003's INDEX rule).
- **N-4.** The prose sections (§1–§2, see A.4) are agent-authored **once into the render inputs** (not free-typed into the rendered file); they too flow through the renderer so that the same inputs reproduce the same bytes.
- **N-5.** Requirement grouping into IEEE-830 §3 subsections is determined **solely by REQ-ID prefix** (`FR-*`, `NFR-*`, `BR-*`, `EI-*`, `CON-*`). The agent controls placement by choosing the prefix in `requirements.json`; the renderer never re-classifies by semantics (determinism boundary, BRD NFR-006).

> **Vì sao phân cấp này cứng?** `requirements.json` là nơi duy nhất mang REQ-ID và citation; `SRS.md` chỉ là bản chiếu. Nếu cho phép sửa yêu cầu trong Markdown, xương sống truy vết REQ-ID (giá trị lõi của sản phẩm) sẽ lệch âm thầm — đúng loại drift mà BRD-004 cấm.

---

### A.2 IEEE 830 section mapping

Each IEEE 830-1998 clause maps to a heading in the rendered `SRS.md`, an authoring owner, and a tier-specific content expectation. **Author** distinguishes *agent-authored analytical content* (judgement — owned by `$ba-srs`) from *CLI-rendered projection* (deterministic — owned by `ba-tools render`). Every listed heading is emitted at every tier; the `light` / `standard` / `strict` columns describe required content depth, not heading presence, and follow BRD Appendix D tiers.

| IEEE 830 clause | `SRS.md` heading | Author | `light` | `standard` | `strict` |
|-----------------|------------------|--------|:-------:|:----------:|:--------:|
| Title / control block | `# Software Requirements Specification: <title>` + Version/Date/Author/Slug | Agent metadata → CLI render | ✓ | ✓ | ✓ |
| 1. Introduction | `## 1. Introduction` | CLI render (container) | ✓ | ✓ | ✓ |
| 1.1 Purpose | `### 1.1 Purpose` | Agent (prose) → CLI render | ✓ | ✓ | ✓ |
| 1.2 Scope | `### 1.2 Scope` | Agent (prose) → CLI render | ○ (may be brief) | ✓ | ✓ |
| 1.3 Definitions | `### 1.3 Definitions` | Agent (prose) → CLI render | ○ | ✓ | ✓ |
| 2. Overall Description | `## 2. Overall Description` | Agent (prose) → CLI render | ○ (may be brief) | ✓ | ✓ |
| (Business context) | `## Business Goals` | CLI render from Business Goals registry | ○ | ✓ | ✓ |
| 3. Specific Requirements | `## 3. Specific Requirements` | CLI render (container) | ✓ | ✓ | ✓ |
| 3.1 Functional (FR-*) | `### 3.1 Functional Requirements` | CLI render from `requirements.json` | ✓ | ✓ | ✓ |
| 3.2 Non-Functional (NFR-*) | `### 3.2 Non-Functional Requirements` | CLI render from `requirements.json` | ○ | ✓ | ✓ |
| 3.3 Business Rules (BR-*) | `### 3.3 Business Rules` | CLI render from `requirements.json` | ○ | ○ | ✓ |
| 3.4 External Interfaces (EI-*) | `### 3.4 External Interfaces` | CLI render from `requirements.json` | ○ | ○ | ✓ |
| 3.5 Constraints (CON-*) | `### 3.5 Constraints` | CLI render from `requirements.json` | ○ | ○ | ✓ |
| 3.6 NFR Coverage | `### 3.6 NFR Coverage` | Agent (checklist) → CLI render | ○ | ○ | ✓ |
| 4. Appendices | `## 4. Appendices` | Agent (optional content) → CLI render | ○ | ○ | ○ |
| 5. Traceability | `## 5. Traceability` | CLI render from registry + trace | ○ | ✓ | ✓ |

**Legend:** `✓` = substantive content required · `○` = content may be brief, empty-with-fallback, or optional to author; the heading is still emitted · Author "→ CLI render" means the agent supplies the content but the deterministic renderer emits the bytes.

**Notes on the profile:**

- **M-1.** **All template headings** — §1, §1.1–§1.3, §2, Business Goals, §3, §3.1–§3.6, §4 Appendices, and §5 Traceability — are always emitted at every tier. A `○` in A.2 permits brief or fallback content only; it never permits heading omission. When content is absent, the renderer emits a stable fallback under the heading instead of deleting it.
- **M-2.** §3.1 (Functional Requirements) is the **irreducible spine** — required at every tier. A `light` SRS with zero FR-* rows is invalid.
- **M-3.** Any REQ-ID whose prefix is not one of `FR-/NFR-/BR-/EI-/CON-` is grouped as *other* by the renderer and appended to the nearest applicable §3 subsection; authors SHOULD prefer the five canonical prefixes so section placement is explicit.
- **M-4.** §3.6 NFR Coverage renders **whatever characteristics the agent supplies** (e.g., an ISO/IEC 25010 mapping) — the renderer does not hardcode or validate the taxonomy (determinism boundary).

---

### A.3 SRS.md template contract — placeholder-by-placeholder

The rendered `SRS.md` is produced by substituting the placeholders in `.agents/ba-daily-operators/ba-tools/ba-core/templates/srs.md`. Substitution uses `string.Template.safe_substitute`: an unresolved `${var}` is left verbatim (never crashes), so **every placeholder below MUST be supplied** to avoid literal `${...}` leaking into a delivered document.

| Placeholder | Source / Author | Required content | Min-length guidance | Brief example | Content @ `light` |
|-------------|-----------------|------------------|---------------------|---------------|--------------------|
| `${title}` | Agent metadata | Human-readable UC/system title | Non-empty; ≤ ~80 chars | `Đăng ký tài khoản người dùng` | Required |
| `${version}` | Registry metadata | SRS version string | Non-empty | `1.0` | Required |
| `${date}` | Registry metadata (NOT wall-clock) | ISO date from `requirements.json` metadata | `YYYY-MM-DD` | `2026-07-20` | Required; see A.6 |
| `${author}` | Registry metadata | Authoring owner / `owner_id` | Non-empty | `alice` | Required |
| `${slug}` | Path / registry | Canonical slug of the UC | Matches folder `<slug>` | `user-registration` | Required |
| `${purpose}` | Agent prose | Why this SRS exists; system under specification | ≥ 2 sentences (~150 chars) | "Đặc tả yêu cầu cho luồng đăng ký… phục vụ dev và QA." | May be 1 grounded sentence |
| `${scope}` | Agent prose | What is in/out of scope for this UC | ≥ 1 in-scope + 1 out-of-scope bullet at `standard`+ | "Trong phạm vi: đăng ký email. Ngoài: SSO." | May be a single line |
| `${definitions}` | Agent prose | Terms/acronyms used in this SRS | Table or list; may be empty-with-fallback | `REQ-ID — mã yêu cầu bền` | Omittable → fallback |
| `${overall_description}` | Agent prose | Product perspective, users, assumptions, high-level context | ≥ 1 paragraph at `standard`+ | "Hệ thống nằm trong…" | May be brief |
| `${business_goals}` | CLI render (Business Goals registry) | Table of goal `id + title` | Rendered table or stable fallback | `\| BG-02 \| Trace REQ-ID \|` | Fallback allowed |
| `${functional_requirements}` | CLI render (FR-* rows) | Markdown table of FR-* requirements | ≥ 1 FR-* row | `\| FR-001 \| Hệ thống PHẢI… \| stated \| BG-02 \|` | **Required (≥1 row)** |
| `${nonfunctional_requirements}` | CLI render (NFR-* rows) | Markdown table of NFR-* requirements | Table or fallback | `\| NFR-001 \| … \| stated \| \|` | Fallback allowed |
| `${business_rules}` | CLI render (BR-* rows) | Markdown table of BR-* requirements | Table or fallback | `\| BR-001 \| … \| stated \| \|` | Fallback allowed |
| `${external_interfaces}` | CLI render (EI-* rows) | Markdown table of EI-* requirements | Table or fallback | `\| EI-001 \| … \| stated \| \|` | Fallback allowed |
| `${constraints}` | CLI render (CON-* rows) | Markdown table of CON-* requirements | Table or fallback | `\| CON-001 \| … \| stated \| \|` | Fallback allowed |
| `${nfr_coverage}` | Agent checklist → CLI render | Characteristic → REQ-IDs (or `N/A + reason`) | Table or fallback | `\| Security \| NFR-009 \|` | Fallback allowed |
| `${appendices}` | Agent (optional) | Supplementary material | Free-form or fallback | "Xem BRD Appendix D." | Fallback allowed |
| `${traceability}` | CLI render (registry + trace) | REQ-ID → downstream artifact mapping | Rendered table or fallback | `\| FR-001 \| SRS,flow,mockup \|` | Fallback allowed |

**Row shape (canonical).** Every requirement row rendered into §3.x uses the fixed 4-column form:

```
| <REQ-ID> | <statement> | <status> | <business_goal> |
```

where `status` defaults to `stated` when absent and `business_goal` is empty when unlinked. Rows are **sorted by REQ-ID (case-insensitive lexicographic)** within each subsection. No other columns are permitted in the standard row.

**T-rules:**

- **T-1.** Empty group → the renderer emits a **stable fallback line** (e.g., "*No requirements in this category.*"), never a broken table or a bare `${placeholder}`.
- **T-2.** A literal `${...}` string appearing in a delivered `SRS.md` is a **defect** — it means an input was not supplied. `strict` delivery SHALL fail if any placeholder leaks.
- **T-3.** The template's section set and heading text are **fixed by this contract**; skills MUST NOT add, remove, or rename `SRS.md` headings out of band. Changing the section set is a versioned change to this SRS-SPEC and to the template together.

---

### A.4 Grounding & authoring rules for §1–§2 prose

Sections §1 (Introduction: Purpose, Scope, Definitions) and §2 (Overall Description) are **agent-authored narrative**. They fall on the *judgement* side of the determinism boundary (`ba-tools` never writes them), so this contract governs **what must be grounded in the source** versus **what may be agent synthesis**.

| Prose element | Grounding requirement | Citation expectation |
|---------------|----------------------|---------------------|
| §1.1 Purpose | MAY be agent synthesis (framing) | No citation required; MUST NOT assert source facts not present |
| §1.2 Scope | In-scope / out-of-scope claims that restate source SHOULD be grounded | Cite source section where scope is stated, when derived from source |
| §1.3 Definitions | Terms taken from source MUST match source usage | Cite source when the definition is quoted/paraphrased from it |
| §2 Overall Description | Factual claims about the system/users MUST be traceable to source or marked as assumption | Cite source for factual claims; label agent inferences as `[Inference]` |

**Normative:**

- **P-1.** Prose SHALL NOT introduce **requirements** — no `SHALL`/`PHẢI` obligations that are not present as a row in `requirements.json`. Requirement-bearing statements belong in §3 (i.e., in the registry), never smuggled into §1–§2 narrative (reinforces N-1/N-2).
- **P-2.** Any **factual claim** about the source domain (numbers, names, behaviours) stated in §1–§2 MUST be either (a) grounded in the source with a citation, or (b) explicitly flagged as an assumption/inference. Ungrounded factual assertions are prohibited.
- **P-3.** Requirement-level grounding remains governed by **BRD-007 (citation-exists)**: every requirement with status `stated` MUST carry a `source_trace` with an exact-substring quote ≥ 12 characters in the declared section. This is enforced on `requirements.json` (Part B), **not** re-checked in prose — but §1–§2 prose MUST NOT contradict a cited requirement.
- **P-4.** Bilingual policy: explanatory prose MAY be Vietnamese (default BA-facing language). Normative obligation words in requirement statements use `SHALL`/`MUST` (English) or `PHẢI`/`KHÔNG ĐƯỢC` (Vietnamese) per BRD §8 convention; a single requirement statement SHOULD be internally consistent in one language.

> **Ranh giới:** §1–§2 là *diễn giải*, không phải *đặc tả nghĩa vụ*. Nghĩa vụ (`PHẢI`) chỉ sống trong `requirements.json` để giữ được citation-exists và trace. Prose có thể tổng hợp/khung hoá, nhưng không được "âm thầm" tạo yêu cầu mới ngoài registry.

---

### A.5 Render determinism

The rendered `SRS.md` is produced by a **pure, deterministic** renderer (`srs_render.py`): no I/O, no model client, no time- or random-based content in requirement rows.

**Guarantees (grounded in `srs_render.py` design contract + BRD NFR-005):**

- **D-1. Byte-identity.** Given the same `requirements.json` (and same business-goals / nfr-checklist inputs, same template, same tool version), rendering SHALL produce a **byte-identical** `SRS.md` on every run and on every supported platform (Windows / macOS / Linux).
- **D-2. Stable ordering.** Requirements SHALL be grouped by REQ-ID prefix and **sorted by REQ-ID (case-insensitive lexicographic)** within each §3 subsection. Ordering SHALL NOT depend on insertion order, dict iteration order, or filesystem order.
- **D-3. No timestamps in requirement rows.** Requirement rows SHALL contain **no** timestamps, UUIDs, run-ids, or any wall-clock/random content. The only date in the document is the header `${date}`, which A.6 requires to come from registry metadata (not `datetime.now()`), so it does not break byte-identity across re-renders of the same registry.
- **D-4. Deterministic fallbacks.** Empty groups and absent optional inputs SHALL render fixed fallback text (see T-1), so structural completeness never depends on data presence.
- **D-5. Safe substitution.** Placeholder substitution uses `safe_substitute`; unknown `${vars}` are preserved verbatim rather than raising — but per T-2 a leaked placeholder is a defect, so callers MUST supply all inputs.
- **D-6. UTF-8.** Output SHALL be UTF-8 with full Vietnamese support; Vietnamese characters SHALL NOT be corrupted or over-escaped (BRD NFR-008).

**Determinism boundary (BRD NFR-006):** the renderer performs **only** provable projection of the registry. It SHALL NOT re-classify requirements semantically, infer MoSCoW, invent goals, or validate the NFR taxonomy. All such judgement is the agent's and is stored as evidence in `requirements.json`.

---

### A.6 Header metadata & determinism reconciliation

Because D-1 requires byte-identity but the template exposes `${date}` / `${version}` / `${author}`, these header fields MUST be **deterministic inputs**, not live values:

- **H-1.** `${date}`, `${version}`, `${author}`, `${slug}`, `${title}` SHALL be read from **fields committed in `requirements.json`** (or derived from the path for `slug`). They SHALL NOT be sourced from the system clock, environment user, or CWD at render time.
- **H-2.** Re-rendering an unchanged `requirements.json` SHALL therefore reproduce an unchanged header — no "last generated at" line, no build timestamp anywhere in `SRS.md`.
- **H-3.** Changing header metadata is a change to `requirements.json` (canonical), consistent with N-1.

---

### A.7 Acceptance Criteria (AC) — Part A reviewer checklist

A reviewer certifies Part A conformance for a given `<slug>` when **all** of the following hold:

**Normative hierarchy**

- [ ] **AC-A-01.** `requirements.json` exists at `.ba-ops/srs/<slug>/` and is the only **authoritative authoring source** for REQ-IDs, statements, statuses, and `source_trace`; `SRS.md` and `INDEX.md` are derived views.
- [ ] **AC-A-02.** Every REQ-ID appearing in `SRS.md` also exists in `requirements.json` (no Markdown-only requirements).
- [ ] **AC-A-03.** No requirement obligation (`SHALL`/`PHẢI`) is authored outside `requirements.json` (e.g., smuggled into §1–§2 prose).

**IEEE 830 profile**

- [ ] **AC-A-04.** At every tier, `SRS.md` contains all template headings §1, §1.1–§1.3, §2, Business Goals, §3, §3.1–§3.6, §4, and §5 in template order. A `○` in A.2 permits brief or fallback content, never omission of the heading.
- [ ] **AC-A-05.** §3.1 Functional Requirements has ≥ 1 FR-* row (spine present at every tier).
- [ ] **AC-A-06.** Requirements appear under the subsection matching their REQ-ID prefix (`FR→3.1`, `NFR→3.2`, `BR→3.3`, `EI→3.4`, `CON→3.5`).
- [ ] **AC-A-07.** Content under each always-present heading meets the active tier's A.2 expectation (`✓` substantive; `○` brief, optional-to-author, or stable fallback).

**Template contract**

- [ ] **AC-A-08.** No literal `${placeholder}` string appears anywhere in the rendered `SRS.md`.
- [ ] **AC-A-09.** Every requirement row uses the 4-column form `| ID | Statement | Status | Goal |`; empty groups show the stable fallback line.
- [ ] **AC-A-10.** `status` defaults to `stated` when absent; `business_goal` cell is empty (not `None`/`null`) when unlinked.

**Prose grounding**

- [ ] **AC-A-11.** Every factual claim in §1–§2 is either cited to source or explicitly marked as assumption/inference.
- [ ] **AC-A-12.** §1–§2 prose does not contradict any cited requirement in `requirements.json`.

**Render determinism**

- [ ] **AC-A-13.** Rendering the same `requirements.json` twice yields **byte-identical** `SRS.md` (diff is empty).
- [ ] **AC-A-14.** No timestamp, UUID, run-id, or random token appears in any requirement row.
- [ ] **AC-A-15.** Header `${date}`/`${version}`/`${author}` derive from registry metadata, not wall-clock/environment (re-render is stable).
- [ ] **AC-A-16.** Output is valid UTF-8 with intact Vietnamese characters.

> **Reviewer note:** AC-A-13 và AC-A-14 là các tiêu chí *chống drift* cốt lõi — nếu render không byte-identical, xương sống truy vết REQ-ID không thể tin cậy khi so hash (BRD-004, NFR-005). Fail bất kỳ AC nào ở trên → SRS chưa đạt hợp đồng Part A và không được coi là handoff-ready.

## Part B: requirements.json canonical schema

### B.1 Schema overview

`requirements.json` is the authoritative requirement registry produced by `$ba-srs`. Rendered SRS Markdown and downstream diagrams, mockups, backlog stories, traces, and indexes may reference this registry but must not invent requirements outside it.

The canonical path for one work item is:

```text
.ba-ops/srs/<slug>/requirements.json
```

All paths stored inside the registry are UTF-8, repository-relative paths resolved from `--repo-root`. Committed artifacts must not contain machine-specific absolute paths.

Two root shapes are accepted:

1. An object containing `requirements`; this is the preferred shape and is required when `nfr_checklist` is present.
2. A plain requirement array.

```json
{"requirements": []}
```

```json
[]
```

The object shape should be used for new registries because it supports additive document-level envelopes without changing the requirement array.

Object-root registries SHOULD include a top-level `metadata` block containing `title`, `version`, `date`, `author`, and `slug` as the deterministic render inputs required by A.6:

```json
{
  "metadata": {
    "title": "Authentication",
    "version": "1.0",
    "date": "2026-07-20",
    "author": "alice",
    "slug": "login"
  },
  "requirements": []
}
```

For a registry rendered as a conforming SRS artifact, all five metadata fields are required envelope fields even though the Draft-07 schema in B.2 does not yet require them. A plain array remains schema-valid, but it cannot independently supply the deterministic header inputs and therefore requires an equivalent deterministic envelope before rendering.

#### Versioning strategy

- The initial contract is identified externally as `urn:ba-daily-ops:schema:requirements:v1`.
- `requirements.json` does not require an inline `schema_version`; the project state version and selected profile come from `.ba-ops/config.json`.
- Additive root or requirement fields may be introduced without changing the root shape. Unknown fields are tolerated unless a definition is explicitly closed.
- `analysis_support` and its nested `confidence` object are closed envelopes; adding, removing, or renaming their keys is a breaking change.
- A breaking root, field, enum, or interpretation change requires a new schema identifier and an explicit migration.
- Schema migration must not silently renumber or reuse REQ-IDs.

### B.2 Draft-07 JSON Schema

The root schema applies to all profiles. For `standard` and `strict`, the validator must additionally apply `#/definitions/standardStrictRoot`, which requires `analysis_support` on every requirement.

Structural validation requires a non-empty `span` for a stated requirement. The stronger minimum length and verbatim-substring rules are enforced by `verify`.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "urn:ba-daily-ops:schema:requirements:v1",
  "title": "BA Daily Ops Requirements Registry",
  "oneOf": [
    {
      "$ref": "#/definitions/requirementsDocument"
    },
    {
      "$ref": "#/definitions/requirementsArray"
    }
  ],
  "definitions": {
    "requirementsDocument": {
      "type": "object",
      "required": [
        "requirements"
      ],
      "properties": {
        "requirements": {
          "$ref": "#/definitions/requirementsArray"
        },
        "nfr_checklist": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/nfrChecklistEntry"
          },
          "default": []
        }
      },
      "additionalProperties": true
    },
    "requirementsArray": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/requirement"
      }
    },
    "requirement": {
      "type": "object",
      "required": [
        "id",
        "statement"
      ],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^(FR|NFR|BR|EI|CON)-[0-9]+$"
        },
        "statement": {
          "type": "string",
          "minLength": 1,
          "pattern": "\\S"
        },
        "status": {
          "type": "string",
          "enum": [
            "stated",
            "derived"
          ],
          "default": "stated"
        },
        "source_trace": {
          "$ref": "#/definitions/sourceTrace"
        },
        "business_goal": {
          "type": "string",
          "pattern": "^BG-[0-9]{2,}$"
        },
        "analysis_support": {
          "$ref": "#/definitions/analysisSupport"
        }
      },
      "allOf": [
        {
          "if": {
            "anyOf": [
              {
                "not": {
                  "required": [
                    "status"
                  ]
                }
              },
              {
                "required": [
                  "status"
                ],
                "properties": {
                  "status": {
                    "const": "stated"
                  }
                }
              }
            ]
          },
          "then": {
            "required": [
              "source_trace"
            ],
            "properties": {
              "source_trace": {
                "allOf": [
                  {
                    "$ref": "#/definitions/sourceTrace"
                  },
                  {
                    "required": [
                      "doc",
                      "span"
                    ],
                    "properties": {
                      "span": {
                        "type": "string",
                        "minLength": 1,
                        "pattern": "\\S"
                      }
                    }
                  }
                ]
              }
            }
          }
        }
      ],
      "additionalProperties": true
    },
    "sourceTrace": {
      "type": "object",
      "required": [
        "doc"
      ],
      "properties": {
        "doc": {
          "type": "string",
          "minLength": 1,
          "pattern": "\\S"
        },
        "section": {
          "oneOf": [
            {
              "type": "string"
            },
            {
              "type": "null"
            }
          ]
        },
        "span": {
          "type": "string",
          "default": ""
        }
      },
      "additionalProperties": true
    },
    "analysisSupport": {
      "type": "object",
      "required": [
        "package_id",
        "analysis_revision",
        "analysis_sha256",
        "support_ids",
        "basis",
        "confidence",
        "promotion_state",
        "assumption_sensitive"
      ],
      "properties": {
        "package_id": {
          "type": "string",
          "minLength": 1,
          "pattern": "\\S"
        },
        "analysis_revision": {
          "type": "integer"
        },
        "analysis_sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        },
        "support_ids": {
          "type": "array",
          "minItems": 1,
          "uniqueItems": true,
          "items": {
            "type": "string",
            "minLength": 1,
            "pattern": "\\S"
          }
        },
        "basis": {
          "type": "string",
          "enum": [
            "stated",
            "accepted_decision",
            "accepted_assumption",
            "promoted_candidate"
          ]
        },
        "confidence": {
          "$ref": "#/definitions/confidence"
        },
        "promotion_state": {
          "const": "accepted"
        },
        "assumption_sensitive": {
          "type": "boolean"
        }
      },
      "additionalProperties": false
    },
    "confidence": {
      "type": "object",
      "required": [
        "level",
        "rationale",
        "support_refs"
      ],
      "properties": {
        "level": {
          "type": "string",
          "enum": [
            "low",
            "medium",
            "high"
          ]
        },
        "rationale": {
          "type": "string",
          "minLength": 1,
          "pattern": "\\S"
        },
        "support_refs": {
          "type": "array",
          "minItems": 1,
          "uniqueItems": true,
          "items": {
            "type": "string",
            "minLength": 1,
            "pattern": "\\S"
          }
        }
      },
      "additionalProperties": false
    },
    "nfrChecklistEntry": {
      "type": "object",
      "required": [
        "characteristic",
        "req_ids"
      ],
      "properties": {
        "characteristic": {
          "type": "string",
          "minLength": 1,
          "pattern": "\\S"
        },
        "req_ids": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "type": "string",
            "pattern": "^NFR-[0-9]+$"
          }
        },
        "na_reason": {
          "type": "string"
        }
      },
      "oneOf": [
        {
          "properties": {
            "req_ids": {
              "minItems": 1
            }
          }
        },
        {
          "required": [
            "na_reason"
          ],
          "properties": {
            "req_ids": {
              "maxItems": 0
            },
            "na_reason": {
              "minLength": 1,
              "pattern": "\\S"
            }
          }
        }
      ],
      "additionalProperties": true
    },
    "standardStrictRequirement": {
      "allOf": [
        {
          "$ref": "#/definitions/requirement"
        },
        {
          "required": [
            "analysis_support"
          ]
        }
      ]
    },
    "standardStrictRequirementsArray": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/standardStrictRequirement"
      }
    },
    "standardStrictDocument": {
      "allOf": [
        {
          "$ref": "#/definitions/requirementsDocument"
        },
        {
          "properties": {
            "requirements": {
              "$ref": "#/definitions/standardStrictRequirementsArray"
            }
          }
        }
      ]
    },
    "standardStrictRoot": {
      "oneOf": [
        {
          "$ref": "#/definitions/standardStrictDocument"
        },
        {
          "$ref": "#/definitions/standardStrictRequirementsArray"
        }
      ]
    }
  }
}
```

JSON Schema cannot enforce repository containment, exact package-currentness, canonical array ordering, cross-file references, or uniqueness by an object's `id` property. Those constraints remain deterministic CLI gates.

### B.3 Field reference

| Field | Type | Required when | Constraints | Example | Enforcing gate |
|---|---|---|---|---|---|
| Root | object or array | Always | Object must contain a `requirements` array; plain array is also accepted | `{"requirements":[]}` | Schema |
| `metadata` | object | Conforming object-root registry rendered to `SRS.md` | Contains deterministic, non-empty `title`, `version`, `date`, `author`, and `slug`; `date` uses `YYYY-MM-DD` | `{"title":"Authentication",...}` | Render-input conformance (not yet Draft-07 schema) |
| `requirements` | array | Object root | Every item must be a requirement object | `[{...}]` | Schema |
| `nfr_checklist` | array | Optional | Available only on object root; authored order is preserved | `[{...}]` | Schema; renderer |
| `requirements[].id` | string | Always | Unique; `FR-*`, `NFR-*`, `BR-*`, `EI-*`, or `CON-*` | `FR-001` | Schema; duplicate and stability gates |
| `requirements[].statement` | string | Always | Trimmed, non-empty, atomic, grounded, and verifiable | `The system shall reject an expired token.` | Schema; atomicity; ambiguity; verifiability |
| `requirements[].status` | enum | `$ba-srs` must emit; parser defaults omitted value to `stated` | `stated` or `derived` | `stated` | Schema |
| `requirements[].source_trace` | object | Every `stated` requirement; also every `derived` requirement at `light` | Identifies source document, optional section scope, and citation span; `light`-tier `derived` rows require a non-empty `doc` | `{"doc":"docs/brief.md",...}` | Schema; grounding; citation-exists for `stated` only |
| `requirements[].business_goal` | string | Optional | Zero or one goal; `BG-` plus at least two ASCII digits | `BG-01` | Goal integrity |
| `requirements[].analysis_support` | object | Every requirement in `standard` and `strict`; optional in `light` | Closed Level-4 envelope tied to one current analysis package | `{...}` | Analysis-support gate |
| `source_trace.doc` | string | Whenever `source_trace` is present; mandatory for `light`-tier `derived` rows | Non-empty repository-relative path contained by repo root | `docs/login-brief.md` | Grounding; path safety; citation-exists for `stated` only |
| `source_trace.section` | string or null | Optional | Markdown heading scope; empty, omitted, or null means document scope | `2. Authentication Requirements` | Citation-exists |
| `source_trace.span` | string | Non-empty for `stated`; optional or empty for `derived` | At verify time, stated spans must be at least 12 characters and verbatim | `Users must authenticate before access.` | Schema; citation-exists |
| `nfr_checklist[].characteristic` | string | Every checklist entry | Agent-authored quality characteristic; CLI does not infer taxonomy | `Security` | Schema; renderer |
| `nfr_checklist[].req_ids` | string array | Every checklist entry | Unique `NFR-*` IDs; non-empty unless `na_reason` is supplied | `["NFR-001"]` | Schema; NFR coverage policy |
| `nfr_checklist[].na_reason` | string | When `req_ids` is empty | Non-empty considered-not-applicable rationale | `No offline operation is in scope.` | Schema; renderer |
| `analysis_support.package_id` | string | With `analysis_support` | Exact `package_id` of the current analysis package | `analysis/login` | Support package-currentness |
| `analysis_support.analysis_revision` | integer | With `analysis_support` | Exact current package revision; booleans are invalid | `3` | `SUPPORT_REVISION_INVALID` or `SUPPORT_REVISION_STALE` |
| `analysis_support.analysis_sha256` | string | With `analysis_support` | Lowercase 64-character SHA-256 matching current canonical analysis | `4c1a...` | `SUPPORT_DIGEST_INVALID` or `SUPPORT_DIGEST_STALE` |
| `analysis_support.support_ids` | string array | With `analysis_support` | Non-empty, unique, lexicographically sorted, current package IDs | `["FACT-001"]` | Support ID and basis gates |
| `analysis_support.basis` | enum | With `analysis_support` | `stated`, `accepted_decision`, `accepted_assumption`, or `promoted_candidate` | `stated` | Support basis matrix |
| `analysis_support.confidence` | object | With `analysis_support` | Closed qualitative-confidence envelope | `{...}` | Confidence gate |
| `analysis_support.promotion_state` | string | With `analysis_support` | Must be `accepted` | `accepted` | `SUPPORT_PROMOTION_STATE` |
| `analysis_support.assumption_sensitive` | boolean | With `analysis_support` | True exactly when support depends on an accepted assumption | `false` | `SUPPORT_ASSUMPTION_SENSITIVE` |
| `confidence.level` | enum | With `confidence` | `low`, `medium`, or `high`; no numeric probability | `high` | `SUPPORT_CONFIDENCE_LEVEL` |
| `confidence.rationale` | string | With `confidence` | Trimmed, non-empty rationale | `Directly supported by FACT-001.` | `SUPPORT_CONFIDENCE_RATIONALE` |
| `confidence.support_refs` | string array | With `confidence` | Non-empty, unique, sorted, and known to the current package | `["FACT-001"]` | `SUPPORT_CONFIDENCE_REFS` |

### B.4 Status semantics

| Status | Meaning | `source_trace` | Citation-exists |
|---|---|---|---|
| `stated` | The obligation is directly present in the source | Required, including non-empty `doc` and `span` | Required |
| `derived` | The obligation is inferred from accepted context rather than directly stated | At `light`, required with non-empty `doc`; at `standard` / `strict`, optional because current `analysis_support` is mandatory. `span` may be omitted or empty. | Skipped |

Additional rules:

- An omitted `status` is interpreted as `stated`; canonical `$ba-srs` output must nevertheless write the field explicitly.
- A `derived` status is not a provenance bypass. `standard` and `strict` still require a current `analysis_support` envelope.
- **At `light`, `derived` status is discouraged.** If used, the requirement MUST include a `source_trace` with non-empty `doc` and MUST make the agent's derivation rationale explicit in `statement`. Citation-exists remains skipped because the obligation is not claimed as a verbatim source statement, but the grounding, atomicity, and verifiability gates still apply.
- A derived row may retain a source document or contextual span for human inspection, but `verify` does not run citation-exists for it.
- A stated row cannot use `analysis_support` as a substitute for its verbatim citation.
- Rejected or unresolved candidates do not belong in the canonical requirement registry.

### B.5 `source_trace` contract

#### Path resolution

`source_trace.doc` must be a repository-relative path. The verifier resolves it under `--repo-root`, confirms that the resolved target remains inside the root, and then reads that file as UTF-8.

For canonical JSON, `source_trace.doc` takes precedence over a command-level default source. A command-level source is only a fallback and does not relax the requirement to persist the originating document in a stated requirement.

#### Section scoping

When `section` is non-empty and citation scope is `section`:

1. Leading Markdown `#` characters and surrounding whitespace are ignored when matching the requested heading.
2. Heading comparison is case-insensitive.
3. The searchable section body ends at the next heading of the same or a higher level.
4. A span appearing only in a sibling or parent section does not pass.

When `section` is omitted, null, or empty, the entire document is searched. A document-scope CLI override also searches the entire document.

#### Verbatim span rules

For every stated requirement:

- `span` must contain at least 12 characters at the verify gate.
- It must be an exact substring of the selected source scope.
- No paraphrasing, ellipsis insertion, whitespace normalization, entity decoding, case folding, or approximate matching is allowed.
- The cited text need not equal the requirement statement, but it must genuinely support it.
- An invalid citation must not be automatically replaced with similar text.

#### Failure codes

| Code | Condition |
|---|---|
| `MALFORMED_JSON` | The registry cannot be parsed as JSON |
| `SCHEMA_INVALID` | The root is neither a list nor an object containing a requirements list |
| `INVALID_REQUIREMENT` | A requirement is not an object, lacks `id` or `statement`, has an invalid status, or a stated row lacks a non-empty span |
| `GROUNDING_MISSING` | A stated row lacks a source document reference |
| `PATH_TRAVERSAL` | A requirements or source path resolves outside the repository root |
| `SOURCE_NOT_FOUND` | A row-level source document does not exist |
| `SOURCE_NOT_PROVIDED` | Neither the row nor the command provides a source document |
| `CITATION_NOT_FOUND` | The span is under 12 characters, absent verbatim, outside the declared section, or the section cannot be resolved |

All listed citation and structural failures block `verify` with exit code `2`.

### B.6 REQ-ID naming and stability

REQ-IDs use uppercase semantic prefixes:

| Prefix | Meaning | SRS grouping |
|---|---|---|
| `FR-` | Functional requirement | §3.1 |
| `NFR-` | Non-functional or quality requirement | §3.2 |
| `BR-` | Business rule | §3.3 |
| `EI-` | External interface requirement | §3.4 |
| `CON-` | Constraint | §3.5 |

The accepted shape is:

```text
^(FR|NFR|BR|EI|CON)-[0-9]+$
```

New IDs should use a zero-padded three-digit suffix, such as `FR-001`, while the gate accepts one or more ASCII digits. The prefix itself is the classification; a separate `classification` or `kind` field is not required in the base schema.

REQ-ID rules:

- An ID is unique within the project or explicit team registry.
- An ID must never be reused for a different requirement.
- Editorial clarification that preserves meaning retains the ID.
- A genuinely different obligation receives a new ID.
- Split, merge, retirement, or renaming requires explicit history; silent renumbering is forbidden.
- Duplicate IDs fail with `DUPLICATE_REQ_ID`.

With a baseline, `detect_reqid_issues` performs two checks using normalized-word Jaccard similarity with threshold `0.75`:

- The same ID whose statement similarity falls below `0.75` produces `REQ_ID_MATERIAL_CHANGE`.
- A new ID whose statement similarity to an old requirement is at least `0.75` produces `REQ_ID_RENUMBERED`.

Both findings are FAIL-class.

### B.7 Optional envelopes

#### Business-goal registry

A requirement may carry one `business_goal` reference. The referenced registry is:

```text
.ba-ops/business-goals.json
```

```json
{
  "business_goals": [
    {
      "id": "BG-01",
      "title": "Reduce unauthorized access",
      "status": "active"
    }
  ]
}
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `business_goals` | array | Yes | Registry entries |
| `business_goals[].id` | string | Yes | Unique `BG-[0-9]{2,}` |
| `business_goals[].title` | string | Yes | Non-empty goal title |
| `business_goals[].status` | string | No | `retired` makes the goal unusable by active requirements |

An absent registry is treated as empty. A present requirement reference must have valid format, resolve to exactly one registry entry, and not reference a retired goal. Relevant failures are `BG_ID_FORMAT_INVALID`, `GOAL_REF_DANGLING`, `GOAL_REF_RETIRED`, and `DUPLICATE_GOAL_ID`.

#### NFR checklist

`nfr_checklist` is agent-authored structured data. The renderer displays exactly the supplied entries in authored order and does not infer quality characteristics.

Each entry either:

- maps a characteristic to one or more `NFR-*` IDs; or
- records an empty `req_ids` list and a non-empty `na_reason`.

The checklist is distinct from the lightweight NFR coverage signal. The signal only reports whether at least one requirement ID begins with `NFR-`; it does not prove checklist completeness or NFR quality.

#### `analysis_support`

`analysis_support` is optional in `light` and mandatory for every requirement in `standard` and `strict`.

Its direct-support matrix is:

| `basis` | Required analysis item |
|---|---|
| `stated` | `fact` with status `stated` |
| `accepted_decision` | `decision` with status `accepted` |
| `accepted_assumption` | `assumption` with status `accepted`; `assumption_sensitive` must be true |
| `promoted_candidate` | `derived_candidate` with status `promoted` |

Support IDs must belong to the current package revision and match the selected basis. Stakeholders, risks, action items, scenarios, hypotheses, questions, answers, unresolved items, and rejected or superseded items cannot directly support requirement promotion.

Missing support in `standard` or `strict` produces `ANALYSIS_SUPPORT_MISSING`. Invalid or stale envelopes produce the applicable `SUPPORT_*` failure code. Derived status does not bypass this gate.

### B.8 Gate mapping matrix

`lint-requirements` is a reporter: it emits findings but does not fail solely because a finding is FAIL-class. `verify` folds the same deterministic checks and exits `2` when any FAIL-class result exists. WARN-only verification exits `0`.

| Gate | `lint-requirements` | `verify` | Severity | Tier applicability |
|---|---|---|---|---|
| Atomicity | Reports `ATOMICITY_COMPOUND` | Folds and gates | FAIL | `light`, `standard`, `strict` |
| Ambiguity | Reports `AMBIGUITY_WEASEL` | Folds as non-blocking finding | WARN | `light`, `standard`, `strict` |
| Verifiability | Reports `VERIFIABILITY_MISSING` | Folds and gates | FAIL | `light`, `standard`, `strict` |
| Grounding | Reports `GROUNDING_MISSING` | Folds and gates | FAIL | `light`, `standard`, `strict` |
| Citation-exists | No substring search; structural issues may be reported | Performs the ≥12-character, scoped verbatim search | FAIL | `light`, `standard`, `strict`; stated only |
| Schema | Reports or returns structured input diagnostics | Validates before all other checks | FAIL | `light`, `standard`, `strict` |
| Trace | Reports invalid, duplicate, or unstable REQ-ID/source-trace data | Gates source trace before artifact trace is written | FAIL | `light`, `standard`, `strict` |
| Goal integrity | Reports duplicate and baseline-stability issues | Gates format, dangling, retired, and duplicate goal references | FAIL | All tiers when `business_goal` is present |
| NFR coverage | Emits set-level coverage signal | Returns `nfr_coverage`; false remains non-blocking | WARN | `light`, `standard`, `strict` |

For a `derived` requirement at `light`, `verify` SHALL require a non-empty `source_trace.doc` and an explicit agent rationale in `statement`. It skips only the citation-exists substring search; grounding, atomicity, and especially the FAIL-class verifiability gate remain applicable.

For `standard` and `strict`, the quality-gate stage additionally applies the Level-4 `analysis_support` gate after citation-exists and before lint structure, matching the fixed D.3 sequence.

### B.9 Examples

#### Minimal valid example

The example is valid for every tier assuming:

- `docs/login-brief.md` contains the quoted span under `Authentication`;
- the current analysis package is `analysis/login`, revision `1`;
- its canonical SHA-256 is the shown digest; and
- it contains `FACT-001` as a `fact` with status `stated`.

```json
{
  "metadata": {
    "title": "Authentication",
    "version": "1.0",
    "date": "2026-07-20",
    "author": "alice",
    "slug": "login"
  },
  "requirements": [
    {
      "id": "FR-001",
      "statement": "The system shall require authentication before protected access.",
      "status": "stated",
      "source_trace": {
        "doc": "docs/login-brief.md",
        "section": "Authentication",
        "span": "Users must authenticate before accessing protected resources."
      },
      "analysis_support": {
        "package_id": "analysis/login",
        "analysis_revision": 1,
        "analysis_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "support_ids": [
          "FACT-001"
        ],
        "basis": "stated",
        "confidence": {
          "level": "high",
          "rationale": "Directly supported by the stated source fact.",
          "support_refs": [
            "FACT-001"
          ]
        },
        "promotion_state": "accepted",
        "assumption_sensitive": false
      }
    }
  ]
}
```

In `light`, the `analysis_support` object may be omitted.

#### Invalid example 1 — invalid root

```json
{
  "items": []
}
```

Expected result: exit `2`, `SCHEMA_INVALID`.

#### Invalid example 2 — stated requirement without a span

```json
{
  "requirements": [
    {
      "id": "FR-001",
      "statement": "The system shall log every authentication attempt.",
      "status": "stated",
      "source_trace": {
        "doc": "docs/login-brief.md",
        "section": "Audit"
      }
    }
  ]
}
```

Expected result: exit `2`, `INVALID_REQUIREMENT`.

#### Invalid example 3 — structurally present but too-short citation

```json
{
  "requirements": [
    {
      "id": "FR-001",
      "statement": "The system shall log every authentication attempt.",
      "status": "stated",
      "source_trace": {
        "doc": "docs/login-brief.md",
        "section": "Audit",
        "span": "too short"
      }
    }
  ]
}
```

The non-empty span passes the structural check but fails the ≥12-character citation gate.

Expected result: exit `2`, `CITATION_NOT_FOUND`.

### B.10 Acceptance criteria

#### AC-B-01 — Canonical authority

Given `$ba-srs` produces a registry, when SRS or downstream artifacts are rendered, then every emitted requirement must originate from `.ba-ops/srs/<slug>/requirements.json`, and no renderer may invent an additional requirement.

#### AC-B-02 — Accepted root shapes

Given a root object containing a requirements array or a plain requirement array, when schema validation runs, then both shapes are accepted. Any other root shape fails with `SCHEMA_INVALID`.

#### AC-B-03 — Required requirement fields

Given a requirement entry, when `id` or `statement` is absent or blank, the entry is not an object, or `status` is outside `stated|derived`, then verification exits `2` with `INVALID_REQUIREMENT`.

#### AC-B-04 — Stated citation

Given a stated requirement, when its source path exists and its span is at least 12 characters and appears verbatim within the declared scope, then citation-exists passes. A short, paraphrased, missing, or out-of-scope span fails with `CITATION_NOT_FOUND`.

#### AC-B-05 — Derived citation handling

Given a derived requirement, citation-exists is skipped. At `light`, the row must still carry a non-empty `source_trace.doc`, make the agent's derivation rationale explicit in `statement`, and pass grounding, atomicity, and verifiability. At `standard` or `strict`, `source_trace` may be omitted or have an empty span, but the requirement must pass current `analysis_support` validation and the same quality gates.

#### AC-B-06 — Repository-contained sources

Given `source_trace.doc`, when its resolved path escapes the repository root, then verification exits `2` with `PATH_TRAVERSAL` before reading or publishing an artifact.

#### AC-B-07 — REQ-ID integrity

Given a registry and optional baseline, when IDs are validated, then only supported prefixes are accepted, duplicate IDs fail, materially repurposed IDs produce `REQ_ID_MATERIAL_CHANGE`, and silent renumbering produces `REQ_ID_RENUMBERED`.

#### AC-B-08 — Quality-gate folding

Given lint findings, when `lint-requirements` runs, then findings remain machine-readable reports. When `verify` runs, every FAIL-class lint finding blocks with exit `2`, while WARN-only findings do not block.

#### AC-B-09 — Business-goal integrity

Given a requirement with `business_goal`, when verification runs, then the ID must match `BG-[0-9]{2,}`, resolve uniquely in `.ba-ops/business-goals.json`, and reference a non-retired goal.

#### AC-B-10 — NFR checklist behavior

Given `nfr_checklist`, when SRS rendering runs, then entries appear in authored order, mapped IDs are displayed, and empty mappings display their `na_reason`. The CLI must not invent classifications or applicability decisions.

#### AC-B-11 — Tier-specific support

Given profile `light`, `analysis_support` may be absent. Given profile `standard` or `strict`, every requirement must contain the exact closed envelope and match one current analysis package revision and digest.

#### AC-B-12 — Deterministic evidence

Given identical registry, source, analysis package, configuration, and tool version, when validation and rendering are repeated, then gate evidence and rendered requirement ordering are deterministic and machine-readable.

## Part C: ISO/IEC/IEEE 29148 strict profile

Part A fixed IEEE 830 as the default shape for `SRS.md`; Part B fixed the `requirements.json` schema and the SRS §3.x mapping. Part C layers **ISO/IEC/IEEE 29148:2018** on top of that base for the `strict` tier — as an *optional contract profile*, not a rewrite of the document shape. It answers three questions: **when** 29148 applies, **what extra fields** each REQ must carry, and **how** the base sections align to 29148 artifacts. It does **not** claim line-by-line 29148 compliance; the alignment is at section granularity.

### C.1 When 29148 applies

29148 is **off by default**. The effective SRS profile flag is resolved in this order:

1. Use `srs_profile` from `.ba-ops/config.json` when that key is present.
2. Otherwise use `strict.requirements_profile` from `coverage-policy.json`.
3. If both locations set a value, `config.json` wins.

`srs_profile: iso-29148` is valid **only** when `.ba-ops/config.json` sets `profile: strict` (BRD-028). Preflight applies this truth table after precedence resolution:

| Active tier | Effective ISO flag | Preflight result |
|-------------|--------------------|------------------|
| `light` or `standard` | Absent | Pass; 29148 is inactive and absence is not an error |
| `light` or `standard` | `iso-29148` | **Hard fail**; the flag is invalid below `strict` |
| `strict` | Absent | Pass under the base strict profile; 29148 is inactive |
| `strict` | `iso-29148` | Pass; activate the 29148 extension |

Registry metadata alone does not activate 29148. When the effective flag is `iso-29148` at `strict`:

- Every REQ in the registry **must** carry the strict-tier fields in §C.3; the CLI-gated subset must pass SRS lint, and reviewers confirm the non-gated fields.
- The reviewer checklist in Part E adds the 29148 column.
- The manifest recorded at publish time includes `"srs_profile": "iso-29148"` for downstream verifiability.

**Non-goals.** Enabling the flag does **not** commit the product to producing a 29148 conformance audit report, nor to renaming IEEE 830 sections. `SRS.md` keeps its 830 skeleton; 29148 alignment is expressed through the mapping table below and through per-REQ fields.

### C.2 Section-level mapping — 29148 ↔ IEEE 830 ↔ `requirements.json`

The table maps **29148 requirements-engineering artifacts / SRS content items** to the **IEEE 830 sections** used in Part A and the **`requirements.json` fields** defined in Part B. It is deliberately coarse: one row per artifact, not per requirement clause. Classification of individual requirements is by **REQ-ID prefix** (`FR-`/`NFR-`/`BR-`/`EI-`/`CON-`); the base schema does not require a separate `kind` field.

| ISO 29148 artifact / SRS content | IEEE 830 section in `SRS.md` (Part A) | `requirements.json` field (Part B) |
|----------------------------------|---------------------------------------|--------------------------------------|
| Business goals / rationale for the system | §1 Introduction, §2 Overall Description, Business Goals | `.ba-ops/business-goals.json`; per-REQ `business_goal` (BG-*) |
| Stakeholders and stakeholder needs | §2 Overall Description | (prose in §2); optional extension fields at strict tier |
| Operational concept / user classes | §2 Overall Description | (prose in §2) |
| Individual requirement statement | §3.1–§3.5 (by REQ-ID prefix) | `req.id`, `req.statement`; classification by prefix |
| Requirement rationale | §3.x notes | `req.rationale` (strict + iso-29148 — §C.3) |
| Requirement source / traceability upward | §3.x notes; §5 Traceability | `req.source_trace{}` (BRD-007) |
| Verification method / acceptance criteria | §3 Specific Requirements | `req.verification.method`, `req.verification.criteria[]` (§C.3) |
| System quality characteristics (25010) | §3.2 Non-Functional Requirements; §3.6 NFR Coverage | `NFR-*` REQ-IDs; root `nfr_checklist[]` |
| Business rules | §3.3 Business Rules | `BR-*` REQ-IDs |
| External interfaces | §3.4 External Interfaces | `EI-*` REQ-IDs |
| Design / implementation constraints | §3.5 Constraints | `CON-*` REQ-IDs |
| Requirements attributes (priority, status, criticality) | §3 tables / prose | `req.priority`, `req.status`, `req.criticality` (§C.3 when flag on) |
| Assumptions and dependencies | §2 Overall Description | (prose in §2); optional metadata envelopes |
| Baseline of accepted requirements | Document header | registry metadata (deterministic inputs per A.6) |
| Verification cross-reference (V&V matrix) | §5 Traceability; INDEX.md | derived — see §C.6 |

**How to read the table.**

- The **left column** names the 29148 artifact or SRS content item; the reviewer uses this column when running the Part E checklist against a contract that cites 29148.
- The **middle column** points to the IEEE 830 section where that content is authored in prose in `SRS.md`. The 830 skeleton is unchanged.
- The **right column** is the schema field in `requirements.json`. Fields marked *strict-required* in §C.3 are absent at `light` / `standard` and **must** be present when the 29148 flag is on.

This is a *mapping*, not a compliance audit. The reviewer confirms each row is addressed somewhere; they do not audit paragraph-level conformance to 29148 prose.

### C.3 Additional strict-tier fields per REQ

At `strict` with the 29148 flag on, each REQ in `requirements.json` must carry the following fields **on top of** the Part B base schema. All fields are **machine-readable**; prose outside the registry does not satisfy the contract, although current CLI enforcement is partial as documented below.

These fields are **additive contract targets** for the `strict + iso-29148` profile only; they do not replace Part B required fields (`id`, `statement`, `status`, `source_trace` when `stated`, etc.). Unless a gate in Part B §B.8 or §C.3 below explicitly names a field, CLI enforcement may be partial — absence of gate coverage is a specification gap for reviewers, not an automatic pass.

| Field | Required? | Purpose |
|-------|-----------|---------|
| `req.rationale` | required | Why the REQ exists — links business intent to the statement. Free text, ≥ 1 sentence. |
| `req.verification.method` | required | One of `inspection`, `analysis`, `demonstration`, `test`. Drives the V&V matrix in §C.5–C.6. |
| `req.verification.criteria[]` | required | Ordered list of acceptance criteria strings. At least one entry; each entry is testable prose. |
| `req.priority` | required | MoSCoW value `must` \| `should` \| `could` \| `wont` (matches `$ba-backlog` grooming output). |
| `req.owner` | required | `owner_id` responsible for the REQ (aligns with BRD-023 owner-folder guard). |
| `req.criticality` | optional | `safety` \| `security` \| `business` \| `none`. Only required when 25010 category demands it. |
| `req.quality_characteristic` | conditional | Required when REQ-ID prefix is `NFR-`. Value is a 25010 category key from §C.4. |
| `req.tags[]` | optional | Free labels; not gated. Useful for slicing views without changing schema. |

**Current CLI enforcement coverage.** Contract-required but non-gated fields remain reviewer obligations; lack of a CLI gate is not a waiver.

| Strict + ISO field | Contract requirement | CLI-gated? | Current enforcement |
|--------------------|----------------------|:----------:|---------------------|
| `rationale` | Required | No | Human review only (presence and quality) |
| `verification.method` | Required | Yes | Presence and allowed enum |
| `verification.criteria[]` | Required | Yes | Non-empty list; each entry ≥ 12 characters |
| `priority` | Required | Yes | Presence and MoSCoW enum |
| `owner` | Required | Yes | Presence and owner validity |
| `criticality` | Optional / domain-conditional | No | Human review only |
| `quality_characteristic` | Required for `NFR-*` | Yes | Presence and C.4 category key |
| `tags[]` | Optional | No | Not gated |

**Gate behaviour.** The SRS lint gate at `strict + iso-29148` must:

1. Load `requirements.json`.
2. For each REQ, verify the CLI-gated required fields above are present and non-empty; for every `NFR-*`, also verify `quality_characteristic`.
3. Verify `verification.method` is one of the allowed enum values and `verification.criteria[]` has at least one entry with length ≥ 12 characters (mirrors the BRD-007 minimum-span discipline for citations).
4. Verify `priority` is present and enum-valid, and `owner` is present and valid.
5. On any missing or invalid field, emit a structured error listing REQ-IDs and the specific field violations, then exit `2`. No mutation, no promotion.

The current lint gate does **not** enforce `rationale`, `criticality`, or `tags[]`, and it does not judge whether verification criteria are *complete*. `rationale` remains contract-required and is checked by agent / human review in §C.5. The gate verifies only the fields marked **Yes** above for presence, type, and the stated mechanical constraints.

### C.4 Quality characteristics — ISO/IEC 25010 mapping

BRD §9 defines the product NFRs (NFR-001…NFR-010). Part A §3.6 renders them under IEEE 830 NFR Coverage. This section maps each 25010 category to how it is authored in the registry and checked in the SRS.

**Scope disclaimer.** BRD NFR anchors in this table refer to **BA Daily Ops product** non-functional requirements when authoring **meta/documentation** SRS; for **customer/project** use-case SRS, authors SHALL derive NFR-* from project source, not copy product NFR IDs.

**25010 category → `quality_characteristic` key → authoring guidance.**

| 25010 category (2011) | `quality_characteristic` key | BRD NFR anchor(s) | Authoring guidance in SRS §3.6 |
|-----------------------|------------------------------|-------------------|--------------------------------|
| Functional suitability | `functional_suitability` | (functional REQs) | Not typical for NFR-* — usually expressed as FR-* (§3.1). |
| Performance efficiency | `performance_efficiency` | NFR-001, NFR-007 | Time-behaviour, resource use, capacity. Give bound + reference environment. |
| Compatibility | `compatibility` | NFR-003 | Co-existence, interoperability. Cite runtime host and file-state layout. |
| Usability | `usability` | NFR-002, NFR-008 | Learnability, operability, accessibility. Cite golden-path command count. |
| Reliability | `reliability` | NFR-010 | Availability, fault tolerance, recoverability. Cite lock + atomic-replace pattern. |
| Security | `security` | NFR-009 | Confidentiality, integrity, non-repudiation, accountability, authenticity. |
| Maintainability | `maintainability` | NFR-006, NFR-005 | Modularity, testability, analysability. Cite determinism boundary. |
| Portability | `portability` | NFR-003, NFR-004 | Adaptability, installability, replaceability. Cite `--repo-root` resolution rule. |

Two authoring rules follow from this mapping:

- Every REQ with `NFR-*` prefix **must** set `quality_characteristic` to one of the eight keys above when the 29148 flag is on. Unset or unknown values fail the lint gate.
- Section §3.6 of `SRS.md` **must** render an `nfr_checklist` block — one row per 25010 category actually used by the registry — showing mapped `NFR-*` IDs or `na_reason`. This block is generated from `requirements.json`; it is not hand-written.

The mapping is **coarse on purpose**. The product does not run a 25010 sub-characteristic audit; it only records which top-level category each NFR belongs to, so reviewers can see the shape of the NFR coverage at a glance.

### C.5 Verification vs validation

29148 distinguishes **verification** (are we building the thing right?) from **validation** (are we building the right thing?). Part C fixes the meaning for this product so gates and human sign-offs land in the correct column.

**Verification — mechanical, owned by `ba-tools` and gates.**

Verification is anything the harness can prove from files, commands, schemas, and hashes without judging business intent. In this product, verification consists of:

- `ba-tools verify` on `requirements.json` — schema, REQ-ID uniqueness, field presence, enum values.
- `ba-tools lint-requirements` — atomicity, ambiguity, verifiability, grounding findings.
- Citation-exists gate (BRD-007) — literal-span presence in the source scope.
- Artifact quality gates (BRD-016) — atomicity, ambiguity, grounding, verifiability, schema, trace, when applicable.
- Render-safety gate (BRD-017) — path containment, official-renderer only.
- Coverage policy check (BRD-026) — required-artifact-kinds satisfied.
- Manifest hash verification — nothing `stale` in a bundle.

Every verification step produces machine-readable evidence. Agent prose claiming "this passes" is **not** verification (BRD-016, R-1).

**Validation — judgement, owned by humans (and, in supervised loops, agents).**

Validation is anything that requires business judgement about whether the requirement itself is the right one. In this product, validation consists of:

- Blind critic review under a rubric — enabled at `standard` / `strict` (BRD-018). Bounded to ≤ 3 rounds; open issues escalate to human.
- Human UAT — BA reads the delivered artifacts and confirms they express the intent (Appendix C DoD checklists at all tiers).
- Client / stakeholder acceptance — sign-off recorded in `MANIFEST.json` at `strict` (BRD §16.4; BR-008).
- BA Lead approval — the named authority whose ID is written into the manifest before a `strict` bundle is publishable.

**Rule of thumb.** If a `ba-tools` command can produce a `pass`/`fail` verdict without asking a human, it is **verification**. If the answer depends on "is this the right requirement?" or "does this express what the stakeholder meant?", it is **validation**. The two never substitute for each other: `INDEX.md` green is a *necessary* condition for publish, not a *sufficient* one (§16.4).

### C.6 Traceability beyond REQ-ID

REQ-ID is the spine (BRD-001). At `strict + iso-29148`, traceability extends in three directions on top of that spine — and all three views are rendered from `requirements.json`, trace records, and `INDEX.md`, not hand-maintained.

**1. Upstream — business goals (BG-*).**

Each business goal in `.ba-ops/business-goals.json` has an ID of the form `BG-<n>`. Every REQ *may* declare `business_goal` referencing one BG-ID. The reviewer view produced by `$ba-deliver status --view business-goals` (a read-only projection over the RTM) shows, for each BG-*, the REQ-IDs that claim it and their coverage state. A BG-* with zero linked REQs is a **goal gap** — reported but not a hard block, since goals may intentionally exceed the current scope.

**2. Cross-artifact — the RTM (`INDEX.md`).**

`INDEX.md` (BRD-003) is the operational RTM. At `strict + iso-29148`, one extra column is populated per REQ row: **verification method** (from `req.verification.method`) — so the RTM doubles as the V&V matrix required by 29148. The column is derived; the file is still not hand-editable (BRD-003).

**3. Downstream — trace records.**

Every artifact carrying `req_ids` produces a trace record under `.ba-ops/runs/<run-id>/` and canonical trace files under the owner root. At `strict + iso-29148`, trace records additionally carry:

- `srs_profile: iso-29148` — so downstream tools know which requirement profile produced them.
- `verification_evidence[]` — pointers to the gate-evidence files that satisfy each `verification.method`. Empty means no evidence yet, which is a **gap** (BRD-026 semantics), not silently `ok`.

No additional file layout is introduced beyond BRD Appendix B. The extension lives entirely in field shapes and rendered views.

---

## Part D: End-to-end workflow & tier matrix

Part D positions the SRS-SPEC gates inside the delivery workflow BRD Appendix A already defines, and extends BRD Appendix D with the SRS-SPEC-specific gates. It is descriptive of *this document's* obligations; it does not replace the BRD.

### D.1 Workflow — source to handoff-ready / publishable

```
Source (UC / brief / meeting note)
        │
        ▼
[optional]  $ba-intake run --mode elicit|meeting
        │            │
        │            ▼
        │   .ba-ops/analysis/<slug>/  (source-normalized, evidence,
        │                              readiness.json at strict)
        │
        ▼
$ba-srs run              (or discrete routes:)
        │
        ├──▶  extract      → candidate requirements registry (run staging)
        ├──▶  lint/verify  → schema, citation, quality, structure on candidate
        ├──▶  render       → candidate SRS.md view from candidate registry
        ├──▶  critic       → candidate pair review (`standard` / `strict`)
        └──▶  promote      → atomic canonical requirements.json + SRS.md
        │
        ▼
$ba-deliver run --uc <slug>
   (orchestrates srs → flow → mockup → index; strict adds critic + docx)
        │
        ▼
INDEX.md  →  read, fix gaps, resume as needed
        │
        ▼
Handoff-ready (light/standard)   or   Publishable (strict, + human sign-off)
```

- **`$ba-intake` is optional** — the conductor skips it when source readiness is already met (BRD-005). Skipping intake at `light` / `standard` is permitted; at `strict + iso-29148` an analysis package is required (BRD-026, Appendix D).
- **`$ba-srs` routes are independently invokable** but the conductor calls them in the fixed order above; the executable runner owns sequencing (BRD-027).
- **Gate failure at any route halts the workflow** before promotion and leaves both canonical artifacts untouched (BRD-010, BRD-027). `$ba-deliver resume` continues from the first unfinished route.

### D.2 Extended tier matrix — artifacts and SRS-SPEC gates

This table extends BRD Appendix D with the four SRS-SPEC gates (`lint`, `verify`, `render`, `critic`) so a reviewer sees the full picture without cross-referencing two documents. Legend: `✓` required, `○` optional, `—` not applicable.

| Artifact / gate | `light` | `standard` | `strict` | `strict + iso-29148` |
|-----------------|:-------:|:----------:|:--------:|:--------------------:|
| `requirements.json` (Part B schema) | ✓ | ✓ | ✓ | ✓ (+ §C.3 strict fields) |
| `SRS.md` — IEEE 830 skeleton (Part A) | ✓ | ✓ | ✓ | ✓ |
| `SRS.md` §3.6 `nfr_checklist` (25010 map, §C.4) | ○ | ✓ | ✓ | ✓ |
| Analysis package (`analysis/<slug>/`) | ○ | ✓ | ✓ | ✓ |
| `readiness.json` (assert-readiness per target) | — | ○ | ✓ | ✓ |
| **Gate: `$ba-srs lint`** — schema + structure + §C.3 fields | ✓ | ✓ | ✓ | ✓ (adds §C.3 field checks) |
| **Gate: `$ba-srs verify`** — citation-exists, atomicity, grounding | ✓ | ✓ | ✓ | ✓ |
| **Gate: `$ba-srs render`** — deterministic rendering to `SRS.md` | ✓ | ✓ | ✓ | ✓ |
| **Gate: critic** (blind, rubric-driven, ≤ 3 rounds) | ○ | ✓ | ✓ | ✓ |
| Coverage policy applied | `light` | `standard` | `strict` | `strict` |
| RTM (`INDEX.md`) — REQ-ID spine | ✓ | ✓ | ✓ | ✓ (+ verification-method column) |
| Business-goal projection (BG-*) | — | ○ | ○ | ✓ |
| `MANIFEST.json` — reproducible cross-machine hash | — | ○ | ✓ | ✓ (records `srs_profile`) |
| Human sign-off (BA Lead) in manifest | ○ | ○ | ✓ | ✓ |
| Golden path `= 1` command | ✓ | (unbounded) | (unbounded) | (unbounded) |

Rows below the SRS-SPEC gates are copied from BRD Appendix D for reviewer convenience; the BRD remains authoritative when the two differ.

### D.3 Gate ordering inside `$ba-srs`

Within the `$ba-srs` skill, gates run in the fixed order below. The order is owned by the executable runner (BRD-027) and does **not** change with the tier or the 29148 flag; only the *set of gates that must pass* changes.

1. **Schema** — the candidate registry parses, has unique REQ-IDs, and contains required fields per Part B (and §C.3 when the flag is on).
2. **Citation-exists** — BRD-007 literal-span check on every `stated` REQ in the candidate registry.
3. **Atomicity / grounding / verifiability** — BRD-016 quality gates run on the candidate registry.
4. **Lint structure** — candidate render inputs and the fixed template satisfy the 830 heading contract, §3.1–§3.6 structure, and the `nfr_checklist` requirement (§C.4) at `standard+`.
5. **Render** — generate a staged `SRS.md` view from the candidate registry; identical candidate inputs must render deterministically (NFR-005).
6. **Critic** — review the staged candidate pair at `standard+`; ≤ 3 rounds; unresolved issues escalate to human (BRD-018).
7. **Promote** — only after all applicable gates pass, atomically replace the canonical `requirements.json` and `SRS.md` as one pair.

Any earlier failure halts the workflow before later gates or promotion run. Evidence for each gate lands under `.ba-ops/runs/<run-id>/`; candidate files do not count toward canonical coverage.

---

## Part E: Review checklist & references

### E.1 Consolidated reviewer checklist

Reviewers work top-down. Sections marked *29148* run only when `srs_profile = iso-29148` is set at `strict`; all other rows run at every tier.

**IEEE 830 shape (all tiers).**

- [ ] `SRS.md` opens with §1 Introduction (`### 1.1 Purpose`, `### 1.2 Scope`, `### 1.3 Definitions`).
- [ ] §2 Overall Description is present (may be brief at `light`).
- [ ] Business Goals is present at every tier; when substantive content is not required, the renderer emits the stable fallback (Part A §A.2).
- [ ] §3 Specific Requirements is present and organized per Part A: `### 3.1 Functional Requirements` (FR-*), `### 3.2 Non-Functional Requirements` (NFR-*), `### 3.3 Business Rules` (BR-*), `### 3.4 External Interfaces` (EI-*), `### 3.5 Constraints` (CON-*), and `### 3.6 NFR Coverage`.
- [ ] §4 Appendices and §5 Traceability follow the template order.
- [ ] Every REQ appears exactly once in `SRS.md` and once in `requirements.json` — no REQ authored in prose that is missing from the registry.

**`requirements.json` schema (all tiers).**

- [ ] `ba-tools verify` exits `0` on the registry.
- [ ] Each REQ has: `id`, `statement`, `status`.
- [ ] `stated` REQs have valid `source_trace` with span ≥ 12 characters (BRD-007).
- [ ] REQ-IDs are unique (BRD-001), and the registry remains within its canonical owner folder (BRD-023).
- [ ] Every artifact declaring `req_ids` resolves to registry entries — no orphans (BRD-002).
- [ ] `INDEX.md` reports `0` gaps / orphans / stale for the UC scope (Appendix C DoD).

**ISO 25010 NFR coverage (`standard+`).**

- [ ] Root `nfr_checklist[]` is present when required by tier (Part A §A.2).
- [ ] §3.6 renders the checklist from `requirements.json` (not hand-written).
- [ ] For meta/documentation SRS, NFR-* REQs cite the BA Daily Ops BRD anchors mapped in §C.4 where applicable; customer/project SRS instead derive NFR-* from project source.

**ISO/IEC/IEEE 29148 (only when `srs_profile = iso-29148`).**

- [ ] `.ba-ops/config.json` sets `profile = strict`, and the effective flag resolves to `srs_profile = iso-29148` from `config.json` or `coverage-policy.json` using the C.1 precedence rule.
- [ ] Every REQ has non-empty `rationale`, `verification.method`, `verification.criteria[]` (≥ 1 entry, each ≥ 12 chars), `priority`, and `owner`.
- [ ] Every `NFR-*` REQ has a `quality_characteristic` set.
- [ ] The §C.2 mapping table has been walked row-by-row against `SRS.md` + `requirements.json`; each row is either satisfied or explicitly waived in `coverage-policy.json`.
- [ ] `INDEX.md` includes the verification-method column and the business-goal projection is generated.
- [ ] `MANIFEST.json` records `srs_profile = iso-29148` and the BA Lead sign-off ID.

**Verification vs validation posture (all tiers).**

- [ ] Every gate result cited as "pass" has a corresponding evidence file under `.ba-ops/runs/<run-id>/`.
- [ ] No agent-authored prose ("this REQ is verified") stands in for a machine-produced verification result.
- [ ] Human sign-off (validation) is recorded outside the gate evidence — never inferred from gate pass.

### E.2 References

- **IEEE Std 830-1998** — *Recommended Practice for Software Requirements Specifications*. Baseline shape for `SRS.md` established in Part A.
- **ISO/IEC/IEEE 29148:2018** — *Systems and software engineering — Life cycle processes — Requirements engineering*. Optional strict-tier profile mapped at section granularity in Part C; not audited section-by-section.
- **ISO/IEC 25010:2011** — *Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models*. Category source for the `quality_characteristic` field in §C.4 and for the `nfr_checklist` view in `SRS.md` §3.6.
- **`docs/BRD-v1.0.md`** — Business Requirements Document v1.0 (companion). Authoritative source for: BRD-001…BRD-028 functional requirements, NFR-001…NFR-010, Appendix D artifact × tier matrix (extended in §D.2), Appendix E references list (this section mirrors and extends it), and §16 governance.

---

*SRS-SPEC — v1.0 · 2026-07-20 · companion to `docs/BRD-v1.0.md` v1.0 · product `ba-daily-ops`.*
