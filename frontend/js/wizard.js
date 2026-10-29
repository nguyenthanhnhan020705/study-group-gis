import { state, allLocationsVerified } from "./state.js";

export function initializeWizard() {
  const main = document.getElementById("workspace");
  const importPanel = document.querySelector('[aria-labelledby="import-title"]');
  const locationPanel = document.querySelector('[aria-labelledby="location-title"]');
  const groupingPanel = document.getElementById("grouping-panel");
  const results = document.getElementById("group-results");
  const map = document.querySelector(".workspace-grid");
  const panels = [importPanel, locationPanel, groupingPanel, results].map((content, index) => {
    const panel = document.createElement("section");
    panel.id = `step-${index + 1}`;
    panel.className = "wizard-step";
    panel.setAttribute("aria-label", `Bước ${index + 1}`);
    panel.append(content);
    main.append(panel);
    return panel;
  });
  results.classList.add("import-panel");
  const actions = document.getElementById("wizard-actions");
  main.append(actions);
  const previous = document.getElementById("wizard-back");
  const next = document.getElementById("wizard-next");
  const hint = document.getElementById("wizard-hint");
  const buttons = [...document.querySelectorAll("[data-step]")];
  let current = 1;
  const allowed = () => [true, state.canGeocode && state.students.length > 0, allLocationsVerified(), Boolean(state.groupingResult)];

  function render(focus = false) {
    const available = allowed();
    if (!available[current - 1]) current = available[2] ? 3 : available[1] ? 2 : 1;
    panels.forEach((panel, index) => { panel.hidden = index + 1 !== current; });
    buttons.forEach((button, index) => {
      button.disabled = !available[index];
      button.dataset.complete = String(Boolean(available[index + 1]));
      if (index + 1 === current) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    });
    const wasHidden = map.hidden;
    map.hidden = ![2, 4].includes(current);
    if (!map.hidden) {
      const host = panels[current - 1];
      const relocated = map.parentElement !== host;
      if (relocated) host.prepend(map);
      if (wasHidden || relocated) requestAnimationFrame(() => window.dispatchEvent(new Event("wizard-map-visible")));
    }
    previous.hidden = current === 1;
    next.hidden = current >= 3;
    next.disabled = !available[current];
    next.textContent = current === 1 ? "Tiếp tục: Xác nhận vị trí →" : "Tiếp tục: Chia nhóm →";
    hint.textContent = [
      available[1] ? "Danh sách hợp lệ. Tiếp tục để kiểm tra vị trí trên bản đồ." : "Tải mẫu, điền thông tin và đọc danh sách để tiếp tục.",
      available[2] ? "Đã xác nhận đủ vị trí. Sẵn sàng chia nhóm." : "Hệ thống đang đối chiếu. Kiểm tra các địa chỉ cần xử lý trước khi tiếp tục.",
      "Điều chỉnh số Nam/Nữ và bấm Chia nhóm để xem kết quả.",
      "Bạn có thể lọc từng nhóm hoặc xuất toàn bộ kết quả ra Excel.",
    ][current - 1];
    if (focus) {
      const title = panels[current - 1].querySelector("h2");
      title.tabIndex = -1;
      title.focus({ preventScroll: true });
      document.getElementById("wizard-nav").scrollIntoView({ block: "start", behavior: "instant" });
    }
  }
  function go(step) {
    if (!allowed()[step - 1]) return;
    current = step;
    render(true);
  }
  buttons.forEach(button => button.addEventListener("click", () => go(Number(button.dataset.step))));
  previous.addEventListener("click", () => go(current - 1));
  next.addEventListener("click", () => go(current + 1));
  window.addEventListener("students-changed", () => render());
  window.addEventListener("grouping-invalidated", () => render());
  window.addEventListener("grouping-changed", () => {
    if (current === 3 && state.groupingResult) go(4);
    else render();
  });
  render();
}
