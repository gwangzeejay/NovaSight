#pragma once

#include "device.h"

namespace nova {
struct RangeSample { bool left; uint16_t distance; };
void startUltrasound();
bool pollUltrasound(RangeSample& sample);
bool startFloorSensors(bool enableTof);
bool takeFloor(FloorFrame& frame);
Motion chestMotion();
bool startCameraDiagnostic();
void pauseCamera(bool paused);
size_t cameraBytes();
}
