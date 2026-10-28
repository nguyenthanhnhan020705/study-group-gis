# Sửa truy cập local và kiểm tra hoạt động Phase 1–6

Ngày24/10/2026. Phạm vi cuối theo người dùng: **chỉ sửa lỗi, chưa triển khai Phase7**. Các nội dung dưới đây kiểm tra hệ thống hiện có; không phải báo cáo nghiệm thu Phase7.

## Nguyên nhân và sửa đổi

Kiểm tra ngoài sandbox xác nhận cả8001/5500 không có listener. Vì vậy frontend/backend không truy cập được do các dịch vụ không chạy. Log demo trước đó chỉ có startup thành công, không có traceback đủ để kết luận vì sao tiến trình cũ dừng. Không quy lỗi cho mạng Geoapify hoặc thuật toán khi chưa có bằng chứng.

Đã thêm `start-webgis.cmd` và `scripts/run_local.py` để chạy chung hai server từ đúng thư mục và Python `.venv`. Runner kiểm tra cổng, backend health, các route WebGIS, CORS của frontend, nội dung HTML/JavaScript của đúng dự án. Chỉ báo READY khi đủ điều kiện. Cổng bị chiếm báo rõ và không kill tiến trình lạ; lỗi startup/child thoát dọn các child thuộc runner, tránh duy trì một nửa hệ thống. Log giữ tại `.local-tests/local-server/`.

Lần chạy đầu hết ngưỡng40giây khi nhiều suite/browser đang chạy song song; chạy riêng sau đó cả hai endpoint trả200. Nâng thời gian chờ startup lên90giây để cho phép máy khởi động chậm, vẫn có deadline và cleanup. Không thay timeout/provider hoặc nghiệp vụ geocoding/grouping/export.

## Bằng chứng kiểm tra

- RED:9test launcher được bổ sung dần; ba test đầu báo chưa có module. GREEN:9test kiểm tra cổng lạ, child lỗi, Popen lỗi, startup timeout, CORS, route backend, HTML và JavaScript đúng dự án. Review độc lập chạy lại9test đạt, không Critical/Important.
- Toàn bộ suite: **222 passed in77.16s**, gồm213test sẵn có và9test launcher. Sau điều chỉnh thời gian chờ/hiển thị log, chạy lại riêng9test launcher đạt.
- Browser Phase2/3/5/6, shared locations và automatic100students đều đạt. Bao gồm upload thật, sửa địa chỉ/giữ input tiếng Việt, chọn thủ công ngoại lệ, stale response, filter, popup trùng điểm, metrics và download XLSX. Ca100dòng dùng provider fixture:98auto/2ngoại lệ/2lookup; không coi là đo accuracy provider.
- Dừng runner thật bằng **Ctrl+C** trong Windows PTY: in `Stopped both local services`, check báo không truy cập. Chạy lại launcher kiểm tra cả hai cổng trống và trở lại READY; CORS/frontend assets đúng. PowerShell PTY trả mã ngắt1 khi gửi Ctrl+C, không coi đó là crash nghiệp vụ.
- Kiểm tra mạng thật bằng headless Edge trên backend8001/frontend5500 hiện hành, upload mẫu30sinh viên giả lập, không nạp tọa độ lưu sẵn hoặc route mock: `students=30,automatic=30,verified=30,unresolved=[]`. Chia6nhóm và export qua API thật; openpyxl xác nhận31/7dòng ở hai sheet. Ảnh nền thật tải đủ các tile hiện có (`complete` và `naturalWidth>0`).
- Cửa sổ Edge điều khiển CDP9223 không mở được, nên chuyển kiểm tra live sang headless Edge; đây là vấn đề công cụ demo, không phải lỗi truy cập frontend/backend. Không dùng ảnh giả để báo nền hoạt động.

Lệnh:

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B -m pytest tests/test_local_runner.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -B scripts/run_local.py --check
.\.venv\Scripts\python.exe -B scripts/check_automatic_location_browser.py
.\.venv\Scripts\python.exe -B scripts/check_phase6_browser.py
.\.venv\Scripts\python.exe -B scripts/check_phase2_browser.py
.\.venv\Scripts\python.exe -B scripts/check_phase3_browser.py
.\.venv\Scripts\python.exe -B scripts/check_phase5_browser.py --map
.\.venv\Scripts\python.exe -B scripts/check_shared_locations_browser.py
```

Bằng chứng local tại `.local-tests/readiness/`: `full-suite.log`, `launcher-red.log`, `launcher-green.log`, `browser-*.log`, `runner-final.log`, `live-final.log`, `live-result.json`, `live-map.png`, `live-automatic.png`, `live-automatic-groups.xlsx`. Script live tạm và workbook chỉ chứa sinh viên giả lập. Không ghi key hoặc danh sách sinh viên thật vào report.

## Cách dùng và giới hạn

Mở **http://127.0.0.1:5500**; API health **http://127.0.0.1:8001/api/health**. Khi cần chạy lại sau tắt máy/đóng runner, mở **start-webgis.cmd** rồi đợi READY. Giữ runner hoạt động; dùng Ctrl+C để dừng. Không chạy song song hai lệnh server thủ công và runner. `--check` chỉ kiểm tra local, không gọi Geoapify. Cấu hình `CORS_ORIGINS` phải cho phép `http://127.0.0.1:5500`.

Các kiểm tra hiện tại đạt, đủ tiếp tục dùng local. Chưa có bằng chứng uptime dài hạn, hiệu năng1000người hoặc mọi địa chỉ thực tế đều nhận đúng; mạng, key/quota và dữ liệu provider vẫn là phụ thuộc ngoài. Refresh xóa dữ liệu phiên theo thiết kế. Không cài Windows service/autostart, không commit/push/deploy. **Phase7 giữ chưa triển khai**; tài liệu chuẩn bị Phase7 không tương đương thực thi hoặc nghiệm thu.
