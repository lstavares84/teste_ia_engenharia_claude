# Memória de Cálculo — Hidráulica (captação, reservação e pressurização)


Ferramenta: Python 3.12 + numpy (scripts em `calc/`). Reprodução: `python calc/run_all.py`. Perda de carga distribuída por Darcy-Weisbach com fator de atrito de Swamee-Jain; rugosidade de projeto ε = 0,05 mm (PEAD envelhecido, conservador frente a 0,007 mm de tubo novo); ν = 1,004×10⁻⁶ m²/s (20 °C).

## 1. Demandas

- Vazão mínima de reposição (8 m³ em 8 h): `Q = V/t` = `8,0 m³ / 8 h` = **1,000 m³/h**
- Vazão simultânea na casa: `ΣQi = 9 + 9 + 12 + 6` = `36 L/min` = **36 L/min**
- Vazão simultânea (SI): `Q = 36/60 000` = **0,600 L/s**
- Vazão simultânea (m³/h): `Q = 0,6 × 3,6` = **2,16 m³/h**
- Tempo para consumir 8 m³ na vazão simultânea: `t = V/Q` = `8 / 2,16` = **3,70 h**

Interpretação: a vazão simultânea (2,16 m³/h) consumiria 8 m³ em 3,7 h; logo, ela é uma condição de pico de curta duração e não deve ser confundida com o volume diário. A bomba de captação é dimensionada pelo volume diário (reposição) e a pressurização pela vazão simultânea.

## 2. Caixa d'água — volumes e níveis (dependem do desenho certificado)

- Área interna: `A = π·Di²/4` = `π·3,96²/4` = **12,316 m²**
- Altura útil até o extravasor p/ 50 m³: `h = V/A` = `50/12,316` = **4,060 m**

| Nível | Cota (m) | Volume acumulado (m³) |
|---|---|---|
| dreno_N3_eixo | 113,62 | 0,9 |
| saida_N2_eixo | 113,80 | 3,1 |
| LSLL_desliga_booster | 114,15 | 7,4 |
| LAL_alarme_baixo | 114,50 | 11,7 |
| P1_liga | 116,80 | 40,0 |
| P1_desliga | 117,35 | 46,8 |
| LAHH_alarme_muito_alto | 117,50 | 48,6 |
| extravasor_N4_soleira | 117,61 | 50,0 |
| entrada_N1_descarga_livre | 117,80 | 52,3 |
| borda_cheio_total | 117,95 | 54,2 |

- Volume operacional (LSLL → P1 desliga): `V = (117,35−114,15)·A` = **39,4 m³**
- Volume abaixo de LSLL (sedimentos/submergência): `V = (114,15−113,55)·A` = **7,4 m³**
- Volume da histerese de partida de P-101: `V = (117,35−116,80)·A` = **6,8 m³**
- Autonomia com P-101 parada (consumo 8 m³/d): `t = V_op/8` = **4,9 dias**

Observação: dos 50 m³ nominais, ~39 m³ são operacionais; ~7 m³ ficam abaixo do desligamento do booster para proteger contra vórtice/ar e reter sedimentos. A autonomia de ~5 dias cobre falha da captação, mas NÃO cobre falha do booster ou de energia (a casa está acima da caixa).

## 3. Captação e recalque rio → caixa (P-101)


Escolha da vazão: Q_min = 1,0 m³/h atenderia exatamente 8 h/dia, sem folga para retrolavagem do filtro, perdas de rendimento por desgaste/areia e enchimento inicial. Adotado **Q = 3,0 m³/h** (fator 3 sobre o mínimo), mantendo velocidade ~1 m/s em DE 40 e potência pequena.

- Tempo diário de bombeamento: `t = 8/3,0` = **2,67 h/dia**  **OK**
- Enchimento inicial (caixa vazia até P1 desliga): `t = (117,35−113,55)·A/Q` = `46,8/3,0` = **15,6 h**
- Enchimento inicial até o extravasor (50 m³): `t = 50/3,0` = **16,7 h**
- Diâmetro interno PEAD DE40 SDR11: `Di = DE − 2e` = `40 − 2·3,7` = **32,6 mm**
- Velocidade: `v = Q/A` = `0,00083/0,000835` = **0,998 m/s**  **OK**
- Reynolds: `Re = v·D/ν` = **32.417 -**
- Fator de atrito (Swamee-Jain): `f = 0,25/[log(ε/3,7D + 5,74/Re^0,9)]²` = **0,0271 -**
- Perda distribuída (L = 115 m): `hf = f·L/D·v²/2g` = **4,85 m**
- Perdas localizadas: `hl = ΣK·v²/2g` = `12,3·0,0508` = **0,62 m**

