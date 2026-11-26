# -*- coding: utf-8 -*-
"""FEA-01 — Pórtico espacial completo da estrutura de apoio da caixa + análise modal.

Modelo: 11 vigas secundárias, 3 principais, 9 pilares, plataforma (3 vigas + borda + 3 postes),
contraventamentos em X como treliça só-tração (iteração não linear: diagonais comprimidas são
removidas e o sistema é resolvido de novo). Ligação secundária↔principal por elo rígido vertical
(as vigas estão empilhadas). Bases rotuladas (conservador para flexão dos pilares sob carga lateral
— a estrutura é contraventada). Cargas da caixa aplicadas como carga distribuída nas secundárias
por faixa de influência, integrando a pressão somente sobre a projeção circular Ø 4,00 m.
"""
import json
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calc"))
sys.path.insert(0, AQUI)
from premissas import *  # noqa
import estrutura as EST    # funções de seção e verificação NBR 8800
from elementos import Portico

RES = json.load(open(os.path.join(AQUI, "..", "calc", "resultados", "resultados.json"), encoding="utf-8"))
R2 = RES["MC-02_estrutura_fundacao"]
E = E_ACO * 1e3
GA = G_ACO * 1e3


def props(nome):
    s = EST.props_I(nome)
    # eixo local y = alma ⇒ Iz (flexão no plano x-y) = inércia forte
    return dict(E=E, G=GA, A=s["A"], Iz=s["Ix"], Iy=s["Iy"], J=s["J"], sec=s, nome=nome)


def props_barra(d):
    A = math.pi * d ** 2 / 4
    return dict(E=E, G=GA, A=A, Iz=1e-12, Iy=1e-12, J=1e-12, nome=f"Ø{d*1000:.0f}")


RIGIDO = dict(E=E * 100, G=GA * 100, A=0.01, Iz=1e-4, Iy=1e-4, J=1e-4, nome="elo rígido")


def construir():
    P = Portico()
    xs, ys = R2["xs_pil"], R2["ys_pil"]
    xj = R2["xs_j"]
    pj, pv, pp = props(R2["perfil_joist"]), props(R2["perfil_viga"]), props(R2["perfil_pilar"])
    ppl, ppost = props("W150x13,0"), props("W150x22,5")
    t_ch = ESTR["chapa_piso_mm"] / 1000
    zj = TANQUE["cota_base"] - t_ch - pj["sec"]["d"] / 2           # eixo das secundárias
    zv = TANQUE["cota_base"] - t_ch - pj["sec"]["d"] - pv["sec"]["d"] / 2   # eixo das principais
    zb = ESTR["cota_topo_pedestal"] + ESTR["graute_mm"] / 1000      # base dos pilares
    # discretização das secundárias: nós a cada 0,22 m em Y
    ys_j = np.round(np.linspace(ys[0], ys[-1], 21), 6)
    for x in xj:
        nos = [P.no(x, y, zj) for y in ys_j]
        for a, b in zip(nos, nos[1:]):
            P.barra(a, b, pj, ref=(0, 0, 1), grupo="VS")
    # principais: nós em cada secundária
    for y in ys:
        nos = [P.no(x, y, zv) for x in xj]
        for a, b in zip(nos, nos[1:]):
            P.barra(a, b, pv, ref=(0, 0, 1), grupo="VP")
        for x in xj:
            P.barra(P.no(x, y, zv), P.no(x, y, zj), RIGIDO, ref=(1, 0, 0), grupo="ELO")
    # pilares
    for x in xs:
        for y in ys:
            nb = P.no(x, y, zb)
            P.barra(nb, P.no(x, y, zv), pp, ref=(1, 0, 0), grupo="PIL")
            P.apoios[nb] = [0, 1, 2]
    # contraventamento em X nas 4 faces (base de um pilar → topo do vizinho)
    br = props_barra(0.016)
    for y in (ys[0], ys[-1]):
        for i in range(2):
            P.barra(P.no(xs[i], y, zb), P.no(xs[i + 1], y, zv), br, grupo="CTV", tipo="truss")
            P.barra(P.no(xs[i + 1], y, zb), P.no(xs[i], y, zv), br, grupo="CTV", tipo="truss")
    for x in (xs[0], xs[-1]):
        for i in range(2):
            P.barra(P.no(x, ys[i], zb), P.no(x, ys[i + 1], zv), br, grupo="CTV", tipo="truss")
            P.barra(P.no(x, ys[i + 1], zb), P.no(x, ys[i], zv), br, grupo="CTV", tipo="truss")
    # plataforma de serviço (leste)
    xp = 82.9
    for y in ys:
        a, b = P.no(xs[-1], y, zv), P.no(xp, y, zv)
        mid = P.no((xs[-1] + xp) / 2, y, zv)
        P.barra(a, mid, ppl, ref=(0, 0, 1), grupo="VPL")
        P.barra(mid, b, ppl, ref=(0, 0, 1), grupo="VPL")
        nb = P.no(xp, y, zb)
        P.barra(nb, b, ppost, ref=(1, 0, 0), grupo="PST")
        P.apoios[nb] = [0, 1, 2]
    nos = [P.no(xp, y, zv) for y in np.linspace(ys[0], ys[-1], 5)]
    for a, b in zip(nos, nos[1:]):
        P.barra(a, b, ppl, ref=(0, 0, 1), grupo="VPL")
    # contraventamento da plataforma (faces norte e sul)
    for y in (ys[0], ys[-1]):
        P.barra(P.no(xs[-1], y, zb), P.no(xp, y, zv), br, grupo="CTV", tipo="truss")
        P.barra(P.no(xp, y, zb), P.no(xs[-1], y, zv), br, grupo="CTV", tipo="truss")
    meta = dict(zj=zj, zv=zv, zb=zb, xs=xs, ys=ys, xj=xj, ys_j=ys_j.tolist(), pj=pj, pv=pv, pp=pp)
    return P, meta


