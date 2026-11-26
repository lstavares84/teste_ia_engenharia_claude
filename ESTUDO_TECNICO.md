# Estudo técnico preliminar: captação de água de rio, caixa de 50 m³ e abastecimento não potável de residência rural

**Natureza do documento:** estudo de engenharia para exercício, em caso fictício. É uma concepção com pré-dimensionamento. **Não serve para fabricação, construção ou operação.**
**Data:** 26/11/2026. **Revisão:** 0.
**Equipe simulada:** estruturas metálicas e fundações, hidráulica e bombeamento, elétrica e automação, modelagem 3D.
**Responsabilidade técnica:** nenhuma ART foi emitida. O projeto executivo exige profissionais habilitados no CREA-SP, com ART por disciplina (Lei 6.496/1977; Res. CONFEA 1.137/2023, alterada pela 1.160/2025).

> Como ler: cada dado traz a origem entre colchetes. **[C]** = dado do cliente; **[H]** = hipótese do estudo; **[F]** = depende de fornecedor; **[L]** = depende de levantamento de campo; **[N]** = critério normativo ou de literatura. As memórias de cálculo completas e reproduzíveis estão em `calc/resultados/MC-01…MC-03`. Este relatório resume os resultados e remete a elas.

---

## 0. Resumo para o proprietário

| Pergunta | Resposta curta |
|---|---|
| Captar água do rio? | **Sim, em princípio.** A solução é uma bomba submersa dentro de um tubo-camisa inclinado no talude, sem energia na margem. A viabilidade depende de o leito estar ≥ 1,8 m abaixo do nível mínimo no ponto de captação (batimetria **[L]**). |
| Encher e manter os 50 m³? | **Sim.** Com 3,0 m³/h, a reposição diária leva 2,7 h (limite: 8 h). O enchimento inicial leva ~17 h e deve ser dividido em pelo menos 2 dias para não passar de 25 m³/dia (limite de dispensa de outorga em SP, a confirmar). |
| Sustentar a caixa? | **Sim, no pré-dimensionamento.** Estrutura de 4,1 t de aço sobre radier. **A caixa vazia tomba com o vento se não for ancorada**: a ancoragem é obrigatória e depende do fabricante. |
| Água na casa com 15 m.c.a.? | **Só com bombeamento.** A casa fica acima da caixa (122,50 m contra no máximo 117,35 m), então a gravidade nunca atende. Um pressurizador duplex na área da caixa entrega 2,2 m³/h a 31 m. **Sem energia não há água não potável na casa.** |
| Operar e manter com segurança? | Sim, com automação por níveis, intertravamentos e alarmes. As válvulas ficam acessíveis por plataforma, a bomba do rio é retirável e os quadros têm bloqueio. |
| Cabe na área 8 × 8 m? | **Não por completo.** Estrutura e radier cabem, mas abrigo, caixa de recepção e pé da escada pedem uma faixa adicional de **4,5 × 8 m**, mais área temporária para o guindaste. |
| Atende às normas? | O estudo aplica os critérios das normas identificadas. **Atendimento formal só no executivo**: várias normas têm edição nova (NBR 6123:2023, NBR 8800:2024, NBR 8681:2025, NBR 5419:2026), e as licenças (outorga/dispensa, APP, descarte) ainda não existem. |

---

## 1. Escopo, limites e convenções

**Dentro do escopo:** captação no rio; recalque até a caixa; caixa com estrutura metálica e fundação; pressurização e linha até a casa; drenagem, extravasão e descarte; elétrica e automação; modelo 3D e desenhos.

**Fora do escopo:** instalações internas da casa e o sistema potável existente.

**Limite físico do projeto na casa:** a caixa de entrada **CE-01**, a cerca de 1 m da fachada. O limite fica na flange ou união a jusante do registro VE-01. Daí em diante vale o projeto interno, a cargo de terceiros, conforme a NBR 5626:2020 e a NBR 16783:2019. Para detalhar os pontos internos são necessários:
- planta e cortes da casa;
- posição e cota real do ponto mais alto;
- lista de aparelhos e vazões;
- traçado e diâmetros internos;
- ponto de interface com a irrigação.

**Coordenadas usadas no estudo:**
- X: ao longo do traçado, com X = 0 na borda d'água do nível mínimo, no ponto de captação.
- Y: transversal, positivo para norte.
- Z: cota na referência fictícia do cliente.
- Centro da caixa: X = 79,60, Y = 0.
- Área 8 × 8 m: X de 76 a 84, Y de −4 a +4.
- Entrada da casa: X = 219,60.

**Ferramentas:**
- Python 3.12 com numpy: cálculos, geração do modelo e desenhos.
- Formatos produzidos: FreeCAD (macro), OBJ, glTF/GLB, three.js (visualizador web) e SVG.
- Todos os resultados saem de **uma única fonte de premissas**, `calc/premissas.py`. Mudar uma premissa e rodar os scripts atualiza cálculos, modelo e desenhos de forma consistente (ver seção 13).

---

## 2. Levantamento e premissas (item 10)

### 2.1 Dados fornecidos pelo cliente [C]

| Item | Valor |
|---|---|
| Níveis do rio (mín./normal/máx.) | 97,50 / 100,00 / 102,00 m |
| Terreno: margem, área da caixa, piso da casa | 103,00 / 112,00 / 120,00 m |
| Ponto de consumo mais alto | 122,50 m, com p ≥ 15 m.c.a. dinâmica |
| Distâncias horizontais | rio → área da caixa 80 m; área da caixa → casa 140 m |
| Caixa (fornecedor fictício) | 50 m³ úteis; Ø 4,00 × 4,50 m; 1.200 kg vazia; vertical, apoiada pela base, ao tempo |
| Base da caixa | 1,50 m acima do terreno; área disponível 8 × 8 m |
| Demanda | 8.000 L/dia (4.000 descarga/lavagem + 4.000 irrigação); simultâneo 2×9 + 12 + 6 = 36 L/min |
| Reposição | 8 m³ em até 8 h de bombeamento por dia |
| Energia | trifásica 380 V, 60 Hz, junto à caixa e à casa; nenhuma na margem |
| Uso da água | somente descarga, lavagem de pisos e irrigação; sistema potável separado, fora do escopo |

### 2.2 Dados que precisam ser confirmados em campo [L]

| Levantamento | Por quê | Afeta |
|---|---|---|
| Planialtimétrico cadastral (curvas a cada 0,5 m) do rio até a casa, com faixa de ~20 m e estradas, cercas e redes | Traçado real, pontos altos e baixos (ventosas e drenos), comprimentos, travessias, platô da caixa | perdas de carga, transientes, terraplenagem, quantitativos |
| Batimetria e seções do rio no ponto de captação; largura da calha regular; marcas de cheia | Confirmar leito ≤ 95,70 m, submergência e faixa de APP (30 m ou 50 m) | viabilidade da captação, licenciamento |
| Sondagens SPT (NBR 6484:2020) programadas conforme a NBR 8036: mínimo 3 furos na área da caixa e 1 na margem; nível d'água; ensaio de colapsibilidade se houver solo poroso; ensaio de infiltração na área de descarte | Fundação, estabilidade do talude, vala de infiltração | radier, contenção da margem, descarte |
| Análise da água do rio em 2 campanhas, na estiagem e na chuva | Definir tratamento e malha do filtro | equipamentos de tratamento, desgaste da bomba |
| Quadro elétrico existente: posição, capacidade livre, proteção geral, corrente de curto-circuito, esquema de aterramento, presença de neutro (380/220 V?), qualidade da tensão | Alimentar o QCB-01 com segurança | alimentador, proteções, DR |
| Posição da entrada potável existente e das redes enterradas | Evitar cruzamentos e ligações cruzadas | traçado da TB-202 |
| Acesso de caminhão e guindaste até a caixa (raio, patolamento, rede aérea) | Içamento da caixa (~1,2 t, Ø 4 m) | logística e área temporária |

### 2.3 Informações que dependem de fornecedores [F]

**Caixa (pedir desenho certificado e manual):**
- dimensões finais e massa;
- material e espessuras;
- forma de apoio exigida: plano integral, anel ou berço; planicidade; manta;
- bocais: posição, diâmetro, tipo e **cargas admissíveis**;
- tampa, boca de visita e ventilação com tela;
- extravasor;
- dreno de fundo;
- acesso ao teto e carga admissível do teto;
- **pontos e cargas de ancoragem**;
- resistência a UV;
- compatibilidade com cloro;
- garantia.

