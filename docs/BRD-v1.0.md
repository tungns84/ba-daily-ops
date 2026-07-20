# BRD — BA Daily Ops

> **Business Requirements Document — v1.0**
> **Ngày:** 2026-07-20 · **Trạng thái:** Product Intent (Ý định sản phẩm) · **Ngôn ngữ:** Tiếng Việt
> **Product slug (canonical):** `ba-daily-ops` · **Tên hiển thị:** BA Daily Ops

---

## 1. Executive Summary (Tóm tắt điều hành)

**BA Daily Ops** biến vòng lặp giao phẩm hằng ngày của Business Analyst — **use case → yêu cầu/SRS → sơ đồ quy trình → mockup UI → chỉ mục truy vết** — thành một quy trình lặp lại được, kiểm chứng được và truy vết được. Mỗi bước là một **skill** hướng người dùng (`$ba-*`) được hậu thuẫn bởi một lớp deterministic (`ba-tools`) và được chặn bởi các cổng chất lượng (gates). Người dùng chỉ cần một lệnh — `$ba-deliver run --uc <slug>` — và **conductor** `$ba-deliver` điều phối toàn bộ chuỗi từ đầu đến cuối.

**Giá trị lõi:** **Truy vết REQ-ID xuyên suốt các giao phẩm.** Xương sống truy vết là **SRS → flow → mockup → (tùy chọn) backlog → INDEX**: một yêu cầu được nhìn thấy nhất quán trên SRS, sơ đồ, mockup và — khi artifact backlog tồn tại — cả backlog, để **drift (lệch chuẩn) lộ ra ngay khi nó xuất hiện**. Backlog là artifact downstream **tùy chọn**, được trace khi có mặt; INDEX hiển thị cột backlog khi artifact tồn tại. Đây là xương sống của sản phẩm: nếu mọi thứ khác thất bại, xương sống truy vết vẫn phải hoạt động.

**Định vị — harness-first:** BA Daily Ops **không** cạnh tranh với ChatGPT/LLM ở tốc độ soạn nháp. Một LLM đơn lẻ vẫn nhanh hơn khi cần một bản nháp rời rạc. Giá trị của sản phẩm nằm ở **khung vận hành quanh** hoạt động soạn thảo: file-state xác định, hash, cổng chất lượng, truy vết REQ-ID và tính di động — những thứ mà một phiên chat LLM không giữ lại được. Ước lượng phân bổ giá trị là **~70% ở harness** và **~30% ở phần soạn thảo của LLM**: LLM đảm nhận phần *phán đoán/soạn thảo*, harness đảm nhận phần *toàn vẹn/tái lập/phát hiện lệch*.

**Cam kết về tính toàn vẹn:** Sản phẩm bảo đảm tính toàn vẹn thông qua **hash, trace và phát hiện drift**, không phải qua việc tái sinh văn bản LLM giống từng byte. Nội dung do agent soạn thảo có thể khác nhau giữa các lần; điều được chứng minh là mối quan hệ giữa source, yêu cầu canonical và các giao phẩm downstream luôn nhất quán và phát hiện được lệch.

---

## 2. Document Control (Kiểm soát tài liệu)

### 2.1 Lịch sử phiên bản

| Phiên bản | Ngày | Trạng thái | Ghi chú |
|-----------|------|-----------|---------|
| 1.0 | 2026-07-20 | Product Intent | Bản gốc. Xác lập ý định sản phẩm và khung yêu cầu. |

### 2.2 Glossary (Định nghĩa chuẩn)

| Thuật ngữ | Định nghĩa |
|-----------|-----------|
| **Skill** | Đơn vị năng lực hướng người dùng, gọi qua tiền tố `$` (ví dụ `$ba-srs`). Đây là thứ BA tương tác trực tiếp. |
| **Conductor** | Skill điều phối chuỗi (`$ba-deliver`) — gọi các skill khác theo đúng thứ tự và theo tier. |
| **Workflow** | Giao thức nội bộ mà một skill thực thi; không hướng người dùng trực tiếp. |
| **Harness** | Bộ khung vận hành = lớp deterministic (`ba-tools`) + file-state + cổng chất lượng. Đảm nhận phần xác định, kiểm chứng được. |
| **REQ-ID** | Mã yêu cầu duy nhất, ổn định qua các lần cập nhật, xuyên suốt mọi giao phẩm. |
| **Drift** | Trạng thái lệch giữa các giao phẩm (hoặc giữa giao phẩm và source) — được phát hiện tự động qua so sánh hash. |
| **Tier** | Mức nghi thức của sản phẩm: `light` \| `standard` \| `strict`. Là bảng điều khiển duy nhất cho coverage, gate và mức ceremony. **`tier` = `profile`**: dùng thay thế cho nhau; `profile` là **tên trường config canonical** (key `profile` trong `.ba-ops/config.json`). |

### 2.3 Phát biểu phạm vi

> BRD v1.0 xác lập **ý định sản phẩm và khung yêu cầu** cho `ba-daily-ops`. Tài liệu này (§1–§7) mô tả *cái gì* và *tại sao* — vấn đề, tầm nhìn, ý niệm sản phẩm, mô hình harness, phạm vi và các user story. Yêu cầu chức năng chi tiết, quy tắc nghiệp vụ và **Acceptance Criteria** được đặc tả ở các mục sau (Acceptance Criteria tại **§11**). Tài liệu không mô tả chi tiết triển khai kỹ thuật.

---

## 3. Business Context & Problem Statement (Bối cảnh & Bài toán)

### 3.1 Bối cảnh

Business Analyst lặp đi lặp lại cùng một chuỗi giao phẩm mỗi ngày: từ một nguồn đầu vào (use case, biên bản họp, brief sản phẩm) họ phải sản xuất SRS/yêu cầu, sơ đồ quy trình, mockup UI và backlog — rồi phải giữ tất cả **nhất quán với nhau**. Trong thực tế:

- Mỗi giao phẩm được tạo trong một công cụ khác nhau (tài liệu, công cụ vẽ, công cụ backlog), không có nguồn sự thật chung.
- Khi một yêu cầu thay đổi, người BA phải cập nhật thủ công ở mọi nơi — SRS, sơ đồ, mockup, backlog. Bỏ sót là điều bình thường.
- **Drift** giữa các giao phẩm xảy ra âm thầm và chỉ bị phát hiện muộn, thường là lúc đã gây hậu quả.
- Việc truy vết "yêu cầu này xuất hiện ở đâu" được làm bằng tay, tốn công, dễ sai.
- Kết quả không tái lập được giữa các máy/người: cùng đầu vào nhưng đầu ra và cách tổ chức khác nhau.

### 3.2 Vì sao một LLM đơn lẻ là chưa đủ

Một LLM có thể soạn nháp rất nhanh, nhưng một phiên chat **không** để lại:

- **File-state bền vững** — không có trạng thái trên đĩa để soi lại, so sánh, kiểm toán.
- **Tính kiểm chứng bằng hash** — không chứng minh được đầu vào/đầu ra nào tương ứng với nhau.
- **Phát hiện drift** — không có cơ chế phát hiện SRS và sơ đồ đã lệch nhau.
- **Xương sống truy vết REQ-ID** — không ràng buộc một yêu cầu qua nhiều giao phẩm.
- **Tính di động & lặp lại** — không tái tạo được cùng cấu trúc trên máy khác.

### 3.3 Phát biểu bài toán

> BA cần một cách để biến vòng lặp giao phẩm hằng ngày thành **quy trình lặp lại được, kiểm chứng được, và truy vết được** — nơi mỗi yêu cầu được nhìn thấy nhất quán trên mọi giao phẩm, và **drift lộ ra ngay khi xuất hiện** — mà không đánh mất tốc độ soạn thảo của LLM.

---

## 4. Vision & Business Objectives (Tầm nhìn & Mục tiêu)

### 4.1 Tầm nhìn

> Biến công việc BA hằng ngày thành một tập **skill** đáng tin cậy: gọi một lệnh, nhận một bộ giao phẩm được kiểm chứng, gắn vào một xương sống truy vết REQ-ID chung — để chất lượng và tính toàn vẹn là **mặc định**, không phải nỗ lực thủ công.

### 4.2 Mục tiêu kinh doanh

| Mã | Mục tiêu | Thước đo giá trị |
|----|----------|------------------|
| **OBJ-1** | Chuẩn hóa vòng lặp giao phẩm BA thành các skill lặp lại được | Cùng đầu vào → cùng cấu trúc giao phẩm, độc lập với người thực hiện |
| **OBJ-2** | Thiết lập xương sống truy vết REQ-ID xuyên suốt SRS → sơ đồ → mockup → (tùy chọn) backlog → INDEX | Mỗi REQ-ID định vị được ở mọi giao phẩm liên quan; backlog được trace khi artifact tồn tại |
| **OBJ-3** | Giảm thời gian tạo bộ giao phẩm và giảm rework | Giảm công cập nhật thủ công khi yêu cầu thay đổi |
| **OBJ-4** | Đảm bảo tính toàn vẹn và phát hiện drift | File-state, hash và trace là thứ *chứng minh được*; drift giữa các giao phẩm bị phát hiện tự động |
| **OBJ-5** | Bảo đảm tính di động giữa máy và runtime | Không hard-code đường dẫn máy; mọi đường dẫn resolve tương đối theo `--repo-root` |
| **OBJ-6** | Cưỡng chế thứ tự thực thi và bảo đảm coverage thật | Chuỗi bước chỉ tiến khi qua gate; chỉ mục truy vết chỉ báo `ok` khi coverage thực sự đủ (không có false-green) |

> **Ghi chú về OBJ-4:** Sản phẩm bảo đảm **tính toàn vẹn và phát hiện drift**, không cam kết đầu ra do LLM sinh ra là tái lập theo byte. Nội dung phán đoán/soạn thảo có thể khác nhau giữa các lần chạy; thứ *chứng minh được* là **file-state, hash và trace** của harness.

### 4.3 Ánh xạ mục tiêu ↔ business goals (OBJ ↔ BG)

Các mục tiêu kinh doanh OBJ-1…OBJ-6 ở §4.2 ánh xạ 1-1 với business goals `BG-01`…`BG-06` được khai báo canonical trong `.ba-ops/business-goals.json`. Bảng này là nguồn ánh xạ chính thức để trace goal xuyên các tài liệu (BRD ↔ SRS ↔ business-goals registry).

| BRD objective | Business goal (`.ba-ops/business-goals.json`) |
|---------------|-----------------------------------------------|
| **OBJ-1** | `BG-01` |
| **OBJ-2** | `BG-02` |
| **OBJ-3** | `BG-03` |
| **OBJ-4** | `BG-04` |
| **OBJ-5** | `BG-05` |
| **OBJ-6** | `BG-06` |

---

## 5. Product Concept (Ý niệm sản phẩm)

### 5.1 Bảng phân tầng (Tier)

