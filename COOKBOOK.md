# Cookbook NovaSight

**Rev A P1 · 10/11/2026 · Hướng dẫn dựng, lắp và nghiệm thu mẫu kỹ thuật**

## 1. Chọn đúng phiên bản

| Vai trò | Nguồn dùng |
| --- | --- |
| Yêu cầu sản phẩm và phỏng vấn | [Mô tả sản phẩm](source_review/product.txt) |
| Kiến trúc điện, cơ khí và mục cần đo | [Brief PCB](source_review/pcb_brief.txt) |
| Thiết kế điện hiện hành | [Project NovaChest](hardware/NS-CHEST-MB/NS-CHEST-MB.kicad_pro) · [Project NovaCane Clip](hardware/NS-CLIP-MB/NS-CLIP-MB.kicad_pro) |
| Chế tạo lô mẫu | [Hồ sơ Gerber P1](output/pcb-prototype/README.md) |
| Review lắp ráp | [BOM, CPL, DXF và STEP](output/pcb-review/README.md) |
| Cấu hình camera P1 | [Đầu nối J2 và kiểm tra OV5640](output/pcb-review/NS-CHEST-MB/OV5640-camera-review.md) |
| Triển khai phần mềm | [Firmware](firmware/) · [NovaApp](novaapp/) · [Công cụ](tools/) |

Ưu tiên schematic và PCB hiện hành khi brief Alpha/Beta khác P1. Ví dụ camera ghi OV3660 trong brief, trong khi schematic P1 dùng cụm OV5640 FPC. Các thư mục `routing`, `review` ngoài `review/current`, các manifest thiết kế và script dựng PDF ghi lại các lần thiết kế trước. Hai ZIP có hậu tố `DFM-review` là CAM trước P1.

## 2. Kiến trúc và phạm vi triển khai

```text
JSN trái/phải ─┐
ToF + IMU ─────┼─> Chest: lọc, chấm độ tin cậy, chọn nguy cơ ──> rung vai
OV5640 ────────┘   Camera dùng riêng để kiểm tra thu JPEG
                                │ BLE khi ghép cặp và Clip sẵn sàng
                                ▼
IMU, Mode, SOS, Xin đường ──> Clip: rung gậy, LED, trạng thái
                                │ BLE GATT
                                ▼
                             NovaApp: cấu hình, luyện rung, GPS và mở SMS
```

| Hạng mục | Bản hiện tại |
| --- | --- |
| Vật cản thân trên | Chest phát siêu âm luân phiên, khoảng 10 Hz mỗi bên. Vật dưới 1 m có thể kích hoạt sau một mẫu trong vùng đo. Vật xa hơn cần ba mẫu nhất quán. Giới hạn theo chế độ và ước lượng tốc độ từ nhịp bước. |
| Mặt đất | VL53L8CX chạy 4×4 ở cấu hình 20 Hz sau khi bật. Chest ghi nền phẳng, bù thay đổi góc, cần hai ô kề nhau cùng dấu và ba khung nhất quán. Ngưỡng lệch độ cao thử nghiệm là 125 mm. |
| Không chắc | Quá hạn, thiếu mẫu mạnh, thiếu hiệu chuẩn hoặc tư thế thiếu tin cậy làm kênh mặt đất suy giảm. Siêu âm lâu không có echo cũng làm trạng thái suy giảm vì vùng trống và lỗi đầu dò có thể giống nhau. Chest phát tối đa ba nhịp không chắc mỗi đợt suy giảm. |
| Camera | Kiểm tra driver, PID `0x5640` và thu JPEG QVGA. Giữ khung hình trong RAM trong thời gian kiểm tra. Cảnh báo vẫn dựa vào siêu âm, ToF và IMU. |
| Clip độc lập | Mode, đèn Xin đường 2 Hz trong 60 giây, phát sự kiện SOS khi giữ 3 giây, IMU phát hiện quét và chỉ số gồ ghề 0–100. Clip nhận nguy cơ từ Chest khi có ghép cặp. |
| NovaApp | Xem trạng thái Clip, chỉnh rung, luyện ba mẫu, nhận sự kiện SOS, lấy GPS theo yêu cầu, mở SMS để người dùng xác nhận gửi, lưu điểm mặt đường và xuất GeoJSON. |

