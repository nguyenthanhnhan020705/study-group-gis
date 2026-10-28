# Phase 5 — Giao diện kết quả WebGIS

Thực hiện ngày 23/10/2026 theo [kế hoạch chi tiết](../superpowers/plans/2026-10-23-phase-5-webgis-results.md), mục 8/AC-10/AC-14 của [BRD](../../README.md). Phạm vi là nối giao diện với API Phase 4; không sửa thuật toán hoặc geocoding.

## Đầu ra

- Bước 03 có hai ô Nam/Nữ, mặc định 3/2; hiển thị `k=max(1,floor(N/(M+F)))`. Chặn số trống, âm, thập phân, không hữu hạn, số vượt miền nguyên an toàn hoặc tổng bằng 0. Chỉ bật chia nhóm khi mọi vị trí đã xác nhận.
- Module `frontend/js/grouping.js` gửi đúng các trường `VerifiedStudent`, chuẩn hóa khoảng trắng đầu/cuối theo schema backend, không gửi ứng viên hoặc trạng thái UI.
- Khi request đang chạy có thông báo và chặn gửi lặp; lỗi HTTP/mạng/không phải JSON/kết quả thiếu hoặc sai ID không được báo thành công. Retry thay thế kết quả cũ.
- Kết quả có bộ lọc chung cho bản đồ, bảng thành viên và bảng thống kê. Tổng sinh viên, số nhóm và khoảng cách toàn bộ giữ nguyên khi lọc; số đang xem được ghi riêng. Có cảnh báo lệch mục tiêu Nam/Nữ và thống kê trung bình/lớn nhất theo mét.
- Marker dùng màu kèm số nhóm. Tọa độ trùng vẫn một marker, nhãn liệt kê nhóm và số người; popup giữ đầy đủ từng người, ID, giới tính, nhóm và địa chỉ đại diện. Lọc riêng nhóm chỉ giữ người tương ứng. Không dịch tọa độ.
- Khi có kết quả hoặc đổi bộ lọc, khung bản đồ tự bao các điểm đang xem, kể cả điểm gần biên vùng nghiên cứu. Preview xác minh vẫn đưa bản đồ đến ứng viên đã chọn.
- Đổi địa chỉ, ứng viên/xác nhận, file hoặc M/F xóa kết quả/lọc và hủy request. Revision cùng định danh controller loại response lỗi thời, kể cả fetch không hủy kịp hoặc M/F đổi lại giá trị cũ.
- Xuất Excel vẫn disabled và ghi rõ Phase 6; không có endpoint/download giả. AC-14 phần tải file chưa được nghiệm thu.
- Dữ liệu chỉ ở bộ nhớ phiên; refresh xóa kết quả. Giữ luồng sửa địa chỉ, quy tắc KTX và bộ gom điểm trước đây.

## Kiểm chứng

| Kiểm tra | Kết quả |
|---|---|
| Baseline trước thay đổi | Toàn bộ pytest: 151 passed |
| TDD state | RED thiếu target/revision helpers → GREEN; schema payload, ID, response bất nhất, bộ lọc và stale response |
| TDD UI | RED thiếu giao diện kết quả → GREEN; 30 người tổng hợp qua API thật → 6 nhóm, mỗi nhóm 3 Nam/2 Nữ |
| Chuẩn hóa địa chỉ sửa | RED khi có khoảng trắng đầu/cuối → GREEN sau khi chiếu chuỗi theo schema backend |
| Khung nhìn kết quả | RED với hai điểm ở rìa vùng nghiên cứu bị cắt khỏi viewport → GREEN sau khi tự fit bounds các điểm đang xem |
| Browser mặc định | Chặn CDN có chủ đích: cả sáu bộ lọc, metric tổng không đổi, XSS an toàn, mobile, lỗi 500/429/non-JSON, warning, singleton và refresh đạt |
| Browser Leaflet | Thư viện Leaflet 1.9.4 thật: kiểm tra marker/màu/nhãn của cả sáu nhóm, một điểm 30 người thuộc sáu nhóm, popup và lọc riêng nhóm đạt |
| Hồi quy Phase 2 | Upload multipart thật 30/18/12; lỗi theo dòng, XSS, mobile, lỗi mạng và response cũ đạt |
| Hồi quy Phase 3 | Chọn/xác nhận, sửa địa chỉ giữ input/IME, response cũ, import mới và mobile đạt |
| Hồi quy shared-locations | Tọa độ chính xác, popup đủ người, 100 người cuộn, preview không đếm lặp và guard giới tính KTX đạt |
| Toàn bộ backend sau thay đổi | 151 passed; kiểm tra UI bổ sung nằm trong script browser riêng |
| Review độc lập | Không còn finding Critical/Important/Minor sau khi đối chiếu sửa chuẩn hóa chuỗi; đã review bổ sung fit bounds và nhãn marker. Reviewer không tự chạy lại suite |

