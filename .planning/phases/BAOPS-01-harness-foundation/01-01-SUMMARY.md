---
phase: BAOPS-01-harness-foundation
plan: 01
subsystem: dependency-supply-chain
tags: [python, pip, binary-only, provenance, cross-platform]

requires: []
provides:
  - Exact approved runtime/bootstrap and development dependency closures for 16 supported target combinations
  - Human dispositions for every package in the normalized dependency union
  - Wheel filenames, compatibility tags, report hashes, artifact SHA-256 values, and provenance for Plan 01-02
affects: [BAOPS-01-02, installer, dependency-locks, zero-network]

tech-stack:
  added: []
  patterns:
    - Binary-only dependency approval precedes lock generation and installation
    - Installer network consent remains invocation-scoped

key-files:
  created:
    - .planning/phases/BAOPS-01-harness-foundation/01-01-SUMMARY.md
  modified:
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Approved the exact six direct pins and all 17 SUS package dispositions with no substitutions."
  - "Normalized colorama as Windows-only from its PEP 508 environment markers."
  - "Scoped Linux x64 approval to glibc-compatible manylinux_2_17_x86_64, not musllinux."
  - "Kept installer network consent invocation-scoped; this approval is not persistent consent."

patterns-established:
  - "Closure contract: Plan 01-02 must reproduce the approved per-target sets and normalized unions exactly."
  - "Artifact contract: source distributions are forbidden; only the recorded wheel files and SHA-256 values are authorized."

requirements-completed: [FOUND-03, NFR-03]

coverage:
  - id: D1
    description: "Exact binary-only dependency closures and artifact evidence approved for all supported targets"
    requirement: FOUND-03
    verification:
      - kind: manual_procedural
        ref: "Blocking-human checkpoint response: approved"
        status: pass
    human_judgment: true
    rationale: "Package legitimacy and organizational acceptance require explicit human judgment; the user approved the exact presented contract."
  - id: D2
    description: "Installer network consent remains invocation-scoped despite package approval"
    requirement: NFR-03
    verification:
      - kind: manual_procedural
        ref: "Approved checkpoint contract limits authorization to recorded artifacts and denies persistent network consent"
        status: pass
    human_judgment: true
    rationale: "Consent scope is a human authorization boundary."

duration: 4h 16m
completed: 2026-07-21
status: complete
---

# Phase BAOPS-01 Plan 01: Binary-Only Dependency Closure Approval Summary

**Human-approved, target-aware Python dependency contract covering 16 binary-only resolutions, 17 explicit SUS dispositions, and 27 exact wheel artifacts without creating a lock, environment, installation, or product source**

## Performance

- **Duration:** 4h 16m elapsed, including the blocking-human approval wait
- **Started:** 2026-07-21T04:50:00Z
- **Completed:** 2026-07-21T09:06:26Z
- **Tasks:** 1 completed
- **Files modified:** 4 planning/tracking files

## Accomplishments

- Received explicit blocking-human approval for the exact runtime/bootstrap and development closures on CPython 3.11 and 3.14 across Windows x64, macOS 12 x64/arm64, and Linux x64.
- Recorded exact report hashes, normalized closure sets, PEP 508 marker treatment, wheel filenames/tags, artifact SHA-256 values, provenance links, and human dispositions.
- Preserved the pre-install boundary: no lock, `.ba-tools-runtime/dev`, installed distribution, package tree, installer, or product source was created.

## Direct Pins

| Scope | Exact pin |
|---|---|
| Runtime and development | `click==8.4.2` |
| Runtime and development | `filelock==3.29.6` |
| Runtime and development | `jsonschema==4.26.0` |
| Runtime and development | `hatchling==1.29.0` |
| Development only | `pytest==9.1.1` |
| Development only | `ruff==0.15.22` |

Runtime/bootstrap roots are the first four pins. Development roots contain all six pins.

## Approved Substitutions

None. The user explicitly approved `SUBSTITUTIONS: none`.

## Target Matrix

The evidence was generated with pip 25.1.1 using `pip install --dry-run --ignore-installed --only-binary=:all: --platform … --python-version … --implementation cp --abi … --report …`. Every operation was dry-run only, and no installed-file action occurred.

