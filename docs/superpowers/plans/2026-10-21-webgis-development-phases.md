# WebGIS v1.0 — Kế hoạch phát triển theo phase

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Đây là kế hoạch phân kỳ; khi bắt đầu mỗi phase, cụ thể hóa thiết kế và các bước triển khai của phase đó trước khi viết mã.

**Goal:** Hoàn thành WebGIS để giảng viên nhập Excel, xác minh vị trí, chia đủ sinh viên theo vị trí và mục tiêu Nam/Nữ, xem bản đồ và xuất kết quả.

**Architecture:** Frontend HTML/CSS/JavaScript và Leaflet giao tiếp với backend FastAPI. Backend xử lý Excel, Geoapify, thuật toán và xuất file; không có cơ sở dữ liệu hoặc lịch sử lưu lâu dài trong v1.0.

**Tech Stack:** Python, FastAPI, pandas, openpyxl, httpx, python-dotenv, numpy, scikit-learn, scipy, pyproj, Leaflet; pytest cho kiểm thử Python.

**Spec:** [README.md — BRD WebGIS v1.0](../../../README.md).

**Trạng thái:** Phase 1–7 hoàn thành trong phạm vi MVP local. Bằng chứng: [Phase 1](../../reports/phase-1.md), [Phase 2](../../reports/phase-2.md), [Phase 3](../../reports/phase-3.md), [Phase 4](../../reports/phase-4.md), [Phase 5](../../reports/phase-5.md), [Phase 6](../../reports/phase-6.md), [nghiệm thu Phase 7](../../reports/acceptance.md), [đánh giá baseline](../../reports/evaluation.md). Nền bản đồ có nguồn Geoapify dự phòng. Thời lượng bên dưới là ước lượng kế hoạch; hosting và chỉnh giao diện tiếp theo cần yêu cầu riêng.

## 1. Ràng buộc xuyên suốt

- Một vai trò giảng viên; giao diện và thông báo bằng tiếng Việt.
- Excel có đúng các cột bắt buộc `Họ và tên`, `Giới tính`, `Nơi ở để học tập`; đọc theo tên cột.
- Mỗi dòng có `student_id` riêng, không gộp sinh viên trùng tên/địa chỉ.
- Chỉ chia nhóm khi toàn bộ sinh viên có vị trí `verified` và được xác nhận.
- `M`, `F` nguyên không âm, `M+F > 0`, `N > 0`; `k=max(1,floor(N/(M+F)))`.
- Thuật toán chính: K-Means riêng từng giới, cân bằng, Hungarian; xử lý ngoại lệ thiếu một giới theo BRD.
- Mỗi sinh viên được gán đúng một nhóm; không bỏ sinh viên để đạt tỷ lệ mục tiêu.
- Sửa địa chỉ phải xóa tọa độ/xác nhận cũ. Sửa đầu vào hoặc tham số chia nhóm phải làm kết quả cũ hết hiệu lực.
- Geoapify chỉ được gọi từ backend; khóa thật nằm trong biến môi trường, không vào Git hoặc frontend.
- Dữ liệu kiểm thử/demo công khai là giả lập; tọa độ tổng hợp trong unit test phải được ghi rõ là dữ liệu thử.
- Không bổ sung đăng nhập, Supabase/PostGIS, GeoServer, routing hoặc lưu lịch sử ngoài phạm vi BRD.
- Hướng dẫn chạy và xác minh dùng Windows PowerShell; mỗi phase cập nhật tài liệu cùng chức năng.

## 2. Tổng quan và thứ tự thực hiện

| Phase | Đầu ra chính | Phụ thuộc | Ước lượng | Tuần | Trạng thái |
|---|---|---|---:|---|---|
| 1 | Backend chạy, frontend có bản đồ nền và trạng thái kết nối | BRD | 1 ngày | 1 | Hoàn thành |
| 2 | Upload/validate Excel và bảng sinh viên | 1 | 2 ngày | 1 | Hoàn thành |
| 3 | Geocoding, sửa địa chỉ và xác nhận vị trí | 2 | 3 ngày | 1–2 | Hoàn thành |
| 4 | API chia nhóm, kiểm tra bất biến và thống kê khoảng cách | 3 | 4 ngày | 2 | Hoàn thành |
| 5 | Luồng WebGIS hiển thị, lọc nhóm và vô hiệu hóa kết quả cũ | 4 | 3 ngày | 3 | Hoàn thành |
| 6 | Xuất Excel khớp kết quả hiện hành, phục hồi nền bản đồ | 5 | 2 ngày | 3 | Hoàn thành |
| 7 | Kiểm thử tích hợp, đánh giá baseline, báo cáo và demo | 6 | 5 ngày | 4 | Hoàn thành |

