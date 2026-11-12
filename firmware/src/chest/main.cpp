#include "chest_sensors.h"
#include "link.h"
#include "pins.h"

using namespace nova;

namespace {
Device device;
Button modeButton;
RangeTrack left, right;
FloorTrack floorTrack;
FloorCalibration calibration;
Calibrator calibrator;
FloorFrame lastFloor;
FloorResult floorResult;
bool calibrating = false, streaming = false, haveFloor = false, camera = false;
uint16_t rawLeft = 0, rawRight = 0;
uint32_t started, calStarted, printed, unhealthyAt, lastWarning, lastHazard;
bool unhealthy = false;
uint8_t warningCount = 0;
Kind previous = Kind::None;
Side previousSide = Side::Both;
Event pending;
uint32_t offeredAt;

void printStatus(uint32_t now) {
    Serial.printf("chest mode=%u level=%u battery_mv=%u usb=%u low=%u L=%u R=%u floor=%u "
        "valid=%u calibrated=%u pitch=%.1f camera_bytes=%u relay=%u\n",
        unsigned(device.mode()), device.level(), device.batteryMv(), device.usbPower(),
        device.lowBattery(), rawLeft, rawRight, floorResult.hazardMm,
        haveFloor && elapsed(now, lastFloor.taken) < 200 && floorResult.reliable,
        calibration.valid(), chestMotion().pitch, unsigned(cameraBytes()), relayReady());
}

void handleCommand(uint32_t now) {
    const String command = device.command();
    if (command.isEmpty()) return;
    if (command == "status") printStatus(now);
    else if (command == "grid") {
        for (size_t i = 0; i < zones; ++i) {
            Serial.printf("%u:%u/%u%s", unsigned(i), lastFloor.mm[i], lastFloor.status[i], i % 4 == 3 ? "\n" : " ");
        }
    } else if (command == "cal floor") {
        calibrator = {};
        calibrating = true;
        calStarted = now;
        Serial.println("cal=collecting keep_still_on_level_floor");
    } else if (command == "cal clear") {
        if (!device.store.isKey("floor") || device.store.remove("floor")) {
            calibration = {};
            floorResult = {};
            calibrating = false;
            floorTrack.reset();
            Serial.println("cal=cleared");
        } else Serial.println("error nvs");
    } else if (command == "stream on" || command == "stream off") {
        streaming = command == "stream on";
    } else if (command == "tof on" || command == "tof off" || command == "camera on" || command == "camera off") {
        const bool tof = command.startsWith("tof ");
        Serial.println(device.store.putBool(tof ? "tof" : "camera", command.endsWith(" on")) ? "ok reboot_required" : "error nvs");
    } else if (command.startsWith("key ")) {
        Serial.println(saveKey(device.store, command.substring(4)) ? "ok reboot_required" : "error key");
    } else if (command.startsWith("peer ")) {
        const String peer = command.substring(5);
        if (peer == "off") {
            Serial.println(!device.store.isKey("peer") || device.store.remove("peer") ? "ok reboot_required" : "error nvs");
        } else if (validPeer(peer)) {
            Serial.println(device.store.putString("peer", peer) ? "ok reboot_required" : "error nvs");
        } else Serial.println("error peer");
    } else if (command.length() == 7 && command.startsWith("level ") && command[6] >= '1' && command[6] <= '3') {
        device.setLevel(command[6] - '0');
        Serial.printf("level=%u\n", device.level());
    } else {
        Serial.println("status | grid | stream on/off | level 1..3 | cal floor/clear | tof on/off | camera on/off | key HEX/off | peer MAC/off");
    }
}

void updateFloor(uint32_t now) {
    FloorFrame frame;
    if (takeFloor(frame)) {
        lastFloor = frame;
        haveFloor = true;
        if (calibrating && calibrator.add(frame)) {
            const FloorCalibration candidate = calibrator.result();
            if (candidate.valid() && device.store.putBytes("floor", &candidate, sizeof candidate) == sizeof candidate) {
                calibration = candidate;
                Serial.println("cal=saved");
            } else Serial.println("cal=failed");
            calibrating = false;
            floorTrack.reset();
        }
        floorResult = floorTrack.update(calibration, frame);
    }
    if (calibrating && elapsed(now, calStarted) >= 12000) {
        calibrating = false;
        Serial.println("cal=timeout");
    }
}

Event currentHazard(uint32_t now) {
    const bool l = left.active(now), r = right.active(now);
    const Mode mode = device.mode();
    const bool center = l && r && abs(int(left.distance()) - int(right.distance())) <= 500;
    Event upper;
    if (center) upper = {Kind::Obstacle, Side::Both, std::min(left.distance(), right.distance())};
    else if (mode != Mode::Crowd) {
        if (l && (!r || left.distance() <= right.distance())) upper = {Kind::Obstacle, Side::Left, left.distance()};
        else if (r) upper = {Kind::Obstacle, Side::Right, right.distance()};
    }
    const bool ground = mode != Mode::Crowd && !calibrating && haveFloor &&
        elapsed(now, lastFloor.taken) < 200 && floorResult.reliable && floorResult.hazardMm &&
        (mode != Mode::Indoor || floorResult.hazardMm <= 1000);
    if (ground && (upper.kind == Kind::None || floorResult.hazardMm + 200 < upper.distance)) {
        return {Kind::Ground, Side::Both, floorResult.hazardMm};
    }
    return upper;
}

void updateAlerts(uint32_t now) {
    const bool healthyUpper = left.alive(now) && right.alive(now);
    const bool healthyGround = device.mode() == Mode::Crowd || (!calibrating && haveFloor &&
        elapsed(now, lastFloor.taken) < 200 && floorResult.reliable);
    const bool degraded = !healthyUpper || !healthyGround;
    if (degraded != unhealthy) {
        unhealthy = degraded;
        unhealthyAt = now;
        warningCount = 0;
    }
    const Event hazard = currentHazard(now);
    if (pending.kind != Kind::None) {
        const auto age = elapsed(now, offeredAt);
        auto result = relayResult();
        if (result == RelayResult::Waiting && age >= 80) {
            result = cancelUnsentRelay() ? RelayResult::Cancelled : relayResult();
        }
        if (result == RelayResult::Waiting || result == RelayResult::Sending || result == RelayResult::Ambiguous) {
            if (age < 650) return;
        }
        if (result != RelayResult::Delivered && hazard.kind != Kind::None) {
            // Re-evaluate the scene after cancellation, rejection, or expiration of a possible remote pulse.
            device.play(hazard, now, true);
        }
        pending = {};
        return;
    }
    if (hazard.kind != Kind::None) {
        const bool changed = hazard.kind != previous || hazard.side != previousSide;
        const auto interval = device.mode() == Mode::Crowd ? 1200 : repeatInterval(hazard);
        if ((!device.busy() || device.training()) && (changed || elapsed(now, lastHazard) >= interval)) {
            if (offerRelay(hazard, now)) {
                pending = hazard;
                offeredAt = now;
            } else device.play(hazard, now, true);
            previous = hazard.kind;
            previousSide = hazard.side;
            lastHazard = now;
        }
    } else {
        previous = Kind::None;
        if (unhealthy && !calibrating && elapsed(now, started) >= 2000 &&
            elapsed(now, unhealthyAt) >= 1100 && warningCount < 3 &&
            (!warningCount || elapsed(now, lastWarning) >= repeatInterval({Kind::Uncertain})) &&
            device.play({Kind::Uncertain}, now)) {
            lastWarning = now;
            ++warningCount;
            device.markTraining();
        }
    }
}
}

