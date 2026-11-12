import sys, os, json, csv, glob, collections, re, datetime, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import pymupdf

BASE = r"D:\Học tập\Claude_project\NovaSight new\hardware"
OUTDIR = r"D:\Học tập\Claude_project\NovaSight new\output\pdf"
os.makedirs(OUTDIR, exist_ok=True)
TMP = os.path.join(os.environ.get('TEMP', '.'), 'ns_pcb_tmp.pdf')
OUT = os.path.join(OUTDIR, 'NovaSight_PCB.pdf')

CH = kipcb.load(BASE + r"\NS-CHEST-MB\NS-CHEST-MB.kicad_pcb")
CL = kipcb.load(BASE + r"\NS-CLIP-MB\NS-CLIP-MB.kicad_pcb")
CR = kipcb.load(BASE + r"\NS-CLIP-MB\routing\NS-CLIP-MB_routed.kicad_pcb")
SCH = {'CH': BASE + r"\NS-CHEST-MB\exports\NS-CHEST-MB.pdf", 'CL': BASE + r"\NS-CLIP-MB\exports\NS-CLIP-MB.pdf"}
DES = json.load(open(BASE + r"\design_final.json", encoding='utf8'))


def jl(p): return json.load(open(p, encoding='utf8'))
DRC = {
    'CH': jl(BASE + r"\NS-CHEST-MB\review\NS-CHEST-MB-drc.json"),
    'CL': jl(BASE + r"\NS-CLIP-MB\review\NS-CLIP-MB-drc.json"),
    'CR': jl(BASE + r"\NS-CLIP-MB\review\routed\NS-CLIP-MB_routed-drc.json"),
}
ERC = {'CH': jl(BASE + r"\NS-CHEST-MB\review\NS-CHEST-MB-erc.json"), 'CL': jl(BASE + r"\NS-CLIP-MB\review\NS-CLIP-MB-erc.json")}


def drc_counts(d):
    c = collections.Counter((v['severity'], v['type']) for v in d['violations'])
    err = sum(n for (s, t), n in c.items() if s == 'error')
    warn = sum(n for (s, t), n in c.items() if s == 'warning')
    return c, err, warn, len(d['unconnected_items'])


def erc_counts(d):
    v = [x for sh in d['sheets'] for x in sh['violations']]
    return len([x for x in v if x['severity'] == 'error']), len([x for x in v if x['severity'] == 'warning']), v


def bom(b):
    rows = list(csv.DictReader(open(BASE + rf"\{b}\exports\{b}-bom.csv", encoding='utf8')))
    return rows


def refnum(r):
    m = re.match(r'([A-Za-z]+)(\d+)', r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)


def compact_refs(refs):
    refs = sorted(refs, key=refnum)
    out = []; i = 0
    while i < len(refs):
        j = i
        while j + 1 < len(refs) and refnum(refs[j + 1])[0] == refnum(refs[i])[0] and refnum(refs[j + 1])[1] == refnum(refs[j])[1] + 1:
            j += 1
        out.append(refs[i] if j == i else (f"{refs[i]}–{refs[j]}" if j > i + 1 else f"{refs[i]}, {refs[j]}"))
        i = j + 1
    return ', '.join(out)


def bom_groups(b):
    rows = bom(b)
    g = collections.OrderedDict()
    for r in rows:
        fp = r['Footprint'].split(':')[-1]
        refs = [x.strip() for x in r['Refs'].split(',')]
        if fp.startswith('TestPoint'):
            key = ('TP', 'Test point', fp)
        else:
            key = (r['Value'].replace('_', ' '), fp)
            key = ('X',) + key
        ent = g.setdefault(key, {'refs': [], 'dnp': 0, 'qty': 0})
        ent['refs'] += refs; ent['qty'] += int(r['Qty'])
        if r['DNP']: ent['dnp'] += 1
    out = []
    for k, v in g.items():
        out.append((compact_refs(v['refs']) + (' (DNP)' if v['dnp'] and v['dnp'] == len(v['refs']) else ''), k[1], k[2], str(v['qty'])))
    pref = {'U': 0, 'Q': 1, 'D': 2, 'L': 3, 'F': 4, 'J': 5, 'S': 6, 'C': 7, 'R': 8, 'T': 9}
    out.sort(key=lambda r: (pref.get(r[0][0], 10), refnum(r[0].split(',')[0].split('–')[0])))
    return out, sum(int(r['Qty']) for r in rows), len(rows)


# ----------------------------------------------------------------------------
doc = Doc(TMP)
c = doc.c
today = '06/11/2026'
dc_ch, e_ch, w_ch, u_ch = drc_counts(DRC['CH'])
dc_cl, e_cl, w_cl, u_cl = drc_counts(DRC['CL'])
dc_cr, e_cr, w_cr, u_cr = drc_counts(DRC['CR'])
ee_ch, ew_ch, ev_ch = erc_counts(ERC['CH'])
ee_cl, ew_cl, ev_cl = erc_counts(ERC['CL'])
npads_ch = sum(len(f['pads']) for f in CH.fps); npads_cl = sum(len(f['pads']) for f in CL.fps)
nfp_ch = len([f for f in CH.fps if not f['ref'].startswith(('FID', 'H'))])
nfp_cl = len([f for f in CL.fps if not f['ref'].startswith(('FID', 'H'))])
bg_ch, qty_ch, nl_ch = bom_groups('NS-CHEST-MB'); bg_cl, qty_cl, nl_cl = bom_groups('NS-CLIP-MB')
parity_ch = len(DRC['CH'].get('schematic_parity', [])); parity_cl = len(DRC['CL'].get('schematic_parity', []))
fab_files = [os.path.basename(p) for p in glob.glob(BASE + r"\*\exports\*")] + [os.path.basename(p) for p in glob.glob(BASE + r"\*\*gerber*")]
has_gerber = any(f.lower().endswith(('.gbr', '.drl', '.zip', '.gtl')) for f in fab_files)
n_cu_ch = 4

def rat(d):
    out = []
    for u in d['unconnected_items']:
        it = u['items']
        if len(it) >= 2:
            out.append(((it[0]['pos']['x'], it[0]['pos']['y']), (it[1]['pos']['x'], it[1]['pos']['y'])))
    return out
RAT = {'CH': rat(DRC['CH']), 'CL': rat(DRC['CL']), 'CR': rat(DRC['CR'])}

def legend(y):
    c.setStrokeColor(HexColor('#E0B93A')); c.setLineWidth(1.2); c.setDash(3, 2); c.line(64, y + 4, 94, y + 4); c.setDash()
    c.setFillColor(GRAY); c.setFont('Ar', 12)
    c.drawString(102, y, 'Kết nối chưa nối (ratsnest, lấy từ DRC)')
    c.setFillColor(HexColor('#FFFFFF')); c.setStrokeColor(RED); c.roundRect(360, y - 3, 22, 14, 2, stroke=1, fill=1)
    c.setFillColor(GRAY); c.drawString(390, y, 'Nhãn linh kiện chính')

CH_FRONT = (50 - 0.0, 50, 150, 99.6)


def cover():
    doc.new(0)
    c.setFillColor(RED); c.rect(0, 52, 570, H - 52, stroke=0, fill=1)
    c.setFillColor(HexColor('#FFFFFF')); c.setFont('ArB', 60); c.drawString(64, H - 150, 'NOVASIGHT')
    c.setFont('ArB', 30); c.drawString(64, H - 232, 'Hồ sơ thiết kế PCB')
    c.setFont('ArB', 26); c.drawString(64, H - 300, 'NS-CHEST-MB')
    c.drawString(64, H - 336, 'NS-CLIP-MB')
    c.setFont('Ar', 20); c.drawString(64, H - 400, 'NovaChest · NovaCane Clip')
    c.setFont('Ar', 20); c.drawString(64, H - 438, 'Schematic, layout, BOM và kiểm tra DRC')
    c.setFont('Ar', 18); c.drawString(64, H - 490, today)
    c.drawString(64, H - 515, 'Dự án NovaSight')
    c.setFillColor(NAVY); c.setFont('ArB', 17)
    c.drawString(620, H - 58, 'NS-CHEST-MB (4 lớp · 100 × 49,6 mm)')
    draw_pcb(c, CH, 620, H - 70, 400, 235, 'F', frame=True)
    c.setFillColor(NAVY); c.setFont('ArB', 17)
    c.drawString(620, H - 330, 'NS-CLIP-MB (2 lớp · 73,4 × 37,4 mm)')
    draw_pcb(c, CL, 620, H - 342, 400, 200, 'F', frame=True)
    doc.footer()


cover()

# ============================ 1. TỔNG QUAN ===================================
doc.std('Tổng quan thiết kế PCB', None, 0)
draw_pcb(c, CH, 64, H - 100, 330, 175, 'F')
c.setFont('ArB', 13); c.setFillColor(GRAY); c.drawString(64, H - 288, 'NS-CHEST-MB')
draw_pcb(c, CL, 64, H - 305, 330, 170, 'F')
c.setFont('ArB', 13); c.setFillColor(GRAY); c.drawString(64, H - 487, 'NS-CLIP-MB')
doc.text(430, H - 105, 580,
         'NS-CHEST-MB là bo chính của NovaChest: 4 lớp, 100 × 49,6 × 1,6 mm, đặt đứng sau mặt trước thiết bị. '
         'Bo mang ESP32-S3-WROOM-1-N16R8, IP5306 (sạc và boost 5 V), buck 3,3 V, hai LDO camera, MPU-6050, '
         'hai mạch lái motor, buffer TRIG cho cảm biến siêu âm, USB-C, công tắc và nút.', 16)
doc.text(430, H - 245, 580,
         'NS-CLIP-MB là bo chính của NovaCane Clip: 2 lớp, 73,4 × 37,4 × 1,0 mm, đặt ngang trên pin. '
         'Bo mang ESP32-C3-MINI-1, TP4056 + DW01A + FS8205A, mạch chia tải, LDO 3,3 V, MPU-6050, hai mạch lái motor, '
         'mạch đèn "Xin đường", ba nút, USB-C và công tắc.', 16)
doc.text(430, H - 385, 580,
         'Cảm biến lớn, pin và motor vẫn là linh kiện rời, nối vào bo qua connector. '
         'Hồ sơ này tổng hợp schematic, layout, BOM, pinout và kết quả ERC/DRC của hai bo tại thời điểm xuất ' + today + '.', 16)


def status_summary():
    doc.std('Tóm tắt trạng thái thiết kế', 'Đọc nhanh: màu xanh là xong, vàng là một phần, đỏ là chưa xong. Số liệu lấy từ file KiCad ngày ' + today + '.', 0)
    rows = [
        ('Schematic và ERC', (OK, f'Xong · {ee_ch} lỗi, {ew_ch} cảnh báo'), (OK, f'Xong · {ee_cl} lỗi, {ew_cl} cảnh báo')),
        ('Đặt linh kiện', (OK, f'Xong · {nfp_ch} linh kiện, khớp schematic'), (OK, f'Xong · {nfp_cl} linh kiện, khớp schematic')),
        ('Khớp brief cơ khí', (WARN, 'Lệch: lỗ H1 và vị trí U4'), (OK, 'Nút, USB-C, LED khớp brief')),
        ('Định tuyến', (BAD, f'Chưa · {len(CH.segs)} đoạn dây'), (BAD, f'Chưa · bản thử {len(CR.segs)} đoạn, chưa đạt DRC')),
        ('DRC', (BAD, f'{e_ch} lỗi · {u_ch} kết nối hở'), (BAD, f'{e_cl} lỗi · {u_cl} kết nối hở')),
        ('Dữ liệu sản xuất', (WARN, 'Có BOM, PDF, STEP · chưa Gerber, CPL, DXF'), (WARN, 'Có BOM, PDF, STEP · chưa Gerber, CPL, DXF')),
    ]
    x0, y0 = 64, H - 135
    cw = [230, 355, 355]
    c.setFillColor(HEAD); c.rect(x0, y0 - 40, sum(cw), 40, stroke=0, fill=1)
    c.setFillColor(NAVY); c.setFont('ArB', 17)
    c.drawString(x0 + 14, y0 - 26, 'Hạng mục'); c.drawString(x0 + cw[0] + 14, y0 - 26, 'NS-CHEST-MB'); c.drawString(x0 + cw[0] + cw[1] + 14, y0 - 26, 'NS-CLIP-MB')
    y = y0 - 40
    for name, a, b in rows:
        rh = 52
        c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(x0, y - rh, x0 + sum(cw), y - rh)
        c.setFillColor(INK); c.setFont('ArB', 17); c.drawString(x0 + 14, y - 31, name)
        xx = x0 + cw[0]
        for col_, txt in (a, b):
            c.setFillColor(col_); c.circle(xx + 22, y - rh / 2, 9, stroke=0, fill=1)
            c.setFillColor(INK); c.setFont('Ar', 15)
            lines = simpleSplit(txt, 'Ar', 15, cw[1] - 58)
            yy = y - rh / 2 + (len(lines) - 1) * 8 - 5
            for ln in lines:
                c.drawString(xx + 42, yy, ln); yy -= 17
            xx += cw[1]
        y -= rh
    c.setStrokeColor(LINE); c.rect(x0, y, sum(cw), y0 - y, stroke=1, fill=0)
    c.line(x0 + cw[0], y, x0 + cw[0], y0); c.line(x0 + cw[0] + cw[1], y, x0 + cw[0] + cw[1], y0)
    doc.text(64, y - 16, 940, 'Kết luận: hai bo đã có schematic và bản đặt linh kiện đủ để review, nhưng chưa đủ điều kiện đặt gia công.', 16, INK)

