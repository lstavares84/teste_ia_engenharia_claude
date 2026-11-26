# Memória de Cálculo — Estrutura Metálica, Ligações e Fundação (preliminar)


Ferramenta: Python 3.12 + numpy — solver próprio de viga contínua por elementos finitos (Euler-Bernoulli, 440 elementos por viga), verificado contra solução analítica de viga contínua de 2 vãos (ver item 9). Perfis com propriedades calculadas a partir das dimensões nominais (d, bf, tw, tf), sem raios de concordância (conservador). **Pré-dimensionamento para estudo — não liberar para fabricação.**

## 1. Configuração estrutural adotada


Plataforma quadrada 4,40 × 4,40 m com chapa de piso contínua (apoio plano integral da base da caixa), sobre 11 vigas secundárias (direção Y, espaçamento 0,44 m, contínuas sobre 3 apoios), apoiadas em 3 vigas principais (direção X, contínuas sobre 3 pilares), 9 pilares curtos (grelha 3×3, vão 2,20 m), contraventamento em X nas 4 faces, placas de base com chumbadores sobre pedestais de um radier de concreto armado. Plataforma de serviço de 1,10 m no lado leste (acesso a registros dos bocais e à escada da caixa).


Justificativa: (a) a forma de apoio exigida pelo fabricante não é conhecida; o apoio plano contínuo atende ao caso mais exigente usual de caixas de fundo plano e também a apoio por anel (com reverificação); (b) a grelha 3×3 limita vãos a 2,20 m, reduzindo altura dos perfis — importante porque a base da caixa está a apenas 1,50 m do terreno; (c) ligações parafusadas permitem galvanização a fogo de todas as peças.

## 2. Ações características

- Altura de água máxima (até a borda — extravasor obstruído): `h = 117,95 − 113,55` = **4,40 m**
- Pressão hidrostática no fundo: `p = γw·h` = `9,81·4,40` = **43,16 kPa**
- Peso da água (sobre a projeção Ø4,00 — conservador): `W = p·π·R²` = `43,16·12,566` = **542,4 kN**
- Peso da caixa vazia: `W = 1200·9,81` = **11,77 kN**
- Peso da chapa de piso: `g = t·ρ·g` = **0,732 kPa**

Hipóteses: o peso da caixa foi distribuído uniformemente na base (conservador para vigas centrais; se o fabricante indicar carga concentrada no costado, reverificar as vigas sob o perímetro). Água considerada até a borda (caso físico máximo) com γq = 1,50 (sem o benefício de 'ação truncada', que permitiria 1,20 — decisão conservadora a revisar no executivo).

### 2.1 Vento (formulação da NBR 6123:1988 — a edição vigente é 12/2023 com errata 04/2025; refazer no executivo)

- S2 (cat. II, classe A, z = 6,0 m): `S2 = b·Fr·(z/10)^p` = `1,00·1,00·(6,0/10)^0,085` = **0,958 -**
- Velocidade característica: `Vk = V0·S1·S2·S3` = `45·1,0·0,958·1,0` = **43,1 m/s**
- Pressão dinâmica: `q = 0,613·Vk²` = **1,138 kPa**
- Força na caixa: `F = Ca·q·Ae` = `0,80·1,138·18,0` = **16,39 kN**
- Força na escada/gaiola e estrutura (estimativa): `F = Ca·q·A + 10 %·F_caixa` = **3,82 kN**
- Força horizontal total de vento: **20,21 kN**

Sensibilidade: com S1 = 1,10 (encosta) a força cresce 21 %; com V0 = 40 m/s reduz 21 %. O efeito é pequeno frente ao peso da água, mas é **governante para a caixa vazia**.

- Momento do vento na base da caixa (deck): `M = F·h/2` = `16,39·2,25` = **36,87 kN·m**
### 2.2 Estabilidade da caixa vazia sobre o deck

