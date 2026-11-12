p = "build.py"
t = open(p, encoding="utf8").read()
def rep(old, new):
    global t
    assert old in t, old[:80]
    t = t.replace(old, new, 1)
rep("doc.table(64, H - 120, [90, 190, 330, 326], rows, size=14, pad=6.5)", "doc.table(64, H - 120, [90, 190, 330, 326], rows, size=15.5, pad=7.5)")
rep("doc.table(64, H - 120, [36, 340, 240, 320], rows, size=14.5, pad=7)", "doc.table(64, H - 120, [36, 340, 240, 320], rows, size=16, pad=8)")
rep("doc.table(64, H - 100, [250, 450, 236], rows, size=14.5, pad=7.5)", "doc.table(64, H - 100, [250, 450, 236], rows, size=16, pad=8.5)")
rep("doc.table(64, H - 120, [650, 286], rows, size=14.5, pad=7, colors=colr)", "doc.table(64, H - 120, [650, 286], rows, size=16, pad=8, colors=colr)")
rep("doc.table(64, H - 125, [40, 280, 280, 336], rows, size=15, pad=8)", "doc.table(64, H - 125, [40, 280, 280, 336], rows, size=16.5, pad=9)")
rep("doc.bullets(64, H - 125, 940, steps_c, 17, 9)", "doc.bullets(64, H - 125, 940, steps_c, 18.5, 11)")
rep("doc.bullets(64, H - 125, 940, steps_l, 17, 10)", "doc.bullets(64, H - 125, 940, steps_l, 18.5, 12)")
# progress page: bigger text
rep("c.setFillColor(NAVY); c.setFont('ArB', 17); c.drawString(x + 12, H - 205, t)\n    doc.text(x + 12, H - 215, 150, s, 13, GRAY)", "c.setFillColor(NAVY); c.setFont('ArB', 18); c.drawString(x + 12, H - 205, t)\n    doc.text(x + 12, H - 215, 150, s, 14.5, GRAY)")
rep("'Vì vậy hồ sơ này mô tả thiết kế, không phải xác nhận bo đủ điều kiện đặt gia công.'], 16)", "'Vì vậy hồ sơ này mô tả thiết kế, không phải xác nhận bo đủ điều kiện đặt gia công.'], 18)")
open(p, "w", encoding="utf8").write(t); print("ok")
