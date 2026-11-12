"""Minimal KiCad .kicad_pcb reader (read-only) used to draw vector layouts."""
import re, math

def tokenize(s):
    return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', s)

def parse(s):
    toks = tokenize(s)
    pos = 0
    def rd():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == '(':
            lst = []
            while toks[pos] != ')':
                lst.append(rd())
            pos += 1
            return lst
        if t.startswith('"'):
            return t[1:-1].replace('\\"', '"')
        return t
    return rd()

def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def first(node, key, default=None):
    r = find(node, key)
    return r[0] if r else default

def num(x):
    return float(x)

def xf(px, py, ang, fx, fy, fang):
    """local (px,py) in footprint at (fx,fy,fang deg) -> board coords. KiCad: y down, rotation CCW-positive on screen."""
    a = math.radians(fang)
    # KiCad rotation is applied in y-down coordinates: x' = x cos a + y sin a ; y' = -x sin a + y cos a
    x = px * math.cos(a) + py * math.sin(a)
    y = -px * math.sin(a) + py * math.cos(a)
    return fx + x, fy + y

class PCB:
    pass

def load(path):
    t = open(path, encoding='utf8').read()
    root = parse(t)
    pcb = PCB()
    pcb.root = root
    pcb.title = (first(first(root, 'title_block') or [], 'title') or [None, ''])[1]
    pcb.layers_cu = [l[1] for l in find(first(root, 'layers'), 'layers')] if False else None
    # outline
    pcb.edge = []
    for k in ('gr_line', 'gr_arc', 'gr_rect', 'gr_circle', 'gr_poly'):
        for n in find(root, k):
            lay = first(n, 'layer')
            if lay and lay[1] == 'Edge.Cuts':
                pcb.edge.append((k, n))
    pcb.nets = {}
    for n in find(root, 'net'):
        if len(n) >= 3:
            pcb.nets[int(n[1])] = n[2]
    # footprints
    pcb.fps = []
    for fp in find(root, 'footprint'):
        d = {}
        d['lib'] = fp[1]
        d['layer'] = first(fp, 'layer')[1]
        at = first(fp, 'at')
        d['x'], d['y'] = num(at[1]), num(at[2])
        d['rot'] = num(at[3]) if len(at) > 3 else 0.0
        d['ref'] = ''; d['value'] = ''
        d['props'] = {}
        for p in find(fp, 'property'):
            if len(p) >= 3:
                d['props'][p[1]] = p[2]
        d['ref'] = d['props'].get('Reference', '')
        d['value'] = d['props'].get('Value', '')
        attr = first(fp, 'attr')
        d['attr'] = attr[1:] if attr else []
        d['node'] = fp
        d['pads'] = []
        for pd in find(fp, 'pad'):
            pp = {'num': pd[1], 'type': pd[2], 'shape': pd[3]}
            a = first(pd, 'at')
            pp['lx'], pp['ly'] = num(a[1]), num(a[2])
            pp['rot'] = num(a[3]) if len(a) > 3 else 0.0
            sz = first(pd, 'size')
            pp['w'], pp['h'] = num(sz[1]), num(sz[2])
            ly = first(pd, 'layers')
            pp['layers'] = ly[1:] if ly else []
            dr = first(pd, 'drill')
            pp['drill'] = None
            if dr:
                vals = [v for v in dr[1:] if not isinstance(v, list) and v != 'oval']
                if vals:
                    pp['drill'] = num(vals[0])
            net = first(pd, 'net')
            pp['net'] = net[1] if net and len(net) > 1 else ''
            rr = first(pd, 'roundrect_rratio')
            pp['rratio'] = num(rr[1]) if rr else 0.25
            poly = first(pd, 'primitives')
            pp['prims'] = poly
            d['pads'].append(pp)
        pcb.fps.append(d)
    pcb.segs = []
    for s in find(root, 'segment'):
        a = first(s, 'start'); b = first(s, 'end')
        pcb.segs.append(dict(x1=num(a[1]), y1=num(a[2]), x2=num(b[1]), y2=num(b[2]),
                             w=num(first(s, 'width')[1]), layer=first(s, 'layer')[1],
                             net=(first(s, 'net') or [0, 0])[1]))
    pcb.vias = []
    for s in find(root, 'via'):
        a = first(s, 'at')
        pcb.vias.append(dict(x=num(a[1]), y=num(a[2]), size=num(first(s, 'size')[1]),
                             drill=num(first(s, 'drill')[1]), net=(first(s, 'net') or [0, 0])[1]))
    pcb.zones = []
    for z in find(root, 'zone'):
        lay = first(z, 'layer') or first(z, 'layers')
        pts = []
        poly = first(z, 'polygon')
        if poly:
            pts = [(num(p[1]), num(p[2])) for p in find(first(poly, 'pts'), 'xy')]
        fills = []
        for fpol in find(z, 'filled_polygon'):
            fl = first(fpol, 'layer')
            fills.append((fl[1] if fl else None, [(num(p[1]), num(p[2])) for p in find(first(fpol, 'pts'), 'xy')]))
        keep = first(z, 'keepout')
        pcb.zones.append(dict(layers=lay[1:] if lay else [], net=first(z, 'net_name')[1] if first(z, 'net_name') else '',
                              pts=pts, fills=fills, keepout=bool(keep), name=(first(z, 'name') or [0, ''])[1]))
    pcb.texts = []
    for g in find(root, 'gr_text'):
        a = first(g, 'at'); l = first(g, 'layer')
        pcb.texts.append(dict(text=g[1], x=num(a[1]), y=num(a[2]), layer=l[1] if l else ''))
    return pcb