Thực hiện tuần tự theo Phụ lục F của BRD. Unit test thuật toán dùng fixture tổng hợp để tái lập kết quả; nghiệm thu geocoding thực tế là một bằng chứng riêng và không được thay bằng mock.

## 3. Trách nhiệm các nhóm file

Tất cả đường dẫn dưới đây tính từ thư mục gốc repository. Các file Phase 1–7 đã tạo; dữ liệu đánh giá và nguồn nằm trong `data/evaluation/`.

| Nhóm file | Trách nhiệm | Phase tạo đầu tiên |
|---|---|---|
| `backend/app/main.py`, `backend/app/core/config.py` | Khởi tạo API, cấu hình môi trường, CORS và giới hạn xử lý | 1 |
| `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/.env.example`, `pytest.ini` | Phụ thuộc ứng dụng/kiểm thử, cấu hình mẫu, import path khi chạy pytest | 1 |
| `backend/app/schemas/student.py`, `backend/app/schemas/group.py` | Hợp đồng dữ liệu sinh viên, trạng thái vị trí, yêu cầu/kết quả nhóm | 2, 4 |
| `backend/app/api/students.py`, `geocoding.py`, `groups.py` | Nhận yêu cầu HTTP, validate và trả response/lỗi | 2, 3, 4 |
| `backend/app/services/excel_service.py`, `geocoding_service.py` | Đọc Excel và tích hợp Geoapify | 2, 3 |
| `backend/app/services/grouping_service.py`, `metrics_service.py`, `export_service.py` | Chia nhóm, đo Haversine, xuất Excel | 4, 6 |
| `frontend/index.html`, `frontend/css/style.css` | Giao diện một trang theo các bước nghiệp vụ | 1 |
| `frontend/js/api.js`, `app.js`, `map.js`, `state.js` | Gọi API, điều khiển giao diện, vẽ bản đồ, trạng thái phiên | 1, 2 |
| `tests/`, `tests/fixtures/`, `data/samples/` | Kiểm thử tự động, fixture và Excel giả lập | 1, 2 |
| `scripts/evaluate_grouping.py`, `docs/reports/` | Thực nghiệm baseline và bằng chứng nghiệm thu | 7 |

## 4. Các tình huống cần chú ý khi rà soát

| Tình huống | Hành vi cần kiểm tra | Phase phụ trách |
|---|---|---|
| Hai người trùng tên/địa chỉ hoặc có dòng rỗng xen giữa | Giữ đủ định danh và số dòng Excel; không tự loại người | 2 |
| Response geocoding cũ đến sau khi đã sửa địa chỉ hoặc upload file mới | Không ghi đè tọa độ/xác nhận của dữ liệu mới | 3, 5 |
| Nhiều người có cùng tọa độ, số vị trí khác nhau ít hơn `k` | Không mất người; vẫn đủ nhóm và cân bằng quy mô khi khả thi | 4 |
| Nhóm một người, chỉ có một giới, hoặc `M=0`/`F=0` | Không chia cho 0, không gọi K-Means quá số mẫu; báo lệch mục tiêu khi cần | 4 |
| Xuất sau khi đầu vào đổi; ô Excel chứa nội dung bắt đầu bằng `=` | Không xuất kết quả cũ; dữ liệu người dùng được ghi như văn bản, không thành công thức | 5, 6 |

## 5. Phase 1 — Nền tảng và môi trường local

**Mục tiêu:** Có bộ khung chạy được để phát triển và kiểm thử các module sau.

**File:** Nhóm cấu hình/backend/frontend của phase 1 trong mục 3; `tests/test_health.py`; chỉnh `.gitignore` và README. Tạo các file `__init__.py` cần thiết cho package Python.

**Giao tiếp:** `GET /api/health` trả HTTP 200 với JSON trạng thái đơn giản, không chứa secrets. `frontend/js/api.js` quản lý một base URL duy nhất; các endpoint nghiệp vụ được thêm ở phase sau.

