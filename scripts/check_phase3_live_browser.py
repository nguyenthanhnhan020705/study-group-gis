"""Live public-address preview; requires development servers on 8001 and 5500.

Calls the real provider through the backend. Does not confirm geographic accuracy.
"""
from pathlib import Path

from openpyxl import Workbook
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / ".local-tests/phase-3"
    output.mkdir(parents=True, exist_ok=True)
    sample = output / "public-preview.xlsx"
    book = Workbook()
    book.active.append(["Họ và tên", "Giới tính", "Nơi ở để học tập"])
    book.active.append(["Mẫu công cộng", "Nam", "Đường Hoàng Diệu 2, Thành phố Hồ Chí Minh"])
    book.save(sample)
    book.close()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors, exposed = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: exposed.append(True) if "apikey=" in request.url.lower() or "api.geoapify.com" in request.url else None)
        page.goto("http://127.0.0.1:5500")
        expect(page.locator("#map-status")).to_have_attribute("data-state", "ready", timeout=30000)
        page.locator("#student-file").set_input_files(str(sample))
        page.locator("#import-button").click()
        expect(page.locator("#geocode-all")).to_be_enabled()
        page.locator("#geocode-all").click()
        eligible = page.locator('.location-candidate option:not([disabled]):not([value=""])')
        expect(eligible.first).to_be_attached(timeout=20000)
        page.locator(".location-candidate").select_option(eligible.first.get_attribute("value"))
        page.locator(".location-preview").click()
        expect(page.locator(".leaflet-overlay-pane path")).to_have_count(1)
        expect(page.locator("#map-status")).to_have_attribute("data-state", "ready", timeout=30000)
        expect(page.locator("#location-progress")).to_contain_text("0/1")
        assert not page.evaluate("async () => (await import('/js/state.js')).allLocationsVerified()")
        page.wait_for_timeout(1200)  # Allow Leaflet zoom/scroll animation to settle for the screenshot.
        page.screenshot(path=str(output / "live-preview.png"), full_page=True)
        # Retry a public address variant through the real UI/API.
        page.locator(".location-address").fill("Đường Hoàng Diệu 2, TP. Thủ Đức, TP. Hồ Chí Minh")
        expect(page.locator(".leaflet-overlay-pane path")).to_have_count(0)
        page.locator(".location-retry").click()
        expect(eligible.first).to_be_attached(timeout=20000)
        expect(page.locator("#location-progress")).to_contain_text("0/1")
        assert not exposed, "Provider/key must stay on backend"
        assert not errors, errors
        print("PASS: real import -> Geoapify -> OSM preview; edit/retry; no automatic confirmation or browser provider/key request")
        browser.close()


if __name__ == "__main__":
    main()