Mức rung mặc định là 1. Xung vật cản dài 250 ms, mẫu mặt đất gồm ba xung 80 ms, mẫu không chắc tăng rồi giảm trong 600 ms. Mode ngắn chuyển Đi bộ → Đông người → Trong nhà, xác nhận bằng 1–3 xung nhẹ. Ở Đông người, Chest chỉ báo ứng viên giữa trong 1,2 m khi hai bên thấy khoảng cách gần nhau. Ở Trong nhà, Chest giới hạn 1 m, dùng mức rung 1 và dừng thu ảnh. Mode trên hai bo lưu riêng.

Mức phát hiện nắng gắt, sai số tốc độ và tư thế, độ trễ 200 ms, tầm phản ứng 1,2 s, pin, IP54 và hiệu quả O&M là các mục nghiệm thu. Dữ liệu trên bàn và mô phỏng cần được ghi riêng với số đo đi bộ thực tế.

## 3. Chuẩn bị công cụ

| Công cụ | Bản đã dùng hoặc mục đích |
| --- | --- |
| PlatformIO Core | 6.2.0 |
| Espressif32 / Arduino-ESP32 | 7.0.1 / 2.0.17 |
| Thư viện firmware | NimBLE-Arduino 1.4.3, STM32duino VL53L8CX 2.1.0 |
| KiCad | 10.0.6 cho DRC, ERC và CAM P1 |
| Python | 3.13; các công cụ dự án dùng thư viện chuẩn |
| Kiểm thử | C++14 trở lên và Node.js có `node --test` |
| Dụng cụ mẫu | Cáp USB-C có data, nguồn giới hạn dòng, DMM, oscilloscope, vật chuẩn khoảng cách, sàn phẳng, thước và pin đúng cực |

