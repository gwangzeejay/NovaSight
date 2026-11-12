# NovaChest · Camera OV5640

NovaChest dùng **cụm camera FPC rời** của bộ ESP32-S3 N16R8 + OV5640, mã Đức Huy **K1_283**, làm mục tiêu tích hợp. Trang bán không công bố mã riêng của cụm FPC, bảng chân hay mặt tiếp xúc. J2 dùng pinout tham chiếu ESP32-S3-EYE và GPIO theo Freenove. Cần đối chiếu cụm thực tế trước khi cấp điện. [Bộ K1_283](https://dientuduchuy.com/products/esp32-s3-wroom-n16r8-wifi-tich-hop-camera-ov5640) · [Espressif ESP32-S3-EYE, trang 4](https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-EYE-MB_20211201_V2.2.pdf) · [Bảng GPIO Freenove](https://docs.freenove.com/projects/fnk0085/en/latest/fnk0085/codes/C/Preface.html#cam-pin)

## J2 trên NovaChest

Hirose FH12-24S-0.5SH(98), 24 chân, bước 0,5 mm, tiếp xúc dưới. Số chân trong bảng là số pad của footprint KiCad. Đối chiếu dấu chân 1 và mặt đồng của cáp với bản vẽ cơ khí của đầu nối. [Hirose FH12](https://www.hirose.com/product/p/CL0528-0015-4-98?lang=en)

| J2 | Tín hiệu | Nguồn hoặc GPIO ESP32-S3 |
| ---: | --- | --- |
| 1 | NC | Hở |
| 2 | GND | GND |
| 3 | SIOD | GPIO4 |
| 4 | AVDD | 2,8 V |
| 5 | SIOC | GPIO5 |
| 6 | RESETB | U12, kéo lên 2,8 V qua R27 |
| 7 | VSYNC | GPIO6 |
| 8 | PWDN | Kéo xuống GND |
| 9 | HREF | GPIO7 |
| 10 | DVDD | 1,5 V |
| 11 | DOVDD | 2,8 V |
| 12 | Y9 / D7 | GPIO16 |
| 13 | XCLK | GPIO15 qua U10 và R29 |
| 14 | Y8 / D6 | GPIO17 |
| 15 | GND | GND |
| 16 | Y7 / D5 | GPIO18 |
| 17 | PCLK | GPIO13 |
| 18 | Y6 / D4 | GPIO12 |
| 19 | Y2 / D0 | GPIO11 |
| 20 | Y5 / D3 | GPIO10 |
| 21 | Y3 / D1 | GPIO9 |
| 22 | Y4 / D2 | GPIO8 |
| 23 | NC | Hở |
| 24 | NC | Hở |

## Nguồn và layout

- U11 TLV809EC26 giám sát rail 2,8 V và điều khiển chân CE của U8. AVDD và DOVDD dùng chung rail 2,8 V. Đây là lựa chọn lên nguồn đồng thời theo mốc tối thiểu 0 ms trong datasheet, cần xác minh DOVDD ổn định cùng lúc hoặc trước AVDD trên cụm thật. Sau đó U8 cấp DVDD 1,5 V. U12 TPS389015 giữ RESETB mức thấp đến khi DVDD qua ngưỡng và hết trễ đặt bởi C28 22 nF, khoảng 23,5 ms danh định tính từ lúc qua ngưỡng. [OmniVision OV5640, mục 2.7.2](https://files.waveshare.com/upload/d/da/OV5640_DataSheet.pdf) · [TI TLV809E](https://www.ti.com/lit/ds/symlink/tlv803e.pdf) · [TI TPS3890](https://www.ti.com/lit/ds/symlink/tps3890.pdf)
- R29 đặt lại gần U10 và J2. Đo tổng đoạn đồng trên layout được 5,23 mm từ U10 đến R29 và 10,57 mm từ R29 đến J2. U10 đệm XCLK xuống miền 2,8 V. [TI SN74LVC1G125](https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf)
- Bản P1 chuyển đoạn chính XCLK trước U10 sang L3 để tách khỏi HREF trên B.Cu. Đoạn sau R29 rộng 0,15 mm vẫn có chỗ cách Y8/Y9 0,35 mm gần J2, dưới mục tiêu 0,45 mm của brief.
- Tổng chiều dài đồng 2D của 11 đường DVP là 25,14–38,32 mm. Y4 và Y7 giảm còn 28,45 và 32,85 mm bằng cách chuyển đoạn giữa hai via sang L3. Chín đường còn lại có đoạn trên B.Cu. Yêu cầu của brief về DVP đi toàn bộ trên L1 vẫn còn mở. L2 GND và từng vùng nguồn VBAT, 3V3, 5V_SW trên L3 đều có một vùng đồng liền sau khi đổ đồng.

## Xác nhận trên mẫu

1. Kiểm tra dấu chân 1, số chân, bước và mặt tiếp xúc của FPC. Đối chiếu chức năng từng chân, đặc biệt là GND, AVDD, DVDD, DOVDD và RESETB, với sơ đồ của đúng cụm hoặc đo trên bo K1_283. Chỉ cắm cụm vào NovaChest sau khi xác nhận pinout, chiều cắm và điện áp nguồn khớp bảng.
2. Đo 2,8 V, 1,5 V, RESETB và XCLK tại J2. Kiểm tra RESETB vẫn thấp ít nhất 6 ms sau khi DVDD ổn định. Bắt đầu SCCB ít nhất 20 ms sau cạnh lên RESETB và ít nhất 1 ms sau khi XCLK chạy. Đo mức cao và biên dạng tín hiệu DVP/SCCB ở phía ESP32-S3 vì ngưỡng VIH tối thiểu là 0,75 × VDD, tương đương khoảng 2,48 V khi VDD là 3,3 V. [OmniVision OV5640](https://files.waveshare.com/upload/d/da/OV5640_DataSheet.pdf) · [Espressif ESP32-S3](https://documentation.espressif.com/esp32_s3_datasheet_en.pdf)
3. Đọc ID `0x5640` từ thanh ghi `0x300A` và `0x300B` ở địa chỉ SCCB 7 bit `0x3C`. Dùng GPIO trong bảng với `esp32-camera`, đặt chân reset và power-down trong driver là `-1` vì bo điều khiển bằng phần cứng. Kiểm tra ảnh JPEG và tín hiệu PCLK/VSYNC/HREF trên mẫu. [Địa chỉ và mã cảm biến](https://github.com/espressif/esp32-camera/blob/master/driver/include/sensor.h) · [Driver OV5640](https://github.com/espressif/esp32-camera/blob/master/sensors/ov5640.c)

Project KiCad là nguồn thiết kế hiện hành. Các tệp `hardware/design_*.json` và `hardware/placement_*.json` là bản ghi của lần dựng Rev A trước.
