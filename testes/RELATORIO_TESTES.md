# Relatório de testes de comprovação

Executado em 2026-11-26 10:00 com Python 3.12.10 / numpy 2.5.4.
Resultado: **16/16 aprovados**.

| Código | Teste | Referência | Obtido | Tolerância | Resultado | Fonte da referência |
|---|---|---|---|---|---|---|
| T01 | Viga contínua 2 vãos (FE 1D) — reação central e momento no apoio | R = 1,25qL = 27,50 kN; M = qL²/8 = 6,050 kN·m | R = 27.500; M = 6.050 | < 0,5 % | ✅ PASSOU | Timoshenko & Young, teoria das estruturas |
| T02 | Pórtico espacial — balanço com cargas em 3 direções | δ = PL³/3EI (eixo forte vertical, fraco lateral); δ = NL/EA | uz -1.667e-02 (ref -1.667e-02); uy 3.333e-02 (ref 3.333e-02); ux 2.500e-04 (ref 2.500e-04) | < 0,1 % | ✅ PASSOU | Resistência dos materiais |
| T03 | Pórtico do projeto — equilíbrio global (6 combinações) | Σ reações = Σ cargas | erro máx 4.23e-09 kN | < 1e-6 kN | ✅ PASSOU | Equilíbrio estático |
| T04 | Pórtico 3D × modelo 1D (MC-02) — carga de água e pilar central | ΣQ = W_água = 542.4 kN; pilar central 1D = 298.3 kN | ΣQ = 542.3 kN; pilar central 3D = 258.0 kN (dif. 14 %) | ΣQ < 1 %; pilar < 20 % | ✅ PASSOU | Consistência entre modelos (o 1D supõe apoios rígidos → conservador) |
| T05 | Placa de Mindlin Q4 — placa quadrada simplesmente apoiada, carga uniforme | w = 0,00406 qa⁴/D; Mx = 0,0479 qa² | w = 2.6082 mm (ref 2.5855); Mx = 0.4777 (ref 0.4790) | < 2 % | ✅ PASSOU | Timoshenko & Woinowsky-Krieger, Theory of Plates, tab. 8 |
| T06 | Placa de Mindlin Q4 — placa quadrada engastada, carga uniforme | w = 0,00126 qa⁴/D | w = 0.8049 mm (ref 0.8024) | < 5 % | ✅ PASSOU | Timoshenko & Woinowsky-Krieger, tab. 35 |
| T07 | Placa sobre base de Winkler — carga uniforme em placa livre | w = q/k = 1,250 mm (uniforme), M ≈ 0 | w = 1.2500–1.2500 mm; |M|max = 1.49e-11 | < 0,1 % | ✅ PASSOU | Solução exata (corpo rígido sobre molas) |
| T08 | MOC — parada instantânea, tubo horizontal sem atrito | ΔH = a·v/g = 33.43 m | ΔH = 33.43 m | < 2 % | ✅ PASSOU | Joukowsky; Wylie & Streeter, Fluid Transients |
| T09 | MOC — regime permanente preservado (sem perturbação) | variação de pressão nula | variação 3.32e-08 m | < 1e-3 m | ✅ PASSOU | Consistência numérica (Courant = 1) |
| T10 | Fator de atrito — Swamee-Jain × Colebrook-White (iterativa) | f Colebrook = 0.02684 | f Swamee-Jain = 0.02708 | < 1,5 % | ✅ PASSOU | Colebrook (1939); Swamee & Jain (1976) |
| T11 | Funções NBR 8800 — limites teóricos (Lb→0, L→0) | MRd = Zx·fy/γa1; NcRd = A·fy/γa1 | MRd 75.83 (ref 75.83); NcRd 1178.9 (ref 1179.0) | < 0,5 % | ✅ PASSOU | ABNT NBR 8800 (formulação 2008) |
| T12 | Modelo glTF 2.0 (.glb) — integridade binária | magic glTF, versão 2, tamanhos e acessores dentro do buffer | versão 2; 73 nós; 146 acessores | estrutural | ✅ PASSOU | Especificação Khronos glTF 2.0 |
| T13 | Desenhos SVG — XML bem formado | 7 folhas válidas | 7/7 válidas | 100 % | ✅ PASSOU | W3C SVG/XML |
| T14 | Modelo 3D — interferências remanescentes tratadas | somente ocorrências de sequência de montagem com tratamento | 2 ocorrências: TB-102×ZN-04; PT-01×ZN-04 | 0 'A RESOLVER' | ✅ PASSOU | Checagem geométrica automática (gerar_modelo.py) |
| T15 | Reprodutibilidade das memórias de cálculo | hash idêntico em execuções sucessivas | 9b336e8abbcc = 9b336e8abbcc | idêntico | ✅ PASSOU | Determinismo do pipeline |
| T16 | Hman de P-101 recalculada de forma independente | MC-01: 32.325 m | 32.325 m | < 0,1 % | ✅ PASSOU | Balanço de energia (Bernoulli + perdas) |

Os testes verificam a **implementação** (software) e a **consistência** dos resultados. Não substituem a revisão independente por engenheiro habilitado, nem a validação com dados reais de campo e de fornecedores.
