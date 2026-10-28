# Phase 2 — Nhập Excel và kiểm tra dữ liệu

Kế hoạch: [Phase 2](../superpowers/plans/2026-10-21-webgis-development-phases.md), BR-01 / AC-01, AC-02.

## Quyết định triển khai

- Giữ workspace/nhánh hiện tại cùng thay đổi Phase 1 chưa commit; chỉ triển khai Phase 2.
- Dùng openpyxl đọc trực tiếp để giữ chính xác dòng Excel và phát hiện công thức; chưa cần pandas.
- Sheet đầu tiên, tiêu đề dòng 1. Tên cột phân biệt dấu/chữ hoa; cho phép khoảng trắng ở hai đầu tiêu đề. Cột thừa bị bỏ qua; cột bắt buộc trùng lặp bị từ chối.
- File tối đa 5 MiB, tối đa 1.000 dòng dữ liệu sau tiêu đề; cấu hình `MAX_UPLOAD_BYTES`, `MAX_STUDENT_ROWS`. Giới hạn bổ sung: 256 cột, 20 MiB nội dung ZIP giải nén, 2.000 ZIP entries, 2.000 ký tự mỗi trường bắt buộc. Các giới hạn này bảo vệ việc đọc workbook không đáng tin cậy.
- Dòng rỗng xen giữa giữ nguyên số dòng và được báo lỗi; dòng rỗng cuối sheet được bỏ qua trong phạm vi giới hạn quét. Không loại người trùng tên/địa chỉ.
- `student_id` dựa trên số dòng trong lần import, ổn định khi đọc lại cùng file. Upload mới thay thế toàn bộ danh sách và trạng thái cũ; ID không dùng để nối các lần import.
- Import có lỗi dòng trả HTTP 200 với `can_proceed=false`, toàn bộ bản ghi và lỗi. Lỗi file/schema trả 400/413/422 với danh sách lỗi rõ ràng; không trả stack trace.
- Bản ghi giữ trường giới tính dạng chuỗi để hiển thị giá trị sai; chỉ Nam/Nữ hợp lệ mới được đếm vào thống kê tương ứng. Đếm thêm số dòng lỗi, không coi số Nam+Nữ là số dòng hợp lệ.
- Đầu vào sai kiểu hoặc chứa công thức trong ba cột bắt buộc được báo lỗi, không tính toán công thức hoặc tự sửa giới tính.
- Frontend render bằng textContent, giới hạn timeout upload 30 giây, hủy/loại response cũ khi chọn file khác. Mọi tọa độ ban đầu null, trạng thái pending.
- Không lưu workbook trên server lâu dài; chưa gọi geocoding. Dữ liệu chỉ ở bộ nhớ phiên trình duyệt, refresh xóa danh sách.

## Checklist

- [x] Test parser/API RED → GREEN, kiểm tra hồi quy Phase 1.
- [x] Upload, thống kê Nam/Nữ, bảng lỗi và danh sách trên giao diện.
- [x] Tạo file giả lập 30 người, 18 Nam/12 Nữ, kèm script tái tạo.
- [x] Kiểm tra trình duyệt, review độc lập và cập nhật tài liệu.

## Tài liệu kỹ thuật

- [openpyxl read-only mode](https://openpyxl.readthedocs.io/en/stable/optimized.html)
- [FastAPI upload files](https://fastapi.tiangolo.com/tutorial/request-files/)

## Bằng chứng kiểm tra (2026-10-21)

- Baseline Phase 1 trước khi sửa: 11 test đạt.
- RED Phase 2: 24 test parser/API thất bại vì chưa có module/endpoint/cấu hình, hoặc POST chưa được CORS cho phép.
- GREEN và hồi quy cuối: `.\.venv\Scripts\python.exe -m pytest -q --tb=short` → **36 passed**, gồm 11 test Phase 1 và 25 test Phase 2.
- `.\.venv\Scripts\python.exe -m pip check` → `No broken requirements found`.
- `git diff --check` đạt.
- Kiểm tra trình duyệt trước giao diện: không tìm thấy `#student-file` như dự kiến.
- `.\.venv\Scripts\python.exe scripts/check_phase2_browser.py` → **5 nhóm PASS**: upload multipart thật và đủ 30/18/12; lỗi theo dòng và render HTML như văn bản; không tràn ngang ở 390px; lỗi mạng xóa kết quả cũ; response cũ không ghi đè file mới.
- Đã xem ảnh mobile trong `.local-tests/phase-2/mobile-errors.png`; bảng cuộn trong vùng riêng. Ảnh desktop ở cùng thư mục. Script tự chạy/dừng backend 8012 và frontend 5512, chặn CDN bản đồ có chủ đích; không coi đây là kiểm thử bản đồ thật.

## Rà soát độc lập

Reviewer xác nhận một lỗi P2: ô lỗi Excel (`cell.data_type == 'e'`) được openpyxl trả như chuỗi và từng được chấp nhận như tên/địa chỉ hợp lệ. Đã thêm regression `test_excel_error_cells_are_retained_but_cannot_proceed`, quan sát thất bại, rồi sửa để báo lỗi theo dòng/trường và giữ bản ghi. Toàn bộ 36 test đạt sau sửa.

Không có phát hiện quan trọng khác về giới hạn upload/ZIP, giữ dòng, trạng thái phiên hoặc hiển thị HTML. Không có minor bị hoãn.

## Kết quả bàn giao

- AC-01, AC-02 đạt; Phase 2 hoàn thành. Chưa triển khai Phase 3 hoặc xác nhận chất lượng geocoding.
- File mẫu lịch sử `danh_sach_sinh_vien_mau.xlsx` có 30 tên giả lập, 18 Nam/12 Nữ. File này đã được thay thế và xóa; dùng [mẫu báo cáo hiện tại](../../data/samples/danh_sach_sinh_vien_bao_cao.xlsx), cùng số lượng, địa chỉ mới và đầy đủ kịch bản cư xá. Không sử dụng danh tính thật.
- Backend có thêm `POST /api/students/import`; tất cả bản ghi đầu vào đều chưa xác minh vị trí.
- Khởi động lại backend phát triển sau khi cập nhật dependency; cổng vẫn 8001, frontend 5500.
- Giữ cùng nhánh với Phase 1 để bảo toàn toàn bộ thay đổi chưa commit; chưa commit/merge/push.