Ba tier theo trục **nghi thức (ceremony)**: người dùng chọn mức nặng/nhẹ phù hợp với việc. Tier là bảng điều khiển duy nhất quyết định coverage policy, các gate được bật và mức ceremony.

| Tier | Nghi thức | Sơ đồ | Cổng readiness | Delivery | Team governance |
|------|-----------|-------|----------------|----------|-----------------|
| **light** | Thấp | Flow inline (`$ba-flow`) | verify / lint | Markdown / inline | Không |
| **standard** | Vừa | + critic + BPMN cơ bản (tùy chọn) | Readiness cơ bản | Markdown | Tùy chọn |
| **strict** | Cao | BPMN đầy đủ + readiness | Readiness đầy đủ | DOCX (`$ba-docx`) | Có |

> Golden path mặc định chạy ở tier **light** với đúng **một lệnh người dùng**. Tier cao hơn thêm chiều sâu phân tích, review độc lập và kiểm soát phát hành nghiêm ngặt hơn — nhưng không thay đổi mô hình một-lệnh dành cho BA.

### 5.2 Bản đồ skill (Skill map)

Mỗi bước trong vòng lặp là một skill hướng người dùng. `$ba-deliver` là conductor điều phối toàn bộ chuỗi; các skill còn lại có thể được conductor gọi tự động hoặc BA gọi riêng khi cần.

| Bước trong vòng lặp | Skill (canonical) |
|---------------------|-------------------|
| Điều phối use case đầu-cuối (conductor) | `$ba-deliver` |
| Thu thập / chuẩn hóa đầu vào (intake) | `$ba-intake` |
| Yêu cầu / SRS | `$ba-srs` |
| Sơ đồ quy trình nhẹ (flow inline) | `$ba-flow` |
| Sơ đồ BPMN đầy đủ | `$ba-bpmn` |
| Mockup UI | `$ba-mockup` |
| Backlog / stories (Jira-ready) | `$ba-backlog` |
| Xuất bản DOCX cho khách | `$ba-docx` |

> Lớp deterministic `ba-tools` là hạ tầng nội bộ mà các skill gọi để thực hiện thao tác file/hash/trace. BA không cần gõ `ba-tools` trực tiếp trong golden path.

### 5.3 Nguyên tắc sản phẩm (Product principles)

- **Xương sống truy vết là trung tâm.** Truy vết REQ-ID xuyên suốt các giao phẩm là giá trị lõi; mọi thành phần khác phục vụ nó.
- **Ranh giới xác định là ranh giới cứng.** `ba-tools` chỉ làm việc file/command/hash chứng minh được; agent/LLM sở hữu toàn bộ phân tích, diễn giải và phán đoán. Hai vai không lẫn vào nhau.
- **Toàn vẹn được chứng minh, không được giả định.** File-state, hash và trace là bằng chứng; tuyên bố "đã đạt" của agent không thay thế được cổng chất lượng.
- **Coverage phải là thật.** Chỉ mục truy vết chỉ báo `ok` khi mọi artifact bắt buộc theo tier thực sự tồn tại, current và đã qua gate — không có báo xanh giả.
- **Nghi thức tương xứng với việc.** Tier cho phép chọn mức ceremony phù hợp; task nhỏ không phải gánh nghi thức nặng.
- **Di động theo thiết kế.** Mọi đường dẫn resolve theo `--repo-root`; không hard-code path máy — cùng repo chạy được trên máy khác.
- **Một lệnh cho người dùng.** BA bàn giao một use case qua một lệnh `$ba-deliver run --uc <slug>`; sự phức tạp nằm trong harness, không nằm ở người dùng.

---

## 6. Harness Model (Mô hình harness)

### 6.1 Điểm mạnh

- **File-state xác định, kiểm chứng bằng hash** — mọi giao phẩm có trạng thái trên đĩa để soi lại, so sánh và kiểm toán.
- **Xương sống truy vết REQ-ID** — ràng buộc một yêu cầu qua nhiều giao phẩm; là nền tảng phát hiện drift.
- **Ranh giới xác định** — `ba-tools` chỉ làm việc file/command/hash (provable); agent sở hữu toàn bộ phân tích/phán đoán. Đây là ranh giới cứng, tạo nên độ tin cậy.
- **Cưỡng chế thứ tự và gate** — chuỗi bước chỉ tiến khi bước trước qua gate; không thể bỏ qua kiểm tra bằng cách khẳng định "đã pass" trong văn xuôi.
- **Coverage policy chống false-green** — chỉ mục truy vết chỉ báo `ok` khi coverage thực sự đủ theo tier.
- **Tính di động** — không hard-code đường dẫn máy; mọi thứ resolve theo `--repo-root`.
- **Hợp đồng đầu ra CLI** — mỗi thành công in JSON UTF-8; mỗi lỗi thoát mã 2. Dễ tự động hóa, dễ kiểm toán.

### 6.2 Lý do thiết kế (Design rationale)

- **Vì sao tách phần provable khỏi phần judgment?** Vì đó là cách duy nhất để một hệ có LLM vẫn cho ra kết quả *kiểm toán được*. Harness không phán đoán nghiệp vụ; nó chỉ chứng minh mối quan hệ giữa các file. Nhờ vậy, chất lượng phán đoán do agent tạo ra luôn được đặt cạnh bằng chứng cơ học độc lập.
- **Vì sao cần một runner cưỡng chế thứ tự?** Vì nếu tin vào việc agent tự chạy đúng trình tự, một bước bị bỏ qua sẽ âm thầm phá vỡ truy vết. Harness sở hữu thứ tự bước, việc gọi gate và promotion từ candidate sang canonical — biến "làm đúng thứ tự" thành đặc tính của hệ thống chứ không phải của người dùng.
- **Vì sao coverage policy theo tier?** Vì "đủ" phụ thuộc bối cảnh: task nhỏ và bàn giao cho khách có nghĩa vụ khác nhau. Policy theo tier cho phép một định nghĩa coverage rõ ràng, kiểm chứng được, thay vì hard-code một pipeline cho mọi dự án.
- **Vì sao toàn vẹn thay cho tái lập byte?** Vì văn bản LLM vốn không tất định, và ép nó tái lập byte là mục tiêu sai. Điều thực sự có giá trị — và khả thi — là chứng minh rằng source, yêu cầu và giao phẩm luôn ăn khớp, và bất kỳ lệch nào cũng lộ ra ngay.
- **Vì sao harness-first (70/30)?** Vì phần soạn thảo của LLM có thể thay thế và ngày càng rẻ; phần tạo ra khác biệt bền vững là khung vận hành quanh nó. Do đó đầu tư ưu tiên vào file-state, gate, truy vết và tính di động — không chạy đua tốc độ nháp.

---

## 7. Scope, Stakeholders, Personas & User Stories

### 7.1 Phạm vi

**Trong phạm vi (In scope):**

- Vòng lặp giao phẩm BA: intake → SRS → sơ đồ → mockup → backlog → chỉ mục/truy vết.
- Xương sống truy vết REQ-ID xuyên suốt các giao phẩm.
- File-state xác định, hash, cổng chất lượng và phát hiện drift.
- Tập skill `$ba-*` hướng người dùng và các workflow nội bộ tương ứng.
- Phân tầng tier (`light` / `standard` / `strict`), cưỡng chế thứ tự thực thi và coverage policy.
- Golden path một lệnh cho người dùng và cơ chế resume.

**Ngoài phạm vi (Out of scope):**

- Cạnh tranh tốc độ soạn nháp với ChatGPT/LLM đơn lẻ.
- Cam kết tái lập theo byte cho nội dung do LLM sinh ra.
- Backend đa người dùng / SaaS chung; sản phẩm là local-first.
- Trích xuất từ scan/ảnh (OCR phải làm trước, không thuộc trách nhiệm skill).

### 7.2 Stakeholders (Bên liên quan)

| Bên liên quan | Quan tâm chính |
|---------------|----------------|
| Business Analyst (người dùng chính) | Tạo giao phẩm nhanh, nhất quán, truy vết được |
| Trưởng nhóm BA / Lead | Nhìn coverage xuyên nhiều BA mà không phá vòng lặp hằng ngày của họ |
| Khách hàng / bên nhận giao phẩm | Nhận tài liệu (ví dụ DOCX) chỉn chu, nhất quán |
| Đội kỹ thuật / dev tiếp nhận yêu cầu | Backlog Jira-ready, REQ-ID rõ ràng, ít drift |

### 7.3 Personas

- **BA bận việc (task nhỏ):** cần đầu ra nhanh, nghi thức nhẹ; phù hợp tier **light**.
- **BA phân tích chuẩn (giao phẩm cho dự án):** cần SRS + sơ đồ + backlog nhất quán; phù hợp tier **standard**.
- **BA/Lead giao phẩm cho khách (chính thức):** cần DOCX, readiness đầy đủ, quản trị nhóm; phù hợp tier **strict**.

### 7.4 User Stories

| Mã | User story | Tier |
|----|-----------|------|
| **US-01** | Là một BA, tôi muốn từ một use case tạo ra SRS có REQ-ID để làm nguồn sự thật cho các giao phẩm sau. | mọi tier |
| **US-02** | Là một BA, tôi muốn mỗi REQ-ID được truy vết xuyên suốt SRS → sơ đồ → mockup → (tùy chọn) backlog → INDEX để drift lộ ra ngay; INDEX hiển thị cột backlog khi artifact backlog tồn tại. | mọi tier |
| **US-03** | Là một BA, tôi muốn bàn giao một use case bằng **đúng một lệnh** `$ba-deliver run --uc <slug>`, để không phải nhớ và gõ từng bước. | mọi tier |
| **US-04** | Là một BA làm **task nhỏ**, tôi muốn tier **light** được chấp nhận qua **verify/lint** (không bắt buộc critic) để không phải gánh nghi thức nặng. | light |
| **US-05** | Là một BA phân tích chuẩn, tôi muốn thêm intake, critic và BPMN cơ bản khi cần chiều sâu. | standard |
| **US-06** | Là một BA/Lead giao phẩm cho khách, tôi muốn readiness đầy đủ, xuất DOCX và quản trị nhóm. | strict |
| **US-07** | Là một BA, tôi muốn nếu quá trình bị dừng giữa chừng thì `$ba-deliver resume` tiếp tục đúng bước còn dở, không chạy lại hay ghi đè bước đã hoàn tất. | mọi tier |
| **US-08** | Là một Lead, tôi muốn chỉ mục truy vết chỉ báo `ok` khi coverage thực sự đủ — không có báo xanh giả — để tin được RTM khi duyệt handoff. | mọi tier |

---

## 8. Functional Requirements

Các từ **PHẢI**, **KHÔNG ĐƯỢC** và **CHỈ** biểu thị yêu cầu bắt buộc.

### 8.A. Traceability

**BRD-001 — REQ-ID ổn định**