- [x] Viết test health check và kiểm tra cấu hình không trả khóa API; chạy để xác nhận chưa có ứng dụng đáp ứng.
- [x] Tạo FastAPI, health endpoint, cấu hình biến môi trường và CORS cho frontend local.
- [x] Tạo frontend tối thiểu với Leaflet, ghi công bản đồ và trạng thái kết nối backend bằng tiếng Việt.
- [x] Tạo dependency files, cấu hình pytest và `.env.example` chỉ chứa placeholder; cập nhật ignore cho file tạm/dữ liệu thực.
- [x] Chạy test, khởi động hai server và kiểm tra kết nối bằng trình duyệt; ghi lại lệnh vào README.

**Xác minh PowerShell** (sau khi tạo các file):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests/test_health.py -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001 --reload
```

Ở terminal thứ hai chạy `.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend`. Mở `http://127.0.0.1:5500`; kiểm tra health và bản đồ nền.

**Điều kiện hoàn thành:** Test health đạt; frontend gọi được backend; không cần khóa thật để chạy health và bộ test. Đóng góp nền tảng cho BR-09 / AC-13, chưa phải nghiệm thu toàn bộ yêu cầu này.

## 6. Phase 2 — Nhập Excel và kiểm tra dữ liệu

**Mục tiêu:** Giảng viên upload file, xem đủ sinh viên và nhận lỗi cụ thể theo dòng.

**File:** `student.py`, `students.py`, `excel_service.py`, `frontend/js/state.js`; cập nhật `app.js`, `api.js`, `index.html`; thêm `tests/test_excel.py`, `tests/test_students_api.py` và fixture.

**Giao tiếp:** `POST /api/students/import` nhận file multipart. Response gồm bản ghi có `student_id`, `excel_row`, tên, giới tính, địa chỉ gốc, trạng thái vị trí ban đầu và lỗi theo dòng/trường. Đầu vào có lỗi phải được trình bày rõ và chặn luồng tiếp theo, không âm thầm bỏ dòng lỗi.

- [x] Viết test: đổi thứ tự cột vẫn đọc đúng; bỏ qua cột `Dấu thời gian`; thiếu cột, tên/địa chỉ rỗng, giới tính sai, file hỏng và file quá giới hạn được báo rõ.
- [x] Viết test: hai người trùng tên/địa chỉ vẫn có hai ID; số dòng lỗi đúng khi có dòng rỗng xen giữa.
- [x] Cài đặt parser, chuẩn hóa khoảng trắng và cấu hình giới hạn dung lượng/số dòng; ghi giá trị chọn vào tài liệu phase.
- [x] Kết nối upload và bảng dữ liệu; hiển thị tổng Nam/Nữ, lỗi từng dòng, trạng thái chưa xác minh.
- [x] Dùng file mẫu nguồn nếu đã có trong workspace và xác nhận giả lập; nếu chưa có, tạo fixture giả lập 30 người (18 Nam, 12 Nữ) và ghi rõ nguồn tạo.
- [x] Chạy `python -m pytest tests/test_excel.py tests/test_students_api.py -q` trong môi trường ảo, rồi thử upload qua giao diện.

**Điều kiện hoàn thành:** AC-01, AC-02 đạt; không mất/gộp sinh viên; file mẫu và lỗi nhập liệu tái lập được. Truy vết BR-01.

## 7. Phase 3 — Geocoding và xác nhận vị trí

**Mục tiêu:** Mọi vị trí đưa vào thuật toán đều đã được kiểm tra và giảng viên xác nhận.

**File:** `geocoding.py`, `geocoding_service.py`; cập nhật schema sinh viên và các file frontend; thêm `tests/test_geocoding.py`, `tests/test_geocoding_api.py`, `docs/reports/geocoding-validation.md`.

**Giao tiếp:** `POST /api/geocode/batch` xử lý danh sách địa chỉ; `POST /api/geocode/retry` xử lý lại `student_id` với địa chỉ đã sửa. Trả tọa độ đại diện, địa chỉ khớp, loại kết quả, confidence, ứng viên và trạng thái theo BRD. Kết quả từ dịch vụ chưa được người dùng xác nhận không tự chuyển thành `verified`.

