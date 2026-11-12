#include "link.h"

#include <NimBLEDevice.h>
#include <algorithm>
#include <atomic>
#include <cstring>
#include <esp_system.h>
#include <mbedtls/md.h>

namespace nova {
namespace {
constexpr char serviceId[] = "74cd0100-8b8c-4cc2-8ad4-5c1104b992d0";
constexpr char challengeId[] = "74cd0101-8b8c-4cc2-8ad4-5c1104b992d0";
constexpr char relayId[] = "74cd0102-8b8c-4cc2-8ad4-5c1104b992d0";
constexpr char ackId[] = "74cd0103-8b8c-4cc2-8ad4-5c1104b992d0";
constexpr char telemetryId[] = "74cd0104-8b8c-4cc2-8ad4-5c1104b992d0";
constexpr char controlId[] = "74cd0105-8b8c-4cc2-8ad4-5c1104b992d0";
constexpr size_t challengeBytes = 8, packetBytes = 16;
constexpr uint32_t challengeLifetime = 120, offerLifetime = 80;
constexpr uint8_t challengeDomain = 1, eventDomain = 2, ackDomain = 3;
LinkKey secret{};

int hexDigit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

void put32(uint8_t* destination, uint32_t value) {
    for (unsigned i = 0; i < 4; ++i) destination[i] = value >> (8 * i);
}

uint32_t get32(const uint8_t* source) {
    uint32_t result = 0;
    for (unsigned i = 0; i < 4; ++i) result |= uint32_t(source[i]) << (8 * i);
    return result;
}

bool sign(uint8_t domain, const uint8_t* challenge, const uint8_t* payload, size_t length, uint8_t* tag) {
    uint8_t input[17]{domain}, digest[32];
    memcpy(input + 1, challenge, challengeBytes);
    memcpy(input + 1 + challengeBytes, payload, length);
    const auto* sha = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
    if (!sha || mbedtls_md_hmac(sha, secret.data(), secret.size(), input, sizeof input, digest)) return false;
    memcpy(tag, digest, 8);
    return true;
}

bool authentic(uint8_t domain, const uint8_t* challenge, const uint8_t* payload, size_t length, const uint8_t* tag) {
    uint8_t expected[8];
    if (!sign(domain, challenge, payload, length, expected)) return false;
    uint8_t difference = 0;
    for (size_t i = 0; i < sizeof expected; ++i) difference |= expected[i] ^ tag[i];
    return difference == 0;
}
}

LinkKey loadKey(Preferences& store) {
    LinkKey key{};
    if (store.getBytesLength("key") == key.size()) store.getBytes("key", key.data(), key.size());
    return key;
}

bool hasKey(const LinkKey& key) {
    return std::any_of(key.begin(), key.end(), [](uint8_t byte) { return byte != 0; });
}

bool saveKey(Preferences& store, const String& hex) {
    if (hex == "off") return !store.isKey("key") || store.remove("key");
    LinkKey key{};
    if (hex.length() != key.size() * 2) return false;
    for (size_t i = 0; i < key.size(); ++i) {
        const int high = hexDigit(hex[2 * i]), low = hexDigit(hex[2 * i + 1]);
        if (high < 0 || low < 0) return false;
        key[i] = (high << 4) | low;
    }
    return hasKey(key) && store.putBytes("key", key.data(), key.size()) == key.size();
}

#ifdef NOVA_CHEST
namespace {
struct Request { Event event; uint32_t at; };
QueueHandle_t requests;
std::atomic<RelayResult> outcome{RelayResult::Local};
std::atomic<uint32_t> lastReady{0};
NimBLEAddress target;

bool readChallenge(NimBLERemoteCharacteristic& characteristic, uint8_t* nonce) {
    const auto data = characteristic.readValue();
    const auto* bytes = data.data();
    if (data.size() != 18 || bytes[0] != 1 || bytes[1] != 1 ||
        !authentic(challengeDomain, bytes + 2, bytes, 2, bytes + 10)) return false;
    memcpy(nonce, bytes + 2, challengeBytes);
    return true;
}

RelayResult sendRelay(const Request& request, NimBLERemoteCharacteristic& challenge,
                      NimBLERemoteCharacteristic& write, NimBLERemoteCharacteristic& ack) {
    uint8_t nonce[challengeBytes], packet[packetBytes]{};
    if (elapsed(millis(), request.at) >= offerLifetime || !readChallenge(challenge, nonce)) return RelayResult::Local;
    packet[0] = static_cast<uint8_t>(request.event.kind);
    packet[1] = static_cast<uint8_t>(request.event.side);
    packet[2] = request.event.distance & 255;
    packet[3] = request.event.distance >> 8;
    const uint32_t id = esp_random() | 1;
    put32(packet + 4, id);
    if (!sign(eventDomain, nonce, packet, 8, packet + 8) ||
        elapsed(millis(), request.at) >= offerLifetime) return RelayResult::Local;
    // The alert loop can cancel a request while discovery or the challenge read is stalled.
    auto waiting = RelayResult::Waiting;
    if (!outcome.compare_exchange_strong(waiting, RelayResult::Sending)) return RelayResult::Local;
    if (!write.writeValue(packet, sizeof packet, true)) return RelayResult::Ambiguous;
    const auto receipt = ack.readValue();
    if (receipt.size() != 12 || !authentic(ackDomain, nonce, receipt.data(), 4, receipt.data() + 4)) {
        return RelayResult::Ambiguous;
    }
    return get32(receipt.data()) == id ? RelayResult::Delivered : RelayResult::Local;
}

void clientTask(void*) {
    auto* client = NimBLEDevice::createClient();
    client->setConnectTimeout(2);
    client->setConnectionParams(9, 16, 0, 150);
    for (;;) {
        lastReady = 0;
        if (client->connect(target)) {
            auto* service = client->getService(serviceId);
            auto* challenge = service ? service->getCharacteristic(challengeId) : nullptr;
            auto* write = service ? service->getCharacteristic(relayId) : nullptr;
            auto* ack = service ? service->getCharacteristic(ackId) : nullptr;
            while (challenge && write && ack && client->isConnected()) {
                Request request;
                if (xQueueReceive(requests, &request, pdMS_TO_TICKS(120)) == pdTRUE) {
                    outcome = sendRelay(request, *challenge, *write, *ack);
                } else {
                    uint8_t nonce[challengeBytes];
                    lastReady = readChallenge(*challenge, nonce) ? millis() : 0;
                }
            }
            if (client->isConnected()) client->disconnect();
        }
        Request discarded;
        if (xQueueReceive(requests, &discarded, 0) == pdTRUE) outcome = RelayResult::Local;
        vTaskDelay(pdMS_TO_TICKS(1200));
    }
}
}

bool validPeer(const String& peer) {
    if (peer.length() != 17) return false;
    for (unsigned i = 0; i < peer.length(); ++i) {
        if (i % 3 == 2 ? peer[i] != ':' : hexDigit(peer[i]) < 0) return false;
    }
    return true;
}

void startLink(const String& peer, const LinkKey& key) {
    if (!validPeer(peer) || !hasKey(key)) return;
    secret = key;
    target = NimBLEAddress(peer.c_str(), BLE_ADDR_PUBLIC);
    requests = xQueueCreate(1, sizeof(Request));
    if (!requests) return;
    NimBLEDevice::init("NovaChest P1");
    if (xTaskCreate(clientTask, "nova-link", 6144, nullptr, 1, nullptr) != pdPASS) {
        vQueueDelete(requests);
        requests = nullptr;
    }
}

bool relayReady() {
    const uint32_t last = lastReady;
    const RelayResult state = outcome;
    return last && elapsed(millis(), last) < 300 &&
        state != RelayResult::Waiting && state != RelayResult::Sending && state != RelayResult::Cancelled;
}

bool offerRelay(Event event, uint32_t now) {
    if (!requests || !relayReady() || (event.kind != Kind::Obstacle && event.kind != Kind::Ground)) return false;
    outcome = RelayResult::Waiting;
    const Request request{event, now};
    if (xQueueSend(requests, &request, 0) == pdTRUE) return true;
    outcome = RelayResult::Local;
    return false;
}

RelayResult relayResult() { return outcome; }

bool cancelUnsentRelay() {
    auto waiting = RelayResult::Waiting;
    return outcome.compare_exchange_strong(waiting, RelayResult::Cancelled);
}

#else
namespace {
QueueHandle_t events, commands;
NimBLECharacteristic* telemetry;
NimBLEServer* clipServer;
std::atomic<bool> ready{false}, appWindow{false};
std::atomic<uint32_t> allowedAt{0};
uint8_t nonce[challengeBytes]{};
uint32_t nonceTime = 0, receipt = 0;
uint16_t nonceOwner = 0;
bool validNonce = false;

class Endpoint : public NimBLECharacteristicCallbacks {
    void onRead(NimBLECharacteristic* characteristic, ble_gap_conn_desc* connection) override {
        if (characteristic->getUUID() == NimBLEUUID(challengeId)) {
            uint8_t data[18]{1, uint8_t(ready && hasKey(secret))};
            esp_fill_random(nonce, sizeof nonce);
            memcpy(data + 2, nonce, sizeof nonce);
            nonceTime = millis();
            nonceOwner = connection->conn_handle;
            receipt = 0;
            validNonce = data[1] && sign(challengeDomain, nonce, data, 2, data + 10);
            if (!validNonce) data[1] = 0;
            characteristic->setValue(data, sizeof data);
        } else if (characteristic->getUUID() == NimBLEUUID(ackId)) {
            uint8_t data[12]{};
            if (nonceOwner == connection->conn_handle && hasKey(secret)) {
                put32(data, receipt);
                sign(ackDomain, nonce, data, 4, data + 4);
            }
            characteristic->setValue(data, sizeof data);
        }
    }

