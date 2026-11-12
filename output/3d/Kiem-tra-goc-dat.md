# NovaSight · Kiểm tra góc đặt cảm biến và gậy

Ngày 11/11/2026. Số liệu tính từ góc trong CAD Alpha (giá ToF 35°, giá camera 25°, đầu dò siêu âm lên 15° và ra 15°), tâm Chest cao 1,25 m và logic firmware P1 (`nova_core.cpp`, `chest/main.cpp`, `device.cpp`). Kết quả chạy tuyến lấy từ chế độ "Mô phỏng sử dụng" trong trang 3D (`NovaSight-3D.html`, bảng "Kiểm tra góc đặt").

## Kết luận nhanh

| Hạng mục | Thiết kế hiện tại | Vấn đề | Đề xuất |
|---|---|---|---|
| ToF chúc xuống | 35° | Hàng tia xa nhất chạm đất ở 3,78 m, ngoài vùng firmware xét (0,55–3,0 m) và sát giới hạn 4 m. 4/16 ô bị bỏ phí. | 40° (tối thiểu 39,3° ở chiều cao 1,25 m; 37,7° ở 1,15 m; 40,9° ở 1,35 m). Sửa cùng hằng số `35.0f` trong `FloorTrack::update` và giá `Carrier_ToF_35deg`. |
| Siêu âm nghiêng ra | 15° | Nếu chùm thật hẹp (±12–15°) có khe mù 11–27 cm thẳng trước mặt ở 1,5 m. Nếu chùm rộng (±20°) quét ngang 1,11 m mỗi bên, dễ báo nhầm khi đi sát rào hoặc tường. | 10°, sau khi đo độ rộng chùm thật của JSN-SR04T. |
| Siêu âm chếch lên | 15° | Phủ tầm đầu 1,75 m từ 0,71 m trở ra. Hợp lý. | Giữ 15°. |
| Camera chúc xuống | 25° | Nhìn mặt đất 1,22 m đến 15,7 m, không lộ trời. Hợp lý. | Giữ 25°. Đo lại ống kính cụm OV5640. |
| Gậy | dài 1,26 m, cung 0,56 m | Đúng kỹ thuật O&M. Nhưng Clip chỉ coi là "đang quét" khi tốc độ góc > 38°/s, tức từ khoảng 0,35 m/s. Khi người dùng đi chậm lại gần chỗ nguy hiểm, cảnh báo chuyển hết sang vai. | Hạ ngưỡng `angular > 38.0f` xuống khoảng 25°/s, hoặc giữ trạng thái quét lâu hơn 1000 ms. |
| Ngưỡng vật cản | `1200 × v + 300`, kẹp 1,5–2,5 m | Chỉ tính tốc độ người đeo. Người đi ngược chiều 1 m/s chỉ được báo ở khoảng 1,1 m, còn 0,6 s. | Tính thêm tốc độ tiếp cận từ hai lần đo siêu âm liên tiếp cùng bên, dùng `max(tốc độ đi, tốc độ tiếp cận)`. |

## So sánh trên tuyến mô phỏng 50 m (chế độ Đi bộ)

Khoảng cách lúc thiết bị báo lần đầu và số giây còn lại để phản ứng. "Đề xuất" = ToF 40°, siêu âm ra 10°, ngưỡng quét 25°/s, ngưỡng vật cản theo tốc độ tiếp cận.

| Tình huống | 1,0 m/s hiện tại | 1,0 m/s đề xuất | 1,3 m/s hiện tại | 1,3 m/s đề xuất |
|---|---|---|---|---|
| Cành cây ngang đầu bên trái | 1,31 m · 1,3 s | 1,50 m · 1,5 s | 1,42 m · 1,1 s | 1,61 m · 1,2 s |
| Ổ gà sâu 20 cm | 2,06 m · 2,1 s | 2,65 m · 2,6 s | 2,14 m · 1,6 s | 2,80 m · 2,2 s |
| Cột điện lệch phải | 1,22 m · 1,2 s | 1,42 m · 1,4 s | 1,45 m · 1,1 s | 1,45 m · 1,1 s |
| Thanh sắt ngang ngực | 1,28 m · 1,3 s | 1,27 m · 1,3 s | 1,40 m · 1,1 s | 1,40 m · 1,1 s |
| Mép vỉa hè hạ 17 cm | 2,13 m · 2,1 s | 2,79 m · 2,8 s | 2,13 m · 1,6 s | 2,80 m · 2,2 s |
| Bậc lên 17 cm | 1,82 m · 1,8 s | 2,37 m · 2,4 s | 1,84 m · 1,4 s | 2,38 m · 1,8 s |
| Người đi ngược chiều | 1,14 m · 0,6 s | 2,03 m · 1,0 s | 1,23 m · 0,5 s | 1,97 m · 0,9 s |
| Báo nhầm khi đi sát rào tôn cao 2 m | 0 | 0 | 1 | 0 |
| Va chạm | 0 | 0 | 0 | 0 |

