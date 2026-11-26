# -*- coding: utf-8 -*-
"""Executa todas as simulações numéricas e grava fea/resultados/FEA.md + figuras PNG + JSON.

Uso: python fea/run_fea.py   (requer numpy e Pillow)
"""
import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "calc"))
import portico3d
import placas
import transiente_moc
from premissas import *  # noqa

OUT = os.path.join(AQUI, "resultados")


def f2(x, n=2):
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    os.makedirs(OUT, exist_ok=True)
    r1, P, meta = portico3d.run(OUT)
    els = r1["reacoes_por_combo"]["ELS G+Q+L"]
    elu = r1["reacoes_por_combo"]["ELU-1 1,4G+1,5Q+1,4Wx+1,05L"]
    r23 = placas.run(OUT, els, elu)
    r4 = transiente_moc.run(OUT)
    # frequência de sloshing (modo convectivo, cilindro rígido)
    R = CAIXA_FORN["D_ext"] / 2 - 0.02
    h = NIVEIS["P1_desliga"] - TANQUE["cota_fundo_int"]
    fslosh = math.sqrt(1.841 * G / R * math.tanh(1.841 * h / R)) / (2 * math.pi)
    tudo = {"FEA-01": {k: v for k, v in r1.items() if k != "reacoes_por_combo"}, **r23, "SIM-04": r4, "f_sloshing_Hz": fslosh}
    json.dump(tudo, open(os.path.join(OUT, "FEA_resumo.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=float)

    L = ["# Resultados das simulações numéricas (FEA e transiente)", "",
         "Gerado por `fea/run_fea.py`. Ferramenta própria em Python/numpy (elementos em `fea/elementos.py`), validada pelos "
         "testes de `testes/run_testes.py`.", ""]
    L += ["## FEA-01 — Pórtico espacial da estrutura", "",
          f"Modelo: {r1['n_nos']} nós, {r1['n_elementos']} elementos (secundárias discretizadas a cada 0,22 m; elos rígidos "
          "secundária↔principal; bases rotuladas; diagonais só-tração por iteração).", "",
          "| Combinação | Iterações | ΣRz (kN) | Erro de equilíbrio (kN) | uz mín (mm) | u horiz. máx (mm) | Diagonais inativas |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for k, v in r1["combos"].items():
        L.append(f"| {k} | {v['iteracoes']} | {f2(v['soma_reacoes_Z'],1)} | {v['erro_equilibrio']:.1e} | {f2(v['uz_min_mm'])} | {f2(v['uh_max_mm'])} | {v['diag_inativas']} |")
    L += ["", "Taxas de utilização máximas (envoltória ELU; N + M biaxial + V conforme NBR 8800 — formulação 2008):", "",
          "| Grupo | Perfil | Taxa | N (kN) | Mz forte (kN·m) | My fraco (kN·m) | Vy (kN) |", "|---|---|---:|---:|---:|---:|---:|"]
    for g, v in r1["verificacao"].items():
        L.append(f"| {g} | {v['perfil']} | **{f2(v['taxa'])}** | {f2(min(v['Nc'], 0) if v['Nc'] < 0 else v['Nt'],1)} | {f2(v['Mz'],1)} | {f2(v['My'],2)} | {f2(v['Vy'],1)} |")
    L += ["", f"Flechas ELS: secundárias {f2(r1['flechas_ELS']['VS'])} mm; principais {f2(r1['flechas_ELS']['VP'])} mm "
          "(incluem a deformação do apoio; limite L/350 = 6,29 mm).", "",
          "Reações verticais do caso Q (água) — comparação com o modelo 1D (MC-02):", "",
          "| Apoio (X;Y) | FEA-01 (kN) |", "|---|---:|"]
    for k, v in r1["reacoes_Q"].items():
        L.append(f"| {k} | {f2(v,1)} |")
    L += ["", f"Análise modal (massa da água como massa rígida no nível do deck, {f2(r1['massa_total_t'],1)} t): "
          + ", ".join(f"{f2(fz)} Hz ({d})" for fz, d in zip(r1["modos_Hz"], r1["modos_desc"])) + ". "
          f"Modo convectivo (sloshing) da água estimado: {f2(fslosh,2)} Hz (desacoplado; relevante para sismo).", "",
          "![Deformada](FEA-01_deformada_ELS.png)", "", "![Utilização](FEA-01_utilizacao_ELU.png)", ""]
    c = r23["FEA-02"]
    L += ["## FEA-02 — Chapa de piso (Mindlin Q4)", "",
          f"ELS: q = {f2(c['ELS']['q'],1)} kPa → flecha máx. **{f2(c['ELS']['w_max_mm'])} mm** (limite L/250 = {f2(c['limite_flecha_mm'])} mm). "
          f"ELU: q = {f2(c['ELU']['q'],1)} kPa → M+ = {f2(c['ELU']['Mx_pos'])} / M− = {f2(c['ELU']['Mx_neg'])} kN·m/m; "
          f"σ elástica máx. = {f2(c['ELU']['sigma_max_MPa'],0)} MPa < fy/γa1 = {f2(c['sigma_Rd_MPa'],0)} MPa.", "",
          "![Chapa flecha](FEA-02_chapa_flecha.png)", "", "![Chapa Mx](FEA-02_chapa_Mx.png)", ""]
    rr = r23["FEA-03"]
    L += ["## FEA-03 — Radier sobre base elástica de Winkler", "",
          f"Malha {rr['malha']}; Ecs = {f2(rr['Ecs_GPa'],1)} GPa; MRd da malha Ø10 c/12,5 = {f2(rr['MRd_malha_kNm_m'],0)} kN·m/m por face.", "",
          "| k_s (MN/m³) [H] | Recalque máx (mm) | Recalque dif. pilares (mm) | Distorção angular | p solo máx (kPa) | p solo mín (kPa) | m* máx (kN·m/m) | Taxa flexão |",
          "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for k, v in rr["casos"].items():
        L.append(f"| {k} | {f2(v['w_max_mm'])} | {f2(v['recalque_diferencial_mm'])} | 1/{1/max(v['distorcao_angular'],1e-9):,.0f} | "
                 f"{f2(v['p_solo_max_kPa'],1)} | {f2(v['p_solo_min_kPa'],1)} | {f2(v['m_star_max'],1)} | {f2(v['taxa_flexao'])} |")
    L += ["", "![Recalque](FEA-03_radier_recalque.png)", "", "![Momento radier](FEA-03_radier_Mx.png)", ""]
    L += ["## SIM-04 — Transiente hidráulico (MOC + cavidade discreta)", "",
          f"Celeridade a = {r4['celeridade_m_s']} m/s; Joukowsky a·v/g = {r4['joukowsky_m']} m; pressão de vapor manométrica ≈ {r4['pressao_vapor_manometrica_m']} m.", "",
          "| Cenário | Rampa (s) | p máx (m.c.a.) | p mín (m.c.a.) | Separação de coluna | Cavidade máx (L) |", "|---|---:|---:|---:|---|---:|"]
    for k, v in r4.items():
        if isinstance(v, dict):
            L.append(f"| {k} | {v['t_rampa_s']} | {f2(v['p_max_mca'],1)} | {f2(v['p_min_mca'],1)} | {'SIM' if v['cavitacao'] else 'não'} | {f2(v['vol_cavidade_max_L'],3)} |")
    L += ["", "![Envoltórias](SIM-04_envoltorias.png)", "", "![Séries](SIM-04_series.png)", ""]
    open(os.path.join(OUT, "FEA.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(json.dumps({"FEA-02": r23["FEA-02"], "FEA-03": {k: {kk: vv for kk, vv in v.items() if kk != 'recalque_pilares_mm'} for k, v in rr["casos"].items()},
                      "SIM-04": r4, "slosh": fslosh}, indent=1, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
