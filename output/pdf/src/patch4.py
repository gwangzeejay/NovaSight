p = "build.py"
t = open(p, encoding="utf8").read()
def rep(old, new):
    global t
    assert old in t, old[:80]
    t = t.replace(old, new, 1)
rep("doc.table(64, H - 120, [180, 560, 196], rows, size=14.5, pad=7)", "doc.table(64, H - 120, [180, 560, 196], rows, size=15.5, pad=6.5)")
rep("doc.table(64, H - 125, [130, 270, 536], rows, size=15.5, pad=8)", "doc.table(64, H - 125, [130, 270, 536], rows, size=17, pad=8.5)")
rep("doc.table(64, H - 120, [130, 330, 150, 150, 176], rows, size=14.5, pad=7)", "doc.table(64, H - 120, [130, 330, 150, 150, 176], rows, size=16, pad=7.5)")
rep("y = doc.table(64, H - 125, [250, 190, 496], rows, size=14, pad=7)", "y = doc.table(64, H - 120, [250, 190, 496], rows, size=15.5, pad=7)")
rep("doc.table(64, y - 22, [330, 260, 346], rows, size=13, pad=6)", "doc.table(64, y - 18, [330, 260, 346], rows, size=14, pad=5.5)")
rep("y = doc.table(64, H - 125, [320, 260, 356], rows, size=14, pad=7, colors=col)", "y = doc.table(64, H - 125, [320, 260, 356], rows, size=16, pad=7.5, colors=col)")
rep("['J1', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9']), size=12, pad=6)", "['J1', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9']), size=13.5, pad=7)")
rep("doc.table(64, H - 125, [80, 380], rows1, size=13, pad=5.5)", "doc.table(64, H - 120, [80, 380], rows1, size=14, pad=5.5)")
rep("doc.table(64 + 480 + 12, H - 125, [80, 380 - 12], rows2, size=13, pad=5.5)", "doc.table(64 + 480 + 12, H - 120, [80, 380 - 12], rows2, size=14, pad=5.5)")
rep("'Lưu ý: symbol trong schematic ghi OV5640", "'Lưu ý: symbol trong schematic ghi OV5640") if False else None
rep("doc.table(64, H - 125, [110, 150, 80], rows[:9], size=13, pad=5.5)", "doc.table(64, H - 125, [110, 150, 80], rows[:9], size=15, pad=7)")
rep("doc.table(64 + 380, H - 125, [110, 150, 80], [rows[0]] + rows[9:], size=13, pad=5.5)", "doc.table(64 + 380, H - 125, [110, 150, 80], [rows[0]] + rows[9:], size=15, pad=7)")
rep("y = doc.table(64, H - 125, [320, 300, 316], rows, size=14, pad=7)", "y = doc.table(64, H - 125, [320, 300, 316], rows, size=15.5, pad=7.5)")
rep("rows], size=13, pad=5.2)", "rows], size=14, pad=5)") if False else None
rep("[list(r) for r in gpc], size=13, pad=5.2)", "[list(r) for r in gpc], size=14, pad=5)")
rep("conn_rows(CL, ['J1', 'J2', 'J3', 'J4', 'J5']), size=12.5, pad=5)", "conn_rows(CL, ['J1', 'J2', 'J3', 'J4', 'J5']), size=13.5, pad=5.5)")
rep("tp_s[:8], size=11, pad=3.6)", "tp_s[:8], size=12, pad=3.8)")
rep("[tp_s[0]] + tp_s[8:], size=11, pad=3.6)", "[tp_s[0]] + tp_s[8:], size=12, pad=3.8)")
rep("y = doc.table(64, H - 125, [250, 200, 200, 286], rows, size=15, pad=7, colors=colr)", "y = doc.table(64, H - 125, [250, 200, 200, 286], rows, size=16.5, pad=8, colors=colr)")
rep("doc.table(64, H - 100, [250, 90, 100, 496], rows, size=14, pad=7)", "doc.table(64, H - 100, [250, 90, 100, 496], rows, size=15.5, pad=8)")
rep("y = doc.table(64, H - 120, [250, 90, 100, 496], rows, size=14, pad=7)", "y = doc.table(64, H - 120, [250, 90, 100, 496], rows, size=15, pad=7)")
rep("doc.table(64, H - 120, [250, 90, 100, 496], rows, size=12.5, pad=4.6)", "doc.table(64, H - 120, [250, 90, 100, 496], rows, size=14, pad=4.8)")
rep("doc.table(64, H - 125, [90, 190, 330, 326], rows, size=12.5, pad=6)", "doc.table(64, H - 120, [90, 190, 330, 326], rows, size=14, pad=6.5)")
rep("doc.table(64, H - 125, [330, 300, 306], rows, size=15, pad=7, colors=colr)", "doc.table(64, H - 125, [330, 300, 306], rows, size=16.5, pad=8, colors=colr)")
rep("doc.table(64, H - 125, [40, 280, 280, 336], rows, size=13, pad=6.5)", "doc.table(64, H - 125, [40, 280, 280, 336], rows, size=15, pad=8)")
rep("doc.table(64, H - 125, [650, 286], rows, size=13, pad=6.5, colors=colr)", "doc.table(64, H - 120, [650, 286], rows, size=14.5, pad=7, colors=colr)")
rep("doc.table(64, H - 125, [36, 340, 240, 320], rows, size=12.5, pad=6)", "doc.table(64, H - 120, [36, 340, 240, 320], rows, size=14.5, pad=7)")
rep("doc.table(64, H - 100, [250, 450, 236], rows, size=13, pad=6.5)", "doc.table(64, H - 100, [250, 450, 236], rows, size=14.5, pad=7.5)")
rep("doc.bullets(64, H - 100, 940, refs, 15, 9)", "doc.bullets(64, H - 105, 940, refs, 17, 11)")
rep("'Khe cho LED đỏ 5 mm và ống LED trắng ở đầu vỏ.'], 16, 8)", "'Khe cho LED đỏ 5 mm và ống LED trắng ở đầu vỏ.'], 18, 10)")
rep("'Bỏ trụ và gân của K9_41, IP5306 module, GY-521.'], 16, 8)", "'Bỏ trụ và gân của K9_41, IP5306 module, GY-521.'], 18, 10)")
rep("doc.text(64, H - 470, 940, 'Lưu ý: symbol trong schematic ghi OV5640", "doc.text(64, H - 490, 940, 'Lưu ý: symbol trong schematic ghi OV5640") if False else None

# summary page
summary = '''
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

'''
rep("doc.std('Bố cục báo cáo', None, 0)", summary + "doc.std('Bố cục báo cáo', None, 0)")
open(p, "w", encoding="utf8").write(t)
print("ok")