status_summary()

doc.std('Bố cục báo cáo', None, 0)
items = [('01', 'Tổng quan', 'Phạm vi, hai bo và tiến độ'), ('02', 'Vận hành', 'Cây nguồn, khối chức năng, power-path'),
         ('03', 'Phần cứng', 'Layout, schematic phóng to, pinout, BOM'), ('04', 'Kiểm chứng', 'ERC/DRC và bộ dữ liệu xuất'),
         ('05', 'Lộ trình', 'Các chặng hoàn thiện và bring-up'), ('06', 'Rủi ro', 'Điểm chưa chắc và tài liệu tham khảo')]
for i, (n, t, s) in enumerate(items):
    col, row = i // 3, i % 3
    x = 64 + col * 480; y = H - 175 - row * 112
    c.setFillColor(RED); c.setFont('ArB', 22); c.drawString(x, y, n)
    c.setFillColor(NAVY); c.setFont('ArB', 24); c.drawString(x + 60, y, t)
    c.setFillColor(GRAY); c.setFont('Ar', 16); c.drawString(x + 60, y - 28, s)

doc.std('Phạm vi thiết kế đã thực hiện', None, 0)
sc = [('01', 'Schematic', 'Hai schematic KiCad A1, chia khối MCU/boot, nguồn và sạc, USB-C, IMU/I²C, camera, motor/đèn và test point.'),
      ('02', 'Footprint và đặt linh kiện', f'{nfp_ch} linh kiện trên NS-CHEST-MB và {nfp_cl} linh kiện trên NS-CLIP-MB, đặt trong đường bao theo brief cơ khí.'),
      ('03', 'Định tuyến', 'Đường nguồn, pour đồng và via khâu GND đang dang dở. Bản định tuyến thử của NS-CLIP-MB chưa đạt DRC.'),
      ('04', 'Dữ liệu xuất', 'Đã có schematic PDF, BOM CSV và mô hình STEP. Chưa có Gerber, file khoan, CPL và DXF.')]
for i, (n, t, s) in enumerate(sc):
    y = H - 140 - i * 100
    c.setFillColor(RED); c.setFont('ArB', 22); c.drawString(64, y, n)
    c.setFillColor(NAVY); c.setFont('ArB', 22); c.drawString(124, y, t)
    doc.text(124, y - 10, 860, s, 17, INK)

doc.std('Hai bo mạch chính của NovaSight', None, 0)
rows = [['Hạng mục', 'NS-CHEST-MB (NovaChest)', 'NS-CLIP-MB (NovaCane Clip)'],
        ['Kích thước · lớp', '100 × 49,6 × 1,6 mm · 4 lớp', '73,4 × 37,4 × 1,0 mm · 2 lớp'],
        ['MCU', 'ESP32-S3-WROOM-1-N16R8', 'ESP32-C3-MINI-1-N4X'],
        ['Nguồn', 'IP5306, công tắc tải Q1, SY8088IAAC, ME6211 ×2', 'TP4056, DW01A + FS8205A, chia tải D4/Q2, AP2112K'],
        ['Cảm biến', 'MPU-6050; connector ToF, camera, 2 JSN-SR04T', 'MPU-6050 (chân GY-521 dự phòng)'],
        ['Phản hồi', '2 mạch lái motor (J7, J8), LED trạng thái', '2 mạch lái motor, 3 LED "Xin đường", LED trạng thái'],
        ['Giao diện', 'USB-C, công tắc, Mode, BOOT, RESET', 'USB-C, công tắc, Mode, Xin đường, SOS'],
        ['Test point', f"{len([f for f in CH.fps if f['ref'].startswith('TP')])} pad Ø1,0 mm", f"{len([f for f in CL.fps if f['ref'].startswith('TP')])} pad Ø1,0 mm"],
        ['Linh kiện · pad', f'{nfp_ch} · {npads_ch}', f'{nfp_cl} · {npads_cl}'],
        ['Dòng BOM · tổng SL', f'{nl_ch} · {qty_ch}', f'{nl_cl} · {qty_cl}']]
doc.table(64, H - 120, [180, 380, 376], rows, size=16.5, pad=8)

# --- tiến độ
doc.std('Tiến độ thiết kế tại thời điểm xuất hồ sơ', 'Trạng thái đọc trực tiếp từ file KiCad và báo cáo ERC/DRC ngày ' + today + '.', 0)
steps = [('Schematic', f'ERC: 0 lỗi\n{ew_ch} + {ew_cl} cảnh báo', OK),
         ('Đặt linh kiện', f'Đối chiếu schematic ↔ PCB: {parity_ch + parity_cl} sai khác', OK),
         ('Định tuyến', 'CHEST: chưa\nCLIP: thử, chưa đạt', BAD),
         ('DRC', f'{u_ch} + {u_cl} kết nối hở\ncòn lỗi khoan, khoảng hở', BAD),
         ('Xuất sản xuất', 'Có: BOM, PDF, STEP\nChưa: Gerber, CPL, DXF', WARN)]
for i, (t, s, col) in enumerate(steps):
    x = 64 + i * 188
    c.setFillColor(HexColor('#FFFFFF')); c.setStrokeColor(LINE); c.rect(x, H - 330, 172, 160, stroke=1, fill=1)
    c.setFillColor(col); c.rect(x, H - 176, 172, 6, stroke=0, fill=1)
    c.setFillColor(NAVY); c.setFont('ArB', 18); c.drawString(x + 12, H - 205, t)
    doc.text(x + 12, H - 215, 150, s, 14.5, GRAY)
    if i < 4: doc.arrow(x + 172, H - 250, x + 188, H - 250)
doc.bullets(64, H - 360, 940, [
    f'NS-CHEST-MB đang ở mức bản đặt linh kiện: {len(CH.segs)} đoạn dây, {len(CH.vias)} via, {u_ch} kết nối chưa nối.',
    f'NS-CLIP-MB có bản định tuyến thử ({len(CR.segs)} đoạn dây, {len(CR.vias)} via, thư mục routing/) nhưng DRC báo {e_cr} lỗi và {u_cr} kết nối hở. File chính chưa lấy bản này.',
    'Vì vậy hồ sơ này mô tả thiết kế, không phải xác nhận bo đủ điều kiện đặt gia công.'], 18)

doc.std('Yêu cầu gia công chung của hai bo', 'Theo brief PCB: đặt gia công và hàn SMT tại JLCPCB, chỉ hàn linh kiện một mặt.', 0)
rows = [['Hạng mục', 'NS-CHEST-MB', 'NS-CLIP-MB'],
        ['Số lớp · độ dày', '4 lớp · 1,6 mm', '2 lớp · 1,0 mm'],
        ['Stackup', 'L1 tín hiệu + linh kiện · L2 GND liền · L3 nguồn (5V, 3V3, VBAT) · L4 tín hiệu chậm', 'L1 tín hiệu + linh kiện · L2 GND liền tối đa'],
        ['Đồng · bề mặt', '1 oz ngoài, 0,5 oz trong · ENIG', '1 oz · ENIG'],
        ['Mặt hàn linh kiện', 'Mặt trước (hướng −Y). Mặt sau chỉ có test point', 'Mặt trên (+Z). Mặt dưới chỉ có pad dây pin, motor, LED trắng'],
        ['Dây/khe tối thiểu', '0,1/0,1 mm (giới hạn JLC); khuyên dùng 0,15/0,15', '0,15/0,15 mm'],
        ['Via', '0,3 mm khoan / 0,6 mm pad', '0,3 mm khoan / 0,6 mm pad'],
        ['Fiducial · lỗ vít', '3 fiducial · 4 lỗ NPTH Ø2,2 (M2)', '3 fiducial · không có lỗ vít, bo kẹp bằng gân vỏ']]
doc.table(64, H - 125, [190, 400, 346], rows, size=15.5, pad=8)

doc.std('Quy tắc thiết kế bắt buộc', 'Các quy tắc đã đưa vào brief và dùng làm tiêu chí review layout.', 0)
rows = [['Quy tắc', 'Nội dung', 'Áp dụng'],
        ['GND liền khối', 'Không chia GND analog/digital; khâu via GND quanh mép bo và mạch nguồn xung, bước ≤ 5 mm', 'Cả hai bo'],
        ['Antenna ESP32', 'Antenna ở mép bo, không có đồng ở mọi lớp bên dưới, không đặt linh kiện', 'Cả hai bo'],
        ['Nguồn xung', 'Vòng C_in → IC → GND ngắn nhất; node SW/LX nhỏ; pad nhiệt IP5306/TP4056 nối GND bằng ≥ 9 via', 'IP5306, SY8088, TP4056'],
        ['USB D+/D−', 'Đi cặp song song, lệch dài ≤ 1 mm, không đổi lớp; ESD đặt sát connector', 'Cả hai bo'],
        ['Không 5 V vào GPIO', 'Tín hiệu từ mạch 5 V phải qua cầu chia hoặc buffer', 'ECHO JSN, VBUS_DET'],
        ['Chân strapping', 'Không bị kéo sai mức lúc khởi động: GPIO0=1, GPIO45=0, GPIO46=0 (S3); GPIO2/8/9=1 (C3)', 'Cả hai bo'],
        ['Test point', 'Mọi rail, GND, EN, BOOT, UART, SDA/SCL có pad Ø1,0 mm và tên trên silkscreen', 'Cả hai bo'],
        ['Chống ẩm', 'Chừa vùng không phủ cho connector và antenna để phủ conformal coating sau này', 'Cả hai bo']]
doc.table(64, H - 120, [180, 560, 196], rows, size=15.5, pad=6.5)

# ============================ 2. VẬN HÀNH ====================================
doc.divider('KIẾN TRÚC', 'HỆ THỐNG', 'Hai bo mạch · Cây nguồn · Khối chức năng', 'NS-CHEST-MB / NS-CLIP-MB', 1)

doc.std('System Diagram của NovaSight', 'Hai bo mạch và các linh kiện rời nối qua connector.', 1)
draw_pcb(c, CH, 64, H - 120, 440, 215, 'F', text_min=99)
draw_pcb(c, CL, 560, H - 120, 440, 215, 'F', text_min=99)
c.setFont('ArB', 16); c.setFillColor(NAVY)
c.drawString(64, H - 350, 'NS-CHEST-MB'); c.drawString(560, H - 350, 'NS-CLIP-MB')
doc.text(64, H - 360, 440, 'Camera OV3660 (FPC 24 chân), breakout ToF VL53L8CX, 2 board JSN-SR04T, 2 motor rung 1027 trên dây vai, pin LP124065 4000 mAh nối vào J2, J3, J5/J6, J7/J8 và J4.', 14, GRAY)
doc.text(560, H - 360, 440, '2 motor 1027, pin 603450, 2 LED đỏ 5 mm và 1 LED trắng 5 mm nối bằng dây hàn vào các pad xuyên lỗ (J2–J4, D1–D3).', 14, GRAY)
doc.text(64, H - 470, 940, 'Chest và Clip trao đổi cảnh báo qua BLE. Mỗi bo dùng một cổng USB-C cho cả sạc và nạp firmware.', 15, INK)

def _tree(title, sub, boxes, arrows, note, bw=190, bh=70, dx=238):
    doc.std(title, sub, 1)
    pos = {}
    for k, (col, row, t_, b_, hl) in boxes.items():
        x = 64 + col * dx; yt = H - 135 - row * 118
        doc.box(x, yt, bw, bh, t_, b_, stroke=RED if hl else LINE); pos[k] = (x, yt)
    def pt(k, side, off=0):
        x, yt = pos[k]
        return {'r': (x + bw, yt - bh / 2 + off), 'l': (x, yt - bh / 2 + off), 'b': (x + bw / 2 + off, yt - bh), 't': (x + bw / 2 + off, yt)}[side]
    for a in arrows:
        if a[0] == 'line':
            doc.arrow(*pt(a[1], a[2]), *pt(a[3], a[4]))
        elif a[0] == 'bus':   # from box a[1] bottom, down to bus, to tops of list
            src = pt(a[1], 'b'); ybus = src[1] - 24
            c.setStrokeColor(GRAY); c.setLineWidth(1.2)
            xs_ = [pt(k, 't')[0] for k in a[2]]
            c.line(src[0], src[1], src[0], ybus); c.line(min(xs_ + [src[0]]), ybus, max(xs_ + [src[0]]), ybus)
            for k in a[2]:
                tx, ty = pt(k, 't'); doc.arrow(tx, ybus, tx, ty)
        elif a[0] == 'elbow':  # from side of box a[1] horizontally to x, down to y of box a[2] then arrow into it
            s = pt(a[1], a[3]); e = pt(a[2], a[4])
            xm = a[5]
            c.setStrokeColor(GRAY); c.setLineWidth(1.2)
            c.line(s[0], s[1], xm, s[1]); c.line(xm, s[1], xm, e[1]); doc.arrow(xm, e[1], e[0], e[1])
            if len(a) > 6:
                c.setFillColor(GRAY); c.setFont('Ar', 11); c.drawString(xm + 4, (s[1] + e[1]) / 2, a[6])
    doc.text(64, H - 540 + 40, 940, note, 14, GRAY)


