# Tự đối chiếu vị trí sau nhập Excel

Cập nhật ngày 24/10/2026 theo yêu cầu giảm thao tác chọn/xác nhận từng sinh viên. Thay đổi này bổ sung vào Phase 1–6 đã hoàn thành; Phase 7 vẫn chưa triển khai. [Kế hoạch](../superpowers/plans/2026-10-24-automatic-location.md).

## Luồng sử dụng

1. Chọn Excel, nhấn **Đọc danh sách**. Nếu dữ liệu nhập hợp lệ, hệ thống tự tra cứu, đối chiếu và cập nhật marker trên bản đồ.
2. Địa chỉ xác định rõ ràng được tự xác nhận, không cần chọn ứng viên hay bấm xác nhận cho mỗi sinh viên. Theo dõi số đã xác định, số tự động và số còn cần xử lý.
3. Mặc định chỉ hiện **Cần xử lý**. Sửa/bổ sung các địa chỉ mơ hồ rồi kiểm tra lại; có thể chọn **Tất cả sinh viên** để xem/sửa điểm tự động. Khi đủ vị trí, chia nhóm và xuất Excel như trước.

Giữ ba cột bắt buộc. Nếu nhiều sinh viên ở các cư xá khác nhau trong KTX Nông Lâm, ghi cư xá A–E ngay trong địa chỉ hoặc thêm cột **Cư xá/Khu vực**. Cột **Điểm cần xác nhận** của file mẫu hiện tại cũng được đọc. Tên tòa được ghép vào chuỗi tìm kiếm `dia_chi_da_sua`, địa chỉ gốc giữ nguyên. Công thức/lỗi Excel/địa điểm bổ sung quá dài bị báo theo dòng. File mẫu và script tạo mẫu đã cập nhật hướng dẫn.

## Điều kiện tự động

- Cư xá A–E: địa chỉ phải xác định được campus Nông Lâm và một tòa cụ thể; Geoapify Places phải trả đúng danh tính OSM, tên, loại, quốc gia và vùng tọa độ đã đăng ký. Không suy ra cư xá từ họ tên hoặc giới tính. Địa chỉ “KTX Nông Lâm” chung vẫn cần bổ sung, kể cả provider chỉ trả một tòa.
- Cỏ May và KTX khu B: đối chiếu danh tính đã đăng ký, không dùng số confidence giả.
- Hai đường đã có nguồn đối chiếu trong dự án (Võ Văn Ngân, Kha Vạn Cân): yêu cầu đúng địa chỉ đăng ký, tên đường, phường, `VN-SG`, loại street, quốc gia, vùng hẹp và confidence tối thiểu cấu hình. Nhận đúng phường Thủ Đức; không tự nhận đoạn đường cùng tên ở phường khác.
- Địa chỉ thường chưa đăng ký: yêu cầu confidence ít nhất0,95 cùng tên và các thành phần địa chỉ khớp, đủ chi tiết, trong vùng nghiên cứu. Confidence cao riêng lẻ không đủ; KTX chưa có danh tính đối chiếu không được auto chỉ từ confidence.
- Frontend chỉ nhận khi có duy nhất một ứng viên `auto_selectable` hợp lệ, tọa độ hữu hạn và phù hợp giới tính nếu có quy định. Các ứng viên mơ hồ vẫn cần xử lý. Có thể sửa lại mọi điểm tự động.

Cache chỉ trong phiên, theo chuỗi địa chỉ đã chuẩn hóa khoảng trắng/hoa thường; vẫn giữ riêng ID và kiểm tra giới tính mỗi sinh viên khi dùng chung kết quả. Lỗi dịch vụ/quota/network/timeout tạm dừng hàng đợi và cho thử lại; không lặp hàng trăm request khi provider lỗi. Không tìm thấy địa chỉ là `needs_review` nên không cản trở các địa chỉ tiếp theo. Sửa địa chỉ/import mới bỏ response cũ, xóa xác nhận và kết quả nhóm/export. Bản đồ cập nhật marker trong quá trình tra cứu, chỉ tự fit toàn bộ khi hàng đợi kết thúc/tạm dừng để hạn chế tải tile lặp.

## Bằng chứng

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
# 213 passed in9.76s
.\.venv\Scripts\python.exe -B scripts/check_automatic_location_browser.py
# 5 PASS, actual import/grouping/export + synthetic provider boundary
```

- Kiểm thử100dòng qua API import thật:98người được tự xác nhận,2ngoại lệ (campus thiếu tòa và xung đột giới); chỉ2lần lookup, một marker Leaflet thật giữ đủ người chung điểm. Đây là dữ liệu thử/provider fixture, không phải đo accuracy Geoapify.
- Browser kiểm tra response trễ sau sửa địa chỉ, file mới hủy hàng đợi, dữ liệu tự động đi qua API grouping/export thật, workbook mở được với đúng hai sheet và đủ năm thành viên trong ca tích hợp. Provider outage của backend dừng danh sách100người sau một lần gọi, có thông báo/thử lại. Mobile390px không tràn trang.
- RED đã quan sát:14tests chưa có optional hint/auto flag/resolver; browser100dòng dừng0/100 trước khi thêm autostart; provider_error vẫn chạy tiếp trước sửa; registered street confidence0,81 chưa được nhận trước khi nối bộ đối chiếu riêng. GREEN cuối213tests.
- Hồi quy Phase2/3/5/6 và shared locations đều đạt. Test manual của Phase3 vẫn kiểm tra chọn/xác nhận khi ứng viên chưa đủ điều kiện auto; test Phase5/6 chuyển bộ lọc sang **Tất cả** trước khi sửa một dòng đã xác nhận.
- Review độc lập phát hiện queue chưa dừng với backend timeout/provider_error; đã thêm regression RED/GREEN và sửa. Review lại, kể cả quy tắc hai đường đăng ký, không còn Critical/Important.

**Kiểm tra dịch vụ thật:** mở Edge demo và upload file30sinh viên giả lập hiện tại; không nạp tọa độ lưu sẵn hoặc mock provider. Kết quả cuối `students=30,automatic=30,verified=30,unresolved=[]`. Tự nhận đủ9điểm đại diện, chia lại qua API thành6nhóm rồi tải Excel, openpyxl xác nhận31/7dòng ở hai sheet. Ảnh nền Geoapify thật tải đủ và được kiểm tra `naturalWidth>0` cho mọi tile đang hiển thị.

Lần kiểm tra đầu tự nhận23sinh viên KTX,7sinh viên hai đường còn cần xử lý do confidence0,81 thấp hơn ngưỡng chung. Sau khi dùng bộ đối chiếu đường/phường/vùng đã có nguồn độc lập, lần chạy lại đạt30/30; không hạ ngưỡng chung hoặc thay confidence provider. Lần chụp ảnh đầu bị timeout; lần cuối chụp thành công.

Demo giữ mở tại `http://127.0.0.1:5500/`. Bằng chứng local: `.local-tests/automatic-location/live-final.log`, `live-result.json`, `live-map.png`, `live-automatic.png`, `live-automatic-groups.xlsx`, `browser-final.log`, `full-suite-final.log` và `regression-*.log`. Tọa độ là điểm đại diện khu/tòa/đoạn đường; không phải vị trí phòng ở. Mẫu30/30 không chứng minh mọi file đều nhận đúng: dữ liệu thiếu cư xá hoặc địa danh trùng tên vẫn cần bổ sung. Phụ thuộc mạng, quota/key và dữ liệu provider. Không lưu lịch sử sinh viên, commit/push hoặc triển khai Phase7.