    void onWrite(NimBLECharacteristic* characteristic, ble_gap_conn_desc* connection) override {
        const auto value = characteristic->getValue();
        const auto* bytes = value.data();
        if (characteristic->getUUID() == NimBLEUUID(controlId)) {
            if (value.size() != 3 || bytes[0] != 1 || !appAllowed(millis())) return;
            const AppCommand command{bytes[1], bytes[2]};
            xQueueSend(commands, &command, 0);
            return;
        }
        if (!validNonce || nonceOwner != connection->conn_handle || !ready || value.size() != packetBytes ||
            elapsed(millis(), nonceTime) >= challengeLifetime) return;
        if (!authentic(eventDomain, nonce, bytes, 8, bytes + 8)) return;
        validNonce = false;
        const auto kind = static_cast<Kind>(bytes[0]);
        const uint16_t distance = bytes[2] | (uint16_t(bytes[3]) << 8);
        if ((kind != Kind::Obstacle && kind != Kind::Ground) || bytes[1] < 1 || bytes[1] > 3 || distance > 4000) return;
        const Event event{kind, static_cast<Side>(bytes[1]), distance};
        if (xQueueSend(events, &event, 0) == pdTRUE) receipt = get32(bytes + 4);
    }
} endpoint;

class ServerEvents : public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* server, ble_gap_conn_desc*) override {
        if (server->getConnectedCount() < 2) server->startAdvertising();
    }
} serverEvents;
}