def powertree_chest():
    boxes = {'usb': (0, 0, 'J1 USB-C', 'VBUS 4,65–5,5 V', True), 'ip': (1, 0, 'U2 IP5306', 'Sạc 2,1 A + boost 5 V', False),
             'q1': (2, 0, 'Q1 AO3401A', 'Công tắc tải 5V_SYS → 5V_SW', False), 'buck': (3, 0, 'U3 SY8088IAAC', 'Buck 3,3 V, tối đa 1 A', False),
             'v33': (4, 0, '3V3', 'ESP32-S3, MPU-6050, ToF', True),
             'bat': (1, 1, 'J4 pin LP124065', 'VBAT 3,0–4,2 V (có mạch bảo vệ)', True), 'sw': (2, 1, 'SW1 → Q2', 'PWR_EN kéo gate Q1 xuống', False),
             'jsn': (3, 1, 'U5, U6 + J5, J6', '5V_SW: 2 JSN-SR04T, buffer TRIG', False), 'ldo': (4, 1, 'U7 2V8 · U8 1V5', 'Camera AVDD/DOVDD · DVDD', False),
             'f1': (1, 2, 'F1 PTC 0,5 A', 'VBAT → VBAT_MOT', False), 'mot': (2, 2, 'Q4, Q5 + J7, J8', 'Low-side AO3400A, 2 motor 1027', False)}
    arrows = [('line', 'usb', 'r', 'ip', 'l'), ('line', 'ip', 'r', 'q1', 'l'), ('line', 'q1', 'r', 'buck', 'l'), ('line', 'buck', 'r', 'v33', 'l'),
              ('line', 'bat', 't', 'ip', 'b'), ('line', 'sw', 't', 'q1', 'b'), ('line', 'v33', 'b', 'ldo', 't'),
              ('line', 'bat', 'b', 'f1', 't'), ('line', 'f1', 'r', 'mot', 'l'), ('elbow', 'q1', 'jsn', 'r', 'l', 64 + 2 * 196 + 170 + 13, '5V_SW')]
    _tree('NovaChest Cây nguồn', 'Công tắc gạt chỉ điều khiển công tắc tải Q1; motor lấy nguồn trực tiếp từ VBAT.', boxes, arrows,
          'Công tắc gạt SW1 chỉ mang dòng µA. Gạt OFF thì Q1 ngắt, tải về 0 và IP5306 tự về standby sau 32 s (≈ 50 µA).', bw=170, dx=196)

powertree_chest()


def powertree_clip():
    boxes = {'usb': (0, 0, 'J1 USB-C', 'VBUS 4,5–5,25 V', True), 'tp': (1, 0, 'U3 TP4056', 'Sạc 400 mA (R_PROG 3,0 kΩ)', False),
             'prot': (2, 0, 'U5 DW01A + Q1 FS8205A', 'Bảo vệ quá xả, quá dòng, ngắn mạch', False), 'bat': (3, 0, 'J2 pin 603450', 'BAT+ 3,0–4,2 V', True),
             'd4': (0, 1, 'D4 SS14', 'VBUS → VSYS khi cắm sạc', False), 'vsys': (1, 1, 'VSYS', '≈ 4,6 V khi cắm sạc, ≤ 0,5 A', True),
             'q2': (2, 1, 'Q2 AO3401A', 'BAT+ → VSYS khi không cắm sạc', False),
             'ldo': (0, 2, 'U4 AP2112K-3.3', '3V3 ≤ 600 mA cho ESP32-C3, MPU-6050', False), 'mot': (1, 2, 'Q3, Q4 + 2 motor', 'Low-side AO3400A, VSYS không qua PTC', False),
             'led': (2, 2, 'Q5 + D1–D3', 'Đèn "Xin đường", điện trở riêng mỗi nhánh', False)}
    arrows = [('line', 'usb', 'r', 'tp', 'l'), ('line', 'tp', 'r', 'prot', 'l'), ('line', 'prot', 'r', 'bat', 'l'),
              ('line', 'usb', 'b', 'd4', 't'), ('line', 'd4', 'r', 'vsys', 'l'), ('line', 'q2', 'l', 'vsys', 'r'),
              ('elbow', 'bat', 'q2', 'b', 'r', 64 + 3 * 238 + 95 + 0, None), ('bus', 'vsys', ['ldo', 'mot', 'led'])]
    # elbow from battery bottom down to Q2 right side: custom since it leaves from bottom
    arrows = [a for a in arrows if a[0] != 'elbow']
    _tree('NovaCane Clip Cây nguồn', 'Mạch chia tải cho phép máy chạy khi cắm sạc; motor lấy nguồn từ VSYS.', boxes, arrows,
          'Khi có VBUS, gate Q2 lên 5 V nên Q2 ngắt; VSYS lấy từ USB qua D4 và TP4056 sạc pin đúng dòng đặt. GND trên bo là P− của mạch bảo vệ; B− không được nối GND ở chỗ khác.')
    # pin → Q2 (battery bottom to Q2 right)
    bxp = 64 + 3 * 238 + 95; yq = H - 135 - 118 - 35
    c.setStrokeColor(GRAY); c.setLineWidth(1.2); c.line(bxp, H - 135 - 70, bxp, yq)
    doc.arrow(bxp, yq, 64 + 2 * 238 + 190, yq)

powertree_clip()


def block_chest():
    doc.std('NovaChest Kiến trúc phần cứng', 'Mọi GPIO của ESP32-S3 đã được dùng hết; GPIO35–37 bị PSRAM octal chiếm.', 1)
    cx, cy, cw, chh = 400, H - 130, 280, 330
    doc.box(cx, cy, cw, chh, 'U4 ESP32-S3-WROOM-1-N16R8', 'Wi-Fi/BLE 5, 16 MB flash, 8 MB PSRAM\nI²C 400 kHz (GPIO2/14)\nUSB nội GPIO19/20', fill=HEAD, stroke=RED, tsize=15, bsize=12)
    L = [('J1 USB-C + U1 USBLC6', 'CC 5,1 kΩ ×2, D+/D−, VBUS_DET GPIO44'), ('SW2 Mode · SW3 BOOT · SW5 RESET', 'GPIO3, GPIO0, EN'),
         ('U9 MPU-6050', 'I²C 0x68, INT GPIO47'), ('J3 ToF VL53L8CX', 'I²C 0x29, LPn GPIO41, INT GPIO42'), ('Đo pin', 'VBAT/2 → GPIO1 (ADC1_CH0)')]
    R = [('J2 camera FPC 24 chân', 'DVP 8 bit, SCCB GPIO4/5, XCLK GPIO15'), ('U5, U6 → J5, J6 JSN-SR04T', 'TRIG GPIO21/39, ECHO GPIO38/40'),
         ('Q4, Q5 → J7, J8 motor', 'PWM GPIO45/46, kéo xuống 100 kΩ'), ('D1 LED trạng thái', 'GPIO48'), ('TP1–TP16', 'Test point các rail và tín hiệu')]
    for i, (t, b) in enumerate(L):
        yt = H - 125 - i * 66
        doc.box(64, yt, 280, 56, t, b, tsize=13, bsize=11); doc.arrow(344, yt - 28, 400, yt - 28)
    for i, (t, b) in enumerate(R):
        yt = H - 125 - i * 66
        doc.box(736, yt, 280, 56, t, b, tsize=13, bsize=11); doc.arrow(680, yt - 28, 736, yt - 28)
    doc.text(64, H - 470, 940, 'Nếu sau này thêm DRV2605L thì phải bỏ LED_STATUS hoặc VBUS_DET để lấy chân.', 14, GRAY)

block_chest()


def block_clip():
    doc.std('NovaCane Clip Kiến trúc phần cứng', 'ESP32-C3-MINI-1: một cổng USB-Serial-JTAG dùng cho cả sạc và nạp firmware.', 1)
    doc.box(400, H - 130, 280, 330, 'U1 ESP32-C3-MINI-1-N4X', 'BLE 5, I²C GPIO4/5\nUSB D− GPIO18, D+ GPIO19\nBOOT GPIO9, strapping GPIO2/8/9', fill=HEAD, stroke=RED, tsize=15, bsize=12)
    L = [('J1 USB-C + U2 USBLC6', 'VBUS_DET GPIO21 (cầu chia 68 kΩ / 100 kΩ)'), ('SW2 Mode · SW3 Xin đường · SW4 SOS', 'GPIO10, GPIO2, GPIO20'),
         ('U6 MPU-6050', 'I²C 0x68, INT GPIO1'), ('Đo pin', 'BAT+/2 → GPIO0 (ADC1_CH0)'), ('SW1 công tắc gạt', 'EN của U4 (LDO) nối VSYS khi ON')]
    R = [('Q3, Q4 → motor trái/phải', 'PWM GPIO6/7, VSYS, flyback B5819W'), ('Q5 → D1, D2, D3', 'GPIO3, 2 Hz, 3 nhánh có điện trở riêng'),
         ('D9 LED trạng thái', 'GPIO8, sáng khi mức thấp'), ('D7, D8 CHRG/STDBY', 'Chỉ để kỹ thuật viên xem khi mở vỏ'), ('TP1–TP13', 'Test point các rail và tín hiệu')]
    for i, (t, b) in enumerate(L):
        yt = H - 125 - i * 66
        doc.box(64, yt, 280, 56, t, b, tsize=13, bsize=11); doc.arrow(344, yt - 28, 400, yt - 28)
    for i, (t, b) in enumerate(R):
        yt = H - 125 - i * 66
        doc.box(736, yt, 280, 56, t, b, tsize=13, bsize=11); doc.arrow(680, yt - 28, 736, yt - 28)

block_clip()

doc.std('NovaChest Công tắc tải và khởi động IP5306', 'Công tắc gạt không mang dòng tải: nó chỉ tạo mức PWR_EN.', 1)
st = [('1', 'SW1 gạt ON', 'Nối VBAT vào PWR_EN (100 kΩ kéo xuống GND).'),
      ('2', 'Q2 AO3400A', 'PWR_EN qua 10 kΩ vào gate Q2; Q2 kéo gate Q1 xuống.'),
      ('3', 'Q1 AO3401A', 'Source = 5V_SYS, Drain = 5V_SW; 100 kΩ + 100 nF gate–source cho khởi động mềm ≈ 1 ms.'),
      ('4', 'Q3 2N7002', 'PWR_EN → 1 µF → gate Q3, 470 kΩ xuống GND; Q3 kéo KEY xuống ≈ 0,42 s.'),
      ('5', 'IP5306', 'Xung KEY nằm trong cửa sổ 30 ms – 2 s nên luôn bật boost, kể cả khi đang standby.')]
for i, (n, t, s) in enumerate(st):
    y = H - 140 - i * 70
    c.setFillColor(RED); c.setFont('ArB', 26); c.drawString(64, y - 8, n)
    c.setFillColor(NAVY); c.setFont('ArB', 18); c.drawString(110, y, t)
    doc.text(300, y + 14, 700, s, 16, INK)
doc.text(64, H - 500, 940, 'Cần kiểm tra trên mạch thật: KEY tích cực mức thấp; 5V_SYS có sụt ngắn khi cắm sạc lúc máy đang chạy không. Nếu có, firmware phải chịu được việc bị reset.', 14, GRAY)

doc.std('NovaCane Clip Chia tải và bảo vệ pin', 'Máy vẫn chạy khi cắm sạc nên không còn quy tắc "gạt OFF trước khi sạc".', 1)
rows = [['Khối', 'Linh kiện', 'Hoạt động'],
        ['Sạc', 'U3 TP4056 (ESOP-8), R_PROG 3,0 kΩ', 'I = 1200 / 3,0 = 400 mA; TEMP nối GND; CE nối VCC; pad đáy nối GND'],
        ['Bảo vệ pin', 'U5 DW01A + Q1 FS8205A', '100 Ω từ B+ vào VCC, 100 nF VCC–B−, 1 kΩ từ CS đến P−; FS8205A nằm trên đường B− → P−'],
        ['Chia tải', 'D4 SS14 + Q2 AO3401A', 'Không cắm sạc: gate = 0 V, Q2 dẫn, pin cấp VSYS. Cắm sạc: gate = 5 V, Q2 ngắt, VSYS lấy từ USB qua D4'],
        ['LDO', 'U4 AP2112K-3.3', 'VIN = VSYS; EN nối VSYS qua SW1; ra 10 µF + 100 nF, thêm 22 µF sát chân 3V3 của module'],
        ['Công tắc', 'SW1', 'Chỉ mang dòng µA; OFF thì LDO tắt, dòng còn lại ≈ 4,5 µA cầu chia pin + dòng nghỉ DW01A']]
