# NovaSight Rev A P1 · Gerber cho PCB mẫu

Hai ZIP được xuất bằng KiCad 10.0.6 từ project P1. Mỗi ZIP chứa Gerber các lớp đồng, solder mask, silkscreen, biên dạng, stencil mặt trên và hai tệp khoan Excellon PTH/NPTH. Dùng ZIP tương ứng với đúng bo.

| Bo | Hồ sơ Gerber | PCB |
| --- | --- | --- |
| NovaChest | [NS-CHEST-MB-RevA-P1-Gerber.zip](NS-CHEST-MB-RevA-P1-Gerber.zip) | FR-4, 4 lớp, 1,60 mm, ENIG, đồng thiết kế 35 µm mặt ngoài và 17,5 µm lớp trong |
| NovaClip | [NS-CLIP-MB-RevA-P1-Gerber.zip](NS-CLIP-MB-RevA-P1-Gerber.zip) | FR-4, 2 lớp, 1,00 mm, ENIG, đồng thiết kế 35 µm |

## Kiểm tra trước khi xuất

| Bo | Lỗi DRC | Kết nối hở | Sai khác PCB và schematic | Vi phạm ERC | Cảnh báo DRC |
| --- | ---: | ---: | ---: | ---: | ---: |
| NovaChest | 0 | 0 | 0 | 0 | 15 |
| NovaClip | 0 | 0 | 0 | 0 | 26 |

- **NovaClip.** Q1 FS8205A dùng footprint TSSOP-8 thân 4,4 × 3 mm, bước 0,65 mm. Đã đi lại mạch bảo vệ pin quanh Q1. R13 dời xuống gần U2. Độ lệch D+/D− từ MCU đến các điện trở nối tiếp giảm từ 5,41 mm xuống 0,29 mm. Đến phía MCU của IC ESD, độ lệch theo tổng chiều dài đường đồng là 0,63 mm. [Bản vẽ vỏ FS8205A](https://www.ic-fortune.com/upload/Download/FS8205A-DS-12_EN.pdf)
- **NovaChest.** R3/R4 đặt gần ESP32-S3. Độ lệch D+/D− đoạn MCU đến điện trở giảm từ 77,72 mm xuống khoảng 0,01 mm. Cặp từ điện trở đến IC ESD đi chung trên L3 và có via GND gần hai điểm chuyển lớp. Đến phía MCU của IC ESD, độ lệch theo tổng chiều dài đường đồng là 0,78 mm. Đã thêm tuyến 5V_SYS rộng 1,5 mm và VBAT rộng 2,5 mm trên L3. VBUS đã mở rộng cục bộ tới 1,5 mm. Phần chính của XCLK trước U10 đã chuyển sang L3, xa đoạn HREF trên lớp đáy.

Độ dài trên là độ dài đồng 2D. Các nhánh từ IC ESD tới J1 còn khác chiều dài và có chuyển lớp. Trở kháng USB 90 Ω và chất lượng tín hiệu cần xác nhận trên mẫu. VBUS vẫn có cổ chai hẹp 0,36 mm. Cần đo sụt áp và nhiệt trên mẫu trước khi chạy tải tối đa. DVP còn đổi lớp và cáp OV5640 K1_283 cần xác nhận pinout, chiều cắm và điện áp trước khi cắm. [Hướng dẫn USB của Espressif](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html#usb) · [Bảng chân OV5640](../pcb-review/NS-CHEST-MB/OV5640-camera-review.md)

## Thông tin chuyển cho xưởng

- Dùng lớp Edge.Cuts làm biên dạng. Hai tệp khoan dùng mm, tọa độ tuyệt đối và chung gốc với Gerber.
- Mỗi ZIP có `Filled-capped-vias.csv` chỉ rõ chín lỗ dưới pad nhiệt IC sạc, kèm tọa độ và đường kính đã đối chiếu với tệp PTH. Khi đặt cả lắp ráp, xác nhận xưởng nhận xử lý lấp và mạ bịt các via này theo vị trí. [Quy trình via-in-pad của JLCPCB](https://jlcpcb.com/help/article/via-in-pad-pofv-guide)
- Bản này dùng cho lô mẫu kỹ thuật. Hồ sơ BOM/CPL phục vụ rà lắp ráp nằm trong thư mục review. Cần chốt mã linh kiện và kiểm tra xoay khi đặt SMT. Một số nhãn in lụa vẫn có thể bị xén ở mép bo hoặc nhỏ hơn thông số của xưởng.
