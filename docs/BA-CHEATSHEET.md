# BA Daily Cheatsheet — Công việc hàng ngày & cách harness hỗ trợ

> Bản đồ thực dụng: với mỗi đầu việc thường ngày của Business Analyst, harness **BA Daily Operators** giúp được đến đâu, gọi gì, ra sản phẩm gì. Mục tiêu xuyên suốt: **một REQ-ID được nhìn nhất quán qua SRS → sơ đồ → mockup → backlog**, để sai lệch (drift) lộ ra ngay khi xuất hiện.

## Cách đọc

| Ký hiệu | Ý nghĩa |
|---|---|
| ✅ | Harness tự động — operator/CLI làm phần việc chứng minh được |
| 🟡 | Bán tự động — bạn soạn nội dung, harness kiểm tra / định dạng / ghi trace |
| 🔜 | Đã thiết kế nhưng **chưa build** (plugin hoãn sang sau / lộ trình v2) |
| ⛔ | Thủ công — nằm ngoài phạm vi harness |

## Bắt đầu nhanh (chạy trọn một use case)

```
ba-uc deliver --uc "docs/uc-001.md: ## UC-001. Tên use case" --fidelity html
```

Một lệnh chạy cả chuỗi: phân tích SRS → kiểm chất lượng → vẽ sơ đồ → dựng mockup → cập nhật ma trận truy vết. Nếu dừng giữa chừng: `ba-uc resume` đi tiếp từ đúng bước còn dở. Xem trạng thái bất kỳ lúc nào: `ba-tools uc-status`.

---

## A. Khai thác & đầu vào

| Việc của bạn | Mức | Bạn làm gì / Harness làm gì | Sản phẩm |
|---|---|---|---|
| Phỏng vấn, workshop, thu thập yêu cầu từ stakeholder | ⛔ | Hoàn toàn thủ công — harness bắt đầu *sau khi* đã có tài liệu nguồn | — |
| Soạn tài liệu use case nguồn (`.md`) | 🟡 | Bạn viết use case; `ba-tools extract-uc` tách đúng section `## UC-NNN` và nhận dạng định danh | Section UC đã parse |

## B. Phân tích yêu cầu

| Việc của bạn | Mức | Bạn làm gì / Harness làm gì | Sản phẩm |
|---|---|---|---|
| Biến nguồn thành SRS/requirements nguyên tử, có gốc | ✅ | `ba-srs-analyze` (route `full`): soạn → lint → verify → vòng tự phản biện | `requirements.json` + `SRS.md` |
| Kiểm chất lượng câu yêu cầu (mơ hồ, không nguyên tử, từ "yếu") | ✅ | `ba-tools lint-requirements` chạy heuristic, báo lỗi để bạn sửa | Danh sách findings (JSON) |
| Xác minh tính có gốc (citation phải là trích thật từ nguồn) | ✅ | `ba-tools verify` = **cổng Quality (D-G1)** + vòng CoVe của `ba-critic`; không grounded thì chặn | Pass/fail (lỗi → thoát mã 2) |
| Giữ REQ-ID ổn định khi chỉnh sửa | ✅ | `lint-requirements` đối chiếu hai lượt, cảnh báo khi câu đổi nghĩa mà ID bị đánh lại | Cảnh báo renumber |

## C. Thiết kế & trực quan hóa

| Việc của bạn | Mức | Bạn làm gì / Harness làm gì | Sản phẩm |
|---|---|---|---|
| Sơ đồ quy trình / luồng (nhẹ, hằng ngày) | ✅ | `ba-mermaid`: sơ đồ Mermaid nhúng Markdown, trích REQ-ID; xuất ảnh qua `mmdc` nếu cần | `.mmd` + bản ghi trace |
| Sơ đồ BPMN chuẩn (draw.io) | 🔜 | Plugin `ba-make-diagram` — **đã thiết kế, chưa build** | — |
| Mockup giao diện | ✅ | `ba-mockup --fidelity html\|wireframe`: mỗi màn trích REQ-ID nó hiện thực | `.html` / `.md` + trace |

## D. Truy vết & phát hiện sai lệch *(giá trị cốt lõi)*

