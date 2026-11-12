#pragma once

#include <Arduino.h>
#include <Preferences.h>
#include "nova_core.h"

namespace nova {
using LinkKey = std::array<uint8_t, 16>;
LinkKey loadKey(Preferences& store);
bool saveKey(Preferences& store, const String& hex);
bool hasKey(const LinkKey& key);

enum class RelayResult : uint8_t { Waiting, Sending, Cancelled, Delivered, Local, Ambiguous };

#ifdef NOVA_CHEST
void startLink(const String& peer, const LinkKey& key);
bool validPeer(const String& peer);
bool offerRelay(Event event, uint32_t now);
RelayResult relayResult();
bool cancelUnsentRelay();
bool relayReady();
#else
struct AppCommand { uint8_t op, value; };
void startClipBle(const LinkKey& key);
void setClipReady(bool ready);
bool takeRelayed(Event& event);
bool takeAppCommand(AppCommand& command);
bool clipConnected();
void allowApp(uint32_t now);
bool appAllowed(uint32_t now);
void publishClip(uint8_t flags, Mode mode, uint8_t level, uint16_t battery, uint8_t roughness, uint32_t sos);
#endif
}
