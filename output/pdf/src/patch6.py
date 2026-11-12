p = "lib.py"
t = open(p, encoding="utf8").read()
def rep(old, new):
    global t
    assert old in t, old[:80]
    t = t.replace(old, new, 1)
rep("pdfmetrics.registerFont(TTFont('Ar', r'C:\\Windows\\Fonts\\arial.ttf'))", "pdfmetrics.registerFont(TTFont('Ar', r'C:\\Windows\\Fonts\\segoeui.ttf'))")
rep("pdfmetrics.registerFont(TTFont('ArB', r'C:\\Windows\\Fonts\\arialbd.ttf'))", "pdfmetrics.registerFont(TTFont('ArB', r'C:\\Windows\\Fonts\\segoeuib.ttf'))")
rep("pdfmetrics.registerFont(TTFont('ArI', r'C:\\Windows\\Fonts\\ariali.ttf'))", "pdfmetrics.registerFont(TTFont('ArI', r'C:\\Windows\\Fonts\\segoeuii.ttf'))\npdfmetrics.registerFont(TTFont('Mo', r'C:\\Windows\\Fonts\\consola.ttf'))\npdfmetrics.registerFont(TTFont('MoB', r'C:\\Windows\\Fonts\\consolab.ttf'))")
rep("colors=None, maxh=None):", "colors=None, maxh=None, mono=()):")
rep("""                font = 'ArB' if (header and ri == 0) or (bold_first and ci == 0) else 'Ar'
                lines = []
                for para in str(cell).split('\\n'):
                    lines += simpleSplit(para, font, size, widths[ci] - 2 * pad) or ['']
                cells.append((font, lines))""", """                font = 'ArB' if (header and ri == 0) or (bold_first and ci == 0) else 'Ar'
                fs = size
                if ci in mono and not (header and ri == 0):
                    font = 'Mo'; fs = size * 0.9
                lines = []
                for para in str(cell).split('\\n'):
                    lines += simpleSplit(para, font, fs, widths[ci] - 2 * pad) or ['']
                cells.append((font, lines, fs))""")
rep("""            for ci, (font, lines) in enumerate(cells):
                col = NAVY if (header and ri == 0) else INK
                if colors and (ri, ci) in colors:
                    col = colors[(ri, ci)]; font = 'ArB'
                c.setFont(font, size); c.setFillColor(col)""", """            for ci, (font, lines, fs) in enumerate(cells):
                col = NAVY if (header and ri == 0) else INK
                if colors and (ri, ci) in colors:
                    col = colors[(ri, ci)]; font = 'MoB' if font == 'Mo' else 'ArB'
                c.setFont(font, fs); c.setFillColor(col)""")
open(p, "w", encoding="utf8").write(t)

p = "build.py"
t = open(p, encoding="utf8").read()
rep("doc.table(40, H - 110, widths, [hdr] + [list(r) for r in ch_], size=size, pad=pad)", "doc.table(40, H - 110, widths, [hdr] + [list(r) for r in ch_], size=size, pad=pad, mono=(0, 2))")
rep("['J1', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9']), size=13.5, pad=7)", "['J1', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9']), size=13.5, pad=7, mono=(0, 2))")
rep("conn_rows(CL, ['J1', 'J2', 'J3', 'J4', 'J5']), size=13.5, pad=5.5)", "conn_rows(CL, ['J1', 'J2', 'J3', 'J4', 'J5']), size=13.5, pad=5.5, mono=(0, 2))")
rep("rows1, size=14, pad=5.5)", "rows1, size=14, pad=5.5, mono=(1,))")
rep("rows2, size=14, pad=5.5)", "rows2, size=14, pad=5.5, mono=(1,))")
rep("rows[:9], size=15, pad=7)", "rows[:9], size=15, pad=7, mono=(1,))")
rep("[rows[0]] + rows[9:], size=15, pad=7)", "[rows[0]] + rows[9:], size=15, pad=7, mono=(1,))")
rep("tp_s[:8], size=12, pad=3.8)", "tp_s[:8], size=12, pad=3.8, mono=(1,))")
rep("[tp_s[0]] + tp_s[8:], size=12, pad=3.8)", "[tp_s[0]] + tp_s[8:], size=12, pad=3.8, mono=(1,))")
rep("[list(r) for r in gp[:half]], size=11, pad=4.5)", "[list(r) for r in gp[:half]], size=11, pad=4.5, mono=(0, 1, 2))")
rep("[list(r) for r in gp[half:]], size=11, pad=4.5)", "[list(r) for r in gp[half:]], size=11, pad=4.5, mono=(0, 1, 2))")
rep("[list(r) for r in gpc], size=14, pad=5)", "[list(r) for r in gpc], size=14, pad=5, mono=(0, 1))")
rep("doc.table(64, H - 100, [250, 90, 100, 496], rows, size=15.5, pad=8)", "doc.table(64, H - 100, [250, 90, 100, 496], rows, size=15.5, pad=8, mono=(0,))")
rep("y = doc.table(64, H - 120, [250, 90, 100, 496], rows, size=15, pad=7)", "y = doc.table(64, H - 120, [250, 90, 100, 496], rows, size=15, pad=7, mono=(0,))")
rep("doc.table(64, H - 120, [250, 90, 100, 496], rows, size=14, pad=4.8)", "doc.table(64, H - 120, [250, 90, 100, 496], rows, size=14, pad=4.8, mono=(0,))")
open(p, "w", encoding="utf8").write(t)
print("ok")
