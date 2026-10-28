# Nghiệm thu Phase 7 — 25/10/2026

Phạm vi: kiểm thử tích hợp, đánh giá baseline và nghiệm thu MVP local hiện có. Giữ giao diện để người dùng chỉnh cách trình bày sau. Không triển khai hosting, đăng nhập, cơ sở dữ liệu hay lịch sử. Báo cáo chức năng đạt theo bằng chứng dưới đây; kiểm tra độc lập cuối đợt được ghi ở phần review.

## Kết quả chạy

| Lệnh (tiền tố `./.venv/Scripts/python.exe -B`) | Kết quả ngày 25/10/2026 | Nguồn |
|---|---|---|
| `-m pytest -q -p no:cacheprovider` | 243 passed, 27,89 giây; exit 0 | Offline, unit/API/integration |
| `-m pytest tests/integration -q -p no:cacheprovider` | 6 passed; exit 0 | MockTransport tại HTTP Geoapify |
| `-m pytest tests/test_evaluation.py -q -p no:cacheprovider` | 15 passed; exit 0 | Snapshot/thuật toán thật, offline |
| `scripts/check_phase7_browser.py` | PASS; exit 0 | UI và API thật; Geoapify fixture, chặn tài nguyên ngoài |
| `scripts/check_automatic_location_browser.py` | PASS 100 dòng, 98 auto/2 ngoại lệ, 2 lookup; lỗi dịch vụ dừng sau một request | Phản hồi geocode giả lập |
| `scripts/check_phase2_browser.py` | PASS import/lỗi dòng/mobile/response cũ | API import thật |
| `scripts/check_phase3_browser.py` | PASS chọn ứng viên/sửa/retry/response cũ/mobile | Geocoding fixture |
| `scripts/check_phase5_browser.py --map` | PASS nhóm/bộ lọc/metrics/XSS/stale/refresh | API thật, ảnh nền bị chặn trong test |
| `scripts/check_phase6_browser.py` | PASS Excel/lỗi ZIP/XML/stale/fallback/retry | API Excel thật, ảnh nền fixture |
| `scripts/check_shared_locations_browser.py` | PASS điểm trùng/popup 100 người/giới tính | Fixture |
| `scripts/check_phase7_live.py` | PASS; exit 0 | Geoapify + Leaflet + ảnh nền thật |
| `scripts/run_local.py --check` | READY; exit 0 sau khởi động lại | HTTP/CORS/assets thật ngoài sandbox |

Log, workbook và ảnh chi tiết: `.local-tests/phase-7/` (không đưa vào Git). Đánh giá tái lập và nguồn điểm được giữ trong `data/evaluation/`. Bộ test đầu đợt 222 passed; cuối đợt thêm 21 test = 243. Việc kiểm thử kết quả đã có là characterization, không sửa đúng thành sai để tạo RED. Công cụ đánh giá mới có bước RED do thiếu command trước khi triển khai, rồi 15 GREEN.

## Luồng dịch vụ thật

Lần nghiệm thu bắt đầu 08:17:01 giờ Việt Nam (01:17:01 UTC). Mẫu 30 người/9 địa chỉ: **30 tự động, 0 cần đối chiếu, 0 lỗi, 0 xác nhận tay**, 9 request tra cứu qua backend, 26,097 giây từ import đến kết thúc geocode. Đây là tỷ lệ tự động hóa **trên mẫu**, không phải độ chính xác 100% cho file bất kỳ.

Đã xem kết quả cho đủ chín điểm: cư xá A/C/B/D/E khớp lần lượt OSM way 291412044/291412048/291412047/726200672/609150037; Cỏ May way 609150034; KTX B ĐHQG node 11562800202. Võ Văn Ngân và Kha Vạn Cân chọn điểm thuộc phường Thủ Đức theo registry. Với Kha Vạn Cân, ứng viên phường Hiệp Bình bị loại; chọn ứng viên thứ hai đúng phường. [Nguồn, nhãn và tọa độ](../../data/evaluation/provenance-sample-30.json). Đối chiếu này kiểm tra danh tính/điểm đại diện, không xác minh nơi ở thực tế của từng người.

