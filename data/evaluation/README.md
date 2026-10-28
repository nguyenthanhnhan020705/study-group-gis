# Dữ liệu đánh giá Phase 7

`confirmed-sample-30.json` là snapshot 30 sinh viên **giả lập** từ workbook mẫu, lấy qua luồng tự đối chiếu Geoapify thật ngày 25/10/2026. Đây là dữ liệu đánh giá cố định, không phải dữ liệu mặc định để tự gán vị trí cho file upload mới.

`provenance-sample-30.json` lưu chín địa danh công cộng, tọa độ trả về, nguồn OSM/nhãn địa chỉ và thời điểm kiểm tra. Đối chiếu danh tính địa danh với registry của dự án; không phải khảo sát thực địa hoặc xác minh nơi ở của sinh viên thật. Quy tắc giới tính các cư xá do chủ dự án cung cấp.

`report-sample-30.json` lưu kết quả thuật toán và **đủ 30 seed ngẫu nhiên 0–29**, cùng môi trường thư viện và SHA256 của chính byte đầu vào. Tọa độ đã xác nhận trong snapshot không được dùng làm bằng chứng rằng API luôn trả đúng.

Chạy lại từ thư mục gốc, không cần mạng/API key:

```powershell
./.venv/Scripts/python.exe -B scripts/evaluate_grouping.py --input data/evaluation/confirmed-sample-30.json --output .local-tests/phase-7/evaluation-repeat.json
```

CLI nhận đúng schema `GenerateGroupsRequest`, từ chối chưa xác nhận/trùng ID/tọa độ sai/ngoài vùng; bản thân cờ `verified` không chứng minh nguồn tọa độ. Người chạy phải kiểm tra nguồn trước khi đưa snapshot mới vào báo cáo. Chỉ đưa dữ liệu giả lập vào thư mục này; dữ liệu thực giữ trong `data/private/` đã bị Git bỏ qua.
