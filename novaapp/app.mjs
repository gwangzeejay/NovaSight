import { SERVICE, TELEMETRY, CONTROL, decodeTelemetry, controlPacket, feature } from "./protocol.mjs";

const byId = id => document.getElementById(id);
const set = (id, value) => { byId(id).textContent = value; };
const modes = ["Đi bộ", "Đông người", "Trong nhà"];
const patterns = ["", "Vật cản", "Mặt đất", "Không chắc"];
const storageKey = "novasight-p1-points";
let device, notify, control, live, currentSos = 0, lastSos = 0, sosLocation;
let quiz = 0, writing = false, locating = false, connecting = false;
let points = [];
try {
  const stored = JSON.parse(localStorage.getItem(storageKey) || "[]");
  if (Array.isArray(stored)) points = stored.filter(point => point?.geometry?.type === "Point" &&
    point.geometry.coordinates?.length === 2 && point.geometry.coordinates.every(Number.isFinite) &&
    Number.isFinite(point.properties?.roughness)).slice(-500);
} catch {
  set("track-status", "Không đọc được nhật ký trong trình duyệt.");
}

function buttons() {
  const online = Boolean(control);
  byId("connect").disabled = connecting || online || !navigator.bluetooth;
  byId("disconnect").disabled = !online;
  byId("save-level").disabled = !live?.setup || writing || live.lowBattery;
  byId("quiz-start").disabled = !live?.setup || writing || live.sweeping || live.lowBattery;
  byId("quiz-check").disabled = !quiz;
  document.querySelectorAll("[data-pattern]").forEach(button => { button.disabled = byId("quiz-start").disabled; });
  byId("record").disabled = !live?.sweeping || !live.imu || locating;
  byId("sos-location").disabled = !currentSos || locating;
  byId("sos-compose").disabled = !currentSos;
  byId("sos-dismiss").disabled = !currentSos;
  byId("export").disabled = byId("clear").disabled = !points.length;
}

function received(event) {
  try {
    const before = live;
    live = decodeTelemetry(event.target.value);
    set("mode", modes[live.mode]);
    set("battery", live.battery ? (live.battery / 1000).toFixed(2) + " V" + (live.lowBattery ? " · pin yếu" : "") : "Chưa có số đo");
    set("movement", live.imu ? (live.sweeping ? "Đang quét" : "Đang nghỉ") : "IMU chưa phản hồi");
    set("roughness", live.sweeping ? live.roughness + " / 100" : "—");
    set("beacon", live.beacon ? "Đang nháy" : "Tắt");
    if (!before || before.setup !== live.setup) {
      set("setup-status", live.setup ? "Đã mở cửa sổ thiết lập." : "Cửa sổ thiết lập đang đóng.");
    }
    if (!before || before.level !== live.level) byId("level").value = live.level;
    if (live.sos && live.sos !== lastSos) {
      lastSos = currentSos = live.sos;
      sosLocation = null;
      set("sos-location-status", "");
      set("sos-status", "Đã nhận yêu cầu SOS từ Clip. Chọn người hỗ trợ và mở tin nhắn khi sẵn sàng.");
    }
    buttons();
  } catch (error) {
    set("connection", error.message);
  }
}

function disconnected() {
  notify?.removeEventListener("characteristicvaluechanged", received);
  notify = control = live = null;
  quiz = 0;
  for (const id of ["mode", "battery", "movement", "roughness", "beacon"]) set(id, "—");
  set("connection", "Chưa kết nối.");
  set("setup-status", "Cửa sổ thiết lập đang đóng.");
  buttons();
}

byId("connect").addEventListener("click", async () => {
  connecting = true;
  buttons();
  set("connection", "Đang chọn thiết bị…");
  try {
    device?.removeEventListener("gattserverdisconnected", disconnected);
    device = await navigator.bluetooth.requestDevice({ filters: [{ services: [SERVICE] }] });
    device.addEventListener("gattserverdisconnected", disconnected);
    const server = await device.gatt.connect();
    const service = await server.getPrimaryService(SERVICE);
    notify = await service.getCharacteristic(TELEMETRY);
    control = await service.getCharacteristic(CONTROL);
    notify.addEventListener("characteristicvaluechanged", received);
    await notify.startNotifications();
    await notify.readValue();
    if (notify?.value?.byteLength) received({ target: notify });
    set("connection", "Đã kết nối " + (device.name || "NovaClip P1") + ".");
  } catch (error) {
    if (device?.gatt.connected) device.gatt.disconnect();
    disconnected();
    set("connection", "Không kết nối được. " + error.message);
  } finally {
    connecting = false;
    buttons();
  }
});
byId("disconnect").addEventListener("click", () => device?.gatt.disconnect());

