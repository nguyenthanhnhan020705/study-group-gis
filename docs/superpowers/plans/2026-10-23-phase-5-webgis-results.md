# Phase 5 — WebGIS Results Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Nối API Phase 4 với giao diện cấu hình, bản đồ, bộ lọc, thành viên và thống kê nhất quán.
**Architecture:** Giữ trang HTML/CSS/ES modules hiện tại. Module `grouping.js` điều phối request/render; `state.js` quản lý phiên, revision, kết quả và lọc. `map.js` tiếp tục gom tọa độ chính xác, bổ sung màu/nhãn nhóm và điểm thuộc nhiều nhóm.
**Tech Stack:** JavaScript ES modules, HTML/CSS, Leaflet 1.9.4, FastAPI hiện có; Playwright/Edge kiểm tra UI.
**Spec:** README.md mục 8, AC-10/AC-14; kế hoạch 7 phase mục 9; hợp đồng API Phase 4. Người dùng yêu cầu triển khai Phase 5 sau khi xem tổng quan phạm vi.

## Global Constraints / quyết định triển khai

- Không thay kiến trúc, thuật toán, geocoding hoặc quy tắc KTX. Không thêm dependency runtime.
- `k=max(1,floor(N/(M+F)))`; M/F nguyên không âm, tổng >0; mặc định 3/2 là lựa chọn triển khai theo kịch bản mẫu.
- Gửi riêng trường VerifiedStudent, không gửi candidates/selectedCandidate/locationRevision/nhom.
- Chỉ gửi khi mọi vị trí verified; kiểm tra cấu trúc và bảo toàn ID của response trước khi công bố kết quả.
- Đổi địa chỉ, lựa chọn/xác nhận, import hoặc M/F làm tăng revision, xóa kết quả/lọc và hủy request; response cũ không khôi phục kết quả dù hủy không kịp.
- Bảng/bản đồ dùng cùng danh sách thành viên từ kết quả. Tổng toàn bộ và số đang xem phân biệt rõ; lọc không đổi overall_metrics.
- Màu kèm số nhóm; điểm cùng tọa độ nhưng nhiều nhóm vẫn một marker, nhãn liệt kê nhóm, popup đủ người. Không dịch tọa độ.
- Nút xuất luôn disabled trong Phase 5, ghi rõ sẽ có ở Phase 6; state có điều kiện kết quả hiện hành để Phase 6 sử dụng.
- Giữ workspace `codex/phase-1-foundation` và thay đổi chưa commit của Phase 1–4. Không tự commit/push toàn bộ mã nguồn cũ. Ledger PowerShell thay helper Bash.
- Phạm vi và hướng triển khai đã được BRD/kế hoạch xác định; thực hiện trực tiếp theo yêu cầu, không thêm vòng phê duyệt thiết kế.

## Review Focus

- Sửa M/F rồi đổi lại hoặc upload khác khi request cũ đang chờ: không nhận lại kết quả cũ.
- Cùng tọa độ thuộc nhiều nhóm: không mất người, nhãn/popup và lọc khớp bảng.
- Response lỗi/thiếu thành viên/sai nhóm/không phải JSON: không báo thành công hoặc để kết quả cũ dùng được.
- M/F trống, thập phân, âm, cả hai 0 và nhóm singleton: UI không gửi request sai, metrics vẫn hữu hạn.
- Tên/địa chỉ chứa HTML, mobile và không tải được CDN: render an toàn, bảng cuộn trong vùng, thao tác chia nhóm vẫn hoạt động.

### Task 1: State và hợp đồng request

**Files:** `frontend/js/state.js`, `frontend/js/api.js`, `scripts/check_phase5_browser.py`.
**Interfaces:** `setGroupingTargets(male, female)`, `invalidateGrouping()`, `groupingPayload()`, `acceptGrouping(revision,result)`, `visibleGroupMembers()`, `selectGroup(id)`, `generateGroups(payload,signal)`.
- [x] Viết và chạy browser assertions RED cho input, schema payload, response giữ ID, revision và lọc.
- [x] Thêm state mục tiêu/revision/lọc, invalidation tại mọi mutation; validate response tại boundary; adapter API.
- [x] Chạy lại assertions GREEN.

### Task 2: Luồng kết quả và bản đồ

**Files:** `frontend/js/grouping.js` (mới), `app.js`, `geocoding.js`, `map.js`, `frontend/index.html`, `frontend/css/style.css`.
**Interfaces:** `initializeGrouping()`; `showStudentLocations(students,preview)` giữ tương thích; màu/nhãn từ `nhom` chỉ trên bản sao kết quả.
- [x] Viết/chạy RED các ca nhập 30 fixture tổng hợp → API thật → 6 nhóm, lọc → 5 người, warnings, stale request, lỗi backend và responsive.
- [x] Thêm form M/F/k, status, filter, summary/metrics, bảng nhóm/thành viên và nút xuất disabled. Hủy request/guard revision.
- [x] Tích hợp marker số nhóm, điểm nhiều nhóm và popup an toàn; phân biệt lớp xác minh với kết quả.
- [x] Chạy GREEN browser và hồi quy Phase 2/3/shared-locations; kiểm tra Leaflet thực với fixture tổng hợp (không dùng như bằng chứng geocoding).

### Task 3: Nghiệm thu, review và tài liệu

**Files:** `docs/reports/phase-5.md`, `docs/reports/ui-checklist.md`, README và kế hoạch 7 phase.
- [x] Chạy toàn bộ `python -B -m pytest -q -p no:cacheprovider`, browser Phase 5 và hồi quy liên quan; xem ảnh desktop/mobile.
- [x] Review độc lập theo requesting-code-review, sửa lỗi quan trọng và kiểm tra lại.
- [x] Ghi lệnh/kết quả/giới hạn, cập nhật trạng thái Phase 5 theo bằng chứng; Phase 6/7 giữ chưa triển khai.