- [x] Viết mock test cho thành công, không kết quả, nhiều ứng viên, chỉ khớp thành phố, ngoài vùng, timeout, quota và khóa không hợp lệ.
- [x] Cài đặt gọi Geoapify từ backend, giới hạn request/thời gian chờ, xử lý lỗi dễ hiểu và cache chỉ trong phạm vi phiên.
- [x] Làm bảng sửa/retry, bản đồ kiểm tra và thao tác xác nhận; giữ nguyên ID, tên và giới tính khi sửa địa chỉ.
- [x] Kiểm tra sửa địa chỉ xóa tọa độ/xác nhận cũ; response đến muộn không ghi đè dữ liệu mới; upload mới thay thế trạng thái phiên cũ.
- [x] Chặn nút chia nhóm nếu còn dòng chưa `verified`; chuẩn bị cùng quy tắc validate tại endpoint grouping ở phase 4.
- [x] Chạy `python -m pytest tests/test_geocoding.py tests/test_geocoding_api.py -q`.
- [x] Kiểm thử Geoapify thật với địa chỉ đại diện trong vùng nghiên cứu, cả cách ghi cũ và mới; ghi ứng viên, kết quả đối chiếu, ngưỡng/vùng lọc đã chọn và hạn chế vào báo cáo, không ghi khóa.

**Điều kiện hoàn thành:** AC-03, AC-04 đạt; phần giao diện AC-05 đạt và được hoàn tất phía backend ở phase 4. Có bằng chứng API thật riêng với mock test. Nếu API thật chưa kiểm tra được, ghi rõ phần còn thiếu, không đánh dấu phase hoàn tất. Truy vết BR-02, BR-03, BR-09.

## 8. Phase 4 — Thuật toán chia nhóm và thống kê

**Mục tiêu:** Chia đúng `k` nhóm, đủ người, cân bằng quy mô và giải thích được sai lệch tỷ lệ.

**File:** `group.py`, `groups.py`, `grouping_service.py`, `metrics_service.py`; thêm `tests/test_grouping.py`, `tests/test_metrics.py`, `tests/test_groups_api.py`.

**Giao tiếp:** `POST /api/groups/generate` nhận danh sách sinh viên đã xác nhận cùng `target_male`, `target_female`; trả `k`, `assignments`, `groups`, `overall_metrics`, `warnings`. Schema chính xác và cách phân bổ số lượng từng giới theo nhóm phải được ghi rõ trong kế hoạch chi tiết phase trước khi triển khai.

- [x] Viết test công thức `k` cho N=30, 34, 42, 3 với M+F=5; từ chối N=0, M=F=0, số âm, số không nguyên, tọa độ thiếu và vị trí chưa xác nhận.
- [x] Viết test 30 người, 18 Nam/12 Nữ, M=3/F=2 phải cho 6 nhóm, mỗi nhóm đúng 3 Nam/2 Nữ.
- [x] Viết test số dư, một giới ít hơn `k`, chỉ có một giới, nhóm một người, M=0/F=0 hợp lệ và nhiều tọa độ trùng nhau.
- [x] Cài đặt chiếu tọa độ sang hệ mét phù hợp; K-Means riêng từng giới với seed cố định; cân bằng, ghép Hungarian và fallback theo Phụ lục A.
- [x] Kiểm tra sau phân nhóm: tập ID giữ nguyên, mỗi ID đúng một lần, đủ `k` nhóm không rỗng, quy mô chênh tối đa 1 theo BRD; vi phạm không được trả thành công.
- [x] Cài đặt Haversine, thống kê Nam/Nữ và cảnh báo sai lệch; định nghĩa rõ cách tổng hợp trung bình toàn bộ nhóm. Nhóm một người có khoảng cách nội nhóm bằng 0, không chia cho 0.
- [x] Chạy `python -m pytest tests/test_grouping.py tests/test_metrics.py tests/test_groups_api.py -q`; đối chiếu khả năng tái lập bằng cùng dữ liệu và seed.

**Điều kiện hoàn thành:** AC-05 phía backend và AC-06 đến AC-09 đạt; thống kê có unit test với khoảng cách đã biết. Truy vết BR-03, BR-04, BR-05, một phần BR-08.

## 9. Phase 5 — WebGIS kết quả và luồng tương tác

**Mục tiêu:** Hoàn thiện luồng từ danh sách đã xác minh đến kết quả có thể kiểm tra trực quan.

**File:** `frontend/index.html`, `frontend/css/style.css`, `frontend/js/app.js`, `api.js`, `map.js`, `state.js`; thêm `docs/reports/ui-checklist.md`.

**Giao tiếp:** Dùng kết quả API phase 4 làm nguồn chung cho bảng, marker và thống kê. Trạng thái phiên giữ bản đầu vào và kết quả tương ứng; khi đầu vào thay đổi, kết quả không còn được dùng để xuất.

