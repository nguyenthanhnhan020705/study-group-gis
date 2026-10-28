# Mẫu Excel báo cáo dùng địa chỉ sau sáp nhập

Ngày cập nhật: 23/10/2026. [Workbook duy nhất](../../data/samples/danh_sach_sinh_vien_bao_cao.xlsx), tạo bằng `scripts/create_report_sample.py`. Toàn bộ tên là giả lập; không đưa dữ liệu sinh viên thật vào kho mã nguồn.

## Dữ liệu và thao tác

30 sinh viên, 18 Nam/12 Nữ. Sheet đầu có ba cột bắt buộc và cột hướng dẫn **Điểm cần xác nhận**. Cột hướng dẫn không được importer dùng để tự chọn tòa. Hai sheet phụ ghi kịch bản và nguồn địa chỉ; không có lat/lon nhập sẵn.

| Điểm cần chọn | Nam | Nữ | Tổng trong popup |
|---|---:|---:|---:|
| Cư xá A | 3 | 0 | 3 |
| Cư xá C | 3 | 0 | 3 |
| Cư xá B | 0 | 3 | 3 |
| Cư xá D | 0 | 2 | 2 |
| Cư xá E | 2 | 2 | 4 |
| Cỏ May | 2 | 1 | 3 |
| KTX khu B ĐHQG-HCM | 3 | 2 | 5 |
| Võ Văn Ngân, phường Thủ Đức | 2 | 1 | 3 |
| Kha Vạn Cân, phường Thủ Đức | 3 | 1 | 4 |

Mọi địa chỉ trong mẫu kết thúc bằng Thành phố Hồ Chí Minh; không sử dụng tỉnh Bình Dương hoặc cấp thành phố Thủ Đức/Dĩ An cũ. Phường Thủ Đức là tên phường mới, được giữ đúng trong hai địa chỉ đường. Các dòng KTX NLU dùng địa chỉ khu thống nhất, sau đó chọn đúng A–E theo cột cuối; Cỏ May là địa danh riêng. [Nguồn và nghiệp vụ KTX](dormitory-addresses.md), [quy tắc cư xá và popup](shared-locations.md).

Hai đường ngoài KTX chỉ đại diện đoạn đường, không đại diện một số nhà/phòng trọ cụ thể. Cần khảo sát địa chỉ thật và xác minh lại từng ứng viên khi dùng dữ liệu thật.

## Nhãn địa chỉ từ dịch vụ bản đồ

Geoapify có thể trả đúng tọa độ/đường/phường nhưng còn cấp thành phố Thủ Đức cũ trong `formatted`. Registry nhỏ `backend/app/services/address_labels.py` chỉ xử lý **hai chuỗi địa chỉ đường đã đối chiếu**, yêu cầu đồng thời khớp tên đường, phường, mã VN-SG, kiểu street, vùng nhỏ, quốc gia và ngưỡng confidence hiện có. Kết quả khác phường không được xác nhận cho hai địa chỉ này. Không đổi tọa độ hoặc nâng confidence; giữ nhãn gốc trong `provider_formatted` và gắn nguồn nhãn hiện hành trong `address_source_url`.

Võ Văn Ngân thuộc phường Thủ Đức được đối chiếu từ [Chi cục Chăn nuôi và Thú y TP.HCM](https://chicuccntyhcm.gov.vn/new/2025/12/04/Tram-Chan-nuoi-va-Thu-y-khu-vuc-1.aspx). Đoạn Kha Vạn Cân thuộc phường Thủ Đức được đối chiếu từ [cổng Giáo dục nghề nghiệp TP.HCM](https://gdnn.tphcm.gov.vn/truong-cao-dang-cong-nghe-tp-ho-chi-minh). Không suy ra toàn tuyến Kha Vạn Cân nằm trong một phường; kết quả thuộc Hiệp Bình bị loại khỏi lựa chọn của địa chỉ mẫu phường Thủ Đức.

Đây không phải bộ chuyển đổi hành chính tự động cho mọi địa chỉ. Nhãn trên ảnh nền OSM do nhà cung cấp cập nhật và có thể còn tên cũ; các nhãn địa chỉ ứng dụng quản lý trong mẫu này được đối chiếu riêng.

## Kiểm tra và tái tạo

```powershell
.\.venv\Scripts\python.exe -B scripts/create_report_sample.py
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B scripts/check_phase2_browser.py
.\.venv\Scripts\python.exe -B scripts/check_shared_locations_browser.py
# Cần backend 8001/frontend 5500/Edge demo CDP 9223, Internet và khóa backend:
.\.venv\Scripts\python.exe -B scripts/check_shared_locations_live.py
```

Kiểm thử nhãn mới đã có lượt RED trước thay đổi và GREEN sau thay đổi. Toàn bộ backend: **151 passed**. Browser import thật: đủ 30 dòng, 18 Nam/12 Nữ; các ca lỗi, XSS, mobile và phản hồi đến muộn đạt. Browser popup/state: giữ đủ người trùng tọa độ/tên, danh sách 100 người cuộn được, preview không đếm lặp và chặn sai giới tính đạt. Reviewer độc lập không tìm thấy lỗi cần sửa trong phạm vi thay đổi này.

Lượt kiểm tra live lưu JSON xác nhận và ảnh popup từng điểm tại `.local-tests/report-sample/` (Git ignore). Script upload qua giao diện, gọi Geoapify thật, chọn/xem/xác nhận từng người và click từng marker; không mock provider hoặc chèn tọa độ.

Kết quả live đã đạt: **30/30 vị trí xác nhận, 9 tọa độ khác nhau, 9 marker**, số người từng popup đúng 3/3/3/2/4/3/5/3/4. Mỗi popup đã kiểm tra đủ tên theo file, tên điểm và nhãn Thành phố Hồ Chí Minh; không còn Bình Dương trong địa chỉ đã xác nhận. Có ảnh `confirmed-30.png`, `point-1-popup.png` đến `point-9-popup.png`, `shared-map.png` và dữ liệu `confirmed.json`. Ảnh nền có lỗi tải mạng tạm thời ở hai lượt đầu; sau khi tải lại đã kiểm tra ảnh thật tải đủ và hoàn tất lượt live thành công, không thay ảnh bằng mock.

Đã xóa hai workbook cũ `danh_sach_sinh_vien_mau.xlsx`, `demo_cu_xa_nhieu_sinh_vien.xlsx` và hai script tạo chúng. Các liên kết và script đang dùng đã chuyển sang mẫu mới. Báo cáo cũ giữ lại số liệu lịch sử, không dùng chúng làm kết quả file mới.