| Closure | Python | OS / architecture | pip platform | ABI | Exact set | Dry-run report SHA-256 |
|---|---|---|---|---|---|---|
| Runtime | 3.11 | Windows x64 | `win_amd64` | `cp311` | R-WIN | `24bfb31eae6e856fd2dc11bff088a7403f294ab27165d2a26cc35bb2ae1d560d` |
| Runtime | 3.11 | macOS 12 x64 | `macosx_12_0_x86_64` | `cp311` | R-POSIX | `90fea05f778ed38ff639f7f22caacf981c02aa717d6771a283e8ec90af2319f2` |
| Runtime | 3.11 | macOS 12 arm64 | `macosx_12_0_arm64` | `cp311` | R-POSIX | `a5e2c729ea2d16cdacf128a72a620aa7863e4e5c7a7a5279fc3089a8a234c1e7` |
| Runtime | 3.11 | Linux x64 | `manylinux_2_17_x86_64` | `cp311` | R-POSIX | `2d4060dad34ff6b237a8fd52021171861654812ae2e34d4150d8d242e2534517` |
| Runtime | 3.14 | Windows x64 | `win_amd64` | `cp314` | R-WIN | `3b9b9714fc793fd197bc5d7b76b3acbcb72bb5220ea15f07745aa97a4aeedbd6` |
| Runtime | 3.14 | macOS 12 x64 | `macosx_12_0_x86_64` | `cp314` | R-POSIX | `0c67e4f54f4fc5498cd824c0f61473b0e570718d2a9ee78a52992e132cb1f9ea` |
| Runtime | 3.14 | macOS 12 arm64 | `macosx_12_0_arm64` | `cp314` | R-POSIX | `7a0866ef05e053ee136d4c503e214401b32af726b8ceaba1786592bc4ffdcd5b` |
| Runtime | 3.14 | Linux x64 | `manylinux_2_17_x86_64` | `cp314` | R-POSIX | `9b199ab978e17d7361b6ce14f9682a10c8ed4361a63f6be3877cb371a31a2350` |
| Development | 3.11 | Windows x64 | `win_amd64` | `cp311` | D-WIN | `3685ddda68f978c767c2388feffe277d76070227740dbd8b52f4d9c691a0458d` |
| Development | 3.11 | macOS 12 x64 | `macosx_12_0_x86_64` | `cp311` | D-POSIX | `4cc8ea8c626ff0db2e23076c66ca567ef99e92b90ab5dfd1a18521f851995723` |
| Development | 3.11 | macOS 12 arm64 | `macosx_12_0_arm64` | `cp311` | D-POSIX | `7e36c8fccc150980a472c421dd4cfbc7e629aef07cadb8ad30bed071454b2e00` |
| Development | 3.11 | Linux x64 | `manylinux_2_17_x86_64` | `cp311` | D-POSIX | `5db622ca661ef82b1680ba54dced5a94c07a09717fc7f95a9f838063f3f3e134` |
| Development | 3.14 | Windows x64 | `win_amd64` | `cp314` | D-WIN | `13e7c1c3a759f1ada8e85f177dc03768d9629355b5ae9773d653dd1bf313861c` |
| Development | 3.14 | macOS 12 x64 | `macosx_12_0_x86_64` | `cp314` | D-POSIX | `cd4236b35755499ef49c37332cb990e8bc6daac7da723a10c9a030a05c3b6bba` |
| Development | 3.14 | macOS 12 arm64 | `macosx_12_0_arm64` | `cp314` | D-POSIX | `0b565d9e3a0004773074253552824e91fd661fff905b68d6f1e0de2c62ab6c3e` |
| Development | 3.14 | Linux x64 | `manylinux_2_17_x86_64` | `cp314` | D-POSIX | `c5b07c7b277bff893e2b20595975ab837e4d7c3f68f011e16f739ea626a2549f` |

The approved Linux target is glibc-compatible `manylinux_2_17_x86_64`, not musllinux.

## Runtime Closure

**R-POSIX (12 packages):**

`attrs==26.1.0, click==8.4.2, filelock==3.29.6, hatchling==1.29.0, jsonschema==4.26.0, jsonschema-specifications==2025.9.1, packaging==26.2, pathspec==1.1.1, pluggy==1.6.0, referencing==0.37.0, rpds-py==2026.6.3, trove-classifiers==2026.6.1.19`

**R-WIN (13 packages):** R-POSIX plus `colorama==0.4.6`.

**Runtime normalized union:** R-WIN exactly.

## Development Closure