y_cs = doc.table(64, H - 115, [130, 270, 536], rows, size=15, pad=6.5)
doc.text(64, y_cs - 16, 940, 'Ngưỡng tắt máy chủ động của firmware là 3,5 V. Ở 3,5 V với tải 300 mA, đầu ra LDO khoảng 3,25 V, vẫn trên mức tối thiểu 3,0 V của ESP32-C3.', 15, INK)
doc.text(64, y_cs - 66, 940, 'Kiểm tra số chân DW01A và FS8205A theo datasheet của đúng hãng đã chọn trên LCSC, vì các hãng clone có thể khác nhau.', 14, GRAY)

doc.std('Ngân sách công suất (tính toán thiết kế)', 'Số liệu tính trong brief, chưa đo trên mạch thật. Dòng thật phải đo ở buổi bring-up.', 1)
rows = [['Thiết bị', 'Tải chính', 'Trung bình', 'Đỉnh', 'Thời lượng ước tính'],
        ['NovaChest', 'ESP32-S3 + camera, BLE bật', '3V3: 240–455 mA', '≈ 500 mA khi Wi-Fi', ''],
        ['', 'Breakout VL53L8CX', '≈ 100 mA', '150 mA', ''],
        ['', '2 × JSN-SR04T (5V_SW)', '16 mA', '60 mA', ''],
        ['', '2 motor 1027 (bật 5% thời gian)', '≈ 27 mA', '240 mA lúc khởi động', ''],
        ['', 'Công suất từ pin (IP5306 91%)', '1,64–2,68 W', '', '≈ 5,0–8,1 giờ (chưa đạt mục tiêu ≥ 10 giờ)'],
        ['NovaCane Clip', 'ESP32-C3 BLE kết nối, IMU 200 Hz', '20–40 mA', '≈ 130 mA khi BLE phát', ''],
        ['', '2 motor, đèn "Xin đường" (60 s mỗi lần bấm)', '≈ 8 mA / ≈ 70 mA', '240 mA lúc khởi động', ''],
        ['', 'Tổng', '≈ 35–55 mA', '≈ 440 mA', '≈ 16–26 giờ (đạt mục tiêu)']]
y_pw = doc.table(64, H - 115, [120, 310, 140, 170, 196], rows, size=13.5, pad=5.5)
doc.text(64, y_pw - 14, 940, 'Nếu đo thật vẫn dưới 10 giờ, Rev B xử lý theo thứ tự: giảm tần suất chụp camera; thay chuỗi boost 5 V → buck 3,3 V (≈ 82%) bằng buck-boost lấy thẳng từ pin (≈ 90%); dùng pin dung lượng lớn hơn.', 14, GRAY)

doc.std('Độ rộng dây nguồn và các giá trị đã tính', 'IPC-2221, đồng 1 oz lớp ngoài, nhiệt tăng 10 °C. Lớp trong 0,5 oz cần rộng khoảng 2,5 lần.', 1)
rows = [['Dòng', 'Bề rộng tối thiểu', 'Dùng trên bo'],
        ['0,5 A', '0,12 mm', '3V3 nhánh; 5V_SW đến JSN: 0,4 mm'],
        ['1 A', '0,30 mm', '3V3 chính, 5V_SW, BAT+ và VSYS của Clip: 0,6–0,8 mm'],
        ['2 A', '0,78 mm', 'VBUS và 5V_SYS của Chest: ≥ 1,5 mm hoặc mảng đồng'],
        ['3 A (đỉnh dòng cuộn cảm)', '1,37 mm', 'VBAT, node SW của IP5306, L1 trên Chest: mảng đồng ≥ 2,5 mm, nhiều via']]
y = doc.table(64, H - 120, [250, 190, 496], rows, size=15.5, pad=7)
rows = [['Mạch', 'Công thức', 'Kết quả'],
        ['Buck 3V3 (Chest)', '0,6 × (1 + 680k/150k)', '3,32 V'],
        ['Cầu chia đo pin 470 kΩ / 470 kΩ', 'VBAT / 2', '2,1 V ở 4,2 V; rò 4,5 µA'],
        ['VBUS_DET 68 kΩ / 100 kΩ', 'VBUS × 100/168', '2,98 V ở 5,0 V; 2,68 V ở 4,5 V'],
        ['ECHO JSN 10 kΩ / 15 kΩ', '5 V × 15/25', '3,0 V ở 5,0 V; 3,15 V ở 5,25 V'],
        ['Xung KEY 1 µF × 470 kΩ', 't = RC · ln(3,7/1,5)', '0,42 s (cửa sổ 30 ms – 2 s)']]
doc.table(64, y - 18, [330, 260, 346], rows, size=14, pad=5.5)

# ============================ 3. PHẦN CỨNG – CHEST ===========================
doc.divider('PHẦN CỨNG', 'NS-CHEST-MB', 'Layout · Schematic · Pinout · BOM', 'NovaChest', 2)

# --- mechanical & placement vs brief
def mm(fp, ref, axis):
    pass

def brief_xy_chest(f):
    return f['x'] - 100.0, 74.8 - f['y']

fpm = {f['ref']: f for f in CH.fps}
doc.std('NovaChest Cơ khí, đường bao và lỗ bắt vít', 'Tọa độ quy đổi về hệ của brief: X sang phải người đeo, Z hướng lên, gốc ở tâm bo.', 2)
rows = [['Hạng mục', 'Brief', 'Trong file PCB']]
brief = {'H1': (-44, 22), 'H2': (44, 22), 'H3': (-20, -20), 'H4': (20, -20)}
col = {}
for i, k in enumerate(['H1', 'H2', 'H3', 'H4']):
    x, z = brief_xy_chest(fpm[k]); bx_, bz_ = brief[k]
    ok = abs(x - bx_) < 1.0 and abs(z - bz_) < 1.0
    rows.append([f'{k} (NPTH Ø2,2, M2)', f'({bx_:+.0f}; {bz_:+.0f})'.replace('-', '−'), (f'({x:+.1f}; {z:+.1f})'.replace('.', ',').replace('-', '−')) + ('' if ok else '  ← lệch')])
    if not ok: col[(i + 1, 2)] = BAD
for k, bxz, nm in [('J1', (32.0, None), 'J1 USB-C, tâm X'), ('SW1', (-32.0, None), 'SW1 công tắc gạt, X'), ('SW2', (30.0, None), 'SW2 nút Mode, X')]:
    x, z = brief_xy_chest(fpm[k])
    rows.append([nm, f'{bxz[0]:+.1f}'.replace('.', ',').replace('-', '−'), f'{x:+.1f}'.replace('.', ',').replace('-', '−')])
u4 = fpm['U4']
xs = [kipcb.pad_world(u4, p_)[0] - 100 for p_ in u4['pads']]
rows.append(['U4 ESP32-S3, khoảng X (chân)', '−38 … −20 (đề xuất)', f'{min(xs):.1f} … {max(xs):.1f}'.replace('.', ',').replace('-', '−')])
col[(len(rows) - 1, 2)] = WARN
y = doc.table(64, H - 125, [320, 260, 356], rows, size=16, pad=7.5, colors=col)
doc.text(64, y - 18, 940, 'H2, H3, H4, J1, SW1 và SW2 khớp brief. H1 nằm lệch khoảng 30 mm so với brief và module U4 dịch khoảng 11 mm về phía +X so với mặt bằng đề xuất. Cần nhóm cơ khí xác nhận trụ bắt bo tại H1 trước khi chốt.', 14, GRAY)

# placement callouts
cg = [(1, 'Cổng USB-C và ESD', 'J1, U1, R1–R6', ['J1']),
      (2, 'Sạc và boost 5 V', 'U2 IP5306, L1, Q1–Q3, J4, SW1', ['U2']),
      (3, 'Buck 3,3 V và LDO camera', 'U3, L2, U7, U8', ['U3', 'U7']),
      (4, 'ESP32-S3', 'U4 WROOM-1-N16R8, nút BOOT/RESET', ['U4']),
      (5, 'Camera và ToF', 'J2 FPC 24 chân, J3 ToF', ['J2', 'J3']),
      (6, 'Cảm biến và motor', 'U9 MPU-6050, U5/U6, J5–J8, Q4/Q5', ['U9', 'J7', 'J5'])]
doc.std('NovaChest Vị trí các khối trên PCB', 'Đối chiếu mặt trên với các khối nguồn, giao tiếp và cảm biến.', 2)
call = [(n, centroid(CH, refs)) for n, _, _, refs in cg]
draw_pcb(c, CH, 64, H - 110, 640, 410, 'F', callouts=call)
for i, (n, t, s, _) in enumerate(cg):
    y = H - 140 - i * 70
    c.setFillColor(RED); c.setFont('ArB', 20); c.drawString(730, y, str(n))
    c.setFillColor(NAVY); c.setFont('ArB', 17); c.drawString(766, y, t)
    c.setFillColor(GRAY); c.setFont('Ar', 13); c.drawString(766, y - 20, s)

doc.std('NovaChest layout mặt trên và mặt dưới', None, 2)
draw_pcb(c, CH, 40, H - 95, 490, 300, 'F', text_min=4, ratsnest=RAT['CH'])
draw_pcb(c, CH, 550, H - 95, 490, 300, 'B', text_min=4, ratsnest=RAT['CH'])
legend(H - 505)
c.setFont('Ar', 14); c.setFillColor(GRAY)
c.drawString(64, H - 420, 'Mặt trên F.Cu'); c.drawString(574, H - 420, 'Mặt dưới B.Cu (nhìn từ mặt sau)')
doc.text(64, H - 440, 940,
         f'Bản đặt linh kiện: {len(CH.segs)} đoạn dây và {len(CH.vias)} via đã có, còn {u_ch} kết nối chưa nối. Vùng không có pour ở mép trên là khoảng cấm đồng dưới antenna. Mặt dưới chỉ có 16 test point và pour đồng.', 15, INK)

doc.std('NovaChest vùng MCU và camera', 'Zoom vùng ESP32-S3, FPC camera và buffer XCLK.', 2)
draw_pcb(c, CH, 64, H - 110, 620, 410, 'F', view=(52, 50, 112, 99), text_min=3.2, ratsnest=RAT['CH'], labels=['U4', 'J2', 'U7', 'U8', 'U10', 'SW2', 'SW3', 'SW5', 'D1'], label_size=11)
legend(H - 538)
doc.text(710, H - 120, 300, 'U4 đặt dọc ở bên trái, antenna chĩa lên mép trên; vùng cấm đồng (keepout) dưới antenna đã vẽ trên cả 4 lớp.\n\nJ2 là FPC 24 chân bước 0,5 mm; dây DVP ngắn ≤ 40 mm trên L1 với mặt GND liền ở L2, XCLK có R nối tiếp 22 Ω sát ESP32.', 14, INK)

doc.std('NovaChest vùng nguồn và ổn áp', 'Zoom vùng IP5306, L1, buck SY8088 và công tắc tải.', 2)
draw_pcb(c, CH, 64, H - 110, 620, 410, 'F', view=(104, 50, 152, 100), text_min=3.2, ratsnest=RAT['CH'], labels=['U2', 'L1', 'U3', 'L2', 'Q1', 'Q2', 'Q3', 'J1', 'U1', 'F1', 'U9', 'SW2'], label_size=11)
legend(H - 538)
dU2 = math.hypot(fpm['U9']['x'] - fpm['U2']['x'], fpm['U9']['y'] - fpm['U2']['y']); dL1 = math.hypot(fpm['U9']['x'] - fpm['L1']['x'], fpm['U9']['y'] - fpm['L1']['y'])
doc.text(710, H - 120, 300, 'U2 IP5306 (ESOP-8) và L1 nằm ở góc dưới bên phải, cạnh J1 và J4.\n\nVòng C_in → IC → GND phải ngắn nhất; pad nhiệt nối GND bằng ≥ 9 via đồng đầy (yêu cầu của brief, chưa hoàn tất vì chưa định tuyến).\n\nKhoảng cách MPU-6050 (U9) tới IP5306: ' + f'{dU2:.1f}'.replace('.', ',') + ' mm, tới L1: ' + f'{dL1:.1f}'.replace('.', ',') + ' mm (yêu cầu ≥ 15 mm).', 14, INK)

doc.std('NovaChest vùng cảm biến và đầu nối', 'Zoom vùng J3/J5/J6, MPU-6050 và cổng nối ngoài.', 2)
draw_pcb(c, CH, 64, H - 110, 620, 410, 'F', view=(50, 76, 112, 100), text_min=3.0, ratsnest=RAT['CH'], labels=['J3', 'J4', 'J5', 'J6', 'SW1', 'SW3', 'SW5', 'J9', 'U5', 'U6'], label_size=11)
legend(H - 538)
doc.text(710, H - 120, 300, 'J5 (JSN phải) và J6 (JSN trái) là PH 4 chân đặt ngoài vùng A bóng đầu dò siêu âm.\n\nSW1 công tắc gạt và J4 pin nằm sát mép dưới; dây pin vòng qua mép dưới bo.', 14, INK)

