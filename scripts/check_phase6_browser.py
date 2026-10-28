"""Real export download + real Leaflet recovery. --live-map uses provider imagery.

Default map checks use explicit network fixtures; export always uses real API.
Starts/stops only its own servers 8016/5518. Never calls geocoding.
"""
import base64
import json
import os
import subprocess
import sys

from openpyxl import load_workbook
from playwright.sync_api import expect, sync_playwright
from check_phase2_browser import ROOT, wait_ready
from check_phase5_browser import install, payload

OUTPUT = ROOT / ".local-tests/phase-6"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGMw7ggFAAICARGASOjmAAAAAElFTkSuQmCC")


def generate(page, data):
    install(page, data)
    page.locator("#generate-groups").click()
    expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    processes = []
    with (OUTPUT / "servers.log").open("w", encoding="utf-8") as log:
        try:
            env = {**os.environ, "CORS_ORIGINS": "http://127.0.0.1:5518"}
            processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8016"], cwd=ROOT, env=env, stdout=log, stderr=log))
            processes.append(subprocess.Popen([sys.executable, "-m", "http.server", "5518", "--bind", "127.0.0.1", "--directory", "frontend"], cwd=ROOT, stdout=log, stderr=log))
            wait_ready("http://127.0.0.1:8016/api/health", processes[0])
            wait_ready("http://127.0.0.1:5518", processes[1])
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="msedge", headless=True)
                context = browser.new_context(accept_downloads=True, viewport={"width": 1440, "height": 1000})
                context.route("**/js/api.js", lambda route: route.fulfill(content_type="text/javascript", body=(ROOT / "frontend/js/api.js").read_text(encoding="utf-8").replace(":8001", ":8016")))
                page = context.new_page()
                page.set_default_timeout(10000)
                errors, downloads = [], []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("download", lambda download: downloads.append(download))
                page.route("https://unpkg.com/**", lambda route: route.abort())
                page.goto("http://127.0.0.1:5518")
                data = payload()
                data["students"][0]["ho_ten"] = '=HYPERLINK("https://example.invalid","Tên thử")'
                generate(page, data)
                page.locator("#group-filter").select_option("2")
                expect(page.locator("#group-members tr")).to_have_count(5)
                expect(page.locator("#export-groups")).to_be_enabled()
                result = page.evaluate("async()=>(await import('/js/state.js')).state.groupingResult")
                with page.expect_download() as pending:
                    page.locator("#export-groups").click()
                download = pending.value
                assert download.suggested_filename == "danh_sach_nhom.xlsx"
                destination = OUTPUT / "export-full.xlsx"
                download.save_as(destination)
                expect(page.locator("#export-status")).to_have_attribute("data-state", "success")
                book = load_workbook(destination)
                assert book.sheetnames == ["Danh_sach_nhom", "Thong_ke_nhom"]
                rows = list(book.worksheets[0].values)[1:]
                assert len(rows) == 30 and book.worksheets[1].max_row == 7
                expected = [(g["group_id"], m["ho_ten"], m["gioi_tinh"], m["vi_tri_dai_dien"]) for g in sorted(result["groups"], key=lambda g: g["group_id"]) for m in sorted(g["members"], key=lambda m: m["student_id"])]
                assert [row[1:] for row in rows] == expected
                assert book.worksheets[0]["C2"].data_type == "s"
                for row, group in zip(list(book.worksheets[1].values)[1:], result["groups"]):
                    assert row[:4] == (group["group_id"], group["size"], group["male"], group["female"])
                    assert abs(row[4] - group["metrics"]["mean_distance_m"]) < 1e-6
                book.close()
                print("PASS: real XLSX download while filtered, all 30 members/6 groups, literal formula text and exact statistics", flush=True)
                blob_base64 = base64.b64encode(destination.read_bytes()).decode()
                for mutation in ("targets", "address", "import", "regenerate"):
                    generate(page, data)
                    before = len(downloads)
                    page.evaluate("""b64=>{
                      window.exportFetch=window.fetch;
                      window.fetch=(url,options)=>String(url).endsWith('/groups/export')?new Promise(resolve=>{
                        window.finishOldExport=()=>resolve(new Response(Uint8Array.from(atob(b64),c=>c.charCodeAt(0)),{headers:{'Content-Type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}}))
                      }):window.exportFetch(url,options);
                    }""", blob_base64)
                    page.locator("#export-groups").click()
                    expect(page.locator("#export-groups")).to_be_disabled()
                    if mutation == "targets":
                        page.locator("#target-male").fill("4")
                        page.locator("#target-male").fill("3")
                    elif mutation == "address":
                        page.locator("#location-filter").select_option("all")
                        page.locator(".location-address").first.fill("Địa chỉ sửa lúc tải")
                    elif mutation == "import":
                        page.locator("#student-file").set_input_files(str(ROOT / "data/samples/danh_sach_sinh_vien_bao_cao.xlsx"))
                    else:
                        page.locator("#generate-groups").click()
                        expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                    page.evaluate("async()=>{window.finishOldExport();await new Promise(r=>setTimeout(r,150));window.fetch=window.exportFetch}")
                    assert len(downloads) == before, "Stale export must never trigger a download"
                    if mutation != "regenerate":
                        expect(page.locator("#group-results")).to_be_hidden()
                print("PASS: stale exports ignored after target change-back, address edit, new file and regenerating groups", flush=True)

                forged_zip = b"PK\x03\x04[Content_Types].xml xl/workbook.xml" + b"PK\x05\x06" + b"\0" * 18
                damaged_zip = bytearray(destination.read_bytes())
                damaged_zip[50] ^= 1  # retain ZIP directory/footer, damage compressed XML
                xlsx_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                for status, text, kind in [(500, '{"message":"Lỗi xuất thử"}', "application/json"), (200, "not a workbook", "text/html"), (200, "not a zip", xlsx_type), (200, forged_zip, xlsx_type), (200, bytes(damaged_zip), xlsx_type)]:
                    generate(page, data)
                    before = len(downloads)
                    page.route("**/api/groups/export", lambda route, request, code=status, body=text, mime=kind: route.fulfill(status=code, body=body, content_type=mime))
                    page.locator("#export-groups").click()
                    expect(page.locator("#export-status")).to_have_attribute("data-state", "error")
                    expect(page.locator("#export-groups")).to_be_enabled()
                    assert len(downloads) == before
                    page.unroute("**/api/groups/export")
                with page.expect_download():
                    page.locator("#export-groups").click()
                print("PASS: server/non-XLSX/corrupt responses rejected, then retry downloads successfully", flush=True)
                page.locator("#group-export").scroll_into_view_if_needed()
                page.screenshot(path=str(OUTPUT / "export-desktop.png"))
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                page.screenshot(path=str(OUTPUT / "export-mobile.png"))

                # Real Leaflet; default uses network fixtures so this test is reproducible offline.
                map_page = context.new_page()
                map_page.set_default_timeout(15000)
                map_page.on("pageerror", lambda error: errors.append(str(error)))
                def leaflet(route):
                    suffix = ".css" if route.request.url.endswith(".css") else ".js"
                    cached = ROOT / f".local-tests/phase-5/leaflet-1.9.4{suffix}"
                    if cached.exists():
                        route.fulfill(path=str(cached), content_type="text/css" if suffix == ".css" else "text/javascript")
                    else:
                        route.continue_()
                map_page.route("https://unpkg.com/**", leaflet)
                available = [True]
                if "--live-map" not in sys.argv:
                    map_page.route("https://tile.openstreetmap.org/**", lambda route: route.abort())
                    def tile(route):
                        if available[0]:
                            route.fulfill(body=PNG, content_type="image/png")
                        else:
                            route.fulfill(status=503, body="failed")
                    map_page.route("**/api/map/tiles/**", tile)
                map_page.goto("http://127.0.0.1:5518", wait_until="domcontentloaded")
                expect(map_page.locator("#map-status")).to_have_attribute("data-state", "ready", timeout=45000)
                expect(map_page.locator("#map-source")).to_contain_text("Geoapify")
                expect(map_page.locator(".leaflet-control-attribution")).to_contain_text("Geoapify")
                expect(map_page.locator(".leaflet-control-attribution")).to_contain_text("OpenStreetMap")
                assert map_page.locator(".leaflet-tile").evaluate_all("images=>images.some(i=>i.complete&&i.naturalWidth>0)")
                print("PASS: OSM failure recovers to Geoapify tiles with correct source and attribution", flush=True)
                if "--live-map" in sys.argv:
                    map_page.screenshot(path=str(OUTPUT / "basemap-live.png"))
                    print("PASS: live provider imagery loaded; no mock tiles used in this run", flush=True)
                else:
                    available[0] = False
                    map_page.reload(wait_until="domcontentloaded")
                    expect(map_page.locator("#map-status")).to_have_attribute("data-state", "error")
                    expect(map_page.locator("#retry-map")).to_be_visible()
                    available[0] = True
                    map_page.locator("#retry-map").click()
                    expect(map_page.locator("#map-status")).to_have_attribute("data-state", "ready")
                    print("PASS: both tile sources failing shows error; retry restores a real Leaflet tile layer", flush=True)
                assert not errors, errors
                browser.close()
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
