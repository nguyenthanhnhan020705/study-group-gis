import { generateGroups, exportGroups } from "./api.js";
import { state, setGroupingTargets, expectedGroupCount, validGroupingTargets, groupingPayload,
  acceptGrouping, visibleGroupMembers, selectGroup, allLocationsVerified } from "./state.js";
import { showStudentLocations, groupColor } from "./map.js";

const number = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 });
const distance = value => `${number.format(value)} m`;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}

export function initializeGrouping() {
  const form = document.getElementById("grouping-form");
  const male = document.getElementById("target-male");
  const female = document.getElementById("target-female");
  const button = document.getElementById("generate-groups");
  const status = document.getElementById("grouping-status");
  const results = document.getElementById("group-results");
  const filter = document.getElementById("group-filter");
  let activeRequest = null;
  let activeExport = null;
  const exportButton = document.getElementById("export-groups");
  const exportStatus = document.getElementById("export-status");

  function exportMessage(text, kind) {
    exportStatus.textContent = text;
    exportStatus.dataset.state = kind;
  }

  function cancelExport(text) {
    activeExport?.abort();
    activeExport = null;
    exportMessage(text, "idle");
  }

  function message(text, kind) {
    status.textContent = text;
    status.dataset.state = kind;
  }

  function render() {
    // Inputs stay mounted to preserve typing/IME and the browser's validity state.
    if (document.activeElement !== male) male.value = state.targetMale ?? "";
    if (document.activeElement !== female) female.value = state.targetFemale ?? "";
    const k = expectedGroupCount();
    document.getElementById("group-count-preview").textContent = k === null ? "—" : String(k);
    document.getElementById("grouping-input-help").textContent = !validGroupingTargets()
      ? "Nhập số Nam/Nữ là số nguyên không âm, tổng lớn hơn 0."
      : !allLocationsVerified() ? "Xác nhận đủ vị trí ở bước 02 để chia nhóm."
        : `Đã sẵn sàng chia ${state.students.length} sinh viên thành ${k} nhóm. Tỷ lệ Nam/Nữ được điều chỉnh nếu dữ liệu không đáp ứng.`;
    button.disabled = !groupingPayload() || Boolean(activeRequest);
    form.setAttribute("aria-busy", String(Boolean(activeRequest)));
    button.textContent = activeRequest ? "Đang chia nhóm…" : "Chia nhóm";
    const result = state.groupingResult;
    results.hidden = !result;
    document.getElementById("group-members").replaceChildren();
    document.getElementById("group-stats").replaceChildren();
    document.getElementById("group-warnings").replaceChildren();
    document.getElementById("group-legend").replaceChildren();
    filter.replaceChildren(new Option("Tất cả nhóm", ""));
    exportButton.disabled = !result || !groupingPayload() || Boolean(activeRequest) || Boolean(activeExport);
    exportButton.textContent = activeExport ? "Đang tạo file Excel…" : "Xuất danh sách nhóm (.xlsx)";
    document.getElementById("export-help").textContent = result
      ? `Xuất toàn bộ ${state.students.length} sinh viên của ${result.k} nhóm, kể cả khi đang lọc một nhóm. File có danh sách và thống kê; không xuất tọa độ thô.`
      : "Cần chia nhóm với dữ liệu hiện tại trước khi xuất Excel.";
    if (!result) {
      showStudentLocations(state.students);
      return;
    }
    const members = visibleGroupMembers();
    document.getElementById("group-total").textContent = String(state.students.length);
    document.getElementById("group-total-count").textContent = String(result.k);
    document.getElementById("group-visible").textContent = String(members.length);
    document.getElementById("overall-distance").textContent = distance(result.overall_metrics.mean_distance_m);
    document.getElementById("overall-max-distance").textContent = distance(result.overall_metrics.max_distance_m);
    document.getElementById("group-view-label").textContent = state.selectedGroup === null
      ? "Đang xem tất cả nhóm trên bản đồ và hai bảng bên dưới."
      : `Đang xem Nhóm ${state.selectedGroup} trên bản đồ và hai bảng bên dưới.`;
    for (const warning of result.warnings) {
      const detail = warning.group_ids.length ? ` (Nhóm ${warning.group_ids.join(", ")})` : "";
      document.getElementById("group-warnings").append(element("li", warning.message + detail));
    }
    document.getElementById("group-warnings-panel").hidden = result.warnings.length === 0;
    const stats = document.createDocumentFragment();
    for (const group of result.groups) {
      filter.add(new Option(`Nhóm ${group.group_id} · ${group.size} người`, String(group.group_id)));
      const legend = element("span", undefined, "group-legend-item");
      const swatch = element("span", undefined, "group-swatch");
      swatch.style.backgroundColor = groupColor(group.group_id);
      swatch.setAttribute("aria-hidden", "true");
      legend.append(swatch, document.createTextNode(`Nhóm ${group.group_id}`));
      document.getElementById("group-legend").append(legend);
      if (state.selectedGroup !== null && group.group_id !== state.selectedGroup) continue;
      const row = element("tr");
      const delta = value => value > 0 ? `+${value}` : String(value);
      for (const value of [`Nhóm ${group.group_id}`, group.size, group.male, group.female,
        `${delta(group.male_delta)} Nam / ${delta(group.female_delta)} Nữ`,
        distance(group.metrics.mean_distance_m), distance(group.metrics.max_distance_m)]) row.append(element("td", value));
      stats.append(row);
    }
    filter.value = state.selectedGroup === null ? "" : String(state.selectedGroup);
    document.getElementById("group-stats").append(stats);
    const rows = document.createDocumentFragment();
    for (const member of members) {
      const row = element("tr");
      for (const value of [`Nhóm ${member.nhom}`, member.student_id, member.ho_ten, member.gioi_tinh, member.vi_tri_dai_dien]) row.append(element("td", value));
      rows.append(row);
    }
    document.getElementById("group-members").append(rows);
    showStudentLocations(members, null, true);
  }

  function invalidate() {
    activeRequest?.abort();
    activeRequest = null;
    cancelExport("Dữ liệu đã thay đổi. Chia nhóm lại trước khi xuất Excel.");
    message("Dữ liệu đã thay đổi. Cần chia nhóm lại trước khi sử dụng kết quả.", "idle");
    render();
  }

  function targetsChanged() {
    const value = input => input.value === "" ? null : input.valueAsNumber;
    setGroupingTargets(value(male), value(female));
    render();
  }
  male.addEventListener("input", targetsChanged);
  female.addEventListener("input", targetsChanged);
  filter.addEventListener("change", () => selectGroup(filter.value === "" ? null : Number(filter.value)));
  window.addEventListener("grouping-invalidated", invalidate);
  window.addEventListener("grouping-changed", render);
  window.addEventListener("students-changed", render);
  exportButton.addEventListener("click", async () => {
    const snapshot = state.groupingResult;
    if (!snapshot || !groupingPayload() || activeRequest || activeExport) return;
    const revision = state.groupingRevision;
    const controller = new AbortController();
    activeExport = controller;
    const timeout = setTimeout(() => controller.abort(), 30000);
    exportMessage("Đang kiểm tra kết quả và tạo file Excel…", "loading");
    render();
    try {
      const blob = await exportGroups(snapshot, controller.signal);
      if (activeExport !== controller || controller.signal.aborted || revision !== state.groupingRevision || state.groupingResult !== snapshot) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "danh_sach_nhom.xlsx";
      document.body.append(link);
      try { link.click(); }
      finally { link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
      exportMessage(`Đã gửi file Excel gồm ${snapshot.assignments.length} sinh viên của ${snapshot.k} nhóm để tải về.`, "success");
    } catch (error) {
      if (activeExport !== controller || revision !== state.groupingRevision || state.groupingResult !== snapshot) return;
      exportMessage(error.name === "AbortError" ? "Quá thời gian tạo file. Vui lòng thử lại."
        : error instanceof TypeError ? "Không kết nối được máy chủ để xuất Excel. Vui lòng thử lại." : error.message, "error");
    } finally {
      clearTimeout(timeout);
      if (activeExport === controller) { activeExport = null; render(); }
    }
  });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const payload = groupingPayload();
    if (!payload || activeRequest) return;
    cancelExport("Đang tính lại nhóm; chỉ xuất sau khi có kết quả mới.");
    // A retry replaces the previous result, even when the next request fails.
    state.groupingResult = null;
    state.selectedGroup = null;
    window.dispatchEvent(new Event("grouping-changed"));
    const revision = state.groupingRevision;
    const controller = new AbortController();
    activeRequest = controller;
    const timeout = setTimeout(() => controller.abort(), 60000);
    message("Đang tính nhóm và kiểm tra kết quả…", "loading");
    render();
    try {
      const result = await generateGroups(payload, controller.signal);
      if (activeRequest !== controller || controller.signal.aborted || revision !== state.groupingRevision) return;
      if (acceptGrouping(revision, result)) message(`Đã chia ${payload.students.length} sinh viên thành ${result.k} nhóm.`, "success");
    } catch (error) {
      if (activeRequest !== controller || revision !== state.groupingRevision) return;
      message(error.name === "AbortError" ? "Quá thời gian chờ chia nhóm. Vui lòng thử lại."
        : error instanceof TypeError ? "Không kết nối được máy chủ. Vui lòng kiểm tra kết nối và thử lại." : error.message, "error");
    } finally {
      clearTimeout(timeout);
      if (activeRequest === controller) {
        activeRequest = null;
        render();
      }
    }
  });
  render();
}
