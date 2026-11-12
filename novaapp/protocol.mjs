const suffix = "-8b8c-4cc2-8ad4-5c1104b992d0";
export const SERVICE = "74cd0100" + suffix;
export const TELEMETRY = "74cd0104" + suffix;
export const CONTROL = "74cd0105" + suffix;

export function decodeTelemetry(view) {
  if (view.byteLength !== 11 || view.getUint8(0) !== 1) throw new Error("Gói BLE không tương thích.");
  const flags = view.getUint8(1);
  const mode = view.getUint8(2);
  const level = view.getUint8(3);
  const battery = view.getUint16(4, true);
  const roughness = view.getUint8(6);
  if (mode > 2 || level < 1 || level > 3 || roughness > 100) throw new Error("Dữ liệu Clip không hợp lệ.");
  return {
    mode, level, battery, roughness,
    sweeping: Boolean(flags & 1), beacon: Boolean(flags & 2),
    setup: Boolean(flags & 4), lowBattery: Boolean(flags & 8), imu: Boolean(flags & 16),
    sos: view.getUint32(7, true),
  };
}

export function controlPacket(op, value) {
  if (![1, 2].includes(op) || ![1, 2, 3].includes(value)) throw new Error("Lệnh Clip không hợp lệ.");
  return Uint8Array.of(1, op, value);
}

export function feature(point, roughness, time = new Date()) {
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates: [point.longitude, point.latitude] },
    properties: { roughness, accuracy_m: point.accuracy, observed_at: time.toISOString() },
  };
}
