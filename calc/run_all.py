# -*- coding: utf-8 -*-
"""Executa todas as memórias de cálculo e grava resultados.

Uso:  python calc/run_all.py
Saídas: calc/resultados/MC-01_hidraulica.md, MC-02_estrutura_fundacao.md, MC-03_eletrica.md,
        calc/resultados/resultados.json (consumido pelo modelo 3D e pelos desenhos)
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import hidraulica, estrutura, eletrica  # noqa: E402

OUT = os.path.join(AQUI, "resultados")
os.makedirs(OUT, exist_ok=True)


def conv(o):
    try:
        import numpy as np
        if isinstance(o, np.generic):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
    except Exception:
        pass
    return str(o)


def main():
    todos = {}
    for nome, mod in [("MC-01_hidraulica", hidraulica), ("MC-02_estrutura_fundacao", estrutura), ("MC-03_eletrica", eletrica)]:
        m = mod.run()
        with open(os.path.join(OUT, nome + ".md"), "w", encoding="utf-8") as fh:
            fh.write(m.texto())
        todos[nome] = m.res
        print(f"[ok] {nome}: {len(m.res)} resultados")
    with open(os.path.join(OUT, "resultados.json"), "w", encoding="utf-8") as fh:
        json.dump(todos, fh, ensure_ascii=False, indent=1, default=conv)
    print("[ok] resultados.json")


if __name__ == "__main__":
    main()
