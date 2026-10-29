"""Exercise the wizard with real local APIs and the synthetic geocoding provider."""
import subprocess
import sys
from playwright.sync_api import sync_playwright, expect
from check_phase2_browser import ROOT, wait_ready
from check_phase6_browser import PNG


def main():
    out = ROOT / '.local-tests/wizard'
    out.mkdir(parents=True, exist_ok=True)
    processes = []
    with (out / 'servers.log').open('w') as log:
        try:
            for args in [
                ['uvicorn', 'phase7_provider:app', '--app-dir', 'tests', '--host', '127.0.0.1', '--port', '8027'],
                ['http.server', '5527', '--bind', '127.0.0.1', '--directory', 'frontend'],
            ]:
                processes.append(subprocess.Popen([sys.executable, '-m', *args], cwd=ROOT, stdout=log, stderr=log))
            wait_ready('http://127.0.0.1:8027/api/health', processes[0])
            wait_ready('http://127.0.0.1:5527', processes[1])
            with sync_playwright() as p:
                browser = p.chromium.launch(channel='msedge', headless=True)
                page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                def route_request(route):
                    url = route.request.url
                    if url.endswith('/js/api.js'):
                        route.fulfill(content_type='text/javascript', body=(ROOT / 'frontend/js/api.js').read_text(encoding='utf8').replace(':8001', ':8027'))
                    elif url.startswith('https://unpkg.com/'):
                        route.fulfill(path=str(ROOT / '.local-tests/phase-5' / ('leaflet-1.9.4.css' if url.endswith('.css') else 'leaflet-1.9.4.js')))
                    elif '/api/map-tiles/' in url or url.startswith('https://tile.openstreetmap.org/'):
                        route.fulfill(content_type='image/png', body=PNG)
                    elif url.startswith(('http://127.0.0.1:5527/', 'http://127.0.0.1:8027/')):
                        route.continue_()
                    else:
                        route.abort()
                page.route('**/*', route_request)
                page.goto('http://127.0.0.1:5527')
                expect(page.locator('#step-1')).to_be_visible()
                expect(page.locator('#download-template')).to_have_text('Tải Excel mẫu ↓')
                expect(page.locator('[data-step="3"]')).to_be_disabled()
                with page.expect_download() as download:
                    page.locator('#download-template').click()
                download.value.save_as(out / 'template.xlsx')
                page.screenshot(path=str(out / 'desktop-import.png'), full_page=True)
                page.locator('#student-file').set_input_files(str(ROOT / 'data/samples/danh_sach_sinh_vien_bao_cao.xlsx'))
                page.locator('#import-button').click()
                expect(page.locator('#count-total')).to_have_text('30')
                page.locator('#wizard-next').click()
                expect(page.locator('#step-2')).to_be_visible()
                expect(page.locator('#location-progress')).to_contain_text('30/30', timeout=30000)
                expect(page.locator('#step-2 .leaflet-container')).to_be_visible()
                page.evaluate("window.mapVisibilityEvents = 0; window.addEventListener('wizard-map-visible', () => window.mapVisibilityEvents++);")
                page.evaluate("window.dispatchEvent(new Event('students-changed'))")
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                assert page.evaluate('window.mapVisibilityEvents') == 0, 'Ordinary state changes must preserve map preview/viewport'
                page.locator('#wizard-next').click()
                expect(page.locator('#step-3')).to_be_visible()
                page.locator('#generate-groups').click()
                expect(page.locator('#step-4')).to_be_visible(timeout=30000)
                expect(page.locator('#group-total')).to_have_text('30')
                expect(page.locator('#step-4 .group-center-marker')).not_to_have_count(0)
                page.locator('#group-filter').select_option('1')
                expect(page.locator('#group-visible')).not_to_have_text('30')
                with page.expect_download() as download:
                    page.locator('#export-groups').click()
                download.value.save_as(out / 'groups.xlsx')
                page.screenshot(path=str(out / 'desktop-results.png'), full_page=True)
                page.locator('[data-step="3"]').click()
                page.route('**/api/groups/generate', lambda route: route.fulfill(status=500, content_type='application/json', body='{"message":"Synthetic failure"}'))
                page.locator('#generate-groups').click()
                expect(page.locator('#grouping-status')).to_have_attribute('data-state', 'error')
                expect(page.locator('[data-step="4"]')).to_be_disabled()
                page.unroute('**/api/groups/generate')
                page.locator('#generate-groups').click()
                expect(page.locator('#step-4')).to_be_visible()
                page.locator('[data-step="3"]').click()
                page.locator('#target-male').fill('4')
                expect(page.locator('[data-step="4"]')).to_be_disabled()
                page.locator('[data-step="1"]').click()
                expect(page.locator('#count-total')).to_have_text('30')
                page.locator('#student-file').set_input_files(str(out / 'template.xlsx'))
                page.locator('#import-button').click()
                expect(page.locator('#import-status')).to_have_attribute('data-state', 'error')
                expect(page.locator('[data-step="2"]')).to_be_disabled()
                page.set_viewport_size({'width': 390, 'height': 844})
                page.screenshot(path=str(out / 'mobile-import.png'), full_page=True)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert not errors, errors
                browser.close()
                print('PASS: template, import, location, grouping, filter, export, invalidation, mobile; no JS errors')
        finally:
            for process in processes:
                process.terminate()
                process.wait(timeout=10)


if __name__ == '__main__':
    main()
