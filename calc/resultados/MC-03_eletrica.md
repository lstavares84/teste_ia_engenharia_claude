# Memória de Cálculo — Alimentação Elétrica e Automação (preliminar)


Rendimentos e fatores de potência são **hipóteses** (sem dados de placa); correntes devem ser recalculadas com os dados dos equipamentos efetivamente comprados. Resistência do cobre a 70 °C: ρ = 0,017241·(1+0,00393·50) Ω·mm²/m; reatância 0,08 Ω/km. Queda de tensão trifásica: ΔV% = √3·I·L·(R·cosφ + X·senφ)/V·100.

## 1. Quadro de cargas


| Tag | Carga | P (kW) | η [H] | cosφ [H] | Fases | S (kVA) | I (A) | Regime |
|---|---|---|---|---|---|---|---|---|
| P-101 | Bomba submersa de captação (motor 4", partida suave) | 1,10 | 0,75 | 0,80 | 3F | 1,83 | 2,79 | intermitente ~3 h/dia |
| P-201A | Booster A (inversor de frequência) | 0,75 | 0,78 | 0,80 | 3F | 1,20 | 1,83 | intermitente (demanda) |
| P-201B | Booster B — reserva (não opera simultâneo) | 0,75 | 0,78 | 0,80 | 3F | 1,20 | 1,83 | reserva |
| DP-101 | Bomba dosadora de cloro | 0,05 | 1,00 | 0,90 | 1F | 0,06 | 0,25 | com P-101 |
| F-101 | Controlador do filtro autolimpante + solenoides | 0,03 | 1,00 | 0,90 | 1F | 0,03 | 0,15 | contínuo |
| QCB-AUX | CLP/relé programável, fonte 24 Vcc, instrumentos, comunicador GSM | 0,10 | 1,00 | 0,90 | 1F | 0,11 | 0,51 | contínuo |
| QCB-AQ | Resistência anticondensação + ventilação do painel | 0,10 | 1,00 | 1,00 | 1F | 0,10 | 0,45 | termostato |
| ILU/TUG | Iluminação e tomada de serviço do abrigo | 1,00 | 1,00 | 0,92 | 1F | 1,09 | 4,94 | eventual |

- Potência aparente máxima simultânea (sem reserva): `ΣS` = **4,42 kVA**
- Corrente equivalente trifásica (equilibrada): `I = S/(√3·V)` = **6,72 A**

Cargas monofásicas (220 V fase-neutro **— confirmar se a rede é 380/220 V com neutro**) distribuídas entre fases.

## 2. Alimentador do QCB (quadro existente → QCB na área da caixa)


Distância entre o quadro existente e o QCB desconhecida — adotado L = 30 m [H].

- Queda de tensão 4×4 mm² + PE, I = 6,7 A: `ΔV%` = **0,38 %**
- Queda de tensão 4×6 mm² + PE, I = 6,7 A: `ΔV%` = **0,26 %**

Adotado: cabo 0,6/1 kV 4 × 4 mm² + PE 4 mm² em eletroduto enterrado; disjuntor tripolar 16 A curva C no quadro de origem (seletividade com a proteção geral existente a verificar) + DPS classe II no QCB. A seção é governada por resistência mecânica, curto-circuito e margem — não pela corrente (< 10 A).

## 3. Circuito da bomba submersa P-101 (QCB → rio)


Percurso: QCB → vala junto ao recalque (≈ 84 m) → caixa de passagem na crista → tubo-camisa (≈ 14 m) → bomba; com folgas: **L = 130 m** [H]. Cabo contínuo, próprio para imersão (sem emendas abaixo da cota 103,8).


| Cabo | ΔV regime (%) | ΔV partida direta 6,5·In, cosφ 0,4 (%) | ΔV soft-starter 3·In, cosφ 0,5 (%) |
|---|---|---|---|
| 4×2,5 mm² | 1,10 | 3,62 | 2,08 |
| 4×4,0 mm² | 0,69 | 2,29 | 1,31 |
| 4×6,0 mm² | 0,46 | 1,55 | 0,89 |


Critérios adotados: ≤ 4 % em regime no circuito terminal (somado à queda a montante, total ≤ 7 % — limites usuais da NBR 5410, confirmar edição vigente) e ≤ 10 % na partida. **Adotado cabo 4 × 4 mm² (3F + PE)** próprio para bomba submersa: folga para motor até 1,5 kW e para o comprimento máximo de cabo indicado pelo fabricante do motor (dado do fornecedor que prevalece sobre este cálculo).

## 4. Proteções e comandos

- P-101: disjuntor-motor ajustado a ~1,05·In (In ≈ 2,8 A — ajustar ao dado de placa), soft-starter com rampa de aceleração e desaceleração (mitigação do golpe de aríete), relé de falta/sequência de fase e sub/sobretensão, relé de subcarga (potência/cosφ) para proteção contra funcionamento a seco, eletrodos/boia de nível mínimo no tubo-camisa (redundância), DR 30 mA (recomendação: circuito alimenta equipamento imerso em água acessível a pessoas).
- P-201A/B: disjuntor-motor + inversor de frequência dedicado por bomba (ou conjunto pressurizador com controle integrado), transmissor de pressão 4–20 mA na descarga, proteção contra marcha a seco por subcarga do inversor e por chave de nível LSLL hard-wired. DR compatível com inversor (tipo B ou conforme fabricante do inversor).
- Circuitos de tomada/iluminação: disjuntor 16 A + DR 30 mA.
- DPS classe II em cada fase e neutro no QCB; DPS para a linha de sinal/remoto, se cabeada.
- Botão de emergência (NR-12) no QCB e seccionadora geral com bloqueio por cadeado (NR-10 — bloqueio e etiquetagem).
## 5. Aterramento e equipotencialização

- Eletrodo de aterramento em anel ou incorporado à armadura do radier (eletrodo de fundação), interligado à estrutura metálica, ao QCB, às carcaças dos motores, à tubulação metálica e ao SPDA, se requerido.
- Esquema de aterramento existente (TN-S, TN-C-S ou TT) **desconhecido** — define a coordenação das proteções. Se TT: com DR 30 mA, RA ≤ 50 V / 0,03 A = 1 667 Ω (condição normativa); recomenda-se como boa prática ≤ 10 Ω para facilitar integração com o SPDA.
- Análise de risco de descargas atmosféricas (NBR 5419-2) para a estrutura metálica de ~6 m em área aberta — decidir sobre SPDA; a própria estrutura metálica aterrada pode servir de captor/descida natural.
## 6. Geração de emergência (opcional recomendado)

- Carga para manter booster + captação + auxiliares: `S = S_P101 + S_P201 + aux` = **3,34 kVA**

Recomendado: entrada para gerador portátil trifásico de ~5 kVA (folga para partida com soft-starter/inversor) com chave reversora manual intertravada no QCB (impede retorno de energia para a rede). Decisão do proprietário.

## 7. Lista de E/S do controlador (preliminar)


| Tipo | Tag | Descrição |
|---|---|---|
| AI | LT-101 | Nível contínuo da caixa (radar/ultrassom no teto ou hidrostático) 4–20 mA |
| AI | PT-201 | Pressão de descarga do booster (também ligado ao inversor) |
| DI | LSHH-101 | Boia de nível muito alto — intertravamento físico de P-101 + alarme |
| DI | LSLL-101 | Boia de nível muito baixo — intertravamento físico de P-201 + alarme |
| DI | LSL-100 | Nível mínimo no tubo-camisa (eletrodo) — bloqueio de P-101 |
| DI | P-101 RUN/FALHA/SUBCARGA | Retornos do soft-starter e relés |
| DI | P-201A/B RUN/FALHA | Retornos dos inversores |
| DI | PDSH-101 | Pressão diferencial alta no filtro (falha de autolimpeza) |
| DI | FALTA FASE | Relé de supervisão de rede |
| DI | PORTA/EMERG. | Porta do abrigo / botão de emergência |
| DI | FQ-101 (pulso) | Totalizador do hidrômetro de captação — registro de volume (outorga) |
| DO | P-101 LIGA | Comando do soft-starter |
| DO | P-201 HAB. | Habilitação do booster (alternância A/B) |
| DO | DP-101 HAB. | Dosadora habilitada apenas com P-101 em operação |
| DO | ALM-LOCAL/REMOTO | Sinalizador no abrigo + relé para alarme na casa (cabo ou GSM) |

