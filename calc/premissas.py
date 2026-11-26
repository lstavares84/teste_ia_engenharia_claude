# -*- coding: utf-8 -*-
"""
Premissas únicas do estudo (fonte única de dados para cálculos, modelo 3D e desenhos).

Convenção de origem de cada dado (campo 'origem' nos comentários):
  [C]  dado fornecido pelo cliente
  [H]  hipótese adotada para o exercício (precisa ser confirmada)
  [F]  depende de fornecedor (valor provisório)
  [N]  critério normativo / literatura técnica (ver relatório, seção de normas)
  [K]  constante física

Cotas em metros na referência fictícia do cliente. Coordenadas de implantação:
  X = eixo do traçado (rio -> casa), Y = transversal, Z = cota.
  Origem X=0 no ponto previsto de captação (borda d'água no nível mínimo).
"""
import math

# ---------------------------------------------------------------- constantes [K]
G = 9.81                 # m/s²
RHO = 1000.0             # kg/m³ (água)
GAMMA_W = RHO * G / 1000 # kN/m³ = 9.81
NU = 1.004e-6            # m²/s, viscosidade cinemática a 20 °C
PV_30C = 0.43            # m.c.a., pressão de vapor a 30 °C (água) [K]
E_ACO = 200_000.0        # MPa  [N] NBR 8800
G_ACO = 77_000.0         # MPa  [N] NBR 8800
RHO_ACO = 7850.0         # kg/m³
GAMMA_CONC = 25.0        # kN/m³ concreto armado [N] NBR 6120

# ---------------------------------------------------------------- dados do cliente [C]
COTAS = {
    "rio_min": 97.50,
    "rio_normal": 100.00,
    "rio_max": 102.00,
    "terreno_margem": 103.00,
    "terreno_caixa": 112.00,
    "piso_casa": 120.00,
    "ponto_alto_casa": 122.50,
}
DIST = {"captacao_caixa": 80.0, "caixa_casa": 140.0}       # horizontais [C]
CAIXA_FORN = {                                              # fornecedor fictício [C]/[F]
    "V_util_m3": 50.0,
    "D_ext": 4.00,
    "H_ext": 4.50,
    "massa_vazia_kg": 1200.0,
    "base_acima_terreno": 1.50,
}
AREA_DISPONIVEL = (8.0, 8.0)                                # m x m [C]
DEMANDA = {
    "diaria_descarga_lavagem_L": 4000.0,
    "diaria_irrigacao_L": 4000.0,
    "diaria_total_L": 8000.0,
    "horas_bombeamento_max": 8.0,
    # vazões simultâneas [C]
    "simult_L_min": {"lavagem_1": 9.0, "lavagem_2": 9.0, "irrigacao": 12.0, "descarga": 6.0},
    "p_din_min_mca": 15.0,
}
ENERGIA = {"V": 380.0, "f": 60.0, "fases": 3}               # [C]

# ---------------------------------------------------------------- hipóteses de implantação [H]
# Perfil simplificado do terreno ao longo do eixo X (sem levantamento topográfico!)
PERFIL_TERRENO = [  # (X, cota)
    (-6.00, 95.50),   # leito do rio (hipótese: profundidade mínima 2,0 m no nível mínimo)
    (-2.25, 95.70),   # leito junto à extremidade do tubo-camisa
    (0.00, 97.50),    # borda d'água no nível mínimo = ponto de captação
    (8.25, 103.00),   # crista da margem (talude 1V:1,5H assumido)
    (76.00, 112.00),  # início da área da caixa (rampa média 13,3 %)
    (84.00, 112.00),  # área da caixa terraplenada em platô 112,00 (8 x 8 m)
    (220.00, 120.00), # entrada da casa (rampa média 5,9 %)
    (232.00, 120.00), # casa
]
X_CAIXA = 79.60        # centro da caixa (área 76..84) [H]
Y_CAIXA = 0.0
X_CASA_ENTRADA = 219.6 # 140 m do centro da caixa [C]+[H]

