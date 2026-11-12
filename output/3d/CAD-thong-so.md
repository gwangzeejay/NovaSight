# NovaSight · thông số đọc từ file FreeCAD Alpha

Nguồn: `NovaChest_V4_Alpha.FCStd` (34 khối, sửa lần cuối 06/11/2026) và `NovaCane_Clip_V2_Alpha.FCStd` (29 khối). Đọc bằng OpenCascade 7.8 từ các file B-rep trong gói FCStd. Đơn vị mm. Hệ tọa độ: Chest X sang phải người đeo, Y từ mặt trước vào ngực, Z lên. Clip X dọc gậy (0 ở phía tay cầm), Z = 0 ở trục gậy.

Khối lượng ước tính theo thể tích B-rep với giả định PETG 1,27 g/cm³, TPU 1,21, PC 1,20. CAD không ghi vật liệu.

## NovaChest V4 Alpha

| Chi tiết | Tên CAD | Kích thước bao X × Y × Z | Khung bao | Thể tích | Khối lượng ≈ | Màu |
|---|---|---|---|---|---|---|
| Vỏ trước | `Front_Cover` | 148,00 × 23,69 × 55,00 | X -74,0…74,0, Y -10,2…13,5, Z -27,5…27,5 | 33,05 cm³ | 42,0 g | #f2f2f0 |
| Vỏ sau + ray | `Rear_Body` | 148,00 × 49,50 × 56,20 | X -74,0…74,0, Y 13,5…63,0, Z -27,5…28,7 | 42,30 cm³ | 53,7 g | #f2f2f0 |
| Khung cằm vát | `Visor` | 44,00 × 15,49 × 49,00 | X -22,0…22,0, Y -0,0…15,5, Z -27,5…21,5 | 3,00 cm³ | 3,8 g | #292b30 |
| Viền đỏ đầu dò phải | `US_Ring_R` | 30,22 × 12,32 × 30,15 | X 43,2…73,4, Y -11,3…1,0, Z -13,7…16,5 | 0,29 cm³ | 0,4 g | #cc1226 |
| Viền đỏ đầu dò trái | `US_Ring_L` | 30,22 × 12,32 × 30,15 | X -73,4…-43,2, Y -11,3…1,0, Z -13,7…16,5 | 0,29 cm³ | 0,4 g | #cc1226 |
| Kính PC camera | `Window_Camera_PC` | 16,00 × 1,00 × 16,00 | X -8,0…8,0, Y 0,5…1,5, Z 4,9…20,9 | 0,20 cm³ | 0,2 g | #b3d9f2 |
| Kính PC ToF | `Window_ToF_PC` | 12,60 × 6,16 × 8,32 | X -6,3…6,3, Y 1,7…7,9, Z -17,8…-9,4 | 0,10 cm³ | 0,1 g | #b3d9f2 |
| Giá ToF 35° | `Carrier_ToF_35deg` | 29,00 × 13,03 × 17,70 | X -14,5…14,5, Y 3,5…16,5, Z -19,3…-1,6 | 1,67 cm³ | 2,1 g | #404247 |
| Giá camera 25° | `Carrier_Camera_25deg` | 15,00 × 9,40 × 16,26 | X -7,5…7,5, Y 3,6…13,0, Z 7,7…24,0 | 0,64 cm³ | 0,8 g | #404247 |
| Nút Mode | `Button_Mode` | 13,20 × 13,20 × 4,50 | X 23,4…36,6, Y 25,9…39,1, Z 24,5…29,0 | 0,51 cm³ | 0,6 g | #292b30 |
| Chụp cáp phải | `Cable_Boot_R` | 7,20 × 7,20 × 9,00 | X 58,4…65,6, Y 29,4…36,6, Z 24,5…33,5 | 0,14 cm³ | 0,2 g | #6b7078 |
| Chụp cáp trái | `Cable_Boot_L` | 7,20 × 7,20 × 9,00 | X -65,6…-58,4, Y 29,4…36,6, Z 24,5…33,5 | 0,14 cm³ | 0,2 g | #6b7078 |
| Nút TPU che USB | `USB_Plug_TPU` | 13,20 × 7,20 × 3,00 | X 25,4…38,6, Y 17,4…24,6, Z -27,5…-24,5 | 0,16 cm³ | 0,2 g | #6b7078 |
| Đệm lưng TPU | `Back_Pad_TPU` | 141,00 × 3,00 × 50,00 | X -70,5…70,5, Y 43,0…46,0, Z -25,0…25,0 | 15,12 cm³ | 18,3 g | #6b7078 |
| Ống dẫn sáng | `Light_Pipe` | 3,00 × 6,00 × 3,00 | X -35,5…-32,5, Y -0,2…5,8, Z -17,5…-14,5 | 0,04 cm³ | 0,1 g | #b3d9f2 |
| Hộp motor vai phải | `Haptic_Pod_R` | 24,00 × 7,00 × 24,00 | X 40,0…64,0, Y 41,0…48,0, Z 43,0…67,0 | 2,56 cm³ | 3,3 g | #6b7078 |
| Hộp motor vai trái | `Haptic_Pod_L` | 24,00 × 7,00 × 24,00 | X -64,0…-40,0, Y 41,0…48,0, Z 43,0…67,0 | 2,56 cm³ | 3,3 g | #6b7078 |
| Đầu dò JSN phải | `JSN_probe_R` | 25,82 × 26,40 × 25,94 | X 44,9…70,7, Y -10,5…15,9, Z -12,2…13,7 | 5,80 cm³ | — | #121214 |
| Đầu dò JSN trái | `JSN_probe_L` | 25,82 × 26,40 × 25,94 | X -70,7…-44,9, Y -10,5…15,9, Z -12,2…13,7 | 5,80 cm³ | — | #121214 |

