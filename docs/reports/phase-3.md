# Phase 3 — Geocoding và xác minh vị trí

Kế hoạch: [Phase 3](../superpowers/plans/2026-10-21-webgis-development-phases.md). Thực hiện theo executing-plans và test-driven-development, giữ workspace hiện tại cùng thay đổi Phase 1–2 chưa commit.

## Thiết kế triển khai

- Hai API JSON: `/api/geocode/batch` nhận `students: [{student_id, address}]` tối đa 5 dòng; `/api/geocode/retry` nhận một dòng. Không gửi tên hoặc giới tính tới nhà cung cấp.
- Trả ứng viên được lọc theo tọa độ hữu hạn, quốc gia VN, vùng nghiên cứu và độ chi tiết. Không tự chọn/không tự chuyển `verified`; tất cả kết quả thành công ở trạng thái `needs_review`.
- Vùng lọc sơ bộ là hình chữ nhật lon 106.4–107.0, lat 10.5–11.2 quanh vùng nghiên cứu, không phải ranh giới hành chính. Confidence tối thiểu sơ bộ 0.7, chấp nhận street/amenity/suburb/quarter/neighbourhood; loại city/state/country/house. Các ngưỡng có cấu hình và phải đối chiếu API thật, không coi confidence là độ chính xác đã đo.
- Request upstream timeout 8 giây, tối đa một job đang xử lý trong mỗi tiến trình và cách nhau ít nhất 1 giây giữa các lần gọi. Không tự retry khi hết quota; lỗi có thông báo cố định, không trả URL/key/body lỗi từ Geoapify.
- Deduplicate địa chỉ trong một batch. Cache ứng viên ở bộ nhớ phiên frontend, xóa khi upload mới/refresh; không cache xác nhận của giảng viên. Sửa địa chỉ xóa ứng viên/tọa độ/xác nhận/kết quả phân nhóm trước khi retry.
- Giao diện có bảng sửa địa chỉ, chọn ứng viên, xem trên bản đồ và xác nhận từng người. Mỗi request gắn phiên import và revision dòng để bỏ response lỗi thời.
- Nút chia nhóm vẫn chưa thực thi thuật toán (Phase 4); bộ kiểm tra readiness chỉ đạt khi mọi dòng đã verified. Không tạo API chia nhóm giả.
- Test mock là dữ liệu tổng hợp; kiểm thử thật dùng địa chỉ công cộng/giả lập, báo cáo riêng tại `geocoding-validation.md`.

## Tiến độ

- [x] Backend + kiểm thử mock và API.
- [x] Sửa/retry, chọn ứng viên, xác nhận và bản đồ.
- [x] Kiểm thử trình duyệt, response đến muộn và hồi quy.
- [x] Kiểm thử Geoapify thật và đối chiếu khu vực.
- [x] Review, tài liệu và trạng thái nghiệm thu.

## Bằng chứng kiểm tra

Ngày 22/10/2026, Python 3.13, Microsoft Edge headless:

| Lệnh | Kết quả |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q` | 59 passed; gồm hồi quy Phase 1–2 và 23 test Phase 3 |
| `scripts/check_phase2_browser.py` | Nhập 30 người, lỗi từng dòng, HTML an toàn, mobile, lỗi upload và response cũ đạt |
| `scripts/check_phase3_browser.py` | Mock Geoapify: chọn/xác nhận riêng từng người, readiness, xóa tọa độ khi sửa, response cũ, file mới, mobile đạt |
| `scripts/validate_geocoding.py` | API thật: 4 phản hồi hợp lệ; 2 địa chỉ có ứng viên đủ bộ lọc, không suy diễn accuracy |
| `scripts/check_phase3_live_browser.py` | Geoapify và OSM thật: preview, sửa/retry, vẫn chưa tự xác nhận; không có request chứa key tới provider trên trình duyệt |

Test Phase 3 đã được chạy đỏ trước triển khai và xanh sau triển khai. Review độc lập phát hiện ô địa chỉ bị thay DOM mỗi lần gõ; đã bổ sung test tái hiện đỏ, sửa giữ nguyên input, kiểm tra xanh với native undo và sự kiện composition tổng hợp. Chưa kiểm thử thủ công mọi bộ gõ hệ điều hành. Bổ sung backend test chặn job đồng thời và cooldown sau 429.

Kết quả geocoding thật, các địa chỉ chưa đạt và quyết định ngưỡng: [geocoding-validation.md](geocoding-validation.md). Ảnh và JSON thử nghiệm lưu trong `.local-tests/phase-3/`, bị Git bỏ qua. Bảng nhập Excel hiển thị trạng thái kiểm tra dữ liệu gốc; bước 02 là nơi theo dõi xác nhận vị trí hiện tại.

## Nghiệm thu và giới hạn

Phase 3 hoàn thành phạm vi chức năng: AC-03, AC-04 đạt; phần giao diện/readiness của AC-05 đạt. AC-05 chưa đánh dấu hoàn tất toàn bộ vì API grouping thuộc Phase 4. Không tự xác nhận ứng viên chỉ vì confidence cao; chưa xác nhận 30 vị trí mẫu hoặc đo độ chính xác đại diện.

Khóa người dùng được đặt trong `backend/.env` (Git ignore); `.env.example` giữ trống. Chưa commit/push các thay đổi của Phase 1–3. Chạy một backend worker local; phân tán rate-limit, thuật toán chia nhóm, xuất Excel và triển khai máy chủ thuộc các phase tiếp theo.

## Demo bổ sung theo yêu cầu người dùng — 23/10/2026

Đã tạo và upload mẫu 12 sinh viên, dùng Geoapify/OSM thật, chọn và xác nhận 12/12 dòng; kiểm tra 12 marker xuất hiện trong khung bản đồ. [Báo cáo demo và giới hạn](phase-3-demo-12.md). Đây là mẫu địa chỉ đã chuẩn bị, không thay thế đánh giá chất lượng trên tập địa chỉ bất kỳ.
