import re
p = "build.py"
t = open(p, encoding="utf8").read()
def rep(old, new, count=1):
    global t
    assert old in t, old[:80]
    t = t.replace(old, new, count)

rep("n_cu_ch = 4\n", """n_cu_ch = 4

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
""")
rep("draw_pcb(c, CH, 40, H - 95, 490, 300, 'F', text_min=4)", "draw_pcb(c, CH, 40, H - 95, 490, 300, 'F', text_min=4, ratsnest=RAT['CH'])")
rep("draw_pcb(c, CH, 550, H - 95, 490, 300, 'B', text_min=4)", "draw_pcb(c, CH, 550, H - 95, 490, 300, 'B', text_min=4, ratsnest=RAT['CH'])\nlegend(H - 470)")
rep("view=(52, 50, 112, 99), text_min=3.2)", "view=(52, 50, 112, 99), text_min=3.2, ratsnest=RAT['CH'], labels=['U4', 'J2', 'U7', 'U8', 'U10', 'SW2', 'SW3', 'SW5', 'D1'], label_size=11)\nlegend(H - 538)")
rep("view=(104, 50, 152, 100), text_min=3.2)", "view=(104, 50, 152, 100), text_min=3.2, ratsnest=RAT['CH'], labels=['U2', 'L1', 'U3', 'L2', 'Q1', 'Q2', 'Q3', 'J1', 'U1', 'F1', 'U9', 'SW2'], label_size=11)\nlegend(H - 538)")
rep("view=(50, 76, 112, 100), text_min=3.0)", "view=(50, 76, 112, 100), text_min=3.0, ratsnest=RAT['CH'], labels=['J3', 'J4', 'J5', 'J6', 'SW1', 'SW3', 'SW5', 'J9', 'U5', 'U6'], label_size=11)\nlegend(H - 538)")
rep("draw_pcb(c, CL, 40, H - 110, 490, 250, 'F', text_min=4)", "draw_pcb(c, CL, 40, H - 110, 490, 250, 'F', text_min=4, ratsnest=RAT['CL'])")
rep("draw_pcb(c, CL, 550, H - 110, 490, 250, 'B', text_min=4)", "draw_pcb(c, CL, 550, H - 110, 490, 250, 'B', text_min=4, ratsnest=RAT['CL'])\nlegend(H - 560)")
rep("view=(85, 50, 124, 88), text_min=3.2)", "view=(85, 50, 124, 88), text_min=3.2, ratsnest=RAT['CL'], labels=['U1', 'J1', 'U2', 'U4', 'SW1', 'U6', 'D3'], label_size=11)\nlegend(H - 470)")
rep("view=(50, 50, 90, 88), text_min=3.2)", "view=(50, 50, 90, 88), text_min=3.2, ratsnest=RAT['CL'], labels=['U3', 'U5', 'Q1', 'Q2', 'J2', 'J3', 'J4', 'D4', 'Q3', 'Q4'], label_size=11)\nlegend(H - 470)")
open(p, "w", encoding="utf8").write(t)
print("ok")
