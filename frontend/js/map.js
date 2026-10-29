import { initializeBasemap } from "./basemap.js";
import { state } from "./state.js";

let activeMap = null;
let locationLayer = null;
let pendingLocations = [];
let pendingFit = false;
let groupLegend = null;

window.addEventListener("wizard-map-visible", () => {
  if (!activeMap) return;
  activeMap.invalidateSize({ pan: false });
  if (pendingLocations.length) {
    activeMap.fitBounds(pendingLocations.map(point => [point.lat, point.lon]), { padding: [35, 45], maxZoom: 15, animate: false });
  }
});

const groupColors = ["#008dba", "#e626b9", "#65b600", "#8552df", "#dc9518", "#16834b", "#e34d54", "#4169df", "#008b86", "#a04ca6", "#795230", "#445e28"];

export function groupColor(id) {
  return groupColors[(id - 1) % groupColors.length];
}

export function showStudentLocations(students, preview = null, fit = false) {
  pendingLocations = groupStudentLocations(students, preview);
  pendingFit = fit;
  renderLocations(preview);
}

export function groupStudentLocations(students, preview = null) {
  const points = new Map();
  function at(lat, lon) {
    const key = `${lat},${lon}`;
    if (!points.has(key)) points.set(key, { lat, lon, students: [], preview: null });
    return points.get(key);
  }
  for (const student of students) {
    if (student.location_confirmed && Number.isFinite(student.lat) && Number.isFinite(student.lon)) {
      at(student.lat, student.lon).students.push(student);
    }
  }
  if (preview && Number.isFinite(preview.lat) && Number.isFinite(preview.lon)) at(preview.lat, preview.lon).preview = preview;
  return [...points.values()];
}

export function createLocationPopup(point) {
  const popup = document.createElement("div");
  popup.className = "location-popup";
  const title = document.createElement("strong");
  title.textContent = point.students.length ? `${point.students.length} sinh viên tại vị trí này` : "Ứng viên chưa xác nhận";
  popup.append(title);
  const addresses = new Set(point.students.map(student => student.vi_tri_dai_dien || student.dia_chi_goc || ""));
  if (addresses.size === 1) {
    const address = document.createElement("p");
    address.textContent = [...addresses][0];
    popup.append(address);
  }
  if (point.students.length) {
    const list = document.createElement("ul");
    list.className = "location-popup-list";
    list.tabIndex = 0;
    list.setAttribute("aria-label", "Danh sách sinh viên tại vị trí này");
    for (const student of point.students) {
      const item = document.createElement("li");
      item.textContent = `${student.ho_ten} · ${student.gioi_tinh} · ${student.student_id}${student.nhom != null ? ` · Nhóm ${student.nhom}` : ""}`;
      if (addresses.size > 1) {
        const address = document.createElement("div");
        address.textContent = student.vi_tri_dai_dien || student.dia_chi_goc || "";
        item.append(address);
      }
      list.append(item);
    }
    popup.append(list);
  }
  if (point.preview) {
    const note = document.createElement("p");
    note.textContent = `Ứng viên chưa xác nhận: ${point.preview.formatted}`;
    popup.append(note);
  }
  return popup;
}

function createGroupPopup(groups) {
  const popup = document.createElement("div");
  popup.className = "group-center-popup";
  for (const group of groups) {
    const section = document.createElement("section");
    section.className = "group-popup-section";
    const heading = document.createElement("h3");
    heading.textContent = `Nhóm ${group.group_id} · ${group.size} sinh viên`;
    const summary = document.createElement("p");
    summary.textContent = `${group.male} Nam · ${group.female} Nữ · Tâm phân bố của nhóm, không phải điểm hẹn.`;
    const list = document.createElement("ul");
    list.className = "group-popup-members";
    list.tabIndex = 0;
    list.setAttribute("aria-label", `Thành viên Nhóm ${group.group_id}`);
    for (const member of group.members) {
      const item = document.createElement("li");
      const name = document.createElement("strong");
      name.textContent = member.ho_ten;
      const detail = document.createElement("div");
      detail.textContent = member.gioi_tinh;
      item.append(name, detail);
      list.append(item);
    }
    section.append(heading, summary, list);
    popup.append(section);
  }
  return popup;
}

