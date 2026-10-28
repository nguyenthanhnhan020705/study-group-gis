# BRD — WebGIS hỗ trợ giảng viên chia nhóm học tập theo vị trí địa lý của sinh viên

> **Business Requirements Document (BRD) — Tài liệu yêu cầu nghiệp vụ**
> Mục đích: làm cơ sở thống nhất phạm vi, phát triển và nghiệm thu WebGIS v1.0 cho đồ án môn học.
> BRD mô tả phạm vi v1.0. Đã triển khai Phase 1–7: nhập Excel, tự đối chiếu vị trí, chia nhóm, WebGIS kết quả, xuất Excel, kiểm thử tích hợp và đánh giá baseline. Nền bản đồ có nguồn Geoapify dự phòng. Xem [báo cáo nghiệm thu và giới hạn](docs/reports/acceptance.md); giao diện trình bày có thể chỉnh tiếp.

## Thông tin và kiểm soát tài liệu

| Thuộc tính | Nội dung |
|---|---|
| Mã tài liệu | BRD-WEBGIS-001 |
| Phiên bản tài liệu | 1.0 — tổ chức lại từ đặc tả hiện có |
| Phiên bản sản phẩm | WebGIS v1.0 (MVP) |
| Ngôn ngữ sản phẩm | Tiếng Việt |
| Thời gian mục tiêu | 4 tuần |
| Trạng thái tài liệu | Bản dự thảo BRD để rà soát; các quyết định đã chốt được giữ nguyên từ đặc tả nguồn |
| Người biên soạn / chủ sở hữu | Chưa xác định trong hồ sơ |
| Người phê duyệt / ngày phê duyệt | Chưa xác định / chưa ghi nhận |

| Phiên bản | Nội dung thay đổi |
|---|---|
| 1.0 | Chuẩn hóa bố cục BRD, bổ sung mã truy vết yêu cầu và đưa đặc tả kỹ thuật vào phụ lục; giữ nguyên phạm vi và quy tắc đã chốt. |

### Mục lục