- [x] Làm hai ô Nam/Nữ, hiển thị `k` dự kiến theo đúng công thức và trạng thái đang xử lý/lỗi.
- [x] Hiển thị marker có màu và nhãn nhóm, popup, bộ lọc nhóm, bảng thành viên và thống kê Haversine.
- [x] Đồng bộ thao tác lọc giữa bản đồ/bảng; phân biệt rõ tổng toàn bộ dữ liệu và số người đang xem.
- [x] Khi sửa địa chỉ, thay M/F hoặc upload mới, vô hiệu hóa kết quả cũ; bỏ qua response chia nhóm đã lỗi thời.
- [x] Kiểm tra trình duyệt: đủ 30 người, lọc từng nhóm khớp API, thao tác nhanh không nhận kết quả cũ, lỗi backend không báo thành công.
- [x] Kiểm tra giao diện máy tính và xem kết quả trên điện thoại, nhãn ngoài màu sắc, ghi công bản đồ, thông báo tiếng Việt; lưu checklist thực tế.

Bằng chứng: [báo cáo Phase 5](../../reports/phase-5.md), [checklist UI](../../reports/ui-checklist.md). Leaflet thật đã kiểm tra; ảnh nền OSM còn lỗi kết nối trong môi trường kiểm tra. Nút xuất luôn disabled trong phase này và ghi rõ Phase 6.

**Điều kiện hoàn thành:** AC-10 và phần vô hiệu hóa kết quả của AC-14 đạt. Nút xuất chỉ sẵn sàng với kết quả còn hiệu lực; chức năng download hoàn thành ở phase 6. Truy vết BR-06.

## 10. Phase 6 — Xuất kết quả Excel

**Mục tiêu:** File tải về khớp chính xác với kết quả phân nhóm hiện hành.

**File:** `export_service.py`, endpoint export trong `groups.py`; cập nhật frontend; thêm `tests/test_export.py`, `tests/test_export_api.py`.

**Giao tiếp:** `POST /api/groups/export` nhận kết quả hợp lệ đang hiển thị, trả `.xlsx`. Hai sheet là `Danh_sach_nhom` và `Thong_ke_nhom`; cột theo mục 9 của BRD. Backend kiểm tra cấu trúc và tính nhất quán dữ liệu trước khi sinh file.

- [x] Viết test đúng hai sheet, đủ N thành viên, nhóm/số lượng/thống kê khớp, thứ tự ổn định và không xuất lat/lon mặc định.
- [x] Viết test dữ liệu đầu vào bất nhất bị từ chối, chuỗi bắt đầu bằng `=` được ghi như văn bản, không trở thành công thức Excel.
- [x] Sinh file trong bộ nhớ hoặc dọn file tạm sau xử lý; chỉ chứa dữ liệu phiên hiện tại.
- [x] Kết nối nút tải file; sửa đầu vào phải chặn xuất tới khi tính lại; bộ lọc hiển thị không âm thầm làm mất nhóm trong file xuất toàn bộ.
- [x] Chạy `python -m pytest tests/test_export.py tests/test_export_api.py -q`; tải file từ trình duyệt và mở đối chiếu với kết quả WebGIS.

Bổ sung theo yêu cầu: nguồn Geoapify / OSM dự phòng, proxy che khóa và kiểm tra ảnh thật. Bằng chứng, kiểm thử và giới hạn ở [báo cáo Phase 6](../../reports/phase-6.md).

**Điều kiện hoàn thành:** AC-11 và AC-14 hoàn chỉnh đạt; không lưu file người dùng lâu dài. Truy vết BR-07 và BR-09.

## 11. Phase 7 — Tích hợp, đánh giá và nghiệm thu

**Mục tiêu:** Có bằng chứng chạy toàn luồng, số liệu đánh giá và bộ demo/báo cáo tái lập được.

**File:** `tests/integration/test_workflow.py`, `scripts/evaluate_grouping.py`, `tests/test_evaluation.py`, `docs/reports/evaluation.md`, `docs/reports/acceptance.md`; cập nhật hướng dẫn README.

