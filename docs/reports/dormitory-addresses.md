# Hai ký túc xá — địa chỉ sau sáp nhập và kiểm tra bản đồ

Kiểm tra ngày 23/10/2026. Tên sinh viên trong các file đi kèm là giả lập; địa danh, tọa độ API và nguồn công bố là dữ liệu thật.

## Cách điền Excel thật

Giữ ba tiêu đề ở dòng 1 của sheet đầu: **Họ và tên**, **Giới tính**, **Nơi ở để học tập**. Cột mà người dùng gọi là “Địa chỉ” hiện được importer đọc theo tên **Nơi ở để học tập**; không chỉ đổi tiêu đề thành “Địa chỉ”. File `.xlsx`, mỗi sinh viên một dòng, giới tính `Nam` hoặc `Nữ`.

Ghi địa điểm đang ở để học tập, không phải quê quán. Mẫu chung: `Tên địa điểm/tên đường, khu phố (nếu biết), phường/xã mới, tỉnh/thành phố mới`. Với hai nơi cần báo cáo, dùng nguyên chuỗi dưới đây:

| Nơi ở | Nội dung ô Nơi ở để học tập |
|---|---|
| KTX trường Nông Lâm TP.HCM | Ký túc xá Trường Đại học Nông Lâm Thành phố Hồ Chí Minh, khu phố 33, phường Linh Xuân, Thành phố Hồ Chí Minh |
| KTX khu B ĐHQG-HCM | Ký túc xá khu B Đại học Quốc gia Thành phố Hồ Chí Minh, đường Mạc Đĩnh Chi, khu phố Tân Hòa, phường Đông Hòa, Thành phố Hồ Chí Minh |

Không cần số phòng. Không ghi chỉ `KTX`, `KTX B` hoặc `ĐHQG`; dễ nhầm trường/khu khác. Không dùng TP.Thủ Đức, TP.Dĩ An hoặc tỉnh Bình Dương trong hai chuỗi chuẩn hiện tại. Nhập nguyên tên dài là cách ít nhầm nhất; các alias ngắn được hỗ trợ ghi trong `known_places.py`.

## Nguồn địa chỉ và giới hạn diễn giải

