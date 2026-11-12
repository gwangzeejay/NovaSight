"""Keep ST's pinned ULD, with bounded ESP32 Wire transfers on I2C faults."""

from pathlib import Path

Import("env")

header = (
    Path(env.subst("$PROJECT_LIBDEPS_DIR")) / env.subst("$PIOENV")
    / "STM32duino VL53L8CX" / "src" / "vl53l8cx.h"
)
marker = "// NovaSight bounded I2C transport"
source = header.read_text(encoding="utf-8")

if marker not in source:
    read = source.index("    uint8_t IO_Read(")
    begin = source.index("      if (dev_i2c) {", read)
    end = source.index("      if (dev_spi) {", begin)
    source = source[:begin] + """      // NovaSight bounded I2C transport
      if (dev_i2c) {
        const uint8_t address = (_dev.platform.address >> 1) & 0x7F;
        for (uint32_t i = 0; i < size;) {
          const uint16_t reg = RegisterAddress + i;
          const uint8_t count = size - i > 128 ? 128 : size - i;
          dev_i2c->beginTransmission(address);
          dev_i2c->write(reg >> 8);
          dev_i2c->write(reg & 0xFF);
          if (dev_i2c->endTransmission(false) ||
              dev_i2c->requestFrom(address, size_t(count)) != count) return 1;
          for (uint8_t n = 0; n < count; ++n) p_values[i++] = dev_i2c->read();
        }
        return 0;
      }
""" + source[end:]
    write = source.index("    uint8_t IO_Write(")
    begin = source.index("      if (dev_i2c) {", write)
    end = source.index("      if (dev_spi) {", begin)
    source = source[:begin] + """      if (dev_i2c) {
        const uint8_t address = (_dev.platform.address >> 1) & 0x7F;
        for (uint32_t i = 0; i < size;) {
          const uint16_t reg = RegisterAddress + i;
          const uint8_t count = size - i > 128 ? 128 : size - i;
          dev_i2c->beginTransmission(address);
          dev_i2c->write(reg >> 8);
          dev_i2c->write(reg & 0xFF);
          const size_t written = dev_i2c->write(p_values + i, count);
          if (dev_i2c->endTransmission(true) || written != count) return 1;
          i += count;
        }
        return 0;
      }
""" + source[end:]
    header.write_text(source, encoding="utf-8")