- [x] Viết integration test import → geocoding mock → xác nhận → grouping → export; kiểm tra ID, số người và số nhóm xuyên suốt.
- [x] Chạy luồng thực với dữ liệu giả lập qua Geoapify, sửa một địa chỉ lỗi, xác nhận vị trí, chia nhóm và mở Excel xuất; ghi bằng chứng riêng với integration mock.
- [x] Viết test baseline giữ cùng N, k, quy mô và ràng buộc giới khi khả thi; cùng seed tái lập kết quả, không dùng dữ liệu chưa xác nhận để báo cáo thực nghiệm.
- [x] Tạo công cụ so sánh K-Means/cân bằng/Hungarian với baseline ngẫu nhiên nhiều seed cố định; ghi seed, dữ liệu, cách tổng hợp, trung bình/phân tán và kết quả chạy thực tế.
- [x] Đo tỷ lệ geocoding, số địa chỉ sửa, khoảng cách nội nhóm, số người thiếu/lặp; không khẳng định thuật toán tốt hơn baseline nếu số liệu không chứng minh.
- [x] Kiểm tra dữ liệu giữa hai phiên không lẫn nhau, refresh không có lịch sử server, log/response không chứa khóa hay dữ liệu cá nhân, file tạm được dọn.
- [x] Chạy `python -m pytest -q`; hoàn tất checklist UI và đánh dấu AC-01 đến AC-14 theo bằng chứng thực tế trong `docs/reports/acceptance.md`.
- [x] Hoàn thiện hướng dẫn PowerShell, bộ dữ liệu giả lập, ảnh demo và giới hạn đề tài. Triển khai hosting là tùy chọn, chỉ xem xét sau khi local đạt nghiệm thu.

**Điều kiện hoàn thành:** AC-12, AC-13 đạt và toàn bộ AC-01 đến AC-14 có bằng chứng; các vấn đề chưa đạt được ghi rõ. Truy vết BR-01 đến BR-09; không coi hosting là điều kiện bắt buộc của MVP.

## 12. Ma trận nghiệm thu

| Tiêu chí BRD | Phase chịu trách nhiệm chính | Bằng chứng cần có |
|---|---|---|
| AC-01, AC-02 | 2 | Test nhập Excel và kiểm tra bảng/lỗi theo dòng |
| AC-03, AC-04 | 3 | Mock test, kiểm thử Geoapify thật và sửa/retry trên web |
| AC-05 | 3, 4 | Chặn ở giao diện và từ chối tại API khi vị trí chưa xác nhận |
| AC-06 | 4 | Test công thức k và đầu vào không hợp lệ |
| AC-07 | 4 | 30 người, 18 Nam/12 Nữ cho 6 nhóm đúng 3+2 |
| AC-08, AC-09 | 4 | Test số dư/thiếu giới, đủ ID, không trùng, cân bằng quy mô |
| AC-10 | 5 | Checklist bản đồ, bộ lọc, bảng và thống kê nhất quán |
| AC-11 | 6 | Test hai sheet và đối chiếu file tải về |
| AC-12 | 7 | Bộ test, phép đo Haversine và báo cáo baseline thực nghiệm |
| AC-13 | 1–7, tổng kiểm tra ở 7 | Cấu hình khóa, dữ liệu giả lập, không lưu lịch sử/file tạm lâu dài |
| AC-14 | 5, 6 | Sửa đầu vào chặn xuất; tính lại rồi xuất đúng kết quả mới |

## 13. Quy tắc kết thúc một phase

1. Đối chiếu đầu ra với BRD và checklist phase; chỉ đánh dấu mục đã có bằng chứng.
2. Chạy kiểm thử liên quan và kiểm tra hồi quy các luồng bị thay đổi; lưu lệnh/kết quả thực tế.
3. Báo cáo file đã thay đổi, cách chạy trên PowerShell, điều kiện nghiệm thu đạt/chưa đạt và vấn đề còn lại.
4. Cập nhật trạng thái phase: `Chưa bắt đầu` → `Đang thực hiện` → `Hoàn thành`; nếu thiếu điều kiện bên ngoài, ghi cụ thể việc còn chờ.
5. Chốt mốc thay đổi Git riêng cho phase khi thực hiện commit; không gộp thay đổi ngoài phạm vi và không đưa secrets/dữ liệu thực vào commit.

**Điểm tiếp theo:** chỉnh giao diện theo phản hồi của người dùng; không bắt buộc hosting cho MVP local. Phase 7 đã bổ sung kiểm thử tích hợp và baseline có số liệu; xem [kế hoạch và bằng chứng Phase 7](2026-10-24-phase-7-acceptance.md). Hợp đồng API và metrics ở [kế hoạch Phase 4](2026-10-23-phase-4-grouping.md).
