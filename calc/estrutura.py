# -*- coding: utf-8 -*-
"""Memória de cálculo da estrutura metálica, ligações, apoios e fundação (pré-dimensionamento).

Método: vigas resolvidas por elementos finitos de barra (Euler-Bernoulli, numpy), com a pressão
da caixa aplicada apenas na projeção circular (Ø 4,00 m). Verificações conforme ABNT NBR 8800
(formulação do Anexo G para FLT/FLM/FLA, compressão com curva única χ) e combinações conforme
ABNT NBR 8681 / NBR 8800 (Tabela 1). Vento conforme formulação da ABNT NBR 6123:1988 (edição substituída pela de 12/2023 — ver relatório).
"""
import math
import numpy as np
from premissas import *
from memo import Memo, f

E = E_ACO * 1e3      # kN/m²  (MPa -> kPa)
GA = G_ACO * 1e3


# ======================================================================= seções
def props_I(nome):
    d, bf, tw, tf = [x / 1000 for x in PERFIS_W[nome]]
    h = d - 2 * tf
    A = 2 * bf * tf + h * tw
    Ix = (bf * d ** 3 - (bf - tw) * h ** 3) / 12
    Iy = 2 * tf * bf ** 3 / 12 + h * tw ** 3 / 12
    Zx = bf * tf * (d - tf) + tw * h ** 2 / 4
    Zy = tf * bf ** 2 / 2 + h * tw ** 2 / 4
    Wx = 2 * Ix / d
    Wy = 2 * Iy / bf
    J = (2 * bf * tf ** 3 + (d - tf) * tw ** 3) / 3
    Cw = Iy * (d - tf) ** 2 / 4
    return dict(nome=nome, d=d, bf=bf, tw=tw, tf=tf, h=h, A=A, Ix=Ix, Iy=Iy, Zx=Zx, Zy=Zy, Wx=Wx, Wy=Wy,
                J=J, Cw=Cw, rx=math.sqrt(Ix / A), ry=math.sqrt(Iy / A), massa=A * RHO_ACO)


def MRd_I(s, fy, Lb, Cb=1.0):
    """Momento resistente de cálculo (kN·m) — NBR 8800 Anexo G, perfil I duplamente simétrico laminado."""
    fy = fy * 1e3
    sr = 0.3 * fy
    Mpl = s["Zx"] * fy
    # FLT
    lam = Lb / s["ry"]
    lp = 1.76 * math.sqrt(E / fy)
    b1 = (fy - sr) * s["Wx"] / (E * s["J"])
    lr = 1.38 * math.sqrt(s["Iy"] * s["J"]) / (s["ry"] * s["J"] * b1) * math.sqrt(1 + math.sqrt(1 + 27 * s["Cw"] * b1 ** 2 / s["Iy"]))
    Mr = (fy - sr) * s["Wx"]
    if lam <= lp:
        Mflt = Mpl
    elif lam <= lr:
        Mflt = min(Mpl, Cb * (Mpl - (Mpl - Mr) * (lam - lp) / (lr - lp)))
    else:
        Mcr = Cb * math.pi ** 2 * E * s["Iy"] / Lb ** 2 * math.sqrt(s["Cw"] / s["Iy"] * (1 + 0.039 * s["J"] * Lb ** 2 / s["Cw"]))
        Mflt = min(Mpl, Mcr)
    # FLM
    lam = s["bf"] / (2 * s["tf"])
    lp = 0.38 * math.sqrt(E / fy)
    lr = 0.83 * math.sqrt(E / (fy - sr))
    if lam <= lp:
        Mflm = Mpl
    elif lam <= lr:
        Mflm = Mpl - (Mpl - Mr) * (lam - lp) / (lr - lp)
    else:
        Mflm = 0.69 * E * s["Wx"] / lam ** 2
    # FLA
    lam = s["h"] / s["tw"]
    lp = 3.76 * math.sqrt(E / fy)
    Mfla = Mpl if lam <= lp else fy * s["Wx"]
    MRk = min(Mflt, Mflm, Mfla, 1.5 * s["Wx"] * fy)
    return MRk / GAMMA["a1"], dict(FLT=Mflt / GAMMA["a1"], FLM=Mflm / GAMMA["a1"], FLA=Mfla / GAMMA["a1"])


def VRd_I(s, fy):
    fy = fy * 1e3
    Aw = s["d"] * s["tw"]
    lam = s["h"] / s["tw"]
    lp = 1.10 * math.sqrt(5 * E / fy)
    lr = 1.37 * math.sqrt(5 * E / fy)
    Vpl = 0.6 * Aw * fy
    if lam <= lp:
        return Vpl / GAMMA["a1"]
    if lam <= lr:
        return lp / lam * Vpl / GAMMA["a1"]
    return 1.24 * (lp / lam) ** 2 * Vpl / GAMMA["a1"]


def NcRd_I(s, fy, Lx, Ly, Lz):
    fy = fy * 1e3
    # flambagem local (Q)
    Q = 1.0
    if s["bf"] / (2 * s["tf"]) > 0.56 * math.sqrt(E / fy) or s["h"] / s["tw"] > 1.49 * math.sqrt(E / fy):
        Q = 0.9  # conservador; perfis adotados atendem (verificado abaixo)
    Nex = math.pi ** 2 * E * s["Ix"] / Lx ** 2
    Ney = math.pi ** 2 * E * s["Iy"] / Ly ** 2
    r0sq = s["rx"] ** 2 + s["ry"] ** 2
    Nez = (math.pi ** 2 * E * s["Cw"] / Lz ** 2 + GA * s["J"]) / r0sq
    Ne = min(Nex, Ney, Nez)
    l0 = math.sqrt(Q * s["A"] * fy / Ne)
    chi = 0.658 ** (l0 ** 2) if l0 <= 1.5 else 0.877 / l0 ** 2
    return chi * Q * s["A"] * fy / GAMMA["a1"], dict(Q=Q, lambda0=l0, chi=chi)


