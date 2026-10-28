# Hai ký túc xá và địa chỉ sau sáp nhập

Yêu cầu: thêm KTX Nông Lâm TP.HCM và KTX khu B ĐHQG-HCM vào file test, chạy lại và hiển thị đúng địa danh/địa chỉ mới. Giữ bước chọn/xác nhận, không yêu cầu số phòng hoặc nhập tọa độ.

Khảo sát thật: forward geocoding trả city/đường trùng tên, không có ứng viên đạt. Geoapify Places trả đúng node OSM 11562800202 của KTX khu B và các way dormitory 291412044/291412047/291412048/726200672/609150037 (Cư xá A/B/C/D/E) trong trường Nông Lâm. Không dùng tâm trường để thay vị trí KTX và không gán confidence giả.

Chọn tra cứu Places trực tiếp cho danh sách alias giới hạn của hai địa danh đã đối chiếu, thay vì hạ confidence hoặc nhúng tọa độ. API trả nguồn Geoapify Places/OSM, confidence=null, địa chỉ hiển thị chuẩn theo nguồn chính thức; chỉ chấp nhận OSM ID, tên/type, quốc gia và cả bounds nhỏ của địa điểm lẫn bounds dự án khớp. Địa chỉ khác vẫn dùng forward geocoding như cũ. Không chuẩn hóa hành chính toàn quốc bằng thay chuỗi tùy tiện.

Nông Lâm có nhiều cư xá, trả các lựa chọn tòa A–E; chọn A chỉ làm điểm đại diện khi dữ liệu chỉ ghi khu KTX. Không coi A là vị trí phòng của mọi sinh viên. KTX Cỏ May là địa danh khác, không tự gộp.

Nguồn địa chỉ: tài liệu tuyển sinh 2025 của Nông Lâm (khu phố 33, phường Linh Xuân, TP.HCM); trang Trung tâm DVSV xác nhận KTX thuộc trường; trang chủ/Thông báo 20/08/2025 của Trung tâm QLKTX&ĐTĐH xác nhận KTX khu B ở đường Mạc Đĩnh Chi, khu phố Tân Hòa, phường Đông Hòa, TP.HCM. Lưu liên kết đầy đủ trong báo cáo kiểm tra.

- [x] Test RED cho alias đúng/sai vùng, không nhầm khu A/Cỏ May, ID/tên/toạ độ bị thay đổi, lỗi an toàn, confidence không bị dựng, không tự verified; hồi quy rate-limit vẫn đạt.
- [x] Thêm known_places.py, mở rộng candidate nguồn, nối vào service có sẵn (giữ timeout/spacing/busy/cooldown), hiển thị nhãn nguồn.
- [x] Thêm hai địa chỉ chuẩn vào mẫu 30 và file kiểm tra tập trung 2 sinh viên; giữ tên cột bắt buộc `Nơi ở để học tập`.
- [x] Chạy unit/hồi quy và API/Edge thật, chọn vị trí, xác nhận2/2, lưu popup mới/ảnh và hướng dẫn nhập Excel.
- [x] Review độc lập không có finding; ghi hạn chế nhãn OSM nền và định nghĩa điểm đại diện.

Kết quả: 137 test đạt; browser thật hai KTX2/2 đạt; browser Phase3 hồi quy đạt; pip check/diff check sạch (chỉ thông báo LF→CRLF). Báo cáo `docs/reports/dormitory-addresses.md`. Giữ workspace chưa commit/push như các phase trước.