# ------------------------------------------------------------------ cargas
R = CAIXA_FORN["D_ext"] / 2
h_agua = NIVEIS["borda_cheio_total"] - TANQUE["cota_fundo_int"]
P_AGUA = GAMMA_W * h_agua
W_TQ = CAIXA_FORN["massa_vazia_kg"] * G / 1000
P_TQ = W_TQ / (math.pi * R ** 2)
P_CH = ESTR["chapa_piso_mm"] / 1000 * RHO_ACO * G / 1000 + ESTR["manta_kPa"]
F_TQ = RES["MC-02_estrutura_fundacao"].get("F_vento_caixa", 16.39)
M_DECK = RES["MC-02_estrutura_fundacao"].get("M_vento_deck", 36.87)
I_BASE = math.pi * R ** 4 / 4


def pressao(x, y, caso):
    dentro = (x - X_CAIXA) ** 2 + (y - Y_CAIXA) ** 2 <= R ** 2
    if caso == "G":
        return P_CH + (P_TQ if dentro else 0.0)
    if caso == "Q":
        return P_AGUA if dentro else 0.0
    if caso == "Wx":
        return M_DECK / I_BASE * (x - X_CAIXA) if dentro else 0.0
    if caso == "Wy":
        return M_DECK / I_BASE * (y - Y_CAIXA) if dentro else 0.0
    return 0.0


def cargas_caso(P, meta, caso):
    """Retorna (F nodal, w por elemento) do caso característico."""
    F = np.zeros(P.ndof())
    w = {}
    sj = ESTR["esp_joists"]
    x0, x1 = meta["xs"][0], meta["xs"][-1]
    for ie, e in enumerate(P.el):
        Xi, Xj = P.X[e["i"]], P.X[e["j"]]
        if caso == "G":   # peso próprio de todas as barras (exceto elos)
            if e["grupo"] not in ("ELO",):
                w[ie] = np.array([0, 0, -e["p"]["A"] * RHO_ACO * G / 1000])
        if e["grupo"] == "VS":
            xc = Xi[0]
            xa, xb = max(x0, xc - sj / 2), min(x1, xc + sj / 2)
            yc = 0.5 * (Xi[1] + Xj[1])
            xx = np.linspace(xa, xb, 25)
            q = float(np.trapezoid([pressao(xi, yc, caso) for xi in xx], xx))
            if q != 0.0:
                w[ie] = w.get(ie, np.zeros(3)) + np.array([0, 0, -q])
        if e["grupo"] == "VPL" and caso == "L":
            # plataforma 3 kPa; vigas em X recebem faixa de 2,2 m (central) ou 1,1 m (extremas)
            if abs(Xi[1] - Xj[1]) < 1e-6:
                trib = 2.2 if abs(Xi[1]) < 1e-6 else 1.1
                w[ie] = np.array([0, 0, -ESTR["sobrecarga_plataforma_kPa"] * trib / 2])
    if caso in ("Wx", "Wy"):
        # força horizontal do vento distribuída nos nós das secundárias sob a caixa (atrito/ancoragens)
        nos = [k for k, p in enumerate(P.X) if abs(p[2] - meta["zj"]) < 1e-6 and (p[0] - X_CAIXA) ** 2 + p[1] ** 2 <= R ** 2]
        d = 0 if caso == "Wx" else 1
        for k in nos:
            F[6 * k + d] += F_TQ / len(nos)
    return F, w