# ======================================================================= FE de viga contínua
def viga_continua(L, apoios, carga, EI, n=440):
    """L: comprimento; apoios: posições (m) com restrição vertical; carga: lista de funções
    q(x) (kN/m) e/ou cargas pontuais [(x,P)]. Retorna dict com x, M, V, deflexão, reações."""
    x = np.linspace(0, L, n + 1)
    nn = len(x)
    K = np.zeros((2 * nn, 2 * nn))
    F = np.zeros(2 * nn)
    for e in range(n):
        le = x[e + 1] - x[e]
        k = EI / le ** 3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
                                     [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]])
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        K[np.ix_(idx, idx)] += k
        xm = 0.5 * (x[e] + x[e + 1])
        q = carga["q"](xm) if "q" in carga else 0.0
        F[idx] += np.array([q * le / 2, q * le ** 2 / 12, q * le / 2, -q * le ** 2 / 12]) * -1  # carga para baixo
    for (xp, P) in carga.get("P", []):
        i = int(np.argmin(np.abs(x - xp)))
        F[2 * i] -= P
    sup = [int(np.argmin(np.abs(x - a))) for a in apoios]
    fix = [2 * i for i in sup]
    free = [i for i in range(2 * nn) if i not in fix]
    u = np.zeros(2 * nn)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], F[free])
    R = K @ u - F
    reac = [R[2 * i] for i in sup]
    # esforços internos por equilíbrio a partir da esquerda
    M = np.zeros(nn)
    V = np.zeros(nn)
    for e in range(n):
        le = x[e + 1] - x[e]
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        k = EI / le ** 3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
                                     [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]])
        xm = 0.5 * (x[e] + x[e + 1])
        q = carga["q"](xm) if "q" in carga else 0.0
        fe0 = np.array([q * le / 2, q * le ** 2 / 12, q * le / 2, -q * le ** 2 / 12]) * -1
        fe = k @ u[idx] - fe0
        V[e] = fe[0]
        M[e] = -fe[1]
        if e == n - 1:
            V[e + 1] = -fe[2]
            M[e + 1] = fe[3]
    return dict(x=x, M=M, V=V, w=u[0::2], reac=reac)


