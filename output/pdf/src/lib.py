import math, sys
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from reportlab.lib.colors import Color, HexColor
import kipcb

pdfmetrics.registerFont(TTFont('Ar', r'C:\Windows\Fonts\segoeui.ttf'))
pdfmetrics.registerFont(TTFont('ArB', r'C:\Windows\Fonts\segoeuib.ttf'))
pdfmetrics.registerFont(TTFont('ArI', r'C:\Windows\Fonts\segoeuii.ttf'))
pdfmetrics.registerFont(TTFont('Mo', r'C:\Windows\Fonts\consola.ttf'))
pdfmetrics.registerFont(TTFont('MoB', r'C:\Windows\Fonts\consolab.ttf'))

W, H = 1080.0, 607.5
RED = HexColor('#A33340'); NAVY = HexColor('#303650'); INK = HexColor('#172033')
GRAY = HexColor('#555B6B'); LINE = HexColor('#D9D9DE'); HEAD = HexColor('#F5E3E3')
OK = HexColor('#2E7D4F'); WARN = HexColor('#B7791F'); BAD = HexColor('#B3261E')
COPPER_F = HexColor('#C73333'); COPPER_B = HexColor('#4D7CC4'); SILK = HexColor('#F2EDA1')
MARGIN = 64.0
NAV = ['Tổng quan', 'Vận hành', 'Phần cứng', 'Tham khảo']
NAVX = [100, 322, 544, 766]


