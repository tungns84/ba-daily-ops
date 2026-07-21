# Requirements: BA Daily Ops

**Defined:** 2026-07-20
**Core Value:** Truy vết REQ-ID xuyên suốt các giao phẩm — drift lộ ra ngay khi xuất hiện

## User Stories

| ID | Story | Tier |
|----|-------|------|
| US-01 | BA tạo SRS có REQ-ID từ use case làm nguồn sự thật | all |
| US-02 | Mỗi REQ-ID truy vết xuyên SRS → flow → mockup → INDEX | all |
| US-03 | Bàn giao UC bằng đúng một lệnh `$ba-deliver run --uc <slug>` | all |
| US-07 | Resume tiếp tục đúng bước còn dở, không ghi đè artifact đã hoàn tất | all |
| US-08 | INDEX chỉ báo `ok` khi coverage thực sự đủ — không false-green | all |

## Acceptance Criteria

Key acceptance criteria from BRD §11 that gate v1 release:

- Citation-exists: stated REQ có span ≥12 ký tự verbatim trong source scope (AC-BRD-007)
- INDEX sinh tất định với trạng thái ok/gap/orphan/stale/waived (AC-BRD-003)
- Coverage policy chống false-green — thiếu mockup không được hiển thị ok (AC-BRD-026)
- Runner sở hữu thứ tự route; gate fail giữ canonical (AC-BRD-027)
- Golden path một điểm vào; dừng tại gate lỗi; resume không chạy lại bước đã promote (AC-BRD-010)
- Drift chuyển artifact sang stale và loại khỏi coverage (AC-BRD-004)

## Definition of Done

**Light tier (v1 pilot):**

- `requirements.json` + `SRS.md` — verify pass; citation-exists 100% cho REQ `stated`
- Mermaid inline — `req_ids` trong frontmatter
- Mockup html hoặc wireframe — `req_ids` máy-đọc-được
- `INDEX.md` — 0 gap / 0 orphan / 0 stale cho REQ thuộc UC
- `$ba-deliver status` báo hoàn tất
- Golden path command count = 1 (không tính doctor/init)

## v1 Requirements

Requirements for initial release (light tier pilot + harness foundation). Each maps to roadmap phases.

### Harness Foundation

- [ ] **FOUND-01**: `ba-tools` CLI trả đúng một JSON UTF-8 ra stdout khi thành công; lỗi ra stderr với exit code 2 (BRD-022)
- [ ] **FOUND-02**: `ba-tools doctor` kiểm tra Python, UTF-8, cấu trúc repo và dependency tùy chọn (BRD-019)
- [x] **FOUND-03**: Installer một lệnh (Windows PowerShell + POSIX) không hard-code path máy (BRD-020)
- [ ] **FOUND-04**: `.ba-ops/` file-state khởi tạo với `config.json`, `coverage-policy.json`, `business-goals.json` (BRD-021, BRD-028)
- [ ] **FOUND-05**: Mọi path nghiệp vụ resolve tương đối `--repo-root`; chống path traversal (NFR-009)
- [ ] **FOUND-06**: Write operations dùng lock và atomic replace; crash không để canonical nửa ghi (NFR-010)

### Traceability & Registry

- [ ] **TRACE-01**: REQ-ID duy nhất, ổn định qua chỉnh sửa nội dung; split/merge có lịch sử (BRD-001)
- [ ] **TRACE-02**: Artifact downstream khai báo `req_ids` máy-đọc-được; orphan được báo (BRD-002)
- [ ] **TRACE-03**: `.ba-ops/INDEX.md` sinh lại từ registry + trace với trạng thái ok/gap/orphan/stale/waived (BRD-003)
- [ ] **TRACE-04**: Hash source/artifact/gate được ghi và so sánh; drift → stale (BRD-004)

### SRS & Requirements Authoring

- [ ] **SRS-01**: `$ba-srs` tạo `requirements.json` canonical và render `SRS.md` derived — không invent REQ trong Markdown (BRD-006, SRS-SPEC N-1)
- [ ] **SRS-02**: Citation-exists gate: stated REQ có span ≥12 ký tự verbatim trong section đã khai báo (BRD-007)
- [ ] **SRS-03**: `ba-tools verify` và `lint-requirements` trên registry — schema, atomicity, grounding, verifiability (BRD-016, SRS-SPEC B.8)
- [ ] **SRS-04**: Render SRS.md byte-identical khi cùng registry input (NFR-005, SRS-SPEC A.5)

### Workflow Runner & Conductor

- [ ] **RUN-01**: Executable workflow runner sở hữu route order, gate orchestration, candidate→canonical promotion (BRD-027)
- [ ] **RUN-02**: Candidate staging dưới `runs/<id>/candidates/`; candidate không tính coverage (BR-007)
- [ ] **RUN-03**: `$ba-deliver run` điều phối srs → flow → mockup → index đúng thứ tự; dừng tại gate fail (BRD-010)
- [ ] **RUN-04**: `$ba-deliver status` cung cấp trạng thái route/gate/artifact có thể kiểm chứng (BRD-011)
- [ ] **RUN-05**: `$ba-deliver resume` tiếp tục từ bước chưa hoàn tất; không promote trùng (BRD-011, US-07)
- [ ] **RUN-06**: Confirmation gate trước overwrite/force rebuild/đổi REQ-ID/publish (BRD-015)

### Artifact Skills (Light Tier)

- [ ] **ART-01**: `$ba-flow` tạo Mermaid inline trong Markdown với frontmatter `req_ids` (BRD-008)
- [ ] **ART-02**: `$ba-mockup` tạo mockup html hoặc wireframe với REQ-ID máy-đọc-được (BRD-009)
- [ ] **ART-03**: Artifact gates kiểm tra req_ids resolve về registry; không orphan reference (BRD-016)