**D-POSIX (16 packages):** R-POSIX plus `iniconfig==2.3.0, pygments==2.20.0, pytest==9.1.1, ruff==0.15.22`.

**D-WIN (17 packages):** D-POSIX plus `colorama==0.4.6`.

**Development normalized union:** D-WIN exactly.

**Audited normalized-name set:** `attrs, click, colorama, filelock, hatchling, iniconfig, jsonschema, jsonschema-specifications, packaging, pathspec, pluggy, pygments, pytest, referencing, rpds-py, ruff, trove-classifiers`.

### Environment Marker Treatment

Active dependency edges:

- Click → `colorama; platform_system == 'Windows'`
- pytest → `colorama>=0.4; sys_platform == "win32"`
- jsonschema → `attrs>=22.2.0`, `jsonschema-specifications>=2023.03.6`, `referencing>=0.28.4`, `rpds-py>=0.25.0`
- jsonschema-specifications → `referencing>=0.31.0`
- referencing → `attrs>=22.2.0`, `rpds-py>=0.7.0`
- hatchling → `packaging>=24.2`, `pathspec>=0.10.1`, `pluggy>=1.0.0`, `trove-classifiers`
- pytest → `iniconfig>=1.0.1`, `packaging>=22`, `pluggy<2,>=1.5`, `pygments>=2.7.2`

Inactive extras retained as metadata but excluded from closures: pytest's `attrs; extra=="dev"` and Pygments' `colorama; extra=="windows-terminal"`.

Pip evaluates platform markers against its host even with `--platform`; raw Windows-host reports therefore included `colorama` universally. Independent PEP 508 marker evaluation returned true on Windows and false on POSIX. The user explicitly accepted authoritative target normalization with `colorama` Windows-only.

## Binary-Only Evidence

Every selected artifact is a wheel with an exact SHA-256. No source distribution was selected.

