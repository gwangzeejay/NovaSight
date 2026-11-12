#pragma once

namespace pins {
#if defined(NOVA_CHEST)
constexpr int sda = 2, scl = 14, imuInt = 47;
constexpr int motorLeft = 45, motorRight = 46, mode = 3;
constexpr int status = 48, battery = 1, vbus = 44;
constexpr bool statusOn = true;
constexpr int triggerLeft = 21, echoLeft = 38, triggerRight = 39, echoRight = 40;
constexpr int tofEnable = 41, tofInt = 42;
constexpr int camSda = 4, camScl = 5, camVsync = 6, camHref = 7;
constexpr int camXclk = 15, camPclk = 13;
constexpr int camData[] = {11, 9, 8, 10, 12, 18, 17, 16};
#elif defined(NOVA_CLIP)
constexpr int sda = 4, scl = 5, imuInt = 1;
constexpr int motorLeft = 6, motorRight = 7, mode = 10;
constexpr int status = 8, battery = 0, vbus = 21;
constexpr bool statusOn = false;
constexpr int route = 2, sos = 20, beacon = 3;
#endif
}