Vùng tránh module (KO_) bản Alpha:

- `KO_K9_41`: 72,00 × 12,00 × 33,00, X -36,0…36,0, Y 13,5…25,5, Z -8,0…25,0
- `KO_Battery_LP124065`: 76,00 × 13,50 × 43,00, X -40,0…36,0, Y 27,0…40,5, Z -21,5…21,5
- `KO_JSN_board_R`: 29,40 × 13,00 × 41,40, X 41,6…71,0, Y 26,5…39,5, Z -20,7…20,7
- `KO_US_probe_R`: 31,17 × 31,75 × 31,33, X 40,0…71,2, Y -10,7…21,1, Z -17,1…14,2
- `KO_Driver_R`: 18,00 × 12,00 × 4,00, X -18,0…0,0, Y 27,5…39,5, Z 21,5…25,5
- `KO_JSN_board_L`: 29,40 × 13,00 × 41,40, X -71,0…-41,6, Y 26,5…39,5, Z -20,7…20,7
- `KO_US_probe_L`: 31,17 × 31,75 × 31,33, X -71,2…-40,0, Y -10,7…21,1, Z -17,1…14,2
- `KO_Driver_L`: 18,00 × 12,00 × 4,00, X -38,0…-20,0, Y 27,5…39,5, Z 21,5…25,5
- `KO_IP5306`: 26,00 × 6,00 × 17,00, X -20,0…6,0, Y 19,5…25,5, Z -25,5…-8,5
- `KO_USB_C_board`: 12,00 × 9,00 × 6,00, X 26,0…38,0, Y 14,0…23,0, Z -25,5…-19,5
- `KO_Switch`: 15,00 × 9,00 × 9,00, X -39,5…-24,5, Y 16,5…25,5, Z -25,5…-16,5
- `KO_GY521`: 4,00 × 18,00 × 23,00, X 37,5…41,5, Y 18,0…36,0, Z -11,5…11,5
- `KO_Mode_tact`: 8,00 × 8,00 × 4,00, X 26,0…34,0, Y 28,5…36,5, Z 21,5…25,5
- `KO_VL53L8CX`: 25,00 × 10,65 × 13,72, X -12,5…12,5, Y 2,5…13,1, Z -18,3…-4,6
- `KO_OV3660`: 11,00 × 10,81 × 11,87, X -5,5…5,5, Y 1,6…12,4, Z 10,3…22,2

Lỗ và trụ chính (trích từ mặt trụ trong B-rep):

