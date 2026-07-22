---
status: complete
phase: BAOPS-01-harness-foundation
source: 01-03-SUMMARY.md, 01-07-SUMMARY.md, 01-08-SUMMARY.md, 01-09-SUMMARY.md, 01-10-SUMMARY.md, ROADMAP Phase 1 success criteria
started: 2026-07-22T03:58:00Z
updated: 2026-07-22T04:42:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Windows one-command install
expected: From repo root in PowerShell (Windows 10+, CPython 3.14), install.ps1 completes and ba-tools.ps1 --version emits one JSON object with 0.1.0 on stdout
result: pass
verified_by: terminal session 1.txt — Python 3.14.6, install.ps1 exit 0, ba-tools.ps1 --version single JSON {"version":"0.1.0"}

### 2. Doctor diagnostics
expected: .\ba-tools.ps1 doctor emits ordered JSON check results on stdout for Python 3.14, UTF-8, repo layout, and optional deps; exit 0 when healthy or exit 2 with actionable JSON on stderr when required checks fail
result: pass

### 3. Initialize .ba-ops workspace
expected: .\ba-tools.ps1 --repo-root . init creates .ba-ops/ containing config.json, coverage-policy.json, and business-goals.json with canonical packaged bytes
result: pass
note: init --repo-root (no value) and init --repo-root . both fail; correct order is --repo-root before init subcommand

### 4. CLI JSON contract
expected: Successful commands (e.g. --help) emit exactly one JSON object on stdout; failures (e.g. invalid flag) emit JSON on stderr with exit code 2 — never mixed streams or double emission
result: pass

### 5. Vietnamese UTF-8 round-trip
expected: Operating in a repo path or init context with Vietnamese UTF-8 text (e.g. thư-mục-dự-án) preserves characters correctly in CLI JSON output without mojibake
result: pass

### 6. Remote foundation CI evidence
expected: GitHub Actions run 29886063228 at commit dcd9859 shows success for the single windows-latest + Python 3.14 foundation job (Ruff, full pytest, offline smoke)
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
