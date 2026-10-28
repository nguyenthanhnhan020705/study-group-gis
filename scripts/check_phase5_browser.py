"""Phase 5: synthetic confirmed locations, real grouping API and browser UI.

Starts/stops its own servers on 8015/5516. Does not call Geoapify.
Default blocks CDN; --map uses real Leaflet/OSM and checks rendered markers.
"""
import json
import os
import subprocess
import sys
from urllib.request import Request, urlopen

from playwright.sync_api import expect, sync_playwright
from check_phase2_browser import ROOT, wait_ready

sys.path.insert(0, str(ROOT / "tests"))
from grouping_fixtures import payload

OUTPUT = ROOT / ".local-tests/phase-5"


def install(page, data):
    page.evaluate("""async data => {
      const s=await import('/js/state.js');
      s.setGroupingTargets(3,2);
      s.acceptImport(s.resetImport(), {students:data.students,errors:[],can_proceed:true});
    }""", data)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    data = payload()
    for index, row in enumerate(data["students"], 2):
        row.update(excel_row=index, candidates=[], selectedCandidate=None, locationRevision=0)
    data["students"][0]["ho_ten"] = '<img src=x onerror=alert(1)> Sinh viên thử'
    processes = []
    with (OUTPUT / "servers.log").open("w", encoding="utf-8") as log:
        try:
            env = {**os.environ, "CORS_ORIGINS": "http://127.0.0.1:5516"}
            processes.append(subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8015"], cwd=ROOT, env=env, stdout=log, stderr=log))
            processes.append(subprocess.Popen([sys.executable, "-m", "http.server", "5516", "--bind", "127.0.0.1", "--directory", "frontend"], cwd=ROOT, stdout=log, stderr=log))
            wait_ready("http://127.0.0.1:8015/api/health", processes[0])
            wait_ready("http://127.0.0.1:5516", processes[1])
            raw = payload()
            response = json.loads(urlopen(Request("http://127.0.0.1:8015/api/groups/generate", data=json.dumps(raw).encode(), headers={"Content-Type": "application/json"})).read())
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="msedge", headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 1000})
                page.set_default_timeout(8000)
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.route("**/js/api.js", lambda route: route.fulfill(content_type="text/javascript", body=(ROOT / "frontend/js/api.js").read_text(encoding="utf-8").replace(":8001", ":8015")))
                page.route("**/api/map/tiles/**", lambda route: route.abort())
                if "--map" not in sys.argv:
                    page.route("https://unpkg.com/**", lambda route: route.abort())
                else:
                    # Cache the actual pinned Leaflet bytes, never a replacement map double.
                    def cached_leaflet(route):
                        suffix = ".css" if route.request.url.endswith(".css") else ".js"
                        cached = OUTPUT / ("leaflet-1.9.4" + suffix)
                        if cached.exists():
                            route.fulfill(path=str(cached), content_type="text/css" if suffix == ".css" else "text/javascript")
                        else:
                            route.continue_()
                    def save_leaflet(response):
                        if response.url.startswith("https://unpkg.com/leaflet@1.9.4/dist/leaflet.") and response.status == 200:
                            suffix = ".css" if response.url.endswith(".css") else ".js"
                            (OUTPUT / ("leaflet-1.9.4" + suffix)).write_bytes(response.body())
                    page.route("https://unpkg.com/**", cached_leaflet)
                    page.on("response", save_leaflet)
                page.goto("http://127.0.0.1:5516", wait_until="domcontentloaded")
                page.evaluate("""async ({data,result}) => {
                  const s=await import('/js/state.js');
                  const check=(ok,message)=>{if(!ok) throw Error(message)};
                  check(typeof s.setGroupingTargets==='function','Phase 5 needs target validation and revision state');
                  s.acceptImport(s.resetImport(), {students:data.students,errors:[],can_proceed:true});
                  for(const pair of [[null,2],[-1,2],[1.5,2],[0,0],[true,2],[Number.MAX_SAFE_INTEGER+1,2]]) {
                    s.setGroupingTargets(...pair); check(s.groupingPayload()===null,'Invalid targets must block request');
                  }
                  s.setGroupingTargets(3,2);
                  s.state.students[0].dia_chi_da_sua='  Đường tổng hợp đã sửa  ';
                  check(s.groupingPayload().students[0].dia_chi_da_sua==='Đường tổng hợp đã sửa','Trim API text to match backend schema without rejecting valid edits');
                  s.state.students[0].dia_chi_da_sua=null;
                  const request=s.groupingPayload();
                  check(request.students.length===30 && !('candidates' in request.students[0]) && !('locationRevision' in request.students[0]),'Project only API schema');
                  check(s.acceptGrouping(s.state.groupingRevision,result),'Accept current valid response');
                  check(s.visibleGroupMembers().length===30,'All members initially visible');
                  s.selectGroup(1); check(s.visibleGroupMembers().length===5,'Filter selects exactly five');
                  const revision=s.state.groupingRevision;
                  s.setGroupingTargets(4,2); s.setGroupingTargets(3,2);
                  check(!s.state.groupingResult && !s.acceptGrouping(revision,result),'Changing back cannot revive old response');
                  for(const corrupt of [
                    {...result,assignments:result.assignments.slice(1)},
                    {...result,groups:result.groups.slice(1)},
                    {...result,k:7},
                    {...result,target_male:9},
                    {...result,overall_metrics:{...result.overall_metrics,mean_distance_m:null}},
                    {...result,groups:result.groups.map((g,i)=>i?g:{...g,members:g.members.map((m,j)=>j?m:{...m,lat:11})})},
                    {...result,assignments:result.assignments.map((a,i)=>i?a:{...a,group_id:999})},
                  ]) {
                    let rejected=false;try{s.acceptGrouping(s.state.groupingRevision,corrupt)}catch{rejected=true}
                    check(rejected && !s.state.groupingResult,'Reject inconsistent response without displaying success');
                  }
                  s.acceptGrouping(s.state.groupingRevision,result);
                  s.editAddress(s.state.students[0],'Đường vừa sửa');
                  check(!s.state.groupingResult && s.groupingPayload()===null,'Edited address invalidates results and readiness');
                }""", {"data": raw, "result": response})
                print("PASS: target validation, strict payload, ID/response consistency, filters and revision guards", flush=True)
                if "--state" in sys.argv:
                    browser.close()
                    return

                install(page, data)
                expect(page.locator("#group-count-preview")).to_contain_text("6")
                expect(page.locator("#generate-groups")).to_be_enabled()
                page.locator("#target-male").fill("")
                expect(page.locator("#generate-groups")).to_be_disabled()
                page.locator("#target-male").fill("3")
                for male, female in [("-1", "2"), ("1.5", "2"), ("0", "0")]:
                    page.locator("#target-male").fill(male)
                    page.locator("#target-female").fill(female)
                    expect(page.locator("#generate-groups")).to_be_disabled()
                page.locator("#target-male").fill("3")
                page.locator("#target-female").fill("2")
                with page.expect_request("**/api/groups/generate") as sent:
                    page.locator("#generate-groups").click()
                assert "candidates" not in sent.value.post_data_json["students"][0]
                expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                expect(page.locator("#group-members tr")).to_have_count(30)
                expect(page.locator("#group-stats tr")).to_have_count(6)
                expect(page.locator("#group-total")).to_have_text("30")
                expect(page.locator("#export-groups")).to_be_enabled()
                assert page.locator("#group-members img").count() == 0
                expect(page.locator("#group-members")).to_contain_text("<img src=x onerror=alert(1)>")
                summary = page.locator("#overall-distance").inner_text()
                for group in range(1, 7):
                    page.locator("#group-filter").select_option(str(group))
                    expect(page.locator("#group-members tr")).to_have_count(5)
                    expect(page.locator("#group-stats tr")).to_have_count(1)
                    expect(page.locator("#group-visible")).to_have_text("5")
                    expect(page.locator("#group-total")).to_have_text("30")
                    assert page.locator("#overall-distance").inner_text() == summary
                    assert page.locator("#group-members tr td:first-child").all_text_contents() == [f"Nhóm {group}"] * 5
                    assert page.evaluate("""async () => {
                      const s=await import('/js/state.js');const m=await import('/js/map.js');
                      return m.groupStudentLocations(s.visibleGroupMembers()).reduce((n,p)=>n+p.students.length,0)
                    }""") == 5
                    if "--map" in sys.argv:
                        expect(page.locator(".student-location-marker")).to_have_count(5, timeout=15000)
                        expect(page.locator(".group-center-marker")).to_have_count(1)
                        expect(page.locator(".map-group-legend")).to_contain_text(f"Nhóm {group}")
                        expected_color = page.evaluate("async id=>(await import('/js/map.js')).groupColor(id)", group)
                        assert page.locator(".student-location-marker").evaluate_all("(nodes,color)=>nodes.every(n=>n.getAttribute('fill')===color)", expected_color)
                page.locator("#group-filter").select_option("")
                page.locator("#grouping-panel").evaluate("node=>node.scrollIntoView({block:'start'})")
                page.screenshot(path=str(OUTPUT / "desktop-results.png"))
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.locator("#grouping-panel").evaluate("node=>node.scrollIntoView({block:'start'})")
                page.screenshot(path=str(OUTPUT / "mobile-results.png"))
                page.set_viewport_size({"width": 1440, "height": 1000})
                print("PASS: real API returns 6 groups / 30 people; all six filters, metrics, XSS safety and mobile", flush=True)

                # Same coordinate can contain members of several groups; never move points.
                same = payload(identical=True)
                install(page, same)
                page.locator("#generate-groups").click()
                expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                page.evaluate("""async () => {
                  const s=await import('/js/state.js');const m=await import('/js/map.js');
                  const points=m.groupStudentLocations(s.visibleGroupMembers());
                  if(points.length!==1 || points[0].students.length!==30) throw Error('Keep all collocated people');
                  const popup=m.createLocationPopup(points[0]);
                  for(let i=1;i<=6;i++)if(!popup.textContent.includes(`Nhóm ${i}`))throw Error('Missing group in shared popup');
                }""")
                if "--map" in sys.argv:
                    expect(page.locator(".leaflet-container")).to_be_visible(timeout=20000)
                    expect(page.locator(".student-location-marker")).to_have_count(6)
                    expect(page.locator(".group-center-marker")).to_have_count(1)
                    ring = page.locator(".student-location-marker").first
                    ring.click(position={"x": 2, "y": ring.bounding_box()["height"] / 2})
                    expect(page.locator(".leaflet-popup-content li")).to_have_count(30)
                    page.locator("#group-filter").select_option("2")
                    expect(page.locator(".student-location-marker")).to_have_count(1)
                    expect(page.locator(".group-center-marker")).to_have_attribute("aria-label", "Tâm Nhóm 2 · 5 sinh viên")
                    page.locator("#map").scroll_into_view_if_needed()
                    page.screenshot(path=str(OUTPUT / "map-filtered.png"))
                    tile_status = page.locator("#map-status").get_attribute("data-state")
                    (OUTPUT / "tile-status.json").write_text(json.dumps({"state": tile_status, "message": page.locator("#map-status").inner_text()}, ensure_ascii=False), encoding="utf-8")
                    print(f"Map tiles status: {tile_status}", flush=True)
                    page.locator("#group-filter").select_option("")
                print("PASS: shared coordinate retains all group memberships and popup members", flush=True)
                if "--map" in sys.argv:
                    edge = payload(2, 1)
                    edge["students"][0].update(lat=10.51, lon=106.41)
                    edge["students"][1].update(lat=11.19, lon=106.99)
                    install(page, edge)
                    page.locator("#generate-groups").click()
                    expect(page.locator("#grouping-status")).to_have_attribute("data-state", "success")
                    page.locator("#map").scroll_into_view_if_needed()
                    page.wait_for_function("""() => {
                      const bounds=document.getElementById('map').getBoundingClientRect();
                      const markers=[...document.querySelectorAll('.student-location-marker')];
                      return markers.length===2 && markers.every(n=>{
                        const r=n.getBoundingClientRect();return r.width>=10 && r.height>=10 && r.left>=bounds.left && r.right<=bounds.right && r.top>=bounds.top && r.bottom<=bounds.bottom;
                      });
                    }""", timeout=5000)
                    print("PASS: group result fits all visible representative points inside the map", flush=True)

                # Invalidate both an existing result and delayed responses, even if fetch ignores abort.
                for mutation in ("targets", "address", "import"):
                    install(page, data)
                    page.evaluate("""() => {
                      window.previousFetch=window.fetch;
                      window.fetch=(url,options)=>String(url).includes('/groups/generate')
                        ? new Promise(resolve=>{window.releaseGrouping=()=>resolve(new Response(JSON.stringify(window.savedResult),{status:200,headers:{'Content-Type':'application/json'}}))})
                        : window.previousFetch(url,options);
                    }""")
                    page.evaluate("r=>window.savedResult=r", response)
                    page.locator("#generate-groups").click()
                    expect(page.locator("#grouping-status")).to_have_attribute("data-state", "loading")
                    expect(page.locator("#generate-groups")).to_be_disabled()
                    if mutation == "targets":
                        page.locator("#target-male").fill("4")
                        page.locator("#target-male").fill("3")
                    elif mutation == "address":
                        page.locator("#location-filter").select_option("all")
                        page.locator(".location-address").first.fill("Địa chỉ sửa trong lúc chờ")
                    else:
                        page.locator("#student-file").set_input_files(str(ROOT / "data/samples/danh_sach_sinh_vien_bao_cao.xlsx"))
                    page.evaluate("async()=>{window.releaseGrouping();await new Promise(r=>setTimeout(r,100));window.fetch=window.previousFetch}")
                    expect(page.locator("#group-results")).to_be_hidden()
                    expect(page.locator("#group-members tr")).to_have_count(0)
                    assert page.locator("#grouping-status").get_attribute("data-state") != "success"
                    assert page.evaluate("async()=>!(await import('/js/state.js')).state.groupingResult")
                print("PASS: delayed responses ignored after target change/change-back, address edit and new file", flush=True)

                for status, body, content in [(500, '{"message":"Lỗi chia nhóm thử"}', "application/json"), (429, '{"message":"Máy chủ đang bận"}', "application/json"), (200, '{"k":6}', "application/json"), (200, "<html>bad gateway</html>", "text/html")]:
                    install(page, data)
                    page.route("**/api/groups/generate", lambda route, request, code=status, text=body, mime=content: route.fulfill(status=code, body=text, content_type=mime))
                    page.locator("#generate-groups").click()
                    expect(page.locator("#grouping-status")).to_have_attribute("data-state", "error")
                    expect(page.locator("#group-results")).to_be_hidden()
                    expect(page.locator("#generate-groups")).to_be_enabled()
                    page.unroute("**/api/groups/generate")
                print("PASS: backend errors, busy response and malformed success never display success", flush=True)

                install(page, payload(12, 6))
                page.locator("#generate-groups").click()
                expect(page.locator("#group-warnings")).not_to_be_empty()
                expect(page.locator("#group-members tr")).to_have_count(12)
                install(page, payload(1, 1, 1, 0))
                page.locator("#target-male").fill("1")
                page.locator("#target-female").fill("0")
                page.locator("#generate-groups").click()
                expect(page.locator("#group-members tr")).to_have_count(1)
                expect(page.locator("#overall-distance")).to_contain_text("0")
                page.reload()
                expect(page.locator("#group-results")).to_be_hidden()
                expect(page.locator("#generate-groups")).to_be_disabled()
                assert not errors, errors
                print("PASS: warnings, singleton zero metrics, refresh clears session; no JavaScript errors", flush=True)
                browser.close()
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    main()
