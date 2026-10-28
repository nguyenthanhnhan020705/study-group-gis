import { importStudents } from "./api.js";
import { acceptImport, resetImport } from "./state.js";

export function initializeImport() {
  const fileInput = document.getElementById("student-file");
  const button = document.getElementById("import-button");
  const status = document.getElementById("import-status");
  const rows = document.getElementById("student-rows");
  let activeRequest = null;

  function message(text, kind) {
    status.textContent = text;
    status.dataset.state = kind;
  }

  function showErrors(errors) {
    const list = document.getElementById("import-errors");
    list.replaceChildren();
    for (const error of errors) {
      const item = document.createElement("li");
      item.textContent = `${error.excel_row ? `Dòng ${error.excel_row} · ` : ""}${error.field}: ${error.message}`;
      list.append(item);
    }
    document.getElementById("errors-panel").hidden = errors.length === 0;
  }

  function clear() {
    activeRequest?.abort();
    activeRequest = null;
    const version = resetImport();
    rows.replaceChildren();
    showErrors([]);
    for (const field of ["total", "male", "female", "invalid"]) {
      document.getElementById(`count-${field}`).textContent = "0";
    }
    document.getElementById("students-table-panel").hidden = true;
    document.getElementById("student-empty").hidden = false;
    return version;
  }

  fileInput.addEventListener("change", () => {
    clear();
    const file = fileInput.files[0];
    button.disabled = !file;
    message(file ? `Đã chọn ${file.name}. Nhấn Đọc danh sách để kiểm tra.` : "Chọn file Excel để bắt đầu.", "idle");
  });

  document.getElementById("import-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = fileInput.files[0];
    if (!file) return;
    const version = clear();
    if (!file.name.toLowerCase().endsWith(".xlsx")) {
      message("Chỉ hỗ trợ file Excel .xlsx. Vui lòng chọn lại.", "error");
      return;
    }
    const controller = new AbortController();
    activeRequest = controller;
    const timeout = setTimeout(() => controller.abort(), 30000);
    button.disabled = true;
    message("Đang đọc và kiểm tra danh sách…", "loading");
    try {
      const result = await importStudents(file, controller.signal);
      if (!acceptImport(version, result)) return;
      const invalidIds = new Set(result.errors.map(error => error.student_id));
      const fragment = document.createDocumentFragment();
      for (const student of result.students) {
        const row = document.createElement("tr");
        const invalid = invalidIds.has(student.student_id);
        row.dataset.invalid = String(invalid);
        for (const value of [student.excel_row, student.ho_ten || "—", student.gioi_tinh || "—", student.dia_chi_goc || "—", invalid ? "Cần sửa dữ liệu" : "Dữ liệu nhập hợp lệ"]) {
          const cell = document.createElement("td");
          cell.textContent = String(value);
          row.append(cell);
        }
        fragment.append(row);
      }
      rows.replaceChildren(fragment);
      for (const field of ["total", "male", "female"]) document.getElementById(`count-${field}`).textContent = result.summary[field];
      document.getElementById("count-invalid").textContent = result.summary.invalid_rows;
      showErrors(result.errors);
      document.getElementById("students-table-panel").hidden = result.students.length === 0;
      document.getElementById("student-empty").hidden = result.students.length !== 0;
      message(result.can_proceed
        ? `Đã đọc ${result.summary.total} dòng từ sheet ${result.worksheet}. Dữ liệu nhập hợp lệ. Hệ thống tự đối chiếu vị trí ở bước 02.`
        : `Có ${result.summary.invalid_rows} dòng cần sửa. Hãy sửa trong Excel và tải lại trước khi xác minh vị trí.`,
      result.can_proceed ? "valid" : "invalid");
      if (result.can_proceed) window.dispatchEvent(new Event("students-imported"));
    } catch (error) {
      if (activeRequest !== controller) return;
      showErrors(error.details || []);
      message(error.name === "AbortError"
        ? "Quá thời gian chờ. Hãy kiểm tra kết nối và thử đọc lại."
        : error.details ? error.message : "Không đọc được danh sách. Hãy kiểm tra kết nối máy chủ và thử lại.", "error");
    } finally {
      clearTimeout(timeout);
      if (activeRequest === controller) {
        activeRequest = null;
        button.disabled = !fileInput.files[0];
      }
    }
  });
}
