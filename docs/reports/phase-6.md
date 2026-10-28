# Phase 6 — Xuất Excel và phục hồi bản đồ nền

Thực hiện ngày 24/10/2026 theo [kế hoạch chi tiết](../superpowers/plans/2026-10-24-phase-6-export-basemap.md), mục 9 của [BRD](../../README.md) và yêu cầu sửa kết nối nền bản đồ.

## Kết quả

- `POST /api/groups/export` nhận toàn bộ kết quả chia nhóm hiện hành, trả `danh_sach_nhom.xlsx` với đúng hai sheet `Danh_sach_nhom` và `Thong_ke_nhom`. Thứ tự nhóm/student_id ổn định; địa chỉ đại diện, số người, Nam/Nữ, khoảng cách và ghi chú lệch tỷ lệ khớp kết quả. Không xuất tọa độ thô.
- Backend kiểm tra bảo toàn ID/assignments, quy mô cân bằng, k, tỷ lệ và tính lại metrics Haversine; không chạy lại KMeans. Chặn dữ liệu bất nhất, vượt 1.000 người/`MAX_STUDENT_ROWS`, body vượt 8 MiB và ký tự XML không hợp lệ. Lỗi validation không phản chiếu dữ liệu sinh viên.
- Tạo workbook trong bộ nhớ, không lưu file người dùng ở backend. Nội dung người dùng là văn bản Excel, kể cả tên bắt đầu bằng `=`, `+`, `-`, `@`; không tạo công thức/hyperlink.
- Nút xuất tải toàn bộ nhóm dù giao diện đang lọc. Đổi M/F, sửa địa chỉ, chọn file mới hoặc chia lại hủy export đang chờ; response cũ không tải xuống. Lỗi HTTP, nội dung không phải XLSX, ZIP giả hoặc XML/CRC hỏng báo lỗi và cho thử lại. Browser kiểm tra directory/local entries, giới hạn giải nén, CRC và XML trước khi tải.
- Nền bản đồ thử OpenStreetMap tiêu chuẩn rồi tự chuyển Geoapify / OSM khi lỗi hoặc quá thời gian. Nguồn và attribution đổi theo ảnh thực; lỗi cả hai nguồn có nút thử lại. Các sự kiện từ layer cũ không ghi đè layer mới.
- Proxy Geoapify chỉ gọi endpoint `osm-carto` cố định, không theo redirect, không trả khóa cho browser. Giới hạn zoom 0..19, x/y trong zoom, ảnh 512 KiB, deadline tổng 10 giây gồm chờ slot và streaming; tối đa tám upstream đồng thời. Cache chỉ PNG có cấu trúc/CRC hợp lệ, tối đa 64 tile/300 giây; gặp 429 dừng gọi mới 30 giây. Cache là ảnh nền công cộng, không phải dữ liệu sinh viên.

## Chẩn đoán và kiểm tra kết nối thật

