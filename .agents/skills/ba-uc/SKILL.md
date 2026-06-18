---
name: ba-uc
description: >
  Delivers one use case end-to-end as a sequential agent loop: srs-analyze (full)
  → mermaid (full, explicit — NOT default author) → mockup (full) → index update.
  A Quality gate (verify + ba-critic CoVe) runs after srs-analyze; a D-G2
  index-integrity gate (orphans + self-coverage) runs after mermaid and mockup.
  Pipeline status is written between steps: complete only after the gate passes,
  failed on gate fail then STOP (D-RES1). Resumable via uc-status (D-RES2).
  Routes: deliver | resume | status | iterate (default: deliver).
  --uc required: "<file>: ## UC-001. <name>". --fidelity required: html | wireframe.
  The shared slug is captured from the srs step output and threaded verbatim to
  every subsequent step. --fidelity is forwarded to the mockup step.
  Trigger phrases: "deliver use case", "ba-uc deliver", "run use case", "$ba-uc".
---

<!-- Workflow file: .agents/ba-daily-operators/ba-core/workflows/ba-uc.md -->
<!-- No body content required — SKILL.md is a discovery index only         -->