| Cenário | Hest (m) | Hman a 3,0 m³/h (m) |
|---|---|---|
| Rio mínimo 97,50 + filtro sujo (PROJETO) | 20,30 | 32,3 |
| Rio normal 100,00 + filtro limpo | 17,80 | 26,8 |
| Rio máximo 102,00 + filtro limpo | 15,80 | 24,8 |


**Ponto de operação de projeto P-101: Q = 3,0 m³/h; Hman ≥ 33 m** (rio no mínimo, filtro no limite de retrolavagem, +10 % nas perdas). A bomba deve operar de forma estável também em Hman ≈ 25 m (rio cheio, filtro limpo), com vazão maior — o motor deve ser não-sobrecarregável em toda a faixa (verificar na curva do fornecedor).


Curvas do sistema (para cruzar com a curva real do fornecedor):


| Q (m³/h) | H rio mín/filtro sujo (m) | H rio normal/limpo (m) | H rio máx/limpo (m) |
|---|---|---|---|
| 0,0 | 20,3 | 17,8 | 15,8 |
| 1,0 | 21,8 | 18,9 | 16,9 |
| 2,0 | 25,8 | 22,0 | 20,0 |
| 3,0 | 32,3 | 26,8 | 24,8 |
| 3,5 | 36,5 | 29,9 | 27,9 |
| 4,0 | 41,3 | 33,5 | 31,5 |
| 5,0 | 52,8 | 42,0 | 40,0 |

- Potência hidráulica: `Ph = ρ·g·Q·H` = `1000·9,81·0,00083·32,3` = **264 W**
- Potência no eixo (η_bomba = 0,50 [H]): `Pe = Ph/η` = **529 W**

Motor recomendado: 0,75 kW a 1,1 kW, trifásico 380 V 60 Hz, submersível 4" — definir com a curva de potência real (não-sobrecarregável até ~5 m³/h). Para cálculos elétricos adotou-se 1,1 kW (conservador).

### 3.1 Submergência e NPSH da bomba submersa

- Submergência do crivo no nível mínimo: `S = 97,50 − 96,30` = **1,20 m**
- NPSH disponível (perda na entrada desprezível): `NPSHd = Patm + S − pv` = `9,30 + 1,20 − 0,43` = **10,07 m**

A submergência mínima exigida (vórtice, arrefecimento do motor) é dado do fabricante e deve ser ≤ 1,2 m. **Pré-condição crítica:** o leito do rio no ponto de captação deve estar em cota ≤ 95,70 m (hipótese). Se o leito for mais raso, será necessário poço escavado no leito ou galeria/poço de infiltração na margem.

### 3.2 Transiente hidráulico (golpe de aríete) — parada brusca por falta de energia

- Celeridade (PE100, E≈1,0 GPa curta duração [H]): `a = √[(K/ρ)/(1 + K·D/(E·e))]` = **329 m/s**
- Período da tubulação: `T = 2L/a` = `2·115/329` = **0,70 s**
- Sobrepressão de Joukowsky (pior caso, fechamento < T): `ΔH = a·Δv/g` = `329·0,998/9,81` = **33,4 m**
- Pressão máxima estimada na bomba (Hman + ΔH + 10 m de margem p/ shutoff): **76 m**  **OK**
- Linha piezométrica mínima após a onda negativa, junto à bomba: `HGL = 97,50 + Hman − ΔH` = **96,4 m**
- Pressão mínima na crista do talude (cota 103,0): `p = HGL − z` = **-6,6 m.c.a.**

Resultado: pressão máxima muito inferior à classe PN16 (160 m), mas a onda negativa pode levar a pressões subatmosféricas no trecho do talude (risco de separação de coluna). Medidas adotadas: partida/parada suave (soft-starter com rampa de desaceleração ≥ 5 s = 7×T) para paradas normais; válvula de retenção de fechamento rápido (mola) junto à bomba; tubo SDR11 (rigidez elevada ao vácuo — confirmar com fabricante). Análise transiente com perfil real (método das características) é exigida no executivo.

- Sobrepressão aproximada com rampa de 5 s: `ΔH ≈ ΔH_J·T/t_r` = **4,7 m**
## 4. Abastecimento caixa → casa