Hệ thống PHẢI cấp một REQ-ID duy nhất cho mỗi yêu cầu trong phạm vi dự án hoặc team. REQ-ID PHẢI được giữ nguyên khi chỉnh sửa nội dung; việc split, merge, đổi tên hoặc ngừng sử dụng ID PHẢI là thao tác có chủ đích và lưu được lịch sử ánh xạ.

**BRD-002 — Metadata truy vết máy đọc được**

Mọi artifact downstream PHẢI khai báo `req_ids` theo định dạng máy đọc được: trường cấu trúc trong JSON, frontmatter trong Markdown, và metadata hoặc comment theo contract trong HTML. Artifact hoặc policy tham chiếu REQ-ID không tồn tại trong registry canonical PHẢI bị báo là `orphan`.

**BRD-003 — RTM và INDEX**

Hệ thống PHẢI sinh `.ba-ops/INDEX.md` từ registry canonical và trace records, thể hiện chuỗi:

`REQ-ID → SRS ($ba-srs) → flow/BPMN ($ba-flow/$ba-bpmn) → mockup ($ba-mockup) → (optional backlog) ($ba-backlog) → DOCX ($ba-docx)`

Cột backlog CHỈ hiển thị khi artifact backlog tồn tại; backlog là artifact downstream tùy chọn và KHÔNG ĐƯỢC coi là nghĩa vụ coverage bắt buộc ở tier `light`.

INDEX PHẢI hiển thị các trạng thái `ok`, `gap`, `orphan`, `stale` và `waived` theo coverage policy. INDEX PHẢI là view có thể tái sinh và KHÔNG ĐƯỢC chỉnh tay như nguồn sự thật. Mục `orphan` được lập từ các `req_ids` trong artifact hoặc trace record **không resolve** được về registry canonical; các entry orphan được liệt kê ở mục orphan riêng của INDEX (không phải dòng registry thường).

**BRD-004 — Phát hiện drift**

Hệ thống PHẢI ghi và so sánh hash của source, yêu cầu canonical, gate evidence và artifact liên quan. Khi hash hiện tại không khớp trace hoặc manifest, artifact PHẢI chuyển sang `stale`, nêu rõ nguyên nhân và KHÔNG ĐƯỢC tính là coverage hợp lệ cho đến khi được tạo lại và qua gate.

### 8.B. Skills

**BRD-005 — Intake tùy chọn**

`$ba-intake` PHẢI chuẩn hóa source thô, biên bản họp hoặc brief mơ hồ thành analysis package chứa evidence, decision, stakeholder, assumption và câu hỏi mở. `$ba-intake` PHẢI hỗ trợ hai chế độ intake qua `--mode elicit|meeting`: `elicit` cho khai vấn/brief chủ động, `meeting` cho biên bản họp. Conductor PHẢI cho phép bỏ qua intake khi source đã đạt readiness, nhưng KHÔNG ĐƯỢC hạ thấp các gate downstream.

**BRD-006 — Phân tích SRS**

`$ba-srs` PHẢI chuyển source thành các yêu cầu nguyên tử, có căn cứ và kiểm thử được trong `requirements.json`, rồi render `SRS.md` theo cấu trúc IEEE-830. `requirements.json` PHẢI là nguồn canonical; SRS Markdown KHÔNG ĐƯỢC tự tạo thêm yêu cầu ngoài registry.

Mỗi yêu cầu PHẢI mang một trạng thái xuất xứ: `stated` hoặc `derived`. Yêu cầu `stated` PHẢI có citation (theo BRD-007). Yêu cầu `derived` — suy ra từ phân tích chứ không trích trực tiếp từ source — PHẢI mang `analysis_support` ở tier `standard` trở lên để chứng minh căn cứ suy luận. Chi tiết ngữ nghĩa `stated`/`derived` và `analysis_support` theo SRS-SPEC Part B.4.

**BRD-007 — Citation-exists**

Mỗi yêu cầu có trạng thái `stated` PHẢI có `source_trace` xác định tài liệu nguồn, phạm vi section khi áp dụng và đoạn trích nguyên văn dài tối thiểu 12 ký tự. Đoạn trích PHẢI là substring chính xác trong phạm vi đã khai báo; citation không hợp lệ PHẢI làm gate thất bại với exit code `2` và liệt kê các REQ-ID vi phạm.

**BRD-008 — Flow nhẹ**

`$ba-flow` PHẢI hỗ trợ Mermaid inline trong artifact Markdown có frontmatter `req_ids`. Route author KHÔNG ĐƯỢC phụ thuộc Mermaid CLI; việc render PNG hoặc SVG PHẢI là tùy chọn và CHỈ được thực hiện bằng renderer chính thức.

**BRD-009 — Mockup**

`$ba-mockup` PHẢI yêu cầu fidelity rõ ràng là `html` hoặc `wireframe`. HTML PHẢI là file tĩnh tự chứa; wireframe PHẢI là Markdown có cấu trúc; cả hai PHẢI mang REQ-ID máy đọc được và KHÔNG ĐƯỢC tham chiếu yêu cầu ngoài registry.

**BRD-010 — Deliver conductor**

`$ba-deliver` PHẢI cung cấp một điểm vào duy nhất để điều phối `$ba-srs`, `$ba-flow`, `$ba-mockup`, trace, INDEX và các plugin được policy yêu cầu. `$ba-deliver run` PHẢI thực hiện các route đúng thứ tự và chỉ chuyển bước sau khi gate trước đạt; khi gate thất bại, conductor PHẢI dừng, giữ state có thể resume và KHÔNG ĐƯỢC đánh dấu workflow hoàn tất.

**BRD-011 — Status và resume**

`$ba-deliver status` PHẢI cung cấp trạng thái bền, có thể kiểm chứng của từng route, gate và artifact. `$ba-deliver resume` PHẢI tiếp tục từ bước chưa hoàn tất đầu tiên và KHÔNG ĐƯỢC chạy lại hoặc ghi đè artifact đã hoàn tất khi input và hash không thay đổi.

### 8.C. Plugins

**BRD-012 — BPMN**

`$ba-bpmn` PHẢI nhận logical model không chứa tọa độ, kiểm tra semantics, tạo layout, chạy presentation gate và xuất bằng draw.io CLI chính thức. Thiếu renderer, lỗi semantic hoặc lỗi geometry PHẢI làm export thất bại; plugin KHÔNG ĐƯỢC thay thế bằng screenshot hoặc renderer tổng hợp.

**BRD-013 — DOCX delivery**

`$ba-docx` PHẢI tạo bundle bàn giao từ các artifact đã qua gate, thay đúng media placeholder, kiểm tra nội dung nhúng và ghi manifest hash sau cùng. Bundle CHỈ được đánh dấu publishable khi mọi artifact đầu vào còn current.

**BRD-014 — Backlog grooming**

`$ba-backlog` PHẢI tạo story theo INVEST/SPIDR, lưu phán đoán MoSCoW có căn cứ trong `stories.json`, tạo view và xuất Jira-ready CSV. Agent hoặc con người PHẢI chịu trách nhiệm về phán đoán nghiệp vụ; CLI CHỈ được kiểm tra schema, REQ-ID, trace và định dạng export.

### 8.D. Gates

**BRD-015 — Confirmation gate**

Hệ thống PHẢI yêu cầu xác nhận trước mọi thao tác có thể làm mất hoặc thay đổi bản canonical, gồm overwrite, force rebuild, đổi REQ-ID và publish bundle. Không có xác nhận hợp lệ thì KHÔNG ĐƯỢC ghi byte.

**BRD-016 — Gate chất lượng artifact**

Mỗi skill PHẢI có gate phù hợp với loại artifact, gồm atomicity, ambiguity, grounding, verifiability, citation-exists, schema và trace khi áp dụng. Kết quả gate PHẢI có evidence máy đọc được; tuyên bố của agent KHÔNG ĐƯỢC thay thế kết quả gate.

**BRD-017 — Gate an toàn render**

Mọi path đầu vào và đầu ra PHẢI được resolve trong repo root. Render CHỈ được sử dụng CLI chính thức đã khai báo; path traversal, symlink escape, renderer không xác định hoặc output không khớp manifest PHẢI làm thao tác thất bại trước publish.

**BRD-018 — Blind critic**

Khi profile hoặc policy yêu cầu review nâng cao, hệ thống PHẢI sử dụng critic độc lập theo rubric và không dựa vào lời tự giải thích của author. Hệ thống CHỈ được tự động điều phối tối đa ba vòng sửa–review; vấn đề còn mở sau vòng cuối PHẢI được chuyển cho con người.

### 8.E. Harness và runtime — nền tảng

**BRD-019 — Doctor**

`ba-tools doctor` PHẢI kiểm tra Python, UTF-8, cấu trúc repo và các dependency tùy chọn như Node, Mermaid CLI và draw.io. Kết quả PHẢI phân biệt dependency bắt buộc với dependency theo plugin và cung cấp hướng khắc phục cụ thể.

**BRD-020 — Installer portable**

Sản phẩm PHẢI cung cấp installer một lệnh cho Windows và shell tương thích POSIX. Installer KHÔNG ĐƯỢC ghi path máy tác giả vào config, PHẢI hỗ trợ path có khoảng trắng và PHẢI xác minh installation trước khi báo thành công.

**BRD-021 — File-state bền**

State nghiệp vụ PHẢI được lưu trong `.ba-ops/` dưới dạng text hoặc JSON có thể inspect và commit vào Git. Việc xóa lịch sử chat hoặc khởi động lại runtime KHÔNG ĐƯỢC làm mất artifact, trace hoặc state đã ghi thành công.

**BRD-022 — CLI output contract**

Mọi lệnh `ba-tools` thành công PHẢI ghi đúng một JSON UTF-8 ra stdout. Mọi `BaToolsError` PHẢI ghi JSON lỗi có cấu trúc ra stderr và kết thúc với exit code `2`; traceback, secret hoặc absolute path nhạy cảm KHÔNG ĐƯỢC rò rỉ trong lỗi ngoài dự kiến.

### 8.F. Team mode

**BRD-023 — Một owner folder cho mỗi REQ**

Mỗi yêu cầu PHẢI thuộc đúng một owner folder. Shared requirement vẫn PHẢI có một owner canonical; các root khác CHỈ được tham chiếu và KHÔNG ĐƯỢC tạo bản canonical cạnh tranh.

**BRD-024 — Chặn ghi cross-owner**

Mọi lệnh ghi PHẢI kiểm tra `owner_id` trước mutation. Owner không khớp PHẢI làm thao tác thất bại trước khi ghi byte, kể cả khi target path tồn tại và người dùng có quyền hệ điều hành.

**BRD-025 — Team report read-only**

Lead hoặc shared root PHẢI có thể tổng hợp coverage trên các root được khai báo rõ trong `team.roots`. Team report CHỈ được đọc và tổng hợp trạng thái; KHÔNG ĐƯỢC sửa state, trace hoặc artifact của owner root.

