# Thiết kế UI/UX theo 4 bước

Trạng thái: người dùng đã duyệt và yêu cầu triển khai.

## Mục tiêu và phạm vi

Phục vụ demo trực tiếp toàn bộ quy trình WebGIS trên nhánh `codex/ui-ux-improvements`. Cải thiện bố cục, điều hướng, nhập Excel và trình bày kết quả trên nền HTML/CSS/JavaScript hiện tại. Tận dụng API và trạng thái phiên hiện có; thuật toán chia nhóm nằm ngoài phạm vi.

## Các hướng đã cân nhắc

- Giao diện 4 bước: ít thông tin đồng thời, thuận tiện thuyết trình; cần quản lý điều kiện chuyển bước. Người dùng đã chọn hướng này.
- Dashboard đồng thời: thuận tiện đối chiếu bản đồ và thao tác nhưng dày thông tin khi trình chiếu.

## Luồng giao diện

Thanh đầu trang gọn với tên ứng dụng và trạng thái kết nối. Thanh tiến trình luôn thể hiện bước hiện tại, bước hoàn thành và bước chưa sẵn sàng. Mỗi bước có tiêu đề, hướng dẫn ngắn, hành động chính và nút quay lại/tiếp tục.

1. **Nhập dữ liệu:** tải mẫu Excel, điền dữ liệu, chọn file và đọc danh sách. Hiện tên file, thống kê và bảng xem trước; lỗi chỉ rõ dòng/cột. Chỉ cho tiếp tục khi dữ liệu hợp lệ.
2. **Vị trí:** hiển thị bản đồ cùng tiến độ đối chiếu tự động và danh sách địa chỉ cần xử lý. Cho sửa/kiểm tra theo khả năng hiện có. Chỉ cho chia nhóm khi toàn bộ vị trí đủ điều kiện hiện hành.
3. **Chia nhóm:** nhập mục tiêu Nam/Nữ, xem số nhóm dự kiến rồi bấm Chia nhóm. Hiển thị trạng thái đang xử lý; thành công chuyển đến kết quả.
4. **Kết quả:** bản đồ, tổng sinh viên/số nhóm/khoảng cách, bộ lọc nhóm, bảng thành viên và nút xuất Excel. Giải thích khoảng cách đường chim bay và vị trí đại diện ở phần trợ giúp ngắn.

Điều hướng trở lại giữ dữ liệu trong phiên. Khi nhập dữ liệu mới hoặc thay đổi vị trí/tham số, kết quả cũ được vô hiệu hóa theo cơ chế hiện hành; không hiển thị bước hoàn thành hoặc cho xuất kết quả hết hiệu lực. Lỗi API giữ nguyên dữ liệu để thử lại. Tải lại trang bắt đầu phiên mới như hiện tại.

## Excel mẫu

File `.xlsx` tải trực tiếp tại bước 1. Sheet đầu tiên có đúng 4 tiêu đề ở dòng 1: `Họ và tên`, `Giới tính`, `Nơi ở để học tập`, `Cư xá/Khu vực`. Các dòng nhập liệu trống; sheet thứ hai chứa hướng dẫn và ví dụ để tránh nhập nhầm sinh viên mẫu.

Giới tính có danh sách chọn Nam/Nữ. Ba cột đầu bắt buộc có nội dung; Cư xá/Khu vực cho phép trống với nhà riêng (đề xuất của người triển khai). Mẫu có đủ 4 cột; giữ tương thích bộ đọc hiện có với file hợp lệ 3 cột, không bắt người dùng bắt buộc tải mẫu. Backend vẫn kiểm tra tiêu đề, dữ liệu, kích thước và số dòng; không coi danh sách chọn Excel là kiểm tra bảo đảm.

## Trình bày và khả năng sử dụng

Đề xuất dùng nền sáng, xanh lá đậm chủ đạo, chữ tương phản cao, cỡ chữ và khoảng cách dễ đọc trên máy chiếu. Thu gọn hình giới thiệu. Màn hình hẹp xếp dọc; bảng có cuộn ngang. Điều hướng dùng bàn phím, focus rõ, thông báo trạng thái hỗ trợ trình đọc màn hình. Bản đồ cập nhật kích thước khi bước được hiển thị để tránh vùng trống.

## Xác nhận triển khai

Kiểm tra file mẫu điền dữ liệu có thể nhập bằng parser thật; mẫu trống, thiếu cột và dữ liệu sai có thông báo phù hợp. Kiểm tra trình duyệt đủ chuỗi nhập → vị trí → chia nhóm → lọc → xuất, quay lại các bước và vô hiệu hóa kết quả cũ; kiểm tra desktop và màn hình hẹp. Chạy các kiểm thử hiện có liên quan để phát hiện hồi quy.
