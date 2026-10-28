# Automatic location matching Implementation Plan

> Use superpowers:executing-plans; implement inline with RED/GREEN verification and a final independent review.

**Goal:** Sau nhập Excel hợp lệ, tự đối chiếu địa chỉ, tự xác nhận vị trí đại diện rõ ràng và hiển thị bản đồ; chỉ xử lý tay ngoại lệ.
**Architecture:** Giữ FastAPI/Geoapify/Leaflet và tọa độ provider thật. Backend đánh dấu candidate `auto_selectable` sau đối chiếu tên/địa danh; frontend chỉ tự nhận đúng một candidate hợp lệ với giới tính, không tự đoán cư xá theo giới. Import đọc cột tùy chọn địa điểm, giữ nguyên địa chỉ gốc, ghép địa chỉ tìm kiếm. Cache trong phiên theo địa chỉ, giữ ID từng sinh viên, bỏ response lỗi thời.
**Spec:** Yêu cầu trực tiếp người dùng 24/10/2026 thay cho quy tắc cũ bắt buộc xác nhận tay từng người. Đây là thay đổi luồng hiện có, không phải Phase 7. Tự động là đối chiếu điểm đại diện từ địa chỉ đã khai, không suy ra nơi ở từ họ tên hay bảo đảm mọi địa chỉ đều đúng.

## Decisions and alternatives

- Tự chọn candidate đầu tiên bị loại vì nhầm cư xá/tên trùng. Bắt xác nhận mọi người bị loại vì không đáp ứng danh sách100người. Chọn tự động có điều kiện và hàng đợi ngoại lệ theo yêu cầu.
- Dùng danh tính OSM đã đăng ký cho cư xá A–E/Cỏ May/KTX B; ghi rõ A–E trong địa chỉ hoặc cột phụ mới xác định được tòa. KTX Nông Lâm chung vẫn cần bổ sung, kể cả sau lọc giới chỉ còn một kết quả.
- Địa chỉ thường: confidence>=0.95, đủ chi tiết, trong bounds, tên và thành phần địa chỉ khớp kết quả; không auto nếu nhiều ứng viên khớp. Dorm chưa có danh tính đối chiếu không dựa confidence để auto.
- Hai đường có nguồn đăng ký riêng dùng bộ kiểm tra hiện hành tên đường/phường/VN-SG/loại/vùng hẹp và confidence tối thiểu cấu hình; không hạ ngưỡng cho địa chỉ thường. Quyết định này dựa trên kiểm tra thật confidence0.81 ở đúng đường/phường, với regression RED/GREEN riêng.
- Cột tùy chọn `Cư xá/Khu vực` hoặc cột mẫu cũ `Điểm cần xác nhận`; không bắt thêm cột. Không bỏ tên tòa xung đột. Cột công thức/lỗi/quá dài phải báo lỗi.
- Khởi chạy tự động sau import thành công; nhóm địa chỉ trùng chỉ gọi một lần, tiến độ và lọc `Cần xử lý`/`Tất cả`. Sửa/retry vẫn thủ công khi cần; lỗi một địa chỉ không chặn các địa chỉ khác, lỗi dịch vụ/quota/network/timeout thì tạm dừng để thử lại.
- Giữ workspace chứa Phase1–6 chưa commit, không commit/push. Không hỏi duyệt lại phần việc người dùng đã yêu cầu, theo chỉ dẫn autonomy cấp cao hơn.

## Tasks

- [x] Backend RED/GREEN: optional hint import; qualified known-place identity; auto flags exact/mismatch/ambiguous/low-confidence/unregistered dorm.
- [x] Browser RED/GREEN: actual100-row import starts automatically, duplicate cache, gender policy, ambiguous exceptions only, map ready points, filter, stale edit/import guard and grouping/export integration.
- [x] Regression pytest and relevant browsers, independent review, document changes/limits and restart local demo.

## Review focus

Wrong building from ambiguous campus; duplicated addresses across genders; a stale response confirming an edited row; automatic import causing duplicate jobs; provider outage/quota and prompt retry; optional hint changing original address or masking conflicting buildings.

## Completion evidence

213 pytest passed in9.76s. Browser100rows:98auto/2exceptions/2lookups, real Leaflet, edit/import stale guards, actual grouping/export, outage pause all PASS; Phase2/3/5/6/shared regression PASS. Independent review fixed provider outage pause and re-reviewed final street/map-fit adjustments: no Critical/Important. Live Geoapify:30/30automatic,9representative locations, actual6groups, workbook31/7rows, actual basemap loaded. See docs/reports/automatic-location.md and.local-tests/automatic-location/live-final.log. No commit/push; Phase7pending.