PlatformIO được pin phiên bản trong [platformio.ini](firmware/platformio.ini). Chest dùng flash 16 MB và PSRAM octal 8 MB, Clip dùng flash 4 MB. Script `patch_tof.py` được áp dụng vào thư viện VL53L8CX tải về khi build Chest để giao dịch I²C trả lỗi thay vì lặp vô hạn khi thiết bị mất phản hồi. [PlatformIO Espressif32](https://docs.platformio.org/en/latest/platforms/espressif32.html) · [ST VL53L8CX](https://www.st.com/resource/en/datasheet/vl53l8cx.pdf)

```powershell
# Nếu pio chưa có, cài bằng Python hoặc dùng PlatformIO Core trong VS Code.
python -m pip install platformio==6.2.0

# Với đường dẫn Windows chứa dấu, đặt các thư mục build/deps trên đường dẫn ASCII có quyền ghi.
$env:PYTHONUTF8 = '1'
$env:PLATFORMIO_BUILD_DIR = Join-Path $env:TEMP 'novasight-p1-build'
$env:PLATFORMIO_LIBDEPS_DIR = Join-Path $env:TEMP 'novasight-p1-libdeps'

pio run -d firmware -e chest
pio run -d firmware -e clip
```

Nếu tài khoản Windows có dấu trong tên, chọn đường dẫn ASCII khác cho hai thư mục trên. Nếu VS Code đã cài PlatformIO nhưng `pio` chưa vào PATH, dùng terminal PlatformIO, hoặc gọi `& "$env:USERPROFILE/.platformio/penv/Scripts/platformio.exe"` thay cho `pio`. Hai target có thể build cùng lượt bằng `pio run -d firmware`.

## 4. Kiểm tra CAD và chuyển hồ sơ xưởng

```powershell
python tools/hardware.py
python tools/hardware.py --out output/build/hardware-p1 --step
```

Công cụ tự tìm `kicad-cli` trên PATH hoặc bản KiCad 10 cài theo tài khoản Windows. Có thể truyền `--kicad "C:/…/kicad-cli.exe"` hoặc đặt biến `KICAD_CLI`. `--board NS-CHEST-MB` hoặc `--board NS-CLIP-MB` chạy riêng một bo. `--out` yêu cầu thư mục đích mới. Xuất STEP cần có thư viện 3D KiCad. Nếu mô hình chuẩn thiếu, kiểm tra đường dẫn `KICAD10_3DMODEL_DIR` và `step.log`.

Công cụ chạy DRC với đổ đồng và đối chiếu schematic, chạy ERC, trích netlist để so GPIO firmware, xuất lại Gerber và khoan rồi so từng tệp với ZIP P1 sau khi bỏ dấu thời gian. Công cụ cũng đối chiếu tọa độ và đường kính của chín via lấp và mạ bịt trong PCB, CSV và tệp khoan PTH. Chế độ xuất tạo báo cáo JSON, netlist XML, CAM/ZIP, BOM, CPL, PDF schematic, DXF và STEP tùy chọn. Khi PCB đã sửa khác P1, phép so CAM sẽ dừng để nhóm phát hành revision mới cùng hồ sơ tương ứng.

| Bo | Đồng / dày / bề mặt | DRC lỗi / hở / sai khác | ERC | Cảnh báo DRC |
| --- | --- | --- | --- | ---: |
| Chest | 4 lớp, 1,60 mm, ENIG | 0 / 0 / 0 | 0 | 15 |
| Clip | 2 lớp, 1,00 mm, ENIG | 0 / 0 / 0 | 0 | 26 |

Khi chuyển xưởng, gửi đúng ZIP P1 theo bo. Dùng Edge.Cuts làm biên dạng, xác nhận khoan PTH và NPTH, thông số stackup và yêu cầu via-in-pad dưới pad nhiệt U2 (Chest) hoặc U3 (Clip). Chest có đồng thiết kế 35 µm mặt ngoài, 17,5 µm bên trong. Clip có đồng thiết kế 35 µm. Chốt MPN, cực tính, biến thể, DNP và xoay CPL trước khi duyệt SMT. Đặc biệt đối chiếu Q1 FS8205A bản Fortune với footprint thân 4,4 × 3 mm của Clip và J1 GCT USB4105 trên hai bo. [Gói chế tạo P1](output/pcb-prototype/README.md) · [Ghi chú BOM và STEP](output/pcb-review/README.md)

## 5. Đấu và kiểm tra mẫu theo thứ tự

1. Mở STEP và DXF cùng bản vỏ. Kiểm tra trục/cao độ đầu dò, mặt tiếp xúc FPC, anten và mép vỏ, khoảng thao tác USB-C và công tắc. Một số mô hình STEP còn thiếu nên dùng linh kiện thật để kiểm tra va chạm.
2. Soi dưới kính và đo ngắn mạch giữa GND với các rail chính. Xác nhận mã IC, hướng diode, đầu pin và jumper trước cấp điện. Tháo camera, ToF, JSN và motor trong lần cấp nguồn đầu.
3. Dùng nguồn bàn có giới hạn dòng theo quy trình kỹ thuật của nhóm, cấp qua đường nguồn đúng trên schematic. Ghi dòng tĩnh và nhiệt từng rail. Chest đo VBAT, VBUS, 5V_SYS, 5V_SW và 3V3. Clip đo BAT+, VSYS, VBUS và 3V3. Đo lại khi chuyển USB ↔ pin và khi chạy motor. So ADC firmware với DMM, kiểm tra `usb=0/1` tương ứng việc rút/cắm USB.
4. Kiểm tra strap ở reset. Chest GPIO45/46 phải ở mức thấp lúc khởi động. Clip kiểm tra GPIO2/8/9 theo brief và thử bật máy khi đang giữ Xin đường. Nếu bo reset khi rút USB hoặc sụt rail, ghi dạng sóng và xử lý nguồn trước khi thêm tải. [Checklist của Espressif](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/schematic-checklist.html)
5. Nạp firmware và xác nhận cổng serial, pin ADC, LED và Mode. Dưới ngưỡng pin 3,50 V hoặc khi ADC thiếu hợp lệ, firmware khóa rung. Sau khi pin đạt 3,65 V, firmware cho phép rung trở lại. Đây là ngưỡng chặn tải trong code. Công tắc nguồn của hai bo điều khiển mạch nguồn phần cứng.
6. Sau khi tắt nguồn, nối từng mô-đun một. Dùng pin đúng cực tính và đúng kích cỡ theo brief, JSN qua tầng đổi mức trên bo, ToF đúng loại breakout, motor 1027 đúng rail và đúng kênh. Đo 22 kHz tại cổng MOSFET và kiểm tra duty ở các mức pin/USB. Công thức code dùng rail giả định bảo thủ và giới hạn điện áp trung bình mục tiêu 3 V. Đo lại với motor thật, gồm dòng khởi động, sụt rail và nhiệt.
7. Xác minh pinout JSN và ToF từ đúng mẫu mua. Với J3 Chest, kiểm tra pull-up I²C, cấp nguồn và tương thích LPn/INT. Với J5/J6, đo TRIG và ECHO tại chân MCU và kiểm tra bằng vật phẳng ở 0,5 m, 1 m và 2 m. Thử riêng từng đầu rồi cả hai để tìm xuyên nhiễu.
8. Đối chiếu từng chân FPC OV5640 K1_283, chân 1, bước 0,5 mm, mặt tiếp xúc dưới, các rail 2,8 V và 1,5 V trước khi cắm. Sau khi đấu xác nhận, đo RESETB, XCLK, DVP và SCCB theo ghi chú camera rồi mới bật driver. [Quy trình kiểm tra camera P1](output/pcb-review/NS-CHEST-MB/OV5640-camera-review.md)

### GPIO trích từ schematic P1

| Chức năng | Chest S3 | Clip C3 |
| --- | --- | --- |
| I²C cảm biến SDA / SCL | 2 / 14 | 4 / 5 |
| MPU6050 `0x68`, INT | 47 | 1 |
| Motor trái / phải | 45 / 46 | 6 / 7 |
| Mode / Xin đường / SOS | 3 / — / — | 10 / 2 / 20 |
| LED trạng thái / LED Xin đường | 48 / — | 8, tích cực thấp / 3 |
| VBAT ADC / VBUS detect | 1 / 44 | 0 / 21 |
| USB D− / D+ | 19 / 20 | 18 / 19 |
| JSN trái TRIG / ECHO | 21 / 38 | — |
| JSN phải TRIG / ECHO | 39 / 40 | — |
| ToF `0x29`, LPn / INT | 41 / 42 | — |
| Camera SCCB SDA / SCL | 4 / 5 | — |
| Camera VSYNC / HREF / PCLK / XCLK | 6 / 7 / 13 / 15 | — |
| Camera D0 … D7 | 11, 9, 8, 10, 12, 18, 17, 16 | — |

ToF và MPU6050 đọc qua polling trong P1. INT có trên sơ đồ để dùng khi cần. Các nút tích cực thấp. USB Serial/JTAG dùng cổng USB trên bo. GPIO21 của Clip thuộc UART TX mặc định và được firmware cấu hình lại thành ngõ vào VBUS sau boot. [USB Serial/JTAG của Espressif](https://docs.espressif.com/projects/esp-iot-solution/en/latest/usb/usb_overview/usb_serial_jtag.html)

## 6. Nạp firmware và đọc serial

1. Cắm một bo qua USB-C data, bật nguồn theo quy trình bring-up và dùng `pio device list` để xác định COM. Ví dụ dưới đây dùng `COM7` cho Chest và `COM8` cho Clip.
2. Nếu cổng chưa vào chế độ nạp, Chest giữ BOOT GPIO0, reset rồi nhả BOOT. Clip giữ BOOT GPIO9 ở mức thấp trong lúc reset hoặc bật nguồn rồi nhả sau khi cổng xuất hiện. Dùng test pad đúng theo schematic. [Nạp ESP32-S3 qua USB](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/establish-serial-connection.html) · [Nạp ESP32-C3 qua USB](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/get-started/establish-serial-connection.html)
3. Nạp đúng target, khởi động lại và mở serial 115200. Nếu cổng đổi sau reset, chạy lại `pio device list`. Đóng terminal serial trước khi nạp lại.

```powershell
pio run -d firmware -e chest -t upload --upload-port COM7
pio device monitor -d firmware -p COM7 -b 115200 --eol LF

pio run -d firmware -e clip -t upload --upload-port COM8
pio device monitor -d firmware -p COM8 -b 115200 --eol LF
```

Mỗi lệnh sau gửi một dòng qua USB. Dùng `status` để xác nhận firmware chạy đúng target và đối chiếu ADC với đồng hồ đo. `L/R` trên Chest là số đo siêu âm gần nhất theo mm, giá trị 0 khi không có mẫu hợp lệ. Chest in dung lượng PSRAM lúc boot. Clip trả địa chỉ MAC ở cuối dòng `status`. Nếu terminal vừa mở đã bỏ lỡ log boot, gửi `status`.

| Bo | Lệnh | Tác dụng |
| --- | --- | --- |
| Cả hai | `status`, `level 1` … `level 3` | Xem trạng thái và đặt mức rung lưu qua khởi động |
| Chest | `stream on`, `stream off`, `grid` | Log mỗi giây và bảng 16 vùng theo dạng `ô:mm/trạng thái` |
| Chest | `tof on`, `tof off` | Bật/tắt driver ToF sau khởi động lại |
| Chest | `cal floor`, `cal clear` | Ghi nền phẳng mới hoặc xóa nền lưu |
| Chest | `camera on`, `camera off` | Bật/tắt tác vụ chẩn đoán camera sau khởi động lại |
| Cả hai | `key HEX`, `key off` | Ghi khóa 32 chữ số hex hoặc xóa khóa, có hiệu lực sau reset |
| Chest | `peer AA:BB:CC:DD:EE:FF`, `peer off` | Chỉ định MAC Clip hoặc bỏ liên kết, có hiệu lực sau reset |

## 7. Hiệu chuẩn Chest

1. Lắp Chest và cụm ToF theo góc cơ thiết kế 35° xuống. Đánh dấu vị trí đeo, chiều cao và hướng của breakout. Đứng yên trước nền phẳng, tránh nắng trực tiếp lúc hiệu chuẩn.
2. Gửi `tof on`, khởi động lại và đợi `tof=ranging`. Chạy `grid`. Trạng thái 5 là ô được firmware dùng làm mẫu mạnh. Dùng vật phẳng dịch qua từng hàng và kiểm tra hàng gần/xa theo hướng module. So số `pitch` trước và sau khi nghiêng xuống một góc đã biết. Nếu trục hoặc dấu sai, sửa hướng lắp hoặc công thức pitch và thứ tự hàng trong firmware trước khi ghi nền.
3. Gửi `cal floor`, đứng yên đến khi `cal=saved`. Firmware cần 20 khung ổn định và tối thiểu 10 ô dùng được. Nếu `cal=timeout` sau 12 giây, kiểm tra `grid`, ánh sáng, nguồn, lắp đặt và IMU. Nền cũ vẫn được dùng cho đến khi ghi được nền mới.
4. Thử trên sàn phẳng và các bậc/vật chuẩn có bảo vệ. Xác nhận `valid=1` trên sàn ổn định, `floor` có khoảng cách khi mục tiêu lặp lại và suy giảm khi che ToF hoặc nghiêng vượt vùng bù. Đổi người đeo, chiều cao hoặc gá cảm biến thì hiệu chuẩn lại. Dùng `cal clear` để thử từ đầu.
5. Sau khi hoàn tất phép đo J2, gửi `camera on` và reboot. Kỳ vọng `camera=OV5640 pid=0x5640` và `camera_bytes` lớn hơn 0. Chuyển Trong nhà và kiểm tra giá trị về 0. Gửi `camera off` và reboot nếu cần cô lập camera. [Driver camera Espressif](https://github.com/espressif/esp32-camera)

## 8. Ghép Chest với Clip trên bàn

1. Xác nhận hai bo đã chạy độc lập với nguồn pin hợp lệ. Chest rung vai cho mục tiêu siêu âm. Clip nhận nút và LED Xin đường ở 2 Hz.
2. Tạo khóa ngẫu nhiên duy nhất cho cặp đang thử bằng lệnh dưới đây. Gửi `key <chuỗi>` qua USB tới cả hai bo. Tránh lưu chuỗi vào tài liệu hoặc log chia sẻ.
3. Lấy MAC từ `status` trên Clip. Gửi `peer <MAC>` qua USB tới Chest rồi khởi động lại cả hai.
4. Quét Clip trong khi có mục tiêu trước Chest. Khi Clip đang quét và sẵn sàng, `relay=1` trên Chest. Chest có thể chuyển sự kiện vật cản/mặt đất đã xác thực cho Clip. Mẫu không chắc vẫn phát tại Chest.
5. Để Clip đứng yên hoặc tắt nguồn và lặp lại. Chest phải trở lại phát tại chỗ. Chest hủy yêu cầu nếu sau 80 ms chưa bắt đầu gửi. Nếu đã bắt đầu gửi và ACK BLE không rõ, Chest đợi đến 650 ms trước khi đánh giá cảnh hiện tại và rung tại chỗ, nhằm tránh chồng với một xung Clip có thể đã bắt đầu. Đo riêng nhánh mất ACK trong bài kiểm tra độ trễ.
6. Để trở lại chế độ độc lập, gửi `peer off` hoặc `key off` rồi reboot.

```powershell
python -c "import secrets; print(secrets.token_hex(16))"
```

Relay dùng nonce một lần, khóa 128 bit và HMAC-SHA256 rút gọn cho thử thách, sự kiện và phản hồi. Việc mở quyền NovaApp là cơ chế riêng dựa trên nút vật lý. Thử trong môi trường BLE kiểm soát và chỉ cấp khóa qua USB cho cặp thử nghiệm.

## 9. Chạy NovaApp

```powershell
python -m http.server 8000 --bind 127.0.0.1 --directory novaapp
```

Trên máy phát triển, mở [localhost:8000](http://localhost:8000). Trên Android, phục vụ thư mục `novaapp` bằng HTTPS và mở URL đó trong Chrome có Bluetooth. Cho phép Bluetooth khi trình duyệt yêu cầu. Điện thoại dùng URL HTTPS của máy chủ khi thử từ xa, còn `localhost` trỏ về chính điện thoại. [Web Bluetooth trên Chrome](https://developer.chrome.com/docs/capabilities/bluetooth)

1. Nhấn **Chọn Clip qua Bluetooth**, chọn **NovaClip P1** và đối chiếu chế độ, pin, IMU và đèn với serial.
2. Giữ nút Mode trên Clip ba giây để mở cửa sổ 60 giây. Thử đổi mức 1–3 và kiểm tra mức trên Clip. Để Clip đứng yên, phát từng mẫu rồi chọn **Phát mẫu ngẫu nhiên** để tập nhận biết.
3. Giữ SOS ba giây. Màn hình nhận sự kiện khi app đang mở và kết nối. Nếu muốn kèm GPS, chọn **Lấy vị trí cho SOS** và cho phép truy cập. Nhập số người hỗ trợ, chọn **Mở tin nhắn SMS** rồi đọc và gửi trong ứng dụng SMS. Rung ngắn trên Clip xác nhận nút đã được ghi nhận khi điện thoại đang kết nối. Nếu chưa có kết nối BLE, Clip rung ba nhịp dài 220 ms thay cho nhịp xác nhận, nghĩa là SOS chưa tới điện thoại. Sự kiện vẫn được giữ 120 giây, nên mở NovaApp và kết nối trong thời gian đó vẫn nhận được. Trạng thái gửi phụ thuộc ứng dụng SMS và mạng của điện thoại.
4. Khi Clip báo đang quét, thử **Lưu điểm tại đây**. Nhật ký chỉ lưu trong trình duyệt, tối đa 500 điểm. Kiểm tra tọa độ, sai số GPS và thời điểm trong GeoJSON xuất ra. Chỉ số gồ ghề là dữ liệu IMU thử nghiệm. Đánh giá lại bằng đoạn mặt đường có nhãn trước khi dùng dữ liệu để so tuyến.
5. Tắt app hoặc ngắt Bluetooth rồi thử Chest và Clip độc lập. Trang hiện tại phục vụ ở foreground, mở SMS có xác nhận và ghi điểm thủ công. Muốn thử SOS nền, xác nhận giao nhận SMS, tự động tổng hợp bản đồ hoặc phân loại hình ảnh thì cần một vòng triển khai và nghiệm thu riêng.

### GATT v1

UUID có tiền tố `74cd01xx`, hậu tố `-8b8c-4cc2-8ad4-5c1104b992d0`. Các số nhiều byte là little-endian.

| Đuôi `xx` | Quyền | Dữ liệu |
| --- | --- | --- |
| 00 | Service | NovaClip P1 |
| 01 | Read | Version 1, ready, nonce 8 B và HMAC 8 B |
| 02 | Write | Loại, hướng, mm uint16, mã yêu cầu uint32, HMAC 8 B |
| 03 | Read | Mã nhận uint32 và HMAC 8 B |
| 04 | Read/Notify | 11 B gồm version, flags, mode, level, mV uint16, độ gồ ghề, mã SOS uint32. Bits 0–4 của flags lần lượt là quét, đèn, mở thiết lập, pin yếu, IMU. |
| 05 | Write | 3 B gồm version, op, giá trị. Op 1 đặt mức 1–3. Op 2 phát mẫu 1–3 khi Clip đứng yên. Cả hai cần cửa sổ vật lý còn mở. |

## 10. Kiểm thử và nghiệm thu

```powershell
python tools/test_core.py --cxx C:/MinGW/bin/g++.exe
node --test tests/app_test.mjs
node --check novaapp/app.mjs
python tools/hardware.py
pio run -d firmware
```

Kiểm thử host bao phủ thời gian xung, duty, debounce và giữ nút, ổn định siêu âm, rollover thời gian, hiệu chuẩn và suy giảm ToF, khung BLE NovaApp và thứ tự tọa độ GeoJSON. Kiểm thử giao diện trên Chrome ở chiều rộng 390 px dùng BLE/GPS giả lập để kiểm tra kết nối, đổi mức rung, thử mẫu, nhận SOS và tải nhật ký. Kiểm thử CAD/CAM trên KiCad 10.0.6 cho kết quả ở mục 4. Build firmware thành công cho cả hai target. Các kiểm thử dưới đây cần chạy trên mẫu thật và ghi số đo.

| Bài thử | Cách chạy | Dữ liệu cần ghi hoặc tiêu chí |
| --- | --- | --- |
| Nguồn, sạc, reset | Chạy từng rail từ nguồn bàn, sau đó từ pin và USB. Rút/cắm ở tải nghỉ và khi rung. | Giá trị rail, nhiệt IC, dòng, số reset, trạng thái VBUS_DET và chênh ADC/DMM. |
| USB | Nạp và đọc CDC trên từng bo, chạy tải cùng lúc, thử các cáp data. | Tỷ lệ nạp, reset, chất lượng đường USB và stackup mục tiêu 90 Ω. |
| Siêu âm và hướng | Đặt mục tiêu trái/giữa/phải ở 0,5 / 1 / 2 / 2,5 m. Thử bề mặt nghiêng, hấp thụ, mưa nhẹ trong môi trường kiểm soát. | Khoảng cách, hướng rung, lỗi bỏ sót/báo nhầm, vùng mù và xuyên nhiễu. |
| Mặt đất | Sàn phẳng, bậc lên, hụt xuống và vật thấp có rào chắn. Thử trong nhà, bóng râm và nắng. | Khoảng cách, độ lệch nền, số ô mạnh, tỷ lệ phát hiện và tỷ lệ phát không chắc. |
| Độ trễ | Đo từ mục tiêu vào vùng kiểm tra đến PWM bằng oscilloscope hoặc quay tốc độ cao. Thử Chest độc lập, relay ổn định, mất ACK và ba khung xác nhận. | Ghi trung vị, p95 và tối đa cho từng nhánh. Mục tiêu brief ≤200 ms cần đánh giá riêng với nhánh nhiều khung và nhánh chờ ACK. |
| Rung, Xin đường, SOS | Đo 250/80/600 ms, ba mức, 2 Hz/60 s và thời gian giữ nút 3 s. Thử GPS được cấp và từ chối. | Điện áp/duty ở tải, cảm nhận ba mẫu, số lần kích hoạt, SMS mẫu được người thử xác nhận. |
| Mất cảm biến hoặc BLE | Ngắt BLE từ app, tắt Clip, che ToF, thử cảm biến bị tháo khi đã tắt nguồn rồi cấp lại. | Phục hồi Chest tại chỗ, LED suy giảm, giới hạn ba mẫu không chắc, tỉ lệ sự kiện trùng hoặc bị mất. |
| Vỏ, RF và pin | Lắp cơ khí, đo RSSI khi đeo, chạy phiên pin có ghi tải và nhiệt. | Thời lượng pin, RSSI, hướng anten, khả năng thao tác, IP54 theo quy trình thử đã chốt. |
| Bài thử O&M | Tập trong khu vực có rào và người hỗ trợ, có tiêu chí dừng. | Mức phân biệt rung, cảnh báo sớm, mức gây giật mình, tỷ lệ phát hiện. |

Mỗi bản ghi nên có ngày, mã bo, phiên bản firmware, mã cảm biến và pin, nguồn cấp, vị trí/góc lắp, ánh sáng, mục tiêu, kết quả và đường dẫn ảnh/dạng sóng. Chốt lỗi phải xử lý và người xác nhận trước khi chuyển giai đoạn thử.

## 11. Chẩn đoán nhanh

| Hiện tượng | Thứ tự kiểm tra |
| --- | --- |
| Không có COM | Cáp data → nguồn và công tắc → đúng USB-C → BOOT/reset → cổng mới → driver USB. |
| COM có nhưng nạp thất bại | Đóng monitor → kiểm tra target và COM → vào bootloader thủ công → thử `--upload-port` tương ứng. |
| LED chớp nhanh, motor im | Gửi `status`, đo VBAT và ADC, kiểm tra nguồn motor, cổng MOSFET và đầu nối. Pin yếu hoặc phép đo ngoài dải sẽ khóa rung. |
| Chest luôn báo không chắc | Xem `L/R`, kiểm tra echo phản xạ, `valid`, `grid`, trạng thái ToF, tư thế IMU và nền đã hiệu chuẩn. |
| `tof=offline` hoặc `cal=timeout` | Xác minh đúng breakout, pinout, rail, LPn, pull-up, địa chỉ và dây; thử lại trên nền phẳng có ít nhất 10 ô mạnh. |
| Camera offline hoặc ảnh bằng 0 | Tắt nguồn để kiểm tra FPC. Đo 2,8 V/1,5 V, RESETB, XCLK, mức logic SCCB/DVP; thoát mode Trong nhà khi kiểm tra thu ảnh. |
| Chest rung nhưng Clip không rung | Kiểm tra cùng khóa, MAC, reset sau ghi NVS, pin Clip, IMU và trạng thái đang quét. Theo dõi `relay` trên Chest và `sweep` trên Clip. |
| App kết nối nhưng điều khiển không chạy | Kiểm tra cửa sổ 60 giây, pin yếu, Clip đứng yên và xung đang phát. Mở lại cửa sổ bằng nút Mode nếu đã hết. |
| SMS chưa mở hoặc GPS lỗi | Kiểm tra số điện thoại, thiết bị có ứng dụng SMS, quyền vị trí, Chrome Android và HTTPS. Có thể mở SMS chỉ với nội dung SOS khi chưa có GPS. |
| Audit báo CAM khác P1 | Kiểm tra KiCad 10.0.6, đúng file gốc, các chỉnh sửa thiết kế và phiên bản ZIP. So báo cáo trước khi lập hồ sơ revision mới. |

## 12. Điều kiện trước thử nghiệm hiện trường

- Chốt pinout và nguồn của đúng biến thể camera, ToF và JSN. Xác nhận cực pin, nguồn sạc, nhiệt và duty dưới tải.
- Xử lý hoặc chấp nhận có ghi nhận 15 cảnh báo Chest, 26 cảnh báo Clip, các đoạn DVP đổi lớp, cổ chai VBUS, mô hình STEP thiếu và các thông số xưởng.
- Hoàn thành bài đo độ trễ, tỷ lệ bỏ sót/báo nhầm, nắng, RF, pin, thao tác, SMS và O&M. Xác nhận các tình huống mất cảm biến, pin yếu và mất BLE.
- Giai đoạn hiện tại là mẫu kỹ thuật cho bàn thử và kịch bản có giám sát. Giữ gậy trắng là công cụ chính khi thử di chuyển.