void setup() {
    Serial.begin(115200);
    device.begin();
    started = millis();
    if (device.store.getBytesLength("floor") == sizeof calibration) {
        device.store.getBytes("floor", &calibration, sizeof calibration);
    }
    startUltrasound();
    if (!startFloorSensors(device.store.getBool("tof", false))) Serial.println("error sensor_task");
    if (device.store.getBool("camera", false)) {
        pauseCamera(device.mode() == Mode::Indoor);
        camera = startCameraDiagnostic();
    }
    startLink(device.store.getString("peer", ""), loadKey(device.store));
    Serial.printf("NovaChest P1 psram=%u camera_task=%u\n", unsigned(ESP.getPsramSize()), camera);
}

void loop() {
    const uint32_t now = millis();
    device.tick(now);
    RangeSample range;
    if (pollUltrasound(range)) {
        const Motion motion = chestMotion();
        auto& track = range.left ? left : right;
        (range.left ? rawLeft : rawRight) = range.distance;
        track.add(range.distance, obstacleLimit(device.mode(), motion.poseValid ? motion.speed : 0), now);
    }
    updateFloor(now);
    modeButton.update(!digitalRead(pins::mode), now);
    if (modeButton.released()) {
        device.nextMode();
        pauseCamera(device.mode() == Mode::Indoor);
        if (pending.kind == Kind::None) {
            if (device.play({Kind::Confirm, Side::Both, 0, uint8_t(unsigned(device.mode()) + 1)}, now)) {
                device.markTraining();
            }
        }
    }
    if (!device.lowBattery()) updateAlerts(now);
    device.showStatus(device.lowBattery() ? now % 350 < 120 : unhealthy ? now % 1200 < 150 : true);
    handleCommand(now);
    if (streaming && elapsed(now, printed) >= 1000) {
        printed = now;
        printStatus(now);
    }
    delay(2);
}
