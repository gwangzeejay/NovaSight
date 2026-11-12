# NovaSight Rev A · Review PCB

**Bản mới nhất là P1.** Xem [Gerber PCB mẫu và kết quả kiểm tra P1](../pcb-prototype/README.md). Project KiCad, báo cáo trong `review/current` và các tệp BOM/CPL/DXF/STEP dưới đây theo bản P1. Hai ZIP có hậu tố `DFM-review` lưu bộ CAM trước P1.

## Kết quả rà soát trước P1

**Trạng thái ngày 09/11/2026.** Chest đã cập nhật thiết kế camera OV5640. Cả hai bo đã thông mạch và khớp sơ đồ trong KiCad 10.0.6. Bộ CAM dùng để review DFM. Phát hành gia công đang chờ các hạng mục dưới đây.

## Kết quả KiCad

| Bo | Bản v2 còn hở | Kết nối hở hiện tại | Lỗi DRC khác | Cảnh báo DRC | Sai khác PCB và schematic | Vi phạm ERC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| NS-CHEST-MB | 1 | 0 | 0 | 15 | 0 | 0 |
| NS-CLIP-MB | 4 | 0 | 0 | 22 | 0 | 0 |

Lần rà soát ngày 09/11 chạy lại DRC sau khi đổ đồng, với kiểm tra mọi lỗi đường mạch và đối chiếu schematic. Chest còn 14 cảnh báo silkscreen và một cảnh báo footprint U4 khác thư viện. Vị trí, kích thước và số thứ tự pad U4 khớp bản thư viện KiCad đang cài. Clip còn 22 cảnh báo silkscreen. Cảnh báo của lần chạy lại trùng UUID và loại với báo cáo JSON đã lưu. Gerber và tệp khoan trong hai ZIP khớp dữ liệu xuất lại từ PCB hiện hành sau khi bỏ dấu thời gian.

- **Chest.** Đã nối `JSN_R_ECHO` tới U4 chân 33, thêm mạch trình tự nguồn và reset OV5640, đi lại Y4/Y7 và dời R29 để rút ngắn XCLK. Đường bao 100 × 49,6 mm. Bo có bốn lớp, dày 1,6 mm.
- **Clip.** Đã nối `IMU_INT`, `MOT_R_PWM`, `LED_STATUS` và các vùng GND bị cô lập. Đã đi lại các nhánh lân cận và dời C13 từ (82,00; 61,75) mm tới (95,50; 56,75) mm, xoay 90°. Đường bao 73,4 × 37,4 mm giữ theo bản v2. Bo có hai lớp, dày 1,0 mm. Khoảng cách vùng GND đặt 0,15 mm theo brief.
- **Hai bo.** Đã đóng gói các liên kết thư viện cục bộ và đặt ENIG trong stackup. Mỗi bo có chín via được đánh dấu filled/capped dưới pad nhiệt IC sạc. Khi đặt bo, cần chuyển chỉ định lấp và bịt các via này cho xưởng cùng dữ liệu khoan.

## Các hạng mục chặn phát hành

