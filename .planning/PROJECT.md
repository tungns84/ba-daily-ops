# BA Daily Ops

## What This Is

**BA Daily Ops** (`ba-daily-ops`) biến vòng lặp giao phẩm hằng ngày của Business Analyst — use case → SRS/yêu cầu → sơ đồ quy trình → mockup UI → chỉ mục truy vết — thành quy trình lặp lại được, kiểm chứng được và truy vết được. Mỗi bước là skill hướng người dùng (`$ba-*`) được hậu thuẫn bởi lớp deterministic `ba-tools` và chặn bởi cổng chất lượng. BA chỉ cần một lệnh — `$ba-deliver run --uc <slug>` — và conductor điều phối toàn bộ chuỗi từ đầu đến cuối.

Sản phẩm **harness-first**: không cạnh tranh tốc độ soạn nháp với LLM đơn lẻ (~70% giá trị ở harness, ~30% ở soạn thảo). Giá trị nằm ở file-state xác định, hash, gate, truy vết REQ-ID và tính di động — những thứ phiên chat LLM không giữ lại.

## Core Value

**Truy vết REQ-ID xuyên suốt các giao phẩm.** Xương sống: SRS → flow → mockup → (tùy chọn) backlog → INDEX. Một yêu cầu phải nhất quán trên mọi artifact; drift lộ ra ngay khi xuất hiện. Nếu mọi thứ khác thất bại, xương sống truy vết vẫn phải hoạt động.

## Business Context

- **Customer**: Business Analyst (người dùng chính); BA Lead, khách hàng nhận giao phẩm, dev tiếp nhận backlog
- **Revenue model**: Công cụ nội bộ / productivity harness (local-first, không SaaS v1)
- **Success metric**: Golden path = 1 lệnh; INDEX 0 gap/orphan/stale sau handoff; conformance corpus ≥ 49/50 mutation
- **Strategy notes**: BRD v1.0 (`docs/BRD-v1.0.md`), SRS-SPEC v1.0 (`docs/SRS-SPEC.md`)

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Xương sống truy vết REQ-ID: registry canonical → SRS → flow/BPMN → mockup → INDEX (BRD-001…004)
- [ ] Skill layer `$ba-*`: intake, srs, flow, mockup, deliver conductor, plugins bpmn/backlog/docx (BRD-005…014)
- [ ] Gates chất lượng: citation-exists, confirmation, artifact quality, render safety, blind critic (BRD-015…018)
- [ ] Harness runtime: doctor, installer portable, file-state `.ba-ops/`, CLI JSON contract (BRD-019…022)
- [ ] Team mode: owner folder, cross-owner write guard, read-only team report (BRD-023…025)
- [ ] Coverage policy theo profile tier light/standard/strict; executable workflow runner (BRD-026…028)
- [ ] SRS artifact pair: `requirements.json` canonical + `SRS.md` derived view theo SRS-SPEC
- [ ] Golden path một lệnh `$ba-deliver run --uc <slug>` với resume (US-03, US-07)
- [ ] Phát hiện drift qua hash; chống false-green RTM (OBJ-4, OBJ-6, BRD-026)
- [ ] Portability: resolve path theo `--repo-root`, zero-network cho `ba-tools`, UTF-8 tiếng Việt (NFR-003…009)

### Out of Scope

- Cạnh tranh tốc độ soạn nháp với ChatGPT/LLM đơn lẻ — harness-first positioning
- Cam kết tái lập theo byte cho nội dung LLM — chỉ hash-stable sau accept + freeze
- Backend đa người dùng / SaaS chung — local-first v1
- OCR/trích xuất từ scan/ảnh — phải làm trước intake
- Semantic correctness từ gate pass — human sign-off bắt buộc ở strict

## Context

**Bài toán:** BA tạo SRS, sơ đồ, mockup, backlog trong công cụ rời rạc; khi yêu cầu đổi, cập nhật thủ công gây drift âm thầm. LLM đơn lẻ soạn nhanh nhưng không có file-state, hash, REQ-ID spine, phát hiện drift.

**Kiến trúc sản phẩm:**
- **Skills** (`$ba-deliver`, `$ba-srs`, `$ba-flow`, `$ba-mockup`, …): hướng người dùng
- **ba-tools**: CLI Python deterministic — file/command/hash/schema/gate
- **`.ba-ops/`**: file-state (config, registry, trace, INDEX, runs/journal)
- **Profile tier** (`light` | `standard` | `strict`): single control plane cho coverage và ceremony

**Tier mặc định:** `light` — golden path 1 lệnh, flow inline, verify/lint, không critic bắt buộc.

**Pilot KPI:** 1–2 BA, 10 UC, 2 tuần; golden path = 1 lệnh; RTM completeness 10/10; conformance ≥ 49/50 mutations.

**Upstream docs:** `docs/BRD-v1.0.md` (Product Intent, BRD-001…028, NFR-001…010), `docs/SRS-SPEC.md` (authoring contract cho SRS pair).

## Constraints

- **Tech stack**: Python 3.11+ (`ba-tools`), chat skill runtime, Node 18+ (Mermaid/draw.io khi cần), git 2.x+
- **Determinism boundary**: `ba-tools` chỉ provable ops; agent sở hữu judgement/authoring
- **CLI contract**: success → 1 JSON UTF-8 stdout; error → JSON stderr + exit 2
- **Render**: draw.io Desktop CLI (BPMN), `@mermaid-js/mermaid-cli` (Mermaid) — cấm screenshot fallback
- **Portability**: cấm absolute path trong config commit; mọi path resolve `--repo-root`
- **Security**: `ba-tools` zero-network; path containment trong repo root
- **Scale**: ≤ 500 REQ, ≤ 50 UC/milestone, ≤ 5 BA (team mode)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Harness-first (70/30) | Giá trị bền ở file-state, gate, trace — không chạy đua tốc độ nháp LLM | — Pending |
| `requirements.json` canonical, `SRS.md` derived | Một nguồn sự thật cho REQ-ID; tránh drift Markdown-only (SRS-SPEC N-1…N-5) | — Pending |
| Profile tier = single control plane | Ceremony tương xứng việc; light giữ golden path 1 lệnh | — Pending |
| Executable workflow runner owns promotion | Agent chỉ tạo candidate; runner promote sau gate — chống LLM bỏ gate (R-1) | — Pending |
| Vertical MVP phases | End-to-end capability mỗi phase — user chọn MVP mode | — Pending |
| Integrity via hash/trace, not byte-repro LLM | Văn bản LLM không tất định; chứng minh mối quan hệ file (OBJ-4, NFR-005) | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-20 after initialization*