function renderGroupCenters() {
  const groups = (state.groupingResult?.groups || [])
    .filter(group => state.selectedGroup === null || group.group_id === state.selectedGroup);
  if (groupLegend) {
    groupLegend.remove();
    groupLegend = null;
  }
  if (!groups.length) return;
  const centers = new Map();
  for (const group of groups) {
    const key = `${group.centroid.lat},${group.centroid.lon}`;
    if (!centers.has(key)) centers.set(key, []);
    centers.get(key).push(group);
  }
  for (const colocated of centers.values()) {
    const first = colocated[0];
    const names = colocated.map(group => group.group_id).join(", ");
    const title = colocated.length === 1
      ? `Tâm Nhóm ${first.group_id} · ${first.size} sinh viên`
      : `Tâm các nhóm ${names} · Bấm để xem tất cả thành viên`;
    // Draw the icon itself so an older cached stylesheet cannot hide the pin.
    const svgNS = "http://www.w3.org/2000/svg";
    const pin = document.createElementNS(svgNS, "svg");
    pin.setAttribute("class", "group-center-pin");
    pin.setAttribute("viewBox", "0 0 32 40");
    pin.setAttribute("width", "32");
    pin.setAttribute("height", "40");
    pin.setAttribute("aria-hidden", "true");
    const shape = document.createElementNS(svgNS, "path");
    shape.setAttribute("d", "M16 1C8 1 2 7 2 15c0 10 14 23 14 23s14-13 14-23C30 7 24 1 16 1Z");
    shape.setAttribute("fill", "#24282b");
    shape.setAttribute("stroke", "#ffffff");
    shape.setAttribute("stroke-width", "2");
    const badge = document.createElementNS(svgNS, "circle");
    badge.setAttribute("cx", "16");
    badge.setAttribute("cy", "15");
    badge.setAttribute("r", "9");
    badge.setAttribute("fill", "#ffffff");
    const label = document.createElementNS(svgNS, "text");
    label.textContent = colocated.length === 1 ? String(first.group_id) : "+";
    label.setAttribute("x", "16");
    label.setAttribute("y", "15");
    label.setAttribute("dy", ".35em");
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("fill", "#24282b");
    label.setAttribute("font-family", "Segoe UI, Arial, sans-serif");
    label.setAttribute("font-size", label.textContent.length > 2 ? "7" : "10");
    label.setAttribute("font-weight", "700");
    pin.append(shape, badge, label);
    const marker = L.marker([first.centroid.lat, first.centroid.lon], {
      icon: L.divIcon({ className: "group-center-marker", html: pin, iconSize: [32, 40], iconAnchor: [16, 40], popupAnchor: [0, -36] }),
      title, alt: title, keyboard: true, riseOnHover: true,
    }).bindPopup(createGroupPopup(colocated), { maxWidth: 360, minWidth: 230, maxHeight: 300 }).addTo(locationLayer);
    marker.getElement().setAttribute("aria-label", title);
  }
  groupLegend = L.control({ position: "bottomleft" });
  groupLegend.onAdd = () => {
    const box = document.createElement("div");
    box.className = "map-group-legend";
    box.setAttribute("aria-label", "Chú giải nhóm trên bản đồ");
    box.tabIndex = 0;
    const title = document.createElement("strong");
    title.textContent = "Nhóm học tập";
    box.append(title);
    for (const group of groups) {
      const item = document.createElement("div");
      item.className = "group-legend-item";
      const swatch = document.createElement("span");
      swatch.className = "group-ring-swatch";
      swatch.style.color = groupColor(group.group_id);
      swatch.setAttribute("aria-hidden", "true");
      item.append(swatch, document.createTextNode(`Nhóm ${group.group_id}`));
      box.append(item);
    }
    const note = document.createElement("small");
    note.textContent = "Ghim đen: tâm nhóm";
    box.append(note);
    L.DomEvent.disableClickPropagation(box);
    L.DomEvent.disableScrollPropagation(box);
    return box;
  };
  groupLegend.addTo(activeMap);
}