- Momento estabilizante (caixa vazia): `Me = W·R` = `11,77·2,0` = **23,54 kN·m**
- Coeficiente ao tombamento sem ancoragem: `Me/Mt` = **0,64 -**  **NÃO ATENDE**
- Deslizamento sem ancoragem (μ = 0,3 [H]): `μ·W/F` = **0,22 -**  **NÃO ATENDE**
- Tração de cálculo por ancoragem (8 pontos no perímetro): `Td = 1,4·M/(4·R) − 1,0·W/8` = `1,4·36,87/(4·2,05) − 11,77/8` = **4,82 kN**
- Cisalhamento de cálculo por ancoragem: `Vd = 1,4·F/8` = **2,87 kN**

**Conclusão: a caixa vazia tomba e desliza com o vento de projeto se não for ancorada.** São necessárias ancoragens (olhais/abas do fabricante ou cintas) fixadas ao deck — dado obrigatório a solicitar ao fornecedor (pontos, cargas admissíveis, tipo de fixação). Pré-dimensionamento: 8 pontos, cada um com Td ≈ 5 kN e Vd ≈ 3 kN; chapa-olhal 9,5 mm soldada em fábrica ao vigamento (antes da galvanização) com 1 parafuso M16.

## 3. Chapa de piso (apoio da caixa)

- Carga de cálculo na chapa: `qd = 1,5·p_água + 1,4·g` = `1,5·43,16 + 1,4·1,768` = **67,22 kPa**
- Momento solicitante (faixa de 1 m, biapoiada — conservador): `Md = qd·s²/8` = **1,627 kN·m/m**
- Momento resistente plástico: `MRd = fy·t²/4/γa1` = **5,128 kN·m/m**  **OK**
- Flecha (serviço, biapoiada — conservador): `δ = 5qL⁴/384EI` = **1,53 mm**
- Limite adotado L/250: **1,76 mm**  **OK**

A planicidade/tolerância de apoio exigida pela caixa deve ser confirmada com o fornecedor. Parafusos da chapa com cabeça escareada (rente), para não criar pontos de carga no fundo da caixa.

## 4. Vigas secundárias (direção Y)


Perfil selecionado (o mais leve da lista W150x13,0, W150x18,0, W200x19,3, W200x26,6 que atende): **W150x13,0** — ASTM A572 Gr.50.

- Momento solicitante máximo (envoltória ELU): **18,00 kN·m**
- Momento resistente (Lb = 1,10 m, Cb = 1): `MRd = min(FLT, FLM, FLA)` = `FLT 27,7; FLM 27,7; FLA 28,4` = **27,66 kN·m**  **OK**
- Cortante solicitante máximo: **41,91 kN**
- Cortante resistente: `VRd = 0,6·fy·d·tw/γa1` = **119,8 kN**  **OK**
- Flecha máxima (ELS, G+Q): **2,05 mm**
- Limite L/350 (NBR 8800 Anexo C): **6,29 mm**  **OK**
- Reação máxima de cálculo de uma secundária sobre a viga principal: **82,2 kN**
- Escoamento local da alma no apoio central: `FRd = (5k + lb)·fy·tw/γa1` = **255,6 kN**  **OK**
- Enrugamento da alma: `FRd = 0,80·tw²·[1+3(lb/d)(tw/tf)^1,5]·√(E·fy·tf/tw)/γa1` = **447,1 kN**  **OK**
## 5. Vigas principais (direção X)


Perfil selecionado (o mais leve da lista W200x26,6, W200x31,3, W200x35,9, W250x32,7, W250x38,5 que atende): **W200x31,3** — ASTM A572 Gr.50. Cargas = reações das 11 secundárias (cargas concentradas a cada 0,44 m).

- Momento solicitante máximo (envoltória ELU): **95,30 kN·m**
- Momento resistente (Lb = 1,10 m): `FLT 103,7; FLM 103,7; FLA 103,7` = **103,69 kN·m**  **OK**
- Cortante solicitante máximo: **200,5 kN**
- Cortante resistente: **252,9 kN**  **OK**
- Flecha máxima (ELS): **2,09 mm**
- Limite L/350: **6,29 mm**  **OK**

