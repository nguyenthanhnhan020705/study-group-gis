"""Offline UI regression with explicitly synthetic students; no provider results mocked as real."""
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from check_phase2_browser import wait_ready

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".local-tests/shared-locations"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "browser.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen([sys.executable, "-m", "http.server", "5515", "--bind", "127.0.0.1", "--directory", "frontend"], cwd=ROOT, stdout=log, stderr=log)
        try:
            wait_ready("http://127.0.0.1:5515", server)
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="msedge", headless=True)
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.route("https://unpkg.com/**", lambda route: route.abort())
                page.goto("http://127.0.0.1:5515")
                page.evaluate("""async () => {
                  const map = await import('/js/map.js');
                  const student = (id, changes={}) => ({student_id:id, ho_ten:'Tên trùng <img src=x onerror=alert(1)>', gioi_tinh:'Nam', location_confirmed:true,lat:10.85,lon:106.76,vi_tri_dai_dien:'Địa chỉ mẫu',...changes});
                  const rows=[student('A'),student('B'),student('C',{lat:10.86}),student('D',{location_confirmed:false}),student('E',{lat:NaN})];
                  const groups=map.groupStudentLocations(rows);
                  if(groups.length!==2 || groups[0].students.length!==2) throw Error('Collocated students must share one marker without losing names/IDs');
                  if(map.groupStudentLocations([student('A'),student('B',{lat:10.850000001})]).length!==2) throw Error('Distinct coordinates must not be rounded together');
                  const preview=map.groupStudentLocations(rows,{lat:10.85,lon:106.76,formatted:'Ứng viên mẫu'});
                  if(preview.length!==2 || preview[0].students.length!==2 || !preview[0].preview) throw Error('Preview must not add a duplicate marker/student');
                  const differentAddresses=map.groupStudentLocations([student('A'),student('B',{vi_tri_dai_dien:'Địa chỉ khác'})]);
                  if(differentAddresses.length!==1) throw Error('Same coordinate may have multiple address labels');
                  const popup=map.createLocationPopup(differentAddresses[0]);
                  if(popup.querySelectorAll('li').length!==2 || popup.querySelector('img')) throw Error('All students must be shown as safe text');
                  if(!popup.textContent.includes('Địa chỉ khác') || !popup.textContent.includes('2 sinh viên')) throw Error('Popup must include every represented address and count');
                  const large=map.groupStudentLocations(Array.from({length:100},(_,i)=>student(String(i))));
                  const largePopup=map.createLocationPopup(large[0]); document.body.append(largePopup);
                  if(largePopup.querySelectorAll('li').length!==100 || getComputedStyle(largePopup.querySelector('ul')).overflowY!=='auto') throw Error('Large lists must retain everyone and scroll');
                  largePopup.remove();
                }""")
                print("PASS: shared-point grouping, exact coordinates, complete safe popup, 100-person scrolling and preview deduplication", flush=True)
                page.evaluate("""async () => {
                  const s=await import('/js/state.js');
                  const point={lat:10.85,lon:106.76,eligible:true,formatted:'Cư xá A',allowed_genders:['Nam']};
                  const female={student_id:'F1',excel_row:2,ho_ten:'Nữ thử',gioi_tinh:'Nữ',dia_chi_goc:'NLU',candidates:[point,{...point,formatted:'Cư xá B',allowed_genders:['Nữ']},{...point,formatted:'Cư xá E',allowed_genders:['Nam','Nữ']}],selectedCandidate:null};
                  s.state.students=[female];s.state.canGeocode=true;window.dispatchEvent(new Event('students-changed'));
                  if(!document.querySelector('.location-candidate option[value="0"]').disabled || document.querySelector('.location-candidate option[value="1"]').disabled) throw Error('Housing choices must enforce gender policy');
                  s.selectLocation(female,0); female.selectedCandidate=0;
                  if(s.confirmLocation(female) || female.location_confirmed) throw Error('State guard must reject female confirmation in male-only A');
                  s.selectLocation(female,1); if(!s.confirmLocation(female)) throw Error('Female must be allowed in B');
                  for(const gender of ['Nam','Nữ']) {
                    const row={...female,gioi_tinh:gender,location_confirmed:false,selectedCandidate:2};
                    if(!s.confirmLocation(row)) throw Error('Mixed E must allow both genders');
                  }
                }""")
                print("PASS: disabled gender-incompatible options and state confirmation guard", flush=True)
                browser.close()
        finally:
            if server.poll() is None:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()
