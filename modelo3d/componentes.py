# -*- coding: utf-8 -*-
"""Definição paramétrica de todos os componentes do modelo 3D (fonte única para
FreeCAD, OBJ, GLB, visualizador web, desenhos e checagem de interferências).

Coordenadas reais do estudo, em metros: X ao longo do traçado (rio -> casa), Y transversal
(positivo = norte), Z = cota na referência fictícia do cliente.

status:  CONF = dado do cliente | HIP = hipótese/decisão do estudo | PEND = depende de fornecedor/levantamento
"""
import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calc"))
from premissas import *  # noqa

RES = json.load(open(os.path.join(AQUI, "..", "calc", "resultados", "resultados.json"), encoding="utf-8"))
EST = RES["MC-02_estrutura_fundacao"]

CATEGORIAS = {
    "terreno": ("Terreno (perfil hipotético)", "#8f9a7a"),
    "rio": ("Rio e níveis", "#3d7fb8"),
    "captacao": ("Captação", "#c77d2e"),
    "tub_p1": ("Recalque rio → caixa", "#2f9e8f"),
    "tub_casa": ("Linha caixa → casa (não potável)", "#8a4fbf"),
    "drenagem": ("Dreno e extravasor", "#6b7f96"),
    "estrutura": ("Estrutura metálica", "#5d6b7a"),
    "acesso": ("Acessos e guarda-corpos", "#d6a92b"),
    "fundacao": ("Fundação", "#a3a3a0"),
    "caixa": ("Caixa d'água 50 m³", "#cfd8e3"),
    "equip": ("Bombas, filtro, cloração", "#d1495b"),
    "civil": ("Abrigo e obras civis", "#b3aa9c"),
    "eletrica": ("Elétrica e automação", "#f08a24"),
    "casa": ("Casa / limite do projeto", "#b9a88f"),
    "zonas": ("Zonas livres (manutenção/operação)", "#22c55e"),
}
STATUS_COR = {"CONF": "#2b8a3e", "HIP": "#e8a317", "PEND": "#d6336c"}

COMPS = []


def add(tag, desc, cat, status, prims, pend="", permite=(), zona=False):
    COMPS.append(dict(tag=tag, desc=desc, cat=cat, status=status, prims=prims, pend=pend,
                      permite=list(permite), zona=zona))


def box(x0, y0, z0, x1, y1, z1):
    return dict(t="box", min=[min(x0, x1), min(y0, y1), min(z0, z1)], max=[max(x0, x1), max(y0, y1), max(z0, z1)])


def cyl(a, b, r, n=12):
    return dict(t="cyl", a=list(a), b=list(b), r=r, n=n)


def polyline(pts, r, n=10):
    return [cyl(pts[i], pts[i + 1], r, n) for i in range(len(pts) - 1)]


def z_terreno(x):
    P = PERFIL_TERRENO_MOD
    if x <= P[0][0]:
        return P[0][1]
    for (x0, z0), (x1, z1) in zip(P, P[1:]):
        if x0 <= x <= x1:
            return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return P[-1][1]


# perfil do terreno: hipótese do cliente + margem oposta (apenas ilustrativa) + platô ampliado até X=88,5 (proposta)
PERFIL_TERRENO_MOD = [(-16.0, 103.0), (-13.0, 101.0), (-10.0, 97.5), (-8.0, 95.5)] + \
    [p for p in PERFIL_TERRENO if p[0] < 84.0] + [(84.0, 112.0), (88.5, 112.0), (220.0, 120.0), (236.0, 120.0)]


def enterrada(x_ini, x_fim, y, prof, passo=8.0):
    """Pontos de uma tubulação enterrada acompanhando o terreno."""
    xs = [x_ini]
    x = x_ini
    sgn = 1 if x_fim > x_ini else -1
    while (x_fim - x) * sgn > passo:
        x += passo * sgn
        xs.append(x)
    xs.append(x_fim)
    # inclui pontos de quebra do perfil
    for xb, _ in PERFIL_TERRENO_MOD:
        if min(x_ini, x_fim) < xb < max(x_ini, x_fim):
            xs.append(xb)
    xs = sorted(set(xs), reverse=(sgn < 0))
    return [(xx, y, z_terreno(xx) - prof) for xx in xs]


def I_horizontal(eixo, x0, x1, c1, c2, z_topo, d, bf, tw, tf):
    """Perfil I horizontal. eixo='X' (c1 = Y do eixo) ou 'Y' (c1 = X do eixo)."""
    zb = z_topo - d
    if eixo == "X":
        return [box(x0, c1 - bf / 2, z_topo - tf, x1, c1 + bf / 2, z_topo),
                box(x0, c1 - bf / 2, zb, x1, c1 + bf / 2, zb + tf),
                box(x0, c1 - tw / 2, zb + tf, x1, c1 + tw / 2, z_topo - tf)]
    return [box(c1 - bf / 2, x0, z_topo - tf, c1 + bf / 2, x1, z_topo),
            box(c1 - bf / 2, x0, zb, c1 + bf / 2, x1, zb + tf),
            box(c1 - tw / 2, x0, zb + tf, c1 + tw / 2, x1, z_topo - tf)]