function renderLocations(preview = null) {
  if (!activeMap) return;
  locationLayer.clearLayers();
  for (const point of pendingLocations) {
    const count = point.students.length;
    const groups = [...new Set(point.students.map(student => student.nhom).filter(id => id != null))].sort((a, b) => a - b);
    // Concentric rings preserve every group's color at an exact shared location.
    const rings = groups.length ? groups : [null];
    const segmented = groups.length > 7;
    for (let index = rings.length - 1; index >= 0; index -= 1) {
      const color = rings[index] === null ? "#17634a" : groupColor(rings[index]);
      const radius = segmented ? 16 : (count > 1 ? 11 : 7) + index * 4;
      const arc = 2 * Math.PI * radius / rings.length;
      const marker = L.circleMarker([point.lat, point.lon], {
        radius,
        color: count ? color : "#a45f16", fillColor: color,
        weight: 2.5, fillOpacity: segmented ? (index === 0 ? 0.06 : 0) : groups.length ? 0.1 : count > 1 ? 0.9 : 0.6,
        // Many collocated groups use colored arcs instead of unbounded rings.
        dashArray: segmented ? `${arc} ${2 * Math.PI * radius - arc}` : null,
        dashOffset: segmented ? String(-index * arc) : null,
        lineCap: segmented ? "butt" : "round",
        className: "student-location-marker",
      }).bindPopup(createLocationPopup(point), { maxWidth: 420, minWidth: 240, maxHeight: 320 }).addTo(locationLayer);
      if (groups.length) {
        const label = document.createElement("span");
        label.textContent = `Nhóm ${groups.join(", ")} · ${count} SV`;
        marker.bindTooltip(label, { direction: "top", className: "group-marker-label", opacity: 1 });
      } else if (count > 1) marker.bindTooltip(String(count), { permanent: true, direction: "center", className: "location-count", opacity: 1 });
    }
  }
  renderGroupCenters();
  if (preview && Number.isFinite(preview.lat) && Number.isFinite(preview.lon)) {
    activeMap.setView([preview.lat, preview.lon], 15);
  } else if (pendingFit && pendingLocations.length) {
    activeMap.fitBounds(pendingLocations.map(point => [point.lat, point.lon]), { padding: [35, 45], maxZoom: 15, animate: false });
  }
  pendingFit = false;
}

function loadResource(element) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      element.remove();
      reject(new Error("Hết thời gian tải bản đồ."));
    }, 8000);
    element.onload = () => { clearTimeout(timeout); resolve(); };
    element.onerror = () => { clearTimeout(timeout); element.remove(); reject(new Error("Không tải được bản đồ.")); };
    document.head.append(element);
  });
}

async function loadLeaflet() {
  const style = document.createElement("link");
  style.rel = "stylesheet";
  style.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
  style.integrity = "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=";
  style.crossOrigin = "anonymous";
  const script = document.createElement("script");
  script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
  script.integrity = "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=";
  script.crossOrigin = "anonymous";
  script.async = true;
  await Promise.all([loadResource(style), loadResource(script)]);
}

export async function initializeMap() {
  const status = document.getElementById("map-status");
  try {
    await loadLeaflet();
    if (!window.L) throw new Error("Leaflet chưa sẵn sàng.");
  } catch {
    status.dataset.state = "error";
    status.textContent = "Không tải được thư viện bản đồ. Kiểm tra Internet và tải lại trang.";
    return;
  }

  // Initial viewport only; this is not a student location or geocoding result.
  const map = L.map("map", { zoomControl: false }).setView([10.85, 106.76], 11);
  activeMap = map;
  locationLayer = L.layerGroup().addTo(map);
  renderLocations();
  L.control.zoom({ zoomInTitle: "Phóng to", zoomOutTitle: "Thu nhỏ" }).addTo(map);
  initializeBasemap(map);
  return map;
}
