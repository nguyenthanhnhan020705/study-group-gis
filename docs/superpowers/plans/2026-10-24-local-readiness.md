# Local availability and Phase 7 readiness Implementation Plan

> Use superpowers:executing-plans inline, RED/GREEN checks and final independent review.

**Goal:** Khôi phục truy cập local, cung cấp một lệnh chạy lại đáng tin cậy, xác minh Phase 1–6 và chuẩn bị Phase 7.
**Architecture:** Giữ backend8001/frontend5500 và toàn bộ nghiệp vụ. Python launcher chạy hai tiến trình từ đúng thư mục/venv, kiểm tra cổng/CORS/health/frontend, dừng các child của chính nó khi một child lỗi, ghi log local; CMD cho Windows chạy một lần. Không cài service hoặc startup Windows.
**Tech stack:** Python stdlib, FastAPI/Leaflet hiện có, pytest/Playwright.
**Spec:** Yêu cầu người dùng sửa không truy cập, kiểm tra ổn định, chuẩn bị Phase7. Chưa triển khai baseline hoặc nghiệm thu Phase7.

## Diagnosis / decisions

- Kiểm tra ngoài sandbox: cả8001/5500 không có listener; log demo cũ chỉ ghi startup thành công, không có traceback ứng dụng. Nguyên nhân truy cập thất bại được xác định là dịch vụ không chạy; chưa xác định lý do tiến trình trước đó đã dừng.
- Chỉ khởi động lại bằng lệnh rời sẽ tái diễn thao tác bỏ sót một server. Chọn một launcher có health check và dừng cả hai child khi một child thoát, không tự kill tiến trình lạ hay tự cấu hình khởi động máy.
- Giữ workspace chứa Phase1–6 chưa commit; không worktree/commit/push. Đây là sửa local có thể đảo ngược đã được yêu cầu, không hỏi lại phê duyệt thiết kế thường lệ.

## Tasks

- [x] RED/GREEN launcher: cổng bị chiếm không tác động dịch vụ lạ; startup lỗi/child thoát dọn child còn lại; readiness xác nhận frontend/backend/CORS; lệnh check không sửa dữ liệu.
- [x] Khởi động demo, xác minh HTTP/CORS/assets, chạy pytest và browser chức năng/hồi quy; chạy lại dữ liệu giả lập qua provider thật, map/grouping/export; ghi lỗi ngoài còn tồn tại nếu có.
- [x] Review độc lập, hướng dẫn khởi động/dừng/kiểm tra/log và báo cáo sửa lỗi. Tài liệu Phase7 đã chuẩn bị theo yêu cầu trước; sau nhắc lại chỉ sửa lỗi, không thực thi Phase7.

## Review focus

Cổng có ứng dụng khác; một server sống một server chết; sai cwd/venv; CORS chặn browser dù healthOK; lỗi provider/quota bị gọi là ứng dụng ổn định tuyệt đối; lần chạy lại ghi đè dữ liệu người dùng hoặc log chứa key.

## Verification and rulings

222pytest passed; launcher9tests independently reviewed and re-run GREEN. BrowserPhase2/3/5/6/shared/100rowauto PASS. Real provider30/30automatic, actual6groups, XLSX31/7rows and actual basemap all PASS. WindowsCtrl+C observed cleanup; restart bothports andcheckREADY PASS. Initial40sec startup underparalleltests timedout; isolatedstartworked, finaldeadline90sec. CDPdemoport unavailable; headless Edge used for live network evidence. Review noCritical/Important. Phase7 remainsunimplemented after explicit usersteering; no commit/push/deploy. See docs/reports/local-readiness.md.
