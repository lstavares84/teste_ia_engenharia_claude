# -*- coding: utf-8 -*-
"""FEA-02 — Chapa de piso do deck (placa de Mindlin contínua sobre as vigas secundárias).
FEA-03 — Radier sobre base elástica de Winkler (placa espessa de Mindlin + molas), com cargas dos
pilares tiradas do pórtico espacial FEA-01. Sensibilidade ao coeficiente de reação vertical k_s
(SEM SONDAGEM: valores hipotéticos 10 / 20 / 40 MN/m³)."""
import json
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calc"))
sys.path.insert(0, AQUI)
from premissas import *  # noqa
from elementos import PlacaRet
import graficos as GR

RES = json.load(open(os.path.join(AQUI, "..", "calc", "resultados", "resultados.json"), encoding="utf-8"))
R2 = RES["MC-02_estrutura_fundacao"]


def malha(breaks, hmax):
    pts = [breaks[0]]
    for a, b in zip(breaks, breaks[1:]):
        n = max(1, int(math.ceil((b - a) / hmax - 1e-9)))
        pts += list(np.linspace(a, b, n + 1)[1:])
    return np.array(pts)


# ====================================================================== FEA-02 chapa
def chapa(saida):
    t = ESTR["chapa_piso_mm"] / 1000
    s = ESTR["esp_joists"]
    nv = 4
    xs = np.linspace(0, nv * s, nv * 10 + 1)
    ys = np.linspace(0, 1.32, 21)
    P = PlacaRet(xs, ys, E_ACO * 1e3, 0.3, t)
    apoio = [k for k in range(P.nn) if any(abs(P.coord(k)[0] - i * s) < 1e-9 for i in range(nv + 1))]
    h = NIVEIS["borda_cheio_total"] - TANQUE["cota_fundo_int"]
    g = ESTR["chapa_piso_mm"] / 1000 * RHO_ACO * G / 1000 + ESTR["manta_kPa"] + CAIXA_FORN["massa_vazia_kg"] * G / 1000 / (math.pi * 4)
    q_els = GAMMA_W * h + g
    q_elu = GAMMA["q_agua"] * GAMMA_W * h + GAMMA["g"] * g
    out = {}
    for nome, q in (("ELS", q_els), ("ELU", q_elu)):
        u, M = P.resolver(lambda x, y: q, fix_w=apoio)
        w = -u[0::3]
        out[nome] = dict(q=q, w_max_mm=float(w.max() * 1000), Mx_pos=float(M[:, 0].max()), Mx_neg=float(M[:, 0].min()),
                         sigma_max_MPa=float(6 * np.abs(M[:, 0]).max() / t ** 2 / 1000))
        if nome == "ELS":
            W = w.reshape(len(ys), len(xs))
            wel = 0.25 * (W[:-1, :-1] + W[1:, :-1] + W[:-1, 1:] + W[1:, 1:]) * 1000
            GR.campo(xs, ys, wel, "FEA-02 — Chapa 9,5 mm do deck: flecha (ELS)", "mm", os.path.join(saida, "FEA-02_chapa_flecha.png"),
                     sub=f"Placa de Mindlin Q4 contínua sobre 5 linhas de vigas secundárias @ 0,44 m; q = {q:.1f} kPa (água até a borda + permanente)")
        else:
            Mx = M[:, 0].reshape(len(ys) - 1, len(xs) - 1)
            GR.campo(xs, ys, Mx, "FEA-02 — Chapa 9,5 mm: momento Mx (ELU)", "kN·m/m", os.path.join(saida, "FEA-02_chapa_Mx.png"),
                     sub=f"q = {q:.1f} kPa; + traciona a face inferior; apoios (vigas) nas linhas x = 0; 0,44; 0,88; 1,32; 1,76 m", divergente=True)
    fyd = ACO_CHAPA["fy"] / GAMMA["a1"]
    out["sigma_Rd_MPa"] = fyd
    out["Mpl_Rd"] = ACO_CHAPA["fy"] * 1e3 * t ** 2 / 4 / GAMMA["a1"]
    out["limite_flecha_mm"] = s / 250 * 1000
    return out