### 8.G. Harness và runtime — chính sách và điều phối

**BRD-026 — Coverage policy theo profile**

Hệ thống PHẢI áp dụng coverage policy máy đọc được theo profile và từng REQ-ID để xác định artifact bắt buộc, tính áp dụng và waiver; sự tồn tại của một artifact downstream bất kỳ KHÔNG ĐƯỢC xem là đủ coverage. Một REQ-ID CHỈ được đánh dấu `ok` khi mọi artifact bắt buộc và applicable đều current, hợp lệ và đã qua gate. Mọi loại trừ hoặc waiver PHẢI được khai báo rõ, có lý do và thẩm quyền phù hợp; waiver KHÔNG ĐƯỢC che giấu artifact `stale`. INDEX và status PHẢI sử dụng các ngữ nghĩa sau:

- `ok`: mọi nghĩa vụ coverage đều được đáp ứng bằng artifact current đã qua gate.
- `gap`: thiếu ít nhất một artifact bắt buộc và applicable mà không có waiver hợp lệ.
- `orphan`: artifact hoặc policy tham chiếu REQ-ID không tồn tại trong registry canonical.
- `stale`: artifact tồn tại nhưng source, statement, artifact hoặc gate hash không còn khớp.
- `waived`: không còn `gap` hoặc `stale`, nhưng ít nhất một nghĩa vụ bắt buộc được miễn bằng waiver hợp lệ; `waived` KHÔNG ĐƯỢC hiển thị thành `ok`.

**BRD-027 — Executable workflow runner**

Hệ thống PHẢI có executable workflow runner đứng sau `$ba-deliver`; runner PHẢI là thành phần duy nhất sở hữu việc chọn và sắp thứ tự route, gọi và diễn giải gate, cùng việc promote candidate thành canonical. Agent CHỈ được tạo candidate; candidate KHÔNG ĐƯỢC tính coverage, dùng downstream hoặc publish trước khi runner xác nhận gate và promote nguyên tử. Gate thất bại hoặc process gián đoạn PHẢI giữ nguyên canonical đã được chấp nhận, lưu state có thể resume và CHỈ cập nhật trace, INDEX hoặc manifest sau promotion thành công.

**BRD-028 — Profile trong config**

`.ba-ops/config.json` PHẢI khai báo `profile` với đúng một giá trị thuộc enum `light | standard | strict`: `light` cho spine tối thiểu, `standard` cho workflow cân bằng, và `strict` cho readiness, coverage cùng kiểm soát publish đầy đủ. Initializer và preflight PHẢI từ chối profile thiếu hoặc không hợp lệ; workflow PHẢI áp dụng gate và coverage policy tương ứng với profile đã chọn.

## 9. Non-Functional Requirements

**NFR-001 — Hiệu năng kiểm chứng**

Các thao tác verify, trace và index không gọi renderer hoặc LLM PHẢI hoàn tất trong tối đa 3 giây với dự án ở mốc **tham chiếu 200 REQ** trên môi trường tham chiếu. Thời gian xử lý PHẢI tăng tuyến tính hợp lý theo số requirement và trace record; ở quy mô tối đa theo giả định (**500 REQ**, §12.2), thời gian dự kiến vẫn nằm trong giới hạn **~8 giây** theo scaling tuyến tính. 3 giây là ngưỡng ở mốc tham chiếu 200 REQ, không phải trần tuyệt đối cho mọi quy mô.

**NFR-002 — Khả dụng của golden path**

Một use case có source đầy đủ PHẢI có thể được giao qua **đúng một lệnh người dùng** — `$ba-deliver run` — không yêu cầu BA thao tác trực tiếp với CAS, hash hoặc state nội bộ. Vòng "đọc INDEX → sửa gap" là bước **remediation riêng** khi coverage chưa đủ; nó KHÔNG được tính vào số lệnh golden path. Sau onboarding, median time-to-first-UC PHẢI đạt mục tiêu tối đa 60 phút.

**NFR-003 — Portability**

Core PHẢI chạy trên Windows 10+, macOS 12+ và Linux với Python 3.11+. Mọi path nghiệp vụ PHẢI được resolve tương đối với repo root; subprocess Python PHẢI dùng `sys.executable`.

**NFR-004 — Cấu hình di động**

Config được commit KHÔNG ĐƯỢC chứa absolute path, home directory hoặc credential máy cục bộ. Đường dẫn dependency tùy chỉnh PHẢI đến từ flag, biến môi trường hoặc cấu hình local không commit.

**NFR-005 — Hash stability**

Với cùng input bytes, config, phiên bản tool và canonical serialization, output tất định do CLI tạo và canonical JSON đã freeze PHẢI có cùng bytes và SHA-256 trên mọi nền tảng được hỗ trợ. Timestamp không mang ý nghĩa nghiệp vụ PHẢI được loại bỏ hoặc chuẩn hóa khỏi vùng hash. Cam kết này KHÔNG áp dụng cho văn xuôi do LLM đang sinh; prose CHỈ trở thành hash-stable sau khi được chấp nhận, canonical hóa và freeze.

**NFR-006 — Determinism boundary**

`ba-tools` CHỈ được thực hiện thao tác có thể chứng minh bằng file, command, schema, gate hoặc hash. Phán đoán về nghiệp vụ, MoSCoW, stakeholder impact và chất lượng diễn đạt PHẢI thuộc agent hoặc con người và được lưu dưới dạng evidence; CLI KHÔNG ĐƯỢC tự suy đoán.

**NFR-007 — Byte budget**

Tài liệu eager-loaded, workflow prompt và skill reference PHẢI vừa với ngân sách context của runtime host; build PHẢI cảnh báo hoặc thất bại khi vượt ngưỡng do host công bố.


**NFR-008 — Ngôn ngữ và encoding**

Artifact, template và output CLI PHẢI hỗ trợ đầy đủ tiếng Việt UTF-8. Runtime Windows PHẢI được kiểm tra ở chế độ UTF-8; ký tự tiếng Việt KHÔNG ĐƯỢC biến dạng hoặc escape ngoài yêu cầu của định dạng JSON.

**NFR-009 — Bảo mật và chính sách mạng**

- **`ba-tools` zero-network:** `ba-tools` KHÔNG ĐƯỢC gọi HTTP, DNS, telemetry hoặc LLM. Renderer PHẢI là process local đã cài; cài dependency có sử dụng mạng PHẢI là hành động installer riêng và có sự đồng ý của người dùng.
- **Chính sách LLM runtime:** Runtime agent PHẢI tuân thủ chính sách triển khai của tổ chức và công bố provider, phạm vi dữ liệu cùng chế độ retention trước khi xử lý source nhạy cảm. Sản phẩm KHÔNG ĐƯỢC tuyên bố dữ liệu không rời repo khi sử dụng cloud LLM.

Mọi file access PHẢI bị giới hạn trong repo root và chống path traversal.

**NFR-010 — Tính sẵn sàng và phục hồi**

Mọi write operation PHẢI dùng lock và atomic replace. Crash KHÔNG ĐƯỢC để lại canonical nửa ghi; resume PHẢI phục hồi từ state hoặc journal gần nhất, phát hiện lock stale và bảo toàn mọi artifact đã promote thành công.

## 10. Business Rules

**BR-001 — REQ-ID là định danh bền**

Một REQ-ID CHỈ được có một bản canonical trong phạm vi dự án hoặc team. Chỉnh câu chữ KHÔNG ĐƯỢC tạo ID mới; split, merge, đổi tên hoặc ngừng sử dụng PHẢI có lịch sử rõ ràng.

**BR-002 — Render phải có nguồn gốc chính thức**

Artifact nhị phân CHỈ được bàn giao với trạng thái đã render khi renderer chính thức chạy thành công và output khớp manifest. Mermaid inline được phép bàn giao dạng text khi profile không yêu cầu render.

**BR-003 — DOCX thay placeholder**

Hình trong DOCX PHẢI thay đúng placeholder hoặc relationship đã khai báo. `$ba-docx` KHÔNG ĐƯỢC append ảnh ở cuối tài liệu để giả lập việc thay media.

**BR-004 — Stale không được publish**

Artifact `stale` KHÔNG ĐƯỢC đưa vào bundle bàn giao. Source không đổi KHÔNG đủ để coi artifact current nếu statement, analysis, gate hoặc artifact hash đã thay đổi.

**BR-005 — Không ghi cross-owner**

Owner CHỈ được ghi vào owner root của mình. Mọi write cross-owner PHẢI thất bại trước mutation; lead CHỈ được tổng hợp read-only nếu chưa có quy trình chuyển owner được phê duyệt.

**BR-006 — Profile quyết định nghĩa vụ**

Profile và coverage policy PHẢI quyết định artifact cùng gate bắt buộc; hệ thống KHÔNG ĐƯỢC hard-code một pipeline cho mọi dự án. Profile không khớp policy PHẢI hard-fail, và `waived` KHÔNG ĐƯỢC đổi nhãn thành `ok`.

**BR-007 — Candidate không phải canonical**

Candidate KHÔNG ĐƯỢC tính coverage, đưa vào INDEX canonical hoặc sử dụng để publish. CHỈ workflow runner được promote candidate sau khi gate đạt; promotion PHẢI nguyên tử và có evidence.

**BR-008 — Con người chịu trách nhiệm phê duyệt cuối**

Hash, schema và gate CHỈ chứng minh tính toàn vẹn cơ học, không chứng minh yêu cầu đúng nghiệp vụ. Bundle cuối PHẢI có phê duyệt của người có thẩm quyền; hệ thống KHÔNG ĐƯỢC tự suy ra semantic correctness từ trạng thái `ok`.

## 11. Acceptance Criteria

### 11.1. BRD-007 — Citation-exists

#### AC-BRD-007-01 — Citation hợp lệ

**Given**

- Workflow đang ở route SRS.
- `FR-001` có trạng thái `stated`.
- Citation xác định source, section và đoạn trích nguyên văn dài ít nhất 12 ký tự.
- Đoạn trích xuất hiện chính xác trong section đã khai báo.

**When**

- BA chạy `$ba-deliver run`.

**Then**

- Citation gate của `FR-001` đạt.
- Gate evidence ghi nhận REQ-ID, source scope và source hash.
- `$ba-deliver status` không báo citation blocker cho `FR-001`.
- Workflow được phép chuyển sang bước kế tiếp.

#### AC-BRD-007-02 — Citation không hợp lệ

**Given**

- Một requirement `stated` có đoạn trích dưới 12 ký tự, không xuất hiện chính xác, hoặc chỉ xuất hiện ngoài section đã khai báo.

**When**

- BA chạy `$ba-deliver run`.

**Then**

