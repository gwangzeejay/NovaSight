#include "device.h"
#include "pins.h"

#include <algorithm>
#include <cmath>

namespace nova {
namespace {
constexpr int leftChannel = 4, rightChannel = 5; // Separate LEDC timer from camera XCLK.
constexpr int pwmHz = 22000, pwmBits = 8;
constexpr uint8_t imuAddress = 0x68;

int16_t word(const uint8_t* bytes) {
    return static_cast<int16_t>(uint16_t(bytes[0]) << 8 | bytes[1]);
}
}

void Device::begin() {
    pinMode(pins::motorLeft, OUTPUT);
    pinMode(pins::motorRight, OUTPUT);
    digitalWrite(pins::motorLeft, LOW);
    digitalWrite(pins::motorRight, LOW);
    ledcSetup(leftChannel, pwmHz, pwmBits);
    ledcSetup(rightChannel, pwmHz, pwmBits);
    ledcAttachPin(pins::motorLeft, leftChannel);
    ledcAttachPin(pins::motorRight, rightChannel);
    ledcWrite(leftChannel, 0);
    ledcWrite(rightChannel, 0);
    pinMode(pins::status, OUTPUT);
    showStatus(false);
    pinMode(pins::mode, INPUT);
    pinMode(pins::vbus, INPUT);
    analogSetPinAttenuation(pins::battery, ADC_11db);
    store.begin("novasight", false);
    level_ = std::clamp<uint8_t>(store.getUChar("level", 1), 1, 3);
    mode_ = static_cast<Mode>(std::min<uint8_t>(store.getUChar("mode", 0), 2));
    sampled_ = millis() - 250;
}

void Device::showStatus(bool on) { digitalWrite(pins::status, on == pins::statusOn); }

void Device::tick(uint32_t now) {
    usb_ = digitalRead(pins::vbus);
    if (elapsed(now, sampled_) >= 250) {
        sampled_ = now;
        uint32_t raw = 0;
        for (int i = 0; i < 4; ++i) raw += analogReadMilliVolts(pins::battery);
        const uint16_t measured = raw / 2; // 470k/470k divider, mean of four reads.
        battery_ = measured >= 2000 && measured <= 4550 ? measured : 0;
        if (!battery_ || battery_ < 3500) low_ = true;
        if (battery_ >= 3650) low_ = false;
    }
    const Pulse pulse = pulseAt(playing_, elapsed(now, since_));
    if (pulse.finished || low_) {
        playing_ = {};
        training_ = false;
    }
    uint8_t level = level_;
    if (playing_.kind == Kind::NoLink) level = 3;
    else if (mode_ == Mode::Indoor || playing_.kind == Kind::Confirm) level = 1;
    else if (playing_.kind == Kind::Obstacle && playing_.distance < 1000 && level < 3 && !training_) ++level;
    uint16_t rail = std::max<uint16_t>(battery_ + 100, 4200);
#ifdef NOVA_CLIP
    if (usb_) rail = std::max<uint16_t>(rail, 4700);
#endif
    const auto duty = playing_.kind == Kind::None ? 0 : motorDuty(pulse.level, level, rail);
    const auto side = static_cast<uint8_t>(pulse.side);
    ledcWrite(leftChannel, (side & 1) ? duty : 0);
    ledcWrite(rightChannel, (side & 2) ? duty : 0);
}

bool Device::play(Event event, uint32_t now, bool replaceTraining) {
    if (low_ || (busy() && !(replaceTraining && training_))) return false;
    playing_ = event;
    since_ = now;
    training_ = false;
    return true;
}

void Device::setLevel(unsigned level) {
    if (level < 1 || level > 3 || level == level_) return;
    if (store.putUChar("level", level) == 1) level_ = level;
}

void Device::nextMode() {
    mode_ = static_cast<Mode>((static_cast<uint8_t>(mode_) + 1) % 3);
    store.putUChar("mode", static_cast<uint8_t>(mode_));
}

String Device::command() {
    for (unsigned i = 0; i < 96 && Serial.available(); ++i) {
        const char byte = Serial.read();
        if (byte == '\r' || byte == '\n') {
            String result = discardCommand_ ? String() : input_;
            input_.clear();
            discardCommand_ = false;
            result.trim();
            if (!result.isEmpty()) return result;
        } else if (!discardCommand_) {
            if (input_.length() < 80) input_ += byte;
            else discardCommand_ = true;
        }
    }
    return {};
}

bool Imu::write(uint8_t reg, uint8_t value) {
    bus_.beginTransmission(imuAddress);
    bus_.write(reg);
    bus_.write(value);
    return bus_.endTransmission() == 0;
}

bool Imu::read(uint8_t reg, uint8_t* data, size_t size) {
    bus_.beginTransmission(imuAddress);
    bus_.write(reg);
    if (bus_.endTransmission(false) || bus_.requestFrom(imuAddress, size) != size) return false;
    for (size_t i = 0; i < size; ++i) data[i] = bus_.read();
    return true;
}

void Imu::begin() {
    uint8_t id;
    ready_ = read(0x75, &id, 1) && id == 0x68 &&
        write(0x6B, 0x01) && write(0x1A, 0x03) && write(0x19, 0x09) &&
        write(0x1B, 0x00) && write(0x1C, 0x00);
    pitchReady_ = false;
}

Motion Imu::sample(uint32_t now) {
    uint8_t data[14];
    if (!ready_ || !read(0x3B, data, sizeof data)) {
        ready_ = false;
        return {};
    }
    const float ax = word(data) / 16384.0f;
    const float ay = word(data + 2) / 16384.0f;
    const float az = word(data + 4) / 16384.0f;
    const float gx = word(data + 8) / 131.0f;
    const float gy = word(data + 10) / 131.0f;
    const float gz = word(data + 12) / 131.0f;
    const float norm = std::sqrt(ax * ax + ay * ay + az * az);
    const float angular = std::sqrt(gx * gx + gy * gy + gz * gz);
    // P1 bench orientation. Confirm the axis/sign with the ToF grid before calibration.
    const float measuredPitch = std::atan2(ax, std::hypot(ay, az)) * 57.29578f;
    const bool poseValid = norm > 0.78f && norm < 1.22f && angular < 140.0f;
    if (poseValid) {
        pitch_ = pitchReady_ && elapsed(now, lastSample_) < 180 ? 0.85f * pitch_ + 0.15f * measuredPitch : measuredPitch;
        pitchReady_ = true;
    }
    lastSample_ = now;
    gravity_ = 0.96f * gravity_ + 0.04f * norm;
    const float highPass = norm - gravity_;
    if (highPass > 0.11f && !stepHigh_ && (!stepped_ || elapsed(now, lastStep_) > 270)) {
        const auto interval = elapsed(now, lastStep_);
        if (stepped_ && interval < 1400) cadence_ = 0.7f * cadence_ + 0.3f * (1000.0f / interval);
        else cadence_ = 0;
        stepped_ = true;
        lastStep_ = now;
        stepHigh_ = true;
    } else if (highPass < 0.035f) {
        stepHigh_ = false;
    }
    if (angular > 38.0f) {
        lastSwing_ = now;
        swung_ = true;
    }
    const bool sweeping = swung_ && elapsed(now, lastSwing_) < 1000;
    roughness_ = sweeping ? 0.94f * roughness_ + 0.06f * std::abs(highPass) : 0;
    const float speed = stepped_ && elapsed(now, lastStep_) < 1450 ? std::min(2.2f, 0.65f * cadence_) : 0;
    return {pitch_, speed, static_cast<uint8_t>(std::min(100.0f, 300.0f * roughness_)), poseValid, sweeping};
}
}
