# Phase 4 — Grouping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement task-by-task; track RED/GREEN and results below.

**Goal:** API phân nhóm đúng k, giữ đủ người, cân bằng quy mô, báo lệch giới và đo Haversine.
**Architecture:** FastAPI → schema xác nhận vị trí → grouping service thuần tính toán → metrics → kiểm tra bất biến → response có schema. Không gọi geocoder, không lưu lịch sử.
**Tech Stack:** Python/FastAPI/Pydantic, NumPy, scikit-learn KMeans, scipy linear_sum_assignment, pyproj EPSG:32648, threadpoolctl.
**Spec:** README.md mục 7/Phụ lục A và kế hoạch phát triển mục Phase 4; người dùng đã yêu cầu tiếp tục Phase 4 theo phạm vi này.

## Global Constraints / quyết định triển khai

- `k=max(1,N//(M+F))`, M/F là số nguyên không âm (không nhận boolean, string hoặc float); N trong 1..1000 và không vượt cấu hình số dòng hiện tại. Không cho nhập k.
- API nhận dữ liệu vị trí đã xác nhận, kiểm tra `verified`, `location_confirmed=true`, tọa độ hữu hạn và nằm trong bounds nghiên cứu hiện hành. Đây là kiểm tra payload của ứng dụng không có tài khoản; không phải chữ ký chứng minh thao tác người dùng.
- Chuẩn hóa đầu vào theo student_id; từ chối ID trùng. Dùng seed 42, n_init=10; không công bố tối ưu toàn cục.
- Lựa chọn thuật toán đã có trong BRD: KMeans riêng giới + cân bằng + Hungarian. KMeans chung chỉ áp dụng fallback được BRD cho phép; greedy đơn thuần không đáp ứng yêu cầu.
- Phép chiếu WGS84 sang UTM 48N (EPSG:32648), `always_xy=True`. Khoảng cách báo cáo là Haversine trên lat/lon, bán kính cầu trung bình 6,371,008.8 m, không phải độ dài giao thông hay trắc địa ellipsoid chính xác.
- Cân bằng mỗi giới: quota `floor(n_gender/k)` hoặc `ceil(n_gender/k)`. Sắp tâm theo tọa độ; quota lớn đặt trước. Gán sinh viên vào các slot quota bằng linear_sum_assignment với chi phí bình phương khoảng cách mét tới tâm KMeans; tính lại tâm sau gán.
- Ghép hai giới: chi phí Haversine giữa tâm cụm, chỉ cho ghép cặp có tổng size thuộc `{floor(N/k),ceil(N/k)}`. Luôn tồn tại ghép như vậy với quota trên; vẫn tối thiểu hóa tổng chi phí trong tập ghép khả thi. Tránh ghép dư+dư làm lệch size 2 người.
- Nếu một giới < k: KMeans/cân bằng giới đủ số lượng; quota tổng là floor/ceil(N/k), phân bổ giới ít vào slot còn lại gần nhất. Nếu k=N, mỗi người là một nhóm. Khi tọa độ trùng làm số vị trí duy nhất < k, fit số tâm duy nhất rồi lặp tâm để điền k quota; không bỏ người/giảm k.
- Đánh số nhóm theo ID nhỏ nhất của thành viên, response ổn định cả khi đảo thứ tự input. Kiểm tra sau xử lý đủ N ID đúng một lần, đúng k nhóm không rỗng, size lệch tối đa 1.
- Trung bình toàn bộ = tổng khoảng cách của mọi cặp nội nhóm / tổng số cặp nội nhóm; không lấy trung bình không trọng số của các mean nhóm. Singleton: 0 cặp, mean/max=0.
- JSON request tối đa 8 MiB; 1 job grouping mỗi tiến trình, chạy trong worker thread, BLAS/OpenMP giới hạn 1 thread trong job; không chặn event loop. Cấu hình local 1 Uvicorn worker.
- Giữ workspace/branch hiện có vì Phase 1–3 chưa commit; không tạo checkout làm mất dependency chưa commit, không tự commit cả các phase trước. Sổ tiến độ local thay helper Bash của skill trên PowerShell.
- Phase 5 mới nối UI cấu hình Nam/Nữ, màu nhóm, bảng/lọc. Phase 7 mới đo baseline. Không mở rộng phạm vi này.

## Hợp đồng API

`POST /api/groups/generate`: `{students: [VerifiedStudent], target_male: int, target_female: int}`.

VerifiedStudent: `student_id`, `ho_ten`, `gioi_tinh` (Nam/Nữ), `dia_chi_goc`, `vi_tri_dai_dien`, `lat`, `lon`, `geocode_status` (verified), `location_confirmed` (true); `excel_row`, `dia_chi_da_sua`, `geocode_confidence` tùy chọn. Không nhận candidates, selectedCandidate, nhom hoặc trường UI tạm; Phase 5 phải chiếu schema khi gửi.

