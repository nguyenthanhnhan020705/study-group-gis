"""Real Excel/Places/Leaflet check; keeps the existing demo Edge window open."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
from create_report_sample import OUTPUT as SAMPLE, ROWS, CASES, main as create_sample

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".local-tests/report-sample"


def main():
    create_sample()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9223")
        page = next(page for page in browser.contexts[0].pages if "127.0.0.1:5500" in page.url)
        # The dedicated demo profile may retain older ES modules across local updates.
        session = page.context.new_cdp_session(page)
        session.send("Network.enable")
        session.send("Network.clearBrowserCache")
        session.detach()
        page.bring_to_front()
        page.goto("http://127.0.0.1:5500")
        expect(page.locator("#connection-status")).to_have_attribute("data-state", "online", timeout=15000)
        expect(page.locator("#map-status")).to_have_attribute("data-state", "ready", timeout=30000)
        page.locator("#student-file").set_input_files(str(SAMPLE))
        page.locator("#import-button").click()
        expect(page.locator("#count-total")).to_have_text("30")
        expect(page.locator("#count-male")).to_have_text("18")
        expect(page.locator("#count-female")).to_have_text("12")
        page.locator("#geocode-all").click()
        expect(page.locator("#geocode-all")).to_be_enabled(timeout=90000)
        rows = page.evaluate("async () => (await import('/js/state.js')).state.students")
        assert len(rows) == 30
        for i, (_, _, target) in enumerate(ROWS):
            card = page.locator(".location-card").nth(i)
            index = next(index for index, candidate in enumerate(rows[i]["candidates"]) if candidate["eligible"] and target in candidate["formatted"])
            candidate = rows[i]["candidates"][index]
            assert candidate["address_source_url"] and "Thành phố Hồ Chí Minh" in candidate["formatted"]
            assert "Bình Dương" not in candidate["formatted"]
            if candidate["source"] == "geoapify_places":
                assert candidate["confidence"] is None
            else:
                assert candidate["confidence"] >= .7 and candidate["provider_formatted"]
            expect(card.locator(f'.location-candidate option[value="{index}"]')).to_be_enabled()
            card.locator(".location-candidate").select_option(str(index))
            card.locator(".location-preview").click()
            card.locator(".location-confirm").click()
        expect(page.locator("#location-progress")).to_contain_text("30/30")
        expect(page.locator(".leaflet-overlay-pane path")).to_have_count(9)
        expect(page.locator(".location-count")).to_have_count(9)
        assert page.locator(".location-count").all_text_contents() == ["3", "3", "3", "2", "4", "3", "5", "3", "4"]
        page.locator("#location-progress").screenshot(path=str(OUTPUT / "confirmed-30.png"))
        page.locator("#map").scroll_into_view_if_needed()
        page.locator(".leaflet-control-zoom-out").click()
        page.wait_for_timeout(1200)
        expect(page.locator("#map-status")).to_have_attribute("data-state", "ready", timeout=30000)
        first_student = 0
        for point, (_, target, genders) in enumerate(CASES):
            # Nearby (but distinct) dormitory blocks need zooming; do not force-click
            # through a neighbouring marker or a popup at overview scale.
            close = page.locator(".leaflet-popup-close-button")
            if close.count():
                close.click()
            page.locator(".location-card").nth(first_student).locator(".location-preview").click()
            page.evaluate("window.dispatchEvent(new Event('students-changed'))")
            page.locator(".leaflet-control-zoom-in").click()
            page.wait_for_timeout(350)
            page.locator(".leaflet-control-zoom-in").click()
            page.wait_for_timeout(700)
            page.locator("#map").scroll_into_view_if_needed()
            page.locator(".leaflet-overlay-pane path").nth(point).click()
            popup = page.locator(".leaflet-popup-content")
            expect(popup).to_contain_text(f"{len(genders)} sinh viên tại vị trí này")
            expect(popup.locator("li")).to_have_count(len(genders))
            for offset in range(len(genders)):
                expect(popup).to_contain_text(f"Sinh viên giả lập {first_student+offset+1:02d}")
            expect(popup).to_contain_text("Thành phố Hồ Chí Minh")
            expect(popup).to_contain_text(target)
            assert "Bình Dương" not in popup.inner_text()
            first_student += len(genders)
            page.wait_for_timeout(400)  # Let Leaflet's popup fade complete before saving evidence.
            page.locator("#map").screenshot(path=str(OUTPUT / f"point-{point+1}-popup.png"))
        confirmed = page.evaluate("async () => (await import('/js/state.js')).state.students")
        assert all(row["location_confirmed"] for row in confirmed)
        assert len({(row["lat"], row["lon"]) for row in confirmed}) == 9
        (OUTPUT / "confirmed.json").write_text(json.dumps(confirmed, ensure_ascii=False, indent=2), encoding="utf-8")
        # Check the visible result with one representative shared popup left open.
        close = page.locator(".leaflet-popup-close-button")
        if close.count():
            close.click()
        page.locator(".location-card").first.locator(".location-preview").click()
        page.evaluate("window.dispatchEvent(new Event('students-changed'))")
        page.locator(".leaflet-control-zoom-in").click()
        page.wait_for_timeout(350)
        page.locator(".leaflet-control-zoom-in").click()
        page.wait_for_timeout(700)
        page.locator("#map").scroll_into_view_if_needed()
        page.locator(".leaflet-overlay-pane path").first.click()
        page.wait_for_timeout(400)
        page.locator("#map").screenshot(path=str(OUTPUT / "shared-map.png"))
        print("PASS: 30 confirmed students, 9 live points; all popup members and current labels checked; gender-compatible A/B/C/D/E/CoMay choices", flush=True)


if __name__ == "__main__":
    main()
