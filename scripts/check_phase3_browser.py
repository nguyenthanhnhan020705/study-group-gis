"""Browser regression with explicitly synthetic Geoapify responses, real import API."""
import os
import subprocess
import sys
import json

from openpyxl import Workbook
from playwright.sync_api import sync_playwright, expect
from check_phase2_browser import ROOT, wait_ready


def main():
    output = ROOT / ".local-tests/phase-3"
    output.mkdir(parents=True, exist_ok=True)
    book = Workbook()
    book.active.append(["Họ và tên", "Giới tính", "Nơi ở để học tập"])
    book.active.append(["Sinh viên thử A", "Nam", "Đường thử A"])
    book.active.append(["Sinh viên thử B", "Nữ", "Đường thử B"])
    sample = output / "browser-synthetic.xlsx"
    book.save(sample)
    book.close()
    processes = []
    with (output / "browser-servers.log").open("w") as log:
        try:
            env = {**os.environ, "CORS_ORIGINS": "http://127.0.0.1:5513"}
            processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--port", "8013"], cwd=ROOT, env=env, stdout=log, stderr=log))
            processes.append(subprocess.Popen([sys.executable, "-m", "http.server", "5513", "--bind", "127.0.0.1", "--directory", "frontend"], cwd=ROOT, stdout=log, stderr=log))
            wait_ready("http://127.0.0.1:8013/api/health", processes[0])
            wait_ready("http://127.0.0.1:5513", processes[1])
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="msedge", headless=True)
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.set_default_timeout(7000)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.route("**/js/api.js", lambda route: route.fulfill(content_type="text/javascript", body=(ROOT / "frontend/js/api.js").read_text(encoding="utf-8").replace(":8001", ":8013")))
                page.route("https://unpkg.com/**", lambda route: route.abort())
                def respond(route):
                    data = route.request.post_data_json
                    route.fulfill(content_type="application/json", body=json.dumps({
                        **data, "status": "needs_review", "message": "Ứng viên thử, chưa xác nhận", "error_code": None,
                        "candidates": [{"lat": 10.85, "lon": 106.76, "formatted": "Đường thử — dữ liệu tổng hợp", "result_type": "street", "confidence": 0.95, "eligible": True, "reason": ""},
                                       {"lat": 10.8, "lon": 106.7, "formatted": "Chỉ cấp thành phố", "result_type": "city", "confidence": 0.99, "eligible": False, "reason": "Quá thô"}],
                    }))
                page.route("**/api/geocode/retry", respond)
                page.goto("http://127.0.0.1:5513")
                page.locator("#student-file").set_input_files(str(sample))
                page.locator("#import-button").click()
                expect(page.locator("#geocode-all")).to_be_enabled()
                expect(page.locator(".location-candidate option")).to_have_count(6)
                expect(page.locator("#location-progress")).to_contain_text("0/2")
                cards = page.locator(".location-card")
                for card in cards.all():
                    expect(card.locator(".location-confirm")).to_be_disabled()
                    card.locator(".location-candidate").select_option("0")
                    card.locator(".location-confirm").click()
                expect(page.locator("#location-progress")).to_contain_text("2/2")
                assert page.evaluate("async () => (await import('/js/state.js')).allLocationsVerified()")
                print("PASS: candidates require explicit selection and per-student confirmation")
                page.locator("#location-filter").select_option("all")

                first = cards.first
                first.locator(".location-address").evaluate("node => window.originalAddressInput = node")
                first.locator(".location-address").fill("Địa chỉ vừa sửa")
                assert first.locator(".location-address").evaluate("node => node === window.originalAddressInput"), "Editing must preserve input identity for Vietnamese composition and undo"
                address_input = first.locator(".location-address")
                address_input.press("End")
                address_input.press_sequentially("x")
                address_input.press("Control+z")
                expect(address_input).to_have_value("Địa chỉ vừa sửa")
                address_input.evaluate("node => { node.dispatchEvent(new CompositionEvent('compositionstart', {bubbles:true})); node.value='Địa chỉ vừa sửa tiếng Việt'; node.dispatchEvent(new InputEvent('input', {bubbles:true, isComposing:true, data:'Việt'})); node.dispatchEvent(new CompositionEvent('compositionend', {bubbles:true, data:'Việt'})); }")
                assert address_input.evaluate("node => node === window.originalAddressInput && node === document.activeElement")
                expect(page.locator("#location-progress")).to_contain_text("1/2")
                assert page.evaluate("async () => {const s=(await import('/js/state.js')).state.students[0]; return s.lat===null && !s.location_confirmed && s.ho_ten==='Sinh viên thử A';}")
                assert not page.evaluate("async () => (await import('/js/state.js')).allLocationsVerified()")
                expect(first.locator(".location-candidate option")).to_have_count(1)
                print("PASS: editing clears coordinates, candidates and confirmation while preserving identity")

                page.unroute("**/api/geocode/retry")
                pending = []
                page.route("**/api/geocode/retry", lambda route: pending.append(route))
                first.locator(".location-retry").click()
                page.wait_for_timeout(200)
                assert len(pending) == 1
                first.locator(".location-address").fill("Một địa chỉ mới hơn")
                respond(pending[0])
                page.wait_for_timeout(200)
                expect(first.locator(".location-candidate option")).to_have_count(1)
                print("PASS: delayed response cannot overwrite an edited address")
                page.unroute("**/api/geocode/retry")
                page.route("**/api/geocode/retry", respond)
                page.locator("#student-file").set_input_files({"name": "new-list.xlsx", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "buffer": sample.read_bytes()})
                expect(cards).to_have_count(0)
                expect(page.locator("#geocode-all")).to_be_disabled()
                print("PASS: new import clears all geocoding state")
                page.locator("#import-button").click()
                expect(page.locator(".location-candidate option")).to_have_count(6)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(output / "mobile-synthetic.png"), full_page=True)
                assert not errors, errors
                print("PASS: mobile layout and no JavaScript errors")
                browser.close()
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