COMBOS = {
    "ELU-1 1,4G+1,5Q+1,4Wx+1,05L": {"G": 1.4, "Q": 1.5, "Wx": 1.4, "L": 1.05},
    "ELU-2 1,4G+1,5Q+1,4Wy+1,05L": {"G": 1.4, "Q": 1.5, "Wy": 1.4, "L": 1.05},
    "ELU-3 1,4G+1,5Q−1,4Wx+1,5L": {"G": 1.4, "Q": 1.5, "Wx": -1.4, "L": 1.5},
    "ELU-4 1,0G+1,4Wx (caixa vazia)": {"G": 1.0, "Wx": 1.4},
    "ELU-5 1,0G+1,4Wy (caixa vazia)": {"G": 1.0, "Wy": 1.4},
    "ELS G+Q+L": {"G": 1.0, "Q": 1.0, "L": 1.0},
}


def resolver_combo(P, meta, comb, casos):
    """Resolve combinação com iteração tração-somente nos contraventamentos."""
    for e in P.el:
        if e["tipo"] == "truss":
            e["ativo"] = True
    F = sum(casos[c][0] * g for c, g in comb.items())
    W = {}
    for c, g in comb.items():
        for ie, wv in casos[c][1].items():
            W[ie] = W.get(ie, np.zeros(3)) + g * wv
    for it in range(6):
        u, Rv, esf, fix = P.resolver(F, W)
        mudou = False
        for ie, e in enumerate(P.el):
            if e["tipo"] == "truss" and e["ativo"] and -esf[ie][0] < -1e-6:  # N < 0 compressão
                e["ativo"] = False
                mudou = True
        if not mudou:
            break
    return u, Rv, esf, it + 1, F, W


def verificar(P, meta, esf_env):
    """Taxas de utilização NBR 8800 por grupo, a partir dos esforços extremos por elemento."""
    out = {}
    Lb = {"VS": 1.10, "VP": 1.10, "PIL": None, "VPL": 1.10, "PST": None}
    for ie, e in enumerate(P.el):
        g = e["grupo"]
        if g in ("ELO",):
            continue
        f = esf_env[ie]
        N = max(f["Nt"], 0.0)
        Nc = max(-f["Nc"], 0.0)
        if e["tipo"] == "truss":
            A = e["p"]["A"]
            Rd = min(A * ACO_CHAPA["fy"] * 1e3 / GAMMA["a1"], 0.75 * A * ACO_CHAPA["fu"] * 1e3 / GAMMA["a2"])
            taxa = N / Rd
        else:
            s = e["p"]["sec"]
            L = np.linalg.norm(P.X[e["j"]] - P.X[e["i"]])
            Lmemb = L if g not in ("PIL", "PST") else L
            MRx, _ = EST.MRd_I(s, ACO_PERFIL["fy"], Lb[g] or Lmemb)
            MRy = min(s["Zy"], 1.5 * s["Wy"]) * ACO_PERFIL["fy"] * 1e3 / GAMMA["a1"]
            VR = EST.VRd_I(s, ACO_PERFIL["fy"])
            if Nc > 0:
                NR, _ = EST.NcRd_I(s, ACO_PERFIL["fy"], Lmemb, Lmemb, Lmemb)
                Nn = Nc
            else:
                NR = s["A"] * ACO_PERFIL["fy"] * 1e3 / GAMMA["a1"]
                Nn = N
            r = Nn / NR
            mm = f["Mz"] / MRx + f["My"] / MRy
            taxa = r + 8 / 9 * mm if r >= 0.2 else r / 2 + mm
            taxa = max(taxa, f["Vy"] / VR)
        if g not in out or taxa > out[g]["taxa"]:
            out[g] = dict(taxa=taxa, el=ie, perfil=e["p"]["nome"], **{k: round(v, 2) for k, v in f.items()})
    return out


