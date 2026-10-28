import { state, editAddress, applyGeocode, selectLocation, confirmLocation, allLocationsVerified, canUseLocation, visibleGroupMembers } from "./state.js";
import { retryGeocoding } from "./api.js";
import { showStudentLocations } from "./map.js";

export function initializeGeocoding() {
  const list = document.getElementById("location-rows");
  const all = document.getElementById("geocode-all");
  const progress = document.getElementById("location-progress");
  const filter = document.getElementById("location-filter");
  let version = state.importVersion;
  let cache = new Map();
  let running = false;
  let controller = null;
  let busyId = null;
  let stoppedMessage = "";

  function element(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }

  function render() {
    if (version !== state.importVersion) {
      controller?.abort();
      controller = null;
      running = false;
      busyId = null;
      stoppedMessage = "";
      cache = new Map();
      version = state.importVersion;
      list.replaceChildren();
    }
    const confirmed = state.students.filter(s => s.location_confirmed).length;
    all.disabled = !state.canGeocode || !state.students.length || running;
    const automatic = state.students.filter(s => s.location_confirmed && s.location_method === "automatic").length;
    const unresolved = state.students.length - confirmed;
    progress.textContent = state.canGeocode ? `${confirmed}/${state.students.length} vị trí đã xác định · ${automatic} tự động · ${unresolved} cần xử lý.${running ? " Đang tự động đối chiếu…" : stoppedMessage}` : "Nhập danh sách hợp lệ và sửa hết lỗi dữ liệu trước khi tìm vị trí.";
    document.getElementById("grouping-readiness").textContent = allLocationsVerified()
      ? "Đã xác nhận đủ vị trí. Thiết lập số Nam/Nữ ở bước 03 để chia nhóm."
      : "Chưa đủ vị trí đã xác nhận để chia nhóm.";
    document.getElementById("generate-groups").dataset.ready = String(allLocationsVerified());
    showStudentLocations(state.groupingResult ? visibleGroupMembers() : state.students, null, !running && confirmed > 0);
    if (!state.canGeocode) {
      list.replaceChildren();
      return;
    }
    const statuses = { pending: "Chưa kiểm tra", needs_review: "Cần kiểm tra và xác nhận", verified: "Đã xác nhận", error: "Lỗi dịch vụ" };
    for (const student of state.students) {
      const card = element("article", undefined, "location-card");
      card.dataset.studentId = student.student_id;
      card.hidden = filter.value === "review" && student.location_confirmed;
      card.append(element("h3", `Dòng ${student.excel_row} · ${student.ho_ten} · ${student.gioi_tinh}`));
      card.append(element("p", `Địa chỉ gốc: ${student.dia_chi_goc}`, "import-help"));
      const label = element("label", "Địa chỉ dùng để tìm vị trí");
      const address = element("input", undefined, "location-address");
      address.type = "text";
      address.id = `address-${student.student_id}`;
      address.maxLength = 2000;
      label.htmlFor = address.id;
      address.value = student.dia_chi_da_sua ?? student.dia_chi_goc;
      address.addEventListener("input", () => editAddress(student, address.value));
      const retry = element("button", busyId === student.student_id ? "Đang kiểm tra…" : "Kiểm tra lại", "location-retry");
      retry.type = "button";
      retry.disabled = running || !address.value.trim();
      retry.addEventListener("click", () => run([student], true));
      card.append(label, address, retry);
      card.append(element("p", `${student.location_method === "automatic" ? "Đã tự động đối chiếu" : statuses[student.geocode_status] || "Chưa kiểm tra"}. ${student.geocode_message || ""}`, "import-help"));
      const candidateLabel = element("label", "Chọn ứng viên địa chỉ");
      const select = element("select", undefined, "location-candidate");
      select.id = `candidate-${student.student_id}`;
      candidateLabel.htmlFor = select.id;
      const empty = element("option", "— Chọn địa chỉ sau khi đối chiếu —");
      empty.value = "";
      select.append(empty);
      for (const [index, candidate] of (student.candidates || []).entries()) {
        const quality = candidate.source === "geoapify_places" ? "Geoapify Places / OSM · đối chiếu địa danh" : `tin cậy ${candidate.confidence ?? "không có"}`;
        const policy = candidate.allowed_genders ? ` · Dành cho ${candidate.allowed_genders.join(" và ")}` : "";
        const option = element("option", `${candidate.formatted} · ${candidate.result_type} · ${quality}${policy}${candidate.eligible ? "" : ` · ${candidate.reason}`}`);
        option.value = String(index);
        option.disabled = !canUseLocation(student, candidate);
        select.append(option);
      }
      select.value = student.selectedCandidate == null ? "" : String(student.selectedCandidate);
      select.addEventListener("change", () => {
        selectLocation(student, select.value === "" ? null : Number(select.value));
        showStudentLocations(state.students, student.candidates?.[student.selectedCandidate]);
      });
      const candidate = student.candidates?.[student.selectedCandidate];
      const preview = element("button", "Xem trên bản đồ", "location-preview");
      preview.type = "button";
      preview.disabled = !canUseLocation(student, candidate);
      preview.addEventListener("click", () => {
        showStudentLocations(state.groupingResult ? visibleGroupMembers() : state.students, candidate);
        document.getElementById("map").scrollIntoView({ behavior: "smooth", block: "center" });
      });
      const confirm = element("button", student.location_confirmed ? "Đã xác nhận" : "Xác nhận vị trí", "location-confirm");
      confirm.type = "button";
      confirm.disabled = !canUseLocation(student, candidate) || student.location_confirmed;
      confirm.addEventListener("click", () => confirmLocation(student));
      card.append(candidateLabel, select);
      if (candidate) card.append(element("p", `Điểm đại diện: ${candidate.lat}, ${candidate.lon}. Hãy đối chiếu bản đồ trước khi xác nhận.`, "import-help"));
      card.append(preview, confirm);
      const existing = list.querySelector(`[data-student-id="${student.student_id}"]`);
      if (existing) {
        existing.hidden = card.hidden;
        // Keep the input mounted: replacing it interrupts IME composition and undo.
        const oldChildren = [...existing.children];
        const newChildren = [...card.children];
        newChildren.forEach((child, index) => {
          const previous = oldChildren[index];
          if (child.classList.contains("location-address") && previous?.classList.contains("location-address")) {
            if (previous.value !== child.value) previous.value = child.value;
          } else if (previous) previous.replaceWith(child);
          else existing.append(child);
        });
        oldChildren.slice(newChildren.length).forEach(child => child.remove());
      } else list.append(card);
    }
  }

  async function run(students, bypassCache = false) {
    if (running || !state.canGeocode) return;
    running = true;
    stoppedMessage = "";
    const requestVersion = state.importVersion;
    render();
    try {
      for (const student of students) {
        if (requestVersion !== state.importVersion) break;
        const revision = student.locationRevision || 0;
        const address = (student.dia_chi_da_sua ?? student.dia_chi_goc).trim();
        const key = address.replace(/\s+/g, " ").toLocaleLowerCase("vi");
        busyId = student.student_id;
        render();
        let result;
        if (!bypassCache && cache.has(key)) result = structuredClone(cache.get(key));
        else {
          const localController = new AbortController();
          controller = localController;
          const timeout = setTimeout(() => localController.abort(), 20000);
          try {
            result = await retryGeocoding(student.student_id, address, localController.signal);
          } catch (error) {
            result = { status: "error", candidates: [], error_code: "request_error", message: error.name === "AbortError" ? "Đã dừng hoặc hết thời gian chờ. Hãy kiểm tra lại." : error.message || "Không kết nối được dịch vụ." };
          } finally {
            clearTimeout(timeout);
            if (controller === localController) controller = null;
          }
          if (requestVersion === state.importVersion && result.status !== "error") cache.set(key, structuredClone(result));
        }
        applyGeocode(student.student_id, requestVersion, revision, result);
        if (result.status === "error") {
          stoppedMessage = " Đã tạm dừng do lỗi dịch vụ. Kiểm tra kết nối rồi nhấn Đối chiếu lại vị trí còn thiếu.";
          break;
        }
      }
    } finally {
      if (requestVersion === state.importVersion) {
        running = false;
        busyId = null;
        render();
      }
    }
  }

  all.addEventListener("click", () => run(state.students.filter(s => !s.location_confirmed)));
  filter.addEventListener("change", render);
  window.addEventListener("students-imported", () => run(state.students.filter(s => !s.location_confirmed)));
  window.addEventListener("students-changed", render);
  render();
}
