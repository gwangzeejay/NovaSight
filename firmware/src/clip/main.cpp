#include "device.h"
#include "link.h"
#include "pins.h"

#include <NimBLEDevice.h>
#include <esp_system.h>

using namespace nova;

namespace {
Device device;
Imu imu(Wire);
Motion motion;
Button mode, route, sos;
bool beacon = false, dirty = true;
uint32_t beaconAt, sampled, retry, published, sosId, sosAt;
bool sosPending = false;

void confirm(uint32_t now, uint8_t pulses = 1) {
    if (device.play({Kind::Confirm, Side::Both, 0, pulses}, now)) device.markTraining();
}

void handleCommand(uint32_t now) {
    const String command = device.command();
    if (command.isEmpty()) return;
    if (command == "status") {
        Serial.printf("clip mode=%u level=%u battery_mv=%u usb=%u low=%u imu=%u sweep=%u roughness=%u beacon=%u app=%u sos=%u mac=%s\n",
            unsigned(device.mode()), device.level(), device.batteryMv(), device.usbPower(), device.lowBattery(),
            imu.online(), motion.sweeping, motion.roughness, beacon, appAllowed(now), unsigned(sosPending ? sosId : 0),
            NimBLEDevice::getAddress().toString().c_str());
    } else if (command.startsWith("key ")) {
        Serial.println(saveKey(device.store, command.substring(4)) ? "ok reboot_required" : "error key");
    } else if (command.length() == 7 && command.startsWith("level ") && command[6] >= '1' && command[6] <= '3') {
        device.setLevel(command[6] - '0');
        Serial.printf("level=%u\n", device.level());
    } else {
        Serial.println("status | level 1..3 | key HEX/off");
    }
}

void updateButtons(uint32_t now) {
    mode.update(!digitalRead(pins::mode), now);
    route.update(!digitalRead(pins::route), now);
    sos.update(!digitalRead(pins::sos), now);
    if (mode.held(3000, now)) {
        allowApp(now);
        confirm(now, 2);
        dirty = true;
    } else if (mode.released()) {
        device.nextMode();
        confirm(now, unsigned(device.mode()) + 1);
        dirty = true;
    }
    if (route.released()) {
        beacon = !beacon;
        beaconAt = now;
        dirty = true;
    }
    if (sos.held(3000, now)) {
        sosId = esp_random() | 1;
        sosAt = now;
        sosPending = true;
        // Without a connected phone NovaApp cannot show the SOS, so say so by touch.
        if (clipConnected()) confirm(now);
        else if (device.play({Kind::NoLink}, now, true)) device.markTraining();
        dirty = true;
    }
}

void appControls(uint32_t now) {
    AppCommand request;
    if (!takeAppCommand(request) || !appAllowed(now)) return;
    if (request.op == 1 && request.value >= 1 && request.value <= 3) {
        device.setLevel(request.value);
        confirm(now);
    } else if (request.op == 2 && request.value >= 1 && request.value <= 3 && !motion.sweeping) {
        const Event example{static_cast<Kind>(request.value), Side::Both, 1500};
        if (device.play(example, now)) device.markTraining();
    }
    dirty = true;
}
}

void setup() {
    Serial.begin(115200);
    device.begin();
    pinMode(pins::route, INPUT);
    pinMode(pins::sos, INPUT);
    pinMode(pins::beacon, OUTPUT);
    digitalWrite(pins::beacon, LOW);
    Wire.begin(pins::sda, pins::scl, 400000);
    Wire.setTimeOut(9);
    imu.begin();
    startClipBle(loadKey(device.store));
    Serial.println("NovaCane Clip P1");
}

void loop() {
    const uint32_t now = millis();
    device.tick(now);
    if (elapsed(now, sampled) >= 10) {
        sampled = now;
        motion = imu.sample(now);
    }
    if (!imu.online() && elapsed(now, retry) >= 1500) {
        retry = now;
        imu.begin();
    }
    Event event;
    if (takeRelayed(event)) {
        // After accepting an authenticated relay, complete it even if the cane comes to rest.
        if (event.kind == Kind::Obstacle) event.side = Side::Both;
        device.play(event, now, true);
    }
    updateButtons(now);
    appControls(now);
    setClipReady(motion.sweeping && !device.lowBattery() && (!device.busy() || device.training()));
    if (beacon && (device.lowBattery() || elapsed(now, beaconAt) >= 60000)) {
        beacon = false;
        dirty = true;
    }
    if (sosPending && elapsed(now, sosAt) >= 120000) {
        sosPending = false;
        dirty = true;
    }
    digitalWrite(pins::beacon, beacon && elapsed(now, beaconAt) % 500 < 250);
    const bool app = appAllowed(now);
    device.showStatus(device.lowBattery() ? now % 350 < 120 : app ? now % 500 < 250 : true);
    if (dirty || elapsed(now, published) >= 500) {
        published = now;
        dirty = false;
        const uint8_t flags = uint8_t(motion.sweeping) | (uint8_t(beacon) << 1) | (uint8_t(app) << 2) |
            (uint8_t(device.lowBattery()) << 3) | (uint8_t(imu.online()) << 4);
        publishClip(flags, device.mode(), device.level(), device.batteryMv(), motion.roughness, sosPending ? sosId : 0);
    }
    handleCommand(now);
    delay(2);
}