- Citation gate thất bại và kết quả liệt kê REQ-ID cùng nguyên nhân.
- Requirement candidate không được promote.
- Các route downstream không được bắt đầu.
- `$ba-deliver status` chỉ rõ route bị chặn.
- Hệ thống không được tự thay citation bằng nội dung gần giống.

### 11.2. BRD-003 — RTM và INDEX

#### AC-BRD-003-01 — Sinh INDEX tất định

**Given**

- Registry chứa các REQ-ID hợp lệ.
- Artifact có metadata `req_ids`, trace record, gate pass và hash current.
- Coverage policy đã được xác định.

**When**

- `$ba-deliver run` hoàn tất các route bắt buộc.

**Then**

- `.ba-ops/INDEX.md` được sinh theo thứ tự REQ-ID ổn định.
- Mỗi REQ-ID liên kết đến đúng artifact đã trace.
- Mỗi dòng hiển thị trạng thái coverage theo policy.
- Tái sinh với cùng snapshot đầu vào tạo cùng nội dung và hash INDEX.

#### AC-BRD-003-02 — Phân loại vấn đề truy vết

**Given**

- `FR-002` thiếu một artifact bắt buộc.
- Một artifact tham chiếu `REQ-999` không tồn tại trong registry (orphan ID chỉ xuất hiện trong trace record của artifact, không phải một dòng registry).
- Trace của `FR-003` chứa hash cũ.
- `FR-004` có waiver hợp lệ cho nghĩa vụ còn thiếu.

**When**

- BA chạy `$ba-deliver run` rồi `$ba-deliver status`.

**Then**

- `FR-002` được báo `gap`.
- `REQ-999` được báo `orphan`.
- `FR-003` được báo `stale`.
- `FR-004` được báo `waived`, không phải `ok`.
- INDEX chỉ rõ artifact kind hoặc trace record gây ra từng vấn đề.

### 11.3. BRD-026 — Coverage policy

#### AC-BRD-026-01 — Chống false-green

**Given**

- Policy yêu cầu SRS, flow và mockup cho `FR-010`.
- SRS và flow current, nhưng mockup chưa tồn tại.
- Không có loại trừ hoặc waiver hợp lệ cho mockup.

**When**

- BA chạy `$ba-deliver run` và xem `$ba-deliver status`.

**Then**

- `FR-010` được đánh dấu `gap`.
- Status xác định mockup là nghĩa vụ còn thiếu.
- Sự tồn tại của SRS và flow không được làm trạng thái thành `ok`.

#### AC-BRD-026-02 — Applicability và waiver

**Given**

- Mockup được khai báo không áp dụng cho `FR-011` kèm lý do.
- `FR-011` đáp ứng mọi nghĩa vụ còn lại.
- `FR-012` vẫn cần mockup nhưng có waiver hợp lệ, còn hạn và được phê duyệt.

**When**

- BA chạy `$ba-deliver run` rồi `$ba-deliver status`.

**Then**

- `FR-011` được đánh dấu `ok`, còn mockup được hiển thị là không áp dụng.
- `FR-012` được hiển thị là `waived`, không phải `ok`.
- Khi waiver hết hạn, lần đánh giá tiếp theo phải chuyển `FR-012` thành `gap`.

#### AC-BRD-026-03 — Stale và orphan

**Given**

- Artifact của `FR-013` có hash không khớp trace.
- Một artifact khác tham chiếu `REQ-999`.
- `FR-013` có waiver cho cùng artifact kind.

**When**

- BA chạy `$ba-deliver status`.

**Then**

- `FR-013` được báo `stale`.
- `REQ-999` được báo `orphan`.
- Waiver không được che trạng thái `stale`.
- Không trường hợp nào được hiển thị thành `ok`.

### 11.4. BRD-027 — Executable workflow runner

#### AC-BRD-027-01 — Runner sở hữu thứ tự route

**Given**

- Policy xác định thứ tự `SRS → flow → mockup → INDEX`.
- Route SRS chưa được promote.

**When**

- BA chạy `$ba-deliver run`.

**Then**

- Runner CHỈ mở route SRS làm bước hiện hành.
- Flow và mockup không được promote hoặc tính coverage.
- `$ba-deliver status` báo SRS là route hiện hành và giữ snapshot profile cùng policy.

#### AC-BRD-027-02 — Gate thất bại giữ nguyên canonical

**Given**

- Canonical SRS có hash `H0`.
- Candidate SRS không đạt citation gate.

**When**

- `$ba-deliver run` đánh giá candidate.

**Then**

- Canonical SRS vẫn có hash `H0`.
- Trace, INDEX và manifest canonical không được cập nhật từ candidate.
- Workflow dừng trước các route downstream.
- `$ba-deliver status` báo gate thất bại và evidence cần sửa.

#### AC-BRD-027-03 — Resume không promote trùng

**Given**

- Candidate đã qua gate và được promote nguyên tử.
- Process bị gián đoạn trước khi bắt đầu route kế tiếp.

**When**

- BA chạy `$ba-deliver resume`.

**Then**

- Runner phục hồi từ state hoặc journal đã lưu.
- Route vừa hoàn tất không được chạy hoặc promote lần thứ hai.
- Workflow tiếp tục từ route hợp lệ kế tiếp.
- `$ba-deliver status` hiển thị đúng canonical hash và gate evidence đã chấp nhận.

### 11.5. BRD-010 — Deliver conductor

#### AC-BRD-010-01 — Golden path một điểm vào

**Given**

- Source chứa use case rõ ràng và citation hợp lệ.
- Coverage policy yêu cầu SRS, flow và mockup.
- Fidelity mockup là `html`.
- Các plugin tùy chọn không áp dụng.
- Repo đã qua preflight.

**When**

- BA gọi `$ba-deliver run` một lần.

**Then**

- Conductor điều phối `$ba-srs`, `$ba-flow`, `$ba-mockup`, trace và INDEX đúng thứ tự.
- Mỗi route đạt gate trước khi route kế tiếp bắt đầu.
- Artifact cuối mang đúng REQ-ID máy đọc được.
- `$ba-deliver status` CHỈ báo hoàn tất khi không còn blocker theo policy.

#### AC-BRD-010-02 — Dừng tại gate lỗi

**Given**

- Route SRS đã đạt gate.
- Candidate flow không hợp lệ.

**When**

- BA chạy `$ba-deliver run`.

**Then**

- Workflow dừng tại route flow.
- Mockup và các route sau không được đánh dấu hoàn tất.
- SRS đã đạt không bị ghi đè.
- `$ba-deliver status` chỉ rõ route lỗi và gate evidence cần xử lý.

#### AC-BRD-010-03 — Tiếp tục từ điểm dừng

**Given**

- Workflow đang dừng tại route flow.
- Input và hash SRS không thay đổi.
- Candidate flow đã được sửa để đạt gate.

**When**

- BA chạy `$ba-deliver resume`.

**Then**

- Conductor tiếp tục từ route flow.
- Route SRS không được chạy lại.
- Các route còn lại được thực hiện theo thứ tự và gate tương ứng.
- Sau khi coverage đạt policy, INDEX được cập nhật và `$ba-deliver status` báo hoàn tất.

### 11.6. BRD-004 — Phát hiện drift

#### AC-BRD-004-01 — Drift chuyển artifact sang `stale` và loại khỏi coverage

**Given**

- `FR-020` đã có SRS, flow và mockup current, đã qua gate và được trace với hash khớp.
- Sau đó source hoặc statement của `FR-020` bị sửa, làm hash hiện tại không khớp trace/manifest.

**When**

- BA chạy `$ba-deliver status` (hoặc `$ba-deliver run`).

**Then**

- Artifact liên quan của `FR-020` được báo `stale`, nêu rõ nguyên nhân (hash nào không khớp).
- `FR-020` KHÔNG được tính là coverage hợp lệ và KHÔNG được hiển thị `ok`.
- Trạng thái `stale` được giữ cho đến khi artifact được tạo lại và qua gate; chỉ khi đó `FR-020` mới có thể trở lại `ok`.

### 11.7. BRD-024 — Chặn ghi cross-owner

#### AC-BRD-024-01 — Ghi cross-owner thất bại, không ghi byte

**Given**

- Owner root có `owner_id = "ba-alice"` trong `.ba-ops/config.json`.
- Một lệnh ghi được gọi với `owner_id` không khớp (ví dụ `--owner ba-bob`) nhắm vào artifact của `FR-021`.
- Người dùng có quyền hệ điều hành trên target path, kể cả khi path đã tồn tại.

**When**

- BA chạy lệnh mutate của `ba-tools` (ví dụ qua `$ba-deliver run`).

**Then**

- Lệnh kiểm tra `owner_id` **trước** mutation và thất bại với exit code `2`.
- **Không byte nào** được ghi vào target path (zero-byte write); canonical hiện có không đổi.
- Lỗi JSON có cấu trúc nêu rõ owner mismatch và không rò rỉ absolute path nhạy cảm.

### 11.8. BRD-015 — Confirmation gate

#### AC-BRD-015-01 — Xác nhận trước khi overwrite canonical

**Given**

- Canonical SRS của `FR-022` đã tồn tại và current.
- BA khởi động một thao tác có thể làm mất/đổi canonical (overwrite, force rebuild, đổi REQ-ID hoặc publish bundle).

**When**

- Thao tác chạy nhưng chưa có xác nhận hợp lệ từ người dùng.

**Then**

- Hệ thống yêu cầu xác nhận và **KHÔNG** ghi byte trước khi có xác nhận hợp lệ.
- Nếu xác nhận bị từ chối hoặc thiếu, canonical của `FR-022` giữ nguyên hash cũ, không mutation.
- Chỉ khi có xác nhận hợp lệ, thao tác mới tiến hành ghi và cập nhật trace/manifest tương ứng.

---

## 12. Constraints, Assumptions, Dependencies

### 12.1 Ràng buộc (Constraints)

