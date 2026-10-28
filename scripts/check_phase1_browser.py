"""Smoke-check Phase 1 in headless Microsoft Edge (already installed on Windows).

Start the backend on 8001 and frontend on 5500 before running this script.
Screenshots are written to the ignored .local-tests/phase-1/ directory.
"""

from pathlib import Path

from playwright.sync_api import expect, sync_playwright

OUTPUT = Path(__file__).resolve().parents[1] / ".local-tests" / "phase-1"
HEALTH = "http://127.0.0.1:8001/api/health"
FRONTEND = "http://127.0.0.1:5500"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(FRONTEND)
        expect(page.locator("#connection-status")).to_have_attribute("data-state", "online")
        expect(page.locator(".leaflet-control-attribution")).to_contain_text("OpenStreetMap")
        expect(page.locator("#map-status")).to_have_attribute("data-state", "ready", timeout=30000)
        assert page.locator(".leaflet-tile-loaded").count() > 0
        page.screenshot(path=str(OUTPUT / "desktop.png"), full_page=True)
        assert not errors, errors
        print("PASS: real health/CORS, Leaflet tiles and attribution, no JavaScript errors")

        page.route(HEALTH, lambda route: route.abort())
        page.get_by_role("button", name="Kiểm tra lại").click()
        expect(page.locator("#connection-status")).to_have_attribute("data-state", "offline")
        page.unroute(HEALTH)
        page.get_by_role("button", name="Kiểm tra lại").click()
        expect(page.locator("#connection-status")).to_have_attribute("data-state", "online")
        print("PASS: connection failure and retry recovery")

        page.route(HEALTH, lambda route: route.fulfill(status=200, content_type="application/json", body='{"status":"error"}'))
        page.get_by_role("button", name="Kiểm tra lại").click()
        expect(page.locator("#connection-status")).to_have_attribute("data-state", "offline")
        page.unroute(HEALTH)
        print("PASS: unexpected health payload is not reported as connected")

        page.set_viewport_size({"width": 390, "height": 844})
        page.reload()
        expect(page.locator("#connection-status")).to_have_attribute("data-state", "online")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(OUTPUT / "mobile.png"), full_page=True)
        print("PASS: mobile 390px has no horizontal overflow")

        page.route("**/leaflet.js", lambda route: route.abort())
        page.reload()
        expect(page.locator("#map-status")).to_have_attribute("data-state", "error")
        expect(page.locator("#connection-status")).to_have_attribute("data-state", "online")
        assert not errors, errors
        print("PASS: missing map library has a readable message; health still works")
        page.unroute("**/leaflet.js")
        # Keep CDN requests pending, rather than failing them immediately.
        pending_routes = []
        page.route("https://unpkg.com/**", lambda route: pending_routes.append(route))
        page.reload(wait_until="domcontentloaded")
        expect(page.locator("#connection-status")).to_have_attribute("data-state", "online")
        expect(page.locator("#map-status")).to_have_attribute("data-state", "error", timeout=12000)
        print("PASS: stalled CDN cannot delay health; map loading has a bounded timeout")
        for route in pending_routes:
            route.abort()
        page.unroute_all(behavior="wait")
        browser.close()


if __name__ == "__main__":
    main()
