# Phase 6 — Excel Export and Basemap Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task and record RED/GREEN evidence.

**Goal:** Xuất Excel khớp toàn bộ kết quả hiện hành và phục hồi bản đồ khi host tile OSM không kết nối được.
**Architecture:** API export nhận snapshot kết quả Phase 4, kiểm tra bảo toàn thành viên/thống kê rồi tạo workbook openpyxl trong bộ nhớ. UI tải snapshot toàn bộ bằng fetch/Blob có guard revision. Bản đồ thử OSM tiêu chuẩn trước, tự chuyển Geoapify qua proxy backend cố định nếu lỗi; không lộ khóa hoặc thay ảnh thật bằng mock trong demo.
**Tech Stack:** FastAPI/Pydantic, openpyxl, httpx hiện có, JavaScript/Leaflet, pytest/Playwright/Edge.
**Spec:** README mục 9, AC-11/AC-14; kế hoạch 7 phase mục Phase 6; yêu cầu người dùng bổ sung sửa lỗi bản đồ nền.

## Global Constraints / quyết định triển khai

- Hai sheet chính xác `Danh_sach_nhom`, `Thong_ke_nhom`; cột theo BRD, khoảng cách mét. Không xuất lat/lon thô.
- Thứ tự nhóm rồi student_id ổn định. Nội dung người dùng luôn ghi như văn bản Excel, kể cả bắt đầu bằng `=`; không tạo công thức hoặc hyperlink ngoài ý muốn.
- Export kiểm tra số nhóm theo k, IDs/assignments/size/Nam/Nữ/delta và tính lại Haversine để từ chối metrics bất nhất; không chạy lại KMeans hoặc thay đổi nhóm.
- Tối đa 1.000 thành viên, đồng thời tuân thủ MAX_STUDENT_ROWS; request export tối đa 8 MiB; lỗi không echo dữ liệu cá nhân.
- Không lưu file người dùng trên server. Workbook trả bằng bytes; browser thu hồi object URL sau download.
- Lọc hiển thị không làm mất nhóm trong file. Đổi đầu vào, xác nhận, upload hoặc M/F trong lúc tải hủy export; response cũ không tự tải.
- OSM host đang trả ERR_CONNECTION_REFUSED ngoài sandbox. CARTO tải được nhưng điều kiện hiện hành yêu cầu API key riêng, nên dùng dịch vụ Geoapify đã cấu hình, qua backend; không thêm tài khoản.
- Proxy chỉ lấy endpoint tile osm-carto cố định, zoom 0..19, x/y theo zoom, timeout và giới hạn kích thước; sanitization mọi lỗi/redirect/quota. Cache tile công cộng trong bộ nhớ có giới hạn, không lưu lâu dài tọa độ sinh viên.
- Tự chuyển nguồn tối đa một lần khi OSM lỗi/treo, hiển thị nguồn và attribution đúng. Cho thử lại khi cả hai nguồn thất bại; không báo ready chỉ vì sự kiện load nếu không có ảnh hợp lệ.
- Giữ workspace/nhánh `codex/phase-1-foundation`, vì Phase 1–5 còn chưa commit; không tạo worktree hoặc commit các thay đổi cũ. Ledger local thay helper Bash trên PowerShell.
- Phạm vi export đã được BRD xác định; triển khai trực tiếp theo yêu cầu, không mở thêm tính năng Phase 7.

## Review Focus

- Workbook chứa đủ toàn bộ sinh viên khi UI đang lọc một nhóm; group/metrics vẫn khớp snapshot.
- Đổi M/F, địa chỉ hoặc import khi export đang chờ không tải snapshot cũ; retry sau lỗi vẫn dùng được.
- Response export JSON/HTML hoặc XLSX hỏng không được tải như file thành công.
- OSM lỗi/treo, lỗi Geoapify/quota, lỗi tile cũ đến sau đổi nguồn không ghi đè trạng thái của nguồn mới.
- Không có khóa trong frontend/response/log; tile proxy không thành open proxy, không theo redirect, không cache lỗi.

### Task 1: Export validation and workbook API

**Files:** `backend/app/schemas/export.py`, `services/export_service.py`, `api/groups.py`, `main.py`, `core/upload_limit.py`; `tests/test_export.py`, `tests/test_export_api.py`.
**Interfaces:** `ExportGroupsRequest`, `validate_export(payload)->None`, `export_workbook(payload)->bytes`; POST `/api/groups/export` nhận snapshot GenerateGroupsResponse và trả XLSX tên cố định `danh_sach_nhom.xlsx`.
- [x] Viết test RED: hai sheet/đủ 30/6 nhóm, cột/địa chỉ đại diện/thứ tự/formula-safe; từ chối ID/assignment/count/metrics/target sai, giới hạn body/rows và lỗi validation an toàn.
- [x] Cài schema/validation/workbook/route, chạy GREEN test export và toàn bộ backend.

### Task 2: Map failure recovery

**Files:** `backend/app/services/map_tiles.py`, `api/map_tiles.py`, `main.py`; `frontend/js/basemap.js`, `map.js`, `api.js`, `frontend/index.html`; `tests/test_map_tiles.py`, browser checks.
**Interfaces:** GET `/api/map/tiles/{z}/{x}/{y}.png`, `MapTileService.get_tile(z,x,y)->bytes`; `initializeBasemap(map)` dùng URL backend từ api.js.
- [x] Lưu bằng chứng OSM ERR_CONNECTION_REFUSED và probe nguồn dự phòng thật.
- [x] RED backend: tọa độ tile sai/thiếu key/upstream timeout/quota/non-PNG/redirect/quá lớn, cache thành công và sanitization.
- [x] RED browser: OSM hỏng thì Geoapify thật/stub network tile phục hồi có attribution; cả hai hỏng hiện lỗi và thử lại. Không mock Leaflet.
- [x] Cài proxy có cache TTL/LRU và client fallback/retry; chạy GREEN; đối chiếu ảnh nền thật trong demo.

### Task 3: UI export, regression and demo

**Files:** `frontend/js/api.js`, `grouping.js`, `index.html`, `scripts/check_phase6_browser.py`; điều chỉnh assertion export của script Phase 5 theo hành vi mới.
- [x] RED download thật qua trình duyệt, mở XLSX đối chiếu 30 thành viên/6 nhóm khi filter còn một nhóm; export error, stale response và retry.
- [x] Cài nút/export status, snapshot guard, timeout và URL cleanup; chạy GREEN.
- [x] Chạy toàn suite + browser hồi quy Phase 2/3/5/shared; review độc lập; cập nhật README/kế hoạch/báo cáo Phase 6 và UI checklist.
- [x] Mở demo hiện hành có bản đồ thật, chia mẫu 30 và tải workbook để người dùng kiểm tra; giữ Phase 7 chưa triển khai.