**Bombas e demais equipamentos:**
- **Bombas:** curvas H×Q, potência e NPSHr certificadas (ISO 9906:2012), faixa de operação, submergência mínima, instalação inclinada, tolerância a areia, comprimento máximo de cabo, vazão mínima.
- **Filtro:** perda de carga × vazão, malha, consumo na retrolavagem.
- **Hidrômetro:** perda de carga e saída pulsada.
- **Dosadora:** faixa de dosagem.
- **Tubos PEAD:** resistência ao vácuo (SDR 11).
- **Perfis:** dimensões nominais conforme catálogo e NBR 15980:2024.

### 2.4 Hipóteses adotadas para o exercício [H] e efeito nos resultados

| Hipótese | Valor adotado | Efeito se estiver errada |
|---|---|---|
| Perfil do terreno | interpolação linear entre as cotas informadas; talude da margem 1V:1,5H; platô da caixa em 112,00 | Pontos altos intermediários mudam perdas, transientes e ventosas. Talude mais íngreme ou instável exige contenção. |
| Leito do rio no ponto | ≤ 95,70 m (lâmina ≥ 1,8 m no nível mínimo) | Leito mais alto: poço escavado no leito ou poço/galeria de infiltração na margem (custo e licença maiores). |
| Caixa | diâmetro interno 3,96 m; fundo interno 113,55; bocais nas cotas do item 5 | Os níveis operacionais e o volume útil real mudam (±1 m³ por cm de diâmetro). |
| Comprimentos de tubo | P-101: 115 m; P-201: 160 m (traçado + 10 % + verticais) | Cada +10 % de comprimento soma ~0,5 m (P-101) ou ~0,4 m (P-201) de perda. |
| Perdas de equipamentos | filtro 2 m limpo e 5 m sujo; hidrômetros 1,0 m e 0,5 m; rede interna da casa 2,5 m | Hman de projeto muda na mesma medida. |
| Rugosidade | ε = 0,05 mm (PEAD envelhecido) | Com tubo novo (0,007 mm), a perda distribuída cai ~15 %. |
| Pressão atmosférica | 9,30 m.c.a. (altitude até ~900 m) | NPSH com margem ampla nos dois casos. |
| Rendimentos e cosφ | bomba 0,50 / 0,40; motores 0,75–0,78; cosφ 0,80 | Correntes e potências. Refazer com dados de placa. |
| Vento | V0 = 45 m/s; S1 = 1,0; S3 = 1,0; Ca = 0,8; formulação da NBR 6123:1988 | Com S1 = 1,1 a força sobe 21 %; com V0 = 40 m/s cai 21 %. **Governa a ancoragem da caixa vazia.** |
| Solo | σadm = 100 kPa, apenas para comparação | A pressão calculada (30 kPa) tem folga ampla, mas recalque e colapsibilidade **não podem ser avaliados** sem sondagem. |
| Água para estrutura | caixa cheia até a borda (55,3 m³ na projeção externa), γq = 1,5 | Conservador. O executivo pode justificar γ = 1,2 (ação truncada), o que reduz esforços ~20 %. |

### 2.5 Pontos que impedem a conclusão do projeto executivo

1. Sem desenho certificado da caixa: bocais, apoio, ancoragem, acesso ao teto.
2. Sem sondagem: fundação da caixa, estabilidade do talude, infiltração do descarte.
3. Sem topografia nem batimetria: traçado, perfil, ponto de captação, faixa de APP.
4. Sem análise da água: tratamento, malha do filtro, materiais.
5. Sem curvas reais de bombas e filtro: pontos de operação definitivos.
6. Dados do quadro elétrico existente desconhecidos.
7. Regularização pendente: outorga ou dispensa (SP Águas), autorização de intervenção em APP (CETESB) e destino do descarte.
8. Edições vigentes das normas não consultadas em texto integral (ver seção 12).

---

## 3. Concepção e alternativas avaliadas

### 3.1 Captação e bombeamento rio → caixa

| Alternativa | Avaliação | Decisão |
|---|---|---|
| A. Bomba de superfície na margem (sucção) | Eixo em ≥ 103,5 (acima da cheia). Sucção estática de 6,0 m no nível mínimo, NPSHd ≈ 9,3 − 6,0 − 0,5 − 0,43 ≈ 2,4 m (marginal). Exige válvula de pé (entope com folhas) e escorva. Exige energia na margem. | Rejeitada |
| B. **Bomba submersa em tubo-camisa inclinado no talude** | Sempre afogada (NPSHd ≈ 10 m). Dispensa válvula de pé e escorva. Retirada por içamento pelo eixo da camisa. Cabo contínuo a partir do QCB na área da caixa, sem quadro na margem. Opera de 97,50 a 102,00 sem ajustes. | **Adotada** |
| C. Bomba em flutuante | Acompanha o nível, mas fica exposta a galhos e troncos na cheia e exige ancoragem e acesso por água. | Rejeitada |
| D. Poço/galeria de infiltração na margem | Pré-filtra a água (reduz turbidez e areia), mas depende de solo permeável e de sondagem. | **Alternativa** se o leito for raso ou a turbidez alta |
| E. Bomba na área da caixa | Sucção de 14,5 m: fisicamente inviável. | Rejeitada |

**Quantidade de bombas na captação:** uma bomba em operação, com reserva fria em estoque. A caixa tem ~39 m³ operacionais, o que dá **4,9 dias de autonomia** para substituir a bomba sem desabastecer.

### 3.2 Abastecimento caixa → casa

| Alternativa | Avaliação | Decisão |
|---|---|---|
| Gravidade | O nível máximo da caixa (117,35) fica abaixo do piso da casa (120,00). Seria preciso linha piezométrica de 137,50. | **Impossível** |
| Elevar a caixa | A base teria de estar em ~133 m (~21 m acima do terreno). | Incompatível com o pedido do cliente (base a 1,50 m) |
| Reservatório elevado na casa | Torre de ~15 m acima do ponto mais alto. | Desproporcional |
| Booster na casa (sucção a 140 m) | Bomba ~6 m acima do nível da caixa, sucção longa: escorva e NPSH problemáticos. | Rejeitada |
| **Booster duplex na área da caixa com inversor (pressão constante)** | Sucção afogada, energia disponível no local, pressão constante, alternância e reserva automáticas. | **Adotada** |

### 3.3 Estrutura e fundação

| Alternativa | Avaliação | Decisão |
|---|---|---|
| **Grelha 3×3 pilares com deck de chapa contínua** | Apoio plano integral (atende o caso mais exigente de fundo plano). Vãos de 2,20 m com perfis baixos. Tudo parafusado e galvanizado. | **Adotada** |
| 4 pilares nos cantos | Vão de 4,4 m com 542 kN: vigas altas (~W360+) num espaço de 1,5 m. | Rejeitada |
| Anel/berço sob o costado | Só cabe se o fabricante exigir esse tipo de apoio. | Reavaliar com dados do fornecedor |
| **Radier único** | Pressão baixa (~30 kPa), recalque uniforme sob o deck, tolera solo desconhecido. | **Adotado (preliminar)** |
| Sapatas isoladas | O pilar central recebe ~55 % da água (298 de 542 kN), com risco de recalque diferencial. | Alternativa após sondagem |

---

## 4. Captação e recalque rio → caixa (resumo da MC-01, §3)

**Vazão de projeto: 3,0 m³/h (0,833 L/s).** A vazão mínima seria 1,0 m³/h (8 m³ em 8 h). O fator 3 cobre:
- a água gasta na retrolavagem do filtro;
- o desgaste da bomba;
- o enchimento inicial em prazo razoável.

