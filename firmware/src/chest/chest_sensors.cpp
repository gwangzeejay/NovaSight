#include "chest_sensors.h"
#include "pins.h"

#include <atomic>
#include <esp_camera.h>
#include <vl53l8cx.h>

namespace nova {
namespace {
constexpr int trigger[] = {pins::triggerLeft, pins::triggerRight};
constexpr int echo[] = {pins::echoLeft, pins::echoRight};
constexpr uint32_t triggerPeriod = 50, echoTimeoutUs = 40000;
portMUX_TYPE echoLock = portMUX_INITIALIZER_UNLOCKED;
volatile int armed = -1;
volatile uint32_t rising = 0, width = 0;
volatile bool sawRise = false, complete = false;
uint32_t launchedAt, lastTrigger;
int emitter = 1;
bool inFlight = false;
QueueHandle_t frames, motionSamples;
std::atomic<bool> cameraPaused{false};
std::atomic<size_t> imageSize{0};

void IRAM_ATTR captureEcho(void* argument) {
    const int channel = static_cast<int>(reinterpret_cast<intptr_t>(argument));
    portENTER_CRITICAL_ISR(&echoLock);
    if (armed == channel && !complete) {
        const uint32_t now = micros();
        if (digitalRead(echo[channel])) {
            rising = now;
            sawRise = true;
        } else if (sawRise) {
            width = elapsed(now, rising);
            complete = true;
        }
    }
    portEXIT_CRITICAL_ISR(&echoLock);
}

void sensorTask(void* arg) {
    const bool enableTof = arg != nullptr;
    Wire.begin(pins::sda, pins::scl, 400000);
    Wire.setBufferSize(256);
    Wire.setTimeOut(12);
    Imu imu(Wire);
    VL53L8CX tof(&Wire, pins::tofEnable);
    VL53L8CX_ResultsData data{};
    uint32_t imuAt = millis() - 10, imuRetry = millis() - 1500;
    uint32_t tofRetry = millis() - 5000, lastFrame = millis();
    bool ranging = false;
    Motion motion;
    for (;;) {
        uint32_t now = millis();
        if (enableTof && !ranging && elapsed(now, tofRetry) >= 5000) {
            tof.begin();
            uint8_t alive = 0;
            ranging = !tof.is_alive(&alive) && alive && !tof.init() &&
                !tof.set_resolution(VL53L8CX_RESOLUTION_4X4) && !tof.set_ranging_frequency_hz(20) &&
                !tof.start_ranging();
            now = millis();
            tofRetry = lastFrame = now;
            Serial.printf("tof=%s\n", ranging ? "ranging" : "offline");
        }
        if (elapsed(now, imuRetry) >= 1500) {
            imuRetry = now;
            if (!imu.online()) imu.begin();
        }
        if (elapsed(now, imuAt) >= 10) {
            imuAt = now;
            motion = imu.sample(now);
            xQueueOverwrite(motionSamples, &motion);
        }
        if (ranging) {
            uint8_t ready = 0;
            if (!tof.check_data_ready(&ready) && ready && !tof.get_ranging_data(&data)) {
                FloorFrame frame;
                frame.pitch = motion.pitch;
                frame.poseValid = motion.poseValid;
                frame.taken = lastFrame = millis();
                for (size_t i = 0; i < zones; ++i) {
                    const size_t index = i * VL53L8CX_NB_TARGET_PER_ZONE;
                    frame.mm[i] = data.distance_mm[index] > 0 ? data.distance_mm[index] : 0;
                    frame.status[i] = data.nb_target_detected[i] ? data.target_status[index] : 255;
                }
                xQueueOverwrite(frames, &frame);
            }
            if (elapsed(millis(), lastFrame) >= 1000) {
                tof.stop_ranging();
                ranging = false;
                tofRetry = millis();
            }
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
}

void cameraTask(void*) {
    bool active = false;
    for (;;) {
        if (cameraPaused) {
            if (active) esp_camera_deinit();
            active = false;
            imageSize = 0;
            vTaskDelay(pdMS_TO_TICKS(250));
            continue;
        }
        if (!active) {
            camera_config_t config{};
            config.pin_pwdn = config.pin_reset = -1;
            config.pin_xclk = pins::camXclk;
            config.pin_sccb_sda = pins::camSda;
            config.pin_sccb_scl = pins::camScl;
            config.pin_d0 = pins::camData[0];
            config.pin_d1 = pins::camData[1];
            config.pin_d2 = pins::camData[2];
            config.pin_d3 = pins::camData[3];
            config.pin_d4 = pins::camData[4];
            config.pin_d5 = pins::camData[5];
            config.pin_d6 = pins::camData[6];
            config.pin_d7 = pins::camData[7];
            config.pin_vsync = pins::camVsync;
            config.pin_href = pins::camHref;
            config.pin_pclk = pins::camPclk;
            config.xclk_freq_hz = 20000000;
            config.ledc_timer = LEDC_TIMER_0;
            config.ledc_channel = LEDC_CHANNEL_0;
            config.pixel_format = PIXFORMAT_JPEG;
            config.frame_size = FRAMESIZE_QVGA;
            config.jpeg_quality = 16;
            config.fb_count = 1;
            config.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
            config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
            const esp_err_t result = esp_camera_init(&config);
            auto* sensor = result == ESP_OK ? esp_camera_sensor_get() : nullptr;
            if (!sensor || sensor->id.PID != OV5640_PID) {
                if (result == ESP_OK) esp_camera_deinit();
                Serial.printf("camera=offline error=0x%x\n", unsigned(result));
                vTaskDelay(pdMS_TO_TICKS(3000));
                continue;
            }
            active = true;
            Serial.printf("camera=OV5640 pid=0x%x\n", sensor->id.PID);
        }
        auto* frame = esp_camera_fb_get();
        imageSize = frame && frame->format == PIXFORMAT_JPEG && frame->len >= 4 &&
            frame->buf[0] == 0xff && frame->buf[1] == 0xd8 ? frame->len : 0;
        if (frame) esp_camera_fb_return(frame);
        vTaskDelay(pdMS_TO_TICKS(210));
    }
}
}

void startUltrasound() {
    for (intptr_t i = 0; i < 2; ++i) {
        pinMode(trigger[i], OUTPUT);
        digitalWrite(trigger[i], LOW);
        pinMode(echo[i], INPUT);
        attachInterruptArg(echo[i], captureEcho, reinterpret_cast<void*>(i), CHANGE);
    }
    lastTrigger = millis() - triggerPeriod;
}

bool pollUltrasound(RangeSample& sample) {
    const uint32_t now = millis();
    if (inFlight) {
        portENTER_CRITICAL(&echoLock);
        const bool done = complete || elapsed(micros(), launchedAt) >= echoTimeoutUs;
        const uint32_t pulse = complete ? width : 0;
        if (done) armed = -1;
        portEXIT_CRITICAL(&echoLock);
        if (!done) return false;
        inFlight = false;
        const uint32_t mm = pulse * 343 / 2000;
        sample = {emitter == 0, static_cast<uint16_t>(mm >= 220 && mm <= 5000 ? mm : 0)};
        return true;
    }
    if (elapsed(now, lastTrigger) < triggerPeriod) return false;
    emitter ^= 1;
    lastTrigger = now;
    launchedAt = micros();
    portENTER_CRITICAL(&echoLock);
    sawRise = complete = false;
    armed = emitter;
    portEXIT_CRITICAL(&echoLock);
    inFlight = true;
    digitalWrite(trigger[emitter], HIGH);
    delayMicroseconds(15);
    digitalWrite(trigger[emitter], LOW);
    return false;
}

bool startFloorSensors(bool enableTof) {
    frames = xQueueCreate(1, sizeof(FloorFrame));
    motionSamples = xQueueCreate(1, sizeof(Motion));
    return frames && motionSamples &&
        xTaskCreate(sensorTask, "nova-sensors", 12288, enableTof ? &frames : nullptr, 1, nullptr) == pdPASS;
}

bool takeFloor(FloorFrame& frame) { return frames && xQueueReceive(frames, &frame, 0) == pdTRUE; }

Motion chestMotion() {
    Motion motion{};
    if (motionSamples) xQueuePeek(motionSamples, &motion, 0);
    return motion;
}

bool startCameraDiagnostic() {
    return xTaskCreate(cameraTask, "nova-camera", 6144, nullptr, 1, nullptr) == pdPASS;
}

void pauseCamera(bool paused) { cameraPaused = paused; }
size_t cameraBytes() { return imageSize; }
}