- **Vỏ trước**: Ø3,2 trục Y tại X -34; Z -16, Y 0 → 2,5; Ø3,2 trục Y tại X -57; Z -23, Y 7,5 → 13,5; Ø3,2 trục Y tại X -57; Z 23, Y 7,5 → 13,5; Ø3,2 trục Y tại X 57; Z -23, Y 7,5 → 13,5; Ø3,2 trục Y tại X 57; Z 23, Y 7,5 → 13,5; Ø8 trục xiên tại X 0; Z 16,04; Ø12 trục Y tại X -16; Z 15,5, Y 0 → 1,5; Ø13 trục Y tại X -64; Z 17,5, Y 10,5 → 13,5; Ø13 trục Y tại X 64; Z -17,5, Y 10,5 → 13,5
- **Vỏ sau + ray**: Ø1 trục Y tại X -2,1; Z -7, Y 47 → 55,5; Ø1 trục Y tại X -2,1; Z 7, Y 47 → 55,5; Ø1 trục Y tại X 4,1; Z -7, Y 47 → 55,5; Ø1 trục Y tại X 4,1; Z 7, Y 47 → 55,5; Ø1,2 trục Y tại X 24,9; Z 28,1, Y 38,62 → 40,29; Ø1,2 trục Y tại X 35,1; Z 28,1, Y 38,62 → 40,29; Ø1,8 trục X tại Y 33,5; Z -7,75, X 36,3 → 37,4; Ø1,8 trục X tại Y 33,5; Z 7,75, X 36,3 → 37,4; Ø2 trục X tại Y 46; Z -10,5, X -6,5 → 6,5; Ø2 trục X tại Y 46; Z 10,5, X -6,5 → 6,5; Ø2 trục Z tại X -9,5; Y 46, Z -7,5 → 7,5; Ø2 trục Z tại X 9,5; Y 46, Z -7,5 → 7,5; Ø2,4 trục Y tại X -57; Z -23, Y 13,5 → 43; Ø2,4 trục Y tại X -57; Z 23, Y 13,5 → 43; Ø2,4 trục Y tại X 57; Z -23, Y 13,5 → 43; Ø2,4 trục Y tại X 57; Z 23, Y 13,5 → 43; Ø3,5 trục Z tại X -62; Y 33, Z 25,5 → 27,5; Ø3,5 trục Z tại X 62; Y 33, Z 25,5 → 27,5; Ø4 trục Z tại X 27; Y 19, Z -27,5 → -26,7; Ø4 trục Z tại X 37; Y 23, Z -27,5 → -26,7; Ø4,5 trục Z tại X 29; Y 21, Z -26,7 → -25,5; Ø4,5 trục Z tại X 35; Y 21, Z -26,7 → -25,5; Ø5 trục Z tại X -26,5; Y 23,5, Z -27,5 → -26,3; Ø5 trục Z tại X -37,5; Y 18,5, Z -27,5 → -26,3
- **Khung cằm vát**: Ø12 trục Y tại X 16; Z 15,5, Y 0 → 1,5
- **Giá ToF 35°**: Ø2,2 trục xiên tại X -9,5; Z -9,84; Ø2,2 trục xiên tại X 9,5; Z -9,84
- **Giá camera 25°**: Ø8,2 trục xiên tại X 0; Z 14,87
- **Chụp cáp phải**: Ø3 trục Z tại X 62; Y 33, Z 24,5 → 33,5
- **Chụp cáp trái**: Ø3 trục Z tại X -62; Y 33, Z 24,5 → 33,5
- **Nút TPU che USB**: Ø3,6 trục Z tại X 27,2; Y 22,8, Z -27,5 → -26,7; Ø3,6 trục Z tại X 36,8; Y 19,2, Z -27,5 → -26,7
- **Đệm lưng TPU**: Ø4,8 trục Y tại X -57; Z -23, Y 43 → 45,4; Ø4,8 trục Y tại X -57; Z 23, Y 43 → 45,4; Ø4,8 trục Y tại X 57; Z -23, Y 43 → 45,4; Ø4,8 trục Y tại X 57; Z 23, Y 43 → 45,4; Ø9,2 trục Y tại X -6,5; Z 7,5, Y 43 → 46; Ø9,2 trục Y tại X 6,5; Z -7,5, Y 43 → 46; Ø13 trục Y tại X -64; Z -18,5, Y 43 → 45; Ø13 trục Y tại X 64; Z 18,5, Y 43 → 45
- **Hộp motor vai phải**: Ø3 trục X tại Y 46,5; Z 44,5, X 44 → 60; Ø3 trục X tại Y 46,5; Z 65,5, X 44 → 60; Ø3 trục Z tại X 41,5; Y 46,5, Z 47 → 63; Ø3 trục Z tại X 62,5; Y 46,5, Z 47 → 63; Ø8 trục Y tại X 44; Z 47, Y 42,5 → 46,5; Ø8 trục Y tại X 60; Z 63, Y 42,5 → 46,5; Ø12 trục Y tại X 52; Z 55, Y 43 → 47
- **Hộp motor vai trái**: Ø3 trục X tại Y 46,5; Z 44,5, X -60 → -44; Ø3 trục X tại Y 46,5; Z 65,5, X -60 → -44; Ø3 trục Z tại X -41,5; Y 46,5, Z 47 → 63; Ø3 trục Z tại X -62,5; Y 46,5, Z 47 → 63; Ø8 trục Y tại X -44; Z 63, Y 42,5 → 46,5; Ø8 trục Y tại X -60; Z 47, Y 42,5 → 46,5; Ø12 trục Y tại X -52; Z 55, Y 43 → 47