# ====================================================================== FEA-03 radier
def radier(saida, reac_els, reac_elu, ks_lista=(10e3, 20e3, 40e3)):
    Lr, Br, hr = R2["radier"]
    X0r, Y0r = 76.9, -Br / 2
    pil = []
    for chave in reac_els:
        x, y = map(float, chave.split(";"))
        pil.append((x - X0r, y - Y0r, reac_els[chave], reac_elu[chave]))
    bx = [0.0, Lr]
    by = [0.0, Br]
    for x, y, _, _ in pil:
        bx += [x - 0.25, x + 0.25]
        by += [y - 0.25, y + 0.25]
    bx = sorted(set(round(v, 4) for v in bx if 0 <= v <= Lr))
    by = sorted(set(round(v, 4) for v in by if 0 <= v <= Br))
    xs, ys = malha(bx, 0.25), malha(by, 0.25)
    Ec = 0.875 * 5600 * math.sqrt(CONCRETO["fck"]) * 1e3  # Ecs (NBR 6118: αi·5600√fck), kPa
    P = PlacaRet(xs, ys, Ec, 0.2, hr)
    q_pp = GAMMA_CONC * hr

    def q_fun(N_index):
        def q(x, y):
            v = q_pp * (1.0 if N_index == 0 else GAMMA["g"])
            for (px, py, Ns, Nd) in pil:
                if abs(x - px) <= 0.25 and abs(y - py) <= 0.25:
                    v += (Ns if N_index == 0 else Nd) / 0.25
            return v
        return q
    out = {"malha": f"{len(xs)-1} × {len(ys)-1} elementos ({len(xs)*len(ys)*3} GL)", "Ecs_GPa": Ec / 1e6, "casos": {}}
    d_ef = hr - CONCRETO["cobrimento_mm"] / 1000 - 0.01
    As = math.pi * 0.010 ** 2 / 4 / 0.125
    MRd = As * ACO_CA50["fyk"] * 1e3 / GAMMA["s"] * 0.9 * d_ef
    out["MRd_malha_kNm_m"] = MRd
    for ks in ks_lista:
        u, M = P.resolver(q_fun(0), molas_w=ks)
        w = -u[0::3]
        p_solo = ks * w
        _, Md = P.resolver(q_fun(1), molas_w=ks)
        mstar = np.abs(Md[:, :2]) + np.abs(Md[:, 2:3])
        # recalques nos pilares
        def w_em(x, y):
            i = int(np.argmin(np.abs(xs - x)))
            j = int(np.argmin(np.abs(ys - y)))
            return w[j * len(xs) + i]
        wc = {f"{px+X0r:.2f};{py+Y0r:.2f}": w_em(px, py) * 1000 for (px, py, _, _) in pil}
        c = wc["79.60;0.00"]
        dif = max(abs(c - v) for k, v in wc.items() if k != "79.60;0.00" and not k.startswith("82.90"))
        beta = max(abs(c - wc[k]) / 1000 / math.hypot(float(k.split(";")[0]) - 79.6, float(k.split(";")[1]))
                   for k in wc if k != "79.60;0.00" and not k.startswith("82.90"))
        out["casos"][f"{ks/1000:.0f}"] = dict(w_max_mm=float(w.max() * 1000), w_min_mm=float(w.min() * 1000),
                                               p_solo_max_kPa=float(p_solo.max()), p_solo_min_kPa=float(p_solo.min()),
                                               recalque_pilares_mm={k: round(v, 2) for k, v in wc.items()},
                                               recalque_diferencial_mm=float(dif), distorcao_angular=float(beta),
                                               M_pos_max=float(Md[:, :2].max()), M_neg_max=float(Md[:, :2].min()),
                                               m_star_max=float(mstar.max()), taxa_flexao=float(mstar.max() / MRd))
        if abs(ks - 20e3) < 1:
            W = w.reshape(len(ys), len(xs))
            wel = 0.25 * (W[:-1, :-1] + W[1:, :-1] + W[:-1, 1:] + W[1:, 1:]) * 1000
            ped = [(px - 0.25, py - 0.25, px + 0.25, py + 0.25, "") for (px, py, _, _) in pil]
            marc = [(px, py, f"{wc[f'{px+X0r:.2f};{py+Y0r:.2f}']:.1f}") for (px, py, _, _) in pil]
            GR.campo(xs, ys, wel, "FEA-03 — Radier sobre Winkler (k = 20 MN/m³): recalque ELS", "mm",
                     os.path.join(saida, "FEA-03_radier_recalque.png"), contornos=ped, marcadores=marc,
                     sub="Cargas de serviço G+Q+L dos 12 apoios (FEA-01) + peso próprio; valores nos pilares em mm. k_s HIPOTÉTICO (sem sondagem)")
            Mx = Md[:, 0].reshape(len(ys) - 1, len(xs) - 1)
            GR.campo(xs, ys, Mx, "FEA-03 — Radier: momento Mx de cálculo (ELU-1, k = 20 MN/m³)", "kN·m/m",
                     os.path.join(saida, "FEA-03_radier_Mx.png"), contornos=ped, divergente=True,
                     sub=f"+ traciona a face inferior; MRd da malha Ø10 c/12,5 ≈ {MRd:.0f} kN·m/m por face")
    return out


def run(saida, reac_els, reac_elu):
    os.makedirs(saida, exist_ok=True)
    r = {"FEA-02": chapa(saida), "FEA-03": radier(saida, reac_els, reac_elu)}
    json.dump(r, open(os.path.join(saida, "FEA-02-03_placas.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return r
