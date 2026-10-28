# Phase 7 — Integration, evaluation and acceptance Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. Work RED/GREEN task-by-task and request one independent whole-change review before completion.

**Goal:** Nghiệm thu luồng WebGIS hiện tại và có số liệu so sánh thuật toán với baseline tái lập được.
**Architecture:** Giữ FastAPI/Geoapify/Leaflet và dữ liệu phiên. Tách kiểm thử provider fixture khỏi kiểm tra mạng thật. Baseline dùng cùng người, k, kích thước và quota giới của kết quả thuật toán; chỉ thay cách phân bố theo địa lý. Công cụ đánh giá đọc snapshot giả lập đã xác minh, không tự geocode hoặc dùng tọa độ chưa kiểm chứng.
**Tech stack:** Python, pytest, httpx MockTransport, openpyxl, NumPy và Playwright hiện có.
**Spec:** README mục12/AC-12/AC-13; kế hoạch7phase mục11; thay đổi tự đối chiếu ngày24/10/2026. Người dùng cho phép triển khai Phase7 ngày25/10/2026; giao diện trình bày có thể sửa sau.

## Status and constraints

**HOÀN THÀNH NGÀY 25/10/2026.** 243 test Python và toàn bộ browser check liên quan đạt; live30/30, baseline30seed, review độc lập không có Critical/Important. Một mục cải thiện nhỏ về phân loại pending trong script chẩn đoán đã ghi tại [nghiệm thu](../../reports/acceptance.md); [đánh giá](../../reports/evaluation.md) lưu số liệu và giới hạn. Không có triển khai hosting; giao diện trình bày để chỉnh sau.

Điều chỉnh cách thực thi: Task 1 kiểm thử characterization trên hành vi đã có, không cố tình phá ứng dụng để tạo RED; Task 2 công cụ mới test trước. Dùng các browser regression hiện có cho đầy đủ ma trận stale geocode/group/export. Ledger và quyết định cuối được giữ để truy vết vì chưa commit.

- Không thêm đăng nhập, cơ sở dữ liệu, routing hoặc hosting bắt buộc. Không ghi dữ liệu sinh viên thật vào Git/log/ảnh.
- API import không tự geocode; frontend tự khởi chạy sau sự kiện import thành công. Integration phải kiểm tra cả API và điều phối frontend để không bỏ sót luồng tự động.
- Không coi confidence hoặc tỷ lệ tự động là độ chính xác thực tế. Tên cư xá phải có dữ liệu đầu vào; campus chung không suy ra tòa theo giới tính.
- Khoảng cách Haversine là đường chim bay. Không kết luận tối ưu toàn cục hoặc tốt hơn baseline trước khi có số liệu.
- Giữ nguyên dữ liệu và phiên hiện có khi chạy kiểm thử; các test server dùng cổng riêng và luôn dọn process của chính mình.
- Không tự cài autostart/Windows service, commit/push hoặc publish khi chưa có yêu cầu.

## Review focus

ID bị mất/trùng giữa các bước; tự xác nhận nhầm tòa sau dùng cache khác giới; response cũ làm sống lại kết quả/export; baseline thay đổi quota khiến so sánh thiếu công bằng; snapshot chưa xác nhận nhưng được dùng báo cáo; provider failure bị ghi là geocoding sai; hai phiên/cache bị lẫn; log làm lộ key hoặc danh sách.

### Task 1 — Reproducible end-to-end tests

**Files:** `tests/integration/test_workflow.py`, `scripts/check_phase7_browser.py`; dùng `tests/grouping_fixtures.py`, API/schema/service hiện có.

- [x] RED: import workbook mẫu qua multipart, dùng MockTransport tại boundary Geoapify của app, nhận đúng candidate auto flags; đối chiếu ID/gốc/hint/giới xuyên import→geocode→grouping→export.
- [x] GREEN: browser tự khởi chạy sau import, tự xác nhận đủ đầu vào rõ ràng; không gọi nhà cung cấp ngoài trong ca offline. XLSX mở bằng openpyxl, hai sheet và đủ người/thống kê.
- [x] RED/GREEN: campus thiếu tòa, kết quả sai phường/giới, lỗi dịch vụ/quota và retry; địa chỉ chưa rõ ngăn chia nhóm, dịch vụ lỗi dừng hàng đợi thay vì lặp100request.
- [x] RED/GREEN: sửa địa chỉ/M/F, đổi file trong lúc geocode/group/export đang chờ; response cũ không ghi đè và file cũ không tải. Giữ nguyên họ tên, giới và ID khi sửa địa chỉ.
- [x] Lệnh nghiệm thu: `python -B -m pytest tests/integration/test_workflow.py -q -p no:cacheprovider`; `python -B scripts/check_phase7_browser.py`. Ghi rõ nguồn fixture và cổng riêng.

### Task 2 — Fair random baseline and evaluation command