Sau khi tạo sáu nhóm, cố ý sửa một địa chỉ thành không xác định: tọa độ và kết quả nhóm cũ bị xóa, không cho xuất. Sửa lại địa chỉ rõ ràng → retry → xác định đủ 30 → tạo lại sáu nhóm → mở Excel hai sheet với 30 thành viên/sáu dòng thống kê. Hai request thêm để thử lỗi/sửa, tổng 11; không có sửa tay cần thiết ở lượt import ban đầu.

Ảnh nền thật dùng Geoapify/OSM, attribution `© OpenStreetMap contributors · Geoapify`. Đã xem `live-desktop.png` (1440×1000) và `live-mobile.png` (390×844); có marker, ảnh nền, attribution và không tràn ngang. 0 lỗi JavaScript. [Kết quả khoảng cách và baseline](evaluation.md).

Lần thử trong sandbox bị chặn mạng: 1 lỗi dịch vụ và 29 dòng **chưa xử lý**, không ghi nhận là 30 địa chỉ sai. Chạy lại với quyền mạng mới có kết quả thật trên. Giới hạn quota/mạng hoặc dữ liệu provider thay đổi vẫn có thể làm lần chạy khác cần xử lý ngoại lệ.

## Đối chiếu nghiệm thu

| AC | Kết quả | Bằng chứng |
|---|---|---|
| 01 | Đạt | Import mẫu 30, 18 Nam/12 Nữ; `test_workflow`, browser Phase 2/7 |
| 02 | Đạt | `test_excel`, `test_students_api`, browser lỗi dòng, giữ nguyên bản ghi |
| 03 | Đạt | Geoapify đi qua backend, không key trong request trình duyệt; kiểm tra riêng key bên dưới |
| 04 | Đạt | Live sửa địa chỉ lỗi rồi retry, kiểm tra xóa tọa độ cũ |
| 05 | Đạt | `test_groups_api` từ chối chưa xác nhận; browser Phase 7 chặn nữ ở cư xá A |
| 06 | Đạt | `test_grouping`, browser tham số và số nhóm |
| 07 | Đạt | Mẫu thật qua service: 6 nhóm × (3 Nam + 2 Nữ) |
| 08 | Đạt | Nhóm dư/thiếu giới/singleton trong unit/API và evaluation |
| 09 | Đạt | Bảo toàn ID xuyên import→geocode→group→export; audit thiếu/lặp 0 |
| 10 | Đạt | Bộ lọc/bảng/metrics/marker/popup; test fallback và ảnh nền thật |
| 11 | Đạt | Workbook mở bằng openpyxl, đủ 30 người/6 nhóm, đúng hai sheet |
| 12 | Đạt | [Evaluation](evaluation.md), 30 baseline seed cùng quota và Haversine có test |
| 13 | Đạt trong MVP local | Fake sample, kiểm tra hai phiên/refresh, key ignored/untracked, không lịch sử/file lưu lâu dài |
| 14 | Đạt | Sửa địa chỉ/đổi target/import khi chờ geocode/group/export, chặn response/file cũ |

## Phiên, dữ liệu và vận hành

Hai browser context nhập danh sách khác nhau và cùng địa chỉ: dữ liệu/nhóm không lẫn nhau, cache vẫn kiểm tra giới tính mỗi sinh viên. Refresh cả hai xóa danh sách và nhóm; localStorage/sessionStorage trống. Backend không có endpoint lấy lịch sử, cache geocode chỉ trong một batch. Cache tile chỉ giữ ảnh công cộng. Import đóng multipart context, xuất bằng BytesIO; không tạo kho file người dùng lâu dài. Test thư mục làm việc tạm trống sau import/group/export và rà mã các đường ghi file; đây không phải giám sát mọi filesystem hệ điều hành.