# ======================================================================= cálculo principal
def run():
    m = Memo("Memória de Cálculo — Estrutura Metálica, Ligações e Fundação (preliminar)")
    m.p("Ferramenta: Python 3.12 + numpy — solver próprio de viga contínua por elementos finitos "
        "(Euler-Bernoulli, 440 elementos por viga), verificado contra solução analítica de viga contínua de 2 vãos "
        "(ver item 9). Perfis com propriedades calculadas a partir das dimensões nominais (d, bf, tw, tf), "
        "sem raios de concordância (conservador). **Pré-dimensionamento para estudo — não liberar para fabricação.**")

    # ------------------------------------------------------------ geometria
    Ld = ESTR["lado_deck"]
    x0 = X_CAIXA - Ld / 2
    y0 = Y_CAIXA - Ld / 2
    xs_pil = [x0, x0 + Ld / 2, x0 + Ld]
    ys_pil = [y0, y0 + Ld / 2, y0 + Ld]
    n_j = int(round(Ld / ESTR["esp_joists"])) + 1
    xs_j = [x0 + i * ESTR["esp_joists"] for i in range(n_j)]
    R = CAIXA_FORN["D_ext"] / 2
    m.h("1. Configuração estrutural adotada")
    m.p(f"Plataforma quadrada {f(Ld,2)} × {f(Ld,2)} m com chapa de piso contínua (apoio plano integral da base da caixa), "
        f"sobre {n_j} vigas secundárias (direção Y, espaçamento {f(ESTR['esp_joists'],2)} m, contínuas sobre 3 apoios), "
        "apoiadas em 3 vigas principais (direção X, contínuas sobre 3 pilares), 9 pilares curtos (grelha 3×3, vão 2,20 m), "
        "contraventamento em X nas 4 faces, placas de base com chumbadores sobre pedestais de um radier de concreto armado. "
        "Plataforma de serviço de 1,10 m no lado leste (acesso a registros dos bocais e à escada da caixa).")
    m.p("Justificativa: (a) a forma de apoio exigida pelo fabricante não é conhecida; o apoio plano contínuo atende ao "
        "caso mais exigente usual de caixas de fundo plano e também a apoio por anel (com reverificação); "
        "(b) a grelha 3×3 limita vãos a 2,20 m, reduzindo altura dos perfis — importante porque a base da caixa está a "
        "apenas 1,50 m do terreno; (c) ligações parafusadas permitem galvanização a fogo de todas as peças.")

    # ------------------------------------------------------------ ações
    m.h("2. Ações características")
    h_agua = NIVEIS["borda_cheio_total"] - TANQUE["cota_fundo_int"]
    p_agua = GAMMA_W * h_agua
    m.calc("Altura de água máxima (até a borda — extravasor obstruído)", "h = 117,95 − 113,55", "", h_agua, "m", 2)
    m.calc("Pressão hidrostática no fundo", "p = γw·h", f"9,81·{f(h_agua,2)}", p_agua, "kPa", 2, "p_agua")
    A_base = math.pi * R ** 2
    W_agua = p_agua * A_base
    m.calc("Peso da água (sobre a projeção Ø4,00 — conservador)", "W = p·π·R²", f"{f(p_agua,2)}·{f(A_base,3)}", W_agua, "kN", 1, "W_agua")
    W_tq = CAIXA_FORN["massa_vazia_kg"] * G / 1000
    m.calc("Peso da caixa vazia", "W = 1200·9,81", "", W_tq, "kN", 2, "W_tanque")
    p_tq = W_tq / A_base
    p_chapa = ESTR["chapa_piso_mm"] / 1000 * RHO_ACO * G / 1000
    m.calc("Peso da chapa de piso", "g = t·ρ·g", "", p_chapa, "kPa", 3)
    m.p("Hipóteses: o peso da caixa foi distribuído uniformemente na base (conservador para vigas centrais; "
        "se o fabricante indicar carga concentrada no costado, reverificar as vigas sob o perímetro). "
        "Água considerada até a borda (caso físico máximo) com γq = 1,50 (sem o benefício de 'ação truncada', "
        "que permitiria 1,20 — decisão conservadora a revisar no executivo).")

    # vento
    m.h("2.1 Vento (formulação da NBR 6123:1988 — a edição vigente é 12/2023 com errata 04/2025; refazer no executivo)", 3)
    V = VENTO
    z_top = CAIXA_FORN["base_acima_terreno"] + CAIXA_FORN["H_ext"]
    S2 = V["b"] * V["Fr"] * (z_top / 10) ** V["p"]
    m.calc("S2 (cat. II, classe A, z = 6,0 m)", "S2 = b·Fr·(z/10)^p", f"1,00·1,00·(6,0/10)^0,085", S2, "-", 3)
    Vk = V["V0"] * V["S1"] * S2 * V["S3"]
    m.calc("Velocidade característica", "Vk = V0·S1·S2·S3", f"{f(V['V0'],0)}·1,0·{f(S2,3)}·1,0", Vk, "m/s", 1, "Vk")
    q = 0.613 * Vk ** 2 / 1000
    m.calc("Pressão dinâmica", "q = 0,613·Vk²", "", q, "kPa", 3, "q_vento")
    A_tq = CAIXA_FORN["D_ext"] * CAIXA_FORN["H_ext"]
    F_tq = V["Ca_cilindro"] * q * A_tq
    m.calc("Força na caixa", "F = Ca·q·Ae", f"{f(V['Ca_cilindro'],2)}·{f(q,3)}·{f(A_tq,1)}", F_tq, "kN", 2, "F_vento_caixa")
    F_esc = V["Ca_escada"] * q * V["A_escada_m2"]
    F_estr = 0.10 * F_tq
    m.calc("Força na escada/gaiola e estrutura (estimativa)", "F = Ca·q·A + 10 %·F_caixa", "", F_esc + F_estr, "kN", 2)
    Fw = F_tq + F_esc + F_estr
    m.calc("Força horizontal total de vento", "", "", Fw, "kN", 2, "F_vento_total")
    S1b = 1.1
    m.p(f"Sensibilidade: com S1 = 1,10 (encosta) a força cresce {f((S1b**2-1)*100,0)} %; com V0 = 40 m/s reduz "
        f"{f((1-(40/45)**2)*100,0)} %. O efeito é pequeno frente ao peso da água, mas é **governante para a caixa vazia**.")
    zc_tq = CAIXA_FORN["H_ext"] / 2
    M_deck = F_tq * zc_tq
    m.calc("Momento do vento na base da caixa (deck)", "M = F·h/2", f"{f(F_tq,2)}·{f(zc_tq,2)}", M_deck, "kN·m", 2, "M_vento_deck")

    # estabilidade da caixa vazia
    m.h("2.2 Estabilidade da caixa vazia sobre o deck", 3)
    Mest = W_tq * R
    m.calc("Momento estabilizante (caixa vazia)", "Me = W·R", f"{f(W_tq,2)}·2,0", Mest, "kN·m", 2)
    m.calc("Coeficiente ao tombamento sem ancoragem", "Me/Mt", "", Mest / M_deck, "-", 2, ok=Mest / M_deck >= 1.5)
    m.calc("Deslizamento sem ancoragem (μ = 0,3 [H])", "μ·W/F", "", 0.3 * W_tq / F_tq, "-", 2, ok=0.3 * W_tq / F_tq >= 1.5)
    n_anc = 8
    R_anc = R + 0.05
    Td = GAMMA["w"] * M_deck / (4 * R_anc) - GAMMA["g_fav"] * W_tq / n_anc
    Vd_anc = GAMMA["w"] * F_tq / n_anc
    m.calc("Tração de cálculo por ancoragem (8 pontos no perímetro)", "Td = 1,4·M/(4·R) − 1,0·W/8",
           f"1,4·{f(M_deck,2)}/(4·{f(R_anc,2)}) − {f(W_tq,2)}/8", Td, "kN", 2, "T_ancoragem_caixa")
    m.calc("Cisalhamento de cálculo por ancoragem", "Vd = 1,4·F/8", "", Vd_anc, "kN", 2, "V_ancoragem_caixa")
    m.p("**Conclusão: a caixa vazia tomba e desliza com o vento de projeto se não for ancorada.** São necessárias "
        "ancoragens (olhais/abas do fabricante ou cintas) fixadas ao deck — dado obrigatório a solicitar ao fornecedor "
        "(pontos, cargas admissíveis, tipo de fixação). Pré-dimensionamento: 8 pontos, cada um com Td ≈ 5 kN e "
        "Vd ≈ 3 kN; chapa-olhal 9,5 mm soldada em fábrica ao vigamento (antes da galvanização) com 1 parafuso M16.")

    # ------------------------------------------------------------ deck (chapa)
    m.h("3. Chapa de piso (apoio da caixa)")
    t = ESTR["chapa_piso_mm"] / 1000
    s_j = ESTR["esp_joists"]
    q_g = p_tq + p_chapa + ESTR["manta_kPa"]
    q_d = GAMMA["q_agua"] * p_agua + GAMMA["g"] * q_g
    q_s = p_agua + q_g
    m.calc("Carga de cálculo na chapa", "qd = 1,5·p_água + 1,4·g", f"1,5·{f(p_agua,2)} + 1,4·{f(q_g,3)}", q_d, "kPa", 2)
    Md = q_d * s_j ** 2 / 8
    MRd = ACO_CHAPA["fy"] * 1e3 * t ** 2 / 4 / GAMMA["a1"]
    m.calc("Momento solicitante (faixa de 1 m, biapoiada — conservador)", "Md = qd·s²/8", "", Md, "kN·m/m", 3)
    m.calc("Momento resistente plástico", "MRd = fy·t²/4/γa1", "", MRd, "kN·m/m", 3, ok=Md <= MRd)
    I_ch = t ** 3 / 12
    w_ch = 5 * q_s * s_j ** 4 / (384 * E * I_ch)
    m.calc("Flecha (serviço, biapoiada — conservador)", "δ = 5qL⁴/384EI", "", w_ch * 1000, "mm", 2, "flecha_chapa_mm")
    m.calc("Limite adotado L/250", "", "", s_j / 250 * 1000, "mm", 2, ok=w_ch <= s_j / 250)
    m.p("A planicidade/tolerância de apoio exigida pela caixa deve ser confirmada com o fornecedor. Parafusos da chapa "
        "com cabeça escareada (rente), para não criar pontos de carga no fundo da caixa.")

    # ------------------------------------------------------------ vigas secundárias
    m.h("4. Vigas secundárias (direção Y)")

    def p_tanque(xx, yy, caso):
        """Pressão (kPa) do caso de carga característico sobre o deck."""
        dentro = (xx - X_CAIXA) ** 2 + (yy - Y_CAIXA) ** 2 <= R ** 2
        if caso == "G":
            return p_chapa + ESTR["manta_kPa"] + (p_tq if dentro else 0.0)
        if caso == "Q":
            return p_agua if dentro else 0.0
        if caso == "Wx":  # binário do vento ao longo de +X sobre a base (caixa cheia: redistribuição linear)
            Ib = math.pi * R ** 4 / 4
            return (M_deck / Ib * (xx - X_CAIXA)) if dentro else 0.0
        if caso == "Wy":
            Ib = math.pi * R ** 4 / 4
            return (M_deck / Ib * (yy - Y_CAIXA)) if dentro else 0.0
        return 0.0

    def q_joist(xj, caso):
        xa = max(x0, xj - s_j / 2)
        xb = min(x0 + Ld, xj + s_j / 2)
        xx = np.linspace(xa, xb, 41)
        cache = {}

        def q(y):
            k = round(y, 6)
            if k not in cache:
                cache[k] = float(np.trapezoid([p_tanque(xi, y0 + y, caso) for xi in xx], xx))
            return cache[k]
        return {"q": q}

    combos = {"ELU1 (1,4G+1,5Q+1,4Wx)": {"G": 1.4, "Q": 1.5, "Wx": 1.4},
              "ELU2 (1,4G+1,5Q+1,4Wy)": {"G": 1.4, "Q": 1.5, "Wy": 1.4},
              "ELS (G+Q)": {"G": 1.0, "Q": 1.0}}

    def analisa_familia(perfil, posicoes, Lviga, apoios_rel, cargas_fn):
        s = props_I(perfil)
        EI = E * s["Ix"]
        res_caso = {}
        for caso in ["G", "Q", "Wx", "Wy"]:
            res_caso[caso] = [viga_continua(Lviga, apoios_rel, cargas_fn(pos, caso), EI) for pos in posicoes]
        return s, res_caso

    def combina(res_caso, comb, i):
        out = None
        for caso, gam in comb.items():
            r = res_caso[caso][i]
            if out is None:
                out = {k: (np.array(v) * gam if k != "x" else v) for k, v in r.items()}
            else:
                for k in ["M", "V", "w", "reac"]:
                    out[k] = out[k] + np.array(r[k]) * gam
        return out

    def escolhe(candidatos, posicoes, Lviga, apoios_rel, cargas_fn, Lb, lim_flecha, rotulo):
        for perfil in candidatos:
            s, rc = analisa_familia(perfil, posicoes, Lviga, apoios_rel, cargas_fn)
            Mmax = Vmax = wmax = 0.0
            for cn, comb in combos.items():
                for i in range(len(posicoes)):
                    r = combina(rc, comb, i)
                    if cn.startswith("ELS"):
                        wmax = max(wmax, float(np.max(np.abs(r["w"]))))
                    else:
                        Mmax = max(Mmax, float(np.max(np.abs(r["M"]))))
                        Vmax = max(Vmax, float(np.max(np.abs(r["V"]))))
            # peso próprio do perfil (pequeno): acréscimo analítico 2 vãos
            gpp = s["massa"] * G / 1000 * GAMMA["g"]
            Lv = Lviga / 2
            Mmax += gpp * Lv ** 2 / 8
            Vmax += 0.625 * gpp * Lv
            MRd, det = MRd_I(s, ACO_PERFIL["fy"], Lb)
            VRd = VRd_I(s, ACO_PERFIL["fy"])
            ok = Mmax <= MRd and Vmax <= VRd and wmax <= lim_flecha
            if ok:
                return perfil, s, rc, dict(Mmax=Mmax, Vmax=Vmax, wmax=wmax, MRd=MRd, VRd=VRd, det=det)
        raise RuntimeError(f"nenhum perfil atende — {rotulo}")

    cand_j = ["W150x13,0", "W150x18,0", "W200x19,3", "W200x26,6"]
    Lb_j = 1.10  # mesa inferior comprimida junto ao apoio central (conservador: L/2)
    pj, sj, rcj, chk_j = escolhe(cand_j, xs_j, Ld, [0, Ld / 2, Ld], q_joist, Lb_j, (Ld / 2) / 350, "secundárias")
    m.p(f"Perfil selecionado (o mais leve da lista {', '.join(cand_j)} que atende): **{pj}** — ASTM A572 Gr.50.")
    m.calc("Momento solicitante máximo (envoltória ELU)", "", "", chk_j["Mmax"], "kN·m", 2, "Md_joist")
    m.calc(f"Momento resistente (Lb = {f(Lb_j,2)} m, Cb = 1)", "MRd = min(FLT, FLM, FLA)",
           f"FLT {f(chk_j['det']['FLT'],1)}; FLM {f(chk_j['det']['FLM'],1)}; FLA {f(chk_j['det']['FLA'],1)}", chk_j["MRd"], "kN·m", 2, ok=True)
    m.calc("Cortante solicitante máximo", "", "", chk_j["Vmax"], "kN", 2)
    m.calc("Cortante resistente", "VRd = 0,6·fy·d·tw/γa1", "", chk_j["VRd"], "kN", 1, ok=True)
    m.calc("Flecha máxima (ELS, G+Q)", "", "", chk_j["wmax"] * 1000, "mm", 2, "flecha_joist_mm")
    m.calc("Limite L/350 (NBR 8800 Anexo C)", "", "", Ld / 2 / 350 * 1000, "mm", 2, ok=True)
    # reações das secundárias -> cargas nas vigas principais
    reac_j = {}
    for caso in ["G", "Q", "Wx", "Wy"]:
        reac_j[caso] = [r["reac"] for r in rcj[caso]]  # [j][apoio 0,1,2]
    gpp_j = sj["massa"] * G / 1000
    Rj_max_elu = max(max(combina(rcj, c, i)["reac"]) for c in list(combos.values())[:2] for i in range(n_j))
    m.calc("Reação máxima de cálculo de uma secundária sobre a viga principal", "", "", Rj_max_elu, "kN", 1, "Rj_max")
    # verificação de alma (escoamento local / enrugamento) no apoio central
    tw, tf_, d_ = sj["tw"], sj["tf"], sj["d"]
    lb_ap = props_I(ESTR["perfil_viga"])["bf"]
    fyk = ACO_PERFIL["fy"] * 1e3
    Rn_esc = (5 * tf_ + lb_ap) * fyk * tw / GAMMA["a1"]
    Rn_enr = 0.80 * tw ** 2 * (1 + 3 * (lb_ap / d_) * (tw / tf_) ** 1.5) * math.sqrt(E * fyk * tf_ / tw) / GAMMA["a1"]
    m.calc("Escoamento local da alma no apoio central", "FRd = (5k + lb)·fy·tw/γa1", "", Rn_esc, "kN", 1, ok=Rj_max_elu <= Rn_esc)
    m.calc("Enrugamento da alma", "FRd = 0,80·tw²·[1+3(lb/d)(tw/tf)^1,5]·√(E·fy·tf/tw)/γa1", "", Rn_enr, "kN", 1, ok=Rj_max_elu <= Rn_enr)

    # ------------------------------------------------------------ vigas principais
    m.h("5. Vigas principais (direção X)")
    ys_rel = [0, Ld / 2, Ld]

    def cargas_viga(iy, caso):
        P = []
        for j, xj in enumerate(xs_j):
            Rv = reac_j[caso][j][iy]
            if caso == "G":
                pass
            P.append((xj - x0, Rv))
        return {"P": P}

    cand_v = ["W200x26,6", "W200x31,3", "W200x35,9", "W250x32,7", "W250x38,5"]
    Lb_v = 0.44  # mesa superior travada pelas secundárias; inferior: conservador 0,44 m entre secundárias? (ver nota)
    # verificação com Lb = 1,10 m (mesa inferior comprimida junto ao pilar central, sem travamento)
    pv, sv, rcv, chk_v = escolhe(cand_v, [0, 1, 2], Ld, [0, Ld / 2, Ld], cargas_viga, 1.10, (Ld / 2) / 350, "principais")
    m.p(f"Perfil selecionado (o mais leve da lista {', '.join(cand_v)} que atende): **{pv}** — ASTM A572 Gr.50. "
        "Cargas = reações das 11 secundárias (cargas concentradas a cada 0,44 m).")
    m.calc("Momento solicitante máximo (envoltória ELU)", "", "", chk_v["Mmax"], "kN·m", 2, "Md_viga")
    m.calc("Momento resistente (Lb = 1,10 m)", "", f"FLT {f(chk_v['det']['FLT'],1)}; FLM {f(chk_v['det']['FLM'],1)}; FLA {f(chk_v['det']['FLA'],1)}", chk_v["MRd"], "kN·m", 2, ok=True)
    m.calc("Cortante solicitante máximo", "", "", chk_v["Vmax"], "kN", 1)
    m.calc("Cortante resistente", "", "", chk_v["VRd"], "kN", 1, ok=True)
    m.calc("Flecha máxima (ELS)", "", "", chk_v["wmax"] * 1000, "mm", 2, "flecha_viga_mm")
    m.calc("Limite L/350", "", "", Ld / 2 / 350 * 1000, "mm", 2, ok=True)
    m.p("Enrijecedores de apoio (chapas 9,5 mm, ambos os lados da alma) sobre cada pilar e nas cargas concentradas "
        "das secundárias alinhadas com pilares — boa prática obrigatória pela alta reação no pilar central.")

    # ------------------------------------------------------------ reações nos pilares
    m.h("6. Pilares, contraventamento, placas de base e chumbadores")
    gpp_v = sv["massa"] * G / 1000
    reac_p = {}
    for caso in ["G", "Q", "Wx", "Wy"]:
        reac_p[caso] = np.array([rcv[caso][iy]["reac"] for iy in range(3)])  # [iy][ix]
    # peso próprio de vigas principais + secundárias (adiciona ao G de forma simples por área de influência)
    peso_estr_deck = (n_j * Ld * gpp_j + 3 * Ld * gpp_v)
    infl = np.array([[0.25, 0.5, 0.25], [0.5, 1.0, 0.5], [0.25, 0.5, 0.25]]) / 4.0  # área de influência normalizada
    reac_p["G"] = reac_p["G"] + peso_estr_deck * infl
    m.p("Reações características nos pilares (kN) — linhas = eixo Y (sul→norte), colunas = eixo X (oeste→leste):")
    for caso, nome in [("G", "Permanente G (caixa vazia + estrutura + chapa)"), ("Q", "Água até a borda Q")]:
        m.p(f"*{nome}*")
        m.tabela(["", "X1", "X2", "X3"], [[f"Y{i+1}"] + [f(v, 1) for v in reac_p[caso][i]] for i in range(3)])
    tot_G = float(reac_p["G"].sum())
    tot_Q = float(reac_p["Q"].sum())
    m.calc("Soma das reações G", "", "", tot_G, "kN", 1, "soma_G")
    m.calc("Soma das reações Q (confere com W_água)", "", f"W_água = {f(W_agua,1)}", tot_Q, "kN", 1, "soma_Q", ok=abs(tot_Q - W_agua) / W_agua < 0.01)
    # vento global (binário nos pilares: rígido) — para caixa VAZIA o momento chega via ancoragens
    z_base_col = ESTR["cota_topo_pedestal"] + ESTR["graute_mm"] / 1000
    h_col = (TANQUE["cota_base"] - ESTR["chapa_piso_mm"] / 1000 - sj["d"] - sv["d"]) - (z_base_col + ESTR["placa_base_mm"] / 1000)
    m.calc("Altura livre do pilar (placa de base → mesa inferior da viga)", "", "", h_col, "m", 3, "h_pilar")
    z_F = TANQUE["cota_base"] + CAIXA_FORN["H_ext"] / 2 - z_base_col
    M_base = F_tq * z_F + (F_esc + F_estr) * 2.5
    m.calc("Momento do vento na base dos pilares", "M = F_caixa·z + F_outros·2,5", "", M_base, "kN·m", 1, "M_vento_base")
    sum_x2 = 6 * (Ld / 2) ** 2
    dN_w = M_base * (Ld / 2) / sum_x2
    m.calc("Variação de normal nos pilares de borda por vento (distribuição rígida)", "ΔN = M·x/Σx²", f"{f(M_base,1)}·2,2/{f(sum_x2,2)}", dN_w, "kN", 2, "dN_vento")
    Nd_max = float(np.max(1.4 * reac_p["G"] + 1.5 * reac_p["Q"])) + 1.4 * dN_w
    Gmin = float(np.min(reac_p["G"]))
    N_uplift = 1.0 * Gmin - 1.4 * dN_w
    m.calc("Normal de cálculo máxima (pilar central/borda, 1,4G+1,5Q+1,4W)", "", "", Nd_max, "kN", 1, "Nd_pilar_max")
    m.calc("Normal mínima, caixa vazia (1,0G − 1,4W)", "", "", N_uplift, "kN", 2, "Nd_pilar_min")
    if N_uplift < 0:
        m.p("Com a caixa vazia e vento, os pilares de canto ficam levemente tracionados ⇒ os chumbadores são necessários "
            "também por arrancamento (não apenas por montagem).")
    # pilar
    sp = props_I(ESTR["perfil_pilar"])
    K_pil = 1.0  # estrutura contraventada nas 4 faces + diafragma do deck: pilares indeslocáveis (K = 1,0)
    NRd, detN = NcRd_I(sp, ACO_PERFIL["fy"], K_pil * h_col, K_pil * h_col, K_pil * h_col)
    m.p("Pilares: todas as faces contraventadas e o deck (chapa parafusada + vigas) atua como diafragma ⇒ topo dos pilares "
        "indeslocável, K = 1,0. Excentricidade acidental de 5 cm na reação da viga (desalinhamento de montagem, vãos com "
        "cargas desiguais). A W150×22,5 foi testada e resultou em interação 0,98–1,07 (dependendo de K) — descartada por "
        "margem insuficiente; adotada **W150×29,8** em todos os pilares (padronização).")
    m.calc(f"Resistência à compressão {ESTR['perfil_pilar']} (K = 1,0, L = {f(h_col,2)} m)", "NcRd = χ·Q·A·fy/γa1",
           f"χ = {f(detN['chi'],3)}; λ0 = {f(detN['lambda0'],3)}; Q = {f(detN['Q'],2)}", NRd, "kN", 1, "NcRd_pilar")
    # momento por excentricidade da reação (e = 5 cm) + força horizontal
    H_d = 1.4 * Fw
    n_diag = 4  # 2 faces × 2 painéis por direção
    hcol_bay = h_col
    theta = math.atan(hcol_bay / (Ld / 2))
    Nt_diag = H_d / (n_diag * math.cos(theta))
    Md_pil = Nd_max * 0.05
    MRd_pil, _ = MRd_I(sp, ACO_PERFIL["fy"], h_col)
    ratio = Nd_max / NRd + 8 / 9 * Md_pil / MRd_pil if Nd_max / NRd >= 0.2 else Nd_max / (2 * NRd) + Md_pil / MRd_pil
    m.calc("Interação N+M (excentricidade acidental 5 cm)", "N/NRd + 8/9·M/MRd", f"{f(Nd_max,1)}/{f(NRd,1)} + 8/9·{f(Md_pil,1)}/{f(MRd_pil,1)}", ratio, "-", 3, "interacao_pilar", ok=ratio <= 1.0)
    # contraventamento
    m.calc("Força horizontal de cálculo", "Hd = 1,4·Fw", "", H_d, "kN", 2)
    m.calc("Ângulo da diagonal", "θ = atan(h/2,20)", "", math.degrees(theta), "°", 1)
    m.calc("Tração na diagonal (4 diagonais tracionadas por direção)", "Nt = Hd/(4·cosθ)", "", Nt_diag, "kN", 2, "Nt_diag")
    d_b = 0.016
    Ab = math.pi * d_b ** 2 / 4
    Nt_rd = min(Ab * ACO_CHAPA["fy"] * 1e3 / GAMMA["a1"], 0.75 * Ab * ACO_CHAPA["fu"] * 1e3 / GAMMA["a2"])
    m.calc("Resistência barra redonda Ø16 A36 (rosca: 0,75·Ab·fu/γa2)", "", "", Nt_rd, "kN", 1, ok=Nt_diag <= Nt_rd)
    # placa de base
    B = Np = 0.30
    sigma = Nd_max / (B * Np)
    fcd_c = CONCRETO["fck"] * 1e3 / (GAMMA["c"] * 1.4)
    m.calc("Pressão de contato na placa 300×300", "σ = Nd/(B·N)", "", sigma / 1000, "MPa", 2)
    m.calc("Resistência ao esmagamento do concreto (A2 = A1)", "σRd = fck/(γc·γn)", "30/(1,4·1,4)", fcd_c / 1000, "MPa", 2, ok=sigma <= fcd_c)
    mm = (Np - 0.95 * sp["d"]) / 2
    nn_ = (B - 0.8 * sp["bf"]) / 2
    l = max(mm, nn_)
    tp = l * math.sqrt(2 * sigma / (ACO_CHAPA["fy"] * 1e3 / GAMMA["a1"]))
    m.calc("Espessura mínima da placa de base (balanço l)", "t = l·√(2σ/(fy/γa1))", f"l = {f(l*1000,0)} mm", tp * 1000, "mm", 1, ok=tp * 1000 <= ESTR["placa_base_mm"])
    # chumbadores
    Vbase = H_d / 2 / 2  # por pilar com diagonal chegando (2 pilares por face, por direção) — conservador
    Ab20 = math.pi * 0.020 ** 2 / 4
    FvRd = 0.4 * Ab20 * CHUMB["fub"] * 1e3 / GAMMA["a2"]
    FtRd = 0.75 * Ab20 * CHUMB["fub"] * 1e3 / GAMMA["a2"]
    Tb = max(0.0, -N_uplift) / 4 + Nt_diag * math.sin(theta) / 2
    m.calc("Cisalhamento por pilar contraventado (conservador)", "V = Hd/4", "", Vbase, "kN", 2)
    m.calc("Cisalhamento resistente 4×M20 F1554 Gr36", "4·0,4·Ab·fub/γa2", "", 4 * FvRd, "kN", 1, ok=Vbase <= 4 * FvRd)
    m.calc("Tração por chumbador (arrancamento: componente vertical da diagonal + levantamento)", "", "", Tb, "kN", 2)
    m.calc("Tração resistente por chumbador M20", "0,75·Ab·fub/γa2", "", FtRd, "kN", 1, ok=Tb <= FtRd)
    m.p("Chumbadores: 4 × M20 ASTM F1554 Gr.36 galvanizados, comprimento de ancoragem ≥ 400 mm com placa/porca na "
        "extremidade (ancoragem a confirmar pela NBR 6118 e ensaios do fornecedor do sistema de ancoragem, se químico). "
        "Mesmo sem tração calculada relevante, a especificação mínima atende a montagem, a caixa vazia e esforços acidentais.")

    # ------------------------------------------------------------ ligações
    m.h("7. Ligações (pré-dimensionamento)")
    Ab12 = math.pi * 0.012 ** 2 / 4
    Ab16 = math.pi * 0.016 ** 2 / 4
    FvRd16 = 0.4 * Ab16 * PARAF["fub"] * 1e3 / GAMMA["a2"]
    FvRd12 = 0.4 * Ab12 * PARAF["fub"] * 1e3 / GAMMA["a2"]
    m.calc("Resistência ao corte, parafuso M16 A325 (rosca no plano)", "0,4·Ab·fub/γa2", "", FvRd16, "kN", 1, "FvRd_M16")
    m.calc("Resistência ao corte, parafuso M12 A325 (rosca no plano)", "0,4·Ab·fub/γa2", "", FvRd12, "kN", 1)
    m.item("Secundária × principal: apoio direto (empilhada), 4 × M16 — transfere apenas forças horizontais/estabilidade; "
           f"esforço horizontal por ligação ≤ Hd/11 = {f(H_d/11,2)} kN ≪ 4·{f(FvRd16,1)} kN.")
    m.item("Principal × pilar: chapa de topo 250×250×16 soldada ao pilar (fábrica) + 4 × M16; enrijecedores de apoio na viga.")
    m.item("Pilar × placa de base: solda de filete 6 mm em todo o contorno (fábrica, antes da galvanização).")
    Lw = 2 * sp["bf"] * 2 + 2 * sp["h"]
    Fw_rd = 0.6 * 485e3 * 0.707 * 0.006 / GAMMA["a2"]
    m.calc("Resistência da solda de filete 6 mm (E70, por metro)", "0,6·fw·0,707·a/γw2", "", Fw_rd, "kN/m", 1)
    m.calc("Comprimento de solda disponível no contorno", "", "", Lw, "m", 3)
    m.calc("Capacidade total da solda pilar-placa", "", "", Fw_rd * Lw, "kN", 0, ok=Fw_rd * Lw >= Nd_max * 0.25)
    m.item("Nota: a compressão é transmitida por contato (topo do pilar fresado/esquadrejado) — a solda dimensionada "
           "para ≥ 25 % de Nd e para os esforços horizontais.")
    m.item("Diagonais Ø16 com esticador e chapas gusset 8 mm soldadas aos pilares; 1 × M16 por extremidade "
           f"(Nt = {f(Nt_diag,1)} kN < {f(FvRd16,1)} kN).")
    m.item("Chapa de piso × secundárias: parafusos M12 cabeça escareada a cada 300 mm ao longo das juntas dos painéis.")

    # ------------------------------------------------------------ quantitativos
    m.h("8. Quantitativo preliminar de aço")
    sp_ = props_I(ESTR["perfil_pilar"])
    plat_L = ESTR["plataforma_largura"]
    itens = [
        ("Vigas secundárias " + pj, n_j, Ld, sj["massa"]),
        ("Vigas principais " + pv, 3, Ld, sv["massa"]),
        ("Pilares " + ESTR["perfil_pilar"], 9, h_col, sp_["massa"]),
        ("Postes da plataforma " + ESTR["perfil_pilar"], 3, h_col + sv["d"] + sj["d"] - 0.03, sp_["massa"]),
        ("Vigas da plataforma W150x13,0", 3, plat_L, props_I("W150x13,0")["massa"]),
        ("Viga de borda da plataforma W150x13,0", 1, Ld, props_I("W150x13,0")["massa"]),
        ("Chapa de piso 9,5 mm", 1, Ld * Ld, ESTR["chapa_piso_mm"] / 1000 * RHO_ACO),
        ("Placas de base 300×300×22,4", 12, 0.09, ESTR["placa_base_mm"] / 1000 * RHO_ACO),
        ("Diagonais Ø16 (8 painéis × 2)", 16, math.hypot(Ld / 2, h_col), Ab16 * RHO_ACO),
        ("Piso grade da plataforma (30 kg/m² [F])", 1, plat_L * Ld, 30.0),
        ("Guarda-corpo (15 kg/m [H])", 1, Ld + 2 * plat_L + 4.0, 15.0),
        ("Escada da plataforma (verba)", 1, 1.0, 180.0),
        ("Escada marinheiro c/ gaiola e patamar superior (verba)", 1, 1.0, 260.0),
    ]
    rows = []
    tot = 0
    for nome, qt, L, mpu in itens:
        mass = qt * L * mpu
        tot += mass
        rows.append([nome, f(qt, 0), f(L, 2), f(mpu, 1), f(mass, 0)])
    lig = 0.06 * tot
    rows.append(["Ligações, enrijecedores, parafusos (6 %)", "", "", "", f(lig, 0)])
    tot += lig
    rows.append(["**TOTAL**", "", "", "", f"**{f(tot,0)}**"])
    m.tabela(["Item", "Qtd", "L ou área (m/m²)", "kg/m ou kg/m²", "Massa (kg)"], rows)
    m.res["massa_aco_kg"] = tot

    # ------------------------------------------------------------ fundação
    m.h("9. Fundação — radier (pré-dimensionamento, SEM SONDAGEM)")
    Lr, Br, hr = 6.50, 5.40, 0.40  # 6,50: inclui os pedestais do patamar em X = 83,20 (achado da modelagem FEA)
    W_rad = Lr * Br * hr * GAMMA_CONC
    W_ped = 12 * 0.5 * 0.5 * 0.12 * GAMMA_CONC
    W_aco = tot * G / 1000
    N_serv = W_agua + W_tq + W_aco + W_rad + W_ped + 3.0 * plat_L * Ld
    m.p(f"Radier {f(Lr,2)} × {f(Br,2)} × {f(hr,2)} m, concreto C30, sobre lastro de 5 cm e base compactada; topo na cota 112,00; "
        "pedestais 50×50 cm até 112,12. Cotas e área: ver desenhos DES-03/DES-04.")
    m.calc("Peso do radier", "W = L·B·h·25", "", W_rad, "kN", 1)
    m.calc("Carga total de serviço na base (água até a borda)", "N = Wágua + Wcaixa + Waço + Wradier + Wped + plataforma", "", N_serv, "kN", 1, "N_servico_fundacao")
    A_r = Lr * Br
    e_plat = 0.5  # excentricidade do centro de massa (deslocamento p/ leste da plataforma)
    Mw_f = M_base + Fw * hr
    sig_med = N_serv / A_r
    sig_max = sig_med + Mw_f / (Br * Lr ** 2 / 6) + (N_serv - W_rad) * 0.0 / (Br * Lr ** 2 / 6)
    m.calc("Pressão média no solo", "σ = N/A", f"{f(N_serv,1)}/{f(A_r,2)}", sig_med, "kPa", 1, "sigma_med")
    m.calc("Pressão máxima com vento", "σ = N/A + M/W", "", sig_max, "kPa", 1, "sigma_max")
    m.calc("Comparação com σadm hipotético = 100 kPa [H — sem sondagem]", "", "", sig_max / SOLO["sigma_adm_kPa_hip"], "-", 2, ok=sig_max <= SOLO["sigma_adm_kPa_hip"])
    # tombamento/deslizamento global — caixa vazia
    N_vazio = W_tq + W_aco + W_rad + W_ped
    Mt = M_base + Fw * hr
    m.calc("Segurança ao tombamento global (caixa vazia)", "FS = N·B/2 / Mt", "", N_vazio * Br / 2 / Mt, "-", 1, ok=N_vazio * Br / 2 / Mt >= 1.5)
    m.calc("Segurança ao deslizamento (tanφ = 0,45 [H])", "FS = 0,45·N/Fw", "", 0.45 * N_vazio / Fw, "-", 1, ok=0.45 * N_vazio / Fw >= 1.5)
    # punção pilar central
    d_ef = hr - 0.05 - 0.01
    Nd_c = float(1.4 * reac_p["G"][1][1] + 1.5 * reac_p["Q"][1][1]) + 1.4 * W_ped / 12
    q_solo_d = (1.4 * (W_tq + W_aco) + 1.5 * W_agua) / A_r
    u1 = 4 * 0.50 + 2 * math.pi * 2 * d_ef
    A1 = 0.5 ** 2 + 4 * 0.5 * 2 * d_ef + math.pi * (2 * d_ef) ** 2
    Fsd = Nd_c - q_solo_d * A1
    rho = (math.pi * 0.010 ** 2 / 4 / 0.125) / d_ef
    tau_sd = Fsd / (u1 * d_ef) / 1000
    tau_rd1 = 0.13 * (1 + math.sqrt(0.20 / d_ef)) * (100 * rho * CONCRETO["fck"]) ** (1 / 3)
    m.calc("Normal de cálculo no pilar central", "", "", Nd_c, "kN", 1)
    m.calc("Força de punção (descontada reação do solo dentro de C')", "Fsd = Nd − σd·A_C'", "", Fsd, "kN", 1)
    m.calc("Tensão solicitante no contorno C' (2d)", "τSd = Fsd/(u·d)", f"u = {f(u1,2)} m; d = {f(d_ef,2)} m", tau_sd, "MPa", 3)
    m.calc("Tensão resistente sem armadura de punção (NBR 6118, 19.5)", "τRd1 = 0,13(1+√(20/d))(100ρfck)^(1/3)", f"ρ = {f(rho*100,3)} %", tau_rd1, "MPa", 3, ok=tau_sd <= tau_rd1)
    # flexão simplificada
    qn = q_solo_d
    M0 = qn * 2.2 * (2.2 - 0.5) ** 2 / 8
    m.calc("Momento estático total por painel 2,2 m (método direto, reação uniforme)", "M0 = q·l2·ln²/8", "", M0, "kN·m", 1)
    As_min = 0.0015 * 1.0 * hr * 1e4
    m.calc("Armadura mínima por face e direção (ρmin = 0,15 %)", "As = 0,0015·b·h", "", As_min, "cm²/m", 2)
    As_neg = 0.65 * M0 * 0.75 / 2.2 / (0.9 * d_ef * ACO_CA50["fyk"] * 1e3 / GAMMA["s"]) * 1e4  # faixa dos pilares
    m.calc("Armadura de flexão necessária na faixa dos pilares (estimativa)", "As = 0,65·0,75·M0/l/(0,9·d·fyd)", "", As_neg, "cm²/m", 2)
    m.p("Adotado (preliminar): malha Ø10 c/ 12,5 cm (6,28 cm²/m) nas duas faces e duas direções; arranques dos pedestais "
        "4 Ø12,5 + estribos Ø6,3 c/ 15. Cobrimento 40 mm.")
    m.p("**Revisão pela FEA-03 (radier sobre Winkler, `fea/`):** a estimativa simplificada acima (reação uniforme) "
        "SUBESTIMA o momento local sob o pilar central, que concentra ~45 % da carga. A placa de Mindlin sobre molas "
        "(k = 10–40 MN/m³) indica m* ≈ 73–86 kN·m/m (ELU) na face inferior sob esse pilar, contra MRd ≈ 86 kN·m/m da "
        "malha mínima (taxa 0,85–1,00). **Adotado reforço inferior adicional Ø12,5 c/ 12,5 cm nas duas direções numa "
        "região de 2,40 × 2,40 m centrada no pilar central** (As total ≈ 16 cm²/m ⇒ MRd ≈ 210 kN·m/m). Ver FEA.md.")
    m.p("Alternativa avaliada: 9 sapatas isoladas ligadas por vigas-baldrame. Com σadm = 100 kPa a sapata do pilar central "
        f"precisaria de ≈ {f(math.sqrt((reac_p['G'][1][1]+reac_p['Q'][1][1])*1.1/100),2)} m de lado, e as de canto ≈ 0,8 m — "
        "carga muito desigual (central ≈ 30 % do total), com risco de recalque diferencial sob o deck que apoia a caixa. "
        "O radier foi preferido por uniformizar recalques e tolerar solo desconhecido; a escolha final depende da sondagem.")
    m.p("**Riscos geotécnicos a investigar:** solos porosos colapsíveis são frequentes no interior de SP — umedecimento por "
        "vazamento, extravasamento ou drenagem pode causar recalque brusco; o platô está em encosta (corte/aterro); nível "
        "d'água desconhecido. Requisitos mínimos: sondagens SPT (NBR 6484) — mínimo 3 furos na área da caixa e 1 na captação — "
        "com ensaio de colapsibilidade se houver solo poroso, e afastamento de toda descarga de água ≥ 10 m da fundação.")

    # ------------------------------------------------------------ verificação do solver
    m.h("10. Verificação do solver (viga contínua de 2 vãos, carga uniforme)")
    s_t = props_I("W150x13,0")
    rr = viga_continua(4.4, [0, 2.2, 4.4], {"q": lambda x: 10.0}, E * s_t["Ix"])
    m.calc("Reação central FE", "", "", rr["reac"][1], "kN", 3)
    m.calc("Reação central analítica", "R = 1,25·q·L", "1,25·10·2,2", 1.25 * 10 * 2.2, "kN", 3, ok=abs(rr["reac"][1] - 27.5) < 0.05)
    m.calc("Momento no apoio central FE", "", "", float(np.max(np.abs(rr["M"]))), "kN·m", 3)
    m.calc("Momento analítico", "M = qL²/8", "10·2,2²/8", 10 * 2.2 ** 2 / 8, "kN·m", 3, ok=abs(float(np.max(np.abs(rr["M"]))) - 6.05) < 0.05)

    m.res.update(dict(perfil_joist=pj, perfil_viga=pv, perfil_pilar=ESTR["perfil_pilar"], n_joists=n_j,
                      xs_pil=xs_pil, ys_pil=ys_pil, xs_j=xs_j, h_col=h_col, d_joist=sj["d"], d_viga=sv["d"],
                      bf_joist=sj["bf"], bf_viga=sv["bf"], d_pilar=sp["d"], bf_pilar=sp["bf"],
                      radier=(Lr, Br, hr), reac_G=reac_p["G"].tolist(), reac_Q=reac_p["Q"].tolist()))
    return m


if __name__ == "__main__":
    print(run().texto())