| Grandeza | Resultado |
|---|---|
| Bombeamento diário para repor 8 m³ | **2,67 h/dia** (≤ 8 h ✓) |
| Enchimento inicial, do vazio a 117,35 / até o extravasor | **15,6 h / 16,7 h** |
| Tubo | PEAD PE 100 DE 40 SDR 11 PN 16 (Di 32,6 mm); v = **1,00 m/s** |
| Perdas no ponto de projeto | distribuída 4,85 m; localizadas 0,62 m (ΣK 12,3); filtro sujo 5 m; hidrômetro 1 m; +10 % nas perdas |
| **Hman** | rio mínimo + filtro sujo: **32,3 m (projeto)**; rio normal: 26,8 m; rio máximo: 24,8 m |
| Submergência / NPSHd | 1,20 m / **10,1 m** |
| Potência hidráulica / eixo | 264 W / ~530 W (η = 0,50 [H]); motor de 0,75 a 1,1 kW |
| Golpe de aríete (parada brusca) | a = 329 m/s; ΔH = 33,4 m; pressão máxima ~76 m, bem abaixo do PN16 (160 m) ✓; **onda negativa de até −6,6 m.c.a. na crista do talude** (risco de separação de coluna) |

**Medidas contra transientes:**
- soft-starter com rampa de parada de 5 s ou mais (ΔH ≈ 4,7 m nas paradas normais);
- retenção de mola junto à bomba;
- SDR 11, resistente ao vácuo (confirmar com o fabricante);
- **análise transiente pelo método das características no executivo**, com o perfil real.

**Ponto de consulta a fornecedores (P-101):**
- Q = 3,0 m³/h a H ≥ 33 m.
- Operação estável até H ≈ 25 m, com vazão maior.
- Motor não sobrecarregável até ~5 m³/h.
- Curvas do sistema a cruzar com a curva real: tabela da MC-01 §3.

**Nenhum modelo comercial é indicado.** Não há curva de fabricante verificada neste estudo.

**Proteção contra resíduos e funcionamento a seco:**
1. Trecho final da camisa perfurado (fendas), com tela inox de ~2 mm [H].
2. Extremidade 0,3 m acima do leito, sobre bloco ou gabião, para não puxar areia.
3. Motor abaixo da zona de entrada, para garantir fluxo de arrefecimento.
4. Filtro autolimpante F-101 de ~130 µm [H] com retrolavagem por ΔP.
5. Proteção a seco por três meios: relé de subcarga (potência/cosφ), eletrodo de nível mínimo na camisa (LSL-100) e bloqueio após 3 tentativas.
6. Inspeção e limpeza da tela com a bomba içada pelo eixo da camisa (zona livre ZN-06).

**Energia na margem:** desnecessária. O cabo submersível 4 × 4 mm² sai do QCB-01, segue em eletroduto enterrado ao lado do recalque (L ≈ 130 m) e não tem emendas abaixo de 103,80.

---

## 5. Reservação: níveis e volumes (MC-01, §2)

| Nível (hipótese, depende do fornecedor) | Cota (m) | Volume acumulado (m³) |
|---|---:|---:|
| Fundo interno | 113,55 | 0 |
| Saída N2 (eixo), 0,25 m acima do fundo para reter sedimentos | 113,80 | 3,1 |
| **LSLL**: booster para (intertravamento físico) | 114,15 | 7,4 |
| LAL: alarme de nível baixo | 114,50 | 11,7 |
| P-101 liga | 116,80 | 40,0 |
| P-101 desliga (nível máximo de operação) | 117,35 | 46,8 |
| LAHH: alarme e parada física de P-101 | 117,50 | 48,6 |
| Soleira do extravasor (50 m³ nominais) | 117,61 | 50,0 |
| Descarga livre da entrada N1 (separação atmosférica) | 117,80 | — |

- **Volume operacional:** 39,4 m³.
- **Volume reservado abaixo do LSLL:** 7,4 m³. Garante submergência (exigida 0,10 m, disponível 0,35 m) e espaço para sedimentos.
- **Histerese de partida:** 6,8 m³, cerca de 1 partida por dia de P-101.

**Incompatibilidade registrada:** os "50.000 L" nominais não são integralmente utilizáveis. O volume operacional é de ~39 m³.

---

## 6. Abastecimento da casa (MC-01, §4)

- Vazão de projeto: 36 L/min = **2,16 m³/h**.
- Linha piezométrica requerida no ponto mais alto: 122,50 + 15 = **137,50 m**.

| Item | Valor |
|---|---|
| Linha TB-202 | PEAD DE 40 SDR 11, 160 m, v = 0,72 m/s, hf = 3,68 m (+0,26 m localizadas) |
| Sucção (DE 63) | v = 0,29 m/s; perdas 0,05 m; NPSHd = **10,7 m** |
| **Hman com caixa no LSLL / caixa cheia** | **30,7 m** / 27,5 m |
| **Setpoint do inversor (pressão na descarga)** | **32,5 m.c.a.**. Mantém ≥ 15 m.c.a. no ponto alto com vazão máxima; com vazão baixa, a pressão sobe a ~22 m.c.a. |
| Pressão estática máxima no térreo da casa | 24,8 m.c.a. (abaixo do limite usual de 40 m.c.a. da NBR 5626 [N], a confirmar no texto vigente) |
| Golpe (parada brusca) | ΔH = 24,1 m; pressão máxima ~65 m (abaixo de PN 16 ✓) |
| Equipamento | **Conjunto pressurizador duplex P-201A/B** (2 × 100 %), bombas centrífugas multiestágio horizontais de ~0,75 kW cada, inversor por bomba, transmissor de pressão, vaso de membrana PV-201 contra ciclagem, alternância e reserva automáticas |

**Ponto de consulta (cada bomba):**
- Q = 2,2 m³/h a H ≥ 31 m.
- NPSHd 10,7 m.
- Operação contínua em baixa vazão: 6 L/min, uma descarga sozinha (a vazão mínima é dado do fabricante).

### 6.1 Funcionamento automático e falhas

| Situação | Comportamento |
|---|---|
| Há consumo | A pressão cai, o inversor acelera a bomba líder e mantém 32,5 m.c.a. Sem consumo, a bomba para por vazão nula. O vaso PV-201 absorve vazamentos pequenos. |
| Nível baixo na caixa | LAL (114,50) dispara alarme. **LSLL (114,15) desliga o booster por boia ligada diretamente ao circuito**, independente do CLP, e o inversor detecta marcha a seco por subcarga. |
| Manutenção | Fechar V-201 na plataforma (isola a caixa) ou V-203 (isola a linha da casa). Uniões e registros por bomba permitem retirar uma bomba com a outra operando. Na casa, o registro VE-01 fica na caixa CE-01. |
| Falta de energia | **Tudo para.** A caixa conserva o volume, mas **a casa fica sem água não potável** até a energia voltar. O sistema rearma sozinho, com partidas escalonadas. |
| Alarmes | Nível baixo, nível muito baixo, nível muito alto, falha das bombas, subcarga (seco), ΔP alto no filtro, falta de fase, tempo máximo de bombeamento excedido (vazamento na linha) e porta/emergência. Indicação no QCB e **remota na casa** (par de sinal na vala da TB-202 ou módulo GSM). |

**Reserva adicional na casa:** não é necessária para vazão e pressão, porque o booster cobre o pico. Para conviver com falta de energia há três caminhos (decisão do proprietário):
- **(a, recomendado)** entrada para gerador portátil de ~5 kVA com chave reversora intertravada;
- (b) aceitar a interrupção (descarga manual com balde);
- (c) pequeno reservatório interno para os vasos, alimentado pelo booster. É **proibido** alimentá-lo pelo sistema potável, salvo com separação atmosférica.

---

## 7. Qualidade da água, tratamento e separação dos sistemas

**A água do rio não é considerada adequada a priori.** Embora os usos sejam não potáveis, descarga, lavagem e irrigação por aspersão geram contato com a pele e aerossóis.

**1. Análises.** Duas campanhas, na estiagem e na chuva, em laboratório acreditado. Parâmetros mínimos sugeridos:
- *E. coli* e coliformes totais;
- turbidez, cor e sólidos suspensos e sedimentáveis;
- pH, condutividade, ferro e manganês (manchas em louças e pisos);
- dureza e alcalinidade (incrustação);
- cloreto e sódio (irrigação);
- odor;
- cianobactérias, se houver represamento a montante;
- agrotóxicos relevantes à bacia, se houver lavouras a montante.

**2. Critérios de qualidade.** A NBR 16783:2019 ("Uso de fontes alternativas de água não potável em edificações", vigente) estabelece os requisitos para este tipo de uso. **Os valores-limite da norma não foram verificados neste estudo** (texto não acessado), e nenhum número é adotado aqui como exigência. A classe do rio pela Res. CONAMA 357/2005 serve de contexto, mas **não autoriza o uso direto**.

