# Estudo: captação de rio, caixa de 50 m³ e abastecimento não potável (exercício)

Este é um estudo preliminar de engenharia sobre um caso fictício. **Não vale para fabricação nem para construção.**

## Por onde começar

1. `ESTUDO_TECNICO.md` (ou `estudo_tecnico.html` no navegador): é o relatório completo, das seções 0 a 16, e responde a todos os itens pedidos.
2. `modelo3d/saida/visualizador_3d.html`: modelo 3D interativo. Abra no navegador com internet, porque ele carrega o three.js de um CDN.
3. `desenhos/svg/DES-01 … DES-07`: as folhas de desenho.
4. `calc/resultados/MC-01 … MC-03`: as memórias de cálculo, com fórmulas, valores e resultados.

## Estrutura de pastas

```
claude/
  ESTUDO_TECNICO.md            relatório (fonte)
  estudo_tecnico.html          relatório em HTML com desenhos embutidos
  gerar_relatorio_html.py      md -> html
  calc/
    premissas.py               FONTE ÚNICA de dados [C]/[H]/[F]/[N]
    hidraulica.py, estrutura.py, eletrica.py, memo.py, run_all.py
    resultados/MC-01_hidraulica.md, MC-02_estrutura_fundacao.md, MC-03_eletrica.md, resultados.json
  modelo3d/
    componentes.py             73 componentes paramétricos (tag, status, pendência, geometria)
    gerar_modelo.py            exportadores + checagem de interferências
    visualizador_template.html
    saida/  captacao_caixa_casa.FCMacro (FreeCAD, editável) | .glb | .obj/.mtl |
            visualizador_3d.html | interferencias.md/.json | componentes.json
  desenhos/
    gerar_desenhos.py
    svg/DES-01..DES-07
  artifact/                    versão do relatório preparada para publicação
```

## Como reproduzir

Requisitos: Python 3.10 ou mais recente e numpy. Rode a partir da pasta `claude/`:

```
python calc/run_all.py
python modelo3d/gerar_modelo.py
python desenhos/gerar_desenhos.py
python gerar_relatorio_html.py
```

Para mudar uma hipótese (cota do leito, comprimento de tubo, vento, níveis etc.), edite `calc/premissas.py` e rode os quatro comandos de novo. Cálculos, modelo, desenhos e relatório HTML são todos regenerados. Os números citados no texto de `ESTUDO_TECNICO.md`, porém, precisam ser revisados à mão.

## Modelo editável no FreeCAD

No FreeCAD 0.21 ou 1.0, use Macro → Macros… e execute `modelo3d/saida/captacao_caixa_casa.FCMacro`. A macro cria grupos por disciplina e um objeto por componente, cada um com as propriedades Descrição, Status e Pendência, e salva `captacao_caixa_casa.FCStd`.

A macro **não foi executada** no ambiente onde foi gerada, porque o FreeCAD não estava instalado; só a sintaxe foi validada. Se der algum erro, o `.glb` e o `.obj` importam diretamente no FreeCAD e no Blender.

## Convenções

- **Origem dos dados:** [C] cliente, [H] hipótese, [F] fornecedor, [L] levantamento, [N] norma.
- **Status no modelo:** CONF, HIP, PEND.
- **Coordenadas reais:** X ao longo do traçado (X = 0 na borda d'água do nível mínimo), Y para o norte, Z = cota.
- **Arquivos OBJ, GLB e HTML:** Y para cima, origem no centro da caixa na cota 112,00.