Enrijecedores de apoio (chapas 9,5 mm, ambos os lados da alma) sobre cada pilar e nas cargas concentradas das secundárias alinhadas com pilares — boa prática obrigatória pela alta reação no pilar central.

## 6. Pilares, contraventamento, placas de base e chumbadores


Reações características nos pilares (kN) — linhas = eixo Y (sul→norte), colunas = eixo X (oeste→leste):


*Permanente G (caixa vazia + estrutura + chapa)*


|  | X1 | X2 | X3 |
|---|---|---|---|
| Y1 | 1,3 | 4,3 | 1,3 |
| Y2 | 4,3 | 15,2 | 4,3 |
| Y3 | 1,3 | 4,3 | 1,3 |


*Água até a borda Q*


|  | X1 | X2 | X3 |
|---|---|---|---|
| Y1 | 6,0 | 54,8 | 6,0 |
| Y2 | 55,3 | 298,3 | 55,3 |
| Y3 | 6,0 | 54,8 | 6,0 |

- Soma das reações G: **37,8 kN**
- Soma das reações Q (confere com W_água): `W_água = 542,4` = **542,5 kN**  **OK**
- Altura livre do pilar (placa de base → mesa inferior da viga): **0,960 m**
- Momento do vento na base dos pilares: `M = F_caixa·z + F_outros·2,5` = **68,6 kN·m**
- Variação de normal nos pilares de borda por vento (distribuição rígida): `ΔN = M·x/Σx²` = `68,6·2,2/29,04` = **5,19 kN**
- Normal de cálculo máxima (pilar central/borda, 1,4G+1,5Q+1,4W): **476,0 kN**
- Normal mínima, caixa vazia (1,0G − 1,4W): **-5,95 kN**

Com a caixa vazia e vento, os pilares de canto ficam levemente tracionados ⇒ os chumbadores são necessários também por arrancamento (não apenas por montagem).


Pilares: todas as faces contraventadas e o deck (chapa parafusada + vigas) atua como diafragma ⇒ topo dos pilares indeslocável, K = 1,0. Excentricidade acidental de 5 cm na reação da viga (desalinhamento de montagem, vãos com cargas desiguais). A W150×22,5 foi testada e resultou em interação 0,98–1,07 (dependendo de K) — descartada por margem insuficiente; adotada **W150×29,8** em todos os pilares (padronização).

- Resistência à compressão W150x29,8 (K = 1,0, L = 0,96 m): `NcRd = χ·Q·A·fy/γa1` = `χ = 0,955; λ0 = 0,330; Q = 1,00` = **1.126,4 kN**
- Interação N+M (excentricidade acidental 5 cm): `N/NRd + 8/9·M/MRd` = `476,0/1.126,4 + 8/9·23,8/75,8` = **0,702 -**  **OK**
- Força horizontal de cálculo: `Hd = 1,4·Fw` = **28,30 kN**
- Ângulo da diagonal: `θ = atan(h/2,20)` = **23,6 °**
- Tração na diagonal (4 diagonais tracionadas por direção): `Nt = Hd/(4·cosθ)` = **7,72 kN**
- Resistência barra redonda Ø16 A36 (rosca: 0,75·Ab·fu/γa2): **44,7 kN**  **OK**
- Pressão de contato na placa 300×300: `σ = Nd/(B·N)` = **5,29 MPa**
- Resistência ao esmagamento do concreto (A2 = A1): `σRd = fck/(γc·γn)` = `30/(1,4·1,4)` = **15,31 MPa**  **OK**
- Espessura mínima da placa de base (balanço l): `t = l·√(2σ/(fy/γa1))` = `l = 89 mm` = **19,2 mm**  **OK**
- Cisalhamento por pilar contraventado (conservador): `V = Hd/4` = **7,07 kN**
- Cisalhamento resistente 4×M20 F1554 Gr36: `4·0,4·Ab·fub/γa2` = **148,9 kN**  **OK**
- Tração por chumbador (arrancamento: componente vertical da diagonal + levantamento): **3,03 kN**
- Tração resistente por chumbador M20: `0,75·Ab·fub/γa2` = **69,8 kN**  **OK**