Response: `k`, `target_male`, `target_female`, `seed`, `strategy`, `assignments:[{student_id,group_id}]`, `groups:[{group_id,members:[VerifiedStudent],size,male,female,male_delta,female_delta,centroid:{lat,lon},metrics:{pair_count,mean_distance_m,max_distance_m}}]`, `overall_metrics` (cùng bộ 3 trường), `warnings:[{code,message,group_ids}]`.

422: input không hợp lệ/vị trí chưa xác nhận; 413: dung lượng/số dòng vượt cấu hình; 429: đang chạy job; 500 thông báo cố định nếu bất biến nội bộ thất bại, không trả kết quả một phần.

## Review Focus

- Hai giới cùng có dư: ghép Hungarian vẫn phải đạt size floor/ceil.
- Nhiều tọa độ trùng và k gần N: không thiếu nhóm, không NaN, không warning KMeans giả thành công.
- Input giả kiểu boolean/string, số vô hạn, duplicate ID hoặc ngoài bounds: chặn ở API trước tính toán.
- Đảo thứ tự sinh viên và quota bằng nhau: assignment/ID nhóm vẫn ổn định trong môi trường pinned.
- Tổng hợp mean khi nhóm singleton hoặc size khác nhau: đúng trọng số số cặp.

### Task 1: Metrics và phép chiếu
**Files:** backend/app/services/metrics_service.py, tests/test_metrics.py; requirements.txt.
**Interfaces:** `haversine_m(a,b)` với tuple(lat,lon); `project_points(points)` → ndarray x/y mét; `pair_metrics(points)` và `aggregate_metrics(metrics)` → dict 3 trường.
- [x] Viết test 1 độ xích đạo ~111195.08m, đối xứng, antipodal, trùng/singleton, mean có trọng số; UTM roundtrip và khoảng cách mét tại HCM.
- [x] Chạy test RED vì thiếu implementation; cài dependencies cần thiết, triển khai và chạy GREEN.
**Expected:** `python -m pytest tests/test_metrics.py -q` đạt.

### Task 2: Schema và thuật toán
**Files:** schemas/group.py, services/grouping_service.py, tests/test_grouping.py.
**Interfaces:** `GenerateGroupsRequest`, `GenerateGroupsResponse`; `generate_groups(payload)` → response; dùng metrics Task 1.
- [x] Test RED k=6/6/8/1 với N=30/34/42/3, 18Nam12Nữ đạt 6x(3+2), số dư, giới ít/không có, M hoặc F=0, singleton, trùng tọa độ, tái lập, cụm địa lý tách biệt.
- [x] Triển khai KMeans, quota, ghép có ràng buộc size, fallback, bất biến và cảnh báo; chạy GREEN.
**Expected:** `python -m pytest tests/test_grouping.py tests/test_metrics.py -q` đạt.

### Task 3: API và giới hạn
**Files:** api/groups.py, main.py, core/upload_limit.py, tests/test_groups_api.py.
**Interfaces:** HTTP schema trên → `generate_groups`; application.state.grouping_lock bảo vệ job.
- [x] Test RED route 30 người, tất cả invalid input, bounds, busy, body limit và lỗi bất biến an toàn.
- [x] Triển khai route sync/threadpool, lock/finally, byte limit; chạy GREEN và toàn suite.
**Expected:** `python -m pytest -q` đạt, health/geocoding/import không hồi quy.

### Task 4: Thực nghiệm và báo cáo
**Files:** scripts/check_phase4_api.py, docs/reports/phase-4.md, README.md, kế hoạch phase; chỉnh thông báo placeholder UI theo trạng thái backend.
**Interfaces:** Ban đầu dùng dữ liệu demo12 đã xác nhận. Sau dọn dự án, script HTTP dùng fixture tổng hợp `tests/grouping_fixtures.py`, không phụ thuộc artifact phiên cũ; số đo công cộng ban đầu được giữ trong báo cáo lịch sử.
- [x] Chạy API thật với dữ liệu demo 12 và fixture tổng hợp 30; lưu JSON/đối chiếu đủ ID, size, Nam/Nữ, metrics.
- [x] Review độc lập toàn thay đổi Phase 4; không có lỗi Important/Critical; xác minh suite/pip check.
- [x] Cập nhật AC-05..09, hướng dẫn gọi API, giới hạn heuristic và Phase 5 UI chưa triển khai.
**Expected:** báo cáo có số đo chạy thật, không suy diễn chất lượng từ test mock.
