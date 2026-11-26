# -*- coding: utf-8 -*-
"""Memória de cálculo hidráulica: demanda, captação (P-101), pressurização (P-201),
transientes, tanque (níveis/volumes), extravasor e dreno."""
import math
from premissas import *
from memo import Memo, f


def area(d):
    return math.pi * d ** 2 / 4


def fator_atrito(Re, eps, D):
    """Swamee-Jain (turbulento) / 64/Re (laminar)."""
    if Re < 2300:
        return 64.0 / Re
    return 0.25 / (math.log10(eps / (3.7 * D) + 5.74 / Re ** 0.9)) ** 2


def perda_distribuida(Q, D, L, eps=RUGOSIDADE_PROJ):
    v = Q / area(D)
    Re = v * D / NU
    fa = fator_atrito(Re, eps, D)
    hf = fa * L / D * v ** 2 / (2 * G)
    return v, Re, fa, hf


def celeridade_pead(D_int, e, K=2.2e9, E=1.0e9):
    """Celeridade da onda (Korteweg); E de curta duração do PE100 ~1,0 GPa [H]."""
    return math.sqrt(K / RHO / (1 + K * D_int / (E * e)))


def run():
    m = Memo("Memória de Cálculo — Hidráulica (captação, reservação e pressurização)")
    m.p("Ferramenta: Python 3.12 + numpy (scripts em `calc/`). Reprodução: `python calc/run_all.py`. "
        "Perda de carga distribuída por Darcy-Weisbach com fator de atrito de Swamee-Jain; "
        "rugosidade de projeto ε = 0,05 mm (PEAD envelhecido, conservador frente a 0,007 mm de tubo novo); "
        "ν = 1,004×10⁻⁶ m²/s (20 °C).")

    # ------------------------------------------------------------ 1. demanda
    m.h("1. Demandas")
    Vd = DEMANDA["diaria_total_L"] / 1000
    Qmin_rep = m.calc("Vazão mínima de reposição (8 m³ em 8 h)", "Q = V/t", f"{f(Vd,1)} m³ / 8 h",
                      Vd / DEMANDA["horas_bombeamento_max"], "m³/h", 3, "Q_min_reposicao")
    qs = DEMANDA["simult_L_min"]
    Qs_Lmin = sum(qs.values())
    m.calc("Vazão simultânea na casa", "ΣQi = 9 + 9 + 12 + 6", f"{f(Qs_Lmin,0)} L/min", Qs_Lmin, "L/min", 0)
    Qs = Qs_Lmin / 60000
    m.calc("Vazão simultânea (SI)", "Q = 36/60 000", "", Qs * 1000, "L/s", 3, "Q_simult_Ls")
    m.calc("Vazão simultânea (m³/h)", "Q = 0,6 × 3,6", "", Qs * 3600, "m³/h", 2, "Q_simult_m3h")
    m.calc("Tempo para consumir 8 m³ na vazão simultânea", "t = V/Q", "8 / 2,16", Vd / (Qs * 3600), "h", 2)
    m.p("Interpretação: a vazão simultânea (2,16 m³/h) consumiria 8 m³ em 3,7 h; logo, ela é uma condição "
        "de pico de curta duração e não deve ser confundida com o volume diário. A bomba de captação é "
        "dimensionada pelo volume diário (reposição) e a pressurização pela vazão simultânea.")

    # ------------------------------------------------------------ 2. tanque
    m.h("2. Caixa d'água — volumes e níveis (dependem do desenho certificado)")
    A = TANQUE["A_int"]
    m.calc("Área interna", "A = π·Di²/4", f"π·{f(TANQUE['D_int'],2)}²/4", A, "m²", 3, "A_tanque")
    m.calc("Altura útil até o extravasor p/ 50 m³", "h = V/A", f"50/{f(A,3)}", 50 / A, "m", 3)
    rows = []
    for k, z in sorted(NIVEIS.items(), key=lambda kv: kv[1]):
        vol = max(0.0, (z - TANQUE["cota_fundo_int"]) * A)
        rows.append([k, f(z, 2), f(vol, 1)])
    m.tabela(["Nível", "Cota (m)", "Volume acumulado (m³)"], rows)
    V_op = (NIVEIS["P1_desliga"] - NIVEIS["LSLL_desliga_booster"]) * A
    V_morto = (NIVEIS["LSLL_desliga_booster"] - TANQUE["cota_fundo_int"]) * A
    V_hist = (NIVEIS["P1_desliga"] - NIVEIS["P1_liga"]) * A
    m.calc("Volume operacional (LSLL → P1 desliga)", "V = (117,35−114,15)·A", "", V_op, "m³", 1, "V_operacional")
    m.calc("Volume abaixo de LSLL (sedimentos/submergência)", "V = (114,15−113,55)·A", "", V_morto, "m³", 1, "V_morto")
    m.calc("Volume da histerese de partida de P-101", "V = (117,35−116,80)·A", "", V_hist, "m³", 1, "V_hist")
    m.calc("Autonomia com P-101 parada (consumo 8 m³/d)", "t = V_op/8", "", V_op / Vd, "dias", 1, "autonomia_dias")
    m.p("Observação: dos 50 m³ nominais, ~39 m³ são operacionais; ~7 m³ ficam abaixo do desligamento do "
        "booster para proteger contra vórtice/ar e reter sedimentos. A autonomia de ~5 dias cobre falha "
        "da captação, mas NÃO cobre falha do booster ou de energia (a casa está acima da caixa).")

    # ------------------------------------------------------------ 3. captação
    m.h("3. Captação e recalque rio → caixa (P-101)")
    C = CAPTACAO
    Q1 = C["Q_proj_m3h"] / 3600
    m.p("Escolha da vazão: Q_min = 1,0 m³/h atenderia exatamente 8 h/dia, sem folga para retrolavagem do "
        "filtro, perdas de rendimento por desgaste/areia e enchimento inicial. Adotado **Q = 3,0 m³/h** "
        "(fator 3 sobre o mínimo), mantendo velocidade ~1 m/s em DE 40 e potência pequena.")
    m.calc("Tempo diário de bombeamento", "t = 8/3,0", "", Vd / C["Q_proj_m3h"], "h/dia", 2, "t_bomb_diario", ok=Vd / C["Q_proj_m3h"] <= 8)
    m.calc("Enchimento inicial (caixa vazia até P1 desliga)", "t = (117,35−113,55)·A/Q",
           f"{f((NIVEIS['P1_desliga']-TANQUE['cota_fundo_int'])*A,1)}/3,0",
           (NIVEIS["P1_desliga"] - TANQUE["cota_fundo_int"]) * A / C["Q_proj_m3h"], "h", 1, "t_enchimento_h")
    m.calc("Enchimento inicial até o extravasor (50 m³)", "t = 50/3,0", "", 50 / C["Q_proj_m3h"], "h", 1)

    D1 = di_pead(C["DE_recalque"])
    m.calc("Diâmetro interno PEAD DE40 SDR11", "Di = DE − 2e", "40 − 2·3,7", D1 * 1000, "mm", 1, "D1_mm")
    v1, Re1, f1, hf1 = perda_distribuida(Q1, D1, C["L_recalque_m"])
    m.calc("Velocidade", "v = Q/A", f"{f(Q1,5)}/{f(area(D1),6)}", v1, "m/s", 3, "v1", ok=0.5 <= v1 <= 3.0)
    m.calc("Reynolds", "Re = v·D/ν", "", Re1, "-", 0)
    m.calc("Fator de atrito (Swamee-Jain)", "f = 0,25/[log(ε/3,7D + 5,74/Re^0,9)]²", "", f1, "-", 4)
    m.calc("Perda distribuída (L = 115 m)", "hf = f·L/D·v²/2g", "", hf1, "m", 2, "hf1")
    K1 = sum(C["K_singular"].values())
    hl1 = K1 * v1 ** 2 / (2 * G)
    m.calc("Perdas localizadas", "hl = ΣK·v²/2g", f"{f(K1,1)}·{f(v1**2/(2*G),4)}", hl1, "m", 2, "hl1")

    def H_sist(Q_m3h, z_rio, filtro):
        Q = Q_m3h / 3600
        v, Re, fa, hf = perda_distribuida(Q, D1, C["L_recalque_m"]) if Q > 0 else (0, 0, 0, 0)
        hl = K1 * v ** 2 / (2 * G)
        k = (Q_m3h / C["Q_proj_m3h"]) ** 2
        h_eq = (filtro + C["perda_hidrometro_m"]) * k
        Hs = NIVEIS["entrada_N1_descarga_livre"] - z_rio
        return Hs + C["fator_seg_perdas"] * (hf + hl) + h_eq

    cen = [("Rio mínimo 97,50 + filtro sujo (PROJETO)", COTAS["rio_min"], C["perda_filtro_sujo_m"]),
           ("Rio normal 100,00 + filtro limpo", COTAS["rio_normal"], C["perda_filtro_limpo_m"]),
           ("Rio máximo 102,00 + filtro limpo", COTAS["rio_max"], C["perda_filtro_limpo_m"])]
    rows = []
    for nome, z, fl in cen:
        rows.append([nome, f(NIVEIS["entrada_N1_descarga_livre"] - z, 2), f(H_sist(3.0, z, fl), 1)])
    m.tabela(["Cenário", "Hest (m)", "Hman a 3,0 m³/h (m)"], rows)
    H1 = H_sist(3.0, COTAS["rio_min"], C["perda_filtro_sujo_m"])
    m.res["H1_proj"] = H1
    m.res["H1_normal"] = H_sist(3.0, COTAS["rio_normal"], C["perda_filtro_limpo_m"])
    m.res["H1_max"] = H_sist(3.0, COTAS["rio_max"], C["perda_filtro_limpo_m"])
    m.p(f"**Ponto de operação de projeto P-101: Q = 3,0 m³/h; Hman ≥ {f(math.ceil(H1),0)} m** "
        "(rio no mínimo, filtro no limite de retrolavagem, +10 % nas perdas). A bomba deve operar de forma estável "
        f"também em Hman ≈ {f(m.res['H1_max'],0)} m (rio cheio, filtro limpo), com vazão maior — o motor deve ser "
        "não-sobrecarregável em toda a faixa (verificar na curva do fornecedor).")
    # curva do sistema
    rows = []
    for Qx in [0.0, 1.0, 2.0, 3.0, 3.5, 4.0, 5.0]:
        rows.append([f(Qx, 1)] + [f(H_sist(Qx, z, fl), 1) for _, z, fl in cen])
    m.p("Curvas do sistema (para cruzar com a curva real do fornecedor):")
    m.tabela(["Q (m³/h)", "H rio mín/filtro sujo (m)", "H rio normal/limpo (m)", "H rio máx/limpo (m)"], rows)
    m.res["curva_sistema_P101"] = [(Qx, [H_sist(Qx, z, fl) for _, z, fl in cen]) for Qx in [0, 1, 2, 3, 3.5, 4, 5]]

    Ph1 = RHO * G * Q1 * H1
    m.calc("Potência hidráulica", "Ph = ρ·g·Q·H", f"1000·9,81·{f(Q1,5)}·{f(H1,1)}", Ph1, "W", 0, "Ph1")
    eta_b1, eta_m1 = 0.50, 0.75
    m.calc("Potência no eixo (η_bomba = 0,50 [H])", "Pe = Ph/η", "", Ph1 / eta_b1, "W", 0, "Pe1")
    m.p("Motor recomendado: 0,75 kW a 1,1 kW, trifásico 380 V 60 Hz, submersível 4\" — definir com a curva "
        "de potência real (não-sobrecarregável até ~5 m³/h). Para cálculos elétricos adotou-se 1,1 kW (conservador).")

    # submergência e NPSH
    m.h("3.1 Submergência e NPSH da bomba submersa", 3)
    subm = COTAS["rio_min"] - C["z_succao_bomba"]
    m.calc("Submergência do crivo no nível mínimo", "S = 97,50 − 96,30", "", subm, "m", 2, "subm_P101")
    npsha = P_ATM_MCA + subm - PV_30C
    m.calc("NPSH disponível (perda na entrada desprezível)", "NPSHd = Patm + S − pv", f"{f(P_ATM_MCA,2)} + {f(subm,2)} − {f(PV_30C,2)}", npsha, "m", 2, "NPSHd_P101")
    m.p("A submergência mínima exigida (vórtice, arrefecimento do motor) é dado do fabricante e deve ser "
        "≤ 1,2 m. **Pré-condição crítica:** o leito do rio no ponto de captação deve estar em cota ≤ 95,70 m "
        "(hipótese). Se o leito for mais raso, será necessário poço escavado no leito ou galeria/poço de infiltração na margem.")

    # transiente
    m.h("3.2 Transiente hidráulico (golpe de aríete) — parada brusca por falta de energia", 3)
    e1 = PEAD_SDR11[C["DE_recalque"]] / 1000
    a1 = celeridade_pead(D1, e1)
    m.calc("Celeridade (PE100, E≈1,0 GPa curta duração [H])", "a = √[(K/ρ)/(1 + K·D/(E·e))]", "", a1, "m/s", 0, "a1")
    T1 = 2 * C["L_recalque_m"] / a1
    m.calc("Período da tubulação", "T = 2L/a", f"2·115/{f(a1,0)}", T1, "s", 2)
    dH1 = a1 * v1 / G
    m.calc("Sobrepressão de Joukowsky (pior caso, fechamento < T)", "ΔH = a·Δv/g", f"{f(a1,0)}·{f(v1,3)}/9,81", dH1, "m", 1, "dH1")
    Hmax1 = H1 + dH1 + 10  # +10 m: margem p/ shutoff
    m.calc("Pressão máxima estimada na bomba (Hman + ΔH + 10 m de margem p/ shutoff)", "", "", Hmax1, "m", 0, "Hmax1", ok=Hmax1 < 160)
    zcr = COTAS["terreno_margem"]
    hgl_min = COTAS["rio_min"] + H1 - dH1
    m.calc("Linha piezométrica mínima após a onda negativa, junto à bomba", "HGL = 97,50 + Hman − ΔH", "", hgl_min, "m", 1)
    m.calc("Pressão mínima na crista do talude (cota 103,0)", "p = HGL − z", "", hgl_min - zcr, "m.c.a.", 1, "pmin_crista")
    m.p("Resultado: pressão máxima muito inferior à classe PN16 (160 m), mas a onda negativa pode levar a pressões "
        "subatmosféricas no trecho do talude (risco de separação de coluna). Medidas adotadas: partida/parada suave "
        "(soft-starter com rampa de desaceleração ≥ 5 s = 7×T) para paradas normais; válvula de retenção de fechamento "
        "rápido (mola) junto à bomba; tubo SDR11 (rigidez elevada ao vácuo — confirmar com fabricante). "
        "Análise transiente com perfil real (método das características) é exigida no executivo.")
    dH1_soft = dH1 * T1 / 5.0
    m.calc("Sobrepressão aproximada com rampa de 5 s", "ΔH ≈ ΔH_J·T/t_r", "", dH1_soft, "m", 1)

    # ------------------------------------------------------------ 4. pressurização
    m.h("4. Abastecimento caixa → casa")
    m.p("Verificação por gravidade: nível máximo operacional 117,35 m < ponto mais alto 122,50 m — a água "
        "**não chega à casa por gravidade** em nenhuma condição; para 15 m.c.a. seria necessária linha "
        "piezométrica de 137,50 m (≈ 20 m acima do nível máximo da caixa). **Pressurização é indispensável** "
        "e o abastecimento da casa depende de energia elétrica.")
    B = BOOSTER
    HGL_req = COTAS["ponto_alto_casa"] + DEMANDA["p_din_min_mca"]
    m.calc("Linha piezométrica requerida no ponto mais alto", "HGL = 122,50 + 15", "", HGL_req, "m", 2, "HGL_req")
    Ds = di_pead(B["DE_succao"])
    vs, Res, fs, hfs = perda_distribuida(Qs, Ds, B["L_succao_m"])
    Ks = sum(B["K_succao"].values())
    hls = Ks * vs ** 2 / (2 * G)
    m.calc("Sucção DE63: velocidade", "v = Q/A", "", vs, "m/s", 3)
    m.calc("Sucção: perdas totais", "hf + ΣK·v²/2g", f"{f(hfs,3)} + {f(Ks,1)}·{f(vs**2/(2*G),4)}", hfs + hls, "m", 3, "h_succao")
    Dr = di_pead(B["DE_recalque"])
    vr, Rer, fr, hfr = perda_distribuida(Qs, Dr, B["L_recalque_m"])
    Kr = sum(B["K_recalque"].values())
    hlr = Kr * vr ** 2 / (2 * G)
    m.calc("Recalque DE40: velocidade", "v = Q/A", "", vr, "m/s", 3, "v2", ok=vr <= 3.0)
    m.calc("Recalque: perda distribuída (L = 160 m)", "hf = f·L/D·v²/2g", f"f = {f(fr,4)}", hfr, "m", 2, "hf2")
    m.calc("Recalque: perdas localizadas", "ΣK·v²/2g", f"{f(Kr,1)}·{f(vr**2/(2*G),4)}", hlr, "m", 2)

    def H_boost(z_nivel):
        perdas = B["fator_seg_perdas"] * (hfs + hls + hfr + hlr) + B["perda_hidrometro_m"] + B["perda_rede_interna_casa_m"]
        return HGL_req - z_nivel + perdas

    H2 = H_boost(NIVEIS["LSLL_desliga_booster"])
    H2_cheio = H_boost(NIVEIS["P1_desliga"])
    rows = [["Nível baixo (LSLL 114,15) — PROJETO", f(HGL_req - NIVEIS['LSLL_desliga_booster'], 2), f(H2, 1)],
            ["Nível alto (117,35)", f(HGL_req - NIVEIS['P1_desliga'], 2), f(H2_cheio, 1)]]
    m.tabela(["Condição", "Desnível + 15 m (m)", "Hman a 2,16 m³/h (m)"], rows)
    m.res["H2_proj"] = H2
    m.res["H2_cheio"] = H2_cheio
    m.p(f"**Ponto de operação de projeto P-201: Q = 2,2 m³/h; Hman ≥ {f(math.ceil(H2),0)} m.**")
    # setpoint de pressão na descarga
    perdas_jus = B["fator_seg_perdas"] * (hfr + hlr) + B["perda_hidrometro_m"] + B["perda_rede_interna_casa_m"]
    HGL_desc = HGL_req + perdas_jus
    p_set = HGL_desc - B["z_eixo_bomba"]
    m.calc("Setpoint de pressão na descarga do booster (controle por inversor)", "p = HGL_req + perdas a jusante − z_bomba",
           f"{f(HGL_req,2)} + {f(perdas_jus,2)} − {f(B['z_eixo_bomba'],2)}", p_set, "m.c.a.", 1, "p_setpoint")
    p_est_casa = HGL_desc - COTAS["piso_casa"]
    m.calc("Pressão estática máxima no térreo da casa (vazão nula, setpoint mantido)", "p = HGL_desc − 120,00", "", p_est_casa, "m.c.a.", 1, "p_est_casa", ok=p_est_casa <= 40)
    m.p("Com controle por inversor mantendo pressão constante na descarga, a pressão no ponto mais alto fica "
        "≥ 15 m.c.a. em vazão máxima e sobe até ~22 m.c.a. com vazão baixa; a pressão estática na casa fica "
        "abaixo do limite de 40 m.c.a. usualmente adotado para instalações prediais (NBR 5626 — confirmar texto vigente).")
    # NPSH booster
    npsha2 = P_ATM_MCA + (NIVEIS["LSLL_desliga_booster"] - B["z_eixo_bomba"]) - (hfs + hls) - PV_30C
    m.calc("NPSH disponível do booster (nível LSLL)", "NPSHd = Patm + Δz − hs − pv",
           f"{f(P_ATM_MCA,2)} + {f(NIVEIS['LSLL_desliga_booster']-B['z_eixo_bomba'],2)} − {f(hfs+hls,3)} − {f(PV_30C,2)}", npsha2, "m", 2, "NPSHd_P201")
    # vórtice
    D_n2 = di_pead(63)
    v_n2 = Qs / area(D_n2)
    Fr = v_n2 / math.sqrt(G * D_n2)
    S_req = D_n2 * (1 + 2.3 * Fr)
    m.calc("Submergência mínima anti-vórtice (ANSI/HI 9.8: S = D(1+2,3·Fr))", "S", f"{f(D_n2,4)}·(1+2,3·{f(Fr,3)})", S_req, "m", 3)
    m.calc("Submergência disponível em LSLL", "S = 114,15 − 113,80", "", NIVEIS["LSLL_desliga_booster"] - NIVEIS["saida_N2_eixo"], "m", 2, ok=NIVEIS["LSLL_desliga_booster"] - NIVEIS["saida_N2_eixo"] > S_req)
    Ph2 = RHO * G * Qs * H2
    m.calc("Potência hidráulica booster", "Ph = ρ·g·Q·H", "", Ph2, "W", 0, "Ph2")
    m.calc("Potência no eixo (η = 0,40 [H], bomba pequena)", "Pe = Ph/η", "", Ph2 / 0.40, "W", 0, "Pe2")
    m.p("Motor recomendado: 0,75 kW trifásico 380 V por bomba; conjunto duplex (1 operação + 1 reserva, alternância).")
    # transiente booster
    a2 = celeridade_pead(Dr, PEAD_SDR11[40] / 1000)
    dH2 = a2 * vr / G
    m.calc("Golpe na parada brusca do booster", "ΔH = a·v/g", f"{f(a2,0)}·{f(vr,3)}/9,81", dH2, "m", 1, "dH2")
    m.calc("Pressão máxima estimada (Hman + ΔH + 10 m)", "", "", H2 + dH2 + 10, "m", 0, ok=H2 + dH2 + 10 < 160)

    # ------------------------------------------------------------ 5. extravasor e dreno
    m.h("5. Extravasor, dreno e limpeza")
    Qmax_in = 6.0 / 3600
    m.p("Vazão máxima afluente admitida: 6 m³/h (P-101 com rio cheio e filtro limpo; 2× a vazão de projeto, "
        "a confirmar na curva). Extravasor DN 100 (DE 110):")
    Lw = math.pi * 0.0994
    h_w = (Qmax_in / (1.84 * Lw)) ** (2 / 3)
    m.calc("Lâmina sobre a boca do extravasor (vertedor circular)", "h = [Q/(1,84·π·D)]^(2/3)", "", h_w * 1000, "mm", 0, "h_extravasor_mm")
    m.p(f"Lâmina de ~{f(h_w*1000,0)} mm ⇒ nível máximo com extravasamento ≈ {f(NIVEIS['extravasor_N4_soleira']+h_w,3)} m, abaixo da "
        "descarga livre da entrada (117,80) — a entrada nunca fica afogada.")
    a_dr = area(di_pead(75))
    h0 = NIVEIS["extravasor_N4_soleira"] - 112.30
    h1 = TANQUE["cota_fundo_int"] - 112.30
    Cd = 0.6
    t_dr = 2 * A / (Cd * a_dr * math.sqrt(2 * G)) * (math.sqrt(h0) - math.sqrt(h1))
    Qpk = Cd * a_dr * math.sqrt(2 * G * h0)
    m.calc("Esvaziamento total por dreno DE75 totalmente aberto", "t = 2A/(Cd·a·√2g)·(√h0 − √h1)", "", t_dr / 60, "min", 0)
    m.calc("Vazão de pico no dreno totalmente aberto", "Q = Cd·a·√(2g·h0)", "", Qpk * 1000, "L/s", 1, "Q_dreno_pico")
    m.p(f"A vazão de pico (~{f(Qpk*1000,0)} L/s) é erosiva para descarte no terreno. Procedimento adotado: (1) consumir a água "
        "via irrigação até LSLL; (2) drenar o volume remanescente (~7 m³ + lodo) com registro de estrangulamento "
        "limitado a ≤ 3 L/s (≈ 40 min), para caixa de decantação e dispersão/infiltração afastada da fundação; "
        "(3) desclorar a água antes do lançamento.")
    m.calc("Tempo de drenagem do volume remanescente a 3 L/s", "t = 7,4 m³ / 3 L/s", "", V_morto / 0.003 / 60, "min", 0)
    return m


if __name__ == "__main__":
    print(run().texto())
