#pragma once

#include <Arduino.h>
#include <Preferences.h>
#include <Wire.h>
#include "nova_core.h"

namespace nova {
class Device {
public:
    void begin();
    void tick(uint32_t now);
    bool play(Event event, uint32_t now, bool replaceTraining = false);
    void setLevel(unsigned level);
    void nextMode();
    Mode mode() const { return mode_; }
    uint8_t level() const { return level_; }
    uint16_t batteryMv() const { return battery_; }
    bool lowBattery() const { return low_; }
    bool usbPower() const { return usb_; }
    bool busy() const { return playing_.kind != Kind::None; }
    bool training() const { return training_; }
    void markTraining() { training_ = true; }
    void showStatus(bool on);
    String command();
    Preferences store;
private:
    uint16_t battery_ = 0;
    uint32_t sampled_ = 0, since_ = 0;
    uint8_t level_ = 1;
    bool usb_ = false, low_ = false, training_ = false;
    bool discardCommand_ = false;
    Mode mode_ = Mode::Walk;
    Event playing_;
    String input_;
};

struct Motion {
    float pitch = 0;
    float speed = 0;
    uint8_t roughness = 0;
    bool poseValid = false, sweeping = false;
};

class Imu {
public:
    explicit Imu(TwoWire& bus) : bus_(bus) {}
    void begin();
    Motion sample(uint32_t now);
    bool online() const { return ready_; }
private:
    bool write(uint8_t reg, uint8_t value);
    bool read(uint8_t reg, uint8_t* data, size_t size);
    TwoWire& bus_;
    uint32_t lastSample_ = 0, lastStep_ = 0, lastSwing_ = 0;
    float pitch_ = 0, cadence_ = 0, gravity_ = 1, roughness_ = 0;
    bool ready_ = false, pitchReady_ = false, stepHigh_ = false, stepped_ = false, swung_ = false;
};
}