# ---------------------------------------------------------------- caixa — hipóteses [H]/[F]
TANQUE = {
    "cota_base": COTAS["terreno_caixa"] + CAIXA_FORN["base_acima_terreno"],  # 113.50
    "esp_fundo": 0.05,      # [F] espessura/fundo -> fundo interno
    "D_int": 3.96,          # [F] diâmetro interno assumido (parede 20 mm)
}
TANQUE["cota_fundo_int"] = TANQUE["cota_base"] + TANQUE["esp_fundo"]          # 113.55
TANQUE["A_int"] = math.pi * TANQUE["D_int"] ** 2 / 4                           # m²
TANQUE["cota_topo"] = TANQUE["cota_base"] + CAIXA_FORN["H_ext"]                # 118.00
# Níveis operacionais (todos [H], dependem do desenho certificado da caixa)
NIVEIS = {
    "saida_N2_eixo": 113.80,   # bocal de saída p/ pressurização (0,25 m acima do fundo: reserva p/ sedimentos)
    "dreno_N3_eixo": 113.62,
    "LSLL_desliga_booster": 114.15,
    "LAL_alarme_baixo": 114.50,
    "P1_liga": 116.80,
    "P1_desliga": 117.35,
    "LAHH_alarme_muito_alto": 117.50,
}
NIVEIS["extravasor_N4_soleira"] = round(TANQUE["cota_fundo_int"] + CAIXA_FORN["V_util_m3"] / TANQUE["A_int"], 3)
NIVEIS["entrada_N1_descarga_livre"] = 117.80
NIVEIS["borda_cheio_total"] = 117.95   # água até a borda (extravasor obstruído) — caso excepcional

# ---------------------------------------------------------------- tubulações [H]/[N]
# PEAD PE 100 SDR 11 (PN 16): diâmetro externo (mm) -> espessura (mm). e = DE/SDR arredondado.
PEAD_SDR11 = {32: 3.0, 40: 3.7, 50: 4.6, 63: 5.8, 75: 6.8, 90: 8.2, 110: 10.0}
RUGOSIDADE_PE = 0.007e-3   # m (tubo novo liso) — usado 0,05 mm para envelhecimento/incrustação
RUGOSIDADE_PROJ = 0.05e-3  # m [H] conservador

def di_pead(de_mm):
    return (de_mm - 2 * PEAD_SDR11[de_mm]) / 1000.0

# ---------------------------------------------------------------- captação (P-101) [H]
CAPTACAO = {
    "Q_proj_m3h": 3.0,          # vazão de projeto escolhida (ver justificativa na memória)
    "DE_recalque": 40,
    "L_recalque_m": 115.0,      # 14 (camisa) + 84 (vala) + 6 (abrigo) + 11 (prumada) [H]
    "K_singular": {             # coeficientes de perda localizada [N] literatura
        "valv_retencao_bomba": 2.0, "valv_retencao_mola_CV102": 2.5,
        "registros_esfera_4x": 4 * 0.2, "curvas90_6x": 6 * 0.6, "curvas45_4x": 4 * 0.3,
        "tes_passagem_3x": 3 * 0.4, "saida_livre": 1.0,
    },
    "perda_filtro_limpo_m": 2.0,    # [F] confirmar com curva do filtro
    "perda_filtro_sujo_m": 5.0,     # [F] ponto de ajuste de retrolavagem (~0,3 bar acima do limpo)
    "perda_hidrometro_m": 1.0,      # [F] confirmar com curva do medidor
    "fator_seg_perdas": 1.10,
    "z_crista_camisa": 103.80,
    "z_extremidade_camisa": 96.00,
    "z_succao_bomba": 96.30,        # crivo da bomba ~0,3 m acima da extremidade
    "L_camisa_m": 14.06,
    "DE_camisa_mm": 200,
}
# ---------------------------------------------------------------- pressurização (P-201) [H]
BOOSTER = {
    "DE_succao": 63, "L_succao_m": 8.0,
    "K_succao": {"entrada": 0.5, "registro": 0.2, "junta_flex": 0.2, "curvas90_4x": 2.4,
                 "filtro_Y": 2.0, "registro_2": 0.2, "te_bifurcacao": 1.0, "reducao": 0.2},
    "DE_recalque": 40, "L_recalque_m": 160.0,
    "K_recalque": {"valv_retencao": 2.5, "registros_3x": 0.6, "curvas90_8x": 4.8, "tes_2x": 2.0},
    "perda_hidrometro_m": 0.5,         # [F] medidor opcional do sistema não potável
    "perda_rede_interna_casa_m": 2.5,  # [H] verba até o ponto mais alto (projeto interno é de terceiros)
    "z_eixo_bomba": 112.30,
    "fator_seg_perdas": 1.10,
}

