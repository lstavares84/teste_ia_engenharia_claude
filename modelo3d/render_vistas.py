# -*- coding: utf-8 -*-
"""Renderiza vistas 3D em PNG a partir de componentes.py (rasterizador próprio numpy + Pillow).

Projeção ortográfica, z-buffer, sombreamento de Lambert, transparência ordenada e realce de
arestas por descontinuidade de profundidade/normal. Supersampling 2× para antisserrilhado.
Uso: python modelo3d/render_vistas.py  ->  modelo3d/vistas/*.png
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import componentes as C  # noqa: E402
from gerar_modelo import tesselar  # noqa: E402

OUT = os.path.join(AQUI, "vistas")
os.makedirs(OUT, exist_ok=True)
SS = 2


def fonte(t, bold=False):
    for f in (("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"), "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, t)
        except Exception:
            pass
    return ImageFont.load_default()


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def preparar(comps, ocultar=(), cats_ocultas=(), modo="cat", mostrar_zonas=False, alpha_caixa=0.45):
    tris, cores, alfas, ids = [], [], [], []
    for k, c in enumerate(comps):
        if c["tag"] in ocultar or c["cat"] in cats_ocultas:
            continue
        if c["zona"] and not mostrar_zonas:
            continue
        V, F = tesselar(c)
        V = np.array(V)
        T = V[np.array(F)]
        cor = hex2rgb(C.CATEGORIAS[c["cat"]][1] if modo == "cat" else C.STATUS_COR[c["status"]])
        a = 1.0
        if c["zona"]:
            a = 0.25
        elif c["cat"] == "rio":
            a = 0.45
        elif c["tag"] == "TQ-101":
            a = alpha_caixa
        tris.append(T)
        cores.append(np.repeat(cor[None, :], len(T), 0))
        alfas.append(np.full(len(T), a))
        ids.append(np.full(len(T), k))
    return np.concatenate(tris), np.concatenate(cores), np.concatenate(alfas), np.concatenate(ids)


def render(tris, cores, alfas, ids, direcao, alvo, largura_m, W=1600, H=1000, fundo=(246, 248, 250), up=(0, 0, 1)):
    d = np.asarray(direcao, float)
    d /= np.linalg.norm(d)
    r = np.cross(d, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, d)
    Ws, Hs = W * SS, H * SS
    esc = Ws / largura_m
    alvo = np.asarray(alvo, float)
    P = tris - alvo
    sx = (P @ r) * esc + Ws / 2
    sy = -(P @ u) * esc + Hs / 2
    dep = P @ d
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    nn = np.linalg.norm(n, axis=1)
    ok = nn > 1e-12
    n[ok] /= nn[ok, None]
    n[np.einsum("ij,j->i", n, d) > 0] *= -1
    luz1 = -d * 0.55 + u * 0.6 + r * 0.25
    luz1 /= np.linalg.norm(luz1)
    luz2 = np.array([0.2, -0.4, 0.9])
    luz2 /= np.linalg.norm(luz2)
    I = 0.42 + 0.45 * np.clip(n @ luz1, 0, 1) + 0.18 * np.clip(n @ luz2, 0, 1)
    col = np.clip(cores * I[:, None], 0, 255)
    img = np.ones((Hs, Ws, 3)) * np.array(fundo, float)
    zb = np.full((Hs, Ws), np.inf)
    idb = np.full((Hs, Ws), -1, int)
    nb = np.zeros((Hs, Ws, 3))

    def rasteriza(k, blend):
        x, y, z = sx[k], sy[k], dep[k]
        x0, x1 = int(max(0, math.floor(x.min()))), int(min(Ws - 1, math.ceil(x.max())))
        y0, y1 = int(max(0, math.floor(y.min()))), int(min(Hs - 1, math.ceil(y.max())))
        if x1 < x0 or y1 < y0:
            return
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-12:
            return
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        l0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        l1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        l2 = 1 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not m.any():
            return
        zz = l0 * z[0] + l1 * z[1] + l2 * z[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        vis = m & (zz < sub - 1e-5)
        if not vis.any():
            return
        if blend:
            a = alfas[k]
            reg = img[y0:y1 + 1, x0:x1 + 1]
            reg[vis] = reg[vis] * (1 - a) + col[k] * a
        else:
            sub[vis] = zz[vis]
            img[y0:y1 + 1, x0:x1 + 1][vis] = col[k]
            idb[y0:y1 + 1, x0:x1 + 1][vis] = ids[k]
            nb[y0:y1 + 1, x0:x1 + 1][vis] = n[k]

    opacos = np.where(alfas >= 0.999)[0]
    for k in opacos:
        rasteriza(k, False)
    # arestas: descontinuidade de id/normal/profundidade
    zf = np.where(np.isfinite(zb), zb, 1e9)
    e = np.zeros((Hs, Ws), bool)
    for ax in (0, 1):
        dz = np.abs(np.diff(zf, axis=ax))
        did = np.diff(idb, axis=ax) != 0
        dn = np.linalg.norm(np.diff(nb, axis=ax), axis=2) > 0.35
        lim = 0.08 + 4.0 / esc   # tolerância cresce com o tamanho do pixel (planos inclinados em vistas amplas)
        ed = did | dn | (dz > lim)
        if ax == 0:
            e[1:, :] |= ed
        else:
            e[:, 1:] |= ed
    img[e] *= 0.45
    transp = np.where(alfas < 0.999)[0]
    ordem = transp[np.argsort(-dep[transp].mean(axis=1))]
    for k in ordem:
        rasteriza(k, True)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    proj = lambda p: (((np.asarray(p) - alvo) @ r) * esc / SS + W / 2, -((np.asarray(p) - alvo) @ u) * esc / SS + H / 2)
    return im, proj


def anotar(im, proj, titulo, sub, rotulos, legenda="cat", nota=""):
    d = ImageDraw.Draw(im)
    W, H = im.size
    d.rectangle([0, 0, W, 92], fill=(255, 255, 255))
    d.text((28, 14), titulo, fill=(20, 28, 36), font=fonte(30, True))
    d.text((28, 56), sub, fill=(80, 90, 100), font=fonte(19))
    for (p, txt, dx, dy) in rotulos:
        x, y = proj(p)
        tx, ty = x + dx, y + dy
        d.line([(x, y), (tx, ty)], fill=(40, 40, 40), width=2)
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(40, 40, 40))
        f = fonte(18)
        bb = d.textbbox((0, 0), txt, font=f)
        wbox = bb[2] - bb[0]
        bx = tx if dx >= 0 else tx - wbox - 12
        d.rectangle([bx, ty - 13, bx + wbox + 12, ty + 14], fill=(255, 255, 255), outline=(60, 60, 60))
        d.text((bx + 6, ty - 12), txt, fill=(20, 20, 20), font=f)
    if legenda:
        itens = ([(C.STATUS_COR[k], n) for k, n in [("CONF", "CONF — dado do cliente"), ("HIP", "HIP — hipótese do estudo"), ("PEND", "PEND — fornecedor/campo")]]
                 if legenda == "status" else [(v[1], v[0]) for k, v in C.CATEGORIAS.items() if k not in ("terreno", "rio", "zonas")])
        y = H - 24 - 24 * len(itens)
        d.rectangle([W - 330, y - 12, W - 12, H - 12], fill=(255, 255, 255), outline=(200, 205, 210))
        for cor, nome in itens:
            d.rectangle([W - 318, y + 2, W - 300, y + 18], fill=tuple(hex2rgb(cor).astype(int)))
            d.text((W - 292, y - 1), nome, fill=(30, 30, 30), font=fonte(16))
            y += 24
    d.text((28, H - 34), nota or "Estudo preliminar — modelo esquemático gerado por script; não válido para construção.", fill=(110, 110, 110), font=fonte(16))
    return im


def main():
    comps = C.construir()
    XC = C.X_CAIXA
    vistas = []
    terreno_area = ()
    # 01 conjunto
    T = preparar(comps)
    im, pj = render(*T, direcao=(1, 1.6, -0.95), alvo=(105, 0, 108), largura_m=270, W=1800, H=1000)
    anotar(im, pj, "V-01 · Implantação geral (isométrica)", "Rio (X = 0) → caixa (X = 79,6) → casa (X = 220); terreno = perfil hipotético entre as cotas informadas",
           [((0, 0, 97.5), "Captação P-101", 40, -90), ((XC, 0, 118), "Caixa 50 m³ + estrutura", -20, -110), ((226, 0, 124), "Casa (122,50)", -60, -90),
            ((150, -0.8, 115.7), "TB-202 não potável", 40, 70), ((45, -3.6, 107), "TB-101 recalque", -40, 80)])
    im.save(os.path.join(OUT, "V01_implantacao_geral.png"))
    # 02 área da caixa NE→SW
    T = preparar(comps, ocultar=("TER-01",))
    im, pj = render(*T, direcao=(-1, -1.15, -0.75), alvo=(82.2, 0, 114.6), largura_m=17)
    anotar(im, pj, "V-02 · Área da caixa — vista nordeste", "Caixa (transparente), estrutura metálica, plataforma, patamar e escada marinheiro, abrigo de equipamentos",
           [((XC, 0, 118), "TQ-101 caixa 50 m³", 120, 30), ((83.40, 0.9, 116), "EM-01 escada c/ gaiola", 90, -40), ((82.4, 2.2, 113.5), "PL-01 plataforma 113,50", 120, 40),
            ((86.1, -0.2, 114.65), "Abrigo (booster, QCB, cloro)", -60, 120), ((82.78, 1.8, 116.5), "Prumada P-101 → N1", 140, -100),
            ((83.7, -1.5, 115), "EX-401 extravasor", -120, -60)])
    im.save(os.path.join(OUT, "V02_area_caixa_NE.png"))
    # 03 sudoeste
    im, pj = render(*T, direcao=(1, 1.1, -0.7), alvo=(81.5, 0, 114.4), largura_m=17)
    anotar(im, pj, "V-03 · Área da caixa — vista sudoeste", "Pilares W150×29,8, contraventamento Ø16, radier, escada 42° da plataforma",
           [((77.4, -2.2, 112.6), "PIL + CTV", -60, 70), ((XC, -2.7, 112.0), "RAD-01 radier", -80, 90), ((82.4, -3.0, 112.8), "ES-01 escada 42°", 80, 80)])
    im.save(os.path.join(OUT, "V03_area_caixa_SW.png"))
    # 04 estrutura sem caixa
    T = preparar(comps, ocultar=("TER-01", "TQ-101", "N1", "N2", "N3", "N4", "BV", "LT-101", "PT-01", "PST-PT", "EM-01", "TB-102", "EX-401", "SP-401",
                                 "ABR-T", "ABR-N", "ABR-L", "ABR-O", "ABR-S", "ABR-PISO", "SK-201", "QCB-01", "CL-101", "F-101", "FQ-101", "QE-EX", "EL-102"))
    im, pj = render(*T, direcao=(-0.9, 1.25, -0.85), alvo=(80.3, 0, 112.9), largura_m=9.5)
    anotar(im, pj, "V-04 · Estrutura metálica sem a caixa", "Chapa 9,5 mm sobre 11 secundárias W150×13,0, 3 principais W200×31,3, 9 pilares, contraventamento em X, 8 olhais de ancoragem",
           [((79.6, 0, 113.5), "CH-01 chapa (apoio integral)", -40, -110), ((80.79, 1.25, 113.65), "ANC olhal", 60, -70)])
    im.save(os.path.join(OUT, "V04_estrutura_sem_caixa.png"))
    # 05 abrigo aberto
    T = preparar(comps, ocultar=("TER-01", "ABR-T", "ABR-S"), )
    im, pj = render(*T, direcao=(-0.35, 1.0, -0.9), alvo=(86.0, -0.3, 112.7), largura_m=5.2)
    anotar(im, pj, "V-05 · Abrigo de equipamentos (cobertura e parede sul ocultas)", "Booster duplex P-201A/B + vaso, filtro F-101, hidrômetro, QCB-01, compartimento de cloração separado",
           [((85.35, -0.8, 112.45), "P-201A", -60, 70), ((85.95, -0.8, 112.45), "P-201B", 40, 90), ((85.2, 0.5, 112.8), "F-101 filtro", -80, -60),
            ((86.3, 0.78, 113.6), "QCB-01", 60, -60), ((87.15, -0.9, 112.85), "CL-101 cloração", 70, 40), ((86.15, -0.55, 112.55), "PV-201", 60, -20)])
    im.save(os.path.join(OUT, "V05_abrigo_equipamentos.png"))
    # 06 captação
    T = preparar(comps, ocultar=("RIO-MAX", "RIO-MIN"))
    im, pj = render(*T, direcao=(0.3, 1.0, -0.32), alvo=(3.5, 0, 100.0), largura_m=24)
    anotar(im, pj, "V-06 · Captação no rio", "Tubo-camisa DE200 inclinado no talude 1:1,5 (hipótese), bomba submersa, bloco de apoio, caixa de válvulas acima da cheia",
           [((9.45, 0, 103.8), "TC-101 crista 103,80", 60, -80), ((11, 1, 103.6), "CX-101 válvulas", 80, -20), ((-0.9, 0, 97.0), "P-101 (interna)", -60, 80),
            ((-2.25, 0, 95.8), "BL-101", -90, 30), ((-9, -4, 100), "Nível normal 100,00", 40, -120)])
    im.save(os.path.join(OUT, "V06_captacao.png"))
    # 07 planta
    T = preparar(comps, ocultar=("TER-01", "ABR-T"))
    im, pj = render(*T, direcao=(0, 0.0001, -1), alvo=(82.2, 0, 112), largura_m=15, up=(0, 1, 0))
    anotar(im, pj, "V-07 · Planta da área da caixa (vista superior)", "Área informada 8 × 8 m (X 76–84) + ampliação proposta 4,5 × 8 m; abrigo sem cobertura",
           [((76.0, 4.0, 112), "Limite 8 × 8 m", 30, -40), ((88.5, 4.0, 112), "Ampliação", -10, -40)], nota="Norte para cima. Escala gráfica: largura da imagem = 15 m.")
    im.save(os.path.join(OUT, "V07_planta_area.png"))
    # 08 elevação sul
    T = preparar(comps, ocultar=("TER-01",))
    im, pj = render(*T, direcao=(0, 1, 0.0001), alvo=(82.2, 0, 115.2), largura_m=14, H=900)
    anotar(im, pj, "V-08 · Elevação sul", "Base da caixa 113,50 (1,50 m acima do terreno); topo 118,00; patamar 118,10; escada marinheiro até 119,20",
           [((77.6, 0, 118.0), "118,00", -60, -30), ((77.4, 0, 113.5), "113,50", -70, 0), ((77.0, 0, 112.0), "112,00", -70, 30)], nota="Vista ortogonal; caixa transparente.")
    im.save(os.path.join(OUT, "V08_elevacao_sul.png"))
    # 09 status
    T = preparar(comps, ocultar=("TER-01",), modo="status")
    im, pj = render(*T, direcao=(-1, -1.15, -0.75), alvo=(82.2, 0, 114.6), largura_m=17)
    anotar(im, pj, "V-09 · Status do dado de cada componente", "Vermelho = depende de fornecedor/levantamento; amarelo = hipótese do estudo; verde = dado do cliente",
           [], legenda="status")
    im.save(os.path.join(OUT, "V09_status_dados.png"))
    # 10 zonas
    T = preparar(comps, ocultar=("TER-01",), mostrar_zonas=True, alpha_caixa=0.3)
    im, pj = render(*T, direcao=(-1, -0.9, -0.85), alvo=(82.5, 0, 115.2), largura_m=17)
    clashes = json.load(open(os.path.join(AQUI, "saida", "interferencias.json"), encoding="utf-8"))
    rot = [((k["ponto"][0], k["ponto"][1], k["ponto"][2]), f"{k['a']} × {k['b']}", 80 + 40 * i, -90 - 40 * i) for i, k in enumerate(clashes)]
    rot += [((82.4, 0, 114.5), "ZN-01 circulação", -150, 80), ((86.3, 0.2, 113), "ZN-02 frente QCB", 60, 60), ((XC, 0, 121), "ZN-04 içamento", -120, -60)]
    anotar(im, pj, "V-10 · Zonas livres e interferências de montagem", "Verde translúcido = espaços que devem ficar livres; rótulos = ocorrências remanescentes (sequência de montagem)", rot, legenda=None)
    im.save(os.path.join(OUT, "V10_zonas_interferencias.png"))
    print("vistas geradas:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
