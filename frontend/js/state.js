// Session-only state. No localStorage or persisted student data.
export const state = {
  importVersion: 0,
  students: [],
  importErrors: [],
  canGeocode: false,
  groupingResult: null,
  groupingRevision: 0,
  targetMale: 3,
  targetFemale: 2,
  selectedGroup: null,
};

export function invalidateGrouping() {
  state.groupingRevision += 1;
  state.groupingResult = null;
  state.selectedGroup = null;
  window.dispatchEvent(new Event("grouping-invalidated"));
}

export function setGroupingTargets(male, female) {
  if (Object.is(male, state.targetMale) && Object.is(female, state.targetFemale)) return;
  state.targetMale = male;
  state.targetFemale = female;
  invalidateGrouping();
}

export function validGroupingTargets() {
  return [state.targetMale, state.targetFemale].every(value => Number.isSafeInteger(value) && value >= 0)
    && Number.isSafeInteger(state.targetMale + state.targetFemale) && state.targetMale + state.targetFemale > 0;
}

export function expectedGroupCount() {
  return validGroupingTargets() && state.students.length
    ? Math.max(1, Math.floor(state.students.length / (state.targetMale + state.targetFemale))) : null;
}

const studentFields = ["student_id", "excel_row", "ho_ten", "gioi_tinh", "dia_chi_goc", "dia_chi_da_sua",
  "vi_tri_dai_dien", "lat", "lon", "geocode_status", "geocode_confidence", "location_confirmed"];

export function groupingPayload() {
  if (!validGroupingTargets() || !allLocationsVerified()) return null;
  return {
    students: state.students.map(student => Object.fromEntries(studentFields
      .filter(field => student[field] !== undefined)
      .map(field => [field, typeof student[field] === "string" ? student[field].trim() : student[field]]))),
    target_male: state.targetMale, target_female: state.targetFemale,
  };
}

function validMetrics(metrics, pairCount) {
  return metrics && Number.isSafeInteger(metrics.pair_count) && metrics.pair_count >= 0
    && (pairCount === undefined || metrics.pair_count === pairCount)
    && [metrics.mean_distance_m, metrics.max_distance_m].every(value => Number.isFinite(value) && value >= 0)
    && metrics.max_distance_m >= metrics.mean_distance_m;
}

export function acceptGrouping(revision, result) {
  if (revision !== state.groupingRevision) return false;
  const fail = () => { throw new Error("Máy chủ trả kết quả chia nhóm không nhất quán. Vui lòng thử lại."); };
  const request = groupingPayload();
  if (!request) return false;
  if (!result || result.k !== expectedGroupCount() || result.target_male !== state.targetMale
      || result.target_female !== state.targetFemale || !Array.isArray(result.groups)
      || result.groups.length !== result.k || !Array.isArray(result.assignments)
      || result.assignments.length !== state.students.length || !Array.isArray(result.warnings)
      || !result.warnings.every(w => w && typeof w.message === "string" && Array.isArray(w.group_ids))) fail();
  const source = new Map(request.students.map(student => [student.student_id, student]));
  const seen = new Map();
  const groupIds = new Set();
  const sizes = [];
  let pairCount = 0;
  for (const group of result.groups) {
    if (!group || !Number.isSafeInteger(group.group_id) || group.group_id < 1 || groupIds.has(group.group_id)
        || !Array.isArray(group.members) || !group.members.length || group.size !== group.members.length) fail();
    groupIds.add(group.group_id);
    let male = 0;
    for (const member of group.members) {
      const original = source.get(member?.student_id);
      if (!original || seen.has(member.student_id)
          || studentFields.some(field => (member[field] ?? null) !== (original[field] ?? null))) fail();
      seen.set(member.student_id, group.group_id);
      male += member.gioi_tinh === "Nam" ? 1 : 0;
    }
    if (group.male !== male || group.female !== group.size - male
        || group.male_delta !== male - state.targetMale || group.female_delta !== group.female - state.targetFemale
        || !validMetrics(group.metrics, group.size * (group.size - 1) / 2)) fail();
    sizes.push(group.size);
    pairCount += group.metrics.pair_count;
  }
  const assigned = new Set();
  for (const assignment of result.assignments) {
    if (!assignment || assigned.has(assignment.student_id) || !seen.has(assignment.student_id)
        || seen.get(assignment.student_id) !== assignment.group_id) fail();
    assigned.add(assignment.student_id);
  }
  if (seen.size !== source.size || Math.max(...sizes) - Math.min(...sizes) > 1
      || !validMetrics(result.overall_metrics, pairCount)) fail();
  state.groupingResult = result;
  state.selectedGroup = null;
  window.dispatchEvent(new Event("grouping-changed"));
  return true;
}

