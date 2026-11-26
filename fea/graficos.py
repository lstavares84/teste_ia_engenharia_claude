# -*- coding: utf-8 -*-
"""Gráficos em PNG com PIL (mapas de cor de campos de placa e gráficos de linhas)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def fonte(t):
    for f in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, t)
        except Exception:
            pass
    return ImageFont.load_default()


def cmap(v):
    """Mapa de cores sequencial/divergente simples (azul → branco → vermelho) para v em [−1, 1]."""
    v = float(np.clip(v, -1, 1))
    if v < 0:
        a = -v
        return (int(255 - 200 * a), int(255 - 140 * a), 255)
    return (255, int(255 - 175 * v), int(255 - 205 * v))


def cmap_seq(v):
    """Sequencial (amarelo claro → azul escuro) para v em [0, 1]."""
    v = float(np.clip(v, 0, 1))
    c0, c1, c2 = np.array([255, 247, 188]), np.array([65, 182, 196]), np.array([8, 48, 107])
    c = c0 + (c1 - c0) * (v / 0.5) if v < 0.5 else c1 + (c2 - c1) * ((v - 0.5) / 0.5)
    return tuple(int(x) for x in c)


def campo(xs, ys, val, titulo, unidade, arq, sub="", divergente=False, marcadores=(), contornos=(), W=1400, H=900):
    """val: matriz (ny-1, nx-1) por elemento."""
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    mx, my, mw, mh = 90, 150, W - 330, H - 220
    sx = mw / (xs[-1] - xs[0])
    sy = mh / (ys[-1] - ys[0])
    s = min(sx, sy)
    ox, oy = mx, my + (ys[-1] - ys[0]) * s
    vmin, vmax = float(np.min(val)), float(np.max(val))
    vabs = max(abs(vmin), abs(vmax)) or 1.0
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            v = val[j, i]
            c = cmap(v / vabs) if divergente else cmap_seq((v - vmin) / ((vmax - vmin) or 1))
            d.rectangle([ox + (xs[i] - xs[0]) * s, oy - (ys[j + 1] - ys[0]) * s, ox + (xs[i + 1] - xs[0]) * s, oy - (ys[j] - ys[0]) * s], fill=c)
    d.rectangle([ox, oy - (ys[-1] - ys[0]) * s, ox + (xs[-1] - xs[0]) * s, oy], outline=(40, 40, 40), width=2)
    for (x0, y0, x1, y1, txt) in contornos:
        d.rectangle([ox + (x0 - xs[0]) * s, oy - (y1 - ys[0]) * s, ox + (x1 - xs[0]) * s, oy - (y0 - ys[0]) * s], outline=(30, 30, 30), width=2)
        if txt:
            d.text((ox + (x0 - xs[0]) * s + 3, oy - (y1 - ys[0]) * s + 2), txt, fill=(20, 20, 20), font=fonte(14))
    for (x, y, txt) in marcadores:
        px, py = ox + (x - xs[0]) * s, oy - (y - ys[0]) * s
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(0, 0, 0))
        d.text((px + 6, py - 18), txt, fill=(0, 0, 0), font=fonte(15))
    d.text((40, 28), titulo, fill="black", font=fonte(28))
    if sub:
        d.text((40, 70), sub, fill=(70, 70, 70), font=fonte(18))
    # escala de cores
    cx, cy, ch = W - 200, my, mh
    for k in range(200):
        t = k / 199
        v = (1 - 2 * t) if divergente else (1 - t)
        c = cmap(v) if divergente else cmap_seq(v)
        d.rectangle([cx, cy + t * ch, cx + 30, cy + (t + 0.006) * ch], fill=c)
    if divergente:
        lab = [(cy, f"{vabs:+.2f}"), (cy + ch / 2, "0"), (cy + ch, f"{-vabs:+.2f}")]
    else:
        lab = [(cy, f"{vmax:.2f}"), (cy + ch / 2, f"{(vmax+vmin)/2:.2f}"), (cy + ch, f"{vmin:.2f}")]
    for yy, t in lab:
        d.text((cx + 40, yy - 10), t, fill="black", font=fonte(16))
    d.text((cx - 10, cy - 30), unidade, fill="black", font=fonte(16))
    d.text((mx, H - 50), f"x (m) 0 – {xs[-1]-xs[0]:.2f}   |   y (m) 0 – {ys[-1]-ys[0]:.2f}   |   mín {vmin:.3f}  máx {vmax:.3f} {unidade}",
           fill=(70, 70, 70), font=fonte(16))
    img.save(arq)


def linhas(series, titulo, xlabel, ylabel, arq, sub="", hlines=(), W=1400, H=820, ylim=None):
    """series: lista de (x, y, cor, rótulo, espessura)."""
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    mx, my, mw, mh = 110, 130, W - 420, H - 220
    xs = np.concatenate([np.asarray(s[0]) for s in series])
    ys = np.concatenate([np.asarray(s[1]) for s in series] + [np.array([h[0] for h in hlines])] if hlines else [np.asarray(s[1]) for s in series])
    x0, x1 = float(xs.min()), float(xs.max())
    y0, y1 = (float(ys.min()), float(ys.max())) if ylim is None else ylim
    pad = 0.05 * (y1 - y0 or 1)
    y0, y1 = y0 - pad, y1 + pad

    def P(x, y):
        return mx + (x - x0) / ((x1 - x0) or 1) * mw, my + mh - (y - y0) / ((y1 - y0) or 1) * mh
    for k in range(6):
        yy = y0 + (y1 - y0) * k / 5
        d.line([P(x0, yy), P(x1, yy)], fill=(230, 230, 230))
        d.text((mx - 80, P(x0, yy)[1] - 9), f"{yy:.1f}", fill=(80, 80, 80), font=fonte(15))
        xx = x0 + (x1 - x0) * k / 5
        d.line([P(xx, y0), P(xx, y1)], fill=(240, 240, 240))
        d.text((P(xx, y0)[0] - 15, my + mh + 8), f"{xx:.1f}", fill=(80, 80, 80), font=fonte(15))
    d.rectangle([mx, my, mx + mw, my + mh], outline=(60, 60, 60))
    for (yv, cor, rot) in hlines:
        d.line([P(x0, yv), P(x1, yv)], fill=cor, width=2)
        d.text((P(x1, yv)[0] + 8, P(x1, yv)[1] - 9), rot, fill=cor, font=fonte(15))
    leg_y = my
    for (x, y, cor, rot, wd) in series:
        pts = [P(a, b) for a, b in zip(x, y)]
        d.line(pts, fill=cor, width=wd)
        d.rectangle([mx + mw + 20, leg_y + 200, mx + mw + 45, leg_y + 210], fill=cor)
        d.text((mx + mw + 52, leg_y + 196), rot, fill=(20, 20, 20), font=fonte(15))
        leg_y += 26
    d.text((40, 28), titulo, fill="black", font=fonte(28))
    if sub:
        d.text((40, 70), sub, fill=(70, 70, 70), font=fonte(18))
    d.text((mx + mw / 2 - 80, my + mh + 36), xlabel, fill="black", font=fonte(17))
    d.text((20, my - 30), ylabel, fill="black", font=fonte(17))
    img.save(arq)