### Coverage & Integrity

- [ ] **COV-01**: Coverage policy theo profile xác định artifact bắt buộc; REQ chỉ `ok` khi đủ và current (BRD-026)
- [ ] **COV-02**: `waived` hiển thị riêng với `ok`; waiver không che stale (BRD-026, BR-006)
- [ ] **COV-03**: Conformance corpus ≥50 mutation; phát hiện ≥49/50; false-green = 0 blocker (BRD §13.4)

### Skills & UX

- [ ] **SKILL-01**: Skill map `$ba-deliver`, `$ba-srs`, `$ba-flow`, `$ba-mockup` với SKILL.md workflow contract (BRD §5.2)
- [ ] **SKILL-02**: Golden path docs BA-facing không yêu cầu gõ `ba-tools` trực tiếp (BRD §17.1)
- [ ] **SKILL-03**: Profile `light` mặc định; tier là single control plane cho ceremony (BRD-028)

### Non-Functional

- [ ] **NFR-01**: Verify/trace/index không gọi renderer/LLM hoàn tất ≤3s @ 200 REQ (NFR-001)
- [ ] **NFR-02**: Core chạy Windows 10+, macOS 12+, Linux; Python 3.11+ (NFR-003)
- [x] **NFR-03**: `ba-tools` zero-network — không HTTP/DNS/telemetry/LLM (NFR-009)
- [ ] **NFR-04**: Artifact và CLI output hỗ trợ UTF-8 tiếng Việt đầy đủ (NFR-008)
- [ ] **NFR-05**: Determinism boundary: CLI không tự suy đoán nghiệp vụ (NFR-006)

## v2 Requirements

Deferred to post-pilot. Tracked but not in current roadmap.

### Standard Tier

- **STD-01**: `$ba-intake` với mode elicit/meeting và analysis package (BRD-005, US-05)
- **STD-02**: Blind critic ≤3 vòng sửa–review (BRD-018)
- **STD-03**: BPMN cơ bản qua `$ba-bpmn` khi profile bật (BRD-012)
- **STD-04**: `analysis_support` bắt buộc trên mọi REQ ở standard+ (SRS-SPEC B.7)

### Strict Tier & Plugins

- **STRICT-01**: `$ba-docx` bundle publishable với manifest hash reproducible (BRD-013)
- **STRICT-02**: `$ba-backlog` INVEST/SPIDR + Jira CSV export (BRD-014)
- **STRICT-03**: Readiness assert per target; human sign-off trong MANIFEST (Appendix C.3)
- **STRICT-04**: ISO 29148 profile extension khi `srs_profile: iso-29148` (SRS-SPEC Part C)

### Team Mode

- **TEAM-01**: Owner folder guard — cross-owner write fail trước mutation (BRD-024)
- **TEAM-02**: `ba-tools report team` read-only aggregate coverage (BRD-025)

## Out of Scope

| Feature | Reason |
|---------|--------|
| SaaS / backend đa người dùng | Local-first v1 (BRD §7.1) |
| Cạnh tranh tốc độ nháp LLM | Harness-first positioning |
| Byte-reproducible LLM prose | Chỉ hash-stable sau accept + freeze |
| OCR / scan ingestion | Source phải text trước intake |
| Screenshot / Pillow render fallback | Chỉ renderer chính thức (BR-002) |
| Agent prose thay gate evidence | Executable runner enforce (R-1) |
| Chỉnh tay INDEX.md | View tái sinh, không phải source of truth |
| Semantic correctness từ INDEX ok | Human sign-off bắt buộc strict |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Pending |
| FOUND-02 | Phase 1 | Pending |
| FOUND-03 | Phase 1 | Complete |
| FOUND-04 | Phase 1 | Pending |
| FOUND-05 | Phase 1 | Pending |
| FOUND-06 | Phase 1 | Pending |
| TRACE-01 | Phase 2 | Pending |
| TRACE-02 | Phase 2 | Pending |
| TRACE-03 | Phase 5 | Pending |
| TRACE-04 | Phase 5 | Pending |
| SRS-01 | Phase 2 | Pending |
| SRS-02 | Phase 2 | Pending |
| SRS-03 | Phase 2 | Pending |
| SRS-04 | Phase 2 | Pending |
| RUN-01 | Phase 3 | Pending |
| RUN-02 | Phase 3 | Pending |
| RUN-03 | Phase 3 | Pending |
| RUN-04 | Phase 3 | Pending |
| RUN-05 | Phase 3 | Pending |
| RUN-06 | Phase 3 | Pending |
| ART-01 | Phase 4 | Pending |
| ART-02 | Phase 4 | Pending |
| ART-03 | Phase 4 | Pending |
| COV-01 | Phase 5 | Pending |
| COV-02 | Phase 5 | Pending |
| COV-03 | Phase 7 | Pending |
| SKILL-01 | Phase 4 | Pending |
| SKILL-02 | Phase 4 | Pending |
| SKILL-03 | Phase 4 | Pending |
| NFR-01 | Phase 7 | Pending |
| NFR-02 | Phase 1 | Pending |
| NFR-03 | Phase 1 | Complete |
| NFR-04 | Phase 1 | Pending |
| NFR-05 | Phase 1 | Pending |

**Coverage:**

- v1 requirements: 34 distinct IDs (header previously noted 35)
- Mapped to phases: 34/34 ✓
- Unmapped: 0

---
*Requirements defined: 2026-07-20*
*Last updated: 2026-07-20 after roadmap creation*
