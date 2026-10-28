# Checklist giao diện sau Phase 7

Bạn có thể chỉnh bố cục, màu sắc, chữ, khoảng cách, bảng và cách trình bày sau khi nghiệm thu logic. Phase 7 không khóa thiết kế giao diện. Nếu đổi thao tác hoặc các phần tử mà JavaScript dùng, cần cập nhật test tương ứng.

- [x] Desktop 1440×1000 và mobile 390×844 không tràn ngang; bảng dài cuộn trong khung.
- [x] Import tự khởi chạy tra cứu, hiển thị số tự động/cần xử lý; không yêu cầu chọn lại 30 địa chỉ mẫu.
- [x] Không cho chia nhóm khi còn ngoại lệ; địa chỉ sai có sửa/retry.
- [x] Điểm trùng vẫn xem đủ thành viên/nhóm; bộ lọc không làm Excel thiếu người.
- [x] Nền bản đồ thật có attribution; nguồn hỏng có fallback và retry.
- [x] Đổi file/địa chỉ/target vô hiệu hóa nhóm và file cũ; phản hồi trễ không khôi phục kết quả cũ.
- [x] Hai phiên không lẫn dữ liệu; refresh xóa dữ liệu phiên.
- [x] Excel tải xuống mở được, đủ người và thống kê; 0 lỗi JavaScript trong các lượt browser check.
- [ ] Chốt bố cục, màu sắc và cách trình bày theo phản hồi của chủ dự án — để đợt chỉnh giao diện sau, không chặn nghiệm thu logic.

Trước khi bàn giao một lần sửa giao diện, chạy `scripts/check_phase7_browser.py` cùng browser test của phần bị đổi. Khi sửa map/CSS kích thước, chạy thêm `scripts/check_phase5_browser.py --map`, `scripts/check_shared_locations_browser.py` và kiểm tra ảnh desktop/mobile. Nếu sửa luồng xuất hoặc trạng thái đầu vào, chạy thêm `scripts/check_phase6_browser.py` và `scripts/check_automatic_location_browser.py`. Không bỏ assertion chỉ để giao diện mới vượt test; cập nhật selector khi cách truy cập phần tử thay đổi có chủ đích.

Ảnh nghiệm thu chức năng hiện tại: `.local-tests/phase-7/live-desktop.png`, `live-mobile.png`. Không dùng các ảnh này làm yêu cầu thiết kế cố định.