**3. Cadeia de tratamento proposta, condicionada às análises:**
- tela na captação;
- filtro autolimpante ~130 µm;
- sedimentação na caixa (saída 0,25 m acima do fundo);
- **desinfecção por cloração** com dosadora proporcional, intertravada com P-101, e residual verificado semanalmente (kit DPD).
Se a turbidez for alta na época de chuvas, acrescentar filtração mais fina, coagulação ou captação por infiltração na margem (alternativa D). A UV só é viável com turbidez baixa e transmitância conhecida.

**4. Uso restrito.**
- Irrigação **apenas de jardim ornamental**: não irrigar hortaliças ou frutas consumidas cruas sem reavaliação.
- Lavagem de pisos sem formação de poças em áreas de crianças e animais.

**5. Separação dos dois sistemas.** São boas práticas, alinhadas à NBR 5626 e à NBR 16783. Os detalhes de identificação devem ser conferidos no texto vigente.
- Tubulações não potáveis com **identificação visual distinta e contínua**: cor lilás, ou faixas e etiquetas a cada 3 m e em todas as derivações, com a inscrição "ÁGUA NÃO POTÁVEL". Fita de aviso enterrada 0,30 m acima do tubo.
- Torneiras de lavagem e irrigação **de uso restrito** (manopla removível ou chave), com placa e pictograma "NÃO BEBA".
- **Nenhuma conexão física** entre os sistemas (nem com válvula). Se houver reposição de emergência a partir do potável, somente por **separação atmosférica** sobre a caixa (descarga livre acima do extravasor).
- Traçados enterrados afastados e sem cruzamento próximo à entrada potável (POT-EX no modelo). Entradas na casa em pontos distintos e identificados.
- Comissionamento com **teste de isolamento**: pressurizar um sistema com o outro despressurizado e verificar ausência de vazão nos pontos, ou fazer ensaio com corante. Registro no *as built*.

---

## 8. Estrutura metálica e fundações (resumo da MC-02)

**Configuração:**
- 9 pilares **W150×29,8**;
- 3 vigas principais **W200×31,3** contínuas;
- 11 vigas secundárias **W150×13,0** a cada 0,44 m;
- deck de **chapa 9,5 mm** (A36) em 5 painéis parafusados com cabeça escareada;
- contraventamento em X com barras Ø16 nas 4 faces;
- plataforma de serviço de 1,10 m a leste, com escada de 42° e guarda-corpo removível no perímetro do deck.

Aço ASTM A572 Gr50, galvanizado a fogo. Massa ~**4,1 t**.

### 8.1 Ações e combinações

- **Água até a borda (extravasor obstruído):** p = 43,2 kPa; W = 542 kN (Ø 4,00).
- **Caixa:** 11,8 kN.
- **Vento** (V0 = 45 m/s, cat. II): q = 1,14 kPa; F = 16,4 kN na caixa e 20,2 kN no total.
- **ELU:** 1,4G + 1,5Q + 1,4W (ψ0 = 1 na água, conservador).
- **Caixa vazia:** 1,0G − 1,4W.
- **ELS:** G + Q.
- **Sismo:** a zona sísmica do local não foi confirmada (a NBR 15421:2023 está vigente) e precisa ser verificada no executivo.

### 8.2 Resultados principais

| Elemento | Solicitante | Resistente / limite | Taxa |
|---|---|---|---:|
| Chapa 9,5 mm (vão 0,44) | Md 1,63 kN·m/m; δ 1,53 mm | 5,13 kN·m/m; L/250 = 1,76 mm | 0,32 / 0,87 |
| Secundária W150×13,0 | Md 18,0 kN·m; Vd 41,9 kN; δ 2,05 mm | 27,7 kN·m; 120 kN; L/350 = 6,3 mm | 0,65 |
| Principal W200×31,3 | Md 95,3 kN·m; Vd 200 kN; δ 2,09 mm | 103,7 kN·m; 253 kN; 6,3 mm | **0,92** |
| Pilar W150×29,8 (K = 1,0; e = 5 cm) | Nd 476 kN | NcRd 1.126 kN; interação N+M | 0,70 |
| Diagonal Ø16 | Nt 7,7 kN | 44,7 kN | 0,17 |
| Placa de base 300×300×22,4 | t mínimo 19,2 mm; σ 5,3 MPa | 22,4 mm; concreto 15,3 MPa | 0,86 / 0,35 |
| Chumbadores 4 × M20 F1554 Gr36 | V 7,1 kN; T 3,0 kN | 149 kN; 69,8 kN por chumbador | < 0,1 |
| **Caixa vazia sem ancoragem** | Mtomb 36,9 kN·m | Mest 23,5 kN·m | **FS 0,64: tomba** |

**Pontos de atenção:**
- **A caixa vazia precisa de ancoragem.** Pré-dimensionamento: 8 pontos com Td ≈ 5 kN e Vd ≈ 3 kN cada, olhais soldados ao vigamento antes da galvanização. A forma de fixação na caixa depende do fabricante.
- Pilares de canto ficam levemente tracionados (−6 kN) com a caixa vazia e vento; os chumbadores atendem.
- A viga principal tem taxa de 0,92, adequada ao estudo. No executivo, recalcular com as edições vigentes, a rigidez real do apoio da caixa e a carga do costado (que pode concentrar no perímetro).
- Os enrijecedores de apoio sobre os pilares são obrigatórios.
- O vão livre sob o deck é de ~1,1–1,3 m: a inspeção é possível, agachado.

**Ligações** (todas parafusadas em campo; soldas só na fábrica, antes da galvanização):
- principal × pilar: chapa de topo 250×250×16 + 4 M16;
- secundária × principal: 4 M16;
- diagonais com esticador e gusset 8 mm;
- chapa de piso: M12 escareados a cada 300 mm;
- pilar × placa: filete de 6 mm, com a compressão transmitida por contato.

**Corrosão:**
- Ambiente rural úmido junto ao rio: categoria **C2–C3** (ISO 9223:2012) adotada como hipótese.
- **Galvanização a fogo** de todas as peças conforme NBR 6323:2025 / ISO 1461:2022 (espessura mínima pela tabela da norma, conforme a espessura do aço).
- Parafusos e chumbadores galvanizados.
- Pintura duplex (ISO 12944) recomendada nos pés de pilar e na interface chapa × caixa.
- Vedação do perímetro da caixa para não acumular água sob o fundo.

### 8.3 Fundação (preliminar, sem sondagem)

**Radier 6,30 × 5,40 × 0,40 m em C30**, sobre lastro e base compactada, com topo em 112,00 e 12 pedestais de 50×50 cm.

| Verificação | Valor |
|---|---|
| Carga de serviço | 959 kN |
| Pressão média / máxima | **28 / 30 kPa** (0,30 do σadm hipotético de 100 kPa) |
| Tombamento e deslizamento com a caixa vazia | FS 14 e 8,9 |
| Punção no pilar central | τSd 0,18 MPa ≤ τRd1 0,41 MPa (NBR 6118, sem armadura de punção) |
| Armadura | **mínima governa**: Ø10 c/12,5 nas duas faces e duas direções (~0,75 t de CA-50 com transpasses) |
| Concreto | ~13,6 m³ de radier + 0,4 m³ de pedestais + 1,7 m³ de lastro |

**Dados geotécnicos necessários antes do executivo:**
- SPT com N por metro e nível d'água;
- classificação dos solos;
- ensaio de colapsibilidade, oedométrico com inundação, se houver solo poroso (frequente no interior de SP);
- avaliação de corte e aterro no platô;
- recalques admissíveis da caixa, informados pelo fabricante.

**As dimensões acima não estão liberadas para construção.**

### 8.4 Área de 8 × 8 m: suficiente?

- **Cabem:** radier (6,30 × 5,40), estrutura, plataforma e escada, com circulação de 0,9 m a oeste e 1,3 m ao sul.
- **Ficam fora:** pé da escada (zona livre até Y = −4,85), abrigo do booster/QCB/cloração (3,0 × 2,5 m), caixa de recepção do extravasor e gaiola da escada marinheiro.