Chumbadores: 4 × M20 ASTM F1554 Gr.36 galvanizados, comprimento de ancoragem ≥ 400 mm com placa/porca na extremidade (ancoragem a confirmar pela NBR 6118 e ensaios do fornecedor do sistema de ancoragem, se químico). Mesmo sem tração calculada relevante, a especificação mínima atende a montagem, a caixa vazia e esforços acidentais.

## 7. Ligações (pré-dimensionamento)

- Resistência ao corte, parafuso M16 A325 (rosca no plano): `0,4·Ab·fub/γa2` = **49,1 kN**
- Resistência ao corte, parafuso M12 A325 (rosca no plano): `0,4·Ab·fub/γa2` = **27,6 kN**
- Secundária × principal: apoio direto (empilhada), 4 × M16 — transfere apenas forças horizontais/estabilidade; esforço horizontal por ligação ≤ Hd/11 = 2,57 kN ≪ 4·49,1 kN.
- Principal × pilar: chapa de topo 250×250×16 soldada ao pilar (fábrica) + 4 × M16; enrijecedores de apoio na viga.
- Pilar × placa de base: solda de filete 6 mm em todo o contorno (fábrica, antes da galvanização).
- Resistência da solda de filete 6 mm (E70, por metro): `0,6·fw·0,707·a/γw2` = **914,4 kN/m**
- Comprimento de solda disponível no contorno: **0,889 m**
- Capacidade total da solda pilar-placa: **813 kN**  **OK**
- Nota: a compressão é transmitida por contato (topo do pilar fresado/esquadrejado) — a solda dimensionada para ≥ 25 % de Nd e para os esforços horizontais.
- Diagonais Ø16 com esticador e chapas gusset 8 mm soldadas aos pilares; 1 × M16 por extremidade (Nt = 7,7 kN < 49,1 kN).
- Chapa de piso × secundárias: parafusos M12 cabeça escareada a cada 300 mm ao longo das juntas dos painéis.
## 8. Quantitativo preliminar de aço


| Item | Qtd | L ou área (m/m²) | kg/m ou kg/m² | Massa (kg) |
|---|---|---|---|---|
| Vigas secundárias W150x13,0 | 11 | 4,40 | 12,4 | 598 |
| Vigas principais W200x31,3 | 3 | 4,40 | 31,0 | 409 |
| Pilares W150x29,8 | 9 | 0,96 | 29,5 | 255 |
| Postes da plataforma W150x29,8 | 3 | 1,29 | 29,5 | 114 |
| Vigas da plataforma W150x13,0 | 3 | 1,10 | 12,4 | 41 |
| Viga de borda da plataforma W150x13,0 | 1 | 4,40 | 12,4 | 54 |
| Chapa de piso 9,5 mm | 1 | 19,36 | 74,6 | 1.444 |
| Placas de base 300×300×22,4 | 12 | 0,09 | 175,8 | 190 |
| Diagonais Ø16 (8 painéis × 2) | 16 | 2,40 | 1,6 | 61 |
| Piso grade da plataforma (30 kg/m² [F]) | 1 | 4,84 | 30,0 | 145 |
| Guarda-corpo (15 kg/m [H]) | 1 | 10,60 | 15,0 | 159 |
| Escada da plataforma (verba) | 1 | 1,00 | 180,0 | 180 |
| Escada marinheiro c/ gaiola e patamar superior (verba) | 1 | 1,00 | 260,0 | 260 |
| Ligações, enrijecedores, parafusos (6 %) |  |  |  | 235 |
| **TOTAL** |  |  |  | **4.144** |