- **Runtime:** chat-skill runtime + `ba-tools` CLI deterministic. Skill được kích hoạt trong một chat runtime bất kỳ hỗ trợ agent skill; `ba-tools` chạy như một CLI Python thuần, độc lập với runtime chat. Không lệ thuộc một sản phẩm chat runtime cụ thể ở tầng BRD.[^1]
- **Ngôn ngữ CLI:** Python 3.11+ (yêu cầu `hashlib.file_digest` cho streaming SHA-256). Giải Python interpreter qua `sys.executable`, **cấm** hard-code path máy tác giả.
- **Render backend chính thức:** draw.io Desktop CLI (BPMN) + `@mermaid-js/mermaid-cli` (`mmdc`) (Mermaid render). **Cấm** Pillow / screenshot / SVG converter tổng hợp thay thế — render giả không được tính là render.
- **Determinism boundary (ranh giới cứng):** `ba-tools` chỉ thực hiện thao tác file / command / schema / gate / hash **chứng minh được**. Phán đoán nghiệp vụ, phân tích, MoSCoW, stakeholder impact, chất lượng diễn đạt thuộc agent LLM hoặc con người và được lưu dưới dạng evidence — CLI **không** tự suy đoán.
- **Byte budget:** tài liệu eager-loaded, workflow prompt và skill reference phải **vừa với ngân sách context của runtime host** hiện dùng; build cảnh báo hoặc thất bại khi vượt ngưỡng do host công bố. Không hard-code một con số tuyệt đối ở tầng BRD.
- **Portability:** cấm absolute path và home directory trong config commit; mọi path nghiệp vụ resolve tương đối theo `--repo-root` (git root / cwd). Path dependency tùy chỉnh chỉ đến từ flag, env var, hoặc local config không commit.
- **CLI I/O contract:** thành công → **đúng một** JSON UTF-8 ra stdout; `BaToolsError` → JSON lỗi có cấu trúc ra stderr + exit code `2`. Cảnh báo đi stderr, **không** phá vỡ stdout JSON.
- **Zero-network cho `ba-tools`:** core CLI không gọi HTTP, DNS, telemetry, hoặc LLM. Renderer là process local đã cài. Runtime LLM policy tách rời và thuộc trách nhiệm triển khai của tổ chức (xem NFR-009).
- **Local-only ở v1:** không SaaS, không backend đa người dùng chia sẻ, không server chung. State nằm trong `.ba-ops/` được commit vào Git của chính project.

[^1]: v1 hiện được cấu hình cho một chat skill runtime cụ thể; hợp đồng skill (SKILL.md frontmatter, discovery, workflow contract) được thiết kế runtime-neutral để có thể porting mà không đổi CLI hay file-state.

### 12.2 Giả định (Assumptions)

1. BA có quyền cài Python 3.11+, Node.js 18+ LTS, và draw.io Desktop trên máy làm việc (khi cần plugin BPMN/DOCX).
2. Source dạng text (Markdown / DOCX text / plain UTF-8); scan hoặc ảnh phải được OCR **trước khi** đưa vào intake — không phải trách nhiệm của skill BA.
3. Mỗi project BA có repo Git riêng để commit thư mục `.ba-ops/`.
4. Quy mô tiêu biểu mỗi project: ≤ 500 REQ, ≤ 50 UC / milestone, ≤ 5 BA cùng thao tác (team mode).
5. Đầu ra tiếng Việt là mặc định cho artifact BA-facing; CLI flag, JSON key, exit code giữ tiếng Anh để ổn định script và CI.
6. BA Lead có quyền chọn profile tier cho project — hệ thống **không** auto-detect tier từ source.
7. Người dùng đầu — chính (BA) — chấp nhận vòng "gõ lệnh → đọc INDEX → sửa gap" như luồng làm việc chính; harness không cố che dấu vòng lặp này.

### 12.3 Phụ thuộc (Dependencies)

| Thành phần | Version tối thiểu | Bắt buộc khi |
|------------|-------------------|--------------|
| Python | 3.11+ | Luôn (chạy `ba-tools`) |
| filelock | 3.x (PyPI) | Luôn (cross-platform state lock) |
| git | 2.x+ | Luôn (commit `.ba-ops/`) |
| Chat skill runtime host | Runtime hỗ trợ agent skill với file-state | Luôn (chạy skill `$ba-*`) |
| Node.js | 18+ LTS | Khi bật export Mermaid hoặc plugin BPMN |
| @mermaid-js/mermaid-cli (`mmdc`) | 11.15+ | Route render Mermaid PNG / SVG |
| draw.io Desktop | Stable hiện hành | Plugin BPMN + plugin DOCX (khi có sơ đồ nhúng) |
| python-docx | 1.2.0+ | Plugin DOCX bàn giao |

**Nguyên tắc phụ thuộc:** thiếu dependency không bắt buộc → skill/plugin liên quan hard-fail sớm với hướng dẫn cài đặt cụ thể, **không** fallback im lặng sang render tổng hợp.

---

## 13. Success Criteria & KPIs

### 13.1 Bối cảnh pilot

- **Quy mô:** 1–2 BA, 10 UC (5 source sạch + 5 source messy), khung thời gian 2 tuần.
- **Nguyên tắc đo:** với `n ≤ 2` người dùng, **mọi tỷ lệ phần trăm** ("≥ 90 % BA…", "≥ 80 % stakeholder acceptance") là **vanity KPI** và không được dùng làm chỉ báo phát hành. Chỉ báo cáo **raw count** dạng `m/n` và **so cặp có kiểm soát** (cùng BA, cùng source, harness vs ad-hoc).
- **Baseline:** mỗi BA làm 3 UC ad-hoc (LLM chat + template quen thuộc) **trước khi** bật harness, để có mốc so cặp trên cùng con người và cùng nguyên liệu.
- **Golden path đo:** đúng **1 lệnh người dùng** — `$ba-deliver run --uc <slug>`. Các lệnh `doctor`, `setup`, `init` là one-off và **không tính** vào golden path count.

### 13.2 KPI theo tier — `light`

| KPI | Đo bằng | Ngưỡng pilot |
|-----|---------|--------------|
| Golden path command count | Số lệnh user gõ để bàn giao 1 UC (loại `doctor` / `init`) | **= 1** |
| Time-to-first-UC | Từ lúc gõ lệnh đến khi `INDEX.md` xanh, không còn gap/orphan/stale cho REQ của UC | Báo cáo raw phút từng UC; mục tiêu median ≤ 60 phút |
| Số UC bàn giao được | Raw count trên tổng 10 | ≥ 8/10 |
| Baseline paired — cycle time | Cặp harness vs ad-hoc, **cùng BA, cùng source** | Raw diff phút cho từng cặp |
| Baseline paired — rework sau UAT | Số REQ phải sửa sau PO review | Raw count từng cặp |
| RTM completeness | 0 gap / 0 orphan / 0 stale sau handoff | 10/10 UC |
| Citation-exists integrity | Số REQ `stated` không tìm được span ≥ 12 ký tự | **= 0** |
| Resume reliability | Kill giữa chừng rồi `$ba-deliver resume` | 10/10 lần recover đúng bước |

### 13.3 KPI theo tier — `strict`

| KPI | Đo bằng | Ngưỡng pilot |
|-----|---------|--------------|
| Số bundle publishable | DOCX + `MANIFEST.json` + SRS + render đầy đủ, strict-gate pass | ≥ 3/10 UC (subset chỉ định) |
| Strict-gate first-pass | Raw count UC qua strict-gate lần đầu (không retry) | Báo `m/n`, không ngưỡng cứng |
| Manifest reproducibility | Chạy lại trên máy thứ 2 → hash text artifact khớp | 3/3 UC subset |
| Coverage policy false-green | Số lần `INDEX` báo `ok` nhưng thiếu artifact bắt buộc theo policy | **= 0** — blocker phát hành |
| Cross-machine portability | Mở repo trên máy thứ 2, không edit config → chạy được | 2/2 máy |

### 13.4 Conformance corpus (drift detection)

- **Corpus:** ≥ **50 seeded mutation** trên input đã cố định — mỗi mutation là một loại drift đã biết: đổi 1 chữ trong source, xóa 1 REQ khỏi registry, đổi hash file, rename mockup, sửa `req_ids` trong Mermaid frontmatter, đổi tên REQ-ID không qua migration, thêm citation không tồn tại, thay ảnh trong DOCX bằng append thay vì rId replace, v.v.
- **Chạy:** trước pilot (baseline), sau pilot, và **mỗi lần release CLI mới** (regression suite).
- **Ngưỡng phát hành:** phát hiện ≥ **49/50** mutation; `false-green = 0`. False-green là **blocker phát hành** — không thương lượng, không waiver.

### 13.5 Điều kiện mở rộng khỏi pilot

Đủ **tất cả** các điều kiện sau:

1. Golden path duy trì `= 1` lệnh trên ≥ 8/10 UC pilot.
2. Conformance corpus ≥ 49/50 và `false-green = 0`.
3. Baseline paired: harness **không tệ hơn** ad-hoc về cycle time trên UC source sạch, **và** giảm rework đo được trên UC source messy.
4. BA Lead xác nhận (định tính, phỏng vấn cấu trúc) rằng RTM một trang đủ tin để duyệt handoff cho dev.
5. Cross-machine portability: 2/2 máy khác nhau tái sản xuất được bundle strict với hash text khớp.

---

## 14. Risks & Mitigations

| ID | Rủi ro | Ảnh hưởng | Giảm thiểu |
|----|--------|-----------|------------|
| R-1 | **LLM bỏ gate** — agent tự viết prose "đã pass" mà không thực sự gọi gate | Chất lượng giả, false confidence | Executable runner (BRD-027) enforce state transition ở tầng CLI; gate failure → exit `2`; skill workflow **phải** gọi `ba-tools` để bước tiến, không có đường vòng bằng lời. |
| R-2 | **False-green RTM** — `INDEX` báo `ok` nhưng thiếu artifact bắt buộc theo policy | Handoff lỗi lọt xuống dev / khách | Coverage policy theo profile (BRD-026); conformance corpus ≥ 50 mutation; blocker phát hành nếu false-green > 0. |
| R-3 | **Doc drift** — tài liệu (BRD, DESIGN, SKILL) lệch code CLI thực tế theo thời gian | Onboarding hiểu sai, BA gõ sai lệnh, mất niềm tin | Sinh docs tham chiếu từ CLI `--help`; single source of truth cho tên skill, route, exit code; định kỳ so khớp doc-vs-help và cảnh báo trong review checklist. |
| R-4 | **draw.io không cài được** trên máy có chính sách hạn chế install | Không dùng được plugin BPMN / DOCX render | Plugin opt-in; tier `light` chỉ cần Mermaid inline; hard-fail sớm với hướng dẫn install rõ ràng; không fallback screenshot. |
| R-5 | **Windows friction** — UTF-8 mặc định, PATH cho Python/Node, khoảng trắng trong đường dẫn | Setup > 30 phút; BA bỏ cuộc trước khi thấy giá trị | `ba-tools doctor` preflight; installer PowerShell chuyên biệt; `PYTHONUTF8=1` mặc định; test matrix Windows / macOS / Linux ở mỗi release. |
| R-6 | **BA ngại CLI** — người dùng chính là BA, không phải developer | Adoption thấp, harness bị bỏ | Bọc CLI trong skill chat; `default_prompt` sẵn; BA chỉ gõ `$ba-deliver run`; docs BA-facing không nói "ba-tools" ở golden path. |
| R-7 | **Source scan / ảnh không đọc được** — DOCX binary, PDF ảnh, chưa OCR | REQ bị bịa; citation không tồn tại | `doctor` cảnh báo file không extract được; yêu cầu OCR trước; citation-exists gate hard-fail exit `2` khi không tìm span nguyên văn. |
| R-8 | **State corruption song song** — 2 BA edit cùng folder | Mất trace, ghi đè canonical | Team mode owner-folder guard (BRD-023/024); `filelock` trên `STATE.md`; cross-owner write fail trước byte đầu tiên. |
| R-9 | **Runtime host thay đổi** — chat skill runtime bump API, đổi discovery | Skill hỏng nhưng CLI vẫn chạy | `.ba-ops/` file-state runtime-agnostic; CLI không depend runtime; hợp đồng skill cô lập trong `SKILL.md` để migrate cục bộ. |
| R-10 | **"Hash = correctness" fallacy** — user tin `INDEX` xanh là nghiệp vụ đúng | Ra quyết định dựa trên toàn vẹn cơ học, không phải đúng đắn semantic | Docs nhấn: hash = provenance + drift detection, **không** phải semantic correctness; human sign-off bắt buộc trong DoD ở `strict`; UAT có kiểm soát ở mọi tier. |
| R-11 | **Ceremony sneak-back** — nghi thức nặng bị vô tình thêm vào tier `light` qua các release | Golden path phình lên > 1 lệnh, adoption giảm | Profile tier là **single control plane** cho ceremony; regression test: `light` phải giữ `= 1` lệnh và **không** trigger readiness / critic / analysis assert. |
| R-12 | **Kỳ vọng sai** về "byte-reproducible LLM output" | Stakeholder đòi thứ sản phẩm không cam kết | Nhấn OBJ-4 và NFR-005: hash-stable chỉ áp cho CLI-produced và canonical-frozen; LLM prose là candidate, chỉ hash-stable sau khi accept + freeze. |

