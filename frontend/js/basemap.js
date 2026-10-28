import { fallbackTileUrl } from "./api.js";

// Separate public imagery delivery from student markers and geocoding state.
export function initializeBasemap(map) {
  const status = document.getElementById("map-status");
  const sourceLabel = document.getElementById("map-source");
  const retry = document.getElementById("retry-map");
  const sources = [
    { name: "OpenStreetMap", url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' },
    { name: "Geoapify / OSM", url: fallbackTileUrl,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors · <a href="https://www.geoapify.com/">Geoapify</a>' },
  ];
  let active = null;
  let generation = 0;
  let timer = null;

  function message(kind, text) {
    status.dataset.state = kind;
    status.textContent = text;
    retry.hidden = kind !== "error";
  }

  function useSource(index) {
    const token = ++generation;
    clearTimeout(timer);
    if (active) map.removeLayer(active);
    const source = sources[index];
    sourceLabel.textContent = source.name;
    const layer = L.tileLayer(source.url, { maxZoom: 19, attribution: source.attribution });
    active = layer;
    let failed = false;
    let loaded = 0;
    function fail() {
      if (token !== generation) return;
      clearTimeout(timer);
      if (index === 0) {
        // Defer removal until Leaflet has finished accounting for the failing tile.
        ++generation;
        setTimeout(() => { if (generation === token + 1) useSource(1); }, 0);
      } else {
        failed = true;
        message("error", "Không tải được nền bản đồ. Kiểm tra kết nối hoặc cấu hình Geoapify ở backend, rồi nhấn Thử lại bản đồ.");
      }
    }
    layer.on("loading", () => {
      if (token !== generation) return;
      failed = false;
      loaded = 0;
      message("loading", index === 0 ? "Đang tải nền OpenStreetMap…" : "Đang tải nền dự phòng Geoapify / OSM…");
      clearTimeout(timer);
      timer = setTimeout(fail, 12000);
    });
    layer.on("tileload", () => { if (token === generation) loaded += 1; });
    layer.on("tileerror", fail);
    layer.on("load", () => {
      if (token !== generation) return;
      clearTimeout(timer);
      if (!failed && loaded > 0) message("ready", `Nền ${source.name} đã tải. Cuộn để thu phóng, kéo để khám phá khu vực.`);
      else fail();
    });
    layer.addTo(map);
  }
  retry.addEventListener("click", () => useSource(0));
  useSource(0);
}