| Việc của bạn | Mức | Bạn làm gì / Harness làm gì | Sản phẩm |
|---|---|---|---|
| Ma trận REQ-ID xuyên SRS → sơ đồ → mockup | ✅ | `ba-tools index update` dựng lại toàn bộ từ các bản ghi trace | `INDEX.md` |
| Phát hiện gap / orphan / stale | ✅ | gap = thiếu phủ; orphan = REQ-ID lạ; stale = nguồn đổi (lệch hash) | Các mục trong INDEX |
| Chặn artifact lệch khỏi trace | ✅ | **Cổng Index (D-G2)**: orphan > 0 hoặc REQ-ID rơi vào gaps → DỪNG | Phán quyết cổng |

## E. Giao hàng trọn chuỗi

| Việc của bạn | Mức | Bạn làm gì / Harness làm gì | Sản phẩm |
|---|---|---|---|
| Chạy 1 UC từ đầu đến cuối (SRS → sơ đồ → mockup → index) | ✅ | `ba-uc deliver` — conductor điều phối tuần tự, có cổng chất lượng giữa các bước | 4 artifact + INDEX |
| Đi tiếp sau khi dừng / lỗi cổng | ✅ | `ba-uc resume` (vào lại đúng `next_step`) · `ba-tools uc-status` để xem | Pipeline chạy tiếp |
| Làm lại một UC, gộp phát hiện mới | ✅ | `ba-uc iterate` | Bản nháp soạn lại |

## F. Backlog & bàn giao

| Việc của bạn | Mức | Bạn làm gì / Harness làm gì | Sản phẩm |
|---|---|---|---|
| Tách story / tiêu chí chấp nhận / sắp thứ tự | 🔜 | Plugin `ba-backlog-grooming` — **chưa build** (làm tay) | — |
| Xuất DOCX SRS/BRD để bàn giao | 🔜 | Plugin `ba-uc-delivery` — **chưa build** (làm tay) | — |

## G. Vận hành & phối hợp

| Việc của bạn | Mức | Bạn làm gì / Harness làm gì | Sản phẩm |
|---|---|---|---|
| Hỗ trợ UAT, viết test case | ⛔ | Thủ công | — |
| Quản lý change request / phân tích tác động | 🟡 | `ba-uc iterate` + cờ drift của index gợi ý phạm vi ảnh hưởng; quy trình CR vẫn thủ công | Artifact cập nhật |
| Báo cáo độ phủ / trạng thái | 🟡 | `INDEX.md` + `uc-status` cho dữ liệu thô; bản báo cáo định dạng vẫn làm tay | — |
| Họp / review với stakeholder | ⛔ | Thủ công | — |

## Ba cổng gác

- **Confirm** — hành động bất khả hồi hoặc ra ngoài (xóa, gửi đi) sẽ hỏi trước.
- **Quality** — `verify` (citation có gốc) + vòng CoVe của `ba-critic`; chặn yêu cầu không có gốc.
- **Safety** — bước render/embed chỉ dùng CLI render thật, không tạo ảnh giả; spine không render (chỉ plugin).

## Nền tảng

- Mọi lệnh `ba-tools` thành công đều in **JSON UTF-8 ra stdout**; lỗi thoát **mã 2** (không lộ traceback).
- **Ranh giới tất định:** CLI chỉ làm việc mà file/lệnh/hash chứng minh được; mọi phân tích, soạn thảo, phán đoán là của agent.
- **Khả chuyển:** đường dẫn theo `--repo-root`, không hard-code đường dẫn máy.

## Ghi chú phạm vi (trung thực)

- ✅ và 🟡 phản ánh **v1.0 đã ship** (5 phase, đã kiểm chứng, chuỗi E2E đã chạy thật).
- 🔜 là các plugin **đã có trong sổ tay thiết kế nhưng chưa hiện thực** — đừng hứa với stakeholder là dùng được ngay.
- ⛔ là phần công việc BA mà harness *không* đặt mục tiêu thay thế.

---

*Tham chiếu: `DESIGN.md` (kiến trúc) · `MILESTONES.md` (v1.0 đã ship) · `CLAUDE.md` (ràng buộc kỹ thuật, hợp đồng CLI).*