**Recomendação:**
- ampliar a área em **4,5 m a leste**, totalizando 12,5 × 8 m, na direção da casa (DES-04);
- reservar área temporária para caminhão-guindaste (patolamento e raio, a definir em campo);
- garantir acesso de veículo até o abrigo.

---

## 9. Tubulações e componentes por trecho

| Trecho | Especificação | Observações |
|---|---|---|
| Camisa da captação TC-101 | PEAD DE 200, ~14 m, trecho final perfurado com tela inox; tampa na cota 103,80 | Ancorada no talude (blocos/estacas); enrocamento e geotêxtil contra erosão |
| Recalque flexível na camisa | PEAD DE 40 flexível até CX-101, com engate rápido | Sai junto com a bomba |
| CX-101 (crista, acima da cheia) | V-101 esfera, CV-102 retenção de mola, PI-101, união de desmontagem | Fora do eixo de retirada (ZN-06) |
| Recalque TB-101 | PEAD PE100 DE 40 SDR 11 PN 16, eletrofusão; 115 m; enterrado a 0,7 m (≥ 1,0 m sob estrada, com camisa) | Ventosas e drenos nos pontos altos e baixos reais (dependem da topografia); fita de aviso |
| Abrigo | F-101 filtro autolimpante; FQ-101 hidrômetro com pulso; injeção de cloro (CL-101/DP-101); registros de isolamento e bypass do filtro | Retrolavagem vai para o dreno |
| Prumada TB-102 | PEAD DE 40 até N1 no teto, apoiada no patamar | Descarga livre em 117,80 (separação atmosférica; dispensa antissifão) |
| Saída N2 → booster (TB-201) | DE 63; V-201 na plataforma; junta flexível (sem carga no bocal); filtro Y; coletor | Sob a plataforma até o abrigo |
| Linha à casa TB-202 | PEAD DE 40 SDR 11, 160 m, enterrada a 0,7 m, **identificada como não potável**; V-203 na saída; CE-01/VE-01 na casa | Camisa na travessia da estrada; registro de descarga no ponto baixo |
| Dreno N3 (DR-301) | DE 75; V-301 na plataforma + V-302 de estrangulamento (≤ 3 L/s) → CP-301 | |
| Extravasor N4 (EX-401) | DN 100 com tela, descendo pelo suporte SP-401 até CP-301 com descarga visível | Lâmina sobre a soleira: 20 mm para 6 m³/h |
| Descarte DR-302 | DN 100 por gravidade (i ≥ 1 %) → CD-301 (decantação e descloração) → vala VI-301 | ≥ 12 m da fundação; fora de APP (a confirmar) |

**Suportes e proteções:**
- Nenhuma tubulação apoiada na caixa: juntas flexíveis em todos os bocais (cargas admissíveis desconhecidas).
- Prumada e extravasor com suportes próprios.
- Trechos aparentes protegidos de UV (PEAD preto com identificação; PVC aparente pintado).
- Passagens pelo piso grade com recorte e colar.
- Canaleta com tampa entre o radier e o abrigo.

---

## 10. Elétrica e automação (resumo da MC-03)

**Quadro de cargas:**
- P-101: 1,1 kW (≈ 2,8 A);
- P-201A/B: 0,75 kW cada (≈ 1,8 A), uma em operação;
- dosadora + filtro: ~0,1 kW;
- comando: ~0,1 kW;
- aquecimento do painel: 0,1 kW;
- tomada e iluminação: 1 kW.

Demanda máxima de **~4,4 kVA (6,7 A trifásico)**.

**Alimentador:** QE existente → QCB-01 com cabo 4 × 4 mm² + PE (L ≈ 30 m [H]), queda de tensão de 0,4 %, disjuntor de 16 A. **Antes de instalar, verificar no QE:**
- capacidade livre;
- proteção a montante e seletividade;
- corrente de curto-circuito (define a capacidade de interrupção dos disjuntores);
- esquema de aterramento;
- existência de neutro (cargas em 220 V).

**Circuito de P-101:** cabo 4 × 4 mm² submersível, 130 m.

| Condição | Queda de tensão |
|---|---|
| Regime | 0,69 % |
| Partida com soft-starter | 1,3 % |
| Partida direta | 2,3 % |

Atende aos critérios usuais da NBR 5410 (≤ 4 % no circuito terminal e ≤ 10 % na partida), a confirmar. O comprimento máximo de cabo do fabricante do motor prevalece.

**Proteções:**
- disjuntores-motor, soft-starter e inversores;
- relés de falta de fase e de subcarga;
- DR 30 mA nas tomadas e na dosadora. Também recomendado no circuito da bomba submersa, por ela ficar imersa em local acessível a pessoas;
- DR compatível com inversor;
- DPS classe II;
- botão de emergência (NR-12);
- seccionadora com bloqueio e etiquetagem (NR-10).

**Painel ao tempo:** QCB-01 IP65 dentro de abrigo ventilado, com resistência anticondensação e proteção contra sol direto. A cloração fica em **compartimento separado e ventilado**, para que vapores de cloro não corroam o painel.

**Aterramento:**
- eletrodo de fundação no radier, ou anel, interligado à estrutura, às carcaças, ao QCB e às tubulações metálicas;
- análise de risco de descargas atmosféricas pela **NBR 5419-2:2026** para decidir sobre SPDA (estrutura metálica de ~6 m em campo aberto).

**Automação:** CLP ou relé programável. A lista de E/S está na MC-03 §7 e a lógica no DES-05. **Os intertravamentos de segurança são feitos por fiação direta** (LSHH → P-101; LSLL → P-201), independentes do CLP.

**Falta de energia:**
- Captação e booster param.
- A caixa conserva até 4,9 dias de autonomia **da captação**, mas a casa não recebe água sem o booster.
- Recomendada a entrada para gerador.

---

## 11. Limpeza, drenagem e descarte

**Procedimento de limpeza** (frequência inicial anual; ajustar pela inspeção do lodo):
1. Interromper P-101.
2. Consumir a água pela irrigação até o LSLL (aproveita ~39 m³).
3. Fechar V-201.
4. Drenar o restante (~7,4 m³ + lodo) por V-301, com V-302 estrangulada em **≤ 3 L/s** (~41 min). Totalmente aberto, o dreno chegaria a 18 L/s, vazão erosiva.
5. Limpar com equipamento e procedimento de **espaço confinado (NR-33)**.
6. Desinfetar e encher.

**Destino:** CP-301 (caixa de recepção com separação atmosférica) → CD-301 (decantação e **descloração**, por tempo de repouso ou neutralizante) → vala de infiltração/dispersão VI-301 em área gramada a jusante.

**Condições do local de descarte:**
- ≥ 12 m da fundação (por causa da colapsibilidade);
- fora da faixa de APP;
- longe de poços e da casa.

**Verificações ambientais e locais:**
- ensaio de infiltração;
- consulta à CETESB e ao município sobre a disposição de água clorada e lodo no solo;
- se houver lançamento no rio, enquadramento como lançamento (outorga e padrões da Res. CONAMA 430/2011). **Não recomendado.**

O lodo seco vai para destinação adequada após caracterização.

O **extravasor** só opera em falha: alarme LAHH e parada física de P-101 vêm antes. A descarga é visível, para indicar a falha, e segue o mesmo destino.

---

## 12. Normas e referências técnicas

**Verificação:** a vigência foi consultada em 26/11/2026, no catálogo Target (normas.com.br), em iso.org, em store.astm.org e nos portais oficiais. **O texto integral das normas não foi acessado.** Os critérios usados foram aplicados a partir do conhecimento técnico das edições indicadas na coluna "Aplicação". Toda diferença entre a edição aplicada e a vigente fica marcada como pendência para o executivo.

### 12.1 Normas brasileiras

