# -*- coding: utf-8 -*-
"""Utilitário para gerar memórias de cálculo rastreáveis em Markdown."""


def f(x, n=3):
    """Formata número no padrão brasileiro (vírgula decimal)."""
    if isinstance(x, str):
        return x
    s = f"{x:,.{n}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


class Memo:
    def __init__(self, titulo):
        self.linhas = [f"# {titulo}", ""]
        self.res = {}

    def h(self, txt, nivel=2):
        self.linhas += [f"{'#' * nivel} {txt}", ""]

    def p(self, txt):
        self.linhas += ["", txt, ""]

    def calc(self, nome, formula, subst, valor, un, n=3, chave=None, ok=None):
        """Registra um cálculo: nome, fórmula, substituição numérica, resultado."""
        status = "" if ok is None else ("  **OK**" if ok else "  **NÃO ATENDE**")
        partes = [f"`{formula}`" if formula else "", f"`{subst}`" if subst else ""]
        expr = " = ".join(x for x in partes if x)
        expr = (expr + " = ") if expr else ""
        self.linhas.append(f"- {nome}: {expr}**{f(valor, n)} {un}**{status}")
        if chave:
            self.res[chave] = valor
        return valor

    def item(self, txt):
        self.linhas.append(f"- {txt}")

    def tabela(self, cab, linhas):
        self.linhas.append("")
        self.linhas.append("| " + " | ".join(cab) + " |")
        self.linhas.append("|" + "|".join(["---"] * len(cab)) + "|")
        for l in linhas:
            self.linhas.append("| " + " | ".join(f(c) if not isinstance(c, str) else c for c in l) + " |")
        self.linhas.append("")

    def fim(self):
        self.linhas.append("")

    def texto(self):
        return "\n".join(self.linhas) + "\n"
