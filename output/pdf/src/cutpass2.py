p = "build.py"
L = open(p, encoding="utf8").read().split("\n")
def cut(a, b):  # 1-indexed inclusive
    global L
    L[a-1:b] = []
def sub(a, b, text):
    global L
    L[a-1:b] = text.split("\n")
# bottom to top
cut(891, 897)                 # việc cơ khí
cut(732, 879)                 # kiểm chứng, lộ trình, rủi ro, 6 điểm
# Clip
cut(685, 692)                 # routed trial page
sub(650, 662, '''doc.std('NovaCane Clip Cơ khí và vị trí linh kiện chính', 'Tọa độ trong hệ của bo: X dọc thân gậy (0 ở đầu tay cầm), Y ngang; kích thước lấy từ file PCB.', 2)
bb_ = kipcb.board_bbox(CL)
rows = [['Hạng mục', 'Giá trị'],
        ['Đường bao', f'{bb_[2] - bb_[0]:.1f} × {bb_[3] - bb_[1]:.1f} mm, 2 lớp, dày 1,0 mm, có 2 rãnh LED'.replace('.', ',')]]
for k, nm in [('SW2', 'SW2 Mode'), ('SW3', 'SW3 Xin đường'), ('SW4', 'SW4 SOS'), ('SW1', 'SW1 công tắc gạt'), ('J1', 'J1 USB-C'),
              ('D1', 'D1 LED đỏ'), ('D2', 'D2 LED đỏ'), ('D3', 'D3 LED trắng'), ('U1', 'U1 ESP32-C3-MINI-1'), ('U6', 'U6 MPU-6050')]:
    x, y_ = brief_xy_clip(fpc[k])
    rows.append([nm, f'X {x:+.1f} ; Y {y_:+.1f}'.replace('.', ',').replace('-', '−')])
doc.table(64, H - 125, [320, 616], rows, size=14, pad=5.5)''')
# Chest
sub(452, 469, '''doc.std('NovaChest Cơ khí và vị trí linh kiện chính', 'Tọa độ trong hệ của bo: X sang phải người đeo, Z hướng lên, gốc ở tâm bo; lấy từ file PCB.', 2)
bb_ = kipcb.board_bbox(CH)
rows = [['Hạng mục', 'Giá trị'],
        ['Đường bao', f'{bb_[2] - bb_[0]:.1f} × {bb_[3] - bb_[1]:.1f} mm, 4 lớp, dày 1,6 mm'.replace('.', ',')]]
for k, nm in [('H1', 'H1 lỗ NPTH Ø2,2'), ('H2', 'H2 lỗ NPTH Ø2,2'), ('H3', 'H3 lỗ NPTH Ø2,2'), ('H4', 'H4 lỗ NPTH Ø2,2'),
              ('J1', 'J1 USB-C'), ('SW1', 'SW1 công tắc gạt'), ('SW2', 'SW2 nút Mode'), ('J4', 'J4 pin'), ('D1', 'D1 LED trạng thái')]:
    x, z = brief_xy_chest(fpm[k])
    rows.append([nm, f'X {x:+.1f} ; Z {z:+.1f}'.replace('.', ',').replace('-', '−')])
doc.table(64, H - 125, [320, 616], rows, size=14, pad=5.5)''')
# values-only page
sub(426, 439, '''doc.std('Các giá trị đã tính trên sơ đồ', 'Giá trị chia áp, xung KEY và buck lấy từ linh kiện trong schematic.', 1)
rows = [['Mạch', 'Công thức', 'Kết quả'],
        ['Buck 3V3 (Chest)', '0,6 × (1 + 680k/150k)', '3,32 V'],
        ['Cầu chia đo pin 470 kΩ / 470 kΩ', 'VBAT / 2', '2,1 V ở 4,2 V; rò 4,5 µA'],
        ['VBUS_DET 68 kΩ / 100 kΩ', 'VBUS × 100/168', '2,98 V ở 5,0 V; 2,68 V ở 4,5 V'],
        ['ECHO JSN 10 kΩ / 15 kΩ', '5 V × 15/25', '3,0 V ở 5,0 V; 3,15 V ở 5,25 V'],
        ['Xung KEY 1 µF × 470 kΩ', 't = RC · ln(3,7/1,5)', '0,42 s (cửa sổ 30 ms – 2 s)'],
        ['R_PROG TP4056 (Clip) 3,0 kΩ', 'I = 1200 / R', '400 mA']]
doc.table(64, H - 120, [380, 260, 296], rows, size=16, pad=8)''')
cut(413, 425)                 # ngân sách
cut(263, 274)                 # quy tắc
cut(233, 251)                 # tiến độ
sub(198, 219, '''doc.std('Bố cục báo cáo', None, 0)
items = [('01', 'Tổng quan', 'Phạm vi, hai bo và yêu cầu gia công'), ('02', 'Vận hành', 'Cây nguồn, khối chức năng, power-path'),
         ('03', 'Phần cứng', 'Layout, schematic phóng to, pinout, BOM'), ('04', 'Tham khảo', 'Bảo vệ trên sơ đồ và tài liệu tham khảo')]
for i, (n, t, s) in enumerate(items):
    col, row = i // 2, i % 2
    x = 64 + col * 480; y = H - 190 - row * 140
    c.setFillColor(RED); c.setFont('ArB', 22); c.drawString(x, y, n)
    c.setFillColor(NAVY); c.setFont('ArB', 24); c.drawString(x + 60, y, t)
    c.setFillColor(GRAY); c.setFont('Ar', 16); c.drawString(x + 60, y - 28, s)

doc.std('Phạm vi thiết kế đã thực hiện', None, 0)
sc = [('01', 'Schematic', 'Hai schematic KiCad A1, chia khối MCU/boot, nguồn và sạc, USB-C, IMU/I²C, camera, motor/đèn và test point.'),
      ('02', 'Footprint và đặt linh kiện', f'{nfp_ch} linh kiện trên NS-CHEST-MB và {nfp_cl} linh kiện trên NS-CLIP-MB, đặt trong đường bao theo brief cơ khí.'),
      ('03', 'BOM và pinout', 'Bảng vật tư, gán chân MCU, đầu nối, FPC camera và điểm đo của cả hai bo.'),
      ('04', 'Dữ liệu xuất', 'Schematic PDF, BOM CSV và mô hình STEP của bo đã lắp linh kiện.')]
for i, (n, t, s) in enumerate(sc):
    y = H - 140 - i * 100
    c.setFillColor(RED); c.setFont('ArB', 22); c.drawString(64, y, n)
    c.setFillColor(NAVY); c.setFont('ArB', 22); c.drawString(124, y, t)
    doc.text(124, y - 10, 860, s, 17, INK)''')
cut(162, 197)                 # status summary
open(p, "w", encoding="utf8").write("\n".join(L))
print("cut ok")