| Norma | Título | Edição vigente (verificada) | Aplicação no estudo |
|---|---|---|---|
| ABNT NBR 5626 | Sistemas prediais de água fria e água quente — Projeto, execução, operação e manutenção | 06/2020 (errata 09/2020) | Pressão estática máxima e mínima na casa, separação atmosférica, limite com a instalação interna |
| ABNT NBR 16783 | Uso de fontes alternativas de água não potável em edificações | 11/2019 | Base para uso não potável, identificação e qualidade. **Valores-limite não verificados** |
| ABNT NBR 15527 | Aproveitamento de água de chuva de coberturas para fins não potáveis — Requisitos | 04/2019 | Referência análoga (não aplicável diretamente: a fonte é rio) |
| ABNT NBR 12213 | Projeto de captação de água de superfície para abastecimento público | 04/1992 (confirmada 2022) | Princípios de captação: proteção contra sólidos, níveis extremos. Referência, pois não se trata de abastecimento público |
| ABNT NBR 12214 | Projeto de estação de bombeamento ou de estação elevatória de água — Requisitos | 07/2020 | Critérios de bombeamento, reserva de bombas, transientes |
| ABNT NBR 12215-1 | Projeto de adutora de água — Parte 1: Conduto forçado | 11/2017 | Recalques: ventosas, descargas, transientes, classe de pressão |
| ABNT NBR 15561 | Tubulação de polietileno PE 80 e PE 100 para transporte de água e esgoto sob pressão — Requisitos | 01/2024 | Especificação de PEAD PE100 SDR 11 PN 16 |
| ABNT NBR 8800 | Projeto de estruturas de aço e de estruturas mistas de aço e concreto de edificações | **10/2024** (errata 02/2025) | Verificações de flexão, cortante, compressão, ligações e flechas. **Expressões aplicadas conforme a edição 2008; revisar pela 2024** |
| ABNT NBR 8681 | Ações e segurança nas estruturas | **09/2025** | Combinações e coeficientes (adotados conforme a Tabela 1 da NBR 8800:2008). **Revisar pela 2025** |
| ABNT NBR 6123 | Forças devidas ao vento em edificações | **12/2023** (consolidada com errata 04/2025) | Vento na caixa e estrutura. **Formulação usada: edição 1988; V0 da região não verificado. Refazer no executivo** |
| ABNT NBR 15421 | Projeto de estruturas resistentes a sismos | 05/2023 | Zona sísmica do local **não verificada** |
| ABNT NBR 6118 | Projeto de estruturas de concreto | 08/2023 (emenda 03/2026) | Radier: punção (τRd1), armadura mínima, cobrimento |
| ABNT NBR 6122 | Projeto e execução de fundações | 09/2019 (emenda 03/2022) | Concepção da fundação; obrigatoriedade de investigação geotécnica |
| ABNT NBR 6484 | Solo — Sondagem de simples reconhecimento com SPT — Método de ensaio | 10/2020 | Programa de sondagem |
| ABNT NBR 8036 | Programação de sondagens de simples reconhecimento dos solos para fundações de edifícios | 06/1983 (confirmada 2023) | Número e locação dos furos |
| ABNT NBR 15980 | Perfis laminados de aço para uso estrutural — Dimensões e tolerâncias | 01/2024 | Dimensões nominais dos perfis W (a conferir) |
| ABNT NBR 14762 | Dimensionamento de estruturas de aço constituídas por perfis formados a frio | 07/2010 | Eventuais perfis dobrados (escadas, guarda-corpos) |
| ABNT NBR 6323 | Galvanização por imersão a quente de produtos de aço-carbono e ferro fundido — Requisitos | **11/2025** (errata 02/2026) | Proteção anticorrosiva |
| ABNT NBR 14718 | Esquadrias — Guarda-corpos para edificação | 08/2019 | Referência para guarda-corpos (complementar à NBR ISO 14122-3) |
| ABNT NBR ISO 14122-1 a -4 | Segurança de máquinas — Meios de acesso permanentes (plataformas, escadas, guarda-corpos, escadas verticais) | 08/2023 | Plataforma, escada 42°, guarda-corpo de 1,10 m, escada marinheiro com gaiola |
| ABNT NBR 5410 | Instalações elétricas de baixa tensão | 09/2004 (errata 2008; revisão em consulta) | Proteções, DR, queda de tensão, aterramento |
| ABNT NBR 5419-1 a -4 | Proteção contra descargas atmosféricas | **03/2026** (errata 04/2026) | Análise de risco e SPDA |
| ABNT NBR IEC 60529 | Graus de proteção providos por invólucros (Códigos IP) | 04/2017 | IP65 do QCB, IP68 de sensores imersos |
| ABNT NBR IEC 61439-1 | Conjuntos de manobra e comando de baixa tensão — Parte 1 | 12/2016 | Montagem e ensaio do QCB |
| ABNT NBR 17094-1 | Motores de indução trifásicos — Requisitos | 04/2018 | Especificação dos motores |

### 12.2 Normas internacionais

| Norma | Edição | Aplicação |
|---|---|---|
| ANSI/HI 9.8 Rotodynamic Pumps for Pump Intake Design | 2024 | Submergência anti-vórtice S = D(1+2,3Fr) na saída N2 (a expressão foi aplicada conforme a edição anterior; conferir) |
| ISO 9906 Rotodynamic pumps — Hydraulic performance acceptance tests | 2012 | Exigir curvas certificadas e ensaio de aceitação |
| ISO 9223 Corrosivity of atmospheres | 2012 | Categoria de corrosividade C2–C3 |
| ISO 1461 Hot dip galvanized coatings | 2022 | Espessura de zinco |
| ISO 12944 (partes 1–9) Corrosion protection by paint systems | 2017–2019 | Sistema duplex opcional |
| ASTM A572/A572M-25 (perfis), A36/A36M-19 (chapas), F1554-20 (chumbadores), F3125/F3125M-26 (parafusos), A123/A123M-24 (galvanização) | indicadas | Especificação de materiais |

### 12.3 Exigências legais, ambientais e de segurança

| Exigência | Fonte | Aplicação e situação |
|---|---|---|
| Outorga de direito de uso ou dispensa | Lei 9.433/1997; Lei SP 7.663/1991; **SP Águas** (LC SP 1.413/2024, sucessora do DAEE; Dec. 69.339/2025) | A **Portaria DAEE 1.631/2017** (art. 3º) considera insignificantes as captações superficiais de até **25 m³/dia**. Elas exigem **cadastro e Declaração de Dispensa de Outorga**, e o Comitê de Bacia pode adotar critérios próprios. O consumo de 8 m³/dia fica abaixo do limite, mas **o enchimento inicial (50 m³) deve ser dividido em ≥ 2 dias**, e o hidrômetro FQ-101 registra o volume. Há nova "Deliberação Geral de Outorgas" da SP Águas em elaboração (consulta pública prorrogada até 24/06/2026): **confirmar a regra vigente antes de protocolar.** |
| Intervenção em APP | Lei 12.651/2012: art. 4º (faixas de 30 m para rio < 10 m; 50 m para 10–50 m), art. 3º X "b" (captação e condução de água são de baixo impacto, comprovada a outorga quando couber) e art. 8º; Res. CONAMA 369/2006 | Captação e trecho do recalque ficam em APP. É necessária **autorização da CETESB**: a Res. SIMA 84/2022 trata de dispensa para outorga agropecuária, de aplicabilidade a verificar. Descarte e abrigo ficam **fora da APP**. |
| Descarte de água de limpeza | Res. CONAMA 430/2011 (se houver lançamento); CETESB e município | Infiltração no solo após descloração, preferencial; consultar o órgão |
| Água não potável | Portaria GM/MS 888/2021 (potabilidade, que **não se aplica** a este sistema) | Reforça a proibição de qualquer uso potável |
| Segurança do trabalho | NR-10 (eletricidade; nova redação, Portaria MTE 737/2026, vigente a partir de 01/06/2027), NR-12 (máquinas), NR-33 (espaço confinado: limpeza da caixa), NR-35 (altura: escada da caixa, ~6 m) | Bloqueio e etiquetagem, emergência, procedimentos e treinamentos |
| Responsabilidade técnica | Lei 6.496/1977; Res. CONFEA 1.137/2023 (alt. 1.160/2025) | ART de projeto (estrutura, fundação, hidráulica, elétrica), de execução e de fabricação da estrutura |

---

## 13. Desenhos, modelo 3D e arquivos

### 13.1 Arquivos produzidos (pasta `claude/`)