Vật cản tầm đầu và ngực vẫn chỉ còn khoảng 1,1–1,5 s ở 1,3 m/s, do ngưỡng tối đa và 3 lần đo xác nhận (khoảng 0,3 s) của siêu âm. Người đi ngược chiều vẫn dưới mục tiêu 1,2 s ngay cả khi tính tốc độ tiếp cận.

## Camera hỗ trợ ToF (ý tưởng nhóm, chưa có trong firmware P1)

Firmware P1 chỉ dùng camera để chẩn đoán (nhận PID `0x5640`, thu JPEG QVGA). Mô phỏng thêm camera theo kiến trúc ưu tiên khoảng cách trong mô tả sản phẩm: camera 5 khung/giây không tự phát cảnh báo vật cản, chỉ hỗ trợ cảnh báo mặt đất theo ba luật:

1. ToF đã thấy cùng một thay đổi mặt đất ở 2 khung và camera đồng ý (độ tin cậy ≥ 60 %, lệch ≤ 0,6 m) thì xác nhận luôn, không chờ khung thứ 3.
2. ToF không tin cậy (nắng gắt) hoặc không đo được (mặt nước phản xạ gương), camera thấy cùng một mục tiêu ≥ 3 khung liên tiếp với độ tin cậy ≥ 70 % trong 0,8–3,0 m thì báo mặt đất (3 xung ngắn).
3. Khi camera đang canh thay ToF thì Chest không phát mẫu "không chắc". Ban đêm và ở chế độ Trong nhà (firmware tạm dừng camera) thì camera không tham gia.

Kết quả trên tuyến 50 m, 1,0 m/s, thiết kế hiện tại:

| Điều kiện | Không camera | Có camera |
|---|---|---|
| Ban ngày, ổ gà | ToF 2,06 m | ToF + camera 2,10 m (xác nhận sau 2 khung) |
| Ban ngày, vũng nước | chỉ gậy chạm ở 0,9 m | camera báo ở 2,85 m |
| Nắng gắt | 3 lần "không chắc", hố và bậc chỉ gậy phát hiện | camera báo ổ gà 2,86 m, vũng nước 2,85 m, mép vỉa hè 2,99 m, bậc lên 2,89 m; không rung "không chắc" |
| Ban đêm | ToF bình thường, vũng nước chỉ gậy phát hiện | giống không camera |

Mô hình nhận diện là giả định: độ tin cậy tính theo kích thước mục tiêu trên ảnh 320 × 240 (thấu kính 41° dọc) và hệ số ánh sáng, có nhiễu và bỏ sót ngẫu nhiên. Ảnh mô phỏng sạch hơn ảnh thật (không lóa, không mờ chuyển động, không bóng đổ giống hố). Cần thu ảnh thật từ cụm OV5640 trên tuyến đi để huấn luyện và đo tỉ lệ báo nhầm trước khi đưa vào firmware.

## Cần đo trên mẫu thật trước khi chốt

1. Độ rộng chùm JSN-SR04T với cột Ø10 cm, thân người và tấm phẳng ở 0,5 / 1 / 1,5 / 2 m, lệch 0–40° khỏi trục. Bảng kiểm tra đang giả định nửa chùm 20°.
2. Thứ tự hàng ToF: firmware coi hàng 0 là hàng chúc sâu nhất. Đặt vật lên sàn gần rồi xa, xem hàng nào đổi trong lệnh `grid` (Cookbook mục hiệu chuẩn bước 2).
3. Trục và dấu pitch của MPU-6050 trên Chest (firmware ghi chú "Confirm the axis/sign").
4. Chiều trái/phải: theo hệ trục thuận của CAD và KiCad, +X là bên trái người đeo, nhưng J5 JSN_R và J7 MOTOR_R nằm ở +X.
5. Tốc độ góc quét gậy thực tế của người dùng khi đi chậm (0,3–0,5 m/s) so với ngưỡng 38°/s.

## Giới hạn của mô phỏng

Cảm biến là mô hình hình học: siêu âm là bó tia trong chùm, chỉ nhận vọng khi mặt phẳng nhẵn lệch dưới 60° khỏi pháp tuyến (bề mặt nhám như cây, cột, người, rào tôn luôn có vọng). ToF là một tia mỗi ô. Chưa mô phỏng nhiễu đa đường, vọng yếu, ánh nắng thật. Người dùng ảo phản xạ sau 0,35 s rồi dừng và né. Giả định thấu kính camera 41° theo chiều dọc.
