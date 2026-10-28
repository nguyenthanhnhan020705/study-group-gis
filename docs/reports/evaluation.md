# Đánh giá thuật toán — Phase 7, 25/10/2026

Trên bộ mẫu giả lập 30 sinh viên, thuật toán có khoảng cách trung bình nội nhóm **451,107 m**, so với trung bình **1.752,536 m** của 30 cách chia ngẫu nhiên cùng ràng buộc, giảm **74,260%**. Thuật toán tốt hơn cả 30 seed theo chỉ số trung bình này. Đây là kết quả trên một bộ mẫu; không chứng minh luôn tốt hơn cho mọi danh sách hoặc tối ưu toàn cục.

## Dữ liệu và khả năng tái lập

- Đầu vào: [snapshot 30 người](../../data/evaluation/confirmed-sample-30.json), 18 Nam/12 Nữ, mục tiêu 3+2; sáu nhóm đều năm người, đúng 3 Nam/2 Nữ.
- Tên sinh viên giả lập từ workbook mẫu. Chín điểm đại diện công cộng lấy qua Geoapify thật ngày 25/10/2026, không tự chế tọa độ. [Nguồn và điểm đã chọn](../../data/evaluation/provenance-sample-30.json).
- SHA256: `4961022ebf7ca6b77e6f997b5259e5f571149836e864fe983b6d785a21e3269c`.
- Thuật toán seed 42, baseline Python `random.Random` seeds 0–29; mỗi seed được công bố trong [report JSON](../../data/evaluation/report-sample-30.json).
- Môi trường lần chạy: Python 3.13.3, NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.9.1, pyproj 3.8.0. Cùng dữ liệu và môi trường tái lập kết quả; đổi phiên bản thư viện có thể thay phân hoạch.

```powershell
./.venv/Scripts/python.exe -B -m pytest tests/test_evaluation.py -q -p no:cacheprovider
./.venv/Scripts/python.exe -B scripts/evaluate_grouping.py --input data/evaluation/confirmed-sample-30.json --output .local-tests/phase-7/evaluation-repeat.json
```

CLI chỉ tính offline, không gọi geocoding, không ghi tên/ID/địa chỉ vào report. Giữ nguyên snapshot nguồn; đường dẫn input và output phải khác nhau. 15 test đánh giá đạt, bao gồm chưa xác nhận, ID trùng, NaN/Infinity, ngoài vùng, dư người, thiếu một giới, cùng seed, singleton và tọa độ trùng.

## Phương pháp

Thuật toán hiện hành dùng KMeans riêng theo giới, cân bằng sức chứa và ghép Hungarian. Baseline xáo trộn riêng Nam/Nữ rồi phân vào **đúng vector quy mô và quota Nam/Nữ của từng nhóm thuật toán**, giữ cùng tập ID và mỗi người đúng một nhóm. Không đổi quota để tạo lợi thế cho phương pháp nào.

Khoảng cách Haversine tính bằng mét, bán kính Trái Đất 6.371.008,8 m. Mỗi nhóm năm người có 10 cặp, toàn bộ sáu nhóm có 60 cặp. Trung bình tổng thể lấy tổng khoảng cách của tất cả cặp nội nhóm chia tổng số cặp; không lấy trung bình không trọng số giữa các nhóm khác quy mô. Max là khoảng cách lớn nhất giữa hai thành viên cùng nhóm. Singleton bằng 0.

Độ lệch giới là tổng `abs(Nam thực tế − Nam mục tiêu) + abs(Nữ thực tế − Nữ mục tiêu)` qua các nhóm; độ lệch quy mô là `max(size) − min(size)`. Báo cáo kiểm tra thiếu/trùng/ID lạ. Tỷ lệ thắng/hòa/thua dùng mean, ngưỡng hòa số học 1e-9 m; không phải ngưỡng ý nghĩa thực tiễn. Baseline mean bằng 0 thì phần trăm giảm là null, không chia cho 0.

## Kết quả

| Chỉ số (m) | Thuật toán | Baseline mean | Độ lệch chuẩn quần thể | Median | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| Trung bình cặp nội nhóm | 451,107 | 1.752,536 | 165,270 | 1.797,912 | 1.285,180 | 2.052,588 |
| Cặp xa nhất nội nhóm | 3.226,656 | 4.119,986 | 31,875 | 4.134,241 | 4.048,711 | 4.134,241 |

Cả thuật toán và từng baseline đều thiếu 0, trùng 0, ID lạ 0, lệch quy mô 0 và lệch giới 0. Mean giảm 74,260% so với baseline mean; thắng 30/30, hòa 0/30, thua 0/30. Kết quả JSON giữ đủ các lần chạy, không chọn bỏ seed bất lợi.

## Giới hạn

30 lần xáo trộn là 30 phân hoạch của **cùng một bộ dữ liệu**, không phải 30 lớp học độc lập. Mẫu có nhiều sinh viên trùng chín điểm, có thể thuận lợi cho gom nhóm địa lý. Chưa đánh giá trên tập lớp học thực tế đa dạng, chưa đo độ chính xác địa chỉ bằng ground truth hay khảo sát người dùng. Haversine là đường chim bay giữa điểm đại diện, không phải quãng đường/chi phí/thời gian di chuyển. Không có phép kiểm định suy rộng hay tuyên bố tối ưu toàn cục.
