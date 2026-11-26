# Relatório de interferências e zonas livres

Gerado automaticamente por `modelo3d/gerar_modelo.py` a partir da geometria de `componentes.py`.
Critério: penetração > 3 mm entre sólidos (caixas por AABB exata; cilindros por amostragem volumétrica a cada 4 cm), excluídos os contatos intencionais declarados em `permite` de cada componente (ex.: viga apoiada em pilar, tubo conectado a bocal, tubo atravessando piso grade). Zonas livres (ZN-xx) representam espaços de operação, circulação, subida, içamento e retirada de equipamentos e não podem ser ocupadas.

Componentes verificados: 73. Ocorrências: 2.

Histórico: a 1ª execução encontrou 8 ocorrências, corrigidas no arranjo — (1) recalque do booster atravessava o compartimento de cloração → passou sob o piso; (2) suporte do extravasor dentro da caixa de recepção CP-301 → deslocado com bloco próprio; (3) escada marinheiro sobre os pedestais do patamar e (4) espaço de subida obstruído → escada afastada para X = 83,40 e largura 0,40 m; (5–6) guarda-corpo/escada e faixa de circulação → ajuste de limites; (7) contato mangueira × recalque na caixa de válvulas → conexão declarada; (8) pé da escada → ajuste da zona. As ocorrências remanescentes abaixo são de sequência de montagem e estão tratadas.

| # | Componente A | Componente B | Tipo | Ponto (X; Y; Z) real | Tratamento |
|---|---|---|---|---|---|
| 1 | TB-102 | ZN-04 | zona livre obstruída | 80.80; 1.40; 118.27 | Sequência de montagem: trecho horizontal da entrada sobre o teto — instalar após o içamento. |
| 2 | PT-01 | ZN-04 | zona livre obstruída | 81.58; 0.55; 118.64 | Sequência de montagem: patamar superior entra no envelope de içamento — montar o patamar e a prumada N1 após posicionar e ancorar a caixa (ou torná-los desmontáveis). |

## Contatos intencionais declarados (não reportados)

- **TC-101** ↔ TER-01, RIO-MIN, RIO-NOR, RIO-MAX, P-101, BL-101, ZN-06
- **P-101** ↔ TC-101, RIO-MIN, RIO-NOR, RIO-MAX, TER-01
- **BL-101** ↔ TER-01, RIO-MIN, RIO-NOR, RIO-MAX, TC-101
- **CX-101** ↔ TER-01, TB-101, EL-101
- **TB-101-M** ↔ TC-101, CX-101, ZN-06, TER-01, TB-101
- **ZN-06** ↔ TER-01, TC-101, TB-101-M
- **TB-101** ↔ CX-101, TER-01, ABR-PISO, F-101
- **F-101** ↔ TB-101, TB-102, ABR-PISO
- **TB-102** ↔ F-101, FQ-101, ABR-N, PL-01, TQ-101, N1, TER-01
- **FQ-101** ↔ TB-102
- **RAD-01** ↔ TER-01, PED, TB-101
- **PED** ↔ RAD-01, PB, PIL, PST
- **PB** ↔ PED, PIL, PST
- **PIL** ↔ PB, VP, CTV, PED
- **VP** ↔ PIL, VS, CTV, VPL
- **VS** ↔ VP, CH-01, ANC, VPL, GC-DECK
- **CH-01** ↔ VS, TQ-101, ANC, GC-DECK, PST-PT
- **CTV** ↔ PIL, VP
- **ANC** ↔ CH-01, TQ-101, VS, ZN-04
- **VPL** ↔ PST, PL-01, PIL, VP, VS
- **PST** ↔ PB, VPL, PED
- **PL-01** ↔ VPL, TB-102, TB-201, DR-301, PST-PT, GC-PL, ES-01
- **GC-PL** ↔ PL-01, VPL, ES-01
- **GC-DECK** ↔ CH-01, VS, ZN-04
- **ES-01** ↔ PL-01, VPL, TER-01, RAD-01
- **PST-PT** ↔ PED, PL-01, PT-01, CH-01, VS
- **PT-01** ↔ PST-PT, EM-01
- **EM-01** ↔ PT-01, TER-01, RAD-01, PST-PT
- **ZN-03** ↔ EM-01, TER-01
- **ZN-01** ↔ PL-01
- **TQ-101** ↔ CH-01, ANC, N1, N2, N3, N4, BV, LT-101, TB-102, TB-201, DR-301, EX-401
- **ZN-04** ↔ TQ-101, BV, LT-101, N1, ANC, GC-DECK
- **N1** ↔ TQ-101, TB-102, ZN-04
- **N2** ↔ TQ-101, TB-201
- **N3** ↔ TQ-101, DR-301
- **N4** ↔ TQ-101, EX-401
- **BV** ↔ TQ-101, ZN-04
- **LT-101** ↔ TQ-101, ZN-04
- **TB-201** ↔ N2, TQ-101, PL-01, CH-01, ABR-O, SK-201, VPL
- **DR-301** ↔ N3, TQ-101, PL-01, CH-01, CP-301
- **EX-401** ↔ N4, TQ-101, SP-401
- **SP-401** ↔ EX-401, RAD-01, TER-01
- **CP-301** ↔ DR-301, TER-01, RAD-01, DR-302
- **DR-302** ↔ CP-301, TER-01, CD-301
- **CD-301** ↔ DR-302, TER-01, VI-301
- **VI-301** ↔ TER-01, CD-301
- **ABR-PISO** ↔ TER-01, TB-101, F-101, SK-201, ABR-O, ABR-N, ABR-L, ABR-S, CL-101
- **ABR-O** ↔ ABR-PISO, TB-201, ABR-N, ABR-S, ABR-T
- **ABR-N** ↔ ABR-PISO, TB-102, QCB-01, ABR-O, ABR-L, ABR-T, EL-102
- **ABR-L** ↔ ABR-PISO, TB-202, ABR-N, ABR-S, ABR-T, EL-102
- **ABR-S** ↔ ABR-PISO, ABR-O, ABR-L, ABR-T, EL-101, CL-101
- **ABR-T** ↔ ABR-O, ABR-N, ABR-L, ABR-S
- **SK-201** ↔ ABR-PISO, TB-201, TB-202
- **ZN-05** ↔ ABR-PISO
- **CL-101** ↔ ABR-PISO, ABR-S, ABR-L
- **QCB-01** ↔ ABR-N, EL-102
- **ZN-02** ↔ ABR-PISO
- **TB-202** ↔ SK-201, ABR-L, ABR-PISO, TER-01, CE-01
- **EL-101** ↔ ABR-PISO, ABR-S, TER-01, CX-101
- **QE-EX** ↔ TER-01, EL-102
- **EL-102** ↔ QE-EX, TER-01, ABR-N, ABR-PISO, QCB-01
- **ATR-01** ↔ TER-01, RAD-01
- **CE-01** ↔ TB-202, TER-01
- **CASA** ↔ TER-01, PA-01
- **PA-01** ↔ CASA
- **POT-EX** ↔ TER-01

## Limitações

- Geometria simplificada (perfis sem raios, conexões e válvulas como trechos retos; bocais com posição hipotética).
- Bocais, teto, boca de visita e acessórios da caixa dependem do desenho certificado do fornecedor — refazer a checagem com ele.
- Terreno é um perfil hipotético extrudado em Y; interferências com o terreno não são verificadas (dependem de topografia).
- Itens dentro da casa não modelados (projeto interno de terceiros).
