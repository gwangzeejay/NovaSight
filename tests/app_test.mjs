import assert from "node:assert/strict";
import test from "node:test";
import { controlPacket, decodeTelemetry, feature } from "../novaapp/protocol.mjs";

test("telemetry matches Clip's little-endian v1 frame", () => {
  const data = Uint8Array.of(1, 0b10111, 2, 3, 0x74, 0x0e, 48, 0x78, 0x56, 0x34, 0x12);
  assert.deepEqual(decodeTelemetry(new DataView(data.buffer)), {
    mode: 2, level: 3, battery: 3700, roughness: 48,
    sweeping: true, beacon: true, setup: true, lowBattery: false, imu: true, sos: 0x12345678,
  });
  assert.throws(() => decodeTelemetry(new DataView(data.buffer, 0, 2)));
  data[0] = 2;
  assert.throws(() => decodeTelemetry(new DataView(data.buffer)));
});

test("only firmware control operations and ranges are encoded", () => {
  assert.deepEqual(controlPacket(1, 3), Uint8Array.of(1, 1, 3));
  assert.deepEqual(controlPacket(2, 1), Uint8Array.of(1, 2, 1));
  assert.throws(() => controlPacket(1, 0));
  assert.throws(() => controlPacket(3, 1));
});

test("GeoJSON uses longitude before latitude and preserves GPS accuracy", () => {
  const point = feature({ latitude: 12.2, longitude: 109.2, accuracy: 7 }, 16, new Date("2026-11-10T00:00:00Z"));
  assert.deepEqual(point.geometry.coordinates, [109.2, 12.2]);
  assert.deepEqual(point.properties, { roughness: 16, accuracy_m: 7, observed_at: "2026-11-10T00:00:00.000Z" });
});