# schematic crops
_src_docs = {}
def tight(key, frac, pad=10):
    """Shrink a fractional crop to the union of schematic objects inside it."""
    if key not in _src_docs: _src_docs[key] = pymupdf.open(SCH[key])
    pg = _src_docs[key][0]; pr = pg.rect
    reg = pymupdf.Rect(frac[0] * pr.width, frac[1] * pr.height, frac[2] * pr.width, frac[3] * pr.height)
    u = None
    def add(r):
        nonlocal u
        r = pymupdf.Rect(r)
        if not r.intersects(reg): return
        if r.width > 0.85 * reg.width or r.height > 0.85 * reg.height: return
        r = r & reg
        u = r if u is None else (u | r)
    for dr in pg.get_drawings(): add(dr['rect'])
    for w in pg.get_text('words'): add(w[:4])
    if u is None: return frac
    u = pymupdf.Rect(u.x0 - pad, u.y0 - pad, u.x1 + pad, u.y1 + pad) & reg
    return (u.x0 / pr.width, u.y0 / pr.height, u.x1 / pr.width, u.y1 / pr.height)

def sch_page(title, sub, key, frac, text, sec=2):
    doc.std(title, sub, sec)
    frac = tight(key, frac)
    fx0, fy0, fx1, fy1 = frac
    cw_, ch_ = (fx1 - fx0) * 2383.92, (fy1 - fy0) * 1683.79
    asp = cw_ / ch_
    if asp >= 1.7:
        bw = 940; bh = bw / asp
        if bh > 330: bh = 330; bw = bh * asp
        doc.overlay((64, H - 110, bw, bh), SCH[key], frac)
        doc.text(64, H - 110 - bh - 14, 940, text.replace('\n', '  '), 14, INK)
    else:
        bh = 405; bw = bh * asp
        if bw > 640: bw = 640; bh = bw / asp
        doc.overlay((64, H - 110, bw, bh), SCH[key], frac)
        doc.text(64 + bw + 24, H - 110, 1016 - (64 + bw + 24), text, 15, INK)

S = lambda x0, y0, x1, y1: (x0 / 2000, y0 / 1413, x1 / 2000, y1 / 1413)
sch_page('NovaChest schematic MCU, boot và giao diện', 'Phần 1: ESP32-S3, EN/BOOT, nút Mode, LED trạng thái và đo pin.', 'CH', S(29, 80, 665, 560),
         'U4 ESP32-S3-WROOM-1-N16R8.\nEN: 10 kΩ lên 3V3, 1 µF xuống GND, nút RESET (SW5).\nGPIO0: 10 kΩ lên 3V3, nút BOOT (SW3).\nSW2 Mode: GPIO3, 10 kΩ lên 3V3, 100 nF.\nD1 LED trạng thái: GPIO48 → 1 kΩ.\nĐo pin: VBAT → 470 kΩ / 470 kΩ → GPIO1, 100 nF.')
sch_page('NovaChest schematic nguồn, sạc và bảo vệ', 'Phần 2: IP5306, công tắc tải Q1/Q2/Q3, buck SY8088 và 4 LED báo pin.', 'CH', S(670, 100, 1440, 600),
         'U2 IP5306: VIN = VBUS, BAT = VBAT, SW → L1 → BAT, VOUT = 5V_SYS.\nQ1 AO3401A là công tắc tải 5V_SYS → 5V_SW; Q2 AO3400A và Q3 2N7002 tạo xung KEY.\nU3 SY8088IAAC: R trên 680 kΩ, R dưới 150 kΩ, feed-forward 22 pF cho 3,32 V.\nD4–D7 là mạch báo pin 4 LED.')
sch_page('NovaChest schematic USB-C, ESD và VBUS', 'Phần 3: J1 USB-C, USBLC6-2SC6, CC1/CC2 và cầu chia VBUS_DET.', 'CH', S(29, 590, 665, 1010),
         'CC1 và CC2 mỗi chân một điện trở 5,1 kΩ 1% xuống GND (thiết bị sink).\nD+ nối GPIO20, D− nối GPIO19, có footprint 0 Ω nối tiếp.\nU1 USBLC6-2SC6 bảo vệ D+/D− và VBUS.\nVBUS → 68 kΩ / 100 kΩ → GPIO44 (VBUS_DET), 2,98 V ở 5,0 V.')
sch_page('NovaChest schematic IMU, I²C và cảm biến ngoài', 'Phần 4: MPU-6050, connector ToF và hai connector JSN-SR04T.', 'CH', S(670, 610, 1440, 1100),
         'U9 MPU-6050: VDD 3V3 + 100 nF, VLOGIC 3V3 + 10 nF, REGOUT 100 nF, CPOUT 2,2 nF.\nAD0, CLKIN, FSYNC nối GND; INT nối GPIO47.\nJ3 ToF: VIN_TOF qua JP1 (0 Ω).\nJ5/J6: 5V_SW, TRIG qua buffer 74AHCT1G125, ECHO qua cầu chia 10 kΩ + 15 kΩ.')
sch_page('NovaChest schematic camera và các rail phụ', 'Phần 7: FPC camera, ME6211 2V8/1V5 và buffer XCLK.', 'CH', S(1440, 48, 1960, 640),
         'J2 FPC 24 chân: pinout theo thiết kế tham chiếu ESP32-S3-EYE.\nU7 ME6211C28M5G-N cấp 2V8 (AVDD, DOVDD); U8 ME6211C15M5G-N cấp 1V5 (DVDD).\nSCCB kéo lên 2V8 bằng 4,7 kΩ; RESET 10 kΩ lên 2V8; PWDN 10 kΩ xuống GND.\nSchematic ghi chú: pinout J2 tạm thời, không nối FPC trước khi đối chiếu.')
sch_page('NovaChest schematic motor và đèn', 'Phần 5: Q4/Q5, diode flyback, PTC F1 và hai connector motor.', 'CH', S(1440, 640, 1990, 1010),
         'J7/J8 chân 1 = VBAT_MOT sau PTC F1 (0,5 A), chân 2 = MOT−.\nQ4/Q5 AO3400A là khóa phía thấp, gate qua 100 Ω và kéo xuống 100 kΩ.\nGate motor trái nối GPIO45, phải nối GPIO46; 100 kΩ giữ hai chân strapping ở mức 0 lúc khởi động.\nD2/D3 B5819W flyback; 100 nF tại connector.')

# GPIO table
doc.std('NovaChest bảng gán chân ESP32-S3', 'Chân module lấy theo symbol ESP32-S3-WROOM-1; GPIO35–37 (chân 28–30) bị PSRAM octal chiếm.', 2)
gp = [('0', '27', 'BOOT', 'Strapping, 10 kΩ lên, SW3'), ('1', '39', 'VBAT_ADC', 'ADC1_CH0'), ('2', '38', 'I2C_SDA', 'Cảm biến'),
      ('3', '15', 'BTN_MODE', 'Strapping JTAG, kéo lên'), ('4', '4', 'CAM_SIOD', 'SCCB'), ('5', '5', 'CAM_SIOC', 'SCCB'),
      ('6', '6', 'CAM_VSYNC', ''), ('7', '7', 'CAM_HREF', ''), ('8', '12', 'CAM_Y4', ''), ('9', '17', 'CAM_Y3', ''),
      ('10', '18', 'CAM_Y5', ''), ('11', '19', 'CAM_Y2', ''), ('12', '20', 'CAM_Y6', ''), ('13', '21', 'CAM_PCLK', ''),
      ('14', '22', 'I2C_SCL', 'Cảm biến'), ('15', '8', 'CAM_XCLK', 'Qua R 22 Ω'), ('16', '9', 'CAM_Y9', ''),
      ('17', '10', 'CAM_Y8', ''), ('18', '11', 'CAM_Y7', ''), ('19', '13', 'USB_D−', ''), ('20', '14', 'USB_D+', ''),
      ('21', '23', 'JSN_L_TRIG', 'Qua U6'), ('38', '31', 'JSN_L_ECHO', 'Qua cầu chia'), ('39', '32', 'JSN_R_TRIG', 'Qua U5'),
      ('40', '33', 'JSN_R_ECHO', 'Qua cầu chia'), ('41', '34', 'TOF_LPN', '47 kΩ lên'), ('42', '35', 'TOF_INT', ''),
      ('43', '37', 'TXD0', 'Chỉ test point'), ('44', '36', 'VBUS_DET', 'Cầu chia 68k/100k'),
      ('45', '26', 'MOT_L_PWM', 'Strapping = 0, 100 kΩ xuống'), ('46', '16', 'MOT_R_PWM', 'Strapping = 0, 100 kΩ xuống'),
      ('47', '24', 'IMU_INT', ''), ('48', '25', 'LED_STATUS', '')]
# verify against design json pins
u4pins = [x for x in DES['chest'] if x['ref'] == 'U4'][0]['pins']
mism = [(g, p, f) for g, p, f, _ in gp if (u4pins.get(p) or '').replace('_SRC', '').replace('_IN', '') not in (f, f.replace('BTN_MODE', 'BTN_MODE'))]
half = (len(gp) + 1) // 2
hdr = ['GPIO', 'Chân', 'Tín hiệu', 'Ghi chú']
doc.table(40, H - 120, [48, 48, 128, 255], [hdr] + [list(r) for r in gp[:half]], size=11, pad=4.5, mono=(0, 1, 2))
doc.table(40 + 479 + 20, H - 120, [48, 48, 128, 255 - 24], [hdr] + [list(r) for r in gp[half:]], size=11, pad=4.5, mono=(0, 1, 2))
GP_MISMATCH = mism

# connectors
def conn_rows(pcb, refs):
    rows = [['Ref', 'Loại / giá trị', 'Pad → net']]
    f = {x['ref']: x for x in pcb.fps}
    for r in refs:
        fp = f[r]
        nets = []
        for pd in fp['pads']:
            n = pd['net'].lstrip('/')
            if pd['num'] in ('', 'MP', 'SH') or n.startswith('unconnected') or not n:
                continue
            nets.append(f"{pd['num']}={n}")
        seen = [];
        for s_ in nets:
            if s_ not in seen: seen.append(s_)
        rows.append([r, fp['value'].replace('_', ' '), ', '.join(seen)])
    return rows