1. [Thông tin tuyển sinh 2025 của Nông Lâm](https://ts.hcmuaf.edu.vn/data/file/Tuyen%20sinh%202025/20250718_%20Th%C3%B4ng%20tin%20tuy%E1%BB%83n%20sinh%202025.pdf), trang 1: cơ sở chính ở khu phố 33, phường Linh Xuân, TP.HCM.
2. [Trung tâm Dịch vụ sinh viên — thông tin KTX Nông Lâm](https://ttdvsv.hcmuaf.edu.vn/ktx-117509-3/vn/traloitructuyen.html): xác nhận KTX thuộc trường; trang cũ vẫn ghi địa chỉ hành chính cũ. Nhãn mới dùng địa chỉ cơ sở chính của trường, đối chiếu vị trí các cư xá trên bản đồ. Không diễn giải thành địa chỉ bưu chính riêng của từng phòng.
3. [Trang chính thức Trung tâm Quản lý KTX và Khu đô thị ĐHQG-HCM](https://www.ktxhcm.edu.vn/), mục Campus: khu B ở đường Mạc Đĩnh Chi, khu phố Tân Hòa, phường Đông Hòa, TP.HCM. Thông báo mời báo giá ngày 20/08/2025 trên cùng hệ thống cũng ghi cùng địa chỉ mới.
4. [Geoapify Places API](https://apidocs.geoapify.com/docs/places/) dùng dữ liệu OSM và có thể tra đối tượng theo category/vùng. Tên quận/thành phố cũ trong phản hồi nhà cung cấp không được coi là địa chỉ hành chính mới.

## Vì sao cần sửa luồng tra cứu

Forward geocoding thật với chuỗi đầy đủ trả thành phố hoặc đường Mạc Đĩnh Chi tại vùng khác, không có ứng viên đủ điều kiện. Không hạ ngưỡng để chấp nhận các kết quả sai này.

Luồng bổ sung nhận diện một danh sách alias giới hạn của đúng hai địa danh, dùng **Geoapify Places thật**. Chỉ giữ đối tượng có OSM ID, tên, loại, quốc gia và vùng nhỏ đã đối chiếu; tọa độ được lấy từ phản hồi mới, không nhúng tọa độ vào danh mục và không nhập tọa độ vào Excel.

| Địa điểm/đối tượng OSM | Tọa độ lấy từ API khi kiểm tra |
|---|---|
| [Nông Lâm — Cư xá A, way 291412044](https://www.openstreetmap.org/way/291412044) | 10.871312, 106.7911041 |
| [KTX khu B ĐHQG-HCM, node 11562800202](https://www.openstreetmap.org/node/11562800202) | 10.8821432, 106.7825645 |

Nông Lâm còn có Cư xá B/C/D/E trong danh sách lựa chọn; KTX Cỏ May là nơi khác, không tự gộp. Nếu dữ liệu thật biết tòa, chọn đúng tòa khi xác nhận. Khi chỉ ghi khu KTX, điểm Cư xá A trong demo là **điểm đại diện của khu**, không phải khẳng định phòng của mọi sinh viên nằm ở A. Khu B cũng là điểm đại diện địa danh, không phải tọa độ riêng từng phòng.

Places không có confidence kiểu forward geocoding: API trả `confidence=null` và `source=geoapify_places`, giao diện ghi nguồn Places/OSM. Địa chỉ hiển thị chuẩn lấy theo các nguồn chính thức trên; liên kết nguồn tọa độ và nguồn địa chỉ có trong candidate. Vẫn phải chọn ứng viên, xem bản đồ và xác nhận riêng từng người; không tự verified.

Nhãn trong dropdown/popup của ứng dụng dùng địa chỉ mới. Chữ in sẵn trên ảnh nền raster OSM phụ thuộc nhà cung cấp tiles; có thể còn địa danh cũ. Không tuyên bố rằng toàn bộ bản đồ nền đã được cập nhật địa giới hành chính.

## File và cách chạy

- [File mẫu hiện tại](../../data/samples/danh_sach_sinh_vien_bao_cao.xlsx): 30 sinh viên giả lập, 18 Nam/12 Nữ, đủ A–E/Cỏ May/khu B và hai đường ngoài KTX. Địa chỉ trong mẫu đều dùng tên phường/thành phố mới. Thay thế các workbook cũ.
- Tái tạo: `python scripts/create_report_sample.py` trong venv dự án. [Kết quả kiểm tra mẫu mới](report-sample.md).
- Kiểm tra trình duyệt thật: backend 8001, frontend 5500, cửa sổ Edge demo CDP 9223; chạy `python scripts/check_shared_locations_live.py`. Script không mock provider hoặc sửa tọa độ.

## Kiểm chứng

21 test mới đã được chạy RED trước thay đổi rồi GREEN; toàn bộ suite 137 passed. Review độc lập không tìm thấy lỗi trong nhận diện địa danh, giới hạn alias, nguồn tọa độ, nhãn hành chính, sanitization/cooldown và xác nhận thủ công.

Script kiểm tra hai KTX cũ đã chạy đạt trên Edge với backend/Geoapify Places/OSM thật, không mock hoặc chèn tọa độ: import mẫu 30 vẫn đúng 18 Nam/12 Nữ; chuyển sang mẫu hai KTX; Nông Lâm có 5 cư xá đúng ID, khu B có 1 POI đúng ID; chưa chọn thì 0/2 xác nhận; chọn/preview/xác nhận từng người thì 2/2, đủ 2 marker ở 2 tọa độ khác nhau. Popup của cả hai đều có phường mới/TP.HCM, không có TP.Thủ Đức/TP.Dĩ An. Trình duyệt không gọi trực tiếp provider hoặc chứa API key. Script đó nay được thay bởi kiểm tra nhiều sinh viên cùng địa điểm; đây là ghi nhận lịch sử kiểm thử.

Lần kiểm tra ban đầu có ba ảnh popup/bản đồ ở `.local-tests/dormitories/`; thư mục tạm này đã được dọn. Ảnh demo hiện tại nằm tại `.local-tests/shared-locations/live/` và có thể tái tạo bằng script đang dùng. Không suy diễn độ chính xác cho mọi địa chỉ từ hai địa danh đã đối chiếu.
