// Validate the ZIP directory and each XML member before offering an XLSX download.
export async function validateWorkbook(data) {
  const invalid = () => { throw new Error("File Excel trả về bị lỗi. Vui lòng thử lại."); };
  if (data.length < 22 || data.length > 16 * 1024 * 1024) invalid();
  const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
  const u16 = offset => view.getUint16(offset, true);
  const u32 = offset => view.getUint32(offset, true);
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let end = -1;
  for (let i = data.length - 22; i >= Math.max(0, data.length - 65557); i -= 1) {
    if (u32(i) === 0x06054b50 && i + 22 + u16(i + 20) === data.length) { end = i; break; }
  }
  if (end < 0 || u16(end + 4) || u16(end + 6) || u16(end + 8) !== u16(end + 10)) invalid();
  const count = u16(end + 10), directory = u32(end + 16);
  if (!count || count > 100 || directory + u32(end + 12) !== end) invalid();
  const required = new Set(["[Content_Types].xml", "xl/workbook.xml", "xl/_rels/workbook.xml.rels",
    "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"]);
  const seen = new Set();
  let position = directory, totalSize = 0;
  try {
    for (let entry = 0; entry < count; entry += 1) {
      if (position + 46 > end || u32(position) !== 0x02014b50) invalid();
      const flags = u16(position + 8), method = u16(position + 10);
      const crc = u32(position + 16), size = u32(position + 20), expanded = u32(position + 24);
      const nameLength = u16(position + 28), local = u32(position + 42);
      const next = position + 46 + nameLength + u16(position + 30) + u16(position + 32);
      if (next > end || flags & 9 || ![0, 8].includes(method) || u16(position + 34)) invalid();
      const name = decoder.decode(data.subarray(position + 46, position + 46 + nameLength));
      if (seen.has(name) || local + 30 > directory || u32(local) !== 0x04034b50) invalid();
      seen.add(name);
      const start = local + 30 + u16(local + 26) + u16(local + 28);
      if (start + size > directory || u16(local + 6) !== flags || u16(local + 8) !== method
          || u32(local + 14) !== crc || u32(local + 18) !== size || u32(local + 22) !== expanded
          || decoder.decode(data.subarray(local + 30, local + 30 + u16(local + 26))) !== name) invalid();
      totalSize += expanded;
      if (totalSize > 32 * 1024 * 1024) invalid();
      let bytes = data.subarray(start, start + size);
      if (method === 8) {
        const reader = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw")).getReader();
        const chunks = []; let length = 0;
        try {
          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            length += value.length;
            if (length > expanded) { await reader.cancel(); invalid(); }
            chunks.push(value);
          }
        } finally { reader.releaseLock(); }
        bytes = new Uint8Array(await new Blob(chunks).arrayBuffer());
      }
      if (bytes.length !== expanded) invalid();
      let checksum = 0xffffffff;
      for (const byte of bytes) {
        checksum ^= byte;
        for (let bit = 0; bit < 8; bit += 1) checksum = (checksum >>> 1) ^ (checksum & 1 ? 0xedb88320 : 0);
      }
      if (((checksum ^ 0xffffffff) >>> 0) !== crc) invalid();
      if (name.endsWith(".xml") || name.endsWith(".rels")) {
        const xml = new DOMParser().parseFromString(decoder.decode(bytes), "application/xml");
        if (xml.querySelector("parsererror")) invalid();
      }
      required.delete(name);
      position = next;
    }
    if (position !== end || required.size) invalid();
  } catch { invalid(); }
}
