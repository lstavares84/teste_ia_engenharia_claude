# -*- coding: utf-8 -*-
"""Memória de cálculo elétrica preliminar: cargas, correntes, quedas de tensão, proteção."""
import math
from premissas import *
from memo import Memo, f

RHO_CU_20 = 0.017241   # Ω·mm²/m  [K]
ALFA_CU = 0.00393      # 1/°C
X_CABO = 0.08e-3       # Ω/m  reatância típica de cabo multipolar BT [H]


def r70(S):
    return RHO_CU_20 * (1 + ALFA_CU * 50) / S   # Ω/m a 70 °C (PVC)


def dv_pct(I, L, S, cos=0.80, V=380.0):
    sen = math.sqrt(1 - cos ** 2)
    return math.sqrt(3) * I * L * (r70(S) * cos + X_CABO * sen) / V * 100


def run():
    m = Memo("Memória de Cálculo — Alimentação Elétrica e Automação (preliminar)")
    m.p("Rendimentos e fatores de potência são **hipóteses** (sem dados de placa); correntes devem ser recalculadas com "
        "os dados dos equipamentos efetivamente comprados. Resistência do cobre a 70 °C: ρ = 0,017241·(1+0,00393·50) "
        "Ω·mm²/m; reatância 0,08 Ω/km. Queda de tensão trifásica: ΔV% = √3·I·L·(R·cosφ + X·senφ)/V·100.")
    V = ENERGIA["V"]
    m.h("1. Quadro de cargas")
    cargas = [
        # tag, descrição, P (kW), η, cosφ, fases, regime
        ("P-101", "Bomba submersa de captação (motor 4\", partida suave)", 1.10, 0.75, 0.80, 3, "intermitente ~3 h/dia"),
        ("P-201A", "Booster A (inversor de frequência)", 0.75, 0.78, 0.80, 3, "intermitente (demanda)"),
        ("P-201B", "Booster B — reserva (não opera simultâneo)", 0.75, 0.78, 0.80, 3, "reserva"),
        ("DP-101", "Bomba dosadora de cloro", 0.05, 1.0, 0.90, 1, "com P-101"),
        ("F-101", "Controlador do filtro autolimpante + solenoides", 0.03, 1.0, 0.90, 1, "contínuo"),
        ("QCB-AUX", "CLP/relé programável, fonte 24 Vcc, instrumentos, comunicador GSM", 0.10, 1.0, 0.90, 1, "contínuo"),
        ("QCB-AQ", "Resistência anticondensação + ventilação do painel", 0.10, 1.0, 1.0, 1, "termostato"),
        ("ILU/TUG", "Iluminação e tomada de serviço do abrigo", 1.00, 1.0, 0.92, 1, "eventual"),
    ]
    rows = []
    soma = 0
    I_tab = {}
    for tag, desc, P, eta, cos, fas, reg in cargas:
        S = P / eta / cos
        I = S * 1000 / (math.sqrt(3) * V) if fas == 3 else S * 1000 / 220.0
        I_tab[tag] = I
        if tag != "P-201B":
            soma += S
        rows.append([tag, desc, f(P, 2), f(eta, 2), f(cos, 2), str(fas) + "F", f(S, 2), f(I, 2), reg])
    m.tabela(["Tag", "Carga", "P (kW)", "η [H]", "cosφ [H]", "Fases", "S (kVA)", "I (A)", "Regime"], rows)
    m.calc("Potência aparente máxima simultânea (sem reserva)", "ΣS", "", soma, "kVA", 2, "S_total_kVA")
    I_tot = soma * 1000 / (math.sqrt(3) * V)
    m.calc("Corrente equivalente trifásica (equilibrada)", "I = S/(√3·V)", "", I_tot, "A", 2, "I_total")
    m.p("Cargas monofásicas (220 V fase-neutro **— confirmar se a rede é 380/220 V com neutro**) distribuídas entre fases.")

    m.h("2. Alimentador do QCB (quadro existente → QCB na área da caixa)")
    L_alim = 30.0
    m.p("Distância entre o quadro existente e o QCB desconhecida — adotado L = 30 m [H].")
    for S in [4.0, 6.0]:
        m.calc(f"Queda de tensão 4×{f(S,0)} mm² + PE, I = {f(I_tot,1)} A", "ΔV%", "", dv_pct(I_tot, L_alim, S), "%", 2)
    m.p("Adotado: cabo 0,6/1 kV 4 × 4 mm² + PE 4 mm² em eletroduto enterrado; disjuntor tripolar 16 A curva C no quadro de "
        "origem (seletividade com a proteção geral existente a verificar) + DPS classe II no QCB. A seção é governada por "
        "resistência mecânica, curto-circuito e margem — não pela corrente (< 10 A).")

    m.h("3. Circuito da bomba submersa P-101 (QCB → rio)")
    L_p1 = 130.0
    m.p("Percurso: QCB → vala junto ao recalque (≈ 84 m) → caixa de passagem na crista → tubo-camisa (≈ 14 m) → bomba; "
        "com folgas: **L = 130 m** [H]. Cabo contínuo, próprio para imersão (sem emendas abaixo da cota 103,8).")
    I1 = I_tab["P-101"]
    rows = []
    for S in [2.5, 4.0, 6.0]:
        dv_r = dv_pct(I1, L_p1, S)
        dv_dol = dv_pct(6.5 * I1, L_p1, S, cos=0.40)
        dv_soft = dv_pct(3.0 * I1, L_p1, S, cos=0.50)
        rows.append([f"4×{f(S,1)} mm²", f(dv_r, 2), f(dv_dol, 2), f(dv_soft, 2)])
    m.tabela(["Cabo", "ΔV regime (%)", "ΔV partida direta 6,5·In, cosφ 0,4 (%)", "ΔV soft-starter 3·In, cosφ 0,5 (%)"], rows)
    m.res["dv_p1_4mm"] = dv_pct(I1, L_p1, 4.0)
    m.p("Critérios adotados: ≤ 4 % em regime no circuito terminal (somado à queda a montante, total ≤ 7 % — limites usuais "
        "da NBR 5410, confirmar edição vigente) e ≤ 10 % na partida. **Adotado cabo 4 × 4 mm² (3F + PE)** próprio para "
        "bomba submersa: folga para motor até 1,5 kW e para o comprimento máximo de cabo indicado pelo fabricante do motor "
        "(dado do fornecedor que prevalece sobre este cálculo).")

    m.h("4. Proteções e comandos")
    m.item(f"P-101: disjuntor-motor ajustado a ~1,05·In (In ≈ {f(I1,1)} A — ajustar ao dado de placa), soft-starter com "
           "rampa de aceleração e desaceleração (mitigação do golpe de aríete), relé de falta/sequência de fase e sub/sobretensão, "
           "relé de subcarga (potência/cosφ) para proteção contra funcionamento a seco, eletrodos/boia de nível mínimo no "
           "tubo-camisa (redundância), DR 30 mA (recomendação: circuito alimenta equipamento imerso em água acessível a pessoas).")
    m.item("P-201A/B: disjuntor-motor + inversor de frequência dedicado por bomba (ou conjunto pressurizador com controle "
           "integrado), transmissor de pressão 4–20 mA na descarga, proteção contra marcha a seco por subcarga do inversor "
           "e por chave de nível LSLL hard-wired. DR compatível com inversor (tipo B ou conforme fabricante do inversor).")
    m.item("Circuitos de tomada/iluminação: disjuntor 16 A + DR 30 mA.")
    m.item("DPS classe II em cada fase e neutro no QCB; DPS para a linha de sinal/remoto, se cabeada.")
    m.item("Botão de emergência (NR-12) no QCB e seccionadora geral com bloqueio por cadeado (NR-10 — bloqueio e etiquetagem).")

    m.h("5. Aterramento e equipotencialização")
    m.item("Eletrodo de aterramento em anel ou incorporado à armadura do radier (eletrodo de fundação), interligado à "
           "estrutura metálica, ao QCB, às carcaças dos motores, à tubulação metálica e ao SPDA, se requerido.")
    m.item("Esquema de aterramento existente (TN-S, TN-C-S ou TT) **desconhecido** — define a coordenação das proteções. "
           "Se TT: com DR 30 mA, RA ≤ 50 V / 0,03 A = 1 667 Ω (condição normativa); recomenda-se como boa prática ≤ 10 Ω "
           "para facilitar integração com o SPDA.")
    m.item("Análise de risco de descargas atmosféricas (NBR 5419-2) para a estrutura metálica de ~6 m em área aberta — "
           "decidir sobre SPDA; a própria estrutura metálica aterrada pode servir de captor/descida natural.")

    m.h("6. Geração de emergência (opcional recomendado)")
    S_ger = (1.10 / 0.75 / 0.80) * 1.0 + (0.75 / 0.78 / 0.80) + 0.3
    m.calc("Carga para manter booster + captação + auxiliares", "S = S_P101 + S_P201 + aux", "", S_ger, "kVA", 2)
    m.p("Recomendado: entrada para gerador portátil trifásico de ~5 kVA (folga para partida com soft-starter/inversor) com "
        "chave reversora manual intertravada no QCB (impede retorno de energia para a rede). Decisão do proprietário.")

    m.h("7. Lista de E/S do controlador (preliminar)")
    m.tabela(["Tipo", "Tag", "Descrição"], [
        ["AI", "LT-101", "Nível contínuo da caixa (radar/ultrassom no teto ou hidrostático) 4–20 mA"],
        ["AI", "PT-201", "Pressão de descarga do booster (também ligado ao inversor)"],
        ["DI", "LSHH-101", "Boia de nível muito alto — intertravamento físico de P-101 + alarme"],
        ["DI", "LSLL-101", "Boia de nível muito baixo — intertravamento físico de P-201 + alarme"],
        ["DI", "LSL-100", "Nível mínimo no tubo-camisa (eletrodo) — bloqueio de P-101"],
        ["DI", "P-101 RUN/FALHA/SUBCARGA", "Retornos do soft-starter e relés"],
        ["DI", "P-201A/B RUN/FALHA", "Retornos dos inversores"],
        ["DI", "PDSH-101", "Pressão diferencial alta no filtro (falha de autolimpeza)"],
        ["DI", "FALTA FASE", "Relé de supervisão de rede"],
        ["DI", "PORTA/EMERG.", "Porta do abrigo / botão de emergência"],
        ["DI", "FQ-101 (pulso)", "Totalizador do hidrômetro de captação — registro de volume (outorga)"],
        ["DO", "P-101 LIGA", "Comando do soft-starter"],
        ["DO", "P-201 HAB.", "Habilitação do booster (alternância A/B)"],
        ["DO", "DP-101 HAB.", "Dosadora habilitada apenas com P-101 em operação"],
        ["DO", "ALM-LOCAL/REMOTO", "Sinalizador no abrigo + relé para alarme na casa (cabo ou GSM)"],
    ])
    m.res["I_P101"] = I1
    return m


if __name__ == "__main__":
    print(run().texto())