def run(saida):
    os.makedirs(saida, exist_ok=True)
    P, meta = construir()
    casos = {c: cargas_caso(P, meta, c) for c in ["G", "Q", "Wx", "Wy", "L"]}
    res = {"n_nos": len(P.X), "n_elementos": len(P.el), "combos": {}}
    env = [dict(Nt=0.0, Nc=0.0, Vy=0.0, Vz=0.0, T=0.0, My=0.0, Mz=0.0) for _ in P.el]
    u_els = None
    reac_tab = {}
    for nome, comb in COMBOS.items():
        u, Rv, esf, it, F, W = resolver_combo(P, meta, comb, casos)
        # equilíbrio: soma das reações verticais = cargas verticais aplicadas
        aplicado = F[2::6].sum()
        for ie, wv in W.items():
            L = np.linalg.norm(P.X[P.el[ie]["j"]] - P.X[P.el[ie]["i"]])
            aplicado += wv[2] * L
        reacZ = sum(Rv[6 * n + 2] for n in P.apoios)
        uz = u[2::6]
        ux = u[0::6]
        uy = u[1::6]
        res["combos"][nome] = dict(iteracoes=it, soma_reacoes_Z=reacZ, cargas_Z=-aplicado,
                                   erro_equilibrio=abs(reacZ + aplicado), uz_min_mm=uz.min() * 1000,
                                   uh_max_mm=max(np.abs(ux).max(), np.abs(uy).max()) * 1000,
                                   diag_inativas=sum(1 for e in P.el if e["tipo"] == "truss" and not e["ativo"]))
        reac_tab[nome] = {f"{P.X[n][0]:.2f};{P.X[n][1]:.2f}": round(Rv[6 * n + 2], 1) for n in P.apoios}
        if nome.startswith("ELU"):
            for ie, f in enumerate(esf):
                env[ie]["Nt"] = max(env[ie]["Nt"], f[6], -f[0])
                env[ie]["Nc"] = min(env[ie]["Nc"], f[6], -f[0])
                env[ie]["Vy"] = max(env[ie]["Vy"], abs(f[1]), abs(f[7]))
                env[ie]["Vz"] = max(env[ie]["Vz"], abs(f[2]), abs(f[8]))
                env[ie]["T"] = max(env[ie]["T"], abs(f[3]))
                env[ie]["My"] = max(env[ie]["My"], abs(f[4]), abs(f[10]))
                env[ie]["Mz"] = max(env[ie]["Mz"], abs(f[5]), abs(f[11]))
        if nome.startswith("ELS"):
            u_els = u.copy()
            res["flechas_ELS"] = {}
            for g in ("VS", "VP"):
                nos = {P.el[k]["i"] for k, e in enumerate(P.el) if e["grupo"] == g} | {P.el[k]["j"] for k, e in enumerate(P.el) if e["grupo"] == g}
                res["flechas_ELS"][g] = float(-min(u[6 * n + 2] for n in nos) * 1000)
    # caso Q isolado (comparação com o modelo 1D)
    uQ, RQ, _, _, _, _ = resolver_combo(P, meta, {"Q": 1.0}, casos)
    res["reacoes_Q"] = {f"{P.X[n][0]:.2f};{P.X[n][1]:.2f}": round(RQ[6 * n + 2], 1) for n in P.apoios}
    res["reacoes_por_combo"] = reac_tab
    res["verificacao"] = verificar(P, meta, env)
    # modal: massa da água + caixa concentrada nos nós das secundárias (sem sloshing)
    mextra = {}
    sj = ESTR["esp_joists"]
    for k, p in enumerate(P.X):
        if abs(p[2] - meta["zj"]) < 1e-6:
            dy = (meta["ys"][-1] - meta["ys"][0]) / 20
            m = 0.0
            for yy in np.linspace(p[1] - dy / 2, p[1] + dy / 2, 5):
                for xx in np.linspace(p[0] - sj / 2, p[0] + sj / 2, 5):
                    m += (pressao(xx, yy, "Q") + pressao(xx, yy, "G")) / G * (dy / 5) * (sj / 5)
            mextra[k] = m  # t (kN/g)
    M = P.massa_lumped(mextra, RHO_ACO / 1000)
    for e in P.el:
        if e["tipo"] == "truss":
            e["ativo"] = True
    modos = P.modal(M, 6)
    res["massa_total_t"] = float(M[0::6].sum())
    res["modos_Hz"] = [round(fz, 2) for fz, _ in modos]
    res["modos_desc"] = []
    for fz, phi in modos:
        dx, dy, dz = np.abs(phi[0::6]).max(), np.abs(phi[1::6]).max(), np.abs(phi[2::6]).max()
        res["modos_desc"].append(["X", "Y", "Z"][int(np.argmax([dx, dy, dz]))])
    json.dump(res, open(os.path.join(saida, "FEA-01_portico.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=float)
    desenho_deformada(P, meta, u_els, res, os.path.join(saida, "FEA-01_deformada_ELS.png"))
    desenho_utilizacao(P, meta, env, os.path.join(saida, "FEA-01_utilizacao_ELU.png"))
    return res, P, meta


# ------------------------------------------------------------------ figuras (PIL, isométrica)
def _proj(p, esc, ox, oy, z0=112.0):
    x, y, z = p[0] - X_CAIXA, p[1], p[2] - z0
    sx = (x - y) * math.cos(math.radians(30))
    sy = (x + y) * math.sin(math.radians(30)) + z * 2.2
    return ox + sx * esc, oy - sy * esc


def _fonte(t):
    from PIL import ImageFont
    for f in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, t)
        except Exception:
            pass
    return ImageFont.load_default()


def desenho_deformada(P, meta, u, res, arq):
    from PIL import Image, ImageDraw
    W, H = 1600, 1000
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    esc, ox, oy = 150, 820, 700
    amp = 150.0
    for e in P.el:
        if e["grupo"] == "ELO":
            continue
        a, b = P.X[e["i"]], P.X[e["j"]]
        d.line([_proj(a, esc, ox, oy), _proj(b, esc, ox, oy)], fill=(190, 196, 204), width=2)
    uz = u[2::6]
    vmax = np.abs(uz).max()
    for e in P.el:
        if e["grupo"] == "ELO":
            continue
        a = P.X[e["i"]] + amp * u[6 * e["i"]:6 * e["i"] + 3]
        b = P.X[e["j"]] + amp * u[6 * e["j"]:6 * e["j"] + 3]
        v = (abs(uz[e["i"]]) + abs(uz[e["j"]])) / 2 / vmax
        cor = (int(30 + 210 * v), int(90 + 60 * (1 - v)), int(200 * (1 - v)))
        d.line([_proj(a, esc, ox, oy), _proj(b, esc, ox, oy)], fill=cor, width=3 if e["tipo"] == "frame" else 1)
    d.text((40, 30), "FEA-01 — Pórtico espacial: deformada ELS (G + Q + L), ampliação ×150", fill="black", font=_fonte(30))
    d.text((40, 75), f"Deslocamento vertical máx.: {vmax*1000:.2f} mm  |  cinza = geometria original  |  cor: azul → vermelho = |uz| crescente",
           fill=(60, 60, 60), font=_fonte(20))
    d.text((40, 105), f"{res['n_nos']} nós, {res['n_elementos']} elementos; modos: " + ", ".join(f"{f:.1f} Hz ({m})" for f, m in zip(res['modos_Hz'][:3], res['modos_desc'][:3])),
           fill=(60, 60, 60), font=_fonte(20))
    img.save(arq)


def desenho_utilizacao(P, meta, env, arq):
    from PIL import Image, ImageDraw
    W, H = 1600, 1000
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    esc, ox, oy = 150, 820, 700
    ver = {}
    for ie, e in enumerate(P.el):
        if e["grupo"] == "ELO":
            continue
        t = verificar_el(P, ie, env[ie])
        ver[ie] = t
        a, b = P.X[e["i"]], P.X[e["j"]]
        r = min(t, 1.2) / 1.0
        cor = (40, 150, 70) if t < 0.5 else ((230, 170, 30) if t < 0.85 else ((230, 90, 30) if t <= 1.0 else (200, 0, 0)))
        d.line([_proj(a, esc, ox, oy), _proj(b, esc, ox, oy)], fill=cor, width=5 if e["tipo"] == "frame" else 2)
    d.text((40, 30), "FEA-01 — Taxa de utilização (envoltória ELU, NBR 8800: N + M + V)", fill="black", font=_fonte(30))
    legenda = [((40, 150, 70), "< 0,50"), ((230, 170, 30), "0,50–0,85"), ((230, 90, 30), "0,85–1,00"), ((200, 0, 0), "> 1,00")]
    for k, (c, txt) in enumerate(legenda):
        d.rectangle([40 + k * 190, 80, 70 + k * 190, 100], fill=c)
        d.text((80 + k * 190, 76), txt, fill="black", font=_fonte(20))
    d.text((40, 115), f"Máxima: {max(ver.values()):.2f}", fill=(60, 60, 60), font=_fonte(20))
    img.save(arq)


def verificar_el(P, ie, f):
    tmp = {ie: f}
    e = P.el[ie]
    out = verificar(type("X", (), {"el": [e], "X": P.X})(), None, [f]) if False else None
    # reutiliza a função de grupo com um único elemento
    g = verificar(_Um(P, ie), None, [f])
    return list(g.values())[0]["taxa"] if g else 0.0


class _Um:
    def __init__(self, P, ie):
        self.el = [P.el[ie]]
        self.X = P.X


if __name__ == "__main__":
    r, _, _ = run(os.path.join(AQUI, "resultados"))
    print(json.dumps({k: v for k, v in r.items() if k not in ("reacoes_por_combo",)}, indent=1, ensure_ascii=False, default=float)[:3000])