## NovaCane Clip V2 Alpha

| Chi tiết | Tên CAD | Kích thước bao X × Y × Z | Khung bao | Thể tích | Khối lượng ≈ | Màu |
|---|---|---|---|---|---|---|
| Vỏ trên | `Top_Shell` | 78,00 × 42,00 × 17,10 | X -0,0…78,0, Y -21,0…21,0, Z 16,2…33,3 | 10,65 cm³ | 13,5 g | #f2f2f0 |
| Yên kẹp | `Saddle` | 78,00 × 42,00 × 18,20 | X -0,0…78,0, Y -21,0…21,0, Z 1,0…19,2 | 20,80 cm³ | 26,4 g | #f2f2f0 |
| Hàm kẹp | `Jaw` | 40,00 × 42,00 × 15,70 | X 6,0…46,0, Y -21,0…21,0, Z -16,7…-1,0 | 8,99 cm³ | 11,4 g | #f2f2f0 |
| Lót TPU L3 đang lắp | `Liner_L3_in_place` | 25,00 × 28,00 × 27,98 | X 13,5…38,5, Y -14,0…14,0, Z -14,0…14,0 | 5,97 cm³ | 7,2 g | #1f1f21 |
| Nút Mode tròn | `Button_Mode_round` | 11,60 × 11,60 × 4,30 | X 30,2…41,8, Y 6,7…18,3, Z 29,5…33,8 | 0,34 cm³ | 0,4 g | #292b30 |
| Nút Xin đường | `Button_Route_bar` | 15,60 × 7,60 × 4,30 | X 28,2…43,8, Y -3,8…3,8, Z 29,5…33,8 | 0,36 cm³ | 0,5 g | #292b30 |
| Nút SOS | `Button_SOS_square` | 10,60 × 10,60 × 4,30 | X 30,7…41,3, Y -17,8…-7,2, Z 29,5…33,8 | 0,36 cm³ | 0,5 g | #cc1226 |
| Nút TPU che USB | `USB_Plug_TPU` | 2,60 × 13,20 × 7,20 | X 75,4…78,0, Y -16,6…-3,4, Z 24,3…31,5 | 0,14 cm³ | 0,2 g | #6b7078 |
| Lót L1 Ø15 | `Liner_L1_ID15` | 25,00 × 28,00 × 27,98 | X 0,0…25,0, Y -14,0…14,0, Z -14,0…14,0 | 10,34 cm³ | 12,5 g | #1f1f21 |
| Lót L2 Ø18 | `Liner_L2_ID18` | 25,00 × 28,00 × 27,98 | X 0,0…25,0, Y -14,0…14,0, Z -14,0…14,0 | 8,33 cm³ | 10,1 g | #1f1f21 |
| Lót L3 Ø21 | `Liner_L3_ID21` | 25,00 × 28,00 × 27,98 | X 0,0…25,0, Y -14,0…14,0, Z -14,0…14,0 | 5,97 cm³ | 7,2 g | #1f1f21 |
| Lót L4 Ø25 | `Liner_L4_ID25` | 25,00 × 28,00 × 27,98 | X 0,0…25,0, Y -14,0…14,0, Z -14,0…14,0 | 2,28 cm³ | 2,8 g | #1f1f21 |
| Thân gậy | `Cane_shaft` | 222,00 × 21,00 × 21,00 | X -2,0…220,0, Y -10,5…10,5, Z -10,5…10,5 | 76,89 cm³ | — | #fafafa |
| Băng đỏ | `Cane_red_band` | 60,00 × 21,10 × 21,10 | X 160,0…220,0, Y -10,6…10,6, Z -10,6…10,6 | 20,98 cm³ | — | #cc1226 |
| Tay cầm gậy | `Cane_grip` | 128,00 × 30,00 × 30,00 | X -130,0…-2,0, Y -15,0…15,0, Z -15,0…15,0 | 90,13 cm³ | — | #141414 |

Vùng tránh module (KO_) bản Alpha:

- `KO_Battery_603450`: 58,00 × 35,80 × 7,50, X 5,5…63,5, Y -17,9…17,9, Z 16,2…23,7
- `KO_ESP32_C3`: 24,00 × 18,00 × 5,60, X 51,2…75,2, Y 0,2…18,2, Z 24,7…30,3
- `KO_TP4056`: 27,00 × 18,00 × 5,60, X 48,2…75,2, Y -18,2…-0,2, Z 24,7…30,3
- `KO_GY521`: 22,00 × 17,00 × 4,00, X 3,0…25,0, Y 1,2…18,2, Z 24,7…28,7
- `KO_Driver`: 17,00 × 12,00 × 4,00, X 3,0…20,0, Y -13,2…-1,2, Z 24,7…28,7
- `KO_Tact_Mode`: 6,00 × 6,00 × 5,30, X 33,0…39,0, Y 9,5…15,5, Z 25,2…30,5
- `KO_Tact_Bar`: 6,00 × 6,00 × 5,30, X 33,0…39,0, Y -3,0…3,0, Z 25,2…30,5
- `KO_Tact_SOS`: 6,00 × 6,00 × 5,30, X 33,0…39,0, Y -15,5…-9,5, Z 25,2…30,5
- `KO_Switch`: 10,00 × 5,00 × 4,70, X 20,0…30,0, Y -19,2…-14,2, Z 24,8…29,5
- `KO_Motor_R`: 10,00 × 2,70 × 10,00, X 4,0…14,0, Y 16,5…19,2, Z 3,0…13,0
- `KO_LED_red_R`: 5,00 × 8,60 × 5,00, X 41,5…46,5, Y 12,4…21,0, Z 25,1…30,1
- `KO_Motor_L`: 10,00 × 2,70 × 10,00, X 4,0…14,0, Y -19,2…-16,5, Z 3,0…13,0
- `KO_LED_red_L`: 5,00 × 8,60 × 5,00, X 41,5…46,5, Y -21,0…-12,4, Z 25,1…30,1
- `KO_LED_white`: 8,60 × 5,00 × 5,00, X 69,4…78,0, Y -2,5…2,5, Z 17,5…22,5

Lỗ và trụ chính (trích từ mặt trụ trong B-rep):

- **Vỏ trên**: Ø1,2 trục X tại Y -16,9; Z 32,7, X 28,2 → 43,8; Ø1,2 trục Y tại X 29,1; Z 32,7, Y -17,5 → -7,5; Ø1,2 trục Y tại X 43,2; Z 32,7, Y -17,5 → -7,5; Ø2,4 trục Z tại X 32,5; Y -16, Z 30,5 → 32,3; Ø2,4 trục Z tại X 39,5; Y -9, Z 30,5 → 32,3; Ø3 trục Y tại X 20; Z 30,1, Y -20,89 → -20,3; Ø3 trục Y tại X 30; Z 25,1, Y -21 → -20,3; Ø3,2 trục Z tại X 72,5; Y -16,7, Z 16,2 → 21,1; Ø3,2 trục Z tại X 72,5; Y 16,7, Z 16,2 → 21,1; Ø4 trục Z tại X 30,8; Y -1,2, Z 30,5 → 32,3; Ø4 trục Z tại X 41,2; Y 1,2, Z 30,5 → 32,3; Ø4,5 trục X tại Y -13; Z 27,9, X 75,96 → 77,2; Ø4,5 trục X tại Y -7; Z 27,9, X 75,96 → 77,2; Ø5,2 trục X tại Y 0; Z 20, X 76,2 → 78; Ø6,4 trục Z tại X 5; Y -16, Z 16,2 → 29,5; Ø6,4 trục Z tại X 73; Y 16, Z 16,2 → 29,5; Ø10 trục Z tại X 5; Y 16, Z 16,2 → 29,3; Ø10 trục Z tại X 73; Y -16, Z 16,2 → 29,3; Ø10,4 trục Z tại X 36; Y 12,5, Z 30,5 → 32,3
- **Yên kẹp**: Ø2,4 trục Z tại X 72,5; Y -16,7, Z 3,5 → 16,2; Ø2,4 trục Z tại X 72,5; Y 16,7, Z 3,5 → 16,2; Ø4 trục Z tại X 26; Y -17,5, Z 1 → 7,7; Ø4 trục Z tại X 26; Y 17,5, Z 1 → 7,7; Ø4,4 trục Z tại X 5,15; Y -15,85, Z 16,1 → 17,7; Ø4,4 trục Z tại X 72,5; Y -16,7, Z 1 → 3,5; Ø4,4 trục Z tại X 72,5; Y 16,7, Z 1 → 3,5; Ø6,4 trục Z tại X 5,15; Y 15,85, Z 16,1 → 17,7; Ø6,4 trục Z tại X 72,85; Y -15,85, Z 16,2 → 17,7; Ø10 trục Z tại X 5; Y 16, Z 1,8 → 16,2; Ø10 trục Z tại X 73; Y -16, Z 1,8 → 16,2
- **Hàm kẹp**: Ø3,4 trục Z tại X 26; Y -17,5, Z -6 → -1; Ø3,4 trục Z tại X 26; Y 17,5, Z -6 → -1; Ø5,8 trục Z tại X 26; Y -17,5, Z -11,82 → -6; Ø5,8 trục Z tại X 26; Y 17,5, Z -11,82 → -6
- **Nút Xin đường**: Ø3,8 trục Z tại X 31; Y 1, Z 30,3 → 33; Ø3,8 trục Z tại X 41; Y -1, Z 30,3 → 33
- **Nút SOS**: Ø2 trục Z tại X 32,6; Y -9,1, Z 30,3 → 33,2; Ø2 trục Z tại X 39,4; Y -15,9, Z 30,3 → 33,2
- **Nút TPU che USB**: Ø3 trục X tại Y -15,1; Z 30, X 77,2 → 78; Ø3 trục X tại Y -4,9; Z 25,8, X 77,2 → 78