---

## 15. Versioning & Release Discipline

### 15.1 Nguyên tắc versioning

- **SemVer cho `ba-tools` CLI:** `MAJOR.MINOR.PATCH`.
  - `MAJOR` bump khi đổi CLI I/O contract (stdout JSON schema, exit-code semantics), đổi file-state layout `.ba-ops/`, hoặc đổi determinism boundary.
  - `MINOR` bump khi thêm route, thêm skill, thêm gate mới mà **không** phá hợp đồng cũ.
  - `PATCH` bump cho bug fix và cải thiện thông báo lỗi.
- **`schema_version` cho file-state:** `.ba-ops/config.json`, `.ba-ops/coverage-policy.json`, `.ba-ops/business-goals.json`, và các JSON canonical khác trong `.ba-ops/` **PHẢI** mang trường `schema_version` (integer, bắt buộc, không default ẩn).
  - CLI đọc file có `schema_version` không hỗ trợ → exit `2` với thông báo cụ thể ("cần bump `ba-tools`" hoặc "cần chạy migrate").
  - **Ngoại lệ — `requirements.json`:** `.ba-ops/srs/<slug>/requirements.json` được versioned **bên ngoài** qua URN `urn:ba-daily-ops:schema:requirements:v1` (theo SRS-SPEC B.1) và **KHÔNG** yêu cầu trường `schema_version` inline. Việc bump schema của registry yêu cầu được thực hiện bằng cách đổi URN version, không phải bằng trường inline. Các JSON canonical khác trong `.ba-ops/` vẫn giữ nguyên yêu cầu `schema_version` inline như trên.
- **Đồng bộ tài liệu:** BRD, DESIGN, và tag git của CLI release cùng nhịp — BRD v`X.Y` khớp `ba-tools` v`X.Y.z`.

### 15.2 Cửa sổ hỗ trợ

- Mỗi `MAJOR` được hỗ trợ ít nhất **2 MINOR** trước khi ngưng nhận PATCH.
- File-state phiên bản cũ có công cụ đọc-chỉ (read-only) để chạy `report team` cross-version; **cấm** ghi cross-version mà không migrate.

### 15.3 Release gate

Trước mỗi release CLI:

1. Conformance corpus (13.4) chạy đầy đủ; `false-green = 0`, phát hiện ≥ 49/50.
2. Test matrix Windows / macOS / Linux qua trên Python 3.11 và 3.12.
3. Docs generated từ `--help` khớp docs commit (doc-vs-help check).
4. Changelog liệt kê breaking change (nếu `MAJOR` bump) và schema bump (nếu có).

---

## 16. Governance & Team Mode

### 16.1 Mô hình quản trị

BA Daily Ops là công cụ **project-local**, không có server chung; quản trị được thực thi qua **file-state có commit vào Git** và các cơ chế guard ở tầng CLI. Không có admin console, không có RBAC ở tầng ứng dụng.

### 16.2 Owner folder

- Mỗi requirement thuộc **đúng một** owner folder (một BA hoặc một nhánh phân tích cụ thể).
- Folder có `owner_id` trong `.ba-ops/config.json`; mọi lệnh mutate của `ba-tools` **PHẢI** kiểm tra `--owner` khớp `owner_id` trước khi ghi byte đầu tiên.
- Owner không khớp → exit `2`, không mutation, kể cả khi user có quyền hệ điều hành trên file.
- **Golden path không cần `--owner` tường minh:** conductor `$ba-deliver` **PHẢI** tự resolve `owner_id` từ `.ba-ops/config.json` và truyền xuống các lệnh `ba-tools`, để golden path vẫn giữ đúng `$ba-deliver run --uc <slug>` (một lệnh) ngay cả ở team mode. `--owner` chỉ cần khi ghi đè owner mặc định một cách có chủ đích.

### 16.3 Team roots và report

- BA Lead / shared root có thể khai báo `team.roots` trong config của root chia sẻ, liệt kê **đường dẫn tương đối** đến các owner root khác.
- `ba-tools --repo-root shared report team` chạy **read-only**: đọc trace, tổng hợp coverage, in JSON — **không** sửa state, trace, hoặc artifact của owner root nào.
- Cross-folder trace write bị chặn ở tầng CLI trước mutation.

### 16.4 Trách nhiệm phê duyệt

- **Hash, schema, gate** chứng minh **tính toàn vẹn cơ học** — không chứng minh yêu cầu đúng nghiệp vụ.
- Bundle bàn giao (`strict`) **PHẢI** có human sign-off của người có thẩm quyền (mặc định BA Lead) — hệ thống ghi tên/ID người sign-off vào `MANIFEST.json`.
- `INDEX` báo `ok` là điều kiện **cần**, không phải điều kiện **đủ**, cho publish.

### 16.5 Chính sách waiver

- Waiver cho coverage policy được ghi trong `coverage-policy.json` (schema ở BRD-026).
- Mỗi waiver **PHẢI** có: lý do, người duyệt, thời điểm duyệt, thời hạn (hoặc `null` với ghi chú lý do vĩnh viễn).
- Waiver hết hạn tự động chuyển REQ liên quan sang `gap`; không được auto-renew.
- `waived` luôn hiển thị **riêng** với `ok` trong INDEX; **cấm** đổi nhãn `waived` thành `ok` ở view tổng hợp.

---

## 17. Glossary

### 17.1 Canonical names

Bảng tên chính thức cho v1.0. Là **tên duy nhất** dùng trong docs, CI, script, và giao tiếp với người dùng.

| Layer | Canonical | Ghi chú |
|-------|-----------|---------|
| **Product slug** | `ba-daily-ops` | Tên repo, package, folder docs |
| **Product display** | BA Daily Ops | Văn xuôi tiếng Việt / tiếng Anh |
| **Skill — conductor** | `deliver` (`$ba-deliver`) | Điều phối one-command UC end-to-end |
| **Skill — SRS** | `srs` (`$ba-srs`) | Bóc REQ từ source, render `SRS.md` |
| **Skill — Mermaid** | `flow` (`$ba-flow`) | Sơ đồ inline trong Markdown |
| **Skill — BPMN** | `bpmn` (`$ba-bpmn`) | Plugin BPMN qua draw.io |
| **Skill — mockup** | `mockup` (`$ba-mockup`) | Fidelity `html` \| `wireframe` |
| **Skill — intake** | `intake` (`$ba-intake`) | Normalize source / meeting note; `--mode elicit\|meeting` |
| **Skill — backlog** | `backlog` (`$ba-backlog`) | INVEST + SPIDR + Jira CSV |
| **Skill — DOCX** | `docx` (`$ba-docx`) | Plugin bàn giao DOCX |
| **Route mặc định** | `run` | Mọi skill có route default là `run` |
| **Profile — nhẹ** | `light` | Mặc định; golden path `= 1` lệnh |
| **Profile — trung** | `standard` | Bật intake + critic + BPMN cơ bản |
| **Profile — nghiêm** | `strict` | Publishable, DOCX, coverage đầy đủ |
| **Agent role (nội bộ)** | `role-*` | `role-critic`, `role-lint`, `role-cite`… — không expose ra golden path |
| **Namespace CLI** | `ba-tools <cmd>` | Deterministic layer cho script / CI / skill nội bộ |
| **Namespace chat** | `$ba-<skill> <route>` | User-facing trong chat runtime |

**Quy tắc namespace:**

- `$ba-<skill>` = BA-facing trong chat runtime. Chỉ skill được chat-trigger qua `$`-prefix.
- `ba-tools <cmd>` = CLI deterministic cho script, CI, và skill workflow nội bộ. **Không** xuất hiện ở golden path docs cho BA.
- **Cấm** viết `$ba-tools ...` (nhầm với CLI).
- **Cấm** viết `ba-<skill>` trần trong chat guide (thiếu `$`, nhầm với CLI).

### 17.2 Glossary of terms