# ---------------------------------------------------------------- local / clima [H]
P_ATM_MCA = 9.30   # m.c.a. — conservador p/ altitudes até ~900 m (interior de SP) [H]
VENTO = {          # NBR 6123 — formulação da edição 1988 (ver relatório) [N]/[H]
    "V0": 45.0,    # m/s — hipótese conservadora; confirmar na isopleta para o município
    "S1": 1.0,     # topografia — terreno em encosta: verificar (sensibilidade S1=1,1 avaliada)
    "S3": 1.0,     # estatístico — adotado 1,0 (conservador)
    "cat": "II", "classe": "A", "b": 1.00, "p": 0.085, "Fr": 1.00,
    "Ca_cilindro": 0.80,   # [H] conservador (cilindro com nervuras/acessórios, h/d≈1,1)
    "Ca_escada": 1.20, "A_escada_m2": 1.6,
}

# ---------------------------------------------------------------- materiais [N]
ACO_PERFIL = {"nome": "ASTM A572 Gr.50", "fy": 345.0, "fu": 450.0}
ACO_CHAPA = {"nome": "ASTM A36", "fy": 250.0, "fu": 400.0}
PARAF = {"nome": "ASTM F3125 Gr. A325 galv.", "fub": 825.0}
CHUMB = {"nome": "ASTM F1554 Gr.36 galv.", "fy": 248.0, "fub": 400.0}
CONCRETO = {"fck": 30.0, "classe_agress": "II (adotada)", "cobrimento_mm": 40}
ACO_CA50 = {"fyk": 500.0}
GAMMA = {"a1": 1.10, "a2": 1.35, "c": 1.40, "s": 1.15,
         "g": 1.40, "g_fav": 1.00, "q_agua": 1.50, "w": 1.40, "q_sobrecarga": 1.50}
SOLO = {"sigma_adm_kPa_hip": 100.0}   # [H] SEM SONDAGEM — apenas para pré-dimensionamento

# Perfis laminados W (dimensões nominais d, bf, tw, tf em mm) — verificar no catálogo
# do fornecedor/NBR 15980 antes do executivo. Propriedades calculadas SEM raios de
# concordância (conservador).
PERFIS_W = {
    "W150x13,0": (148, 100, 4.3, 4.9),
    "W150x18,0": (153, 102, 5.8, 7.1),
    "W150x22,5": (152, 152, 5.8, 6.6),
    "W150x29,8": (157, 153, 6.6, 9.3),
    "W200x19,3": (203, 102, 5.8, 6.5),
    "W200x26,6": (207, 133, 5.8, 8.4),
    "W200x31,3": (210, 134, 6.4, 10.2),
    "W200x35,9": (201, 165, 6.2, 10.2),
    "W250x32,7": (258, 146, 6.1, 9.1),
    "W250x38,5": (262, 147, 6.6, 11.2),
}

# ---------------------------------------------------------------- estrutura — geometria [H]
ESTR = {
    "lado_deck": 4.40,          # deck quadrado 4,40 x 4,40 (caixa Ø4,00 + 0,20 por lado)
    "n_vaos": 2,                # 3 x 3 pilares, vão 2,20 m
    "esp_joists": 0.44,         # 11 vigas secundárias
    "chapa_piso_mm": 9.5,       # chapa lisa A36 parafusada (painéis 0,88 x 4,40 m)
    "manta_kPa": 0.10,          # manta/apoio elastomérico sobre o deck (se exigida) [F]
    "perfil_joist": "W150x13,0",
    "perfil_viga": "W200x35,9",
    "perfil_pilar": "W150x29,8",   # confirmado pela verificação N+M (ver memória)
    "plataforma_largura": 1.10, # plataforma de serviço lado leste
    "sobrecarga_plataforma_kPa": 3.0,   # [H] manutenção
    "sobrecarga_deck_manut_kPa": 2.0,   # [H] deck sem caixa / montagem
    "cota_topo_pedestal": 112.12,
    "graute_mm": 30,
    "placa_base_mm": 22.4,
}
