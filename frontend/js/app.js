import { checkHealth } from "./api.js";
import { initializeMap } from "./map.js";
import { initializeImport } from "./students.js";
import { initializeGeocoding } from "./geocoding.js";
import { initializeGrouping } from "./grouping.js";
import { initializeWizard } from "./wizard.js";

const status = document.getElementById("connection-status");
const retry = document.getElementById("retry-connection");

async function refreshConnection() {
  retry.disabled = true;
  status.dataset.state = "checking";
  status.textContent = "Đang kiểm tra kết nối…";
  try {
    await checkHealth();
    status.dataset.state = "online";
    status.textContent = "● Máy chủ đã kết nối";
  } catch {
    status.dataset.state = "offline";
    status.textContent = "○ Chưa kết nối máy chủ";
  } finally {
    retry.disabled = false;
  }
}

retry.addEventListener("click", refreshConnection);
// Modules run after HTML parsing. The external map must not delay health.
refreshConnection();
initializeMap();
initializeImport();
initializeGeocoding();
initializeGrouping();
initializeWizard();