doc.std('NovaChest đầu nối và pinout', 'Pinout lấy từ netlist trong file PCB. Connector ghi "VERIFY" còn chờ đối chiếu với board thật.', 2)
doc.table(64, H - 125, [60, 270, 606], conn_rows(CH, ['J1', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9']), size=13.5, pad=7, mono=(0, 2))

doc.std('NovaChest camera FPC J2 (24 chân)', 'Loại tiếp điểm, thứ tự chân và chiều dài FPC phải khớp module camera mua về: sai ở đây là lỗi hay gặp nhất.', 2)
j2 = [p for p in fpm['J2']['pads'] if p['num'].isdigit()]
j2.sort(key=lambda p: int(p['num']))
def j2row(p):
    n = p['net'].lstrip('/')
    return [p['num'], '— (NC)' if n.startswith('unconnected') else n]
rows1 = [['Chân', 'Net']] + [j2row(p) for p in j2[:12]]
rows2 = [['Chân', 'Net']] + [j2row(p) for p in j2[12:]]
doc.table(64, H - 120, [80, 380], rows1, size=14, pad=5.5, mono=(1,))
doc.table(64 + 480 + 12, H - 120, [80, 380 - 12], rows2, size=14, pad=5.5, mono=(1,))
doc.text(64, H - 470, 940, 'Lưu ý: symbol trong schematic ghi OV5640 (OV5640_FPC_VERIFY_CONTACT), brief ghi camera OV3660. Cần thống nhất tên module và đối chiếu ảnh chụp FPC thật.', 14, GRAY)

doc.std('NovaChest điểm đo (test point)', 'Mọi test point là pad đồng Ø1,0 mm trên mặt dưới B.Cu, có tên trên silkscreen.', 2)
tps = sorted([f for f in CH.fps if f['ref'].startswith('TP')], key=lambda f: refnum(f['ref'])[1])
rows = [['Điểm đo', 'Net', 'Mặt']] + [[f['ref'], f['value'], f['layer']] for f in tps]
doc.table(64, H - 125, [110, 150, 80], rows[:9], size=15, pad=7, mono=(1,))
doc.table(64 + 380, H - 125, [110, 150, 80], [rows[0]] + rows[9:], size=15, pad=7, mono=(1,))

def bom_pages(title, groups, qty, nl, nm, sec=2):
    size = 10.8; pad = 3.5; widths = [250, 230, 410, 40]
    hdr = ['Ref', 'Giá trị', 'Footprint', 'SL']
    avail = 428
    i = 0; page = 1
    total_pages = None
    chunks = []
    cur = []; h = 0
    for r in groups:
        lines = max(len(simpleSplit(str(cell), 'Ar', size, widths[k] - 2 * pad)) for k, cell in enumerate(r))
        rh = lines * size * 1.22 + 2 * pad - 2
        if h + rh > avail and cur:
            chunks.append(cur); cur = []; h = 0
        cur.append(r); h += rh
    if cur: chunks.append(cur)
    for k, ch_ in enumerate(chunks):
        doc.std(f'{title} ({k + 1}/{len(chunks)})', f'{nm}: {nl} dòng BOM, tổng {qty} linh kiện. DNP = không lắp. Cột LCSC chưa có trong file xuất.' if k == 0 else None, sec)
        doc.table(40, H - 110, widths, [hdr] + [list(r) for r in ch_], size=size, pad=pad, mono=(0, 2))

bom_pages('BOM NovaChest', bg_ch, qty_ch, nl_ch, 'NS-CHEST-MB')

# ============================ NS-CLIP-MB =====================================
doc.divider('PHẦN CỨNG', 'NS-CLIP-MB', 'Layout · Schematic · Pinout · BOM', 'NovaCane Clip', 2)
fpc = {f['ref']: f for f in CL.fps}
def brief_xy_clip(f): return f['x'] - 47.7, 68.7 - f['y']
doc.std('NovaCane Clip Cơ khí, đường bao và vị trí nút', 'Tọa độ quy đổi về hệ của brief: X dọc thân gậy (0 ở đầu tay cầm), Y ngang.', 2)
rows = [['Hạng mục', 'Brief', 'Trong file PCB']]
for k, bxy, nm in [('SW2', (36.0, 12.5), 'SW2 Mode'), ('SW3', (36.0, 0.0), 'SW3 Xin đường'), ('SW4', (36.0, -12.5), 'SW4 SOS'),
                   ('SW1', (25.0, None), 'SW1 công tắc gạt, X'), ('J1', (None, -10.0), 'J1 USB-C, Y'), ('D1', (42.7, None), 'D1 LED đỏ, X')]:
    x, y_ = brief_xy_clip(fpc[k])
    b_ = ' ; '.join(f'{v:+.1f}' for v in bxy if v is not None); p_ = ' ; '.join(f'{v:+.1f}' for v, bv in zip((x, y_), bxy) if bv is not None)
    rows.append([nm, b_.replace('.', ',').replace('-', '−'), p_.replace('.', ',').replace('-', '−')])
u1 = fpc['U1']
xs = [kipcb.pad_world(u1, q)[0] - 47.7 for q in u1['pads']]
rows.append(['U1 ESP32-C3-MINI-1 (tâm X)', '59,1 … 75,7 (thân)', f'{u1["x"] - 47.7:.1f} (thân dự kiến {u1["x"] - 47.7 - 8.3:.1f} … {u1["x"] - 47.7 + 8.3:.1f})'.replace('.', ',')])
rows.append(['Đường bao', '73,4 × 37,4 mm, bo góc R3,5, 2 rãnh LED', f'{kipcb.board_bbox(CL)[2] - kipcb.board_bbox(CL)[0]:.1f} × {kipcb.board_bbox(CL)[3] - kipcb.board_bbox(CL)[1]:.1f} mm'.replace('.', ',')])
y = doc.table(64, H - 125, [320, 300, 316], rows, size=15.5, pad=7.5)
doc.text(64, y - 18, 940, 'Vị trí các nút và USB-C khớp brief. Bo không có lỗ vít: được kẹp giữa 4 gân đỡ và 4 gân ép của vỏ, chừa 4 vùng trống 4 × 4 mm ở 4 góc. Chiều cao tact (Z đỉnh 29,4 mm) cần đối chiếu STEP của linh kiện đã chọn.', 14, GRAY)

cgc = [(1, 'USB-C và ESD', 'J1, U2, R10–R15', ['J1']), (2, 'Sạc, bảo vệ, chia tải', 'U3 TP4056, U5, Q1, Q2, D4, J2', ['U3', 'U5', 'Q2']),
       (3, 'LDO 3,3 V', 'U4 AP2112K', ['U4']), (4, 'ESP32-C3-MINI-1', 'U1, nút BOOT/EN', ['U1']),
       (5, 'IMU và nút', 'U6 MPU-6050, SW2–SW4', ['U6', 'SW3']), (6, 'Motor và đèn', 'Q3–Q5, D1–D3, J3, J4', ['Q3', 'Q4', 'J3'])]
doc.std('NovaCane Clip Vị trí các khối trên PCB', 'Đối chiếu mặt trên với các khối nguồn, giao tiếp và cảm biến.', 2)
call = [(n, centroid(CL, refs)) for n, _, _, refs in cgc]
draw_pcb(c, CL, 64, H - 110, 640, 340, 'F', callouts=call)
for i, (n, t, s, _) in enumerate(cgc):
    y = H - 140 - i * 66
    c.setFillColor(RED); c.setFont('ArB', 20); c.drawString(730, y, str(n))
    c.setFillColor(NAVY); c.setFont('ArB', 17); c.drawString(766, y, t)
    c.setFillColor(GRAY); c.setFont('Ar', 13); c.drawString(766, y - 20, s)
doc.text(64, H - 470, 640, 'Phía tay cầm (X 2–20): pad pin, DW01A + FS8205A, mạch lái motor. Giữa (X 20–55): MPU-6050, 3 nút, công tắc, mạch LED. Phía mũi gậy (X 55–76): USB-C, TP4056, chia tải, LDO, module ESP32-C3.', 13, GRAY)

doc.std('NovaCane Clip layout mặt trên và mặt dưới', 'Bản đặt linh kiện trong NS-CLIP-MB.kicad_pcb (file chính).', 2)
draw_pcb(c, CL, 40, H - 110, 490, 250, 'F', text_min=4, ratsnest=RAT['CL'])
draw_pcb(c, CL, 550, H - 110, 490, 250, 'B', text_min=4, ratsnest=RAT['CL'])
legend(H - 490)
c.setFont('Ar', 14); c.setFillColor(GRAY)
c.drawString(64, H - 395, 'Mặt trên F.Cu'); c.drawString(574, H - 395, 'Mặt dưới B.Cu (nhìn từ mặt sau)')
doc.text(64, H - 415, 940, f'File chính có {len(CL.segs)} đoạn dây, {len(CL.vias)} via và {u_cl} kết nối chưa nối. Hai rãnh ở mép trên/dưới là chỗ cho thân LED đỏ 5 mm; mặt dưới chỉ có pad dây pin, motor và LED trắng.', 15, INK)

doc.std('NovaCane Clip bản định tuyến thử (thư mục routing/)', 'Kết quả định tuyến tự động chưa đạt DRC; chưa thay thế file PCB chính.', 2)
draw_pcb(c, CR, 40, H - 110, 490, 250, 'F', text_min=4, ratsnest=RAT['CR'])
draw_pcb(c, CR, 550, H - 110, 490, 250, 'B', text_min=4, ratsnest=RAT['CR'])
legend(H - 490)
c.setFont('Ar', 14); c.setFillColor(GRAY)
c.drawString(64, H - 395, 'Mặt trên F.Cu'); c.drawString(574, H - 395, 'Mặt dưới B.Cu (nhìn từ mặt sau)')
doc.text(64, H - 415, 940, f'Bản thử có {len(CR.segs)} đoạn dây ({sum(1 for s in CR.segs if s["layer"] == "F.Cu")} F.Cu, {sum(1 for s in CR.segs if s["layer"] == "B.Cu")} B.Cu) và {len(CR.vias)} via. DRC: {e_cr} lỗi, {w_cr} cảnh báo, {u_cr} kết nối còn hở. Bản này còn lỗi track_width và khoảng hở mép bo.', 15, INK)

doc.std('NovaCane Clip vùng ESP32-C3 và USB-C', 'Zoom đầu mũi gậy: antenna ở mép bo, USB-C và nguồn.', 2)
draw_pcb(c, CL, 64, H - 110, 620, 340, 'F', view=(85, 50, 124, 88), text_min=3.2, ratsnest=RAT['CL'], labels=['U1', 'J1', 'U2', 'U4', 'SW1', 'U6', 'D3'], label_size=11)
legend(H - 470)
doc.text(710, H - 120, 300, 'U1 đặt trục dài theo X, antenna ở đầu X = 75,7 (mép bo). Không có đồng ở mọi lớp dưới antenna; vùng này nằm ngoài pin (pin kết thúc ở X 63,5).\n\nThân gậy nhôm nằm dưới antenna khoảng 13 mm nên phải đo RSSI khi Clip kẹp trên gậy thật.', 14, INK)

doc.std('NovaCane Clip vùng nguồn, sạc và bảo vệ', 'Zoom phía tay cầm: pad pin, DW01A + FS8205A, mạch lái motor.', 2)
draw_pcb(c, CL, 64, H - 110, 620, 340, 'F', view=(50, 50, 90, 88), text_min=3.2, ratsnest=RAT['CL'], labels=['U3', 'U5', 'Q1', 'Q2', 'J2', 'J3', 'J4', 'D4', 'Q3', 'Q4'], label_size=11)
legend(H - 470)
doc.text(710, H - 120, 300, 'TP4056 và DW01A + FS8205A đặt gần pad pin B+/B−. Theo brief, pad đáy TP4056 nối mảng đồng ≥ 100 mm² (chưa hoàn tất vì chưa định tuyến).\n\nGND trên bo là P− của mạch bảo vệ; B− chỉ nối qua FS8205A.', 14, INK)

sch_page('NovaCane Clip schematic MCU, boot và nút', 'Phần 1: ESP32-C3-MINI-1, EN/BOOT, ba nút, LED trạng thái và đo pin.', 'CL', S(29, 80, 665, 560),
         'U1 ESP32-C3-MINI-1-N4X: 3V3 10 µF + 100 nF; EN 10 kΩ lên 3V3 + 1 µF.\nGPIO9 (BOOT), GPIO8 và GPIO2 đều kéo lên 10 kΩ.\nSW2 Mode GPIO10, SW3 Xin đường GPIO2, SW4 SOS GPIO20; mỗi nút 10 kΩ lên 3V3 và 100 nF.\nĐo pin: BAT+ → 470 kΩ / 470 kΩ → GPIO0.')
sch_page('NovaCane Clip schematic sạc, bảo vệ và chia tải', 'Phần 2: TP4056, DW01A + FS8205A, D4/Q2, SW1 và LDO.', 'CL', S(670, 90, 1440, 665),
         'U3 TP4056: PROG 3,0 kΩ cho 400 mA, CE nối VCC, TEMP nối GND.\nU5 DW01A + Q1 FS8205A: bảo vệ pin một cell.\nD4 SS14 và Q2 AO3401A tạo power-path; VSYS 22 µF.\nU4 AP2112K-3.3 cấp 3V3; EN nối VSYS qua SW1, kéo xuống 100 kΩ.')
sch_page('NovaCane Clip schematic USB-C và ESD', 'Phần 3: J1 USB-C, USBLC6-2SC6 và VBUS_DET.', 'CL', S(29, 590, 665, 1010),
         'CC1 và CC2 mỗi chân 5,1 kΩ 1% xuống GND.\nD− nối GPIO18, D+ nối GPIO19: USB-Serial-JTAG của ESP32-C3, một cổng dùng cho cả sạc và nạp firmware.\nU2 USBLC6-2SC6 trên D+/D−/VBUS.\nVBUS_DET: 68 kΩ / 100 kΩ → GPIO21, 2,98 V khi có 5,0 V.')
sch_page('NovaCane Clip schematic IMU và I²C', 'Phần 4: MPU-6050 (U6) và chân GY-521 dự phòng.', 'CL', S(670, 640, 1440, 1000),
         'MPU-6050 cùng mạch như NovaChest: VDD/VLOGIC 3V3, REGOUT 100 nF, CPOUT 2,2 nF, INT → GPIO1.\nSDA/SCL (GPIO4/5) kéo lên 3V3 bằng 4,7 kΩ.\nĐặt chip thẳng trục X của bo, cách 3 nút ≥ 8 mm.\nJ5 (GY-521) là tùy chọn, không lắp (DNP).')
sch_page('NovaCane Clip schematic motor, đèn "Xin đường"', 'Phần 5: Q3/Q4 (motor), Q5 (đèn), D1–D3.', 'CL', S(1440, 770, 1990, 1060),
         'Q3/Q4 AO3400A, gate từ GPIO6/7 qua 100 Ω, kéo xuống 100 kΩ; nguồn motor là VSYS.\nD5/D6 B5819W flyback.\nQ5 AO3400A (gate GPIO3): drain chung cathode ba nhánh, mỗi nhánh một điện trở lên VSYS: D1 đỏ + 100 Ω, D2 đỏ + 100 Ω, D3 trắng + 68 Ω.')

doc.std('NovaCane Clip bảng gán chân ESP32-C3', 'Bảng này thay cho pin map Super Mini trong Đặc tả v2. GPIO11–17 không đưa ra ngoài module.', 2)
gpc = [('0', 'VBAT_ADC', 'ADC1_CH0'), ('1', 'IMU_INT', ''), ('2', 'BTN_ROUTE (Xin đường)', 'Strapping, 10 kΩ lên'), ('3', 'LED_BEACON', 'Gate Q5'),
       ('4', 'I2C_SDA', '4,7 kΩ lên'), ('5', 'I2C_SCL', '4,7 kΩ lên'), ('6', 'MOT_L_PWM', 'Gate Q3'), ('7', 'MOT_R_PWM', 'Gate Q4'),
       ('8', 'LED_STATUS', 'Strapping, 10 kΩ lên, sáng khi mức thấp'), ('9', 'BOOT', 'Strapping, 10 kΩ lên, có test pad'), ('10', 'BTN_MODE', ''),
       ('18', 'USB_D−', ''), ('19', 'USB_D+', ''), ('20', 'BTN_SOS', 'U0RXD, 10 kΩ lên'), ('21', 'VBUS_DET', 'U0TXD, cầu chia; firmware cấu hình lại thành input')]
doc.table(64, H - 125, [80, 330, 526], [['GPIO', 'Chức năng', 'Ghi chú']] + [list(r) for r in gpc], size=14, pad=5, mono=(0, 1))

doc.std('NovaCane Clip đầu nối và pinout', 'Pad dây hàn trực tiếp cho pin, motor và LED; J5 (GY-521) là tùy chọn không lắp.', 2)
ycl = doc.table(64, H - 120, [60, 330, 546], conn_rows(CL, ['J1', 'J2', 'J3', 'J4', 'J5']), size=13.5, pad=5.5, mono=(0, 2))
tpc = sorted([f for f in CL.fps if f['ref'].startswith('TP')], key=lambda f: refnum(f['ref'])[1])
rows = [['Điểm đo', 'Net', 'Mặt']] + [[f['ref'], f['value'], f['layer']] for f in tpc]
c.setFont('ArB', 16); c.setFillColor(NAVY); c.drawString(64, ycl - 28, 'Điểm đo (13 pad Ø1,0 mm, mặt trên)')
tp_s = [rows[0]] + rows[1:]
doc.table(64, ycl - 40, [100, 150, 70], tp_s[:8], size=12, pad=3.8, mono=(1,))
doc.table(64 + 420, ycl - 40, [100, 150, 70], [tp_s[0]] + tp_s[8:], size=12, pad=3.8, mono=(1,))

bom_pages('BOM NovaCane Clip', bg_cl, qty_cl, nl_cl, 'NS-CLIP-MB')

# ============================ 4. KIỂM CHỨNG ==================================
doc.divider('KIỂM CHỨNG', 'THIẾT KẾ', 'ERC · DRC · Bộ dữ liệu xuất', 'NS-CHEST-MB / NS-CLIP-MB', 3)

def kc(a): return a
doc.std('Kết quả kiểm tra thiết kế (KiCad 10.0.6)', f'Báo cáo ERC/DRC xuất ngày {today} từ thư mục review/.', 3)
rows = [['Kiểm tra thiết kế', 'NS-CHEST-MB', 'NS-CLIP-MB', 'NS-CLIP-MB (bản định tuyến thử)'],
        ['ERC', f'{ee_ch} lỗi, {ew_ch} cảnh báo', f'{ee_cl} lỗi, {ew_cl} cảnh báo', '—'],
        ['DRC: lỗi (không kể hở)', str(e_ch), str(e_cl), str(e_cr)],
        ['DRC: cảnh báo', str(w_ch), str(w_cl), str(w_cr)],
        ['Kết nối PCB còn hở', str(u_ch), str(u_cl), str(u_cr)],
        ['Đối chiếu schematic ↔ PCB', f'{parity_ch} sai khác', f'{parity_cl} sai khác', '0 sai khác'],
        ['Pad · linh kiện đã đặt', f'{npads_ch} · {nfp_ch}', f'{npads_cl} · {nfp_cl}', f'{npads_cl} · {nfp_cl}'],
        ['Dây · via', f'{len(CH.segs)} · {len(CH.vias)}', f'{len(CL.segs)} · {len(CL.vias)}', f'{len(CR.segs)} · {len(CR.vias)}']]
colr = {(2, 1): BAD, (2, 2): BAD, (2, 3): BAD, (4, 1): BAD, (4, 2): BAD, (4, 3): BAD, (5, 1): OK, (5, 2): OK, (5, 3): OK, (1, 1): OK, (1, 2): OK}
y = doc.table(64, H - 125, [250, 200, 200, 286], rows, size=16.5, pad=8, colors=colr)
doc.text(64, y - 18, 940, 'Chưa thể coi hai bo là "0 vi phạm": các kết nối hở là do chưa định tuyến xong. Lỗi hole_clearance và drill_out_of_range là lỗi footprint/thiết lập cần sửa, được liệt kê ở trang sau.', 15, INK)

def drc_table(title, counts, unconn, note):
    notes = {'unconnected_items': 'Kết nối chưa có dây; do chưa định tuyến xong',
             'hole_clearance': 'Pad GND A1/B12/A12/B1 của J1 cách lỗ NPTH 0,194 mm (yêu cầu 0,25 mm)',
             'drill_out_of_range': 'Via/pad nhiệt PTH 41 của U4 khoan 0,2 mm < tối thiểu 0,3 mm',
             'silk_overlap': 'Chữ silkscreen chồng nhau',
             'nonmirrored_text_on_back_layer': 'Chữ ở mặt sau chưa lật gương',
             'isolated_copper': 'Mảng đồng cô lập chưa nối net',
             'silk_edge_clearance': 'Silkscreen sát mép bo',
             'lib_footprint_issues': 'Footprint khác thư viện',
             'track_width': 'Dây hẹp hơn quy tắc tối thiểu',
             'copper_edge_clearance': 'Đồng sát mép bo',
             'starved_thermal': 'Thermal relief thiếu nhánh nối',
             'clearance': 'Khoảng hở giữa hai net',
             'via_dangling': 'Via không nối vào dây nào',
             'silk_over_copper': 'Silkscreen chồng lên đồng'}
    rows = [['Loại vi phạm', 'Mức', 'Số lượng', 'Diễn giải']]
    rows.append(['unconnected_items', 'lỗi', str(unconn), notes['unconnected_items']])
    for (sev, typ), n in sorted(counts.items(), key=lambda kv: (kv[0][0] != 'error', -kv[1])):
        rows.append([typ, 'lỗi' if sev == 'error' else 'cảnh báo', str(n), notes.get(typ, '')])
    return rows

doc.std('DRC NS-CHEST-MB theo loại vi phạm', None, 3)
rows = drc_table('', dc_ch, u_ch, '')
doc.table(64, H - 100, [250, 90, 100, 496], rows, size=15.5, pad=8, mono=(0,))
doc.std('DRC NS-CLIP-MB theo loại vi phạm', 'Bản PCB chính NS-CLIP-MB.kicad_pcb (bản định tuyến thử ở trang sau).', 3)
rows = drc_table('', dc_cl, u_cl, '')
y = doc.table(64, H - 120, [250, 90, 100, 496], rows, size=15, pad=7, mono=(0,))
doc.std('DRC NS-CLIP-MB bản định tuyến thử (routing/)', 'File routing/NS-CLIP-MB_routed.kicad_pcb: ' + f'{len(CR.segs)} đoạn dây, {len(CR.vias)} via.', 3)
rows = drc_table('', dc_cr, u_cr, '')
doc.table(64, H - 120, [250, 90, 100, 496], rows, size=14, pad=4.8, mono=(0,))

doc.std('Các lỗi cần sửa trước khi đặt gia công', 'Rút ra từ báo cáo DRC; hướng xử lý là đề xuất, chưa áp dụng vào file PCB.', 3)
rows = [['Bo', 'Lỗi', 'Nguyên nhân', 'Hướng xử lý đề xuất'],
        ['Cả hai', 'hole_clearance ×4', 'Pad GND A1, B12, A12, B1 của J1 cách lỗ NPTH 0,194 mm, yêu cầu 0,25 mm', 'Kiểm tra footprint USB-C GCT USB4105; giảm pad hoặc hạ ràng buộc khi JLC cho phép'],
        ['CHEST', 'drill_out_of_range ×12', 'Via nhiệt PTH 41 của U4 khoan 0,2 mm, tối thiểu 0,3 mm', 'Dùng via 0,3 mm hoặc đổi pad nhiệt sang via-in-pad theo quy tắc JLC'],
        ['CHEST', f'{u_ch} kết nối hở', 'Chưa định tuyến; 4 lớp cần hoàn tất plane L2/L3', 'Định tuyến nguồn, khâu GND, hoàn tất pour'],
        ['CLIP', f'{u_cl} kết nối hở', 'File chính chưa định tuyến', 'Lấy bản routing/ làm cơ sở và sửa lỗi track_width, khoảng hở mép'],
        ['CLIP thử', f"track_width ×{dc_cr[('error', 'track_width')]}, copper_edge_clearance ×{dc_cr[('error', 'copper_edge_clearance')]}", 'Dây hẹp hơn quy tắc; đồng/dây sát mép bo', 'Mở rộng dây nguồn theo bảng IPC-2221; lùi đồng khỏi mép'],
        ['Cả hai', 'Cảnh báo silkscreen', f'{dc_ch.get(("warning", "silk_overlap"), 0)} và {dc_cl.get(("warning", "silk_overlap"), 0)} cảnh báo silk_overlap', 'Dời hoặc thu nhỏ chữ Reference sau khi định tuyến xong']]
doc.table(64, H - 120, [90, 190, 330, 326], rows, size=15.5, pad=7.5)

doc.std('Bộ dữ liệu xuất của hai bo', 'Đối chiếu với danh sách file cần giao lại trong brief.', 3)
exp = {'NS-CHEST-MB': os.listdir(BASE + r"\NS-CHEST-MB\exports"), 'NS-CLIP-MB': os.listdir(BASE + r"\NS-CLIP-MB\exports")}
def has(b, ext): return any(f.lower().endswith(ext) for f in exp[b])
rows = [['Hạng mục', 'NS-CHEST-MB', 'NS-CLIP-MB'],
        ['Project KiCad (sch, pcb, pro)', 'Có', 'Có'],
        ['Schematic xuất PDF', 'Có' if has('NS-CHEST-MB', '.pdf') else 'Chưa', 'Có' if has('NS-CLIP-MB', '.pdf') else 'Chưa'],
        ['BOM (CSV)', 'Có, chưa có mã LCSC', 'Có, chưa có mã LCSC'],
        ['STEP bo đã lắp linh kiện', 'Có' if has('NS-CHEST-MB', '.step') else 'Chưa', 'Có' if has('NS-CLIP-MB', '.step') else 'Chưa'],
        ['Gerber · file khoan', 'Chưa', 'Chưa'], ['CPL (tọa độ lắp)', 'Chưa', 'Chưa'], ['DXF đường bao', 'Chưa', 'Chưa'],
        ['Báo cáo ERC · DRC', 'Có (DRC chưa đạt)', 'Có (DRC chưa đạt)']]
colr = {}
for ri, r in enumerate(rows[1:], 1):
    for ci in (1, 2):
        v = r[ci]
        colr[(ri, ci)] = OK if v.startswith('Có') and 'chưa' not in v else (BAD if v == 'Chưa' else WARN)
doc.table(64, H - 125, [330, 300, 306], rows, size=16.5, pad=8, colors=colr)

doc.std('Đối chiếu số liệu giữa brief và file PCB', 'Các điểm lệch phát hiện khi đọc file; cần quyết định trước khi chốt layout.', 3)
rows = [['#', 'Điểm lệch', 'Brief', 'File PCB / schematic'],
        ['1', 'Vị trí lỗ H1 (NS-CHEST-MB)', 'X −44, Z +22', 'X −14,0; Z −7,7'],
        ['2', 'Vị trí module U4 theo X', '−38 … −20 (đề xuất)', f'{min(xs_ := [kipcb.pad_world(fpm["U4"], p_)[0] - 100 for p_ in fpm["U4"]["pads"]]):.1f} … {max(xs_):.1f}'.replace('.', ',').replace('-', '−')],
        ['3', 'Tên camera', 'OV3660', 'Symbol/BOM ghi OV5640_FPC_VERIFY_CONTACT'],
        ['4', 'Connector đánh dấu VERIFY', 'Pinout phải đối chiếu board thật', 'J2, J3, J5, J6, L1 còn nhãn VERIFY trong schematic'],
        ['5', 'Mã LCSC trong BOM', 'Chỉ ghi mã đã tra (C479072, C24112)', 'File CSV xuất không có cột LCSC'],
        ]
yy_ = doc.table(64, H - 125, [40, 280, 280, 336], rows, size=16.5, pad=9)
doc.text(64, yy_ - 18, 940, 'Điểm 1–2 là sai lệch về cơ khí/mặt bằng; điểm 3–5 là sai lệch về tài liệu. Chưa có điểm nào được sửa trong file PCB.', 15, INK)

# ============================ 5. LỘ TRÌNH ====================================
doc.divider('LỘ TRÌNH', 'HOÀN THIỆN', 'Các chặng chính', 'NS-CHEST-MB / NS-CLIP-MB', 4)
doc.std('Lộ trình hoàn thiện', None, 4)
gs = [('G1', 'Hồ sơ thiết kế', 'Schematic, footprint, đặt linh kiện', OK, 'Xong'),
      ('G2', 'Định tuyến', 'Hoàn tất dây, plane, via khâu GND', BAD, 'Chưa xong'),
      ('G3', 'DRC và review', 'DRC sạch; người khác review schematic', BAD, 'Chưa xong'),
      ('G4', 'Dữ liệu sản xuất', 'Gerber, khoan, CPL, BOM LCSC, DXF, STEP', WARN, 'Một phần'),
      ('G5', 'Kiểm tra cơ khí', 'STEP vào FreeCAD, va chạm với vỏ, pin, cảm biến', WARN, 'Một phần'),
      ('G6', 'Bring-up', 'Cấp nguồn lab, đo dòng, RSSI, nhiệt', HexColor('#777777'), 'Chưa bắt đầu')]
for i, (g, t, s, col, st_) in enumerate(gs):
    x = 64 + i * 158
    c.setFillColor(RED); c.setFont('ArB', 24); c.drawCentredString(x + 66, H - 200, g)
    c.setFillColor(NAVY); c.setFont('ArB', 16)
    for k, ln in enumerate(simpleSplit(t, 'ArB', 16, 145)): c.drawCentredString(x + 66, H - 235 - k * 19, ln)
    c.setFillColor(GRAY); c.setFont('Ar', 13)
    for k, ln in enumerate(simpleSplit(s, 'Ar', 13, 145)): c.drawCentredString(x + 66, H - 285 - k * 16, ln)
    doc.chip(x + 6, H - 350, 120, 24, st_, col)
doc.text(64, H - 440, 940, 'Đặt mạch chỉ sau khi hoàn tất "Trước khi đặt mạch" trong brief. Buổi bring-up đầu tiên cấp nguồn bằng nguồn lab giới hạn dòng, chưa cắm pin thật.', 15, INK)

doc.std('Checklist trước khi đặt mạch', 'Rút gọn từ mục 7 của brief; trạng thái tại thời điểm xuất hồ sơ.', 4)
rows = [['Hạng mục', 'Trạng thái'],
        ['Đã có hàng thật và đã đo: breakout VL53L8CX, JSN-SR04T, camera OV3660, pin LP124065 và 603450', 'Chưa xác nhận trong hồ sơ'],
        ['Pinout J2, J3, J5, J6 đối chiếu ảnh chụp board thật', 'Chưa (schematic còn nhãn VERIFY)'],
        ['Footprint module ESP32 từ thư viện chính thức; vùng cấm đồng dưới antenna vẽ trên mọi lớp', 'Có vùng keepout (cần review)'],
        ['Không chân strapping nào bị kéo sai mức (S3: GPIO0=1, 45=0, 46=0; C3: GPIO2=8=9=1)', 'Theo schematic: đạt (chờ bring-up)'],
        ['STEP bo lắp linh kiện vào FreeCAD: 0 va chạm với vỏ, pin, đầu dò, camera, ToF', 'Có STEP, chưa chạy va chạm'],
        ['Vùng A (bóng đầu dò siêu âm): không linh kiện cao quá 1,2 mm', 'Chưa kiểm tra'],
        ['DRC theo quy tắc JLC đạt, không còn lỗi', 'Chưa đạt'],
        ['Một người khác review schematic theo tài liệu', 'Chưa']]
colr = {}
for ri, r in enumerate(rows[1:], 1):
    colr[(ri, 1)] = BAD if r[1] in ('Chưa', 'Chưa đạt', 'Chưa kiểm tra') or r[1].startswith('Chưa (') else WARN
doc.table(64, H - 120, [650, 286], rows, size=16, pad=8, colors=colr)

doc.std('Bring-up NS-CHEST-MB', 'Chỉ thực hiện sau khi bo đạt DRC và được sản xuất.', 4)
steps_c = ['Chưa lắp ESP32, chưa cắm camera; cấp 3,7 V vào J4 bằng nguồn lab giới hạn 0,5 A.', 'SW1 ở OFF: dòng < 0,2 mA sau 40 s.',
           'Gạt ON: 5V_SW lên 4,9–5,15 V trong 1 s; 3V3 3,25–3,35 V; 2V8 và 1V5 đúng.', 'Kiểm tra IP5306: xung KEY 0,3–0,6 s, gạt ON/OFF 20 lần bật đủ 20 lần.',
           'Cắm USB khi máy đang ON: đo độ sụt 5V_SYS, ghi lại ESP32 có reset không.', 'Nạp firmware qua USB-C: giữ BOOT rồi nhấn RESET; quét I²C thấy 0x68 và 0x29.',
           'Camera chụp JPEG ở XCLK 20 MHz; hai JSN đo đúng ở 0,5 m, 1 m, 2 m (ECHO ≤ 3,3 V).', 'Motor rung đúng bên; đo dòng 10 phút ở chế độ Đi bộ; nhiệt module ESP32 < 65 °C; đo RSSI BLE.']
doc.bullets(64, H - 125, 940, steps_c, 18.5, 11)

doc.std('Bring-up NS-CLIP-MB', 'Chỉ thực hiện sau khi bo đạt DRC và được sản xuất.', 4)
steps_l = ['Cấp 3,7 V vào B+/B− bằng nguồn lab giới hạn 0,3 A; SW1 OFF: dòng < 20 µA.', 'Gạt ON: 3V3 lên 3,25–3,35 V; hạ nguồn về 3,5 V và cho ESP32 phát BLE: 3V3 vẫn ≥ 3,2 V.',
           'Cắm USB khi máy ON: máy không reset, dòng sạc 360–440 mA (PROG = 1 V ứng với 400 mA), VBUS_DET = 1.',
           'Bảo vệ pin: xả nguồn lab xuống 2,4 V thì mạch ngắt; ngắn mạch P+/P− qua 0,1 Ω thì mạch ngắt.',
           'Nạp firmware lần đầu: chạm pad BOOT xuống GND rồi bật nguồn; các lần sau nạp tự động qua USB-JTAG.',
           'Ba nút, đèn "Xin đường" nháy 2 Hz, hai motor, MPU-6050 đọc 200 Hz; giữ nút Xin đường lúc bật máy vẫn khởi động bình thường.',
           'Đo RSSI khi Clip kẹp trên gậy nhôm thật; đo dòng trung bình 10 phút.']
doc.bullets(64, H - 125, 940, steps_l, 18.5, 12)

# ============================ 6. RỦI RO ======================================
doc.divider('ĐIỂM CẦN', 'KIỂM SOÁT', 'Rủi ro thiết kế và tài liệu tham khảo', 'NS-CHEST-MB / NS-CLIP-MB', 5)
doc.std('Sáu điểm phải xác minh trên hàng thật', 'Sai một trong số này là phải làm lại bo.', 5)
rows = [['#', 'Điểm chưa chắc', 'Ảnh hưởng nếu sai', 'Cách xác minh'],
        ['1', 'Loại tiếp điểm, thứ tự chân và chiều dài FPC của module OV3660', 'Camera không chạy, có thể cháy', 'Chụp FPC, đối chiếu bảng J2; đo chiều dài flex'],
        ['2', 'Pinout, nguồn và pull-up của breakout VL53L8CX', 'ToF không kết nối được', 'Chụp hai mặt board; nếu không có mạch chuyển mức, đổi sang loại có (kiểu Pololu #3419)'],
        ['3', 'Thứ tự chân board JSN và mức điện áp ECHO', 'Không đo được, hoặc hỏng GPIO', 'Oscilloscope'],
        ['4', 'IP5306: KEY tích cực thấp, tự thức khi có tải, sụt áp khi cắm sạc', 'Không bật được, hoặc máy reset', 'Thử trên module MHCD42 đang có'],
        ['5', 'Chiều cao công tắc, tact, USB-C so với các lỗ trên vỏ', 'Không lắp được, nút bấm không ăn', 'Đưa STEP linh kiện vào FreeCAD'],
        ['6', 'Hiệu năng antenna khi có pin, ngực người đeo và gậy nhôm gần đó', 'BLE rớt kết nối', 'Đo RSSI; nếu kém, Rev B dùng bản -1U với antenna ngoài']]
doc.table(64, H - 120, [36, 340, 240, 320], rows, size=16, pad=8)

doc.std('Đặc điểm kiểm soát rủi ro trên sơ đồ', None, 5)
rows = [['Vấn đề kỹ thuật', 'Phần tử trong thiết kế', 'Vai trò'],
        ['Bảo vệ đường pin', 'Chest: F1 PTC 0,5 A cho nhánh motor; Clip: DW01A + FS8205A', 'Ngắt khi quá dòng, ngắn mạch, quá xả'],
        ['Tín hiệu 5 V vào GPIO', 'Cầu chia ECHO 10k/15k, VBUS_DET 68k/100k, buffer 74AHCT1G125', 'Giữ mức ≤ 3,3 V tại ESP32'],
        ['Chân strapping', '100 kΩ kéo xuống gate motor (Chest GPIO45/46); 10 kΩ kéo lên GPIO2/8/9 (Clip)', 'Đúng mức lúc khởi động'],
        ['Xung hồi và nhiễu motor', 'Diode B5819W song song motor, 100 nF tại connector', 'Đường hồi dòng, chống nhiễu'],
        ['ESD cổng USB', 'USBLC6-2SC6 trên D+/D− và VBUS', 'Bảo vệ cổng sạc/nạp'],
        ['Khởi động mềm tải', 'Q1: 10 kΩ + 100 nF gate–source (τ ≈ 1 ms)', 'Hạn chế dòng vọt vào tụ'],
        ['Tắt máy đúng cách', 'Công tắc chỉ điều khiển MOSFET hoặc chân EN', 'Công tắc chỉ mang dòng µA']]
doc.table(64, H - 100, [250, 450, 236], rows, size=16, pad=8.5)

doc.std('Việc phía cơ khí phải sửa theo bo mới', None, 5)
doc.text(64, H - 100, 460, 'NovaChest', 20, RED, 'ArB')
doc.bullets(64, H - 135, 440, ['Dời nút Mode về Y ≈ 21 để khớp với bo.', 'Kéo dài light pipe đến Y = 22,4.', 'Làm 4 trụ bắt bo tại H1–H4 (H1 đang lệch brief, cần xác nhận).',
                               'Bỏ trụ và gân của K9_41, IP5306 module, GY-521.'], 18, 10)
doc.text(540, H - 100, 460, 'NovaCane Clip', 20, RED, 'ArB')
doc.bullets(540, H - 135, 440, ['Gân đỡ và gân ép bo theo file DXF của bo.', 'Chiều dài chân nút bấm theo tact đã chọn (đỉnh nút Z = 29,4 ± 0,2 mm).', 'Khe cho LED đỏ 5 mm và ống LED trắng ở đầu vỏ.'], 18, 10)

doc.std('Tài liệu tham khảo', None, 5)
refs = ['[D1] Schematic ESP32-S3-EYE V2.2 (Espressif): pinout FPC camera, rail 2V8/1V5, buck SY8088.',
        '[D2] ESP32-S3-WROOM-1 datasheet (Espressif): chân strapping, GPIO35–37 bị PSRAM octal chiếm.',
        '[D3] ESP32-C3-MINI-1 datasheet (Espressif) và hướng dẫn nối dây nạp ESP32-C3.',
        '[D4] IP5306 datasheet (Injoinic) và ghi chú sụt áp khi chuyển nguồn.',
        '[D5] TP4056 datasheet; SY8088 application note và SY8088IAAC trên LCSC.',
        '[D6] VL53L8CX (STMicroelectronics) và Pololu #3419.',
        '[D7] JSN-SR04T V3.0; MPU-6050 pinout; motor 1027 INEED C1027.',
        '[D8] NovaSight 2026, Brief thiết kế PCB (NovaChest & NovaCane Clip), 06/11/2026 (tài liệu nội bộ).']
doc.bullets(64, H - 105, 940, refs, 17, 11)

doc.save()

# ------------------------------- overlays ------------------------------------
src_cache = {}
d = pymupdf.open(TMP)
for pg, (x0, y0, x1, y1), src, frac in doc.overlays:
    if src not in src_cache: src_cache[src] = pymupdf.open(src)
    sd = src_cache[src]
    pr = sd[0].rect
    clip = pymupdf.Rect(frac[0] * pr.width, frac[1] * pr.height, frac[2] * pr.width, frac[3] * pr.height)
    d[pg].show_pdf_page(pymupdf.Rect(x0 + 1, H - y1 + 1, x1 - 1, H - y0 - 1), sd, 0, clip=clip)
d.set_metadata({'title': 'NovaSight - Hồ sơ thiết kế PCB', 'author': 'Dự án NovaSight', 'subject': 'NS-CHEST-MB, NS-CLIP-MB'})
d.save(OUT, garbage=3, deflate=True)
print('pages', len(d), 'saved', OUT, os.path.getsize(OUT))
print('GPIO mismatches vs design json:', GP_MISMATCH)







