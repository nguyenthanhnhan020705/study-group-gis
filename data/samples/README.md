# File mẫu báo cáo

Chỉ dùng [danh_sach_sinh_vien_bao_cao.xlsx](danh_sach_sinh_vien_bao_cao.xlsx): **30 sinh viên giả lập, 18 Nam/12 Nữ**, không chứa thông tin sinh viên thật hoặc tọa độ nhập sẵn.

Mọi địa chỉ trong mẫu dùng phường và Thành phố Hồ Chí Minh sau sáp nhập. Có đủ cư xá NLU A–E, Cỏ May, KTX khu B và hai đường ngoài KTX: Võ Văn Ngân, Kha Vạn Cân, phường Thủ Đức. Chín điểm có lần lượt 3/3/3/2/4/3/5/3/4 sinh viên.

Sheet đầu có ba cột bắt buộc: **Họ và tên**, **Giới tính**, **Nơi ở để học tập**. Từ cập nhật 24/10/2026, hệ thống đọc thêm cột **Điểm cần xác nhận** để tự đối chiếu tòa/đường; file riêng có thể dùng tên cột **Cư xá/Khu vực**. Địa chỉ gốc được giữ nguyên. Hai sheet phụ ghi kịch bản, số người trong popup và nguồn địa chỉ. Tái tạo từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe scripts/create_report_sample.py
```

Script ghi đè file mẫu giả lập cùng tên. Không đặt dữ liệu thật tại đường dẫn này.

## Nhiều sinh viên cùng cư xá

Upload rồi nhấn **Đọc danh sách**: hệ thống tự đối chiếu, tự đưa điểm rõ ràng lên bản đồ. Chỉ địa chỉ mơ hồ, thiếu thông tin hoặc lỗi dịch vụ mới hiện trong **Cần xử lý**; có thể xem toàn bộ bằng bộ lọc **Tất cả sinh viên**. NLU có nhiều tòa nên cần tên cư xá trong địa chỉ hoặc cột cuối; Cỏ May là địa danh riêng. Địa chỉ trùng dùng chung kết quả tra cứu nhưng giữ đủ từng sinh viên.

Quy tắc do người dùng cung cấp: A/C Nam, B/D Nữ, E/Cỏ May cả hai. Khi xác nhận đủ, bản đồ có 9 điểm; click mỗi điểm phải có đủ người trong sheet hướng dẫn. Kiểm tra bằng `scripts/check_shared_locations_live.py`, cần backend 8001/frontend 5500/Edge demo CDP 9223 và Internet. [Kết quả kiểm tra mẫu mới](../../docs/reports/report-sample.md).

Giữ tiêu đề cột địa chỉ là **Nơi ở để học tập**. [Hướng dẫn điền file thật, địa chỉ chuẩn, nguồn xác minh và giới hạn điểm đại diện](../../docs/reports/dormitory-addresses.md).

Ngoài KTX, đây là điểm đại diện đoạn đường, không phải số nhà/phòng trọ. Nhãn hai đường chỉ cập nhật khi khớp đường, phường, vùng và mức tin cậy; không sửa tọa độ. Toàn bộ workbook cũ và hai script tạo mẫu cũ được thay thế bằng mẫu duy nhất này. Không lưu Excel thật của sinh viên trong thư mục mẫu.