class Doc:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=(W, H))
        self.c.setTitle('NovaSight - Hồ sơ thiết kế PCB (NS-CHEST-MB, NS-CLIP-MB)')
        self.c.setAuthor('Dự án NovaSight')
        self.page = 0
        self.overlays = []   # (page_index, rect(x0,y0,x1,y1 in pdf pts bottom-left), src, clip_frac)
        self.sec = 0

    # ---- page chrome
    def new(self, sec=None):
        if self.page:
            self.c.showPage()
        self.page += 1
        if sec is not None:
            self.sec = sec
        return self.c

    def footer(self, dark=False):
        c = self.c
        col = HexColor('#FFFFFF') if dark else GRAY
        for i, (n, x) in enumerate(zip(NAV, NAVX)):
            act = i == self.sec
            c.setFont('ArB' if act else 'Ar', 14)
            c.setFillColor(HexColor('#FFFFFF') if dark else (RED if act else GRAY))
            c.drawCentredString(x + 36, H - 576, n)
        c.setFont('Ar', 14); c.setFillColor(col)
        c.drawRightString(W - 64, H - 576, str(self.page))

    def title(self, text, sub=None, size=30):
        c = self.c
        c.setFillColor(NAVY); c.setFont('ArB', size)
        c.drawString(MARGIN, H - 62, text)
        if sub:
            c.setFont('Ar', 16); c.setFillColor(GRAY)
            c.drawString(MARGIN, H - 92, sub)

    def std(self, title, sub=None, sec=None):
        self.new(sec)
        self.title(title, sub)
        self.footer()
        return self.c

    def divider(self, line1, line2, sub, tag='NovaChest / NS-CLIP-MB', sec=None):
        self.new(sec)
        c = self.c
        c.setFillColor(NAVY); c.rect(0, 0, W, H, stroke=0, fill=1)
        c.setFillColor(HexColor('#FFFFFF')); c.setFont('ArB', 48)
        c.drawString(64, H - 237, line1); c.drawString(64, H - 297, line2)
        c.setFont('Ar', 24); c.drawString(64, H - 372, sub)
        c.setFont('Ar', 18); c.drawString(64, H - 500, tag)
        self.footer(dark=True)

    # ---- text helpers
    def text(self, x, ytop, w, s, size=16, color=INK, font='Ar', lead=None):
        c = self.c
        lead = lead or size * 1.32
        c.setFont(font, size); c.setFillColor(color)
        y = ytop - size
        for para in s.split('\n'):
            lines = simpleSplit(para, font, size, w) or ['']
            for ln in lines:
                c.drawString(x, y, ln); y -= lead
        return y + lead - size * 0.0  # y position after last line baseline offset

    def bullets(self, x, ytop, w, items, size=16, gap=6, color=INK):
        y = ytop
        for it in items:
            self.c.setFillColor(RED); self.c.circle(x + 4, y - size * 0.62, 2.6, stroke=0, fill=1)
            yb = self.text(x + 16, y, w - 16, it, size, color)
            y = yb - gap
        return y

    def table(self, x, ytop, widths, rows, size=13, header=True, pad=6, lead=1.22, zebra=False, bold_first=False,
              colors=None, maxh=None, mono=()):
        """rows: list of lists of str. returns y bottom."""
        c = self.c
        y = ytop
        for ri, row in enumerate(rows):
            cells = []
            hmax = 0
            for ci, cell in enumerate(row):
                font = 'ArB' if (header and ri == 0) or (bold_first and ci == 0) else 'Ar'
                fs = size
                if ci in mono and not (header and ri == 0):
                    font = 'Mo'; fs = size * 0.9
                lines = []
                for para in str(cell).split('\n'):
                    lines += simpleSplit(para, font, fs, widths[ci] - 2 * pad) or ['']
                cells.append((font, lines, fs))
                hmax = max(hmax, len(lines))
            rh = hmax * size * lead + 2 * pad - 2
            if maxh and (ytop - (y - rh)) > maxh:
                break
            if header and ri == 0:
                c.setFillColor(HEAD); c.rect(x, y - rh, sum(widths), rh, stroke=0, fill=1)
            elif zebra and ri % 2 == 0:
                c.setFillColor(HexColor('#FAF6F6')); c.rect(x, y - rh, sum(widths), rh, stroke=0, fill=1)
            xx = x
            for ci, (font, lines, fs) in enumerate(cells):
                col = NAVY if (header and ri == 0) else INK
                if colors and (ri, ci) in colors:
                    col = colors[(ri, ci)]; font = 'MoB' if font == 'Mo' else 'ArB'
                c.setFont(font, fs); c.setFillColor(col)
                yy = y - pad - size * 0.88 + 1
                for ln in lines:
                    c.drawString(xx + pad, yy, ln); yy -= size * lead
                xx += widths[ci]
            c.setStrokeColor(LINE); c.setLineWidth(0.6)
            c.line(x, y - rh, x + sum(widths), y - rh)
            y -= rh
        # outer + vertical lines
        c.setStrokeColor(LINE); c.setLineWidth(0.6)
        c.rect(x, y, sum(widths), ytop - y, stroke=1, fill=0)
        xx = x
        for wcol in widths[:-1]:
            xx += wcol; c.line(xx, y, xx, ytop)
        return y

    def box(self, x, ytop, w, h, title, body=None, fill=HexColor('#FFFFFF'), stroke=LINE, tsize=14, bsize=11,
            tcolor=NAVY):
        c = self.c
        c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(0.9)
        c.rect(x, ytop - h, w, h, stroke=1, fill=1)
        c.setFillColor(tcolor); c.setFont('ArB', tsize)
        lines = simpleSplit(title, 'ArB', tsize, w - 12)
        y = ytop - 6 - tsize
        for ln in lines:
            c.drawCentredString(x + w / 2, y + 3, ln); y -= tsize * 1.15
        if body:
            c.setFont('Ar', bsize); c.setFillColor(GRAY)
            for ln in simpleSplit(body, 'Ar', bsize, w - 12):
                c.drawCentredString(x + w / 2, y, ln); y -= bsize * 1.25

    def arrow(self, x1, y1, x2, y2, col=GRAY):
        c = self.c
        c.setStrokeColor(col); c.setFillColor(col); c.setLineWidth(1.2)
        c.line(x1, y1, x2, y2)
        a = math.atan2(y2 - y1, x2 - x1)
        s = 6
        p = c.beginPath(); p.moveTo(x2, y2)
        p.lineTo(x2 - s * math.cos(a - 0.4), y2 - s * math.sin(a - 0.4))
        p.lineTo(x2 - s * math.cos(a + 0.4), y2 - s * math.sin(a + 0.4)); p.close()
        c.drawPath(p, stroke=0, fill=1)

    def chip(self, x, ytop, w, h, text, color=OK, size=12):
        c = self.c
        c.setFillColor(color); c.roundRect(x, ytop - h, w, h, 4, stroke=0, fill=1)
        c.setFillColor(HexColor('#FFFFFF')); c.setFont('ArB', size)
        c.drawCentredString(x + w / 2, ytop - h / 2 - size * 0.35, text)

    def overlay(self, rect_tl, src, clip_frac):
        """rect_tl = (x, ytop, w, h) in slide coords (y from bottom of page for ytop). clip_frac=(x0,y0,x1,y1) fraction of src page."""
        x, yt, w, h = rect_tl
        self.overlays.append((self.page - 1, (x, yt - h, x + w, yt), src, clip_frac))
        c = self.c
        c.setStrokeColor(LINE); c.setLineWidth(0.8); c.setFillColor(HexColor('#F7F6F1'))
        c.rect(x, yt - h, w, h, stroke=1, fill=1)

    def save(self):
        self.c.showPage(); self.c.save()