Khóa thật chỉ được đọc để so sánh byte nội bộ, không in ra. Scan frontend/docs/scripts/tests/data đánh giá và log/JSON Phase 7 không thấy khóa; `git check-ignore backend/.env` đạt, `git ls-files backend/.env` rỗng. Response lỗi provider không chứa khóa; lỗi chia nhóm không echo payload sinh viên. Response import/group thành công đương nhiên chứa danh sách người dùng để frontend hiển thị; không phải endpoint công khai xem lịch sử. Log mặc định chỉ có phương thức/route/status, không tên sinh viên; không bao gồm cấu hình debug HTTP tùy chỉnh bên ngoài dự án.

Launcher chạy hai dịch vụ, đã kiểm tra Ctrl+C in `Stopped both local services`, rồi chạy lại và health/CORS/assets đạt. Mã exit 1 của PowerShell PTY khi gửi Ctrl+C là thao tác ngắt; không phải crash ứng dụng. Kiểm tra ngoài sandbox xác nhận bản chạy lại truy cập được. Truy cập `http://127.0.0.1:5500`; chạy lại bằng `start-webgis.cmd` khi máy/runner dừng. Không tự cài Windows service/autostart.

## Giới hạn và review

Chưa đo uptime dài hạn, chưa benchmark tải nhiều giảng viên/1000 dòng, chưa nghiệm thu triển khai internet. API hiện theo phiên và một job chia nhóm mỗi process; cần thiết kế giới hạn dùng chung khi đổi sang nhiều worker. Độ chính xác geocoding với file thực không có ground truth; địa chỉ thiếu tòa/phường vẫn cần bổ sung. UI hiện tại được kiểm tra hoạt động, không chốt thiết kế cuối; xem [checklist chỉnh giao diện](ui-checklist.md).

Review độc lập cuối đợt: **đạt nghiệm thu Phase 7, không có Critical/Important**. Reviewer tái tính report khớp hoàn toàn, kiểm tra SHA256, đối chiếu 30 tọa độ với chín nguồn, rà test/log và ảnh desktop/mobile. Không chạy lại dịch vụ ngoài hoặc đọc giá trị secret.

Một cải thiện nhỏ để sau: `scripts/check_phase7_live.py` đang cộng các dòng `pending` chưa được tra cứu vào `review` khi dịch vụ lỗi giữa hàng đợi. Nên bổ sung trường `pending` và chỉ đếm `needs_review` vào `review`. Lượt thành công được công bố không bị ảnh hưởng; đoạn báo cáo lỗi sandbox bên trên đã phân biệt đúng 1 lỗi và 29 chưa xử lý. Đây là vấn đề phân loại trong script chẩn đoán, không phải tự xác nhận sai trong ứng dụng.

Các quyết định thực thi: giữ workspace hiện tại vì Phase 1–6 chưa commit; không tạo worktree từ HEAD thiếu mã hiện có (đổi lại các thay đổi cùng nằm một thư mục). Giữ ledger/bằng chứng PowerShell vì chưa có commit làm hồ sơ thay thế (theo dõi tiến độ thủ công). Test tích hợp mô tả hành vi có sẵn, không cố ý phá mã đúng để làm RED (đòi hỏi expectation độc lập và review); công cụ đánh giá mới vẫn test trước. Tái sử dụng các browser regression cho ma trận stale response thay vì sao chép (cần chạy đủ các lệnh được liệt kê). Chỉ xác nhận danh tính địa danh/điểm đại diện theo registry, không nhận là đã đo độ chính xác nơi ở (accuracy vẫn chưa đo). Giữ thay đổi tại chỗ để người dùng kiểm tra, không commit/push/merge.

Các phạm vi reviewer không kết luận: thiết kế giao diện để người dùng chỉnh sau; hosting/multiworker/uptime cần nghiệm thu riêng; độ chính xác nơi ở thật và khả năng thuật toán luôn tốt hơn cần thêm dữ liệu ground truth. Các giới hạn này được giữ nguyên, không phải điều kiện còn thiếu của Phase 7 theo phạm vi MVP local.
