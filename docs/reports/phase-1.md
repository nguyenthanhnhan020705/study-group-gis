# Phase 1 — Nhật ký triển khai và xác minh

Kế hoạch: [7 phase phát triển](../superpowers/plans/2026-10-21-webgis-development-phases.md), mục 5.

## Phạm vi và quyết định

- Chỉ triển khai Phase 1 theo yêu cầu; giữ nguyên thay đổi BRD/kế hoạch có sẵn.
- Làm trên nhánh `codex/phase-1-foundation` trong workspace hiện tại để giữ tài liệu chưa commit cùng mã nguồn. Không tạo worktree mới hoặc tự commit tài liệu của người dùng.
- Dùng Python 3.13 qua lệnh `python`: Python launcher `py` trên máy hiện trỏ mặc định tới Python 2.7.
- Health trả `{"status":"ok"}`; CORS mặc định chỉ cho `http://127.0.0.1:5500` và `http://localhost:5500`.
- `load_settings(env_file)` đọc `backend/.env` theo đường dẫn file, biến môi trường ưu tiên hơn file; khóa tùy chọn và không xuất hiện trong repr/response.
- Frontend dùng ES modules, base URL tại `api.js`, thời gian chờ health 5 giây, có nút thử lại và thông báo khi không tải được bản đồ.
- Leaflet 1.9.4 và nền OpenStreetMap; tâm bản đồ chỉ là vùng xem ban đầu quanh TP.HCM, không phải tọa độ sinh viên.
- Chỉ cài phụ thuộc cho phase hiện tại; chưa thêm pandas/K-Means/Geoapify request hay dữ liệu sinh viên.
- Kiểm thử backend trước triển khai, kiểm tra trình duyệt với server thật sau triển khai. Giới hạn upload/request thuộc phase 2–3, chưa áp dụng cho endpoint chưa tồn tại.

## Tiến độ

- [x] Test health, CORS, cấu hình: RED → GREEN.
- [x] Frontend Leaflet và trạng thái kết nối.
- [x] Chạy hai server, kiểm tra trình duyệt và responsive.
- [x] Rà soát độc lập, cập nhật README và kế hoạch.

## Tài liệu tham khảo

- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Leaflet Quick Start](https://leafletjs.com/examples/quick-start/)
- [python-dotenv](https://bbc2.github.io/python-dotenv/)

## Kết quả xác minh

Ngày kiểm tra: 2026-10-21. Python 3.13.3, FastAPI 0.156.8, Uvicorn 0.54.0, pytest 9.1.1; trình duyệt Microsoft Edge headless.

| Kiểm tra | Kết quả |
|---|---|
| RED trước triển khai | 11 test thất bại vì chưa có package `app`, đúng điều kiện ban đầu |
| `python -m pytest -q` trong `.venv` | 11 passed; health, không lộ khóa, CORS, dotenv/biến môi trường |
| `python -m pip check` | No broken requirements found |
| Backend thực tại `127.0.0.1:8001` | Health HTTP 200; frontend đọc được qua CORS |
| Trình duyệt desktop | Leaflet và tile OpenStreetMap thật tải được, có attribution, không lỗi JavaScript |
| Mất kết nối → thử lại | Offline khi request lỗi, trở lại online khi API hoạt động |
| Health trả payload không hợp lệ | Không hiển thị đã kết nối |
| Điện thoại 390px | Không tràn ngang; đã xem ảnh chụp toàn trang |
| CDN lỗi ngay / CDN treo | Có thông báo lỗi; health vẫn hoạt động; timeout tải thư viện 8 giây |
| Git ignore | Loại trừ `.env`, ảnh kiểm tra và dữ liệu riêng; giữ `.env.example` |

Lệnh kiểm tra trình duyệt: `.\.venv\Scripts\python.exe scripts/check_phase1_browser.py` khi hai server đang chạy. Cần cài `backend/requirements-browser.txt` và có Edge. Sáu nhóm kiểm tra PASS; ảnh desktop/mobile trong `.local-tests/phase-1/`.

## Rà soát độc lập và sửa lỗi

Một reviewer độc lập đã đọc backend/frontend/tests và chạy 11 test. Phát hiện quan trọng duy nhất: `DOMContentLoaded` chờ script Leaflet từ CDN nên health không khởi chạy nếu CDN treo. Reviewer tái hiện: sau 6,5 giây chưa gửi health và trạng thái vẫn `checking`.

Đã sửa bằng cách khởi chạy health trực tiếp từ ES module, tải CSS/JS Leaflet bất đồng bộ với timeout 8 giây. Regression trình duyệt giữ request CDN ở trạng thái pending: health chuyển online và bản đồ báo timeout đúng hạn. Script dọn các request giả lập trước khi đóng browser. Không còn phát hiện quan trọng hoặc minor chưa xử lý trong phạm vi review.

## Điều chỉnh và giới hạn

- Cổng 8000 đang bị chiếm nên dùng 8001; phải đổi đồng thời lệnh Uvicorn và `frontend/js/api.js` nếu đổi cổng. Chi phí thay đổi là cập nhật một URL và lệnh chạy.
- Giữ nhánh hiện tại `codex/phase-1-foundation` cùng các tài liệu có sẵn; chưa commit/merge/push. Không tạo worktree nhằm tránh tách các tài liệu chưa commit khỏi mã triển khai.
- Dùng `python` thay `py` để tránh Python 2.7; máy khác cần trỏ lệnh tới Python 3.10+.
- Starlette hiện tại cảnh báo TestClient với `httpx` cũ; dùng `httpx2` trong dependency kiểm thử. Đây không phải thay đổi thư viện Geoapify ở phase sau.
- Sandbox ban đầu trả `ERR_NETWORK_ACCESS_DENIED` cho CDN. Kiểm tra có quyền mạng đã tải bản đồ thật; không dùng tile giả để tuyên bố thành công.
- Chưa có geocoding, Excel, phân nhóm hoặc lưu dữ liệu. Không đánh dấu các tiêu chí AC của toàn MVP là đã đạt chỉ từ Phase 1.