# ======================= PCB drawing =========================
def _chain_outline(pcb):
    segs = []
    for k, n in pcb.edge:
        if k == 'gr_line':
            a = kipcb.first(n, 'start'); b = kipcb.first(n, 'end')
            segs.append(((float(a[1]), float(a[2])), (float(b[1]), float(b[2]))))
    if not segs:
        x0, y0, x1, y1 = kipcb.board_bbox(pcb)
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    def key(p): return (round(p[0], 3), round(p[1], 3))
    pts = [segs[0][0], segs[0][1]]
    used = {0}
    changed = True
    while changed:
        changed = False
        for i, (a, b) in enumerate(segs):
            if i in used: continue
            if key(a) == key(pts[-1]):
                pts.append(b); used.add(i); changed = True
            elif key(b) == key(pts[-1]):
                pts.append(a); used.add(i); changed = True
    return pts


def draw_pcb(c, pcb, x, ytop, w, h, side='F', view=None, tracks=True, text_min=3.6, callouts=None, pad_color=None,
             frame=True, show_zones=True, mask_fill=None, ratsnest=None, labels=None, label_size=9):
    """Draw PCB into box (x, ytop-h .. ytop). Returns (scale, tf) where tf maps pcb mm -> pdf pts."""
    bx0, by0, bx1, by1 = kipcb.board_bbox(pcb)
    vx0, vy0, vx1, vy1 = view if view else (bx0 - 1.2, by0 - 1.2, bx1 + 1.2, by1 + 1.2)
    vw, vh = vx1 - vx0, vy1 - vy0
    s = min(w / vw, h / vh)
    ox = x + (w - vw * s) / 2
    oy = ytop - (h - vh * s) / 2
    mirror = side == 'B'

    def tf(px, py):
        u = (px - vx0) * s
        if mirror: u = (vw * s) - u
        return ox + u, oy - (py - vy0) * s
    cu = COPPER_B if mirror else COPPER_F
    layer = 'B.Cu' if mirror else 'F.Cu'
    silk_l = 'B.SilkS' if mirror else 'F.SilkS'
    pad_col = pad_color or HexColor('#F6F6F6')
    # frame
    if frame:
        c.setFillColor(HexColor('#FFFFFF')); c.setStrokeColor(LINE); c.setLineWidth(0.8)
        c.rect(ox - 4, oy - vh * s - 4, vw * s + 8, vh * s + 8, stroke=1, fill=1)
    c.saveState()
    clip = c.beginPath(); clip.rect(ox, oy - vh * s, vw * s, vh * s); c.clipPath(clip, stroke=0, fill=0)
    # board
    pts = _chain_outline(pcb)
    p = c.beginPath()
    X, Y = tf(*pts[0]); p.moveTo(X, Y)
    for q in pts[1:]:
        X, Y = tf(*q); p.lineTo(X, Y)
    p.close()
    c.setFillColor(mask_fill or cu); c.setStrokeColor(HexColor('#222222')); c.setLineWidth(max(0.6, 0.15 * s))
    c.drawPath(p, stroke=1, fill=1)
    # zones (filled) on this layer
    if show_zones:
        for z in pcb.zones:
            if z['keepout']: continue
            for fl, poly in z['fills']:
                if fl == layer and len(poly) > 2:
                    q = c.beginPath(); X, Y = tf(*poly[0]); q.moveTo(X, Y)
                    for pt in poly[1:]:
                        X, Y = tf(*pt); q.lineTo(X, Y)
                    q.close()
                    c.setFillColor(HexColor('#D24848') if not mirror else HexColor('#6590CE'))
                    c.setStrokeColor(pad_col); c.setLineWidth(0.3)
                    c.drawPath(q, stroke=0, fill=1)
    # keepout outline (antenna) as dashed
    for z in pcb.zones:
        if z['keepout'] and layer in z['layers'] and len(z['pts']) > 2 and len(z['layers']) >= 2:
            q = c.beginPath(); X, Y = tf(*z['pts'][0]); q.moveTo(X, Y)
            for pt in z['pts'][1:]:
                X, Y = tf(*pt); q.lineTo(X, Y)
            q.close()
            c.setStrokeColor(HexColor('#FFD27A')); c.setLineWidth(0.6); c.setDash(3, 2)
            c.drawPath(q, stroke=1, fill=0); c.setDash()
    # tracks
    if tracks:
        c.setStrokeColor(pad_col); c.setLineCap(1)
        for sg in pcb.segs:
            if sg['layer'] != layer: continue
            c.setLineWidth(max(0.4, sg['w'] * s))
            X1, Y1 = tf(sg['x1'], sg['y1']); X2, Y2 = tf(sg['x2'], sg['y2'])
            c.line(X1, Y1, X2, Y2)
        c.setLineCap(0)
    # vias
    for v in pcb.vias:
        X, Y = tf(v['x'], v['y'])
        c.setFillColor(pad_col); c.circle(X, Y, max(0.8, v['size'] * s / 2), stroke=0, fill=1)
        c.setFillColor(cu); c.circle(X, Y, max(0.4, v['drill'] * s / 2), stroke=0, fill=1)
    # pads
    lyr_ok = (layer, '*.Cu')
    for fp in pcb.fps:
        for pd in fp['pads']:
            on = any(l in lyr_ok for l in pd['layers'])
            if not on and pd['type'] != 'np_thru_hole': continue
            X, Y = tf(*kipcb.pad_world(fp, pd))
            ang = pd['rot']
            if pd['type'] == 'np_thru_hole':
                d = pd['drill'] or pd['w']
                c.setFillColor(HexColor('#111111')); c.circle(X, Y, d * s / 2, stroke=0, fill=1)
                continue
            c.saveState(); c.translate(X, Y); c.rotate(-ang if mirror else ang)
            pw, ph = pd['w'] * s, pd['h'] * s
            c.setFillColor(pad_col)
            sh = pd['shape']
            if sh == 'circle':
                c.circle(0, 0, pw / 2, stroke=0, fill=1)
            elif sh == 'oval':
                r = min(pw, ph) / 2
                c.roundRect(-pw / 2, -ph / 2, pw, ph, r, stroke=0, fill=1)
            elif sh == 'roundrect':
                c.roundRect(-pw / 2, -ph / 2, pw, ph, min(pw, ph) * pd['rratio'], stroke=0, fill=1)
            else:
                c.rect(-pw / 2, -ph / 2, pw, ph, stroke=0, fill=1)
            if pd['drill'] and pd['type'] == 'thru_hole':
                c.setFillColor(HexColor('#2A2A2A') if pd['drill'] > 0.5 else cu)
                c.circle(0, 0, pd['drill'] * s / 2, stroke=0, fill=1)
            c.restoreState()
    # silk
    c.setStrokeColor(SILK); c.setFillColor(SILK); c.setLineCap(1)
    for fp in pcb.fps:
        on_side = (fp['layer'] == layer)
        for kind, data, wd, ly in kipcb.fp_graphics(fp, (silk_l,)):
            c.setLineWidth(max(0.3, wd * s))
            if kind == 'line' or kind == 'poly':
                q = c.beginPath(); X, Y = tf(*data[0]); q.moveTo(X, Y)
                for pt in data[1:]:
                    X, Y = tf(*pt); q.lineTo(X, Y)
                c.drawPath(q, stroke=1, fill=0)
            elif kind == 'circle':
                X, Y = tf(data[0], data[1]); c.circle(X, Y, data[2] * s, stroke=1, fill=0)
            elif kind == 'arc3':
                q = c.beginPath(); X, Y = tf(*data[0]); q.moveTo(X, Y)
                for pt in data[1:]:
                    X, Y = tf(*pt); q.lineTo(X, Y)
                c.drawPath(q, stroke=1, fill=0)
        # ref text
        node = fp['node']
        for pr in kipcb.find(node, 'property'):
            if pr[1] != 'Reference': continue
            ly = kipcb.first(pr, 'layer')
            if not ly or ly[1] != silk_l: continue
            if any(isinstance(t, list) and t and t[0] == 'hide' and t[1] == 'yes' for t in pr): continue
            at = kipcb.first(pr, 'at')
            ef = kipcb.first(pr, 'effects'); fs = kipcb.first(ef, 'font'); sz = float(kipcb.first(fs, 'size')[1])
            tx, ty = kipcb.xf(float(at[1]), float(at[2]), 0, fp['x'], fp['y'], fp['rot'])
            ps = min(sz, 1.0) * s * 1.0
            if ps >= text_min:
                X, Y = tf(tx, ty)
                c.setFont('Ar', ps); c.drawCentredString(X, Y - ps * 0.33, fp['ref'])
    c.setLineCap(0)
    # board text
    for t in pcb.texts:
        if t['layer'] == silk_l:
            X, Y = tf(t['x'], t['y']); c.setFont('ArB', max(5, 1.2 * s)); c.drawCentredString(X, Y, t['text'])
    # ratsnest (unconnected pairs from DRC)
    if ratsnest:
        c.setStrokeColor(HexColor('#FFE08A')); c.setLineWidth(0.55); c.setDash(2.2, 1.6)
        for (a, b) in ratsnest:
            X1, Y1 = tf(*a); X2, Y2 = tf(*b)
            c.line(X1, Y1, X2, Y2)
        c.setDash()
    # component labels
    if labels:
        fpd = {f['ref']: f for f in pcb.fps}
        for ref in labels:
            f = fpd.get(ref)
            if not f: continue
            wp = [kipcb.pad_world(f, q) for q in f['pads']] or [(f['x'], f['y'])]
            cx = sum(p[0] for p in wp) / len(wp); cy = sum(p[1] for p in wp) / len(wp)
            X, Y = tf(cx, cy)
            tw = pdfmetrics.stringWidth(ref, 'ArB', label_size) + 6
            c.setFillColor(HexColor('#FFFFFF')); c.setStrokeColor(RED); c.setLineWidth(0.8)
            c.roundRect(X - tw / 2, Y - label_size / 2 - 2, tw, label_size + 4, 2, stroke=1, fill=1)
            c.setFillColor(RED); c.setFont('ArB', label_size)
            c.drawCentredString(X, Y - label_size * 0.33, ref)
    # outline again on top
    c.setStrokeColor(HexColor('#222222')); c.setLineWidth(max(0.6, 0.12 * s)); c.setFillColor(HexColor('#000000'))
    c.drawPath(p, stroke=1, fill=0)
    c.restoreState()
    # callouts
    if callouts:
        for num, (px, py) in callouts:
            X, Y = tf(px, py)
            c.setFillColor(RED); c.rect(X - 11, Y - 11, 22, 22, stroke=0, fill=1)
            c.setFillColor(HexColor('#FFFFFF')); c.setFont('ArB', 14); c.drawCentredString(X, Y - 5, str(num))
    return s, tf


def centroid(pcb, refs):
    xs = []; ys = []
    for fp in pcb.fps:
        if fp['ref'] in refs:
            xs.append(fp['x']); ys.append(fp['y'])
    return (sum(xs) / len(xs), sum(ys) / len(ys)) if xs else (0, 0)