## 9. Fundação — radier (pré-dimensionamento, SEM SONDAGEM)


Radier 6,30 × 5,40 × 0,40 m, concreto C30, sobre lastro de 5 cm e base compactada; topo na cota 112,00; pedestais 50×50 cm até 112,12. Cotas e área: ver desenhos DES-03/DES-04.

- Peso do radier: `W = L·B·h·25` = **340,2 kN**
- Carga total de serviço na base (água até a borda): `N = Wágua + Wcaixa + Waço + Wradier + Wped + plataforma` = **958,6 kN**
- Pressão média no solo: `σ = N/A` = `958,6/34,02` = **28,2 kPa**
- Pressão máxima com vento: `σ = N/A + M/W` = **30,3 kPa**
- Comparação com σadm hipotético = 100 kPa [H — sem sondagem]: **0,30 -**  **OK**
- Segurança ao tombamento global (caixa vazia): `FS = N·B/2 / Mt` = **14,1 -**  **OK**
- Segurança ao deslizamento (tanφ = 0,45 [H]): `FS = 0,45·N/Fw` = **8,9 -**  **OK**
- Normal de cálculo no pilar central: **469,8 kN**
- Força de punção (descontada reação do solo dentro de C'): `Fsd = Nd − σd·A_C'` = **389,9 kN**
- Tensão solicitante no contorno C' (2d): `τSd = Fsd/(u·d)` = `u = 6,27 m; d = 0,34 m` = **0,183 MPa**
- Tensão resistente sem armadura de punção (NBR 6118, 19.5): `τRd1 = 0,13(1+√(20/d))(100ρfck)^(1/3)` = `ρ = 0,185 %` = **0,407 MPa**  **OK**
- Momento estático total por painel 2,2 m (método direto, reação uniforme): `M0 = q·l2·ln²/8` = **20,7 kN·m**
- Armadura mínima por face e direção (ρmin = 0,15 %): `As = 0,0015·b·h` = **6,00 cm²/m**
- Armadura de flexão necessária na faixa dos pilares (estimativa): `As = 0,65·0,75·M0/l/(0,9·d·fyd)` = **0,35 cm²/m**

Adotado (preliminar): malha Ø10 c/ 12,5 cm (6,28 cm²/m) nas duas faces e duas direções; arranques dos pedestais 4 Ø12,5 + estribos Ø6,3 c/ 15. Cobrimento 40 mm. A armadura mínima governa.


Alternativa avaliada: 9 sapatas isoladas ligadas por vigas-baldrame. Com σadm = 100 kPa a sapata do pilar central precisaria de ≈ 1,86 m de lado, e as de canto ≈ 0,8 m — carga muito desigual (central ≈ 30 % do total), com risco de recalque diferencial sob o deck que apoia a caixa. O radier foi preferido por uniformizar recalques e tolerar solo desconhecido; a escolha final depende da sondagem.


**Riscos geotécnicos a investigar:** solos porosos colapsíveis são frequentes no interior de SP — umedecimento por vazamento, extravasamento ou drenagem pode causar recalque brusco; o platô está em encosta (corte/aterro); nível d'água desconhecido. Requisitos mínimos: sondagens SPT (NBR 6484) — mínimo 3 furos na área da caixa e 1 na captação — com ensaio de colapsibilidade se houver solo poroso, e afastamento de toda descarga de água ≥ 10 m da fundação.

## 10. Verificação do solver (viga contínua de 2 vãos, carga uniforme)

- Reação central FE: **27,500 kN**
- Reação central analítica: `R = 1,25·q·L` = `1,25·10·2,2` = **27,500 kN**  **OK**
- Momento no apoio central FE: **6,050 kN·m**
- Momento analítico: `M = qL²/8` = `10·2,2²/8` = **6,050 kN·m**  **OK**
