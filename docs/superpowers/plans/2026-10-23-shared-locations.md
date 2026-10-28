# Quy tắc cư xá và popup nhiều sinh viên

Yêu cầu người dùng: NLU A/C Nam; B/D Nữ; E và Cỏ May cả hai. Điểm trùng phải cho xem tất cả sinh viên tại đó.

- Dùng quy tắc giới tính do người dùng cung cấp, không coi là dữ liệu suy ra từ Geoapify. Candidate NLU có allowed_genders; dropdown vô hiệu hóa lựa chọn sai và state guard cũng từ chối xác nhận. Không gửi tên/giới tính sinh viên cho provider. Cỏ May vẫn là địa danh riêng, lấy tọa độ thật từ ID đã đối chiếu 609150034, không gộp danh tính vào cư xá E.
- Gộp marker theo cặp lat/lon bằng nhau chính xác, không làm tròn hoặc dịch điểm để tách chồng. Sinh viên giữ riêng trong state/grouping. Cùng địa chỉ được geocode cùng điểm thì có một marker, popup liệt kê đủ ID/tên/giới tính và địa chỉ của tất cả người đã xác nhận.
- Popup có tổng số, danh sách cuộn và nhãn số lượng trên marker nếu >1 người; dùng DOM textContent để tránh HTML injection. Preview cùng tọa độ dùng chung marker và có nhãn chưa xác nhận, không tính thêm sinh viên. Khi sửa một người, chỉ người đó bị bỏ khỏi popup.
- Kiểm tra RED→GREEN bằng pytest metadata và Playwright chạy module UI thật: cùng tọa độ/tên trùng không mất người, địa chỉ khác nhau tại một tọa độ vẫn giữ danh sách, địa chỉ giống nhau nhưng tọa độ khác không tự gộp, preview không lặp người, 100 người có thể cuộn, HTML an toàn, guard giới tính.
- Thêm file mẫu nhiều sinh viên ở A/B/E/Cỏ May và KTX B; chạy API/Edge thật, xác nhận lựa chọn hợp lệ, kiểm tra popup nhiều người và giữ kết quả cho người dùng.
- Hồi quy toàn bộ test, review độc lập, cập nhật hướng dẫn và nguồn chính sách là thông tin người dùng cung cấp ngày 23/10/2026.