async function write(op, value) {
  if (!control || !live?.setup || writing) return false;
  writing = true;
  buttons();
  try {
    await control.writeValueWithResponse(controlPacket(op, value));
    set("training-status", op === 1 ? "Đã gửi mức rung. Mức hiện hành hiển thị theo phản hồi của Clip." :
      "Đã gửi yêu cầu phát mẫu. Cảm nhận rung trên Clip.");
    return true;
  } catch (error) {
    set("training-status", "Lỗi gửi lệnh. " + error.message);
    return false;
  } finally {
    writing = false;
    buttons();
  }
}
byId("save-level").addEventListener("click", () => write(1, Number(byId("level").value)));
document.querySelectorAll("[data-pattern]").forEach(button => {
  button.addEventListener("click", () => write(2, Number(button.dataset.pattern)));
});
byId("quiz-start").addEventListener("click", async () => {
  quiz = 0;
  const chosen = 1 + Math.floor(Math.random() * 3);
  if (await write(2, chosen)) quiz = chosen;
  buttons();
});
byId("quiz-check").addEventListener("click", () => {
  set("training-status", Number(byId("answer").value) === quiz ? "Đúng. " + patterns[quiz] + "." :
    "Mẫu vừa phát là " + patterns[quiz] + ".");
  quiz = 0;
  buttons();
});

function locationOnce() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("Trình duyệt thiếu tính năng vị trí."));
    navigator.geolocation.getCurrentPosition(position => resolve(position.coords),
      error => reject(new Error(error.message)), { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 });
  });
}

async function locate(status, run) {
  if (locating) return;
  locating = true;
  buttons();
  set(status, "Đang lấy vị trí…");
  try {
    const coordinates = await locationOnce();
    await run(coordinates);
  } catch (error) {
    set(status, "Không lấy được vị trí. " + error.message);
  } finally {
    locating = false;
    buttons();
  }
}

byId("sos-location").addEventListener("click", () => {
  const id = currentSos;
  locate("sos-location-status", coordinates => {
    if (id !== currentSos) return;
    sosLocation = coordinates;
    set("sos-location-status", "Đã lấy vị trí. Sai số báo cáo khoảng " + Math.round(coordinates.accuracy) + " m.");
  });
});
byId("sos-compose").addEventListener("click", () => {
  const phone = byId("phone").value.trim().replace(/[\s-]/g, "");
  if (!/^\+?\d{7,15}$/.test(phone)) {
    set("sos-location-status", "Hãy nhập số điện thoại hợp lệ.");
    byId("phone").focus();
    return;
  }
  const coordinates = sosLocation ? " Vị trí " + sosLocation.latitude.toFixed(6) + ", " +
    sosLocation.longitude.toFixed(6) + " (sai số ~" + Math.round(sosLocation.accuracy) + " m)." : "";
  set("sos-location-status", "Hãy xác nhận nội dung và gửi trong ứng dụng SMS.");
  window.location.href = "sms:" + phone + "?body=" + encodeURIComponent("NovaSight SOS. Tôi cần bạn liên hệ hỗ trợ." + coordinates);
});
byId("sos-dismiss").addEventListener("click", () => {
  currentSos = 0;
  sosLocation = null;
  set("sos-status", "Đã đóng sự kiện SOS.");
  set("sos-location-status", "");
  buttons();
});

function listPoints() {
  set("point-count", points.length + " / 500 điểm đã lưu.");
  byId("points").replaceChildren(...points.slice(-5).reverse().map(point => {
    const item = document.createElement("li");
    const [longitude, latitude] = point.geometry.coordinates;
    item.textContent = latitude.toFixed(5) + ", " + longitude.toFixed(5) + " · gồ ghề " + point.properties.roughness + "/100";
    return item;
  }));
  buttons();
}

byId("record").addEventListener("click", () => {
  locate("track-status", coordinates => {
    if (!live?.sweeping || !live.imu) {
      set("track-status", "Clip đã dừng quét. Hãy thử lại khi đang quét.");
      return;
    }
    const updated = [...points, feature(coordinates, live.roughness)].slice(-500);
    localStorage.setItem(storageKey, JSON.stringify(updated));
    points = updated;
    listPoints();
    set("track-status", "Đã lưu điểm.");
  });
});
byId("export").addEventListener("click", () => {
  const file = new Blob([JSON.stringify({ type: "FeatureCollection", features: points }, null, 2)],
    { type: "application/geo+json" });
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = "novasight-diem-mat-duong.geojson";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
byId("clear").addEventListener("click", () => {
  if (!window.confirm("Xóa toàn bộ điểm mặt đường lưu trong trình duyệt này?")) return;
  try {
    localStorage.removeItem(storageKey);
    points = [];
    listPoints();
    set("track-status", "Đã xóa nhật ký.");
  } catch (error) {
    set("track-status", "Không xóa được nhật ký. " + error.message);
  }
});

if (!navigator.bluetooth) set("connection", "Cần trình duyệt hỗ trợ Web Bluetooth và ngữ cảnh an toàn (HTTPS hoặc localhost).");
listPoints();