| Thuật ngữ | Định nghĩa |
|-----------|------------|
| **Skill** | Đơn vị năng lực chat-triggerable qua `$ba-<name>`. Cấu tạo: `SKILL.md` + workflow contract + gate + (có thể) gọi `ba-tools`. Là lớp năng lực **duy nhất** BA-facing. |
| **Route** | Chế độ chạy của một skill (`run`, `render`, `resume`, `status`, …). Route mặc định là `run`. |
| **`ba-tools`** | CLI Python deterministic. **Không** phải skill; **không** chat-triggerable qua `$`. |
| **Conductor** | Skill điều phối chuỗi (canonical: `deliver`). Gọi các skill khác đúng thứ tự theo profile tier. |
| **REQ-ID** | Mã yêu cầu duy nhất, ổn định qua các lần cập nhật, xuyên artifact. Split / merge / rename chỉ qua migration có chủ đích. |
| **RTM (Requirements Traceability Matrix) / `INDEX.md`** | Ma trận `REQ → SRS § → sơ đồ → mockup → story → DOCX`. Sinh lại từ registry + trace, không sửa tay. Nguồn phát hiện gap / orphan / stale. |
| **Gap** | REQ tồn tại trong registry nhưng thiếu artifact downstream bắt buộc theo coverage policy hiện hành. |
| **Orphan** | Artifact hoặc trace tham chiếu REQ-ID không tồn tại trong registry canonical. |
| **Stale** | Source, statement, artifact, hoặc gate hash đã đổi kể từ lần trace ghi; artifact cần rebuild và qua gate lại. |
| **Waived** | Kind bắt buộc bị miễn bởi waiver hợp lệ, chưa hết hạn. Hiển thị **riêng** với `ok`; không tính là coverage đầy đủ. |
| **Citation-exists** | Gate: mọi REQ `stated` phải có span nguyên văn ≥ 12 ký tự trong section source đã khai báo. Chống bịa cấp rẻ và hiệu quả. |
| **Coverage policy** | Bộ artifact bắt buộc theo profile và theo REQ trước khi `INDEX` được coi là `ok`. Nguồn quyết định chống false-green. |
| **Gate** | Điểm kiểm bắt buộc trước hoặc sau bước quan trọng. Fail → exit `2`, không bàn giao. Evidence gate là máy-đọc-được; lời tự tuyên bố của agent **không** thay thế được gate. |
| **Determinism boundary** | Ranh giới cứng: `ba-tools` = file / command / schema / hash **provable**; agent LLM = analysis / authoring / judgement. Không nhượng bộ. |
| **Profile tier** | `light` \| `standard` \| `strict`. Single control plane cho coverage policy, gate bật, mức ceremony. **`tier` và `profile` là đồng nghĩa**; `profile` là tên trường config canonical (`profile` trong `.ba-ops/config.json`). |
| **Analysis package** | `.ba-ops/analysis/<slug>/` — evidence source-normalized (decision, stakeholder, assumption, question). Optional ở `light`, bắt buộc ở `strict`. |
| **Handoff-ready** | Trạng thái đủ chuyển sang dev nội bộ: `INDEX` không có gap / orphan / stale cho REQ của UC, các gate bắt buộc theo tier hiện hành đã pass. Áp dụng cho `light` và `standard`. |
| **Publishable** | Trạng thái đủ bàn giao ra ngoài dự án (khách hàng, audit): strict-gate pass, `MANIFEST.json` với hash reproducible cross-machine, human sign-off có trong manifest. Chỉ áp dụng cho `strict`. |
| **Executable runner** | Component enforce route / gate / state transition ở tầng CLI; đảm bảo LLM **không** bỏ gate bằng prose. Sở hữu duy nhất việc promote candidate → canonical. |
| **Candidate vs canonical** | Candidate = artifact agent viết vào vùng staging, chưa qua gate. Canonical = artifact runner đã promote sau khi gate pass. Candidate **không** tính coverage. |
| **Manifest hash** | SHA-256 của tập text artifact bàn giao (+ metadata render binaries) ghi trong `MANIFEST.json`. Nền tảng của tính reproducibility. |
| **Owner folder** | Folder có `owner_id`. Chỉ owner được write; các bên khác đọc qua `report team`. |
| **Golden path** | Luồng bàn giao **đúng 1 lệnh** người dùng cho tier `light`: `$ba-deliver run --uc <slug>`. Không tính lệnh setup one-off. |

---

## 18. Appendices

### Appendix A — Golden path (luồng bàn giao 1 lệnh)

```
┌────────────────────────────────────────────────────────────────┐
│  Source (UC snippet / brief / meeting note)                    │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
              $ba-deliver run --uc <slug> --fidelity html
                               │
       ┌───────────────────────┼───────────────────────┐
       │       (skill nội bộ, BA không phải gõ)        │
       ▼                       ▼                       ▼
   $ba-srs run             $ba-flow run           $ba-mockup run
       │                       │                       │
       └───────────────────────┴───────────────────────┘
                               │
                               ▼
                     ba-tools index (auto)
                               │
                               ▼
                   INDEX.md  →  đọc, fix nếu gap
                               │
                               ▼
                            Handoff
```

**Setup one-off** (không tính vào golden path count): `ba-tools doctor` + `ba-tools init`.

**Diễn giải:** BA gõ **đúng một lệnh** — `$ba-deliver run`. Conductor `deliver` gọi lần lượt `srs` → `flow` → `mockup`, mỗi bước qua gate trước bước kế tiếp, cuối cùng `ba-tools index` cập nhật RTM. BA đọc `INDEX.md`, sửa các gap còn lại (nếu có), rồi handoff.

### Appendix B — Cấu trúc `.ba-ops/` (mức logic)

```
.ba-ops/
├── PROJECT.md               # metadata dự án
├── REQUIREMENTS.md          # rendered view của registry (spine)
├── INDEX.md                 # RTM một trang, sinh lại từ trace
├── STATE.md                 # phiên / UC đang mở, cursor resume
├── config.json              # schema_version, profile, owner_id, team.roots?
├── business-goals.json      # schema_version + registry BG-01…BG-06 (ánh xạ OBJ↔BG, §4.3)
├── coverage-policy.json     # required_artifact_kinds + per_req + waivers
├── MANIFEST.json            # hash bundle bàn giao (strict)
│
├── srs/<slug>/              # requirements.json + SRS.md
├── mermaid/<slug>/          # inline .md (+ export/ nếu render PNG/SVG)
├── mockup/<slug>/           # .html hoặc .md wireframe
│
├── analysis/<slug>/         # optional ở light, bắt buộc ở strict
│   ├── source-normalized.md
│   ├── evidence.json
│   └── readiness.json
│
├── runs/<run-id>/           # executable runner journal + candidates
│   ├── plan.json
│   ├── journal.jsonl
│   └── candidates/<step-id>/
│
└── plugins/
    ├── bpmn/<slug>/         # model.json + export/ + quality.json
    ├── docx/<slug>/         # rendered.docx + manifest.json
    └── backlog/<slug>/      # stories.json + jira.csv
```

**Nguyên tắc:** mọi path trong sơ đồ trên đều tương đối `--repo-root`. Không có absolute path ở bất kỳ file commit nào.

### Appendix C — Definition of Done theo tier

**C.1 — `light` (một UC hoàn tất)**

- [ ] `requirements.json` + `SRS.md` — `ba-tools verify` pass; citation-exists 100 % cho REQ `stated`.
- [ ] Mermaid inline trong Markdown — `req_ids` khai báo trong frontmatter.
- [ ] Mockup (`html` **hoặc** `wireframe`) — `req_ids` gắn máy-đọc-được trên artifact.
- [ ] `INDEX.md` — 0 gap / 0 orphan / 0 stale cho REQ thuộc UC.
- [ ] `$ba-deliver status` báo hoàn tất.
- [ ] Human UAT: BA đọc lại toàn bộ và tick checkbox trong workflow trước khi coi là handoff-ready.

**C.2 — `standard` (một UC hoàn tất)** — thêm vào C.1:

- [ ] Intake artifact (`elicit` hoặc `meeting`) trong `.ba-ops/analysis/<slug>/`.
- [ ] Critic (blind, theo rubric) ≤ 3 vòng sửa–review — log pass ghi trong `STATE.md`; vấn đề còn mở sau vòng cuối chuyển cho con người, **không** tự động coi là đạt.
- [ ] BPMN cơ bản (nếu profile bật) — semantic + presentation gate pass.

**C.3 — `strict` (một UC hoàn tất, publishable)** — thêm vào C.2:

- [ ] `analysis/<slug>/readiness.json` — assert-readiness pass cho **mỗi** target thuộc phạm vi (`srs`, `mermaid`, `bpmn`, `mockup`, `backlog`, `docx` nếu bật).
- [ ] Coverage policy `strict` — `INDEX` `ok` với **toàn bộ** artifact bắt buộc; 0 waiver đang che gap.
- [ ] `MANIFEST.json` — hash text artifact reproducible trên máy thứ 2 (test cross-machine).
- [ ] DOCX bàn giao (nếu bật plugin) — media rId thay đúng chỗ (không append ảnh mới ở cuối); manifest ghi sau cùng.
- [ ] Human sign-off từ BA Lead (hoặc người có thẩm quyền tương đương) — tên/ID ghi vào `MANIFEST.json`.

### Appendix D — Ma trận Artifact × Tier

Ký hiệu: `✓` = bắt buộc; `○` = optional; `—` = không áp dụng.

| Artifact / Gate | `light` | `standard` | `strict` |
|-----------------|:-------:|:----------:|:--------:|
| `requirements.json` | ✓ | ✓ | ✓ |
| `SRS.md` (rendered view) | ✓ | ✓ | ✓ |
| Citation-exists gate | ✓ | ✓ | ✓ |
| Mermaid inline (spine sơ đồ) | ✓ | ✓ | ✓ |
| Mermaid export PNG / SVG | ○ | ○ | ✓ |
| Mockup (`html` \| `wireframe`) | ✓ | ✓ | ✓ |
| `INDEX.md` RTM | ✓ | ✓ | ✓ |
| Coverage policy áp dụng | `light` | `standard` | `strict` |
| Analysis package (`analysis/<slug>/`) | ○ | ✓ | ✓ |
| `readiness.json` (assert-readiness per target) | — | ○ | ✓ |
| Intake artifact (`elicit` / `meeting`) | ○ | ✓ | ✓ |
| Critic (blind, ≤ 3 vòng) | ○ | ✓ | ✓ |
| Plugin BPMN | — | ○ | ✓ (khi client yêu cầu) |
| Plugin DOCX bàn giao | — | ○ | ✓ (khi client yêu cầu) |
| Backlog grooming + Jira CSV | ○ | ○ | ○ |
| `MANIFEST.json` reproducible cross-machine | — | ○ | ✓ |
| Team owner-folder guard | ○ | ○ | ✓ |
| Human sign-off (BA Lead) | ○ | ○ | ✓ |
| Golden path `= 1` lệnh | ✓ | (không ràng buộc) | (không ràng buộc) |

### Appendix E — References

Chuẩn và tài liệu tham chiếu chuyên môn được dùng để định hình yêu cầu và gate của sản phẩm.

- **IEEE 830-1998** — *Recommended Practice for Software Requirements Specifications*. Khung cho cấu trúc `SRS.md`.
- **ISO/IEC/IEEE 29148:2018** — *Systems and software engineering — Life cycle processes — Requirements engineering*. Optional cho hợp đồng yêu cầu chuẩn cao hơn IEEE 830; v1.0 mapping tương đương ở mức section, không phải section-by-section compliance. Bật ở `strict` khi hợp đồng ghi rõ.
- **BPMN 2.0** — *Business Process Model and Notation*, OMG spec. Nền tảng cho plugin BPMN; v1.0 chỉ ràng buộc subset (task, gateway, event cơ bản, một pool).
- **INVEST** — Bill Wake. Rubric chất lượng user story trong skill `backlog` (Independent, Negotiable, Valuable, Estimable, Small, Testable).
- **SPIDR** — Mike Cohn. Patterns split story khi kích thước vượt ngưỡng (Spike, Path, Interface, Data, Rules).
- **ISO/IEC 25010:2011** — *Systems and software Quality Requirements and Evaluation (SQuaRE) — System and software quality models*. Mapping NFR ở §9.

---

*— Kết thúc BRD v1.0 (Origin).*
