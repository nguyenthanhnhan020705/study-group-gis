# Phase 4 — Thuật toán chia nhóm và thống kê

Thực hiện ngày 23/10/2026 theo [kế hoạch chi tiết](../superpowers/plans/2026-10-23-phase-4-grouping.md) và mục 7/Phụ lục A của [BRD](../../README.md). Phạm vi là backend/API; giao diện cấu hình, màu nhóm, bảng và bộ lọc thuộc Phase 5.

## Đầu ra

- `POST /api/groups/generate` nhận danh sách đã xác nhận, `target_male`, `target_female`; tự tính `k=max(1,N//(M+F))`.
- Chiếu WGS84 sang UTM 48N, KMeans riêng từng giới (seed 42, n_init=10), gán vào quota bằng bài toán assignment theo khoảng cách mét; ghép cụm bằng ma trận Haversine và `linear_sum_assignment`.
- Quota mỗi giới chênh tối đa 1. Ghép hai giới chỉ cho các cặp có tổng size thuộc floor/ceil(N/k), tránh ghép hai cụm cùng dư gây lệch 2 người.
- Thiếu một giới: cụm từ giới đủ số lượng, phân bổ giới ít vào các slot còn lại; k=N cho nhóm singleton. Tọa độ trùng được lặp tâm để giữ đủ k quota, không giảm k hoặc bỏ người.
- Kiểm tra sau phân nhóm: đủ N ID đúng một lần, đúng k nhóm không rỗng, size chênh tối đa 1; đánh số nhóm ổn định theo ID. Cảnh báo `minority_fallback` và `target_mismatch` giải thích trường hợp không đạt mục tiêu Nam/Nữ.
- Haversine dùng bán kính cầu trung bình 6.371.008,8 m. Nhóm singleton có 0 cặp, mean/max=0. Trung bình toàn bộ có trọng số theo số cặp nội nhóm, không lấy trung bình đơn giản của các mean nhóm.

## Kiểm thử đã chạy

| Kiểm tra | Bằng chứng |
|---|---|
| TDD metrics | 4 test RED thiếu module → GREEN 4 passed |
| TDD grouping | 22 test RED thiếu schema/service → GREEN, gồm k, số dư, thiếu giới, trùng tọa độ, tính tái lập và cụm tách biệt |
| TDD API | 31 test RED route chưa có → GREEN; chặn đầu vào chưa xác nhận, boolean/string/số thực M/F, NaN/Infinity, trùng ID và ngoài vùng |
| Toàn bộ suite | `python -m pytest -q`: 116 passed, gồm 59 test hồi quy Phase 1–3 |
| Dependency | `python -m pip check`: No broken requirements found |
| Hồi quy trình duyệt | `scripts/check_phase3_browser.py`: chọn/xác nhận, sửa địa chỉ, response cũ, upload mới và mobile đều đạt |
| HTTP thật | `scripts/check_phase4_api.py` tự tạo/dừng API server 8014; kết quả dưới đây |

## Kết quả HTTP thật

| Dữ liệu | Mục tiêu | Kết quả | Khoảng cách trung bình cặp nội nhóm | Lớn nhất |
|---|---|---|---:|---:|
| 12 người mẫu Phase 3, 6 Nam/6 Nữ, dùng 12 điểm công cộng đã xác nhận | 3 Nam + 2 Nữ | k=2; mỗi nhóm 6 người, 3 Nam/3 Nữ; có cảnh báo lệch mục tiêu | 1.440,96 m (30 cặp) | 3.335,04 m |
| 30 người tổng hợp, 18 Nam/12 Nữ, tái sử dụng các điểm công cộng của demo 12 | 3 Nam + 2 Nữ | k=6; cả 6 nhóm đúng 5 người, 3 Nam/2 Nữ; không cảnh báo | 732,68 m (60 cặp) | 2.014,64 m |

Cả hai ca giữ nguyên tập ID, không lặp/thiếu người. API trả 422 khi một người trong mẫu mất xác nhận vị trí. Các request, response và summary nằm trong `.local-tests/phase-4/` (Git ignore).

Sau lần dọn dự án, `check_phase4_api.py` dùng fixture tổng hợp tái lập từ `tests/grouping_fixtures.py`, không còn phụ thuộc JSON demo12 đã xóa. Bảng trên giữ số đo lịch sử của lần chạy với điểm công cộng; số đo fixture mới không được diễn giải như geocoding thật. Artifacts thử được tạo lại khi chạy và có thể dọn an toàn.

Mẫu 30 là fixture tổng hợp dùng tọa độ công cộng đã có, không phải 30 địa chỉ được geocode mới. Các số đo trên mô tả kết quả chạy; chưa so baseline ngẫu nhiên và không chứng minh tối ưu toàn cục hoặc quãng đường giao thông tốt hơn. Đánh giá baseline thuộc Phase 7.

## Giới hạn và vận hành

- Schema chỉ nhận trường sinh viên được công bố, không nhận candidates/selectedCandidate/trạng thái UI khác. Phase 5 cần chiếu payload đúng schema.
- Tối đa 1.000 sinh viên, đồng thời tuân thủ `MAX_STUDENT_ROWS` nếu cấu hình nhỏ hơn; JSON tối đa 8 MiB. Vị trí phải nằm trong `GEOCODING_BOUNDS` hiện hành.
- Một job mỗi tiến trình; route sync dùng worker thread, BLAS/OpenMP giới hạn 1 thread trong job. Cấu hình local dùng một Uvicorn worker. Nhiều tiến trình cần quy hoạch giới hạn dùng chung khi triển khai.
- Backend kiểm tra trạng thái xác nhận trong payload. Ứng dụng hiện không có tài khoản/chữ ký dữ liệu nên không coi đây là bằng chứng chống giả mạo thao tác xác nhận.
- Không lưu lịch sử, không gọi Geoapify trong thuật toán, không thay đổi dữ liệu đầu vào. Dependency chính được pin trong `backend/requirements.txt`.
- Chưa commit/push; giữ các thay đổi Phase 1–3 trước đó trong workspace hiện hành.

## Review và nghiệm thu

Reviewer độc lập không tìm thấy lỗi cần sửa trong phạm vi Phase 4. Reviewer chạy riêng 26 test grouping/metrics và 350 ca ngẫu nhiên tái lập với N=1..90, giới tính lệch, size mục tiêu 1..14, tọa độ trùng/một phần trùng và kiểm tra đảo thứ tự; tất cả đạt. Không sửa file hoặc đọc khóa.

Phase 4 hoàn thành; AC-05 phía backend và AC-06..AC-09 đạt. Quyết định quota có ràng buộc size, trung bình theo số cặp và chạy trong workspace hiện có được ghi rõ trong kế hoạch/ledger. Chưa có mục Minor bị hoãn từ review. Giao diện Phase 5, xuất Excel và đánh giá baseline vẫn chưa triển khai.
