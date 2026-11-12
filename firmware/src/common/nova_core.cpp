#include "nova_core.h"

#include <algorithm>
#include <cmath>

namespace nova {
namespace {
template <typename T>
T bounded(T value, T low, T high) {
    return std::min(std::max(value, low), high);
}
}

Pulse pulseAt(Event event, uint32_t age) {
    uint32_t on = 0, period = 0, duration = 0;
    switch (event.kind) {
        case Kind::Obstacle: on = period = duration = 250; break;
        case Kind::Ground: on = 80; period = 150; duration = 380; break;
        case Kind::Uncertain: on = period = duration = 600; break;
        case Kind::Confirm:
            on = 80; period = 160; duration = period * bounded<uint8_t>(event.pulses, 1, 3) - 80;
            break;
        // SOS recorded but no phone is connected: three long pulses, unlike the 80 ms confirmation taps.
        case Kind::NoLink: on = 220; period = 440; duration = period * 3 - 220; break;
        case Kind::None: return {0, event.side, true};
    }
    if (age >= duration) return {0, event.side, true};
    const auto phase = age % period;
    if (phase >= on) return {0, event.side, false};
    const auto ramp = event.kind == Kind::Uncertain ? std::min(phase, on - phase) : phase;
    const uint32_t rise = event.kind == Kind::Uncertain ? 300 : 70;
    return {static_cast<uint8_t>(std::min(ramp, rise) * 255 / rise), event.side, false};
}

uint16_t motorDuty(uint8_t amplitude, uint8_t level, uint16_t railMv) {
    const uint32_t fraction[] = {70, 85, 100};
    const uint32_t supply = std::max<uint16_t>(railMv, 3000);
    return static_cast<uint16_t>(amplitude * fraction[bounded<uint8_t>(level, 1, 3) - 1] * 30 / supply);
}

uint16_t obstacleLimit(Mode mode, float speedMps) {
    if (mode == Mode::Indoor) return 1000;
    if (mode == Mode::Crowd) return 1200;
    if (!std::isfinite(speedMps)) return 1600;
    return static_cast<uint16_t>(bounded(1200.0f * speedMps + 300.0f, 1500.0f, 2500.0f));
}

uint32_t repeatInterval(Event event) {
    if (event.kind == Kind::Uncertain) return 1700;
    if (event.kind == Kind::Ground) return 1150;
    return bounded<uint32_t>(event.distance / 2, 350, 1250);
}

void Button::update(bool down, uint32_t now) {
    released_ = false;
    if (down != raw_) {
        raw_ = down;
        changed_ = now;
    }
    if (raw_ == stable_ || elapsed(now, changed_) < 30) return;
    stable_ = raw_;
    if (stable_) {
        pressed_ = changed_;
        long_ = false;
    } else {
        released_ = !long_;
    }
}

bool Button::held(uint32_t duration, uint32_t now) {
    if (!stable_ || !raw_ || long_ || elapsed(now, pressed_) < duration) return false;
    long_ = true;
    return true;
}

void RangeTrack::add(uint16_t mm, uint16_t limit, uint32_t now) {
    if (elapsed(now, sample_) > 220) count_ = 0;
    sample_ = now;
    if (mm) {
        seen_ = true;
        lastEcho_ = now;
    }
    if (mm < 220 || mm > limit) {
        count_ = 0;
        distance_ = 0;
        return;
    }
    if (mm > distance_ + 120 || mm + 400 < distance_) count_ = 0;
    distance_ = mm;
    if (count_ < 3) ++count_;
}

bool RangeTrack::active(uint32_t now) const {
    return distance_ && (distance_ < 1000 || count_ >= 3) && elapsed(now, sample_) < 220;
}

bool RangeTrack::alive(uint32_t now) const {
    return seen_ && elapsed(now, lastEcho_) < 3500;
}

namespace {
bool floorSample(const FloorFrame& frame, size_t i) {
    return frame.status[i] == 5 && frame.mm[i] >= 200 && frame.mm[i] <= 4000;
}
}

bool FloorCalibration::valid() const {
    return version == 1 && std::isfinite(pitch) && std::abs(pitch) <= 180 &&
        std::count_if(mm.begin(), mm.end(), [](auto value) { return value >= 250 && value <= 3900; }) >= 10;
}

bool Calibrator::add(const FloorFrame& frame) {
    if (!frame.poseValid || !std::isfinite(frame.pitch) || std::abs(frame.pitch) > 180) return false;
    if (!count_) firstPitch_ = frame.pitch;
    if (std::abs(frame.pitch - firstPitch_) > 3) return false;
    unsigned stable = 0;
    for (size_t i = 0; i < zones; ++i) {
        if (floorSample(frame, i) && (!first_[i] || std::abs(int(frame.mm[i]) - int(first_[i])) < 130)) ++stable;
    }
    if (stable < 10) return false;
    for (size_t i = 0; i < zones; ++i) {
        if (!floorSample(frame, i)) continue;
        if (!first_[i]) first_[i] = frame.mm[i];
        if (std::abs(int(frame.mm[i]) - int(first_[i])) >= 130) continue;
        sums_[i] += frame.mm[i];
        ++samples_[i];
    }
    pitchSum_ += frame.pitch;
    return ++count_ >= 20;
}

FloorCalibration Calibrator::result() const {
    FloorCalibration calibration;
    if (count_ < 20) return calibration;
    calibration.pitch = pitchSum_ / count_;
    for (size_t i = 0; i < zones; ++i) {
        if (samples_[i] >= 16) calibration.mm[i] = sums_[i] / samples_[i];
    }
    return calibration;
}

FloorResult FloorTrack::update(const FloorCalibration& calibration, const FloorFrame& frame) {
    const float delta = frame.pitch - calibration.pitch;
    if (!calibration.valid() || !frame.poseValid || !std::isfinite(delta) || std::abs(delta) > 12) {
        reset();
        return {};
    }
    if (elapsed(frame.taken, last_) > 200) reset();
    last_ = frame.taken;
    unsigned healthy = 0;
    std::array<int8_t, zones> change{};
    std::array<uint16_t, zones> distance{};
    for (size_t i = 0; i < zones; ++i) {
        if (calibration.mm[i] < 250 || calibration.mm[i] > 3900 || !floorSample(frame, i)) continue;
        ++healthy;
        constexpr float radians = 0.017453293f;
        // VL53L8CX 4x4 covers 45 degrees, so adjacent rows are 11.25 degrees apart.
        const float nominal = 35.0f + (1.5f - float(i / 4)) * 11.25f;
        const float angle = (nominal + delta) * radians;
        const float vertical = std::sin(angle);
        if (vertical < 0.08f) continue;
        const float expected = calibration.mm[i] * std::sin(nominal * radians) / vertical;
        const float heightChange = (expected - frame.mm[i]) * vertical;
        // A drop is evaluated at the expected edge, not at the deeper return.
        const float forward = std::min<float>(expected, frame.mm[i]) * std::cos(angle);
        if (std::abs(heightChange) < 125 || forward < 550 || forward > 3000) continue;
        change[i] = heightChange > 0 ? 1 : -1;
        distance[i] = static_cast<uint16_t>(forward);
    }
    uint16_t nearest = 0;
    int8_t sign = 0;
    for (size_t i = 0; i < zones; ++i) {
        if (!change[i]) continue;
        const bool next = i % 4 != 3 && change[i + 1] == change[i];
        const bool above = i + 4 < zones && change[i + 4] == change[i];
        if ((next || above) && (!nearest || distance[i] < nearest)) {
            nearest = distance[i];
            sign = change[i];
        }
    }
    if (healthy < 6 || !nearest || sign != sign_ || nearest > distance_ + 150 || nearest + 450 < distance_) count_ = 0;
    if (healthy >= 6 && nearest && count_ < 3) ++count_;
    distance_ = nearest;
    sign_ = sign;
    return {healthy >= 6, static_cast<uint16_t>(count_ >= 3 ? nearest : 0)};
}

void FloorTrack::reset() {
    count_ = 0;
    distance_ = 0;
    sign_ = 0;
}
}