def I_vertical(x, y, z0, z1, d, bf, tw, tf):
    """Pilar I com alma paralela a X (mesas perpendiculares a X)."""
    return [box(x - d / 2, y - bf / 2, z0, x - d / 2 + tf, y + bf / 2, z1),
            box(x + d / 2 - tf, y - bf / 2, z0, x + d / 2, y + bf / 2, z1),
            box(x - d / 2 + tf, y - tw / 2, z0, x + d / 2 - tf, y + tw / 2, z1)]


def guarda_corpo(p0, p1, z, h=1.10, esp=1.2, r=0.0212):
    """Guarda-corpo: travessão superior, intermediário, rodapé e montantes."""
    prims = [cyl((p0[0], p0[1], z + h), (p1[0], p1[1], z + h), r, 8),
             cyl((p0[0], p0[1], z + h / 2), (p1[0], p1[1], z + h / 2), r * 0.8, 8)]
    L = math.dist(p0, p1)
    n = max(1, int(math.ceil(L / esp)))
    for i in range(n + 1):
        t = i / n
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        prims.append(cyl((x, y, z), (x, y, z + h), r, 8))
    return prims


def construir():
    COMPS.clear()
    # ------------------------------------------------------------------ terreno e rio
    ys = (-20.0, 20.0)
    v, fcs = [], []
    for i, (x, z) in enumerate(PERFIL_TERRENO_MOD):
        v += [[x, ys[0], z], [x, ys[1], z]]
        if i:
            a = 2 * (i - 1)
            fcs += [[a, a + 2, a + 3], [a, a + 3, a + 1]]
    add("TER-01", "Terreno — perfil HIPOTÉTICO (sem topografia); platô 112,00 ampliado até X = 88,5 (proposta)",
        "terreno", "HIP", [dict(t="mesh", v=v, f=fcs)], pend="Levantamento planialtimétrico e perfil dos trechos")
    for tag, nivel, desc, st in [("RIO-MIN", COTAS["rio_min"], "Nível mínimo de operação 97,50", "CONF"),
                                 ("RIO-NOR", COTAS["rio_normal"], "Nível normal 100,00", "CONF"),
                                 ("RIO-MAX", COTAS["rio_max"], "Nível máximo esperado 102,00 (cheia)", "CONF")]:
        # extensão da lâmina entre as margens (interpolação no perfil)
        xa = -13.0 + (nivel - 101.0) / (97.5 - 101.0) * 3.0 if nivel <= 101 else -13.0 - (nivel - 101.0) / 2.0 * 3.0
        xb = (nivel - 97.5) * 1.5
        add(tag, desc + " (largura do rio NÃO informada — margem oposta ilustrativa)", "rio", st,
            [box(xa, -20, nivel - 0.01, xb, 20, nivel)], pend="Batimetria e largura do rio (define faixa de APP)")

    # ------------------------------------------------------------------ captação
    C = CAPTACAO
    a = (-2.25, 0.0, C["z_extremidade_camisa"] + 0.10)
    b = (9.45, 0.0, C["z_crista_camisa"])
    add("TC-101", "Tubo-camisa PEAD DE200 inclinado, trecho final perfurado + tela inox; tampa na crista (103,80)",
        "captacao", "HIP", [cyl(a, b, 0.10, 16)], pend="Batimetria/leito ≤ 95,70 no ponto; estabilidade do talude",
        permite=["TER-01", "RIO-MIN", "RIO-NOR", "RIO-MAX", "P-101", "BL-101", "ZN-06"])
    ux, uz = (b[0] - a[0]), (b[2] - a[2])
    L = math.hypot(ux, uz)
    p0 = (a[0] + ux * 0.30 / L, 0, a[2] + uz * 0.30 / L)
    p1 = (a[0] + ux * 1.60 / L, 0, a[2] + uz * 1.60 / L)
    add("P-101", "Bomba submersa 4\" multiestágio + motor 380 V (Q = 3,0 m³/h; H ≥ 33 m) com patim e cabo de içamento inox",
        "captacao", "PEND", [cyl(p0, p1, 0.05, 12)], pend="Curva real do fabricante; submergência mínima; teor de areia admissível",
        permite=["TC-101", "RIO-MIN", "RIO-NOR", "RIO-MAX", "TER-01"])
    add("BL-101", "Bloco de apoio da extremidade do tubo-camisa (concreto/gabião) + enrocamento de proteção",
        "captacao", "HIP", [box(-2.8, -0.45, 95.55, -1.7, 0.45, 96.0)], permite=["TER-01", "RIO-MIN", "RIO-NOR", "RIO-MAX", "TC-101"],
        pend="Natureza do leito; erosão na cheia")
    zt11 = z_terreno(11.0)
    add("CX-101", "Caixa de válvulas na crista (V-101 registro, CV-102 retenção, PI-101 manômetro, união de desmontagem) — acima da cheia",
        "captacao", "HIP", [box(10.6, 0.6, zt11 - 0.6, 11.4, 1.4, zt11 + 0.25)], permite=["TER-01", "TB-101", "EL-101"])
    add("TB-101-M", "Mangueira/PEAD flexível de recalque dentro do tubo-camisa até a caixa de válvulas (desconectada para içar a bomba)",
        "tub_p1", "HIP", polyline([b, (9.9, 0.4, 103.7), (10.6, 1.0, zt11 - 0.3)], 0.02),
        permite=["TC-101", "CX-101", "ZN-06", "TER-01", "TB-101"])
    # zona de retirada da bomba (prolongamento do eixo do tubo-camisa)
    add("ZN-06", "Zona livre para içamento/retirada da bomba P-101 pelo eixo do tubo-camisa",
        "zonas", "HIP", [cyl(b, (b[0] + 1.8, 0, b[2] + 1.2), 0.30, 12)], zona=True, permite=["TER-01", "TC-101", "TB-101-M"])

    # ------------------------------------------------------------------ recalque rio -> caixa (enterrado)
    pts = [(10.6, 1.0, zt11 - 0.3), (12.0, 1.0, z_terreno(12.0) - 0.7), (12.0, -3.6, z_terreno(12.0) - 0.7)]
    pts += enterrada(12.0, 84.95, -3.6, 0.7)[1:]
    pts += [(84.95, -3.6, 111.6), (84.95, 0.3, 111.6), (84.95, 0.3, 112.6), (85.08, 0.3, 112.6)]
    add("TB-101", "Recalque PEAD PE100 DE40 SDR11 PN16 enterrado (0,7 m), eletrofusão — rio → abrigo",
        "tub_p1", "HIP", polyline(pts, 0.02), pend="Traçado, pontos altos (ventosas) e travessias conforme topografia",
        permite=["CX-101", "TER-01", "ABR-PISO", "F-101"])
    zf = (112.1, 112.8)
    add("F-101", "Filtro autolimpante (tela/disco ~130 µm [H]) com retrolavagem por ΔP, descarga para o dreno",
        "equip", "PEND", [cyl((85.2, 0.5, zf[0]), (85.2, 0.5, zf[1]), 0.12, 16)], pend="Curva de perda de carga, malha conforme análise de sólidos",
        permite=["TB-101", "TB-102", "ABR-PISO"])
    pts2 = [(85.32, 0.62, 112.6), (85.45, 0.7, 112.6), (85.65, 0.7, 112.6), (85.65, 1.15, 112.6), (85.65, 1.8, 112.3),
            (82.78, 1.8, 112.3), (82.78, 1.8, 118.35), (80.8, 1.8, 118.35), (80.8, 1.3, 118.35), (80.8, 1.3, 118.0)]
    add("TB-102", "Hidrômetro FQ-101 + injeção de cloro + prumada DE40 até a entrada N1 no teto (descarga livre 117,80)",
        "tub_p1", "HIP", polyline(pts2, 0.02),
        permite=["F-101", "FQ-101", "ABR-N", "PL-01", "TQ-101", "N1", "TER-01"],
        pend="Posição do bocal N1 e forma do teto (fornecedor)")
    add("FQ-101", "Hidrômetro com saída pulsada (registro de volume captado — exigência típica de outorga/cadastro)",
        "equip", "PEND", [box(85.45, 0.62, 112.52, 85.62, 0.78, 112.68)], permite=["TB-102"])

    # ------------------------------------------------------------------ fundação
    Lr, Br, hr = EST["radier"]
    xr0 = 76.9
    add("RAD-01", f"Radier C30 {Lr:.2f} × {Br:.2f} × {hr:.2f} m (pré-dimensionado SEM sondagem)", "fundacao", "PEND",
        [box(xr0, -Br / 2, 112.02 - hr, xr0 + Lr, Br / 2, 112.02)], pend="Sondagem SPT, colapsibilidade, NA",
        permite=["TER-01", "PED", "TB-101"])
    xs, ys_ = EST["xs_pil"], EST["ys_pil"]
    peds = []
    for x in xs + [82.9]:
        for y in ys_:
            peds.append(box(x - 0.25, y - 0.25, 112.02, x + 0.25, y + 0.25, 112.12))
    for y in (0.5, 1.3):
        peds.append(box(83.2 - 0.15, y - 0.15, 112.02, 83.2 + 0.15, y + 0.15, 112.12))
    add("PED", "Pedestais 50×50 cm + graute 30 mm + chumbadores 4×M20 F1554 Gr36", "fundacao", "HIP", peds,
        permite=["RAD-01", "PB", "PIL", "PST"])

    # ------------------------------------------------------------------ estrutura
    dj, bj = EST["d_joist"], EST["bf_joist"]
    dv, bv = EST["d_viga"], EST["bf_viga"]
    Pj = PERFIS_W[EST["perfil_joist"]]
    Pv = PERFIS_W[EST["perfil_viga"]]
    Pp = PERFIS_W[EST["perfil_pilar"]]
    t_ch = ESTR["chapa_piso_mm"] / 1000
    z_deck = TANQUE["cota_base"]
    z_topo_j = z_deck - t_ch
    z_topo_v = z_topo_j - dj
    z_base_v = z_topo_v - dv
    z_pb = ESTR["cota_topo_pedestal"] + ESTR["graute_mm"] / 1000
    z_pb_top = z_pb + ESTR["placa_base_mm"] / 1000
    pb = [box(x - 0.15, y - 0.15, z_pb, x + 0.15, y + 0.15, z_pb_top) for x in xs for y in ys_]
    pb += [box(82.9 - 0.15, y - 0.15, z_pb, 82.9 + 0.15, y + 0.15, z_pb_top) for y in ys_]
    add("PB", "Placas de base 300×300×22,4 A36", "estrutura", "HIP", pb, permite=["PED", "PIL", "PST"])
    pil = []
    for x in xs:
        for y in ys_:
            pil += I_vertical(x, y, z_pb_top, z_base_v, *[k / 1000 for k in Pp])
    add("PIL", f"Pilares {EST['perfil_pilar']} A572 Gr50 (9 un.)", "estrutura", "HIP", pil,
        permite=["PB", "VP", "CTV", "PED"])
    vp = []
    for y in ys_:
        vp += I_horizontal("X", xs[0] - 0.07, xs[-1] + 0.07, y, None, z_topo_v, *[k / 1000 for k in Pv])
    add("VP", f"Vigas principais {EST['perfil_viga']} contínuas (3 un.) + enrijecedores de apoio", "estrutura", "HIP", vp,
        permite=["PIL", "VS", "CTV", "VPL"])
    vs = []
    for x in EST["xs_j"]:
        vs += I_horizontal("Y", ys_[0] - 0.05, ys_[-1] + 0.05, x, None, z_topo_j, *[k / 1000 for k in Pj])
    add("VS", f"Vigas secundárias {EST['perfil_joist']} @ 0,44 m (11 un.) contínuas", "estrutura", "HIP", vs,
        permite=["VP", "CH-01", "ANC", "VPL", "GC-DECK"])
    add("CH-01", "Chapa de piso lisa 9,5 mm A36 em 5 painéis parafusados (cabeça escareada) — apoio integral da caixa",
        "estrutura", "PEND", [box(xs[0], ys_[0], z_topo_j, xs[-1], ys_[-1], z_deck)],
        pend="Forma de apoio, planicidade e manta exigidas pelo fabricante", permite=["VS", "TQ-101", "ANC", "GC-DECK", "PST-PT"])
    ctv = []
    zb, zt = z_pb_top + 0.08, z_base_v - 0.08
    for y in (ys_[0], ys_[-1]):
        for i in range(2):
            ctv += [cyl((xs[i], y, zb), (xs[i + 1], y, zt), 0.008, 6), cyl((xs[i], y, zt), (xs[i + 1], y, zb), 0.008, 6)]
    for x in (xs[0], xs[-1]):
        for i in range(2):
            ctv += [cyl((x, ys_[i], zb), (x, ys_[i + 1], zt), 0.008, 6), cyl((x, ys_[i], zt), (x, ys_[i + 1], zb), 0.008, 6)]
    add("CTV", "Contraventamento em X, barras Ø16 A36 com esticador (4 faces)", "estrutura", "HIP", ctv, permite=["PIL", "VP"])
    anc = []
    for k in range(8):
        ang = math.radians(22.5 + 45 * k)
        x = X_CAIXA + 2.06 * math.cos(ang)
        y = Y_CAIXA + 2.06 * math.sin(ang)
        anc.append(box(x - 0.05, y - 0.05, z_deck, x + 0.05, y + 0.05, z_deck + 0.15))
    add("ANC", "8 ancoragens da caixa (olhal no deck; Td ≈ 5 kN cada) — tipo depende do fabricante", "estrutura", "PEND", anc,
        pend="Pontos e cargas admissíveis de ancoragem da caixa", permite=["CH-01", "TQ-101", "VS", "ZN-04"])

    # plataforma de serviço
    xp0, xp1 = 81.86, 82.9
    z_pl = z_deck
    vpl = []
    for y in ys_:
        vpl += I_horizontal("X", xs[-1] + 0.08, xp1, y, None, z_pl - 0.03, *[k / 1000 for k in PERFIS_W["W150x13,0"]])
    vpl += I_horizontal("Y", ys_[0] - 0.05, ys_[-1] + 0.05, xp1, None, z_pl - 0.03, *[k / 1000 for k in PERFIS_W["W150x13,0"]])
    add("VPL", "Vigas da plataforma de serviço W150×13,0", "estrutura", "HIP", vpl, permite=["PST", "PL-01", "PIL", "VP", "VS"])
    pst = []
    for y in ys_:
        pst += I_vertical(xp1, y, z_pb_top, z_pl - 0.03 - 0.148, *[k / 1000 for k in PERFIS_W["W150x22,5"]])
    add("PST", "Postes da plataforma W150×22,5 (3 un.)", "estrutura", "HIP", pst, permite=["PB", "VPL", "PED"])
    add("PL-01", "Plataforma de serviço 1,0 × 4,4 m, piso grade galvanizada, cota 113,50 — acesso aos registros dos bocais",
        "acesso", "HIP", [box(xp0, ys_[0], z_pl - 0.03, xp1 + 0.05, ys_[-1], z_pl)],
        permite=["VPL", "TB-102", "TB-201", "DR-301", "PST-PT", "GC-PL", "ES-01"])
    gc = []
    gc += guarda_corpo((xp1 + 0.0, ys_[0]), (xp1 + 0.0, ys_[-1]), z_pl)
    gc += guarda_corpo((xp0, ys_[-1]), (xp1, ys_[-1]), z_pl)
    add("GC-PL", "Guarda-corpo da plataforma h = 1,10 m (travessões + rodapé)", "acesso", "HIP", gc, permite=["PL-01", "VPL", "ES-01"])
    gcd = []
    gcd += guarda_corpo((xs[0] + 0.03, ys_[0] + 0.03), (xs[0] + 0.03, ys_[-1] - 0.03), z_deck)
    gcd += guarda_corpo((xs[0] + 0.03, ys_[-1] - 0.03), (xs[-1] - 0.06, ys_[-1] - 0.03), z_deck)
    gcd += guarda_corpo((xs[0] + 0.03, ys_[0] + 0.03), (xs[-1] - 0.06, ys_[0] + 0.03), z_deck)
    add("GC-DECK", "Guarda-corpo removível no perímetro do deck (remover durante o içamento da caixa)", "acesso", "HIP", gcd,
        permite=["CH-01", "VS", "ZN-04"])
    # escada da plataforma (descendo para o sul)
    es = []
    nd = 8
    y_top, y_bot = ys_[0], ys_[0] - 1.65
    for i in range(1, nd):
        y = y_top - (y_top - y_bot) * i / nd
        z = z_pl - (z_pl - 112.0) * i / nd
        es.append(box(81.95, y - 0.13, z - 0.04, 82.85, y + 0.13, z))
    es += [cyl((81.93, y_top, z_pl), (81.93, y_bot, 112.0), 0.04, 8), cyl((82.87, y_top, z_pl), (82.87, y_bot, 112.0), 0.04, 8)]
    es += [cyl((81.93, y_top, z_pl + 0.9), (81.93, y_bot, 112.9), 0.02, 8), cyl((82.87, y_top, z_pl + 0.9), (82.87, y_bot, 112.9), 0.02, 8)]
    add("ES-01", "Escada 42° (1,00 m de largura, 8 espelhos de 0,19 m) plataforma ↔ terreno", "acesso", "HIP", es,
        permite=["PL-01", "VPL", "TER-01", "RAD-01"])
    # patamar superior + escada marinheiro com gaiola
    pp = [cyl((83.2, y, 112.12), (83.2, y, 118.05), 0.05, 8) for y in (0.5, 1.3)]
    pp += [cyl((81.9, y, z_pl), (81.9, y, 118.05), 0.05, 8) for y in (0.5, 1.3)]
    add("PST-PT", "Montantes do patamar superior (tubo 100×100) — 2 no radier, 2 sobre a plataforma", "acesso", "PEND", pp,
        permite=["PED", "PL-01", "PT-01", "CH-01", "VS"], pend="Depende do acesso ao teto previsto pelo fabricante")
    pt = [box(81.45, 0.5, 118.05, 83.42, 1.3, 118.10)]
    pt += guarda_corpo((81.6, 0.5), (83.2, 0.5), 118.10) + guarda_corpo((81.6, 1.3), (83.2, 1.3), 118.10)
    add("PT-01", "Patamar superior 1,75 × 0,80 m (cota 118,10) com guarda-corpo, acesso à boca de visita do teto",
        "acesso", "PEND", pt, pend="Posição da boca de visita, resistência do teto (fornecedor)", permite=["PST-PT", "EM-01"])
    em = [cyl((83.40, y, 112.0), (83.40, y, 119.2), 0.02, 8) for y in (0.70, 1.10)]
    z = 112.3
    while z < 119.0:
        em.append(cyl((83.40, 0.70, z), (83.40, 1.10, z), 0.012, 6))
        z += 0.30
    for ang in (0, 60, -60, 120, -120):
        x = 83.77 + 0.36 * math.cos(math.radians(ang))
        y = 0.90 + 0.36 * math.sin(math.radians(ang))
        em.append(cyl((x, y, 114.3), (x, y, 119.2), 0.01, 6))
    for zc in (114.3, 115.8, 117.3, 119.2):
        em += [cyl((83.40, 0.70, zc), (83.59, 0.59, zc), 0.01, 6), cyl((83.40, 1.10, zc), (83.59, 1.21, zc), 0.01, 6),
               cyl((83.95, 0.59, zc), (84.13, 0.9, zc), 0.01, 6), cyl((83.95, 1.21, zc), (84.13, 0.9, zc), 0.01, 6)]
    add("EM-01", "Escada marinheiro com gaiola (início do guarda-corpo a 2,3 m) terreno → patamar 118,10 — alternativa: escada do fabricante",
        "acesso", "PEND", em, pend="Requisitos NR-35/NBR ISO 14122-4 e acessório do fabricante", permite=["PT-01", "TER-01", "RAD-01", "PST-PT"])
    add("ZN-03", "Espaço livre de subida da escada marinheiro", "zonas", "HIP", [box(83.43, 0.6, 112.05, 84.07, 1.2, 119.1)], zona=True,
        permite=["EM-01", "TER-01"])
    add("ZN-01", "Faixa livre de circulação da plataforma (0,70 m × 2,1 m de altura)", "zonas", "HIP",
        [box(82.05, ys_[0], z_pl + 0.01, 82.75, ys_[-1] - 0.03, z_pl + 2.1)], zona=True, permite=["PL-01"])
    add("ZN-08", "Área livre ao pé da escada (1,0 m)", "zonas", "HIP", [box(81.9, -4.85, 112.05, 82.9, -3.90, 114.1)], zona=True)

    # ------------------------------------------------------------------ caixa
    Rt = CAIXA_FORN["D_ext"] / 2
    add("TQ-101", "Caixa d'água 50 m³ Ø4,00 × 4,50 m, 1 200 kg vazia (dados do fornecedor fictício — sem desenho certificado)",
        "caixa", "PEND", [cyl((X_CAIXA, Y_CAIXA, z_deck), (X_CAIXA, Y_CAIXA, TANQUE["cota_topo"]), Rt, 48)],
        pend="Desenho certificado, bocais, apoio, ancoragem, tampa, ventilação",
        permite=["CH-01", "ANC", "N1", "N2", "N3", "N4", "BV", "LT-101", "TB-102", "TB-201", "DR-301", "EX-401"])
    add("ZN-04", "Envelope de içamento da caixa (Ø4,20 até 6 m acima do topo) — montagem por guindaste",
        "zonas", "HIP", [cyl((X_CAIXA, Y_CAIXA, TANQUE["cota_topo"] + 0.02), (X_CAIXA, Y_CAIXA, TANQUE["cota_topo"] + 6), Rt + 0.10, 32)],
        zona=True, permite=["TQ-101", "BV", "LT-101", "N1", "ANC", "GC-DECK"])

    def bocal_lateral(y, z):
        x = X_CAIXA + math.sqrt(Rt ** 2 - (y - Y_CAIXA) ** 2)
        return x

    xn2 = bocal_lateral(-0.3, NIVEIS["saida_N2_eixo"])
    xn3 = bocal_lateral(-1.0, NIVEIS["dreno_N3_eixo"])
    xn4 = bocal_lateral(-1.5, NIVEIS["extravasor_N4_soleira"])
    add("N1", "Bocal N1 — entrada no teto, descarga livre em 117,80 (separação atmosférica)", "caixa", "PEND",
        [cyl((80.8, 1.3, 117.95), (80.8, 1.3, 118.08), 0.04, 10)], permite=["TQ-101", "TB-102", "ZN-04"])
    add("N2", "Bocal N2 — saída DN50 eixo 113,80 (0,25 m acima do fundo) para pressurização", "caixa", "PEND",
        [cyl((xn2 - 0.05, -0.3, 113.80), (xn2 + 0.08, -0.3, 113.80), 0.045, 10)], permite=["TQ-101", "TB-201"])
    add("N3", "Bocal N3 — dreno de fundo DN65/75 eixo 113,62", "caixa", "PEND",
        [cyl((xn3 - 0.05, -1.0, 113.62), (xn3 + 0.08, -1.0, 113.62), 0.05, 10)], permite=["TQ-101", "DR-301"])
    add("N4", "Bocal N4 — extravasor DN100, soleira 117,61 (50 m³), com tela", "caixa", "PEND",
        [cyl((xn4 - 0.05, -1.5, 117.61), (xn4 + 0.10, -1.5, 117.61), 0.065, 10)], permite=["TQ-101", "EX-401"])
    add("BV", "Boca de visita/ventilação no teto (posição e dimensão do fabricante)", "caixa", "PEND",
        [cyl((80.9, 0.85, 117.95), (80.9, 0.85, 118.15), 0.30, 16), cyl((79.0, -0.6, 117.95), (79.0, -0.6, 118.35), 0.08, 10)],
        permite=["TQ-101", "ZN-04"])
    add("LT-101", "Transmissor de nível no teto + boias LSHH/LSLL suspensas (internas)", "eletrica", "PEND",
        [box(79.85, -0.65, 118.0, 80.05, -0.45, 118.25)], permite=["TQ-101", "ZN-04"])

    # ------------------------------------------------------------------ saída, dreno, extravasor
    pts = [(xn2, -0.3, 113.80), (81.95, -0.3, 113.80), (81.95, -0.3, 112.35), (84.1, -0.3, 112.35), (84.1, -0.8, 112.35),
           (85.0, -0.8, 112.35), (85.0, -0.8, 112.3)]
    add("TB-201", "Saída N2 → V-201 (na plataforma) → junta flexível → filtro Y → coletor de sucção DE63 dos boosters",
        "tub_casa", "HIP", polyline(pts, 0.0315), permite=["N2", "TQ-101", "PL-01", "CH-01", "ABR-O", "SK-201", "VPL"])
    pts = [(xn3, -1.0, 113.62), (81.95, -1.0, 113.62), (81.95, -1.0, 112.2), (83.45, -1.0, 112.2), (83.45, -1.2, 112.2)]
    add("DR-301", "Dreno N3 DE75: V-301 (plataforma) + V-302 de estrangulamento (≤ 3 L/s) → caixa CP-301", "drenagem", "HIP",
        polyline(pts, 0.0375), permite=["N3", "TQ-101", "PL-01", "CH-01", "CP-301"])
    pts = [(xn4, -1.5, 117.61), (83.7, -1.5, 117.61), (83.7, -1.5, 112.45)]
    add("EX-401", "Extravasor DN100 com tela anti-insetos, descarga visível com separação atmosférica sobre CP-301", "drenagem", "HIP",
        polyline(pts, 0.055), permite=["N4", "TQ-101", "SP-401"])
    add("SP-401", "Suporte do extravasor (tubo 60 mm sobre bloco próprio, fora da caixa de recepção)", "estrutura", "HIP",
        [cyl((84.15, -1.5, 112.0), (84.15, -1.5, 117.75), 0.03, 8), cyl((83.7, -1.5, 117.0), (84.15, -1.5, 117.0), 0.015, 6),
         box(84.0, -1.65, 111.7, 84.3, -1.35, 112.0)],
        permite=["EX-401", "RAD-01", "TER-01"])
    add("CP-301", "Caixa de recepção dreno/extravasor 0,6 × 0,8 m com grelha (separação atmosférica, inspeção visual)",
        "drenagem", "HIP", [box(83.4, -1.9, 111.5, 84.0, -1.1, 112.05)], permite=["DR-301", "TER-01", "RAD-01", "DR-302"])
    pts = [(83.7, -1.9, 111.7), (83.7, -5.0, 111.6)] + enterrada(83.7, 60.5, -5.0, 0.6)[1:]
    add("DR-302", "Linha de descarte DN100 por gravidade (i ≥ 1 %) → caixa de decantação/descloração CD-301",
        "drenagem", "HIP", polyline(pts, 0.055), permite=["CP-301", "TER-01", "CD-301"])
    zt = z_terreno(60.0)
    add("CD-301", "Caixa de decantação e descloração (≈ 2 m³) — destino final a aprovar", "drenagem", "PEND",
        [box(59.0, -5.8, zt - 1.2, 60.5, -4.2, zt + 0.1)], pend="Aprovação ambiental do ponto de descarte", permite=["DR-302", "TER-01", "VI-301"])
    zt = z_terreno(60.0)
    add("VI-301", "Vala de infiltração/dispersão 8 × 1 m (≥ 12 m da fundação; ≥ 50 m da margem — conferir APP)",
        "drenagem", "PEND", [box(51.0, -5.5, z_terreno(55) - 0.8, 59.0, -4.5, z_terreno(55) + 0.02)],
        pend="Ensaio de infiltração; largura do rio/APP; aprovação CETESB/município", permite=["TER-01", "CD-301"])

    # ------------------------------------------------------------------ abrigo de equipamentos
    x0a, x1a, y0a, y1a = 84.6, 87.6, -1.5, 1.0
    add("ABR-PISO", "Abrigo de equipamentos 3,0 × 2,5 m — laje de piso (FORA da área 8×8: requer ampliação)", "civil", "HIP",
        [box(x0a, y0a, 111.9, x1a, y1a, 112.1)], permite=["TER-01", "TB-101", "F-101", "SK-201", "ABR-O", "ABR-N", "ABR-L", "ABR-S", "CL-101"])
    add("ABR-O", "Abrigo — parede oeste", "civil", "HIP", [box(x0a, y0a, 112.1, x0a + 0.15, y1a, 114.6)], permite=["ABR-PISO", "TB-201", "ABR-N", "ABR-S", "ABR-T"])
    add("ABR-N", "Abrigo — parede norte (QCB fixado internamente)", "civil", "HIP", [box(x0a, y1a - 0.15, 112.1, x1a, y1a, 114.6)],
        permite=["ABR-PISO", "TB-102", "QCB-01", "ABR-O", "ABR-L", "ABR-T", "EL-102"])
    add("ABR-L", "Abrigo — parede leste", "civil", "HIP", [box(x1a - 0.15, y0a, 112.1, x1a, y1a, 114.6)],
        permite=["ABR-PISO", "TB-202", "ABR-N", "ABR-S", "ABR-T", "EL-102"])
    add("ABR-S", "Abrigo — parede sul com porta 0,9 m", "civil", "HIP",
        [box(x0a, y0a, 112.1, 85.4, y0a + 0.15, 114.6), box(86.3, y0a, 112.1, x1a, y0a + 0.15, 114.6), box(85.4, y0a, 114.2, 86.3, y0a + 0.15, 114.6)],
        permite=["ABR-PISO", "ABR-O", "ABR-L", "ABR-T", "EL-101", "CL-101"])
    add("ABR-T", "Abrigo — cobertura ventilada", "civil", "HIP", [box(x0a - 0.1, y0a - 0.1, 114.6, x1a + 0.1, y1a + 0.1, 114.7)],
        permite=["ABR-O", "ABR-N", "ABR-L", "ABR-S"])
    add("SK-201", "Conjunto pressurizador duplex P-201A/B (2 × 100 %, 0,75 kW, inversor, Q = 2,2 m³/h, H ≥ 31 m) + vaso PV-201",
        "equip", "PEND", [box(85.0, -1.25, 112.1, 86.3, -0.35, 112.18),
                          cyl((85.15, -0.8, 112.35), (85.55, -0.8, 112.35), 0.10, 12),
                          cyl((85.75, -0.8, 112.35), (86.15, -0.8, 112.35), 0.10, 12),
                          cyl((86.15, -0.55, 112.18), (86.15, -0.55, 112.55), 0.09, 12)],
        pend="Curvas reais; vazão mínima; ajuste do inversor", permite=["ABR-PISO", "TB-201", "TB-202"])
    add("ZN-05", "Zona de remoção/manutenção das bombas do booster (frente do skid)", "zonas", "HIP",
        [box(85.0, -0.34, 112.12, 86.3, 0.2, 113.0)], zona=True, permite=["ABR-PISO"])
    add("CL-101", "Compartimento de cloração separado e ventilado (tanque de solução 100 L + dosadora DP-101) — acesso externo",
        "equip", "PEND", [box(86.85, -1.35, 112.1, 87.45, -0.45, 112.85)], pend="Produto e dosagem conforme análise de água",
        permite=["ABR-PISO", "ABR-S", "ABR-L"])
    add("QCB-01", "Quadro de comando e proteção QCB-01 IP65 (soft-starter P-101, inversores P-201, CLP, DPS, DR, GSM)",
        "eletrica", "HIP", [box(85.9, 0.70, 113.0, 86.7, 0.85, 114.2)], permite=["ABR-N", "EL-102"])
    add("ZN-02", "Espaço livre de operação à frente do QCB (≥ 1,0 m)", "zonas", "HIP", [box(85.9, -0.3, 112.12, 86.7, 0.69, 114.2)],
        zona=True, permite=["ABR-PISO"])
    pts = [(86.2, -0.8, 112.35), (86.4, -0.8, 112.35), (86.4, -0.8, 111.7), (87.8, -0.8, 111.7), (87.8, -0.8, 111.3)] + enterrada(88.0, 218.8, -0.8, 0.7)
    pts += [(218.8, -0.8, z_terreno(218.8) - 0.3)]
    add("TB-202", "Linha não potável PEAD DE40 SDR11 enterrada (0,7 m), fita de aviso ‘ÁGUA NÃO POTÁVEL’, identificação lilás",
        "tub_casa", "HIP", polyline(pts, 0.02), pend="Traçado, travessia da estrada (camisa ≥ 1,0 m), pontos altos",
        permite=["SK-201", "ABR-L", "ABR-PISO", "TER-01", "CE-01"])

    # ------------------------------------------------------------------ elétrica
    pts = [(85.4, -1.6, 111.4), (85.4, -3.3, z_terreno(85.4) - 0.6)] + enterrada(85.4, 12.3, -3.3, 0.6)[1:]
    pts += [(12.3, 1.3, z_terreno(12.3) - 0.6), (11.4, 1.3, zt11 - 0.3)]
    add("EL-101", "Eletroduto PEAD corrugado Ø50 com cabo 4×4 mm² p/ bomba submersa + cabo de sinal (L ≈ 130 m)",
        "eletrica", "HIP", polyline(pts, 0.025, 8), permite=["ABR-PISO", "ABR-S", "TER-01", "CX-101"])
    add("QE-EX", "Quadro existente junto à área da caixa (posição, capacidade e esquema de aterramento A LEVANTAR)", "eletrica", "PEND",
        [box(88.3, 3.3, 112.0, 88.7, 3.7, 113.8)], pend="Capacidade, proteção geral, Icc, esquema de aterramento", permite=["TER-01", "EL-102"])
    pts = [(88.5, 3.5, 112.0), (88.5, 3.5, 111.5), (87.0, 3.5, 111.5), (87.0, 1.2, 111.5), (87.0, 1.2, 112.6), (87.0, 0.9, 112.6)]
    add("EL-102", "Alimentador 4×4 mm² + PE (QE existente → QCB-01)", "eletrica", "HIP", polyline(pts, 0.02, 8),
        permite=["QE-EX", "TER-01", "ABR-N", "ABR-PISO", "QCB-01"])
    add("ATR-01", "Malha/anel de aterramento + eletrodo de fundação no radier, ligado à estrutura e ao QCB", "eletrica", "HIP",
        polyline([(76.7, -2.9, 111.5), (83.4, -2.9, 111.5), (83.4, 2.9, 111.5), (76.7, 2.9, 111.5), (76.7, -2.9, 111.5)], 0.01, 6),
        permite=["TER-01", "RAD-01"])

    # ------------------------------------------------------------------ casa
    zc = COTAS["piso_casa"]
    add("CE-01", "Caixa de entrada não potável: registro VE-01, identificação — LIMITE DO ESCOPO (1 m antes da parede)",
        "casa", "HIP", [box(218.5, -1.2, zc - 0.6, 219.3, -0.4, zc + 0.15)], permite=["TB-202", "TER-01"])
    roof = dict(t="mesh", v=[[220.5, -6.5, 123.2], [232.0, -6.5, 123.2], [232.0, 6.5, 123.2], [220.5, 6.5, 123.2],
                             [220.5, 0, 125.0], [232.0, 0, 125.0]],
                f=[[0, 1, 5], [0, 5, 4], [3, 4, 5], [3, 5, 2], [0, 4, 3], [1, 2, 5]])
    add("CASA", "Casa (volume ilustrativo — projeto interno é de terceiros)", "casa", "HIP",
        [box(220.5, -6.0, zc, 232.0, 6.0, 123.2), roof], pend="Projeto das instalações internas (NBR 5626 / NBR 16783)",
        permite=["TER-01", "PA-01"])
    add("PA-01", "Ponto de consumo mais alto — cota 122,50, p ≥ 15 m.c.a. (posição real a informar)", "casa", "CONF",
        [cyl((225.0, 3.0, 122.40), (225.0, 3.0, 122.60), 0.15, 12)], permite=["CASA"])
    add("POT-EX", "Entrada do sistema POTÁVEL existente (fora do escopo) — manter afastada e sem interligação",
        "casa", "PEND", [box(218.5, 4.0, zc - 0.6, 219.3, 4.8, zc + 0.15)], pend="Posição real do sistema potável", permite=["TER-01"])

    # ------------------------------------------------------------------ marcos de área
    def moldura(x0, y0, x1, y1, z, e=0.04):
        return [box(x0, y0, z, x1, y0 + e, z + 0.02), box(x0, y1 - e, z, x1, y1, z + 0.02),
                box(x0, y0, z, x0 + e, y1, z + 0.02), box(x1 - e, y0, z, x1, y1, z + 0.02)]
    add("AREA-8x8", "Área disponível informada 8 × 8 m (X 76–84)", "zonas", "CONF", moldura(76, -4, 84, 4, 112.03))
    add("AREA-AMP", "Ampliação proposta 4,5 × 8 m (abrigo, caixa de recepção, pé da escada, circulação)", "zonas", "HIP",
        moldura(84, -4, 88.5, 4, 112.03))
    return COMPS


if __name__ == "__main__":
    c = construir()
    print(len(c), "componentes")
