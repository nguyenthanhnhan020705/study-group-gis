# Kiểm thử Geoapify thật — 22/10/2026

## Phương pháp

Chạy `scripts/validate_geocoding.py` với khóa ở `backend/.env`, gọi Geoapify thật qua service backend. Chỉ dùng địa chỉ đường/địa điểm công cộng; không gửi danh tính sinh viên. Kết quả đã lọc, không chứa khóa, nằm tại `.local-tests/phase-3/live-geocoding.json` (bị Git bỏ qua). Mock test được báo cáo riêng trong [Phase 3](phase-3.md).

Theo [tài liệu forward geocoding](https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/), request dùng `filter=countrycode:vn`, `format=json`, `limit=5`. Confidence là chỉ báo từ nhà cung cấp, không phải tỷ lệ chính xác đã kiểm chứng.

## Kết quả thực tế

| Địa chỉ gửi | Số ứng viên / đủ bộ lọc | Đối chiếu kết quả |
|---|---:|---|
| Đường Hoàng Diệu 2, TP. Thủ Đức, TP. Hồ Chí Minh | 4 / 1 | Ứng viên Hẻm 14 Đường Hoàng Diệu 2, 10.8600827 / 106.7611872, street, confidence 0.729. Các ứng viên Khánh Hội confidence 0 bị loại. |
| Đường Hoàng Diệu 2, Thành phố Hồ Chí Minh | 1 / 1 | Cùng khu vực, 10.860083 / 106.761187, street, confidence 0.81. Vẫn khớp hẻm 14, không đủ cơ sở tự xác nhận toàn tuyến đường. |
| Ký túc xá khu A, Đại học Quốc gia TP. Hồ Chí Minh | 5 / 0 | Có kết quả VinUni Hà Nội ngoài vùng; các ký túc xá khác confidence thấp. Cần bổ sung/sửa địa chỉ, chưa xác nhận. |
| Đường Nguyễn An Ninh, Dĩ An, Bình Dương | 3 / 0 | Có quán cà phê ngoài vùng và kết quả cấp city, không đạt. Cách ghi hành chính cũ này cần chỉnh và kiểm tra lại. |

Cả 4 request nhận phản hồi hợp lệ; 2/4 có ứng viên đủ bộ lọc. **Đây không phải tỷ lệ chính xác 50%**: chưa có ground truth hoặc xác nhận của người dùng. Không suy diễn rằng 30 địa chỉ trong file mẫu đều geocode đạt.

## Bản đồ và sửa/retry thật

`scripts/check_phase3_live_browser.py` đã chạy trên Edge với backend 8001/frontend 5500, không mock Geoapify hoặc bản đồ. Luồng import một bản ghi công cộng → tìm vị trí → chọn ứng viên → xem điểm trên Leaflet/OSM → sửa sang biến thể địa chỉ Thủ Đức → retry đã đạt. Điểm nằm trong vùng Thủ Đức theo tọa độ/địa danh trả về; việc khớp đúng nơi học tập cụ thể vẫn cần người dùng đối chiếu. Script giữ 0/1 xác nhận, không tự chứng nhận độ chính xác. Ảnh: `.local-tests/phase-3/live-preview.png`.

Trình duyệt không gọi trực tiếp Geoapify và không gửi tham số API key. Ban đầu sandbox chặn mạng; kiểm thử thật đạt sau khi backend và trình duyệt được chạy với quyền mạng được cấp.

## Ngưỡng và giới hạn

- Bounds sơ bộ: west 106.4, south 10.5, east 107.0, north 11.2; đây là hộp lọc quanh vùng nghiên cứu, không phải ranh giới hành chính.
- Confidence tối thiểu 0.7. Chấp nhận street/amenity/suburb/quarter/neighbourhood; loại house/city/state/country. Ngưỡng còn bảo thủ, chưa được hiệu chỉnh bằng tập địa chỉ gán nhãn.
- Luôn yêu cầu người dùng chọn ứng viên và xác nhận riêng từng sinh viên; không hạ ngưỡng tự động để ép kết quả thành công.
- Giới hạn một job mỗi tiến trình, khoảng cách request mặc định 1 giây và nghỉ 30 giây sau HTTP 429. Chạy một Uvicorn worker trong giai đoạn local; nhiều worker cần bộ giới hạn dùng chung trước deploy.
- API, quota, dữ liệu địa danh và tiles phụ thuộc dịch vụ bên ngoài; kết quả có thể thay đổi giữa các lần chạy.

## Bổ sung hai KTX sau sáp nhập — 23/10/2026

Các phép thử 4 địa chỉ ở trên là bằng chứng trước khi bổ sung tra cứu Places cho hai địa danh cụ thể. KTX Nông Lâm và KTX khu B ĐHQG-HCM được đối chiếu riêng bằng Geoapify Places/OSM và nhãn địa chỉ mới từ nguồn đơn vị quản lý. Không hạ ngưỡng forward geocoding. [Báo cáo, file mẫu và hướng dẫn nhập địa chỉ thật](dormitory-addresses.md).