Fixture trong `tests/grouping_fixtures.py` là tọa độ tổng hợp đã gắn trạng thái xác nhận cho mục đích kiểm tra UI/API. Không gọi Geoapify và không dùng những điểm này làm bằng chứng độ chính xác địa chỉ hoặc đánh giá baseline.

Ảnh và log tại `.local-tests/phase-5/` (Git ignore): `desktop-results.png`, `mobile-results.png`, `map-filtered.png`, `browser-offline.log`, `browser-map.log`, các log hồi quy và `tile-status.json`.

## Cách dùng và tái lập trên PowerShell

Khởi động backend/frontend như README (8001/5500), tải lại trang để nhận JavaScript mới. Nhập Excel → xác nhận vị trí → đặt Nam/Nữ ở bước 03 → Chia nhóm → lọc và đối chiếu hai bảng/bản đồ.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B scripts/check_phase5_browser.py
.\.venv\Scripts\python.exe -B scripts/check_phase5_browser.py --map
.\.venv\Scripts\python.exe -B scripts/check_phase2_browser.py
.\.venv\Scripts\python.exe -B scripts/check_phase3_browser.py
.\.venv\Scripts\python.exe -B scripts/check_shared_locations_browser.py
```

Script Phase 5 tự tạo/dừng backend 8015/frontend 5516, không ảnh hưởng server demo 8001/5500. Cần Playwright và Edge theo `backend/requirements-browser.txt`. `--state` chỉ chạy các ca hợp đồng/trạng thái. `--map` cần CDN ở lần đầu; byte Leaflet thật được lưu trong `.local-tests/phase-5/leaflet-1.9.4.js/.css` để tái lập, trình duyệt vẫn kiểm tra SRI. Không thay Leaflet bằng mock.

## Giới hạn và nghiệm thu

- Lượt sandbox đầu không tải được CDN. Lượt có quyền mạng đã tải và chạy Leaflet thật; các lượt tiếp theo dùng byte thư viện đã cache.
- Ảnh nền `tile.openstreetmap.org` vẫn lỗi kết nối trong lượt kiểm tra, kể cả phép thử ngoài sandbox. Ứng dụng hiển thị thông báo lỗi tile; không dùng ảnh giả và không tuyên bố nền bản đồ tải thành công. Marker, màu, nhãn, popup và bộ lọc được kiểm tra trên Leaflet thật độc lập với tile.
- Màu được dùng lại khi quá tám nhóm; mọi nhóm luôn có số nhóm ở nhãn/popup/chú giải. Điểm có nhiều nhóm dùng màu chung và nhãn liệt kê; danh sách dài xem trong popup/bộ lọc.
- Chưa kiểm tra lại Geoapify thật trong Phase 5 vì không thay boundary đó. Không đo tốc độ UI với 1.000 sinh viên hoặc tuyên bố tối ưu đường đi.
- AC-10 và phần vô hiệu hóa kết quả của AC-14 đạt. AC-11 và phần xuất AC-14 thuộc Phase 6; baseline và nghiệm thu tổng thể thuộc Phase 7.
- Giữ workspace/nhánh hiện tại với thay đổi các phase trước chưa commit; không commit/merge/push.