| Arquivo | Conteúdo | Como abrir |
|---|---|---|
| `ESTUDO_TECNICO.md` / `estudo_tecnico.html` | Este relatório | Qualquer editor ou navegador |
| `calc/premissas.py` | **Fonte única** de dados, hipóteses e geometria | Python 3.10+ |
| `calc/hidraulica.py`, `estrutura.py`, `eletrica.py`, `run_all.py` | Memórias de cálculo executáveis | `python calc/run_all.py` (requer numpy) |
| `calc/resultados/MC-01_hidraulica.md`, `MC-02_estrutura_fundacao.md`, `MC-03_eletrica.md`, `resultados.json` | Memórias geradas: fórmulas, substituições e resultados | Editor de texto ou Markdown |
| `modelo3d/componentes.py` | Definição paramétrica dos 73 componentes (tag, status, pendência, geometria, contatos permitidos) | Python |
| `modelo3d/gerar_modelo.py` | Exportadores e checagem de interferências | `python modelo3d/gerar_modelo.py` |
| `modelo3d/saida/captacao_caixa_casa.FCMacro` | **Modelo editável FreeCAD**: gera os objetos por disciplina com propriedades Descrição, Status e Pendência, e salva `.FCStd` | FreeCAD 0.21/1.0: Macro → Executar. *Escrito para essa API, mas **não executado** aqui (FreeCAD indisponível); só a sintaxe foi validada* |
| `modelo3d/saida/captacao_caixa_casa.glb` | glTF 2.0 binário, com nós nomeados pela tag e metadados em `extras` | Visualizador 3D do Windows, Blender, gltf-viewer, Navisworks (com plug-in) |
| `modelo3d/saida/captacao_caixa_casa.obj/.mtl` | Malha com grupos `TAG__STATUS` | Blender, SketchUp, FreeCAD, Rhino |
| `modelo3d/saida/visualizador_3d.html` | **Visualizador compartilhável**: camadas, cor por status do dado, clique para identificar, interferências | Navegador. O arquivo carrega o three.js da internet (cdnjs/jsdelivr) |
| `modelo3d/saida/interferencias.md/.json` | Relatório de interferências e zonas livres | Editor |
| `desenhos/svg/DES-01 … DES-07` | Implantação, perfil hidráulico, estrutura e fundação, arranjo da área, P&ID, unifilar, captação | Navegador ou Inkscape (exportável para PDF/DXF) |
| `desenhos/gerar_desenhos.py` | Gerador dos desenhos | `python desenhos/gerar_desenhos.py` |

**Reprodução completa:**

```
python calc/run_all.py
python modelo3d/gerar_modelo.py
python desenhos/gerar_desenhos.py
```

Leva ~1 minuto. A memória estrutural inclui uma verificação do solver de vigas contra a solução analítica (MC-02 §10).

### 13.2 Convenções do modelo

