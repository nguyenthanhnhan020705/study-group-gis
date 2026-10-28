"""Reproducible Phase 2 browser check; starts/stops its own local test servers.

Uses ports 8012/5512 and overrides only api.js's base URL in the test browser.
No Geoapify calls; CDN is blocked because this verifies import, not map tiles.
"""

import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen

from openpyxl import Workbook
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".local-tests" / "phase-2"


def wait_ready(url, process):
    for _ in range(80):
        if process.poll() is not None:
            raise RuntimeError("Test server exited; check ports 8012/5512.")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Test server did not start: {url}")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Họ và tên", "Giới tính", "Nơi ở để học tập"])
    sheet.append(["<img src=x onerror=alert(1)>", "Nam", "Đường A"])
    sheet.append([None, None, None])
    sheet.append(["Sinh viên lỗi", "nam", "Đường B"])
    invalid = OUTPUT / "invalid.xlsx"
    workbook.save(invalid)
    workbook.close()
    processes = []
    with (OUTPUT / "servers.log").open("w", encoding="utf-8") as log:
        try:
            environment = {**os.environ, "CORS_ORIGINS": "http://127.0.0.1:5512"}
            processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--port", "8012"], cwd=ROOT, env=environment, stdout=log, stderr=log))
            processes.append(subprocess.Popen([sys.executable, "-m", "http.server", "5512", "--bind", "127.0.0.1", "--directory", "frontend"], cwd=ROOT, stdout=log, stderr=log))
            wait_ready("http://127.0.0.1:8012/api/health", processes[0])
            wait_ready("http://127.0.0.1:5512", processes[1])
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(channel="msedge", headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                page.route("**/api/geocode/retry", lambda route: route.abort())
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.route("**/js/api.js", lambda route: route.fulfill(content_type="text/javascript", body=(ROOT / "frontend/js/api.js").read_text(encoding="utf-8").replace(":8001", ":8012")))
                page.route("https://unpkg.com/**", lambda route: route.abort())
                page.goto("http://127.0.0.1:5512")
                sample = ROOT / "data/samples/danh_sach_sinh_vien_bao_cao.xlsx"
                page.locator("#student-file").set_input_files(str(sample))
                page.get_by_role("button", name="Đọc danh sách").click()
                expect(page.locator("#student-rows tr")).to_have_count(30)
                expect(page.locator("#count-male")).to_have_text("18")
                expect(page.locator("#count-female")).to_have_text("12")
                expect(page.locator("#import-status")).to_have_attribute("data-state", "valid")
                print("PASS: actual multipart upload, 30 records / 18 male / 12 female")

                page.locator("#student-file").set_input_files(str(invalid))
                expect(page.locator("#student-rows tr")).to_have_count(0)
                page.get_by_role("button", name="Đọc danh sách").click()
                expect(page.locator("#student-rows tr")).to_have_count(3)
                expect(page.locator("#count-invalid")).to_have_text("2")
                expect(page.locator("#import-status")).to_have_attribute("data-state", "invalid")
                expect(page.locator("#import-errors")).to_contain_text("Dòng 3")
                expect(page.locator("#import-errors")).to_contain_text("Dòng 4")
                assert page.locator("#student-rows img").count() == 0
                expect(page.locator("#student-rows")).to_contain_text("<img src=x onerror=alert(1)>")
                print("PASS: invalid rows retained with original line numbers; HTML displayed as text")

                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.screenshot(path=str(OUTPUT / "mobile-errors.png"), full_page=True)
                page.set_viewport_size({"width": 1440, "height": 1000})
                page.screenshot(path=str(OUTPUT / "desktop-errors.png"), full_page=True)
                print("PASS: table scrolls inside its container on mobile")

                endpoint = "**/api/students/import"
                page.route(endpoint, lambda route: route.abort())
                page.locator("#student-file").set_input_files(str(sample))
                page.get_by_role("button", name="Đọc danh sách").click()
                expect(page.locator("#import-status")).to_have_attribute("data-state", "error")
                expect(page.locator("#student-rows tr")).to_have_count(0)
                page.unroute(endpoint)
                print("PASS: failed upload clears previous records and shows retryable error")

                pending = []
                page.route(endpoint, lambda route: pending.append(route))
                page.get_by_role("button", name="Đọc danh sách").click()
                expect(page.locator("#import-status")).to_have_attribute("data-state", "loading")
                page.wait_for_timeout(200)
                assert len(pending) == 1, "Expected an in-flight upload before changing the selected file"
                page.locator("#student-file").set_input_files(str(invalid))
                for route in pending:
                    route.fulfill(status=200, content_type="application/json", body='{"students":[],"errors":[],"can_proceed":true,"summary":{"total":999,"male":999,"female":0,"invalid_rows":0}}')
                page.unroute_all(behavior="wait")
                expect(page.locator("#student-rows tr")).to_have_count(0)
                expect(page.locator("#count-total")).to_have_text("0")
                expect(page.locator("#import-status")).to_have_attribute("data-state", "idle")
                print("PASS: stale response cannot overwrite a newly selected file")
                assert not errors, errors
                browser.close()
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