Headless Edge ngoài sandbox tái hiện `ERR_CONNECTION_REFUSED` từ `tile.openstreetmap.org`. CARTO tải được, nhưng [điều khoản basemap CARTO](https://carto.com/legal/basemap-terms/index.html) yêu cầu API key riêng; dùng nguồn Geoapify đã cấu hình thay vì thêm dịch vụ không có tài khoản. URL OSM giữ theo [chính sách tile chính thức](https://operations.osmfoundation.org/policies/tiles/); nguồn dự phòng theo [tài liệu Geoapify raster tiles](https://apidocs.geoapify.com/docs/maps/map-tiles/).

Probe Geoapify thật trả HTTP 200, `image/png`, 36.787 byte. Lần kiểm tra headless live ban đầu có một tile trả 503 và trạng thái lỗi được giữ đúng. Sau khi siết deadline/kiểm tra ảnh và khởi động lại backend, demo Edge thật tải đầy đủ ảnh nền qua proxy: tất cả tile đang hiển thị có `naturalWidth > 0`, trạng thái `ready`, nhãn `Geoapify / OSM`. Đã xem ảnh chụp để xác nhận có đường phố/địa danh thật, không dùng tile fixture trong demo.

## Bằng chứng kiểm thử

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
# 197 passed in 139.17s
.\.venv\Scripts\python.exe -B scripts/check_phase6_browser.py
.\.venv\Scripts\python.exe -B scripts/check_phase5_browser.py --map
.\.venv\Scripts\python.exe -B scripts/check_phase2_browser.py
.\.venv\Scripts\python.exe -B scripts/check_phase3_browser.py
.\.venv\Scripts\python.exe -B scripts/check_shared_locations_browser.py
```

- Baseline trước thay đổi: 151 tests. Thêm 25 tests export và 21 tests tile proxy; toàn suite cuối 197 tests đạt. RED quan sát được: module export/tile chưa có; nút export disabled; thiếu total deadline và PNG truncated chưa bị từ chối. Lỗi nền được tái hiện trực tiếp qua mạng trước khi sửa.
- Browser Phase 6 đạt: tải XLSX thật qua API, lọc còn năm người vẫn xuất 30 người/sáu nhóm; đối chiếu từng dòng, giới tính, địa chỉ và metrics bằng openpyxl; kiểm tra formula text, stale export, lỗi server/non-XLSX/ZIP giả/XML hỏng và retry.
- Browser bản đồ dùng Leaflet 1.9.4 thật: OSM lỗi chuyển nguồn đúng attribution; cả hai lỗi hiện error; retry phục hồi. Mặc định dùng network fixture PNG hợp lệ để tái lập offline. Chỉ demo thực dùng ảnh provider để chứng minh kết nối thật.
- Hồi quy Phase 2/3/5 và shared locations đạt. Script Phase 5 đổi `goto` sang `domcontentloaded` vì ảnh OSM có thể treo, đồng thời chặn proxy để kiểm thử marker không tiêu quota Geoapify. Desktop 1440px và mobile 390px không tràn trang.
- Review độc lập tìm hai Important (ZIP giả và thiếu deadline tổng) cùng một Minor (PNG truncated); đã sửa, thêm regression và review lại không còn Critical/Important.

Log/ảnh local (không commit): `.local-tests/phase-6/full-suite-final.log`, `browser-final.log`, `regression-phase*-final.log`, `export-desktop.png`, `export-mobile.png`; demo: `.local-tests/phase-6-demo/basemap.png`, `results.png`, `result.log`, `danh_sach_nhom.xlsx`.

## Demo hiện hành và giới hạn

Demo tại `http://127.0.0.1:5500/`, backend `8001`, dùng 30 sinh viên giả lập. Vị trí lấy từ kết quả Geoapify/OSM đã xác minh và lưu ở lần kiểm tra trước, có thông báo trên giao diện; chia nhóm được tính lại qua API hiện tại. Sáu nhóm, mỗi nhóm năm người (3 Nam/2 Nữ), trung bình nội nhóm 451,107 m, lớn nhất 3.226,656 m. Đây là khoảng cách đường chim bay giữa các cặp trong nhóm.

Tải workbook khi đang lọc Nhóm 2 rồi mở kiểm tra được 31 dòng danh sách và bảy dòng thống kê (gồm tiêu đề), đủ 30 người/sáu nhóm. Demo giữ cửa sổ Edge và server để người dùng kiểm tra; refresh xóa dữ liệu phiên như thiết kế.

Nguồn dự phòng vẫn phụ thuộc mạng, khóa và quota Geoapify; không bảo đảm dịch vụ ngoài luôn sẵn sàng. Kiểm tra ZIP dùng `DecompressionStream("deflate-raw")` của Edge/Chrome hiện đại, là môi trường đã kiểm thử. Chưa đo độ chính xác geocoding, hiệu năng 1.000 sinh viên hoặc so sánh baseline. AC-11 và AC-14 hoàn chỉnh đạt; Phase 7 (tích hợp toàn luồng, baseline, nghiệm thu tổng thể) chưa triển khai. Không commit/push hoặc deploy.
