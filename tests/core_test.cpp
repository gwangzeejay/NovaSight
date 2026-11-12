#include "nova_core.h"

#include <cassert>
#include <iostream>

using namespace nova;

void testPulses() {
    const Event obstacle{Kind::Obstacle, Side::Left, 900};
    assert(pulseAt(obstacle, 0).level == 0);
    assert(pulseAt(obstacle, 35).level == 127);
    assert(pulseAt(obstacle, 70).level == 255);
    assert(pulseAt(obstacle, 249).side == Side::Left);
    assert(pulseAt(obstacle, 250).finished);
    const Event ground{Kind::Ground};
    for (uint32_t time : {75, 225, 375}) assert(pulseAt(ground, time).level == 255);
    for (uint32_t time : {85, 235}) assert(pulseAt(ground, time).level == 0);
    assert(pulseAt(ground, 380).finished);
    assert(pulseAt({Kind::Uncertain}, 150).level == pulseAt({Kind::Uncertain}, 450).level);
    assert(pulseAt({Kind::Uncertain}, 600).finished);
    assert(pulseAt({Kind::Confirm, Side::Both, 0, 3}, 400).finished);
    // No-phone SOS cue: three 220 ms pulses, clearly longer than the 80 ms confirmation taps.
    const Event noLink{Kind::NoLink};
    for (uint32_t time : {100, 540, 980}) assert(pulseAt(noLink, time).level == 255);
    for (uint32_t time : {250, 690}) assert(pulseAt(noLink, time).level == 0 && !pulseAt(noLink, time).finished);
    assert(pulseAt(noLink, 1100).finished);
    for (const uint16_t rail : {3600, 4200, 4700}) {
        assert(motorDuty(255, 1, rail) < motorDuty(255, 2, rail));
        assert(motorDuty(255, 2, rail) < motorDuty(255, 3, rail));
        assert(motorDuty(255, 3, rail) * rail <= 255 * 3000);
    }
}

void testButton() {
    Button button;
    button.update(true, 100);
    button.update(false, 110);
    assert(!button.released());
    button.update(true, 150);
    button.update(true, 181);
    assert(!button.held(3000, 3149));
    assert(button.held(3000, 3150));
    assert(!button.held(3000, 3200));
    button.update(false, 3250);
    button.update(false, 3280);
    assert(!button.released());
    button.update(true, 3300);
    button.update(true, 3340);
    button.update(false, 3350);
    button.update(false, 3380);
    assert(button.released());
}

void testRange() {
    RangeTrack range;
    assert(obstacleLimit(Mode::Walk, 2) == 2500);
    assert(obstacleLimit(Mode::Crowd, 2) == 1200);
    assert(obstacleLimit(Mode::Indoor, 2) == 1000);
    range.add(1500, 1600, 100);
    range.add(1450, 1600, 200);
    assert(!range.active(200));
    range.add(1380, 1600, 300);
    assert(range.active(300));
    assert(!range.active(520));
    range.add(0, 1600, 560);
    assert(!range.active(560) && range.alive(560));
    assert(!range.alive(3800));
    range.add(900, 1600, UINT32_MAX - 10);
    assert(range.active(7));
    range.add(100, 1600, 10);
    assert(!range.active(10));
}

void testFloor() {
    Calibrator calibrator;
    FloorFrame frame;
    frame.mm.fill(1800);
    frame.status.fill(5);
    assert(!calibrator.add(frame));
    frame.poseValid = true;
    for (unsigned i = 0; i < 19; ++i) assert(!calibrator.add(frame));
    assert(calibrator.add(frame));
    const FloorCalibration calibration = calibrator.result();
    assert(calibration.valid() && calibration.mm[4] == 1800);
    FloorTrack floor;
    assert(floor.update(calibration, frame).reliable);
    frame.mm[5] = 2200;
    frame.taken = 50;
    assert(!floor.update(calibration, frame).hazardMm);
    frame.mm[6] = 2200;
    for (uint32_t time : {100, 150}) {
        frame.taken = time;
        assert(!floor.update(calibration, frame).hazardMm);
    }
    frame.taken = 200;
    assert(floor.update(calibration, frame).hazardMm > 900);
    frame.taken = 500;
    assert(!floor.update(calibration, frame).hazardMm);
    frame.status.fill(9);
    assert(!floor.update(calibration, frame).reliable);
    frame.status.fill(5);
    frame.pitch = 14;
    assert(!floor.update(calibration, frame).reliable);
}

int main() {
    testPulses();
    testButton();
    testRange();
    testFloor();
    std::cout << "NovaSight core checks passed\n";
}
