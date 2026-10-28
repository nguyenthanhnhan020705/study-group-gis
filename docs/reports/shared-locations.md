# Cư xá theo giới tính và điểm có nhiều sinh viên

Cập nhật theo thông tin người dùng cung cấp ngày 23/10/2026. Quy tắc cư xá dưới đây là yêu cầu nghiệp vụ của chủ dự án, không phải thông tin suy ra từ Geoapify hoặc xác nhận của đơn vị quản lý.

| Cư xá NLU | Giới tính được chọn/xác nhận |
|---|---|
| A, C | Nam |
| B, D | Nữ |
| E, KTX Cỏ May | Nam và Nữ |

KTX Cỏ May vẫn là địa danh riêng. Có chuỗi địa chỉ chuẩn sau sáp nhập trong file mẫu và alias `KTX Cỏ May, phường Linh Xuân, TP.HCM`. Tọa độ lấy thật từ Geoapify Places, OSM way 609150034 đã đối chiếu; không nhúng tọa độ trong Excel hoặc tự đặt confidence.

Candidate NLU có `allowed_genders`. Giao diện vẫn hiển thị các cư xá để nhận biết nhưng vô hiệu hóa lựa chọn không phù hợp; lớp state cũng từ chối xác nhận sai giới, kể cả bỏ qua thuộc tính disabled của dropdown. Chọn E hoặc Cỏ May hợp lệ với cả hai giới; không tự chọn tòa thay người dùng. Không gửi tên/giới tính sinh viên tới nhà cung cấp bản đồ. Giới tính trong payload phân nhóm vẫn được kiểm tra theo schema Phase 4; quy tắc cư xá này kiểm soát thao tác chọn/xác nhận trong giao diện hiện tại.

## Điểm trùng và popup

- Các sinh viên **đã xác nhận** có cùng lat/lon được biểu diễn bằng một marker; danh sách sinh viên trong state/phân nhóm vẫn giữ từng người riêng.
- Marker nhiều người có nhãn số lượng. Click mở popup có tổng số, tên, giới tính, ID của mọi sinh viên tại điểm; có địa chỉ đại diện và nhãn nhóm nếu dữ liệu có nhóm.
- Danh sách dài cuộn được; tên trùng không bị gộp mất, HTML trong tên/địa chỉ được hiển thị dạng văn bản an toàn.
- Preview cùng tọa độ dùng chung marker nhưng ghi rõ chưa xác nhận, không tăng số sinh viên. Sửa địa chỉ của một người xóa xác nhận/điểm của riêng người đó, người còn lại giữ nguyên.
- Chỉ gộp tọa độ bằng nhau chính xác. Không làm tròn, dịch tọa độ, hoặc gộp hai tọa độ khác nhau chỉ vì chuỗi địa chỉ giống nhau. Các địa chỉ trong cùng phiên có thể dùng cache chung kết quả nhưng mỗi sinh viên vẫn cần xác nhận riêng.

## File mẫu và kiểm thử

Mẫu 10 người trước đây đã được thay thế và xóa. Dùng [file báo cáo 30 người](../../data/samples/danh_sach_sinh_vien_bao_cao.xlsx), 18 Nam/12 Nữ, đủ A–E/Cỏ May/khu B và hai đường ngoài KTX. Tái tạo bằng `scripts/create_report_sample.py`; [kết quả mới](report-sample.md). Các kết quả 10 người bên dưới là lịch sử lần kiểm tra trước.

6 test backend mới được chạy RED trước thay đổi rồi GREEN cho toàn bộ chính sách A–E và Cỏ May. Toàn suite hiện **143 passed**. `scripts/check_shared_locations_browser.py` được chạy RED trước khi thêm nhóm điểm/guard, rồi GREEN: nhóm theo tọa độ chính xác, giữ người trùng tên/địa chỉ, XSS an toàn, danh sách 100 người có cuộn, preview không đếm lặp và lựa chọn sai giới bị chặn ở dropdown lẫn state. `scripts/check_phase3_browser.py` hồi quy toàn bộ luồng cũ và mobile cũng đạt. Reviewer độc lập không có finding cần sửa.

Kiểm tra live hiện tại bằng `scripts/check_shared_locations_live.py` dùng backend8001/frontend5500 và cửa sổ demo9223, không mock provider hoặc chèn tọa độ. Script hiện dùng mẫu 30 người và ghi tại `.local-tests/report-sample/` (Git ignore); artifacts lần 10 người ở `.local-tests/shared-locations/live/`.

Lần chạy thật đã đạt: **10/10 xác nhận, 5 tọa độ khác nhau, 5 marker đều có nhãn 2**. Click từng điểm có đúng hai dòng sinh viên tương ứng 01–02 (A), 03–04 (B), 05–06 (E), 07–08 (Cỏ May), 09–10 (khu B). Hai điểm E/Cỏ May đều có một Nam và một Nữ. Tất cả tọa độ lấy từ Places thật, không dựng trong Excel. Đã xem ảnh popup E và Cỏ May; nhãn đúng địa chỉ mới và đầy đủ người. Cửa sổ demo giữ ở popup A cho người dùng.

Các địa điểm khác nhau nhưng rất gần (ví dụ E và Cỏ May) vẫn có thể nhìn gần chồng ở mức thu nhỏ; phóng to để chọn riêng. Không dịch tọa độ hoặc gộp hai tòa khác nhau để làm hình đẹp. Script kiểm tra phóng to khi cần và không force-click qua điểm khác. Danh sách cùng tọa độ luôn dùng một marker/popup chung ở mọi mức zoom.