| Hạng mục | Kết quả đo hoặc thông tin cần chốt |
| --- | --- |
| Footprint Q1 trên Clip | BOM chọn Fortune FS8205A, mã C16052, nhưng PCB dùng `TSSOP-8_3x3mm_P0.65mm`. Datasheet cho thân danh định 4,40 × 2,93 mm và nhịp hai hàng chân 6,40 mm. Hai mép ngoài của pad đồng hiện chỉ cách nhau 5,40 mm. Cần đổi sang footprint thân 4,4 × 3 mm, đi lại các nhánh quanh Q1 và cập nhật hồ sơ lắp ráp. [Datasheet Fortune, trang 6](https://www.ic-fortune.com/upload/Download/FS8205A-DS-12_EN.pdf) · [JLCPCB C16052](https://jlcpcb.com/partdetail/FortuneSemicon-FS8205A/C16052) |
| USB trên hai bo | D+/D− còn đổi lớp. Chiều dài đường đồng 2D từ MCU tới điện trở nối tiếp là 49,43 / 127,15 mm trên Chest và 14,33 / 8,92 mm trên Clip, theo thứ tự D+ / D−. Độ lệch lần lượt 77,72 mm và 5,41 mm. Cần đi lại theo cặp, kiểm tra chênh lệch ≤ 1 mm và chốt stackup USB 90 Ω với xưởng. |
| Nguồn Chest | Các đoạn track VBUS và 5V_SYS hiện khoảng 0,36–0,60 mm và 0,45–0,60 mm. Brief yêu cầu tuyến chính ≥ 1,5 mm hoặc vùng đồng tương đương. Cần kiểm tra toàn tuyến dòng lớn, các đoạn thắt và cụm via của VBAT, 5V_SYS, VBUS và IP_SW. |
| Camera Chest | 11 đường DVP đều dưới 40 mm. Y4/Y7 có đoạn trên L3 và chín đường còn lại có đoạn trên B.Cu. L2 GND liền. Yêu cầu đi DVP toàn bộ trên L1 còn mở. Khoảng cách giữa mép đồng XCLK trước U10 và HREF có chỗ chỉ 0,152 mm, trong khi brief yêu cầu 0,60 mm cho đoạn XCLK rộng 0,20 mm. Cần xác nhận pinout, điện áp và mặt tiếp xúc FPC của bộ Đức Huy K1_283, sau đó kiểm tra trình tự nguồn và tín hiệu trên mẫu. [Bảng chân J2 và bước kiểm tra OV5640](NS-CHEST-MB/OV5640-camera-review.md) |
| Kiểm tra mẫu và vỏ | Cần xác nhận pinout breakout ToF, JSN-SR04T và cực tính pin. Cần kiểm tra va chạm với vỏ, tải và nhiệt của nguồn sạc, USB và RSSI khi lắp hoàn chỉnh theo các mục [ĐO] trong brief. |
| DFM và BOM | Chữ tham chiếu F.Silkscreen đang nhỏ hơn mức công bố 1,0 mm hoặc có nét nhỏ hơn 0,15 mm của JLCPCB. J1 thực tế là GCT USB4105 trên cả hai bo, khoảng hở nhỏ nhất từ lỗ định vị tới đồng khoảng 0,194 mm. Chú thích trong quy tắc DRC hiện ghi HRO. BOM đang có mã LCSC cho 2/147 dòng Chest và 2/97 dòng Clip. Cần chốt MPN, nguồn linh kiện và xoay CPL theo quy ước xưởng. [Thông số chế tạo JLCPCB](https://jlcpcb.com/capabilities/pcb-capabilities/) |
| Độ đầy đủ của STEP | Chest thiếu mô hình SW1 và U9. Clip thiếu SW1, U6 và mô hình cụm dây ở J2, J3, J4. Dùng DXF và STEP để review vị trí, sau đó bổ sung đúng mô hình trước khi nghiệm thu va chạm. |

Tham chiếu kỹ thuật cho USB và RF. [Espressif ESP32-S3](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html) · [Espressif ESP32-C3](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c3/pcb-layout-design.html)

Tham chiếu khả năng chế tạo và via-in-pad. [JLCPCB](https://jlcpcb.com/capabilities/pcb-capabilities/)

## Tệp bàn giao

- Project đang dùng nằm trong [NS-CHEST-MB](../../hardware/NS-CHEST-MB/NS-CHEST-MB.kicad_pro) và [NS-CLIP-MB](../../hardware/NS-CLIP-MB/NS-CLIP-MB.kicad_pro). Mở bằng KiCad 10. Bản Chest trước khi cập nhật camera nằm trong `routing/before-ov5640-camera`. Các bản trước lần review đi dây nằm trong `routing/before-routing-review` của mỗi bo.
- Báo cáo [DRC Chest](../../hardware/NS-CHEST-MB/review/current/NS-CHEST-MB-drc.json), [ERC Chest](../../hardware/NS-CHEST-MB/review/current/NS-CHEST-MB-erc.json), [DRC Clip](../../hardware/NS-CLIP-MB/review/current/NS-CLIP-MB-drc.json) và [ERC Clip](../../hardware/NS-CLIP-MB/review/current/NS-CLIP-MB-erc.json).
- Hồ sơ CAM gồm Gerber, khoan PTH/NPTH và danh sách lỗ. [DFM Chest](NS-CHEST-MB/NS-CHEST-MB-DFM-review.zip) · [DFM Clip](NS-CLIP-MB/NS-CLIP-MB-DFM-review.zip)
- Dữ liệu review lắp ráp. Chest [BOM](NS-CHEST-MB/NS-CHEST-MB-BOM-review.csv), [CPL](NS-CHEST-MB/NS-CHEST-MB-CPL-review.csv), [DXF](NS-CHEST-MB/NS-CHEST-MB-mechanical-review.dxf), [STEP](NS-CHEST-MB/NS-CHEST-MB-assembly.step). Clip [BOM](NS-CLIP-MB/NS-CLIP-MB-BOM-review.csv), [CPL](NS-CLIP-MB/NS-CLIP-MB-CPL-review.csv), [DXF](NS-CLIP-MB/NS-CLIP-MB-mechanical-review.dxf), [STEP](NS-CLIP-MB/NS-CLIP-MB-assembly.step).
- Schematic dạng PDF. [Chest](../pdf/NS-CHEST-MB-RevA-schematic.pdf) · [Clip](../pdf/NS-CLIP-MB-RevA-schematic.pdf)
