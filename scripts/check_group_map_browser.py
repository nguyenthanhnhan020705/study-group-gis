"""Group map UI: real Leaflet and grouping API, explicitly synthetic locations."""
import base64
import json
import os
import subprocess
import sys

from playwright.sync_api import expect, sync_playwright
from check_phase2_browser import ROOT, wait_ready
from check_phase5_browser import install, payload
from check_phase6_browser import PNG

OUT = ROOT / ".local-tests/group-map"


def assert_black_pin_painted(page):
    # Check pixels, not just the invisible Leaflet marker's DOM box.
    png = base64.b64encode(page.locator(".group-center-marker").first.screenshot()).decode()
    black_pixels = page.evaluate("""async png => {
      const image = new Image(); image.src = 'data:image/png;base64,' + png;
      await image.decode();
      const canvas = document.createElement('canvas');
      canvas.width = image.width; canvas.height = image.height;
      const context = canvas.getContext('2d'); context.drawImage(image, 0, 0);
      const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
      let count = 0;
      for (let i = 0; i < pixels.length; i += 4)
        if (pixels[i] < 70 && pixels[i+1] < 70 && pixels[i+2] < 70 && pixels[i+3] > 200) count++;
      return count;
    }""", png)
    assert black_pixels >= 160, f"Black pin shape must actually be painted; only {black_pixels} dark pixels"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    processes = []
    with (OUT / "servers.log").open("w", encoding="utf8") as log:
        try:
            env = {**os.environ, "CORS_ORIGINS": "http://127.0.0.1:5530"}
            for command in (["-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8030"],
                            ["-m", "http.server", "5530", "--bind", "127.0.0.1", "--directory", "frontend"]):
                processes.append(subprocess.Popen([sys.executable, "-B", *command], cwd=ROOT, env=env, stdout=log, stderr=log))
            wait_ready("http://127.0.0.1:8030/api/health", processes[0])
            wait_ready("http://127.0.0.1:5530", processes[1])
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="msedge", headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.route("**/js/api.js", lambda route: route.fulfill(content_type="text/javascript", body=(ROOT / "frontend/js/api.js").read_text(encoding="utf8").replace(":8001", ":8030")))
                page.route("https://unpkg.com/**", lambda route: route.fulfill(path=str(ROOT / ".local-tests/phase-5" / ("leaflet-1.9.4.css" if route.request.url.endswith(".css") else "leaflet-1.9.4.js"))))
                page.route("https://tile.openstreetmap.org/**", lambda route: route.fulfill(content_type="image/png", body=PNG))
                page.goto("http://127.0.0.1:5530", wait_until="domcontentloaded")
                data = payload()
                data["students"][0]["ho_ten"] = '<img src=x onerror=alert(1)> Tên thử'
                install(page, data)
                page.locator("#generate-groups").click()
                expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                expect(page.locator(".group-center-marker")).to_have_count(6)
                expect(page.locator(".map-group-legend .group-legend-item")).to_have_count(6)
                assert page.locator(".student-location-marker").count() == 30
                assert page.locator(".group-marker-label").count() == 0
                before = page.evaluate("async()=>JSON.stringify((await import('/js/state.js')).state.groupingResult)")
                result = json.loads(before)
                for group in result["groups"]:
                    group_id = group["group_id"]
                    pin = page.get_by_role("button", name=f"Tâm Nhóm {group_id} · 5 sinh viên", exact=True)
                    pin.focus()
                    pin.press("Enter")
                    expect(page.locator(".leaflet-popup-content .group-popup-members li")).to_have_count(5)
                    for index, member in enumerate(group["members"]):
                        item = page.locator(".leaflet-popup-content .group-popup-members li").nth(index)
                        expect(item.locator("strong")).to_have_text(member["ho_ten"])
                        expect(item.locator("div")).to_have_text(member["gioi_tinh"])
                        expect(item).to_have_text(member["ho_ten"] + member["gioi_tinh"])
                    assert page.locator(".leaflet-popup-content img").count() == 0
                    page.locator(".leaflet-popup-close-button").click()
                assert page.evaluate("async()=>JSON.stringify((await import('/js/state.js')).state.groupingResult)") == before
                page.locator("#group-filter").select_option("2")
                expect(page.locator(".group-center-marker")).to_have_count(1)
                expect(page.locator(".student-location-marker")).to_have_count(5)
                expect(page.locator(".map-group-legend .group-legend-item")).to_have_count(1)
                expect(page.locator("#group-members tr")).to_have_count(5)
                page.locator("#group-filter").select_option("")
                page.locator("#map").scroll_into_view_if_needed()
                page.screenshot(path=str(OUT / "desktop.png"))
                page.set_viewport_size({"width": 390, "height": 844})
                page.locator("#group-filter").select_option("2")
                page.locator("#group-filter").select_option("")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.locator("#map").scroll_into_view_if_needed()
                page.screenshot(path=str(OUT / "mobile.png"))
                page.set_viewport_size({"width": 1440, "height": 1000})
                # All centers and students may coincide: retain access to every group.
                install(page, payload(identical=True))
                page.locator("#generate-groups").click()
                expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                expect(page.locator(".group-center-marker")).to_have_count(1)
                page.locator(".group-center-marker").click()
                expect(page.locator(".group-popup-members li")).to_have_count(30)
                expect(page.locator(".group-popup-section")).to_have_count(6)
                page.evaluate("async()=>{const s=await import('/js/state.js');s.selectGroup(2)}")
                expect(page.locator(".group-center-marker")).to_have_count(1)
                page.locator(".group-center-marker").click()
                expect(page.locator(".group-popup-members li")).to_have_count(5)
                page.locator("#target-male").fill("4")
                expect(page.locator(".group-center-marker")).to_have_count(0)
                expect(page.locator(".map-group-legend")).to_have_count(0)
                expect(page.locator("#export-groups")).to_be_disabled()
                install(page, payload(100, 100))
                page.locator("#target-male").fill("100")
                page.locator("#target-female").fill("0")
                page.locator("#generate-groups").click()
                expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                page.locator(".group-center-marker").click()
                expect(page.locator(".group-popup-members li")).to_have_count(100)
                assert page.locator(".group-popup-members").evaluate("node=>node.scrollHeight>node.clientHeight && getComputedStyle(node).overflowY==='auto'")
                install(page, payload(40, 24, identical=True))
                page.locator("#generate-groups").click()
                expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                expect(page.locator(".student-location-marker")).to_have_count(8)
                shapes = page.locator(".student-location-marker").evaluate_all("nodes=>nodes.map(n=>[n.getAttribute('d'),n.getAttribute('stroke-dasharray'),n.getAttribute('stroke-dashoffset')].join('|'))")
                assert len(set(shapes)) == 8, "Every shared group's colored stroke must occupy its own ring or arc"
                # Reproduce a browser using CSS from before the center-pin release.
                css = (ROOT / "frontend/css/style.css").read_text(encoding="utf8")
                stale_css = css[:css.index(".group-center-marker {")] + css[css.index(".group-center-marker:focus-visible"):]
                page.route("**/css/style.css*", lambda route: route.fulfill(content_type="text/css", body=stale_css))
                page.reload(wait_until="domcontentloaded")
                install(page, data)
                page.locator("#generate-groups").click()
                expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                page.locator("#group-filter").select_option("1")
                expect(page.locator(".group-center-marker")).to_have_count(1)
                assert_black_pin_painted(page)
                page.locator(".group-center-marker").click()
                expect(page.locator(".group-popup-members li")).to_have_count(5)
                # An old module URL can remain cached even after replacing CSS.
                stale_map = (ROOT / "frontend/js/map.js").read_text(encoding="utf8").replace("  renderGroupCenters();", "  // Pre-pin cached module has no center rendering.")
                page.route("**/js/map.js", lambda route: route.fulfill(content_type="text/javascript", body=stale_map))
                page.reload(wait_until="domcontentloaded")
                install(page, data)
                page.locator("#generate-groups").click()
                expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                expect(page.locator(".group-center-marker")).to_have_count(6)
                assert_black_pin_painted(page)
                assert not errors, errors
                browser.close()
                print("PASS: center popups retain all members safely; keyboard/filter/shared centers/invalidation/mobile; state unchanged")
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