## Ốc vít và insert suy ra từ lỗ trong CAD

| Sản phẩm | Vị trí | Lỗ trong CAD | Chi tiết đề xuất |
|---|---|---|---|
| NovaChest | 4 trụ góc (±57; ±23) | Vỏ trước Ø3,2 sâu Y 7,5–13,5; vỏ sau Ø2,4 xuyên Y 13,5–43; đệm lưng hốc Ø4,8 | Insert đồng M2 Ø3,2 × 4 + vít M2 × 35 đầu tròn |
| NovaChest | 4 lỗ bo P1 H1–H4 | Chưa có trụ trong CAD | Vít M2 × 6 tự ren, cần thêm trụ (xem đối chiếu) |
| Clip | Hàm (26; ±17,5) | Hàm Ø3,4 + bậc Ø5,8 (đáy Z −6); yên Ø4,0 sâu Z 1–7,7 | Insert đồng M3 Ø4 × 5,7 + vít M3 × 12 lục giác chìm |
| Clip | Mũi gậy (72,5; ±16,7) | Yên bậc Ø4,4 (Z 1–3,5) + Ø2,4 (Z 3,5–16,2); vỏ trên Ø3,2 (Z 16,2–21,1) | Insert đồng M2 Ø3,2 × 4 + vít M2 × 16 |

## Đối chiếu bo P1 (KiCad) với CAD Alpha

Giao khối OpenCascade giữa đường bao bo thật + khối linh kiện (chiều cao ước lượng theo footprint) với các chi tiết CAD:

- Không va chạm với vỏ, khung, giá camera/ToF, pin, board JSN, đầu dò (NovaChest) và vỏ trên, yên, nút, pin, motor (Clip).
- Nút TPU che USB-C lấn 0,27 mm vào miệng cổng J1 và 0,3 mm vào mép bo ở cả hai sản phẩm.
- NovaChest: nút Mode trong CAD ở (30; Y 32,5), cần bấm SW2 trên bo P1 ở (30; Y 21,75; đỉnh Z 23,75), lệch 10,75 mm.
- NovaChest: CAD chưa có trụ cho 4 lỗ bo P1. Trụ cần dài: H2 20,1 mm và H3, H4 9,9 mm từ vỏ trước; H1 12,1 mm và rơi lên giá ToF.
- NovaChest: ống dẫn sáng kết thúc ở Y 5,8, LED D1 ở Y ≈ 22,0, thiếu khoảng 16 mm.
- NovaChest: giá camera dựng cho OV3660 (lỗ ống kính Ø8,2); P1 dùng OV5640 K1_283, cần đo lại.
- Clip: đỉnh tact EVQP2 ở Z 28,8, đáy nắp nút ở Z 29,5, hở 0,7 mm.
- Clip: khe USB-C, 2 lỗ LED đỏ, lỗ LED trắng, 3 nút và vùng motor khớp vị trí linh kiện bo P1 trong ±0,1 mm.
