# Demo Excel → bản đồ — 23/10/2026

Đây là báo cáo lịch sử: đã tạo `demo_phase3_12_sinh_vien.xlsx`, upload qua giao diện thật tại `http://127.0.0.1:5500` và dùng backend Geoapify thật ở cổng 8001. Workbook, script riêng và artifacts của demo này đã được xóa; mẫu đang dùng là [mẫu báo cáo 30 người](../../data/samples/danh_sach_sinh_vien_bao_cao.xlsx).

## Kết quả kiểm tra

- Excel có 12 sinh viên giả lập: 6 Nam, 6 Nữ; 12 địa chỉ đường/hẻm công cộng quanh Thủ Đức.
- Giao diện đọc đúng 12 dòng, không có lỗi nhập liệu.
- Sau geocoding: 12 dòng có ứng viên đủ điều kiện, 0 dòng tự xác nhận.
- Đã đối chiếu tên đường/hẻm, chọn ứng viên đại diện, mở preview và bấm xác nhận từng dòng của mẫu giả lập.
- Trạng thái cuối: **12/12 đã xác nhận**, 12 cặp tọa độ khác nhau, 12 marker có tâm nằm trong khung bản đồ, `allLocationsVerified()` trả `true`.
- Đã xem ảnh kết quả để kiểm tra các điểm cùng xuất hiện trên nền OSM, giữ cửa sổ Edge mở cho người dùng xem lại.

Mẫu đã được chuẩn bị sau khi thử địa chỉ: ghi rõ Hẻm 199 Đặng Văn Bi và Hẻm 171 Lê Văn Việt, tránh coi ứng viên hẻm là khớp chính xác toàn tuyến đường. Với Linh Trung, Đình Phong Phú và Nguyễn Văn Bá, chọn một đoạn đường làm điểm đại diện trong số các ứng viên cùng tên. Không chứa địa chỉ cư trú người thật; không có tọa độ dựng sẵn trong Excel hoặc mock phản hồi provider.

## Bằng chứng và cách xem

- Script tạo/upload riêng của demo 12 đã ngừng sử dụng. Để chạy demo hiện tại, dùng `scripts/check_shared_locations_live.py`.
- Ứng viên API thật: `.local-tests/phase-3/demo-12/candidates.json`.
- Trạng thái đã xác nhận: `.local-tests/phase-3/demo-12/confirmed.json`.
- Ảnh bản đồ: `.local-tests/phase-3/demo-12/map-12-students.png`.
- Ảnh số lượng xác nhận: `.local-tests/phase-3/demo-12/confirmed-count.png`.
- Các ảnh preview riêng từng sinh viên nằm cùng thư mục artifacts, bị Git bỏ qua.

Các đường dẫn artifacts trên ghi lại cấu trúc lần chạy cũ, không còn là file phải giữ hoặc điều kiện để chạy kiểm thử. Demo hiện tại dùng mẫu cư xá. Mở tab mới, refresh hoặc đóng tab không giữ trạng thái vì ứng dụng hiện chỉ lưu trong bộ nhớ phiên.

**Giới hạn:** 12/12 ở mẫu địa chỉ đã chọn không chứng minh mọi file Excel đều geocode đúng hoặc tự xuất hiện trên bản đồ. Địa chỉ tùy ý vẫn cần sửa, chọn và xác nhận; điểm là đại diện đường/hẻm, không phải vị trí nhà chính xác. Báo cáo 4 địa chỉ thử ban đầu vẫn được giữ riêng tại [geocoding-validation.md](geocoding-validation.md).