void startClipBle(const LinkKey& key) {
    secret = key;
    events = xQueueCreate(1, sizeof(Event));
    commands = xQueueCreate(3, sizeof(AppCommand));
    if (!events || !commands) return;
    NimBLEDevice::init("NovaClip P1");
    auto* server = clipServer = NimBLEDevice::createServer();
    server->setCallbacks(&serverEvents, false);
    server->advertiseOnDisconnect(true);
    auto* service = server->createService(serviceId);
    service->createCharacteristic(challengeId, NIMBLE_PROPERTY::READ, 18)->setCallbacks(&endpoint);
    service->createCharacteristic(relayId, NIMBLE_PROPERTY::WRITE, packetBytes)->setCallbacks(&endpoint);
    service->createCharacteristic(ackId, NIMBLE_PROPERTY::READ, 12)->setCallbacks(&endpoint);
    telemetry = service->createCharacteristic(telemetryId, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY, 11);
    service->createCharacteristic(controlId, NIMBLE_PROPERTY::WRITE, 3)->setCallbacks(&endpoint);
    service->start();
    NimBLEDevice::getAdvertising()->addServiceUUID(serviceId);
    NimBLEDevice::getAdvertising()->setScanResponse(true);
    server->startAdvertising();
    Serial.printf("clip_mac=%s\n", NimBLEDevice::getAddress().toString().c_str());
}

void setClipReady(bool value) { ready = value; }
bool takeRelayed(Event& event) { return events && xQueueReceive(events, &event, 0) == pdTRUE; }
bool takeAppCommand(AppCommand& command) { return commands && xQueueReceive(commands, &command, 0) == pdTRUE; }

bool clipConnected() { return clipServer && clipServer->getConnectedCount() > 0; }

void allowApp(uint32_t now) {
    allowedAt = now;
    appWindow = true;
}

bool appAllowed(uint32_t now) {
    if (appWindow && elapsed(now, allowedAt) >= 60000) appWindow = false;
    return appWindow;
}

void publishClip(uint8_t flags, Mode mode, uint8_t level, uint16_t battery, uint8_t roughness, uint32_t sos) {
    if (!telemetry) return;
    uint8_t data[11]{1, flags, static_cast<uint8_t>(mode), level, uint8_t(battery), uint8_t(battery >> 8), roughness};
    put32(data + 7, sos);
    telemetry->setValue(data, sizeof data);
    telemetry->notify();
}
#endif
}