Verificação por gravidade: nível máximo operacional 117,35 m < ponto mais alto 122,50 m — a água **não chega à casa por gravidade** em nenhuma condição; para 15 m.c.a. seria necessária linha piezométrica de 137,50 m (≈ 20 m acima do nível máximo da caixa). **Pressurização é indispensável** e o abastecimento da casa depende de energia elétrica.

- Linha piezométrica requerida no ponto mais alto: `HGL = 122,50 + 15` = **137,50 m**
- Sucção DE63: velocidade: `v = Q/A` = **0,289 m/s**
- Sucção: perdas totais: `hf + ΣK·v²/2g` = `0,020 + 6,7·0,0043` = **0,048 m**
- Recalque DE40: velocidade: `v = Q/A` = **0,719 m/s**  **OK**
- Recalque: perda distribuída (L = 160 m): `hf = f·L/D·v²/2g` = `f = 0,0285` = **3,68 m**
- Recalque: perdas localizadas: `ΣK·v²/2g` = `9,9·0,0263` = **0,26 m**

| Condição | Desnível + 15 m (m) | Hman a 2,16 m³/h (m) |
|---|---|---|
| Nível baixo (LSLL 114,15) — PROJETO | 23,35 | 30,7 |
| Nível alto (117,35) | 20,15 | 27,5 |


**Ponto de operação de projeto P-201: Q = 2,2 m³/h; Hman ≥ 31 m.**

- Setpoint de pressão na descarga do booster (controle por inversor): `p = HGL_req + perdas a jusante − z_bomba` = `137,50 + 7,33 − 112,30` = **32,5 m.c.a.**
- Pressão estática máxima no térreo da casa (vazão nula, setpoint mantido): `p = HGL_desc − 120,00` = **24,8 m.c.a.**  **OK**

Com controle por inversor mantendo pressão constante na descarga, a pressão no ponto mais alto fica ≥ 15 m.c.a. em vazão máxima e sobe até ~22 m.c.a. com vazão baixa; a pressão estática na casa fica abaixo do limite de 40 m.c.a. usualmente adotado para instalações prediais (NBR 5626 — confirmar texto vigente).

- NPSH disponível do booster (nível LSLL): `NPSHd = Patm + Δz − hs − pv` = `9,30 + 1,85 − 0,048 − 0,43` = **10,67 m**
- Submergência mínima anti-vórtice (ANSI/HI 9.8: S = D(1+2,3·Fr)): `S` = `0,0514·(1+2,3·0,407)` = **0,100 m**
- Submergência disponível em LSLL: `S = 114,15 − 113,80` = **0,35 m**  **OK**
- Potência hidráulica booster: `Ph = ρ·g·Q·H` = **181 W**
- Potência no eixo (η = 0,40 [H], bomba pequena): `Pe = Ph/η` = **452 W**

Motor recomendado: 0,75 kW trifásico 380 V por bomba; conjunto duplex (1 operação + 1 reserva, alternância).

- Golpe na parada brusca do booster: `ΔH = a·v/g` = `329·0,719/9,81` = **24,1 m**
- Pressão máxima estimada (Hman + ΔH + 10 m): **65 m**  **OK**
## 5. Extravasor, dreno e limpeza


Vazão máxima afluente admitida: 6 m³/h (P-101 com rio cheio e filtro limpo; 2× a vazão de projeto, a confirmar na curva). Extravasor DN 100 (DE 110):

- Lâmina sobre a boca do extravasor (vertedor circular): `h = [Q/(1,84·π·D)]^(2/3)` = **20 mm**

Lâmina de ~20 mm ⇒ nível máximo com extravasamento ≈ 117,630 m, abaixo da descarga livre da entrada (117,80) — a entrada nunca fica afogada.

- Esvaziamento total por dreno DE75 totalmente aberto: `t = 2A/(Cd·a·√2g)·(√h0 − √h1)` = **62 min**
- Vazão de pico no dreno totalmente aberto: `Q = Cd·a·√(2g·h0)` = **18,1 L/s**

A vazão de pico (~18 L/s) é erosiva para descarte no terreno. Procedimento adotado: (1) consumir a água via irrigação até LSLL; (2) drenar o volume remanescente (~7 m³ + lodo) com registro de estrangulamento limitado a ≤ 3 L/s (≈ 40 min), para caixa de decantação e dispersão/infiltração afastada da fundação; (3) desclorar a água antes do lançamento.

- Tempo de drenagem do volume remanescente a 3 L/s: `t = 7,4 m³ / 3 L/s` = **41 min**