- **FreeCAD:** coordenadas reais em mm, com Z = cota.
- **OBJ, GLB e HTML:** Y para cima, origem no centro da caixa na cota 112,00 (X' = X − 79,60; Y' = Z − 112,00; Z' = −Y).
- **Status de cada componente:** CONF (dado do cliente), HIP (hipótese) ou **PEND** (depende de fornecedor ou campo). No visualizador, o modo "Status do dado" pinta o modelo por essa classificação.
- **Elementos que dependem de dados não confirmados:**
  - caixa e bocais (TQ-101, N1–N4, BV);
  - ancoragens (ANC);
  - patamar e escada do teto (PT-01, EM-01, PST-PT);
  - bombas (P-101, SK-201);
  - filtro e hidrômetro (F-101, FQ-101);
  - cloração (CL-101);
  - radier (RAD-01);
  - descarte (CD-301, VI-301);
  - quadro existente (QE-EX);
  - entrada potável (POT-EX);
  - terreno (TER-01, perfil hipotético).

### 13.3 Interferências

A checagem automática cobre penetração > 3 mm entre sólidos e a ocupação das **zonas livres**:
- ZN-01: circulação da plataforma (0,70 m);
- ZN-02: frente do QCB (1,0 m);
- ZN-03: subida da escada;
- ZN-04: envelope de içamento da caixa;
- ZN-05: remoção das bombas;
- ZN-06: retirada de P-101;
- ZN-08: pé da escada.

A 1ª execução encontrou **8 interferências reais de arranjo**, corrigidas, entre elas:
- o recalque do booster atravessava o compartimento de cloro;
- o suporte do extravasor estava dentro da caixa de recepção;
- a escada estava sobre os pedestais.

Restam **2 ocorrências de sequência de montagem**: o patamar superior e a prumada sobre o teto invadem o envelope de içamento. Devem ser montados depois de posicionar e ancorar a caixa. Os contatos intencionais (apoios, conexões, travessias de piso) estão declarados em `interferencias.md`.

**Limitações da checagem:**
- bocais em posição hipotética;
- terreno não verificado;
- interior da casa não modelado.

---

## 14. Relação preliminar de materiais e equipamentos

| # | Item | Qtd. | Características para consulta | Situação |
|---|---|---:|---|---|
| 1 | Bomba submersa 4" multiestágio (P-101) + motor | 1 + 1 reserva | Água bruta de rio com sólidos (teor a analisar); Q 3,0 m³/h @ H ≥ 33 m; faixa H 25–33 m; motor 3F 380 V 60 Hz, 0,75–1,1 kW, não sobrecarregável; inox; retenção incorporada; instalação inclinada ~34° em camisa DN 200; curva ISO 9906; tolerância a areia; comprimento de cabo ≥ 130 m com 4 mm² | **PEND curva** |
| 2 | Conjunto pressurizador duplex (P-201A/B) | 1 | 2 × centrífuga multiestágio horizontal inox; Q 2,2 m³/h @ H ≥ 31 m cada; NPSHd 10,7 m; inversor por bomba, transmissor 0–10 bar, vaso de membrana 8–24 L [H], alternância; 3F 380 V; vazão mínima informada | **PEND curva** |
| 3 | Filtro autolimpante F-101 | 1 | DN 32–40; Q 3 m³/h; malha ~130 µm [H, conforme análise]; retrolavagem por ΔP (≈0,3 bar) e tempo; PN 10; 220 V | PEND |
| 4 | Hidrômetro FQ-101 com saída pulsada | 1 | DN 25–32, adequado a 3 m³/h, perda ≤ 1 m | PEND |
| 5 | Dosadora de hipoclorito DP-101 + tanque 100 L + injetor | 1 | Proporcional / on-off intertravada; faixa conforme demanda de cloro | PEND análise |
| 6 | Transmissor de nível LT-101 | 1 | Radar ou ultrassom 0–5 m, 4–20 mA, IP67/68; ou hidrostático submersível | HIP |
| 7 | Chaves de nível (boias) LSHH/LSLL + eletrodo LSL-100 | 3 | Contato seco, cabo suspenso, para água bruta | HIP |
| 8 | Caixa d'água 50 m³ | 1 | Conforme fornecedor; pedir os dados da seção 2.3 | **PEND** |
| 9 | Tubo PEAD PE100 SDR 11 PN 16 DE 40 | ~300 m | NBR 15561:2024; preto (UV) com identificação lilás na TB-202 | HIP |
| 10 | Tubo PEAD DE 63 (sucção), DE 75 (dreno), DE 200 perfurado (camisa) | 10 / 6 / 14 m | — | HIP |
| 11 | Tubo DN 100 (extravasor e descarte) | ~40 m | PVC esgoto série reforçada ou PEAD | HIP |
| 12 | Válvulas | — | Esfera PN 16: V-101, V-201 (DN 50), V-203, VE-01 e de isolamento (~10). Retenção de mola: CV-102, CV-201A/B. Gaveta/esfera de estrangulamento V-301/V-302 (DN 65). Ventosas e descargas conforme topografia. Juntas flexíveis nos bocais (3). Filtro Y (1). Manômetros (3) | HIP |
| 13 | Estrutura metálica | ~4,1 t | Ver MC-02 §8: W150×13,0 (11 × 4,4 m); W200×31,3 (3 × 4,4 m); W150×29,8 (9 × ~1,0 m); chapa 9,5 mm (19,4 m²); placas 300×300×22,4 (12); Ø16 com esticador (16); plataforma, grade, guarda-corpos, escada 42°, escada marinheiro com gaiola e patamar; galvanizado a fogo | HIP |
| 14 | Parafusos, chumbadores, olhais | — | M16/M12 A325 galvanizados; 48 chumbadores M20 F1554 Gr36 galvanizados; 8 olhais de ancoragem | HIP / PEND (olhais) |
| 15 | Fundação | — | Concreto C30 ~14 m³; lastro ~1,7 m³; CA-50 ~0,75 t; graute 30 mm | **PEND sondagem** |
| 16 | Abrigo de equipamentos | 3,0 × 2,5 m | Alvenaria ou metálico, ventilado, porta com chave, compartimento de cloro separado com acesso externo, piso com ralo | HIP |
| 17 | QCB-01 | 1 | IP65, NBR IEC 61439; seccionadora com bloqueio; DPS; disjuntores-motor; soft-starter 1,5 kW; 2 inversores 0,75 kW; relés de fase e de subcarga; DR; CLP; fonte 24 Vcc; GSM; sinalização; aquecedor | HIP |
| 18 | Cabos | — | Submersível 4 × 4 mm² (~130 m); alimentador 4 × 4 mm² + PE (~30 m); sinal (~150 m, opcional p/ remoto); eletrodutos PEAD corrugado Ø 50 | HIP |
| 19 | Aterramento | 1 cj. | Eletrodo de fundação ou anel, barra de equipotencialização (BEP), conexões à estrutura | HIP |
| 20 | Entrada para gerador + chave reversora | 1 | ~5 kVA, intertravada | Decisão do proprietário |
| 21 | Caixas CP-301, CD-301, CE-01, CX-101; vala VI-301; enrocamento e geotêxtil da margem | — | — | HIP / PEND |
| 22 | Sinalização "ÁGUA NÃO POTÁVEL", fita de aviso, torneiras de uso restrito | — | — | HIP |

---

## 15. Operação, manutenção e pendências

### 15.1 Como o sistema funciona

1. **Captação.** Quando a caixa desce a 116,80, P-101 liga com partida suave. A água passa pelo filtro, pelo hidrômetro e pela cloração e entra na caixa por cima. Em 117,35, P-101 desliga. Se o rio baixar demais ou a bomba girar a seco, ela para e alarma.
2. **Casa.** Ao abrir um ponto, o booster mantém a pressão. Se a caixa chegar a 114,15, o booster para e alarma.
3. **Falhas.** São sinalizadas no abrigo e na casa.

### 15.2 Plano básico de manutenção

| Frequência | Atividade |
|---|---|
| Diária (automática) | Conferir ausência de alarmes (painel ou celular) |
| Semanal | Medir o cloro residual (DPD); repor hipoclorito; olhar o ΔP do filtro e o totalizador do hidrômetro |
| Mensal | Testar as boias LSHH/LSLL e o alarme remoto; manobrar os registros; inspecionar a CX-101, as caixas CP e CD e a vala; alternar as bombas do booster |
| Trimestral e após cada cheia | Içar P-101 e limpar tela e camisa; inspecionar erosão e enrocamento da margem |
| Anual | Inspeção interna da caixa e limpeza se houver lodo (NR-33); inspeção da galvanização e reaperto de parafusos; medição de aterramento; termografia e reaperto do QCB; aferição dos transmissores; análise da água (no 1º ano, nas duas estações) |

### 15.3 Pendências e decisões do proprietário

1. **Levantamentos:** topografia, batimetria e sondagem (seção 2.2).
2. **Caixa:** obter os dados do fornecedor (seção 2.3), especialmente apoio, ancoragem, bocais e acesso ao teto.
3. **Qualidade da água:** análises nas duas estações; definição do tratamento; aceitação dos usos restritos.
4. **Elétrica:** levantamento do quadro existente; decisão sobre gerador e SPDA.
5. **Autorizações:**
   - cadastro e dispensa de outorga, ou outorga, na SP Águas;
   - autorização de intervenção em APP na CETESB;
   - aprovação do descarte;
   - eventuais exigências municipais.
6. **Área:** aprovar a ampliação para 12,5 × 8 m e a área temporária do guindaste.
7. **Decisões:**
   - booster duplex (recomendado) ou simples com reserva em estoque;
   - remoto cabeado ou GSM;
   - cor e identificação da rede não potável na casa.
8. **Antes de fabricar e instalar:**
   - projeto executivo com ART;
   - recalcular com as edições vigentes (NBR 6123:2023, NBR 8800:2024, NBR 8681:2025, NBR 6118:2023, NBR 5419:2026);
   - curvas reais das bombas;
   - análise transiente;
   - desenhos de fabricação;
   - plano de içamento;
   - comissionamento com teste de isolamento entre os sistemas.

---

## 16. Conclusão para o proprietário

| # | A solução consegue… | Resposta | Evidência principal | Condições a confirmar |
|---|---|---|---|---|
| 1 | Captar água do rio nas condições informadas? | **Sim, preliminarmente** | Bomba sempre afogada entre 97,50 e 102,00; NPSHd 10,1 m; Hman 32,3 m no pior caso (MC-01 §3) | Leito ≤ 95,70 m (batimetria); talude estável; curva real da bomba; outorga ou dispensa; autorização em APP |
| 2 | Encher e manter a caixa de 50 m³? | **Sim** | 2,7 h/dia de bombeamento (limite 8 h); enchimento inicial de 16,7 h; autonomia de 4,9 dias (MC-01 §2–3) | Volume operacional real (~39 m³) depende do desenho da caixa; enchimento inicial em ≥ 2 dias para não passar de 25 m³/dia |
| 3 | Sustentar a caixa? | **Sim, no pré-dimensionamento** | Taxa máxima de 0,92 (viga principal); flechas ≤ 2,1 mm; radier a 30 kPa; punção OK (MC-02) | **Ancoragem da caixa vazia é obrigatória**; forma de apoio do fabricante; sondagem e colapsibilidade; recálculo com as edições vigentes das normas |
| 4 | Fornecer água à casa com a vazão e pressão pedidas? | **Sim, com o booster e com energia** | 2,16 m³/h com ≥ 15 m.c.a. no ponto 122,50; setpoint 32,5 m.c.a.; estática ≤ 24,8 m.c.a. (MC-01 §4) | Curvas reais; traçado e topografia; projeto interno da casa. **Sem energia não há fornecimento** (gerador opcional) |
| 5 | Operar e permitir manutenção com segurança? | **Sim** | Intertravamentos físicos, alarmes local e remoto, plataforma, escadas e zonas livres verificadas no modelo (2 ocorrências de montagem tratadas) | Procedimentos NR-10, NR-33 e NR-35; acesso ao teto conforme fabricante; treinamento |
| 6 | Ser construída nas áreas disponíveis? | **Parcialmente** | A estrutura cabe nos 8 × 8 m; o conjunto completo pede 12,5 × 8 m (DES-04) | Aprovação da ampliação; área do guindaste; terraplenagem do platô |
| 7 | Atender às normas e exigências identificadas? | **Os critérios foram aplicados; a conformidade formal fica para o executivo** | Seção 12, com edições verificadas | Edições novas da NBR 6123, 8800, 8681, 6323 e 5419; valores da NBR 16783 não verificados; licenças pendentes; ART |

### 16.1 Limitações do estudo

- Caso fictício, sem visita, topografia, sondagem, batimetria nem análise de água.
- Dados da caixa sem certificação.
- Normas com vigência verificada, mas sem consulta ao texto integral.
- O vento usou a formulação de 1988.
- Rendimentos, perdas de equipamentos e posições de bocais são hipóteses.
- O modelo 3D é esquemático, com perfis sem raios e válvulas simplificadas.
- A macro FreeCAD não foi executada neste ambiente.
- Os resultados são preliminares e servem para decidir a concepção e orientar o executivo.

### 16.2 Etapas antes do executivo e da obra

1. Levantamentos de campo e análise da água.
2. Dados certificados da caixa e propostas de bombas, filtro e dosadora.
3. Regularização: outorga ou dispensa, APP e descarte.
4. Projeto executivo multidisciplinar com ART:
   - recálculo pelas normas vigentes;
   - análise transiente;
   - fundações com base na sondagem;
   - desenhos de fabricação;
   - projeto elétrico completo;
   - projeto interno da casa.
5. Plano de içamento e de montagem (sequência: estrutura → caixa → ancoragem → patamar e prumada).
6. Fabricação com inspeção (galvanização, soldas).
7. Obra com acompanhamento técnico.
8. Comissionamento:
   - teste de estanqueidade;
   - teste de isolamento entre os sistemas;
   - ajuste dos níveis e do setpoint;
   - teste dos alarmes e intertravamentos;
   - entrega do manual de operação e do *as built*.