**Files:** `scripts/evaluate_grouping.py`, `tests/test_evaluation.py`, `docs/reports/evaluation.md`.
**Interface:** CLI `--input <confirmed-snapshot.json> --output <report.json>`, input là `GenerateGroupsRequest` từ dữ liệu giả lập đã xác nhận; hashSHA256 của input xuất trong report.

- [x] RED: từ chối input có người chưa verified/confirmed, ID trùng, tọa độ không hữu hạn hoặc schema sai; không gọi API ngoài và không tự tạo tọa độ.
- [x] RED: baseline giữ cùng tập ID, đúng một nhóm/người, cùng k và vector size/Nam/Nữ của thuật toán; không thay quota để tạo ưu thế cho cách nào.
- [x] GREEN: shuffle riêng Nam/Nữ bằng RNG theo seed cố định, phân vào quota từng nhóm. Dùng30seeds0..29 đã định trước; thuật toán dùng seed42 hiện hành. Một input/seed phải tái lập đúng kết quả.
- [x] RED/GREEN: cùng dữ liệu tính mean khoảng cách theo toàn bộ cặp nội nhóm (có trọng số số cặp), max, độ lệch giới/quy mô, số thiếu/lặp. Singleton và toàn tọa độ trùng có metrics0, không chia cho0.
- [x] Report ghi metric thuật toán và baseline mean/std/median/min/max cùng tỷ lệ seed thuật toán tốt hơn; kết quả thua hoặc ngang vẫn công bố. Không chọn bỏ seed xấu hoặc coi30lầnshuffle là30bộ dữ liệu độc lập.
- [x] Lệnh: `python -B -m pytest tests/test_evaluation.py -q -p no:cacheprovider`; CLI chạy trên snapshot giả lập đủ nguồn, lưu kết quả và điều kiện chạy trong evaluation.md.

### Task 3 — Live validation, isolation and privacy

**Files:** `scripts/check_phase7_live.py`, `tests/integration/test_session_isolation.py`, `docs/reports/acceptance.md`.

- [x] Kiểm tra startup bằng `start-webgis.cmd`/`run_local.py --check`, xác nhận HTTP/CORS/assets và log lỗi dễ chẩn đoán; kiểm tra dừng/chạy lại không để một server tồn tại đơn lẻ.
- [x] Chạy mẫu30người qua Geoapify thật, không dùng tọa độ lưu sẵn để báo tỷ lệ tra cứu; ghi tổng dòng, địa chỉ duy nhất, số auto/review/error, số sửa tay, số lần gọi và thời gian. Ghi ngày và quota/network nếu thất bại.
- [x] Đối chiếu thủ công từng địa danh mẫu với danh tính/nguồn đã đăng ký, gồm cư xá A–E, Cỏ May, KTX B và hai đường đúng phường. Không suy rộng tỷ lệ đúng của bộ mẫu sang mọi địa chỉ.
- [x] Thực hiện một địa chỉ lỗi→sửa→retry trong giao diện, kiểm tra tọa độ cũ bị xóa, nhóm cũ hết hiệu lực; tính lại và mở workbook mới. Screenshot desktop/mobile, nguồn ảnh nền thật và attribution đúng.
- [x] Hai browser context riêng nhận hai bộ dữ liệu khác nhau; không lẫn sinh viên/kết quả/cache. Refresh xóa dữ liệu phiên; API không cung cấp lịch sử server.
- [x] Kiểm tra credentials/PII không xuất hiện trong frontend/response/lỗi/log test, cache không lưu danh sách người lâu dài, file người dùng không lưu trên server. Không in key thật trong lệnh hoặc report.

### Task 4 — Acceptance report and handoff

**Files:** `docs/reports/acceptance.md`, `docs/reports/evaluation.md`, `docs/reports/ui-checklist.md`, `README.md`, masterphaseplan.

- [x] Chạy toàn bộ pytest, browser liên quan và live check; ghi ngày/lệnh/count/exitcode/nguồn dữ liệu, tách rõ fixture và provider thật.
- [x] Đối chiếu AC-01..AC-14; chỉ đánh dấu AC-12/AC-13 khi đủ bằng chứng. Ghi vấn đề chưa đạt, độ chính xác/hiệu năng chưa đo và phụ thuộc mạng/quota.
- [x] Review độc lập, sửa Critical/Important bằng regression RED/GREEN rồi chạy suite liên quan. Không coi hết lỗi unit test là đã chứng minh uptime dài hạn.
- [x] Cập nhật trạng thái Phase7 hoàn thành khi thực sự đạt nghiệm thu. Deploy chỉ là tùy chọn theo yêu cầu sau đó.

## Ready-to-start criteria

Phase1–6 truy cập được, unit/API/browser regression đạt; mẫu giả lập và dữ liệu địa danh đã có nguồn; quy trình chạy local có kiểm tra health/CORS/log. Các tiêu chí này là điều kiện bắt đầu, không thay cho kết quả đánh giá/nghiệm thu Phase7.
