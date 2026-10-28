import { validateWorkbook } from "./xlsx-validation.js";
// Keep the backend address in this one place; never put service keys here.
const API_BASE_URL = "http://127.0.0.1:8001";

export const fallbackTileUrl = `${API_BASE_URL}/api/map/tiles/{z}/{x}/{y}.png`;

export async function exportGroups(payload, signal) {
  const response = await fetch(`${API_BASE_URL}/api/groups/export`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload), signal,
  });
  if (!response.ok) {
    let result;
    try { result = await response.json(); } catch { /* Keep the error readable for non-JSON gateways. */ }
    throw new Error(typeof result?.message === "string" ? result.message : "Không xuất được Excel. Vui lòng thử lại.");
  }
  const type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  if (response.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase() !== type) {
    throw new Error("Máy chủ không trả file Excel hợp lệ. Vui lòng thử lại.");
  }
  const data = new Uint8Array(await response.arrayBuffer());
  await validateWorkbook(data);
  return new Blob([data], { type });
}

export async function generateGroups(payload, signal) {
  const response = await fetch(`${API_BASE_URL}/api/groups/generate`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload), signal,
  });
  let result;
  try { result = await response.json(); }
  catch { throw new Error("Không đọc được kết quả từ máy chủ. Vui lòng thử lại."); }
  if (!response.ok) throw new Error(typeof result?.message === "string" ? result.message : "Không chia được nhóm. Vui lòng kiểm tra dữ liệu và thử lại.");
  return result;
}

export async function retryGeocoding(studentId, address, signal) {
  const response = await fetch(`${API_BASE_URL}/api/geocode/retry`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_id: studentId, address }), signal,
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || "Địa chỉ không hợp lệ hoặc dịch vụ chưa sẵn sàng. Hãy thử lại.");
  if (!["needs_review", "error"].includes(result.status) || !Array.isArray(result.candidates)) throw new Error("Kết quả vị trí không hợp lệ.");
  return result;
}

export async function checkHealth() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      signal: controller.signal,
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Không kết nối được máy chủ.");
    const result = await response.json();
    if (result.status !== "ok") throw new Error("Máy chủ chưa sẵn sàng.");
    return result;
  } finally {
    clearTimeout(timeout);
  }
}

export async function importStudents(file, signal) {
  const form = new FormData();
  form.append("file", file);
  // Browser sets the multipart boundary; do not set Content-Type manually.
  const response = await fetch(`${API_BASE_URL}/api/students/import`, {
    method: "POST", body: form, signal,
  });
  const result = await response.json();
  if (!Array.isArray(result.students) || !Array.isArray(result.errors) || !result.summary || typeof result.can_proceed !== "boolean") {
    throw new Error("Máy chủ trả dữ liệu không hợp lệ. Vui lòng thử lại.");
  }
  if (!response.ok) {
    const error = new Error(result.errors[0]?.message || "Không đọc được file. Vui lòng thử lại.");
    error.details = result.errors;
    throw error;
  }
  return result;
}