export function selectGroup(id) {
  state.selectedGroup = state.groupingResult?.groups.some(group => group.group_id === id) ? id : null;
  window.dispatchEvent(new Event("grouping-changed"));
}

export function visibleGroupMembers() {
  return (state.groupingResult?.groups || [])
    .filter(group => state.selectedGroup === null || group.group_id === state.selectedGroup)
    .flatMap(group => group.members.map(member => ({ ...member, nhom: group.group_id })));
}

export function resetImport() {
  state.importVersion += 1;
  state.students = [];
  state.importErrors = [];
  state.canGeocode = false;
  invalidateGrouping();
  window.dispatchEvent(new Event("students-changed"));
  return state.importVersion;
}

export function acceptImport(version, result) {
  if (version !== state.importVersion) return false;
  state.students = result.students;
  state.importErrors = result.errors;
  state.canGeocode = result.can_proceed;
  invalidateGrouping();
  window.dispatchEvent(new Event("students-changed"));
  return true;
}

function clearConfirmation(student) {
  student.location_method = null;
  student.location_confirmed = false;
  student.lat = null;
  student.lon = null;
  student.vi_tri_dai_dien = null;
  student.geocode_confidence = null;
  invalidateGrouping();
}

export function editAddress(student, address) {
  student.dia_chi_da_sua = address;
  student.locationRevision = (student.locationRevision || 0) + 1;
  student.candidates = [];
  student.selectedCandidate = null;
  clearConfirmation(student);
  student.geocode_status = "pending";
  student.geocode_message = "Địa chỉ đã đổi. Cần kiểm tra lại.";
  window.dispatchEvent(new Event("students-changed"));
}

export function applyGeocode(studentId, version, revision, result) {
  const student = state.students.find(row => row.student_id === studentId);
  if (!student || version !== state.importVersion || revision !== (student.locationRevision || 0)) return false;
  clearConfirmation(student);
  student.candidates = result.candidates || [];
  student.selectedCandidate = null;
  student.geocode_status = result.status;
  student.geocode_message = result.message;
  const automatic = student.candidates.map((candidate, index) => ({ candidate, index }))
    .filter(({ candidate }) => result.status === "needs_review" && candidate.auto_selectable === true && canUseLocation(student, candidate));
  if (automatic.length === 1) {
    student.selectedCandidate = automatic[0].index;
    setConfirmedLocation(student, automatic[0].candidate, "automatic");
    student.geocode_message = "Đã tự động đối chiếu địa chỉ và xác định điểm đại diện. Bạn có thể sửa hoặc kiểm tra lại.";
  } else if (result.status !== "error") {
    student.geocode_message = "Cần bổ sung hoặc đối chiếu địa chỉ: chưa xác định được duy nhất một điểm phù hợp. " + (result.message || "");
  }
  window.dispatchEvent(new Event("students-changed"));
  return true;
}

export function selectLocation(student, index) {
  clearConfirmation(student);
  student.selectedCandidate = Number.isInteger(index) && canUseLocation(student, student.candidates?.[index]) ? index : null;
  student.geocode_status = "needs_review";
  window.dispatchEvent(new Event("students-changed"));
}

export function canUseLocation(student, candidate) {
  return Boolean(candidate?.eligible && Number.isFinite(candidate.lat) && Number.isFinite(candidate.lon)
    && (candidate.allowed_genders == null || (Array.isArray(candidate.allowed_genders) && candidate.allowed_genders.includes(student.gioi_tinh))));
}

function setConfirmedLocation(student, candidate, method) {
  student.lat = candidate.lat;
  student.lon = candidate.lon;
  student.vi_tri_dai_dien = candidate.formatted;
  student.geocode_confidence = candidate.confidence;
  student.geocode_status = "verified";
  student.location_confirmed = true;
  student.location_method = method;
}

export function confirmLocation(student) {
  const candidate = student.candidates?.[student.selectedCandidate];
  if (!canUseLocation(student, candidate)) return false;
  setConfirmedLocation(student, candidate, "manual");
  invalidateGrouping();
  window.dispatchEvent(new Event("students-changed"));
  return true;
}

export function allLocationsVerified() {
  return state.canGeocode && state.students.length > 0 && state.students.every(student =>
    student.geocode_status === "verified" && student.location_confirmed && Number.isFinite(student.lat) && Number.isFinite(student.lon));
}
