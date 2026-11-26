# -*- coding: utf-8 -*-
"""SIM-04 — Transiente hidráulico no recalque rio → caixa (P-101) pelo Método das Características,
com modelo de cavidade discreta de vapor (DVCM) para representar separação de coluna.

Contorno de montante: bomba + retenção. A vazão cai de Q0 a zero numa rampa t_r e a retenção
impede o refluxo. Contorno de jusante: descarga livre na caixa, carga constante 117,80.
Perfil do tubo: HIPOTÉTICO (camisa no talude → vala → abrigo → prumada), sem topografia.
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calc"))
sys.path.insert(0, AQUI)
from premissas import *  # noqa
import hidraulica as HD
import graficos as GR

# perfil (s = distância ao longo do tubo a partir da bomba, z = cota do eixo)
PERFIL = [(0.0, 96.30), (14.0, 103.80), (16.0, 103.0), (98.0, 111.30), (102.0, 111.60), (104.0, 112.60), (105.0, 112.30), (109.0, 112.30), (115.0, 118.35)]


def z_tubo(s):
    for (s0, z0), (s1, z1) in zip(PERFIL, PERFIL[1:]):
        if s0 <= s <= s1:
            return z0 + (z1 - z0) * (s - s0) / (s1 - s0)
    return PERFIL[-1][1]


def simular(t_r, T=20.0, N=46, atrito=True, perfil=True, H_jus=None, Q0=None, L=None, a=None, cavit=True):
    D = di_pead(CAPTACAO["DE_recalque"])
    A = math.pi * D ** 2 / 4
    L = L or CAPTACAO["L_recalque_m"]
    a = a or HD.celeridade_pead(D, PEAD_SDR11[CAPTACAO["DE_recalque"]] / 1000)
    Q0 = Q0 if Q0 is not None else CAPTACAO["Q_proj_m3h"] / 3600
    v0 = Q0 / A
    _, _, f, _ = HD.perda_distribuida(Q0, D, L)
    f = f if atrito else 0.0
    dx = L / N
    dt = dx / a
    B = a / (G * A)
    Rf = f * dx / (2 * G * D * A ** 2)
    s = np.linspace(0, L, N + 1)
    z = np.array([z_tubo(x) for x in s]) if perfil else np.zeros(N + 1)
    H_jus = H_jus if H_jus is not None else NIVEIS["entrada_N1_descarga_livre"]
    # regime permanente: H decresce linearmente pela perda distribuída (localizadas concentradas no início)
    hf = f * L / D * v0 ** 2 / (2 * G)
    H = H_jus + hf * (1 - s / L)
    Qu = np.full(N + 1, Q0)
    Qd = np.full(N + 1, Q0)
    hv = -(P_ATM_MCA - PV_30C)           # pressão de vapor manométrica (m)
    Hv = z + hv
    vol = np.zeros(N + 1)
    Hmax, Hmin = H.copy(), H.copy()
    serie_t, serie_bomba, serie_crista = [], [], []
    i_cr = int(np.argmin(np.abs(s - 14.0)))
    nst = int(T / dt)
    cav_max = 0.0
    for n in range(nst):
        t = (n + 1) * dt
        Hn, Qun, Qdn = H.copy(), Qu.copy(), Qd.copy()
        # nós internos
        for i in range(1, N):
            Cp = H[i - 1] + B * Qd[i - 1] - Rf * Qd[i - 1] * abs(Qd[i - 1])
            Cm = H[i + 1] - B * Qu[i + 1] + Rf * Qu[i + 1] * abs(Qu[i + 1])
            if vol[i] <= 0:
                Hp = 0.5 * (Cp + Cm)
                if cavit and Hp < Hv[i]:
                    Hp = Hv[i]
                    qu, qd = (Cp - Hp) / B, (Hp - Cm) / B
                    vol[i] = max(0.0, (qd - qu) * dt)
                else:
                    qu = qd = (Cp - Cm) / (2 * B)
                    vol[i] = 0.0
            else:
                Hp = Hv[i]
                qu, qd = (Cp - Hp) / B, (Hp - Cm) / B
                vol[i] += 0.5 * ((qd - qu) + (Qd[i] - Qu[i])) * dt
                if vol[i] <= 0:
                    vol[i] = 0.0
                    Hp = 0.5 * (Cp + Cm)
                    qu = qd = (Cp - Cm) / (2 * B)
            Hn[i], Qun[i], Qdn[i] = Hp, qu, qd
            cav_max = max(cav_max, vol[i])
        # montante: vazão imposta pela bomba (rampa) com retenção
        Qp = Q0 * max(0.0, 1 - t / t_r) if t_r > 0 else 0.0
        Cm = H[1] - B * Qu[1] + Rf * Qu[1] * abs(Qu[1])
        Hp0 = Cm + B * Qp
        if cavit and Hp0 < Hv[0]:
            Hp0 = Hv[0]
        Hn[0], Qun[0], Qdn[0] = Hp0, Qp, Qp
        # jusante: carga constante
        Cp = H[N - 1] + B * Qd[N - 1] - Rf * Qd[N - 1] * abs(Qd[N - 1])
        Hn[N] = H_jus
        Qun[N] = Qdn[N] = (Cp - H_jus) / B
        H, Qu, Qd = Hn, Qun, Qdn
        Hmax = np.maximum(Hmax, H)
        Hmin = np.minimum(Hmin, H)
        serie_t.append(t)
        serie_bomba.append(H[0] - z[0])
        serie_crista.append(H[i_cr] - z[i_cr])
    return dict(s=s, z=z, Hmax=Hmax, Hmin=Hmin, t=np.array(serie_t), p_bomba=np.array(serie_bomba),
                p_crista=np.array(serie_crista), a=a, v0=v0, dt=dt, cav_max_L=cav_max * 1000, hv=hv,
                pmax=float((Hmax - z).max()), pmin=float((Hmin - z).min()), H0=float(H_jus + hf))


def run(saida):
    os.makedirs(saida, exist_ok=True)
    cen = {"A — falta de energia (rampa 0,3 s)": 0.3, "B — parada suave por soft-starter (rampa 5 s)": 5.0}
    out = {}
    res = {}
    for nome, tr in cen.items():
        r = simular(tr)
        res[nome] = r
        out[nome] = dict(t_rampa_s=tr, p_max_mca=round(r["pmax"], 1), p_min_mca=round(r["pmin"], 1),
                         cavitacao=bool(r["pmin"] <= r["hv"] + 0.01), vol_cavidade_max_L=round(r["cav_max_L"], 3))
    out["celeridade_m_s"] = round(res[list(cen)[0]]["a"], 1)
    out["joukowsky_m"] = round(res[list(cen)[0]]["a"] * res[list(cen)[0]]["v0"] / G, 1)
    out["pressao_vapor_manometrica_m"] = round(res[list(cen)[0]]["hv"], 2)
    out["classe_PN16_mca"] = 160
    rA, rB = res[list(cen)[0]], res[list(cen)[1]]
    GR.linhas([(rA["s"], rA["Hmax"] - rA["z"], (200, 40, 40), "A: pressão máx.", 3),
               (rA["s"], rA["Hmin"] - rA["z"], (240, 140, 140), "A: pressão mín.", 3),
               (rB["s"], rB["Hmax"] - rB["z"], (30, 90, 180), "B: pressão máx.", 3),
               (rB["s"], rB["Hmin"] - rB["z"], (120, 170, 230), "B: pressão mín.", 3)],
              "SIM-04 — Envoltórias de pressão no recalque P-101 (MOC + DVCM)", "distância a partir da bomba s (m)",
              "pressão manométrica (m.c.a.)", os.path.join(saida, "SIM-04_envoltorias.png"),
              sub=f"a = {rA['a']:.0f} m/s; v0 = {rA['v0']:.2f} m/s; perfil HIPOTÉTICO; vapor ≈ {rA['hv']:.1f} m.c.a.; classe PN16 = 160 m",
              hlines=[(rA["hv"], (120, 0, 120), "pressão de vapor"), (0.0, (90, 90, 90), "atmosférica")])
    GR.linhas([(rA["t"], rA["p_bomba"], (200, 40, 40), "A: junto à bomba", 2),
               (rA["t"], rA["p_crista"], (240, 140, 60), "A: crista do talude", 2),
               (rB["t"], rB["p_bomba"], (30, 90, 180), "B: junto à bomba", 2),
               (rB["t"], rB["p_crista"], (100, 170, 120), "B: crista do talude", 2)],
              "SIM-04 — Pressão × tempo após a parada da bomba P-101", "tempo (s)", "pressão manométrica (m.c.a.)",
              os.path.join(saida, "SIM-04_series.png"), sub="Cenário A: queda de energia. Cenário B: parada com rampa do soft-starter.",
              hlines=[(rA["hv"], (120, 0, 120), "vapor")])
    return out