| Package artifact | Wheel tags | SHA-256 |
|---|---|---|
| `attrs-26.1.0-py3-none-any.whl` | `py3-none-any` | `c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309` |
| `click-8.4.2-py3-none-any.whl` | `py3-none-any` | `e6f9f66136c816745b9d65817da91d61d957fb16e02e4dcd0552553c5a197b76` |
| `colorama-0.4.6-py2.py3-none-any.whl` | `py2.py3-none-any` | `4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6` |
| `filelock-3.29.6-py3-none-any.whl` | `py3-none-any` | `14d5f5597d2e0c4dbd774cfb6d8132da1db44da83732aab679d54f7dcf97ab65` |
| `hatchling-1.29.0-py3-none-any.whl` | `py3-none-any` | `50af9343281f34785fab12da82e445ed987a6efb34fd8c2fc0f6e6630dbcc1b0` |
| `iniconfig-2.3.0-py3-none-any.whl` | `py3-none-any` | `f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12` |
| `jsonschema-4.26.0-py3-none-any.whl` | `py3-none-any` | `d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce` |
| `jsonschema_specifications-2025.9.1-py3-none-any.whl` | `py3-none-any` | `98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe` |
| `packaging-26.2-py3-none-any.whl` | `py3-none-any` | `5fc45236b9446107ff2415ce77c807cee2862cb6fac22b8a73826d0693b0980e` |
| `pathspec-1.1.1-py3-none-any.whl` | `py3-none-any` | `a00ce642f577bf7f473932318056212bc4f8bfdf53128c78bbd5af0b9b20b189` |
| `pluggy-1.6.0-py3-none-any.whl` | `py3-none-any` | `e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746` |
| `pygments-2.20.0-py3-none-any.whl` | `py3-none-any` | `81a9e26dd42fd28a23a2d169d86d7ac03b46e2f8b59ed4698fb4785f946d0176` |
| `pytest-9.1.1-py3-none-any.whl` | `py3-none-any` | `37a86b45efb9a47a61a36449063e8e18d0cab3161329fc099eb21783169c4f0c` |
| `referencing-0.37.0-py3-none-any.whl` | `py3-none-any` | `381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231` |
| `trove_classifiers-2026.6.1.19-py3-none-any.whl` | `py3-none-any` | `ab4c4ec93cc4a4e7815fa759906e05e6bb3f2fbd92ea0f897288c6a43efd15b3` |
| `rpds_py-2026.6.3-cp311-cp311-win_amd64.whl` | `cp311-cp311-win_amd64` | `2c54a076ca4d370980ab57bc0e31df57bbe8d41340436a90ef8b1219a3cbb127` |
| `rpds_py-2026.6.3-cp311-cp311-macosx_10_12_x86_64.whl` | `cp311-cp311-macosx_10_12_x86_64` | `7b689145a1485c335569bd056464f3243a29af7ed3871c7be31ad624ba239bc7` |
| `rpds_py-2026.6.3-cp311-cp311-macosx_11_0_arm64.whl` | `cp311-cp311-macosx_11_0_arm64` | `db08f45aecde626498fb3df07bcf6d2ec040af42e859a4f5040d79c200342911` |
| `rpds_py-2026.6.3-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64` | `9c1255b302953c86a486b81d330d5ee1d5bd937691ce271b6be0ef0e299eaab7` |
| `rpds_py-2026.6.3-cp314-cp314-win_amd64.whl` | `cp314-cp314-win_amd64` | `0be972be84cfcaf46c8c6edf690ca0f154ac17babf1f6a955a51579b34ad2dc5` |
| `rpds_py-2026.6.3-cp314-cp314-macosx_10_12_x86_64.whl` | `cp314-cp314-macosx_10_12_x86_64` | `931908d9fc855d8f74783377822be318edb6dcb19e47169dc038f9a1bf60b06e` |
| `rpds_py-2026.6.3-cp314-cp314-macosx_11_0_arm64.whl` | `cp314-cp314-macosx_11_0_arm64` | `d7469697dce35be237db177d42e2a2ee26e6dcc5fc052078a6fefabd288c6edd` |
| `rpds_py-2026.6.3-cp314-cp314-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `cp314-cp314-manylinux_2_17_x86_64.manylinux2014_x86_64` | `dc319e5a1de4b6913aac94bf6a2f9e847371e0a140a43dd4991db1a09bc2d504` |
| `ruff-0.15.22-py3-none-win_amd64.whl` | `py3-none-win_amd64` | `9be63ba1eb936acd2d1342fb8337c356353706fce233b2a15a09a97037e6acde` |
| `ruff-0.15.22-py3-none-macosx_10_12_x86_64.whl` | `py3-none-macosx_10_12_x86_64` | `b82c6482946e9eda7ff2e091d25b8bad3f718684e1916d41bd56873cee05b697` |
| `ruff-0.15.22-py3-none-macosx_11_0_arm64.whl` | `py3-none-macosx_11_0_arm64` | `11c1c715af53a09f714e011106bffc419751ec8232fcb5da42173284ea3fec6f` |
| `ruff-0.15.22-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64` | `365523eb91d9224e1bcb03b022fbf0facb8f9e23792a2c53d9d4b3924bdbdebb` |

## Package Legitimacy Approval

The prior legitimacy seam returned `SLOP: none`, `ASSUMED: none`, and `SUS` for all 17 normalized names. Reason abbreviations: `UD` unknown downloads, `TN` too new, and `NR` repository absent from the automated seam. The seam's too-new signal was package-level/current-release metadata; approval remains bound to the exact versions and artifact hashes in this record.

The user's `approved` response explicitly accepted every listed SUS disposition:

| Package | Verdict/reasons | PyPI release | Attributable source | Human disposition |
|---|---|---|---|---|
| attrs 26.1.0 | SUS: UD, NR | https://pypi.org/project/attrs/26.1.0/ | https://github.com/python-attrs/attrs | ACCEPTED |
| click 8.4.2 | SUS: TN, UD | https://pypi.org/project/click/8.4.2/ | https://github.com/pallets/click/ | ACCEPTED |
| colorama 0.4.6 | SUS: UD | https://pypi.org/project/colorama/0.4.6/ | https://github.com/tartley/colorama | ACCEPTED |
| filelock 3.29.6 | SUS: TN, UD | https://pypi.org/project/filelock/3.29.6/ | https://github.com/tox-dev/py-filelock | ACCEPTED |
| hatchling 1.29.0 | SUS: TN, UD | https://pypi.org/project/hatchling/1.29.0/ | https://github.com/pypa/hatch/tree/master/backend | ACCEPTED |
| iniconfig 2.3.0 | SUS: UD | https://pypi.org/project/iniconfig/2.3.0/ | https://github.com/pytest-dev/iniconfig | ACCEPTED |
| jsonschema 4.26.0 | SUS: UD | https://pypi.org/project/jsonschema/4.26.0/ | https://github.com/python-jsonschema/jsonschema | ACCEPTED |
| jsonschema-specifications 2025.9.1 | SUS: UD | https://pypi.org/project/jsonschema-specifications/2025.9.1/ | https://github.com/python-jsonschema/jsonschema-specifications | ACCEPTED |
| packaging 26.2 | SUS: UD | https://pypi.org/project/packaging/26.2/ | https://github.com/pypa/packaging | ACCEPTED |
| pathspec 1.1.1 | SUS: UD, NR | https://pypi.org/project/pathspec/1.1.1/ | https://github.com/cpburnz/python-pathspec | ACCEPTED |
| pluggy 1.6.0 | SUS: UD, NR | https://pypi.org/project/pluggy/1.6.0/ | https://github.com/pytest-dev/pluggy | ACCEPTED |
| pygments 2.20.0 | SUS: UD | https://pypi.org/project/Pygments/2.20.0/ | https://github.com/pygments/pygments | ACCEPTED |
| pytest 9.1.1 | SUS: UD | https://pypi.org/project/pytest/9.1.1/ | https://github.com/pytest-dev/pytest | ACCEPTED |
| referencing 0.37.0 | SUS: UD | https://pypi.org/project/referencing/0.37.0/ | https://github.com/python-jsonschema/referencing | ACCEPTED |
| rpds-py 2026.6.3 | SUS: TN, UD | https://pypi.org/project/rpds-py/2026.6.3/ | https://github.com/crate-py/rpds | ACCEPTED |
| ruff 0.15.22 | SUS: TN, UD | https://pypi.org/project/ruff/0.15.22/ | https://github.com/astral-sh/ruff | ACCEPTED |
| trove-classifiers 2026.6.1.19 | SUS: UD | https://pypi.org/project/trove-classifiers/2026.6.1.19/ | https://github.com/pypa/trove-classifiers | ACCEPTED |

### Approval Scope

Approval authorizes only the exact names, versions, markers, target sets, wheel files, report hashes, and SHA-256 values recorded above. It does not grant persistent installer network consent. Under D-05, any future installer network access requires fresh, invocation-scoped explicit consent.

## Task Commits

| Task | Name | Commit |
|---|---|---|
| 1 | Approve every binary-only target closure | This atomic plan metadata commit |

No separate production-code commit exists because this checkpoint creates only its approval record and required planning tracking updates.

## Files Created/Modified

- `.planning/phases/BAOPS-01-harness-foundation/01-01-SUMMARY.md` — exact closure, artifact, provenance, and approval contract.
- `.planning/STATE.md` — plan progress, metrics, decisions, and session continuity.
- `.planning/ROADMAP.md` — Phase 1 plan progress.
- `.planning/REQUIREMENTS.md` — plan requirements marked complete by the execute-plan tracking contract.

## Decisions Made

- Accepted all 17 `SUS` packages at the exact versions and artifacts presented at the blocking-human checkpoint.
- Approved no package substitutions.
- Accepted `colorama==0.4.6` only for Windows target closures after PEP 508 marker normalization.
- Approved Linux x64 only as `manylinux_2_17_x86_64`.
- Preserved invocation-scoped installer network consent; package approval alone cannot authorize a later download.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pip's cross-target `--platform` handling retained host-evaluated platform markers in raw reports. The pre-checkpoint automation independently evaluated the relevant PEP 508 markers and presented `colorama` as Windows-only; the user explicitly approved that normalization.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-02 may consume this record as its exact dependency-lock input contract.
- Plan 01-02 must prove its generated target sets and normalized unions equal this approval exactly before creating the development environment or installing distributions.
- No blocker remains for Plan 01-02.

## Self-Check: PASSED

- Summary exists with all seven plan-required headings.
- Evidence counts match the approved checkpoint: 16 target rows, 27 wheel artifacts, and 17 explicit `ACCEPTED` SUS dispositions.
- All exact closure sets, report hashes, marker treatment, artifact hashes, and provenance links were transcribed from the verified checkpoint evidence.
- `.planning/STATE.md`, `.planning/ROADMAP.md`, and `.planning/REQUIREMENTS.md` contain the required sequential-execution tracking updates.
- No lock, `.ba-tools-runtime`, package tree, environment, installer, installed distribution, or product source exists.
- Atomic metadata commit verification is performed immediately after committing and reported in the completion response.

---
*Phase: BAOPS-01-harness-foundation*
*Completed: 2026-07-21*