- [1. Bối cảnh, mục tiêu và phạm vi](#brd-01)
- [2. Các bên liên quan](#brd-02)
- [3. Quy trình nghiệp vụ mục tiêu](#brd-03)
- [4. Danh mục yêu cầu nghiệp vụ](#brd-04)
- [5. Yêu cầu dữ liệu đầu vào](#brd-05)
- [6. Yêu cầu xác minh vị trí](#brd-06)
- [7. Quy tắc nghiệp vụ chia nhóm](#brd-07)
- [8. Yêu cầu giao diện và tương tác](#brd-08)
- [9. Yêu cầu đầu ra](#brd-09)
- [10. Yêu cầu phi chức năng và bảo vệ dữ liệu](#brd-10)
- [11. Giả định, phụ thuộc và rủi ro](#brd-11)
- [12. Tiêu chí nghiệm thu và truy vết](#brd-12)
- [13. Kế hoạch và trạng thái dự án](#brd-13)
- [14. Giới hạn và hướng phát triển](#brd-14)
- [Phụ lục A–F: đặc tả và hướng dẫn kỹ thuật](#appendices)

<a id="brd-01"></a>

## 1. Bối cảnh, mục tiêu và phạm vi

### 1.1. Bài toán

Giảng viên cần chia sinh viên thành các nhóm học tập sao cho:

1. Các thành viên trong cùng nhóm ở **tương đối gần nhau về nơi ở để học tập**.
2. Tỷ lệ **nam/nữ** gần với mong muốn của giảng viên.
3. **100% sinh viên hợp lệ** được xếp vào **đúng một nhóm**, kể cả khi số lượng nam/nữ không chia hết.
4. Quá trình xử lý và kết quả được giải thích, kiểm tra, quan sát trên bản đồ WebGIS.

Đầu vào là danh sách Excel gồm họ tên, giới tính và **nơi ở hiện tại phục vụ việc học** (không phải hộ khẩu). Địa chỉ chỉ cần đạt độ chi tiết cấp đường hoặc địa điểm công cộng như ký túc xá; **không yêu cầu số nhà hoặc tọa độ nhà riêng**.

### 1.2. Mục tiêu sản phẩm

- Một trang WebGIS duy nhất dành cho **giảng viên**.
- Upload, kiểm tra và chỉnh sửa dữ liệu sinh viên trên giao diện.
- Tìm tọa độ đại diện bằng Geoapify, kiểm tra kết quả và hiển thị Leaflet.
- Tự xác định số nhóm, chia nhóm dựa trên **K-Means theo từng giới tính**, cân bằng quy mô và ghép cụm ở gần nhau.
- Hiển thị bản đồ, danh sách, số lượng nam/nữ và các chỉ số khoảng cách.
- Xuất kết quả ra **Excel (.xlsx)** để sử dụng ngoài hệ thống.
- Có quy trình kiểm thử và chỉ số đánh giá đủ để làm báo cáo môn học.

### 1.3. Phạm vi v1.0

**Bắt buộc:**

- Upload Excel, xác thực cột và dữ liệu.
- Geocoding Geoapify từ backend, sửa địa chỉ lỗi trực tiếp trên web, kiểm tra lại tọa độ.
- Chặn chia nhóm cho đến khi toàn bộ sinh viên có vị trí đã xác nhận hợp lệ.
- Tự tính `k` theo quy mô nhóm, chia đủ mọi sinh viên.
- Bản đồ Leaflet, bảng kết quả và thống kê nhóm.
- Xuất Excel, không lộ API key, kiểm thử bộ dữ liệu mẫu.

**Ngoài phạm vi v1.0:** đăng nhập, giao diện sinh viên, lưu lịch sử phân nhóm trên máy chủ, Supabase/PostGIS bắt buộc, GeoServer, tối ưu theo mạng lưới giao thông, phân nhóm dựa trên thời gian di chuyển, thuật toán Greedy Nearest-Neighbor làm thuật toán chính. Những phần này chỉ được nêu ở mục hướng phát triển, **không tự triển khai**.

<a id="brd-02"></a>

## 2. Các bên liên quan

| Bên liên quan | Vai trò / nhu cầu |
|---|---|
| Giảng viên sử dụng WebGIS | Nhập danh sách, xác minh vị trí, thiết lập Nam/Nữ, xem và xuất kết quả nhóm. Đây là vai trò sử dụng duy nhất trong v1.0. |
| Sinh viên trong danh sách | Đối tượng được phân nhóm; cung cấp nơi ở để học tập ở mức đại diện, không có giao diện riêng trong v1.0. |
| Nhóm thực hiện đồ án | Phát triển, kiểm thử, đo chỉ số và chuẩn bị báo cáo theo yêu cầu đã chốt. |
| Bên đánh giá / nghiệm thu đồ án | Đối chiếu sản phẩm với tiêu chí nghiệm thu; cá nhân phụ trách chưa được xác định trong hồ sơ. |

<a id="brd-03"></a>

## 3. Quy trình nghiệp vụ mục tiêu

Chỉ có một vai trò: **Giảng viên**. Phiên bản đầu chưa có tài khoản và phân quyền.

1. Giảng viên mở WebGIS và tải lên file `.xlsx`.
2. Hệ thống kiểm tra tên cột, dữ liệu trống, giá trị giới tính, định dạng và số dòng.
3. Backend chuyển các địa chỉ văn bản thành tọa độ đại diện bằng Geoapify.
4. Giao diện trình bày tọa độ, địa chỉ đã khớp, mức tin cậy và trạng thái của từng dòng.
5. Với địa chỉ không tìm được, mơ hồ hoặc quá thô, giảng viên **sửa ngay trên web** và nhấn **Kiểm tra lại**. Không bắt buộc tải Excel lại.
6. Giảng viên xác nhận vị trí hợp lệ ở độ chi tiết được phép (đường/khu vực/địa điểm công cộng).
7. Chỉ khi tất cả dòng hợp lệ, giảng viên nhập số nam và số nữ mong muốn trong một nhóm, rồi nhấn **Chia nhóm**.
8. Hệ thống tự tính số nhóm, chạy thuật toán, kiểm tra kết quả, hiển thị bản đồ và bảng tổng hợp.
9. Giảng viên nhấn **Xuất Excel** để lưu danh sách các nhóm về máy.

Không lưu lịch sử vào cơ sở dữ liệu. Khi làm mới trang hoặc bắt đầu phiên mới, người dùng có thể phải upload lại dữ liệu. Không xem kết quả geocoding chưa kiểm chứng là vị trí chính xác.

<a id="brd-04"></a>

## 4. Danh mục yêu cầu nghiệp vụ

Các yêu cầu dưới đây là bắt buộc trong v1.0. Mã BR dùng để đối chiếu yêu cầu chi tiết và tiêu chí nghiệm thu; không biểu thị chức năng đã hoàn thành.

| Mã | Yêu cầu | Tham chiếu chi tiết | Nghiệm thu |
|---|---|---|---|
| BR-01 | Nhập Excel theo tên cột, kiểm tra dữ liệu và báo lỗi theo dòng, không làm mất sinh viên. | Mục 5 | AC-01, AC-02 |
| BR-02 | Chuyển địa chỉ thành vị trí đại diện qua backend, hỗ trợ sửa và xác minh trên web. | Mục 6 | AC-03, AC-04 |
| BR-03 | Chỉ cho phép chia nhóm khi mọi vị trí đã được xác nhận hợp lệ. | Mục 6–7 | AC-05 |
| BR-04 | Tự tính số nhóm từ tổng sinh viên và quy mô mong muốn theo công thức đã chốt. | Mục 7 | AC-06 |
| BR-05 | Chia nhóm theo vị trí và mục tiêu Nam/Nữ; xử lý số dư và thiếu một giới, gán mỗi người đúng một nhóm. | Mục 7, Phụ lục A | AC-07, AC-08, AC-09 |
| BR-06 | Hiển thị bản đồ, thành viên, bộ lọc và thống kê nhất quán; vô hiệu hóa kết quả khi đầu vào thay đổi. | Mục 8 | AC-10, AC-14 |
| BR-07 | Xuất Excel khớp kết quả hiện hành, đủ thành viên và thống kê nhóm. | Mục 9 | AC-11 |
| BR-08 | Có kiểm thử tính đúng đắn và đánh giá khoảng cách với baseline từ kết quả thực nghiệm. | Mục 7, Phụ lục E | AC-12 |
| BR-09 | Bảo vệ khóa API, dùng dữ liệu giả lập khi demo công khai và không lưu lịch sử trên server. | Mục 10 | AC-03, AC-13 |

<a id="brd-05"></a>

## 5. Yêu cầu dữ liệu đầu vào

### 5.1. Schema Excel bắt buộc

Đọc cột **theo tên**, không phụ thuộc thứ tự cột trong file.

| Tên cột chính xác | Kiểu | Quy tắc |
|---|---|---|
| `Họ và tên` | Chuỗi | Không được rỗng; chuẩn hóa khoảng trắng. |
| `Giới tính` | Chuỗi | Chỉ nhận `Nam` hoặc `Nữ` sau khi trim; giá trị không hợp lệ phải báo rõ dòng. |
| `Nơi ở để học tập` | Chuỗi | Không rỗng; mô tả nơi ở hiện tại để đến trường, không yêu cầu số nhà. |

- Chấp nhận `.xlsx` cho v1.0, đọc bằng pandas/openpyxl.
- Bỏ qua các cột thừa như `Dấu thời gian` từ Google Form, nhưng không được nhầm cột.
- Không loại bỏ hai sinh viên chỉ vì **trùng tên hoặc trùng địa chỉ**. Gán một `student_id` nội bộ ổn định cho từng dòng; hai người có thể ở cùng khu vực.
- Không âm thầm sửa giới tính, xóa sinh viên hoặc giả định tọa độ cho hàng không hợp lệ.
- Trả về danh sách lỗi kèm **số dòng Excel**, tên trường và lý do.
- Giới hạn kích thước file và số lượng bản ghi ở mức cấu hình để chống lạm dụng; từ chối file không phải Excel hoặc không đọc được.

### 5.2. Bộ dữ liệu kiểm thử đã có

- Tên file mẫu báo cáo: `danh_sach_sinh_vien_bao_cao.xlsx`.
- **30 sinh viên giả lập**, **18 nam** và **12 nữ**, địa chỉ chủ yếu quanh TP. Thủ Đức và Dĩ An cũ.
- Dữ liệu **giả lập**, không phải thông tin cá nhân của sinh viên thật.
- Kịch bản chuẩn: giảng viên nhập **3 nam + 2 nữ/nhóm**; kết quả phải là **6 nhóm**, mỗi nhóm **5 người, gồm 3 nam và 2 nữ** nếu mọi bản ghi có tọa độ hợp lệ.
- Bộ dữ liệu có một số tên địa danh hành chính cũ, có thể dùng kiểm thử sửa và xác minh địa chỉ.
- File mẫu chỉ được đưa vào GitHub khi đã chắc chắn là **dữ liệu giả lập**.

### 5.3. Cấu trúc bản ghi nội bộ đề xuất

```json
{
  "student_id": "S001",
  "excel_row": 2,
  "ho_ten": "Nguyễn Văn A",
  "gioi_tinh": "Nam",
  "dia_chi_goc": "Đường Hoàng Diệu 2, TP. Hồ Chí Minh",
  "dia_chi_da_sua": null,
  "vi_tri_dai_dien": null,
  "lat": null,
  "lon": null,
  "geocode_status": "pending",
  "geocode_confidence": null,
  "location_confirmed": false,
  "nhom": null
}
```

Các tên và tọa độ trong ví dụ là minh họa schema, **không phải kết quả đo hoặc geocoding thực tế**. Không ghi tọa độ giả vào sản phẩm hoặc báo cáo như dữ liệu đã kiểm chứng.

<a id="brd-06"></a>

## 6. Yêu cầu xác minh vị trí

### 6.1. Ràng buộc địa lý và quyền riêng tư

- Tập trung vào **nơi ở để học tập**; không yêu cầu sinh viên cung cấp số nhà.
- Mức chi tiết mục tiêu: tên đường/phường-khu vực/thành phố, hoặc ký túc xá công khai.
- Chỉ sử dụng điểm đại diện của địa chỉ được xác nhận; không mô tả đây là vị trí cửa nhà.
- Do thay đổi địa giới hành chính tại Việt Nam, phải xử lý thận trọng địa chỉ tên cũ như `Bình Dương`, `Linh Trung`; **không được tự thay thế mọi địa chỉ cũ theo một quy tắc duy nhất** nếu có thể làm sai vị trí.
- Lưu lại chuỗi gốc, chuỗi đã chỉnh, kết quả từ dịch vụ và trạng thái xác nhận; phục vụ kiểm tra lỗi trong phiên hiện tại.
- Nếu địa chỉ chỉ khớp ở cấp thành phố/tỉnh, không tự coi là đủ chính xác để chia nhóm.

### 6.2. Tích hợp dịch vụ

- Dùng **Geoapify Forward Geocoding API** thử nghiệm đầu tiên.
- Gọi từ backend FastAPI; tham số gồm `text`, `filter=countrycode:vn`, `format=json`, `limit` phù hợp và `apiKey` từ biến môi trường.
- Kiểm tra `lat`, `lon`, `result_type`, địa chỉ định dạng trả về và `rank.confidence`/mức độ khớp ở cấp đường khi có.
- Mức tin cậy **chỉ là tín hiệu hỗ trợ**, không thay thế việc kiểm tra khu vực và tên đường; ngưỡng lọc phải được hiệu chỉnh từ kết quả kiểm thử, không tự tuyên bố độ chính xác khi chưa đo.
- Nếu API không trả kết quả, báo lỗi, hết quota, hết thời gian chờ hoặc tọa độ nằm ngoài vùng địa lý mong đợi: không chấp nhận tự động.
- Có thể cache kết quả **trong phiên làm việc** theo chuỗi địa chỉ đã chuẩn hóa để tránh gọi lặp API; không lưu lịch sử trên server.
- Tôn trọng giới hạn truy cập, điều kiện sử dụng và yêu cầu ghi công nhà cung cấp dữ liệu/bản đồ.

Tài liệu chính thức: [Geoapify Forward Geocoding](https://apidocs.geoapify.com/docs/geocoding/forward-geocoding/), [Geoapify API keys](https://myprojects.geoapify.com/help/api-keys/).

### 6.3. Trạng thái và xử lý lỗi

| Trạng thái | Ý nghĩa | Thao tác |
|---|---|---|
| `pending` | Chưa geocode | Gửi yêu cầu geocoding. |
| `needs_review` | Không tìm thấy, kết quả mơ hồ hoặc chưa đủ chi tiết | Sửa địa chỉ ngay trong bảng; thử lại. |
| `verified` | Địa chỉ được hệ thống đối chiếu tự động đủ điều kiện hoặc giảng viên xác nhận sau kiểm tra | Cho phép dùng để chia nhóm. |
| `error` | Lỗi dịch vụ/kết nối/quota | Hiển thị nguyên nhân dễ hiểu; cho phép thử lại, không tự tạo tọa độ. |

**Quy tắc chặn:** nút **Chia nhóm** bị vô hiệu hóa nếu còn bất kỳ sinh viên nào chưa đạt `verified`. Giảng viên có thể xem bản đồ và danh sách lỗi trước khi hoàn tất.

**Cập nhật 24/10/2026 theo yêu cầu người dùng:** sau nhập Excel hợp lệ, giao diện tự tra cứu và đưa các vị trí đối chiếu rõ ràng lên bản đồ, không yêu cầu chọn/xác nhận từng sinh viên. Có thể thêm cột `Cư xá/Khu vực` (hoặc cột mẫu `Điểm cần xác nhận`) để chỉ rõ cư xá A–E trong khu Nông Lâm; địa chỉ gốc vẫn giữ nguyên. Danh tính cư xá được đối chiếu với Geoapify Places/OSM đã đăng ký. Địa chỉ thường cần confidence ít nhất 0,95 cùng tên và khu vực khớp; confidence cao đơn lẻ không đủ. Chỉ tự xác nhận khi duy nhất một ứng viên đủ điều kiện và phù hợp quy định giới tính. “KTX Nông Lâm” chung không suy ra A/B/C/D/E từ tên hay giới tính. Ngoại lệ hiện trong bộ lọc **Cần xử lý**; có thể chuyển **Tất cả sinh viên** để sửa điểm tự động.

Hai đường có nguồn đăng ký riêng dùng bộ đối chiếu tên đường/phường/vùng và confidence tối thiểu cấu hình thay cho ngưỡng chung0,95. Kiểm thử Geoapify thật với file mẫu đạt30/30tự động, có bản đồ và xuất Excel; xem [báo cáo tự đối chiếu](docs/reports/automatic-location.md). File khác vẫn có thể cần bổ sung các địa chỉ chưa rõ.

### 6.4. Sửa địa chỉ trên WebGIS

- Bảng kiểm tra có cột: dòng Excel, tên, địa chỉ gốc, địa chỉ đang sử dụng, kết quả khớp, trạng thái và nút **Sửa / Kiểm tra lại**.
- Sửa địa chỉ **không thay đổi** tên, giới tính hoặc `student_id`.
- Khi chỉnh chuỗi, phải xóa trạng thái xác nhận và kết quả tọa độ cũ; chỉ dùng tọa độ mới sau khi xác minh.
- Nếu nhiều kết quả, có thể cho giảng viên chọn kết quả phù hợp; không tự chọn một kết quả mơ hồ như chắc chắn đúng.
- Không yêu cầu nhập kinh độ/vĩ độ thủ công hoặc kéo điểm tới vị trí nhà riêng trong v1.0.

<a id="brd-07"></a>

## 7. Quy tắc nghiệp vụ chia nhóm

| Mã quy tắc | Nội dung bắt buộc |
|---|---|
| RULE-01 | Mỗi dòng sinh viên có định danh riêng; không gộp người chỉ vì trùng tên hoặc địa chỉ. |
| RULE-02 | Mọi sinh viên phải có vị trí `verified` trước khi chia nhóm; sửa địa chỉ phải xóa tọa độ và xác nhận cũ. |
| RULE-03 | `M`, `F` là số nguyên không âm, `M+F > 0`, `N > 0`; tự tính `k=max(1,floor(N/(M+F)))`. |
| RULE-04 | Mỗi sinh viên xuất hiện đúng một lần trong đúng một nhóm; không bỏ người để đạt tỷ lệ mong muốn. |
| RULE-05 | Tỷ lệ Nam/Nữ là mục tiêu linh hoạt khi dữ liệu không đáp ứng; phải thông báo sai lệch. |
| RULE-06 | Cân bằng quy mô nhóm theo `floor(N/k)` hoặc `ceil(N/k)` theo điều kiện chi tiết bên dưới. |
| RULE-07 | Thay đổi địa chỉ hoặc tham số Nam/Nữ làm kết quả cũ hết hiệu lực, phải tính lại trước khi xuất. |

Các ràng buộc tính toán, trường hợp ngoại lệ và tiêu chí đo lường được giữ nguyên dưới đây. Thuật toán đã chọn được mô tả tại Phụ lục A.

### 7.1. Các đầu vào và ràng buộc

- Danh sách **N** sinh viên với tọa độ đã xác nhận.
- `target_male` = `M`: số nam mong muốn trong nhóm.
- `target_female` = `F`: số nữ mong muốn trong nhóm.
- `M`, `F` là số nguyên không âm; **`M+F > 0`**.
- Từ chối tập không có sinh viên hoặc tọa độ thiếu/không hợp lệ.
- Ưu tiên gần nhau về địa lý và tỷ lệ nam/nữ mong muốn; **không biến tỷ lệ mong muốn thành ràng buộc cứng** khi dữ liệu không cho phép.

### 7.2. Xác định số nhóm tự động — ĐÃ CHỐT

```text
target_size = M + F
k = max(1, floor(N / target_size))
```

Không cho người dùng tự nhập `k` trong v1.0. Công thức xác định `k` dùng tổng số sinh viên, **không dùng số lượng của giới đang thiếu để giảm `k`**.

Ví dụ:

| N | M + F mong muốn | k | Phân bổ quy mô khả thi |
|---:|---|---:|---|
| 30 | 3 + 2 | 6 | 6 nhóm x 5 |
| 34 | 3 + 2 | 6 | 4 nhóm x 6 và 2 nhóm x 5 |
| 42 | 3 + 2 | 8 | 2 nhóm x 6 và 6 nhóm x 5 |
| 3 | 3 + 2 | 1 | 1 nhóm x 3 |

Kích thước thực tế của nhóm cần được cân bằng về **`floor(N/k)` hoặc `ceil(N/k)`** khi khả thi. Ví dụ 34 người chia 6 nhóm sẽ có quy mô 5–6 người/nhóm.

### 7.3. Đảm bảo tính đúng đắn

- `len(assignments) == N`.
- Tập `student_id` đầu ra **bằng** tập `student_id` đầu vào.
- Mỗi `student_id` xuất hiện **đúng một lần**.
- Có đúng `k` nhóm không rỗng khi `k <= N`.
- Quy mô giữa các nhóm chênh nhau không quá **1** khi nghiệm phân bổ đã chọn cho phép; nếu thuật toán không đáp ứng phải trả lỗi kiểm thử, không âm thầm công bố thành công.
- Khi N=30, Nam=18, Nữ=12, M=3, F=2: đạt 6 nhóm, mỗi nhóm 3 Nam + 2 Nữ.
- Nếu tỷ lệ tổng thể không đủ, trả kết quả **linh hoạt** và báo lệch so với mục tiêu, không loại bỏ bất kỳ người nào.

### 7.4. Khoảng cách và tiêu chí đánh giá

- **Haversine** trên WGS84 cho khoảng cách đường chim bay giữa hai điểm đại diện, đơn vị mét/km.
- Tính khoảng cách trung bình cặp thành viên trong từng nhóm và toàn bộ nhóm; có thể ghi thêm khoảng cách lớn nhất trong nhóm để phát hiện thành viên ở xa.
- Thống kê số lượng thành viên và Nam/Nữ theo nhóm, độ lệch với tỷ lệ mong muốn.
- So sánh với **baseline chia ngẫu nhiên** cùng `N`, `k` và quy mô nhóm; nếu so sánh mức độ gần nhau phải cố gắng giữ cùng ràng buộc giới để công bằng.
- Lặp baseline với các seed cố định và báo cáo trung bình/phân tán từ **kết quả chạy thực tế**.
- Không đánh đồng khoảng cách đường chim bay với thời gian hoặc quãng đường giao thông.

<a id="brd-08"></a>

## 8. Yêu cầu giao diện và tương tác

Ưu tiên một trang đơn giản, responsive trên máy tính, hỗ trợ màn hình điện thoại ở mức xem kết quả.

| Vùng giao diện | Thành phần |
|---|---|
| Header | Tên dự án, mô tả ngắn, trạng thái kết nối backend. |
| Bước 1 — Nhập dữ liệu | Upload Excel, nút đọc file, số lượng sinh viên/Nam/Nữ, bảng lỗi dữ liệu. |
| Bước 2 — Xác nhận vị trí | Bảng sinh viên, trạng thái Geoapify, sửa địa chỉ trên dòng, nút kiểm tra lại, bản đồ kiểm tra tọa độ. |
| Bước 3 — Thiết lập | Hai ô số `Nam/nhóm` và `Nữ/nhóm`, hiển thị `k` dự kiến, nút **Chia nhóm**. |
| Bước 4 — Kết quả | Bản đồ Leaflet, màu/nhãn nhóm, bộ lọc nhóm, bảng thành viên, thống kê khoảng cách và tỷ lệ. |
| Bước 5 — Xuất | Nút **Xuất danh sách nhóm (.xlsx)** sau khi tính thành công. |

**Quy tắc tương tác:**

- Không báo `Đã chia nhóm thành công` trước khi backend kiểm tra các bất biến.
- Nút **Chia nhóm** chỉ bật khi dữ liệu và tọa độ đều hợp lệ.
- Khi chỉnh địa chỉ hoặc thay đổi tham số Nam/Nữ sau khi đã chia, đánh dấu kết quả cũ **hết hiệu lực**, yêu cầu tính lại.
- Dùng màu sắc phân biệt nhóm nhưng kèm **số nhóm** trong popup/chú giải cho người khó phân biệt màu.
- Popup nên hiển thị tên, giới tính, số nhóm và địa chỉ đại diện; **không hiện địa chỉ nhà riêng hoặc tọa độ chính xác được coi là vị trí cư trú thật**.
- Bản đồ bắt buộc hiển thị ghi công cho nhà cung cấp nền bản đồ và nguồn dữ liệu thích hợp.

<a id="brd-09"></a>

## 9. Yêu cầu đầu ra

### 9.1. Dữ liệu kết quả

- Danh sách sinh viên có `student_id` và `nhom`.
- Danh sách nhóm với số lượng tổng, Nam, Nữ, tâm nhóm (cho tính toán/bản đồ), độ lệch tỷ lệ, khoảng cách trung bình và lớn nhất.
- Tập vị trí đại diện để hiển thị trên Leaflet.
- Chỉ số tổng thể của kết quả chia nhóm.

### 9.2. File `.xlsx`

Ưu tiên hai sheet:

1. **Danh_sach_nhom**: STT, Nhóm, Họ và tên, Giới tính, Nơi ở để học tập (đã xác nhận ở mức đại diện).
2. **Thong_ke_nhom**: Nhóm, tổng sinh viên, số nam, số nữ, khoảng cách trung bình và khoảng cách lớn nhất, ghi chú trường hợp tỷ lệ lệch.

Sắp xếp theo số nhóm rồi theo tên hoặc `student_id` ổn định. **Không xuất mặc định lat/lon thô**. Chỉ xuất dữ liệu sinh viên trong phiên mà người dùng đang thao tác. Nội dung file phải khớp chính xác với trạng thái kết quả đang hiển thị.

<a id="brd-10"></a>

## 10. Yêu cầu phi chức năng và bảo vệ dữ liệu

- Dùng **dữ liệu giả lập** khi demo công khai và đưa code lên GitHub.
- Không lưu lịch sử trong Supabase hoặc DB khác ở v1.0. Không lưu Excel người dùng tải lên hay tọa độ vào server lâu dài; nếu tạo file tạm phải dọn khi xử lý xong và không log dữ liệu cá nhân.
- Trước khi mở hệ thống công khai cho **dữ liệu thực**, phải bổ sung biện pháp kiểm soát truy cập, giới hạn request/size, vận hành an toàn và quy trình bảo vệ dữ liệu; phiên bản không đăng nhập chưa phù hợp để công khai dữ liệu sinh viên thật.
- Giới hạn CORS, bảo vệ API key, chống lạm dụng quota geocoding và xử lý lỗi rate limit.
- Không hiển thị dữ liệu quá chính xác so với mức sinh viên đã cung cấp; không hứa hệ thống có thể xác định vị trí nhà.
- Deployment tùy chọn sau khi chạy local và kiểm thử: frontend tĩnh + backend FastAPI trên Render hoặc nền tảng tương đương; sử dụng biến môi trường trên nền tảng deploy.

Các yêu cầu về giao diện tiếng Việt, khả năng xem trên điện thoại, nhãn nhóm ngoài màu sắc và thông báo lỗi được quy định tại mục 8 và Phụ lục F. Hệ thống phải có khả năng tái lập kết quả kiểm thử với seed cố định (mục 7, Phụ lục A và E). Chỉ tiêu hiệu năng định lượng chưa được chốt.

<a id="brd-11"></a>

## 11. Giả định, phụ thuộc và rủi ro

### 11.1. Giả định và phụ thuộc

- Giảng viên cung cấp file đúng schema và kiểm tra vị trí đại diện trước khi chia nhóm.
- Geoapify đã được kiểm thử thật ở Phase 3; xem [kết quả và hạn chế](docs/reports/geocoding-validation.md). File 30 sinh viên giả lập trong `data/samples/` có nguồn tạo, chưa xác nhận toàn bộ vị trí.
- Geocoding phụ thuộc kết nối mạng, quota và chất lượng dữ liệu của Geoapify; chất lượng tại vùng nghiên cứu chưa được xác minh.
- Thời gian 4 tuần là kế hoạch mục tiêu; triển khai công khai là tùy chọn sau khi chạy local và kiểm thử đạt yêu cầu.

### 11.2. Rủi ro và phương án xử lý

| Mã | Rủi ro / ảnh hưởng | Phương án trong phạm vi đã xác định |
|---|---|---|
| RISK-01 | Địa chỉ cũ, mơ hồ hoặc quá thô dẫn đến vị trí sai. | Giữ địa chỉ gốc, hỗ trợ sửa/retry, xác nhận vị trí và chặn chia nhóm khi chưa hợp lệ. |
| RISK-02 | Timeout, hết quota hoặc lỗi dịch vụ làm gián đoạn geocoding. | Báo nguyên nhân, cho phép thử lại, cache trong phiên và không tạo tọa độ giả. |
| RISK-03 | Tỷ lệ giới hoặc số lượng không chia hết mục tiêu. | Cân bằng quy mô, xử lý giới thiểu số, công bố độ lệch và bảo đảm đủ người. |
| RISK-04 | Vị trí đại diện và khoảng cách đường chim bay không phản ánh di chuyển thực tế. | Nêu rõ giới hạn đo lường trong kết quả đánh giá và báo cáo. |
| RISK-05 | Lộ khóa API hoặc dữ liệu sinh viên. | Gọi dịch vụ từ backend, dùng biến môi trường, không log/lưu lâu dài dữ liệu cá nhân, demo bằng dữ liệu giả lập. |

### 11.3. Các điểm cần xác định trước khi nghiệm thu

| Nội dung | Trạng thái |
|---|---|
| Chủ sở hữu tài liệu, người nghiệm thu và mốc phê duyệt | Chưa ghi nhận trong hồ sơ. |
| Giới hạn dung lượng Excel, số sinh viên và request | Yêu cầu có cấu hình; chưa chốt giá trị cụ thể. |
| Ngưỡng confidence và vùng địa lý chấp nhận | Cần hiệu chỉnh từ kiểm thử geocoding thực tế. |
| Mục tiêu thời gian xử lý và tỷ lệ geocoding thành công | Chưa chốt ngưỡng; không tự gán chỉ tiêu khi chưa đo. |

<a id="brd-12"></a>

## 12. Tiêu chí nghiệm thu và truy vết

AC-01 đến AC-14 có bằng chứng kiểm tra trong [nghiệm thu Phase 7](docs/reports/acceptance.md), gồm 243 test Python, kiểm thử trình duyệt và dịch vụ thật trên mẫu giả lập. [Đánh giá baseline](docs/reports/evaluation.md) công bố phương pháp, số liệu và giới hạn. Đây là nghiệm thu MVP local, không phải cam kết uptime hay độ chính xác địa chỉ cho mọi dữ liệu thực. Đối chiếu mã AC với danh mục BR tại mục 4.

- [x] **AC-01:** Giảng viên upload file Excel đúng mẫu và thấy được số lượng Nam/Nữ.
- [x] **AC-02:** Lỗi cột/dữ liệu được chỉ rõ theo dòng, không làm mất sinh viên.
- [x] **AC-03:** Geocoding hoạt động qua backend, không làm lộ API key.
- [x] **AC-04:** Địa chỉ sai/không đủ tin cậy có thể sửa trực tiếp trên WebGIS rồi geocode lại.
- [x] **AC-05:** Không thể chia nhóm khi vẫn còn sinh viên chưa xác nhận vị trí.
- [x] **AC-06:** Tự tính `k=max(1,floor(N/(M+F)))` với đầu vào hợp lệ.
- [x] **AC-07:** 30 sinh viên mẫu (18 Nam, 12 Nữ), cấu hình 3+2 cho ra 6 nhóm đúng tỷ lệ.
- [x] **AC-08:** Trường hợp có sinh viên dư, lệch giới hoặc một giới ít hơn `k` không làm crash hay bỏ sót người.
- [x] **AC-09:** Mọi sinh viên được gán đúng một nhóm; quy mô nhóm được cân bằng.
- [x] **AC-10:** Bản đồ, bộ lọc, bảng thành viên và thống kê hiển thị nhất quán; có nguồn Geoapify / OSM dự phòng khi host OSM không kết nối được.
- [x] **AC-11:** Xuất Excel đủ N sinh viên và có sheet thống kê.
- [x] **AC-12:** Có test tự động, phép đo Haversine và baseline thực nghiệm phục vụ báo cáo.
- [x] **AC-13:** Dùng dữ liệu giả lập, không lưu lịch sử trên server, không commit key.
- [x] **AC-14:** Sửa địa chỉ hoặc thay đổi tham số Nam/Nữ làm kết quả cũ hết hiệu lực; chỉ xuất kết quả sau khi tính lại thành công.

<a id="brd-13"></a>

## 13. Kế hoạch và trạng thái dự án

Kế hoạch thực hiện gồm **7 phase**: [Kế hoạch phát triển WebGIS theo phase](docs/superpowers/plans/2026-10-21-webgis-development-phases.md). Đã triển khai Phase 1–7; bằng chứng tại [Phase 1](docs/reports/phase-1.md), [Phase 2](docs/reports/phase-2.md), [Phase 3](docs/reports/phase-3.md), [Phase 4](docs/reports/phase-4.md), [Phase 5](docs/reports/phase-5.md), [Phase 6](docs/reports/phase-6.md), [nghiệm thu Phase 7](docs/reports/acceptance.md) và [đánh giá thuật toán](docs/reports/evaluation.md). Chỉnh giao diện và hosting là công việc tiếp theo theo yêu cầu.

### 13.1. Lộ trình 4 tuần

| Thời gian | Trọng tâm | Điều kiện hoàn thành |
|---|---|---|
| **Tuần 1** | Tạo cấu trúc; đọc/validate Excel; kết nối Geoapify; sửa địa chỉ trên web | Bộ dữ liệu giả lập đọc đủ; địa chỉ lỗi được hiển thị/sửa/retry; không rò rỉ key. |
| **Tuần 2** | Thuật toán `k`, K-Means giới tính, cân bằng, Hungarian, Haversine | Test 30 người 3+2 đạt 6 nhóm; test số dư và một giới thiếu; bất biến đều đạt. |
| **Tuần 3** | Giao diện Leaflet, bản đồ nhóm, thống kê, Excel export; kết nối API | Hoàn thành luồng từ upload đến xuất file trên local. |
| **Tuần 4** | Test end-to-end, đo chỉ số với baseline, sửa lỗi, demo/deploy tùy chọn, báo cáo | Tái lập kết quả test; có số liệu thực nghiệm và ảnh chụp chức năng phục vụ báo cáo. |

Lịch trên là **kế hoạch**, không phải cam kết chức năng đã hoàn thành.

### 13.2. Trạng thái theo hồ sơ dự án

| Hạng mục | Trạng thái |
|---|---|
| Phân tích bài toán và chốt phạm vi v1.0 | Đã thống nhất |
| Chốt công thức `k`, phương án xử lý dư và tỷ lệ nam/nữ linh hoạt | Đã thống nhất yêu cầu |
| Chốt sửa địa chỉ trên web, xuất Excel, không lưu lịch sử | Đã thống nhất |
| Dữ liệu 30 sinh viên giả lập | Đã tạo file mẫu trong `data/samples/`, 18 Nam/12 Nữ |
| Tài khoản và API key Geoapify | Người dùng xác nhận đã có |
| Kiểm thử Geoapify với địa chỉ công cộng | Mẫu 30 người giả lập/9 địa chỉ tự đối chiếu đủ trong lần nghiệm thu; chưa đo accuracy bằng ground truth |
| Bộ khung FastAPI, frontend Leaflet và kiểm thử health/CORS | Đã triển khai Phase 1; xem báo cáo kiểm tra |
| Nhập Excel, kiểm tra theo dòng và bảng sinh viên | Đã triển khai Phase 2; xem báo cáo kiểm tra |
| Geocoding và xác nhận vị trí | Đã triển khai Phase 3 |
| API chia nhóm, cân bằng và thống kê Haversine | Đã triển khai Phase 4 |
| Giao diện kết quả, bộ lọc và thống kê đồng bộ | Đã triển khai Phase 5 |
| Xuất Excel và nguồn bản đồ dự phòng | Đã triển khai Phase 6 |
| Đánh giá baseline và nghiệm thu tổng thể | Đã triển khai Phase 7; báo cáo và snapshot tái lập trong `docs/reports/`, `data/evaluation/` |
| Chỉnh trình bày giao diện / hosting | Theo yêu cầu sau; không thuộc lần nghiệm thu local này |

> Đây là **đặc tả đầu vào cho quá trình phát triển**, không phải báo cáo tuyên bố rằng phần mềm đã hoàn thành.

**Đối chiếu repository:** đã có toàn bộ luồng từ Excel đến xuất nhóm, kiểm thử Phase 1–7 trong `tests/` và `scripts/`; mẫu giả lập trong `data/samples/`; snapshot và report đánh giá trong `data/evaluation/`. Khóa Geoapify chỉ nằm trong cấu hình backend riêng, không đưa vào Git/frontend.

<a id="brd-14"></a>

## 14. Giới hạn và hướng phát triển

**Giới hạn v1.0:** geocoding phụ thuộc chất lượng dữ liệu Geoapify/OSM; địa chỉ cấp đường chỉ cho vị trí đại diện; thuật toán không xét tuyến đường, ùn tắc, thời gian di chuyển; K-Means và Hungarian mang tính heuristic cho toàn bài toán tổ hợp.

**Hướng phát triển (chưa triển khai):** tài khoản giảng viên, lưu lịch sử an toàn bằng Supabase/PostGIS, điều chỉnh nhóm thủ công có kiểm tra ràng buộc, tối ưu theo mạng lưới giao thông, nhiều tiêu chí phân nhóm, quản trị dữ liệu thật và kiểm soát truy cập.

<a id="appendices"></a>

## Phụ lục A. Ràng buộc thuật toán đã chọn

### A.1. Thuật toán chủ đạo — Cách A trong hồ sơ

1. Tách sinh viên thành danh sách **Nam** và **Nữ**.
2. Chuyển vị trí sang hệ tọa độ phẳng có đơn vị mét phù hợp vùng nghiên cứu (ví dụ UTM cho phạm vi quanh TP.HCM) để K-Means không coi một độ vĩ độ và một độ kinh độ là cùng độ dài.
3. Nếu số sinh viên ở **mỗi giới ≥ k**, chạy `KMeans(n_clusters=k)` **riêng cho Nam và riêng cho Nữ**. Đặt `random_state` cố định để tái lập kết quả kiểm thử.
4. **Hậu xử lý cân bằng:** K-Means gốc không bảo đảm cụm đều; điều chuyển thành viên giữa các cụm cùng giới một cách có kiểm soát để đáp ứng phân bổ số lượng hợp lý, cố gắng tăng khoảng cách ít nhất.
5. Tính tâm các cụm và ma trận **k × k** khoảng cách tâm cụm **Haversine**.
6. Ghép mỗi cụm Nam với một cụm Nữ bằng `scipy.optimize.linear_sum_assignment` (Hungarian) để tối thiểu hóa tổng khoảng cách giữa các tâm cụm.
7. Kết hợp các cặp thành `k` nhóm; hiệu chỉnh phân bổ nếu cần để đạt quy mô nhóm mục tiêu và ưu tiên tỷ lệ giới.
8. Đánh số nhóm ổn định, tính thống kê và kiểm tra bất biến dữ liệu.

**Trường hợp thiếu giới tính:** nếu một giới có **ít hơn `k` sinh viên** hoặc hoàn toàn không có sinh viên, không được gọi K-Means với `n_clusters > n_samples`. Khi đó hình thành các nhóm vị trí từ giới đủ số lượng hoặc toàn bộ dữ liệu, rồi phân bổ sinh viên giới thiểu số vào nhóm phù hợp gần nhất, giữ ưu tiên quy mô. Ghi nhận lý do tỷ lệ lệch trong thống kê. Đây là ngoại lệ bắt buộc, không phải lỗi làm dừng hệ thống.

**Lưu ý học thuật:** thuật toán chính là **K-Means riêng từng giới + cân bằng + Hungarian**, không thay bằng Greedy Nearest-Neighbor hoặc K-Means chung rồi đổi chéo tùy tiện. Hậu xử lý gần nhất chỉ là bước cân bằng/phân bổ phụ trợ, không phải thuật toán chính. Không khẳng định phương án tìm được là tối ưu toàn cục của mọi ràng buộc.

## Phụ lục B. Kiến trúc và hợp đồng API đề xuất

### B.1. Kiến trúc kỹ thuật

```text
Trình duyệt
  └── HTML / CSS / JavaScript + Leaflet
         │ HTTP JSON / multipart
         ▼
Backend Python FastAPI
  ├── ExcelService: pandas, openpyxl
  ├── GeocodingService: requests/httpx, Geoapify, python-dotenv
  ├── GroupingService: numpy, scikit-learn, scipy, pyproj
  ├── MetricsService: Haversine, thống kê, baseline
  └── ExportService: pandas/openpyxl, trả .xlsx

Không có cơ sở dữ liệu và không có GeoServer trong MVP.
```

- Frontend chịu trách nhiệm giao diện, quản lý dữ liệu của phiên, gọi API và vẽ bản đồ.
- Backend chịu trách nhiệm đọc Excel, gọi dịch vụ Geoapify, kiểm tra dữ liệu, thuật toán, thống kê và sinh file Excel.
- Không nhúng API key Geoapify vào JavaScript hoặc request từ frontend trực tiếp đến Geoapify.
- API trả lỗi thống nhất bằng JSON rõ ràng, có số dòng/student_id liên quan.
- Có thể triển khai frontend tĩnh và backend FastAPI độc lập sau khi thử nghiệm local ổn định.

### B.2. Hợp đồng REST API

Đường dẫn có thể tinh chỉnh khi viết code, nhưng **hành vi nghiệp vụ phải giữ nguyên**.

| Phương thức | Endpoint | Mục đích |
|---|---|---|
| GET | `/api/health` | Kiểm tra backend hoạt động (không lộ secrets). |
| POST | `/api/students/import` | Nhận `multipart/form-data` file Excel; trả bản ghi đã kiểm tra và lỗi từng dòng. |
| POST | `/api/geocode/batch` | Geocode địa chỉ của danh sách; trả các kết quả/tình trạng từng sinh viên. |
| POST | `/api/geocode/retry` | Geocode lại một `student_id` với địa chỉ đã sửa, không làm mất người. |
| POST | `/api/groups/generate` | Nhận danh sách vị trí đã xác nhận và M/F; tính nhóm, trả assignments + thống kê. |
| POST | `/api/groups/export` | Nhận kết quả đang hiển thị; trả file Excel dạng download. |

### B.3. Contract sinh nhóm minh họa

```json
{
  "students": [
    {
      "student_id": "S001",
      "ho_ten": "Nguyễn Văn A",
      "gioi_tinh": "Nam",
      "dia_chi": "Đường Hoàng Diệu 2, TP. Hồ Chí Minh",
      "lat": 10.8,
      "lon": 106.7,
      "location_confirmed": true
    }
  ],
  "target_male": 3,
  "target_female": 2
}
```

Tọa độ ở đoạn ví dụ là **giá trị minh họa hợp đồng dữ liệu**, không phải điểm thực. Khi thực thi, bắt buộc dùng bản ghi đã xác thực và tọa độ đã xác nhận.

Phản hồi thành công nên có: `k`, `assignments` (student_id + nhom), `groups` (thành viên và thống kê), `overall_metrics` và các `warnings` về sai lệch tỷ lệ. Lỗi dùng HTTP 400/422 cho dữ liệu/logic không hợp lệ; 429, 502 hoặc 503 phù hợp với sự cố gọi Geoapify; không trả stack trace hoặc API key ra trình duyệt.

## Phụ lục C. Cấu trúc thư mục đề xuất

```text
webgis-student-grouping/
├── README.md
├── .gitignore
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── api/
│       │   ├── students.py
│       │   ├── geocoding.py
│       │   └── groups.py
│       ├── core/
│       │   └── config.py
│       ├── schemas/
│       │   └── student.py
│       └── services/
│           ├── excel_service.py
│           ├── geocoding_service.py
│           ├── grouping_service.py
│           ├── metrics_service.py
│           └── export_service.py
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       ├── api.js
│       └── map.js
├── data/
│   └── samples/
│       └── danh_sach_sinh_vien_bao_cao.xlsx
├── tests/
│   ├── test_excel.py
│   ├── test_geocoding.py
│   ├── test_grouping.py
│   └── test_export.py
└── docs/
    └── images/
```

Đây là **cấu trúc đích** để Codex tạo dần, **không phải mô tả các file đã hoàn thành**. Chỉ đưa file mẫu giả lập vào `data/samples`; không tự sao chép dữ liệu thật vào repository.

## Phụ lục D. Chạy WebGIS local trên Windows PowerShell

Yêu cầu Python 3.10 trở lên (đã kiểm tra với Python 3.13), Git và trình duyệt hiện đại. Chạy lệnh từ thư mục gốc dự án. Kiểm tra `python --version` trước khi tạo môi trường; trên máy phát triển hiện tại, `py` mặc định trỏ tới Python 2.7 nên hướng dẫn dùng `python`.

**Chạy chung frontend/backend sau khi đã cài môi trường:** mở `start-webgis.cmd` ở thư mục gốc (hoặc gõ `.\start-webgis.cmd` trong PowerShell). Chờ dòng `READY`, mở **http://127.0.0.1:5500** và giữ runner hoạt động. Nhấn **Ctrl+C** trong cửa sổ runner để dừng cả hai dịch vụ. Launcher dùng Python trong `.venv`, chạy từ đúng thư mục, kiểm tra health/CORS/assets, chờ khởi động tối đa90giây; nếu một tiến trình thoát thì dừng các tiến trình con còn lại và báo lỗi. Không cài service hoặc tự chạy khi mở máy.

Kiểm tra trạng thái chỉ đọc bằng `.\.venv\Scripts\python.exe scripts/run_local.py --check`. Log nằm ở `.local-tests/local-server/backend.log` và `frontend.log`. Nếu cổng8001/5500 bị chiếm, launcher báo lỗi và không dừng ứng dụng đang giữ cổng. Không chạy đồng thời launcher với hai lệnh server thủ công bên dưới. Khi cả hai địa chỉ đều không truy cập được, kiểm tra runner còn chạy; health OK chưa xác nhận Geoapify/key/quota hoạt động. Xem [báo cáo sửa truy cập local](docs/reports/local-readiness.md).

### D.1. Cài đặt và chạy backend

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001 --reload
```

Backend: `http://127.0.0.1:8001`; OpenAPI: `http://127.0.0.1:8001/docs`; health: `http://127.0.0.1:8001/api/health` trả `{"status":"ok"}`. Chọn cổng 8001 vì 8000 đang được ứng dụng khác sử dụng trên máy phát triển. Không cần kích hoạt môi trường ảo hoặc thay đổi ExecutionPolicy.

### D.2. Cấu hình môi trường

Phase 1–2 chạy được khi chưa có `.env` và chưa có khóa Geoapify. Khi cần cấu hình riêng, sao chép `backend/.env.example` thành `backend/.env` nếu file chưa tồn tại, rồi chỉnh trên máy:

```dotenv
GEOAPIFY_API_KEY=
GEOCODING_COUNTRY=vn
CORS_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
MAX_UPLOAD_BYTES=5242880
MAX_STUDENT_ROWS=1000
```

Biến môi trường có ưu tiên hơn giá trị trong `backend/.env`; vị trí file được xác định từ mã backend, không phụ thuộc thư mục chạy lệnh. CORS nhận danh sách origin HTTP(S) cách nhau bằng dấu phẩy, không chứa đường dẫn hoặc dấu `/` cuối. Health chỉ phản ánh backend đang chạy, không xác nhận khóa hoặc chất lượng Geoapify.

Không dán khóa thật vào README, source code, issue, commit hoặc ảnh chụp. `.gitignore` loại trừ `.env*` (ngoại trừ `.env.example`), `.venv/`, cache, `.local-tests/`, `data/private/`, `data/uploads/`, `data/exports/` và `backend/tmp/`. Đặt dữ liệu cá nhân thực trong `data/private/`; chỉ dùng dữ liệu giả lập cho fixture và demo.

### D.3. Chạy frontend

Mở terminal PowerShell thứ hai:

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Mở **http://127.0.0.1:5500**. Giao diện hỗ trợ nhập Excel, sửa/xác nhận vị trí, cấu hình Nam/Nữ, chia nhóm, xem bản đồ/bảng/lọc/thống kê và xuất Excel. Bản đồ tự chuyển Geoapify / OSM khi nền OpenStreetMap lỗi; ghi rõ nguồn và có nút thử lại khi không tải được.

Base URL backend chỉ cấu hình tại `frontend/js/api.js`. Nếu đổi cổng backend, sửa cùng giá trị tại đây; nếu đổi địa chỉ frontend, cập nhật `CORS_ORIGINS` và khởi động lại backend. Không chạy bằng `file://`. Nhấn `Ctrl+C` ở từng terminal để dừng server.

Leaflet và bản đồ nền cần Internet. Khi CDN không phản hồi trong 8 giây, giao diện báo lỗi tải bản đồ; health check hoạt động độc lập và có timeout 5 giây. Khi backend chưa chạy, mở backend rồi nhấn **Kiểm tra lại**. Cấu hình Leaflet tham khảo [tài liệu chính thức](https://leafletjs.com/examples/quick-start/).

### D.4. Kiểm tra tự động

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Kiểm tra trình duyệt tùy chọn, cần Microsoft Edge và hai server ở trên đang chạy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-browser.txt
.\.venv\Scripts\python.exe scripts/check_phase1_browser.py
```

Script kiểm tra kết nối thật, bản đồ, trạng thái mất kết nối/thử lại, bố cục điện thoại và CDN lỗi/chậm. Ảnh kiểm tra nằm trong `.local-tests/phase-1/` và không đưa vào Git. Kết quả thực tế và hạn chế được ghi tại [báo cáo Phase 1](docs/reports/phase-1.md).

### D.5. Sử dụng chức năng nhập Excel

1. Tại **Danh sách sinh viên**, chọn file `.xlsx`; có thể dùng [file mẫu 30 sinh viên giả lập](data/samples/danh_sach_sinh_vien_bao_cao.xlsx).
2. Nhấn **Đọc danh sách**. Hệ thống đọc sheet đầu tiên, tiêu đề ở dòng 1, theo tên cột bắt buộc; thứ tự cột tùy ý. Đọc thêm cột tùy chọn `Cư xá/Khu vực` hoặc `Điểm cần xác nhận` để bổ sung địa điểm tìm kiếm, bỏ qua các cột khác.
3. Xem tổng dòng dữ liệu, Nam, Nữ và số dòng cần sửa. Dòng rỗng xen giữa hoặc giới tính ngoài `Nam`/`Nữ` vẫn xuất hiện với số dòng Excel, trường lỗi và lý do.
4. Nếu có lỗi, sửa trong Excel rồi tải lại. Chọn file mới xóa dữ liệu nhập trước đó; không tiếp tục xác minh khi còn lỗi.

File mẫu do `scripts/create_report_sample.py` tạo, không phải danh tính của sinh viên thật; [nguồn và cách tái tạo](data/samples/README.md). Địa chỉ chưa geocode nên mọi bản ghi đều có vị trí `pending`, tọa độ rỗng. Dữ liệu hợp lệ sau import chỉ có nghĩa là hợp lệ để xác minh vị trí, chưa đủ điều kiện chia nhóm.

Giới hạn mặc định: **5 MiB/file, 1.000 dòng sau tiêu đề**; thay đổi bằng hai biến `MAX_UPLOAD_BYTES` và `MAX_STUDENT_ROWS`, đều phải là số nguyên dương. Dòng rỗng cuối sheet được bỏ qua trong giới hạn quét; nếu file có định dạng kéo dài quá giới hạn dòng, hãy xóa các dòng thừa trước khi tải. Giới hạn đọc bổ sung: 256 cột, 20 MiB nội dung giải nén, 2.000 ZIP entries và 2.000 ký tự/trường bắt buộc. Không chấp nhận công thức ở các trường bắt buộc.

API `POST /api/students/import` nhận multipart trường `file`, trả `students`, `errors`, `summary`, `can_proceed`, `worksheet`. Lỗi từng dòng trả HTTP 200 với `can_proceed=false` để xem/sửa đủ dữ liệu; lỗi file/schema trả HTTP 400/413/422 với cùng cấu trúc lỗi. Không lưu lịch sử hay workbook lâu dài; refresh trang xóa danh sách.

Kiểm tra Phase 2 trên Edge (script tự tạo và dừng server thử ở cổng 8012/5512, không cần dừng server phát triển):

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt -r backend/requirements-browser.txt
.\.venv\Scripts\python.exe scripts/check_phase2_browser.py
```

Bộ kiểm tra này chặn CDN bản đồ có chủ đích để tập trung vào upload/API, bảng dữ liệu và thay đổi file; kiểm tra bản đồ thật thuộc script Phase 1. Ảnh kiểm tra ở `.local-tests/phase-2/`. Nếu server đang chạy phiên bản cũ, dừng bằng `Ctrl+C`, cài dependency cập nhật và chạy lại lệnh Uvicorn ở D.1.

### D.6. Geocoding và xác nhận vị trí

Điền `GEOAPIFY_API_KEY` trong `backend/.env` (tạo từ `.env.example` nếu chưa có), rồi khởi động lại backend. Không điền khóa thật vào file mẫu hoặc JavaScript.

1. Nhập Excel hợp lệ: hệ thống tự đối chiếu tuần tự, dùng lại kết quả cho địa chỉ trùng và tự hiển thị điểm đủ điều kiện lên bản đồ. Tiến độ ghi số đã xác định/tự động/cần xử lý.
2. Chỉ xử lý các địa chỉ còn trong **Cần xử lý**: bổ sung cư xá/tên đường/phường hoặc chọn ứng viên đủ điều kiện, xem bản đồ rồi xác nhận. Chọn **Tất cả sinh viên** để xem/sửa các điểm tự động. Khi dịch vụ lỗi, hàng đợi tạm dừng; nhấn **Đối chiếu lại vị trí còn thiếu** sau khi kết nối phục hồi.
3. Nếu chưa khớp, sửa ô địa chỉ rồi **Kiểm tra lại**. Thao tác sửa xóa tọa độ và xác nhận cũ ngay lập tức; tên, giới tính, ID và địa chỉ gốc được giữ.
4. Refresh hoặc chọn file mới xóa trạng thái phiên/cache. Xác nhận đủ vị trí rồi dùng bước 03 để cấu hình và chia nhóm; bước 04 có bộ lọc, bảng thành viên và thống kê.

API: `POST /api/geocode/batch` với `students: [{student_id, address}]`, tối đa 5 dòng; `POST /api/geocode/retry` với `{student_id, address}`. JSON tối đa 64 KiB. API trả ứng viên và cờ `auto_selectable`; frontend xác nhận tự động sau kiểm tra duy nhất/giới tính, các ứng viên còn lại giữ `needs_review`. `location_method` trong phiên phân biệt `automatic`/`manual`; không gửi trường này sang API chia nhóm. Lỗi thiếu khóa trả 503, đang bận/cooldown trả 429; lỗi upstream từng dòng nằm trong `status=error` và `error_code`.

Cấu hình mặc định: timeout 8 giây, khoảng cách gọi 1 giây, confidence 0.7, bounds `106.4,10.5,107.0,11.2` (west,south,east,north). Các biến `GEOCODING_TIMEOUT`, `GEOCODING_INTERVAL`, `GEOCODING_MIN_CONFIDENCE`, `GEOCODING_BOUNDS` nằm trong `.env.example`. Bộ giới hạn áp dụng trên mỗi tiến trình; dùng một worker local. Confidence/bounds là bộ lọc sơ bộ, không thay thế kiểm tra địa chỉ của người dùng.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check_phase3_browser.py
# Các lệnh sau cần Internet và khóa thật; browser live cần server 8001/5500:
.\.venv\Scripts\python.exe scripts/validate_geocoding.py
.\.venv\Scripts\python.exe scripts/check_phase3_live_browser.py
```

Browser regression dùng Geoapify giả lập có ghi rõ, tự tạo/dừng server 8013/5513. Báo cáo API thật và hạn chế địa chỉ: [geocoding-validation.md](docs/reports/geocoding-validation.md). Artifacts nằm trong `.local-tests/phase-3/`, không commit.

### D.7. API chia nhóm và thống kê (Phase 4)

Cài dependency cập nhật và khởi động lại backend theo D.1; `/openapi.json` có phiên bản `0.4.0`, giao diện API tại `http://127.0.0.1:8001/docs`.

`POST /api/groups/generate` nhận:

```json
{
  "students": [{
    "student_id": "DEMO-01", "ho_ten": "Sinh viên mẫu 01", "gioi_tinh": "Nam",
    "dia_chi_goc": "Đường Võ Văn Ngân, Thủ Đức",
    "vi_tri_dai_dien": "Vo Van Ngan Street, Thủ Đức",
    "lat": 10.8496978, "lon": 106.7691507,
    "geocode_status": "verified", "location_confirmed": true
  }],
  "target_male": 3,
  "target_female": 2
}
```

Đây là payload minh họa một sinh viên giả lập (k=1), không chứng minh địa chỉ của người thật. Khi dùng dữ liệu phiên, chỉ gửi các trường schema; `excel_row`, `dia_chi_da_sua`, `geocode_confidence` là tùy chọn. Không gửi candidates/selectedCandidate hoặc trường UI tạm. M/F phải là số nguyên không âm, tổng lớn hơn 0; mọi vị trí phải được xác nhận và nằm trong bounds hiện hành. Tối đa 1.000 người, không vượt `MAX_STUDENT_ROWS`, JSON tối đa 8 MiB.

Response gồm `k`, `target_male`, `target_female`, `seed`, `strategy`, `assignments`, `groups`, `overall_metrics`, `warnings`. Mỗi nhóm có thành viên, size, Nam/Nữ, độ lệch mục tiêu, tâm nhóm và `metrics` (số cặp, khoảng cách trung bình/lớn nhất theo mét). Trung bình toàn bộ có trọng số số cặp nội nhóm; singleton trả 0.

Thuật toán dùng UTM 48N, KMeans riêng giới, quota cân bằng và ghép Hungarian có ràng buộc size; thiếu giới dùng fallback được mô tả trong [kế hoạch chi tiết](docs/superpowers/plans/2026-10-23-phase-4-grouping.md). Cảnh báo giải thích trường hợp không đạt mục tiêu. HTTP 422 cho input không hợp lệ, 413 vượt giới hạn, 429 đang có job, 500 nếu không tạo được partition hợp lệ. Không trả kết quả thiếu người để báo thành công.

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
# Tự dùng fixture tổng hợp và tạo/dừng API server 8014; không cần JSON demo cũ:
.\.venv\Scripts\python.exe scripts/check_phase4_api.py
```

[Báo cáo Phase 4](docs/reports/phase-4.md) ghi kết quả HTTP thật và giới hạn. Phase 5 nối cấu hình Nam/Nữ, bản đồ, bảng/lọc và thống kê; Phase 6 bổ sung xuất Excel và bản đồ dự phòng. Xem [Phase 5](docs/reports/phase-5.md), [Phase 6](docs/reports/phase-6.md) và [checklist UI](docs/reports/ui-checklist.md). Thay M/F, sửa địa chỉ hoặc upload mới làm kết quả hết hiệu lực và phải tính lại. [Đánh giá Phase 7](docs/reports/evaluation.md) có baseline 30 seed; không khẳng định tối ưu toàn cục.

### D.8. Chạy nghiệm thu và đánh giá Phase 7

```powershell
./.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider
./.venv/Scripts/python.exe -B scripts/check_phase7_browser.py
./.venv/Scripts/python.exe -B scripts/evaluate_grouping.py --input data/evaluation/confirmed-sample-30.json --output .local-tests/phase-7/evaluation-repeat.json
```

Browser test cần Playwright và Edge theo hướng dẫn cài phụ thuộc trình duyệt ở trên; dùng server riêng 8027/5527 và mock HTTP nhà cung cấp, không cần key/mạng. Lệnh đánh giá chạy offline trên snapshot giả lập có nguồn, không tự geocode. [Nguồn dữ liệu và cách tái lập](data/evaluation/README.md).

Kiểm tra dịch vụ thật dùng `./.venv/Scripts/python.exe -B scripts/check_phase7_live.py`, cần key backend và mạng, chạy server riêng 8028/5528 và chỉ dùng workbook giả lập đi kèm. Xem [nghiệm thu](docs/reports/acceptance.md) để biết các lệnh regression bổ sung, phân biệt fixture/dịch vụ thật và giới hạn. Có thể sửa bố cục/màu sắc sau; khi đổi tương tác hoặc selector, cập nhật và chạy lại browser test liên quan.

Kiểm tra UI Phase 5 bằng `python -B scripts/check_phase5_browser.py` trong venv; thêm `--map` để kiểm tra marker/màu/nhãn với Leaflet thật. Script tự tạo/dừng server 8015/5516, dùng vị trí tổng hợp và API chia nhóm thật, chặn proxy tile để không gọi Geoapify.

Xuất file bằng nút **Xuất danh sách nhóm (.xlsx)** sau khi chia nhóm thành công. `POST /api/groups/export` nhận toàn bộ response chia nhóm hiện hành, kiểm tra ID, số người, Nam/Nữ và tính lại metrics Haversine trước khi trả workbook trong bộ nhớ. Hai sheet là `Danh_sach_nhom` và `Thong_ke_nhom`, không có lat/lon thô; lọc giao diện không giảm số người xuất. Dữ liệu thay đổi hủy download đang chờ. Request tối đa 8 MiB, tối đa 1.000 sinh viên và tuân thủ `MAX_STUDENT_ROWS`.

Nền bản đồ thử OpenStreetMap trước; nếu lỗi/treo sẽ chuyển Geoapify / OSM qua `GET /api/map/tiles/{z}/{x}/{y}.png`. Nguồn dự phòng dùng `GEOAPIFY_API_KEY` hiện có ở backend, cần mạng và quota Geoapify. Giao diện ghi nguồn, attribution và cho thử lại khi lỗi. Proxy chỉ gọi endpoint raster cố định, deadline tổng 10 giây, cache bộ nhớ tối đa 64 tile/300 giây; không trả khóa cho browser.

Chạy `python -B scripts/check_phase6_browser.py` để kiểm tra download XLSX qua API thật và các tình huống lỗi bản đồ bằng network fixture với Leaflet thật. Thêm `--live-map` để kiểm tra ảnh nền dịch vụ thật (cần mạng/key/quota); script tự tạo/dừng server 8016/5518. Xem [báo cáo Phase 6](docs/reports/phase-6.md).

### D.9. Điền địa chỉ thật và kiểm tra hai ký túc xá sau sáp nhập

Cột địa chỉ trong file import phải mang tiêu đề **Nơi ở để học tập**. Ghi một nơi đang ở để học tập cho mỗi sinh viên, theo `Tên KTX/đường, khu phố (nếu biết), phường/xã mới, tỉnh/thành phố mới`. Không chỉ ghi “KTX”, không cần số phòng. Hai chuỗi chuẩn và nguồn chính thức nằm tại [hướng dẫn địa chỉ KTX](docs/reports/dormitory-addresses.md).

[File mẫu báo cáo hiện tại](data/samples/danh_sach_sinh_vien_bao_cao.xlsx) có 30 sinh viên, 18 Nam/12 Nữ, đủ cư xá A–E, Cỏ May, KTX khu B và hai đường ngoài KTX; tất cả dùng địa chỉ mới. Cột cuối hướng dẫn chọn điểm, hai sheet phụ ghi kịch bản và nguồn. File thay thế toàn bộ mẫu Excel cũ. [Kết quả kiểm thử và giới hạn](docs/reports/report-sample.md).

Với các alias đã đối chiếu của đúng hai địa danh, backend tra Geoapify Places theo đối tượng OSM và vùng nhỏ. Tọa độ lấy từ API thật; nhãn dropdown/popup dùng địa chỉ mới theo nguồn chính thức. `source=geoapify_places`, `confidence=null` vì Places không có điểm confidence kiểu forward geocoding. Nông Lâm có các lựa chọn Cư xá A–E, cần chọn đúng tòa khi biết; nếu chỉ biết khu KTX, đó là điểm đại diện của khu. Địa chỉ khác tiếp tục dùng forward geocoding và ngưỡng confidence đã cấu hình. Không có bước tự xác nhận vị trí.

Ảnh nền raster OSM do nhà cung cấp cập nhật và có thể còn chữ địa danh cũ; nhãn địa chỉ do ứng dụng hiển thị là phần được chuẩn hóa ở đây. Xem nguồn, tọa độ đối chiếu, cách tái tạo và kiểm thử thật trong báo cáo trên.

Theo thông tin người dùng cung cấp, NLU A/C dành cho Nam, B/D dành cho Nữ, E và Cỏ May dành cho cả hai. Dropdown và bước xác nhận chặn lựa chọn sai giới; Cỏ May vẫn được tra như địa danh riêng. Sinh viên có cùng tọa độ đã xác nhận được hiển thị chung một marker có số lượng; popup chứa đầy đủ danh sách, có cuộn khi đông người. Mỗi sinh viên vẫn giữ ID riêng để chia nhóm. [Mẫu nhiều người cùng địa chỉ và bằng chứng kiểm thử](docs/reports/shared-locations.md).

## Phụ lục E. Kế hoạch kiểm thử và đo lường

### E.1. Unit test bắt buộc

- **Excel:** đúng tên cột dù đổi thứ tự; thiếu cột; dòng trống; giới tính không hợp lệ; tên/địa chỉ trùng nhưng là hai sinh viên khác nhau; thêm cột `Dấu thời gian`.
- **Geoapify:** mock response thành công; không kết quả; kết quả cấp thành phố; nhiều ứng viên; timeout; rate limit; lỗi khóa; sửa lại địa chỉ phải xóa trạng thái xác nhận cũ.
- **Grouping:** N=30 M=3 F=2 và 18 Nam/12 Nữ => 6 nhóm 3+2; N=34 M+F=5 => 6 nhóm với quy mô 5–6; giới tính mất cân bằng; một giới ít hơn `k`; chỉ có một giới; N nhỏ hơn quy mô nhóm; N=0; M=F=0.
- **Bất biến:** không có sinh viên mất, lặp hoặc được gán hai nhóm; `k` và size đúng; dữ liệu đầu ra ổn định khi cùng seed.
- **Export:** tổng số dòng thành viên đúng N; tên nhóm khớp API; đúng 2 sheet; không có tọa độ thô mặc định.

### E.2. Integration và giao diện

1. Upload Excel mẫu.
2. Kiểm thử Geoapify với một số địa chỉ tại TP.HCM (bao gồm cách ghi cũ/mới).
3. Đối chiếu vị trí đại diện với bản đồ và địa danh thực tế trước khi chấp nhận.
4. Chủ động tạo một địa chỉ lỗi; xác nhận sửa trực tiếp trên web và retry thành công.
5. Chia 30 người thành 6 nhóm; xem màu nhóm, popup, bảng thống kê.
6. Xuất Excel và so với danh sách trên web.
7. Thử làm mới trang: không có lịch sử lưu trên máy chủ.

### E.3. Chỉ số dùng trong báo cáo

- Tỷ lệ geocoding thành công; số địa chỉ cần sửa; số vị trí xác minh đạt độ chi tiết chấp nhận được.
- Số nhóm, quy mô, Nam/Nữ của từng nhóm; số sinh viên bị thiếu/lặp (**phải bằng 0**).
- Khoảng cách trung bình và lớn nhất trong nhóm (Haversine).
- So sánh khoảng cách với baseline chia ngẫu nhiên có kiểm soát cùng quy mô/tỷ lệ khi khả thi.
- Nêu rõ sai số vị trí đại diện cấp đường và giới hạn đo đường chim bay; **không suy diễn chất lượng nếu chưa có kết quả chạy thật**.

## Phụ lục F. Quy ước và trình tự triển khai cho Codex

**Không triển khai tất cả trong một lần.** Codex cần làm tuần tự, kiểm tra sau mỗi giai đoạn và báo cáo những file đã tạo, cách chạy, kết quả test và các lỗi chưa xử lý.

1. **Khởi tạo skeleton:** cấu trúc thư mục, FastAPI health check, frontend Leaflet tối thiểu, `requirements.txt`, `.gitignore`, `.env.example`. Kiểm tra khởi chạy backend/frontend.
2. **Module Excel:** nhập, validate và trả lỗi từng dòng; unit test với mẫu.
3. **Module geocoding:** gọi Geoapify từ backend, trả confidence/candidate/status, cơ chế sửa và retry trên frontend; test với mock trước, API thật sau.
4. **Module grouping:** công thức `k`, K-Means riêng từng giới, cân bằng, Hungarian, fallback và các bất biến; unit test đầy đủ trước khi tích hợp.
5. **Kết quả WebGIS:** hiển thị marker, màu nhóm, bảng sinh viên, thống kê, bộ lọc.
6. **Xuất Excel:** tạo hai sheet, test đối chiếu với kết quả API.
7. **Tích hợp + báo cáo:** test end-to-end, đo đánh giá baseline, tối ưu UX, hỗ trợ triển khai nếu còn thời gian.

**Nguyên tắc Codex phải tuân thủ:**

- Luôn đọc `README.md` trước khi sửa code; thay đổi kiến trúc lớn phải được người dùng duyệt.
- Không tự phát minh tính năng như đăng nhập, Supabase, routing hoặc thuật toán khác làm thay đổi yêu cầu đã chốt.
- Không tự tạo hoặc giả mạo kết quả geocoding, kết quả thuật toán hay chỉ số đánh giá.
- Viết test cho công thức `k` và bảo đảm 100% thành viên được gán nhóm.
- Không cho geocode chưa xác nhận đi vào thuật toán.
- Không hardcode API key; mọi hướng dẫn về secrets chỉ dùng placeholder.
- Giữ giao diện bằng **tiếng Việt**, thông báo lỗi dễ hiểu cho giảng viên.
- Tránh commit file cấu hình chứa secret hoặc dữ liệu thật.
- Từng bước phải có hướng dẫn chạy trên **Windows PowerShell**.