def board_bbox(pcb):
    xs = []; ys = []
    for k, n in pcb.edge:
        for key in ('start', 'end', 'mid', 'center'):
            for p in find(n, key):
                xs.append(num(p[1])); ys.append(num(p[2]))
    return min(xs), min(ys), max(xs), max(ys)

def pad_world(fp, pad):
    x, y = xf(pad['lx'], pad['ly'], 0, fp['x'], fp['y'], fp['rot'])
    return x, y

def fp_graphics(fp, layers):
    """Return list of primitives (kind, pts/data, width, layer) in board coords for fp_* items on given layers."""
    out = []
    for n in fp['node']:
        if not isinstance(n, list) or not n:
            continue
        k = n[0]
        if k not in ('fp_line', 'fp_rect', 'fp_circle', 'fp_arc', 'fp_poly'):
            continue
        ly = first(n, 'layer')
        if not ly or ly[1] not in layers:
            continue
        st = first(n, 'stroke')
        w = num(first(st, 'width')[1]) if st and first(st, 'width') else 0.12
        def W(px, py):
            return xf(px, py, 0, fp['x'], fp['y'], fp['rot'])
        if k == 'fp_line':
            a = first(n, 'start'); b = first(n, 'end')
            out.append(('line', [W(num(a[1]), num(a[2])), W(num(b[1]), num(b[2]))], w, ly[1]))
        elif k == 'fp_rect':
            a = first(n, 'start'); b = first(n, 'end')
            x1, y1, x2, y2 = num(a[1]), num(a[2]), num(b[1]), num(b[2])
            pts = [W(x1, y1), W(x2, y1), W(x2, y2), W(x1, y2), W(x1, y1)]
            out.append(('poly', pts, w, ly[1]))
        elif k == 'fp_circle':
            c = first(n, 'center'); e = first(n, 'end')
            cx, cy, ex, ey = num(c[1]), num(c[2]), num(e[1]), num(e[2])
            r = math.hypot(ex - cx, ey - cy)
            X, Y = W(cx, cy)
            out.append(('circle', (X, Y, r), w, ly[1]))
        elif k == 'fp_arc':
            a = first(n, 'start'); m = first(n, 'mid'); e = first(n, 'end')
            pts = [W(num(a[1]), num(a[2])), W(num(m[1]), num(m[2])), W(num(e[1]), num(e[2]))]
            out.append(('arc3', pts, w, ly[1]))
        elif k == 'fp_poly':
            pts = [W(num(p[1]), num(p[2])) for p in find(first(n, 'pts'), 'xy')]
            out.append(('poly', pts, w, ly[1]))
    return out
