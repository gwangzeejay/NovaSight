#pragma once

#include <array>
#include <cstddef>
#include <cstdint>

namespace nova {
constexpr uint32_t elapsed(uint32_t now, uint32_t since) { return now - since; }

enum class Mode : uint8_t { Walk, Crowd, Indoor };
enum class Kind : uint8_t { None, Obstacle, Ground, Uncertain, Confirm, NoLink };
enum class Side : uint8_t { Left = 1, Right = 2, Both = 3 };

struct Event {
    Kind kind = Kind::None;
    Side side = Side::Both;
    uint16_t distance = 0;
    uint8_t pulses = 1;
};

struct Pulse {
    uint8_t level;
    Side side;
    bool finished;
};

Pulse pulseAt(Event event, uint32_t age);
uint16_t motorDuty(uint8_t amplitude, uint8_t level, uint16_t railMv);
uint16_t obstacleLimit(Mode mode, float speedMps);
uint32_t repeatInterval(Event event);

class Button {
public:
    void update(bool down, uint32_t now);
    bool released() const { return released_; }
    bool held(uint32_t duration, uint32_t now);
private:
    bool raw_ = false, stable_ = false, long_ = false, released_ = false;
    uint32_t changed_ = 0, pressed_ = 0;
};

class RangeTrack {
public:
    void add(uint16_t mm, uint16_t limit, uint32_t now);
    bool active(uint32_t now) const;
    bool alive(uint32_t now) const;
    uint16_t distance() const { return distance_; }
private:
    uint32_t sample_ = 0, lastEcho_ = 0;
    uint16_t distance_ = 0;
    uint8_t count_ = 0;
    bool seen_ = false;
};

constexpr std::size_t zones = 16;
struct FloorFrame {
    std::array<uint16_t, zones> mm{};
    std::array<uint8_t, zones> status{};
    float pitch = 0;
    bool poseValid = false;
    uint32_t taken = 0;
};

struct FloorCalibration {
    std::array<uint16_t, zones> mm{};
    float pitch = 0;
    uint32_t version = 1;
    bool valid() const;
};

class Calibrator {
public:
    bool add(const FloorFrame& frame);
    FloorCalibration result() const;
    unsigned count() const { return count_; }
private:
    std::array<uint32_t, zones> sums_{};
    std::array<uint16_t, zones> first_{};
    std::array<uint8_t, zones> samples_{};
    float pitchSum_ = 0, firstPitch_ = 0;
    unsigned count_ = 0;
};

struct FloorResult {
    bool reliable = false;
    uint16_t hazardMm = 0;
};

class FloorTrack {
public:
    FloorResult update(const FloorCalibration& calibration, const FloorFrame& frame);
    void reset();
private:
    uint32_t last_ = 0;
    uint16_t distance_ = 0;
    int8_t sign_ = 0;
    uint8_t count_ = 0;
};
}
