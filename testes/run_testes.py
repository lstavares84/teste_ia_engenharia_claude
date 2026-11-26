# -*- coding: utf-8 -*-
"""Testes de comprovação (verificação de software e de consistência) — executados de fato.

Uso: python testes/run_testes.py  ->  testes/RELATORIO_TESTES.md  (código de saída 1 se algum falhar)
Cada teste compara a ferramenta de cálculo com solução analítica de referência (literatura clássica)
ou verifica integridade/consistência dos entregáveis.
"""
import hashlib
import json
import math
import os
import struct
import subprocess
import sys
import time
import xml.dom.minidom

import numpy as np

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in ("calc", "fea", "modelo3d"):
    sys.path.insert(0, os.path.join(RAIZ, p))

from premissas import *  # noqa
import estrutura as EST
import hidraulica as HD
from elementos import Portico, PlacaRet
import transiente_moc as MOC

R = []


def teste(cod, nome, ref, obtido, tol, criterio, fonte):
    ok = bool(criterio)
    R.append(dict(cod=cod, nome=nome, ref=ref, obtido=obtido, tol=tol, ok=ok, fonte=fonte))
    print(("PASS " if ok else "FAIL ") + cod, nome, "|", obtido)


def err(a, b):
    return abs(a - b) / abs(b)


# T01 viga contínua
s = EST.props_I("W150x13,0")
r = EST.viga_continua(4.4, [0, 2.2, 4.4], {"q": lambda x: 10.0}, E_ACO * 1e3 * s["Ix"])
e1, e2 = err(r["reac"][1], 27.5), err(np.max(np.abs(r["M"])), 6.05)
teste("T01", "Viga contínua 2 vãos (FE 1D) — reação central e momento no apoio", "R = 1,25qL = 27,50 kN; M = qL²/8 = 6,050 kN·m",
      f"R = {r['reac'][1]:.3f}; M = {np.max(np.abs(r['M'])):.3f}", "< 0,5 %", e1 < 0.005 and e2 < 0.005, "Timoshenko & Young, teoria das estruturas")

# T02 pórtico: balanço 3D
P = Portico()
E, Gm = 200e6, 77e6
pr = dict(E=E, G=Gm, A=0.004, Iz=8e-6, Iy=2e-6, J=1e-7)
a, b = P.no(0, 0, 0), P.no(2.0, 0, 0)
P.barra(a, b, pr, ref=(0, 0, 1))
P.apoios[a] = [0, 1, 2, 3, 4, 5]
F = np.zeros(P.ndof())
F[6 * b + 2] = -10.0
F[6 * b + 1] = 5.0
F[6 * b + 0] = 100.0
u, Rv, esf, _ = P.resolver(F, {})
wz, wy, ux = u[6 * b + 2], u[6 * b + 1], u[6 * b]
rz, ry, rx = -10 * 8 / (3 * E * 8e-6), 5 * 8 / (3 * E * 2e-6), 100 * 2 / (E * 0.004)  # vertical: Iz (forte, alma vertical); lateral: Iy
teste("T02", "Pórtico espacial — balanço com cargas em 3 direções", "δ = PL³/3EI (eixo forte vertical, fraco lateral); δ = NL/EA",
      f"uz {wz:.3e} (ref {rz:.3e}); uy {wy:.3e} (ref {ry:.3e}); ux {ux:.3e} (ref {rx:.3e})", "< 0,1 %",
      err(wz, rz) < 1e-3 and err(wy, ry) < 1e-3 and err(ux, rx) < 1e-3, "Resistência dos materiais")

# T03 / T04 pórtico do projeto (resultados gravados)
fea = json.load(open(os.path.join(RAIZ, "fea", "resultados", "FEA_resumo.json"), encoding="utf-8"))
f1 = fea["FEA-01"]
emax = max(v["erro_equilibrio"] for v in f1["combos"].values())
teste("T03", "Pórtico do projeto — equilíbrio global (6 combinações)", "Σ reações = Σ cargas", f"erro máx {emax:.2e} kN", "< 1e-6 kN",
      emax < 1e-6, "Equilíbrio estático")
sq = sum(f1["reacoes_Q"].values())
res = json.load(open(os.path.join(RAIZ, "calc", "resultados", "resultados.json"), encoding="utf-8"))["MC-02_estrutura_fundacao"]
dif_c = err(f1["reacoes_Q"]["79.60;0.00"], res["reac_Q"][1][1])
teste("T04", "Pórtico 3D × modelo 1D (MC-02) — carga de água e pilar central", f"ΣQ = W_água = {res['W_agua']:.1f} kN; pilar central 1D = {res['reac_Q'][1][1]:.1f} kN",
      f"ΣQ = {sq:.1f} kN; pilar central 3D = {f1['reacoes_Q']['79.60;0.00']:.1f} kN (dif. {dif_c*100:.0f} %)", "ΣQ < 1 %; pilar < 20 %",
      err(sq, res["W_agua"]) < 0.01 and dif_c < 0.20, "Consistência entre modelos (o 1D supõe apoios rígidos → conservador)")

# T05/T06 placa Mindlin
Ep, nu, t, aa, q = 200e6, 0.3, 0.0095, 1.0, 10.0
D = Ep * t ** 3 / (12 * (1 - nu ** 2))
xs = np.linspace(0, aa, 17)
Pl = PlacaRet(xs, xs, Ep, nu, t)
borda = [k for k in range(Pl.nn) if Pl.coord(k)[0] in (0, aa) or Pl.coord(k)[1] in (0, aa)]
u, M = Pl.resolver(lambda x, y: q, fix_w=borda)
w_ss = -u[0::3].min()
teste("T05", "Placa de Mindlin Q4 — placa quadrada simplesmente apoiada, carga uniforme", "w = 0,00406 qa⁴/D; Mx = 0,0479 qa²",
      f"w = {w_ss*1000:.4f} mm (ref {0.00406*q*aa**4/D*1000:.4f}); Mx = {M[:,0].max():.4f} (ref {0.0479*q*aa**2:.4f})", "< 2 %",
      err(w_ss, 0.00406 * q * aa ** 4 / D) < 0.02 and err(M[:, 0].max(), 0.0479 * q) < 0.02, "Timoshenko & Woinowsky-Krieger, Theory of Plates, tab. 8")
u, M = Pl.resolver(lambda x, y: q, fix_all=borda)
w_cl = -u[0::3].min()
teste("T06", "Placa de Mindlin Q4 — placa quadrada engastada, carga uniforme", "w = 0,00126 qa⁴/D",
      f"w = {w_cl*1000:.4f} mm (ref {0.00126*q*aa**4/D*1000:.4f})", "< 5 %", err(w_cl, 0.00126 * q * aa ** 4 / D) < 0.05,
      "Timoshenko & Woinowsky-Krieger, tab. 35")
# T07 Winkler
xs = np.linspace(0, 3, 9)
Pl = PlacaRet(xs, xs, 26e6, 0.2, 0.4)
u, M = Pl.resolver(lambda x, y: 25.0, molas_w=20e3)
w = -u[0::3]
teste("T07", "Placa sobre base de Winkler — carga uniforme em placa livre", "w = q/k = 1,250 mm (uniforme), M ≈ 0",
      f"w = {w.min()*1000:.4f}–{w.max()*1000:.4f} mm; |M|max = {np.abs(M).max():.2e}", "< 0,1 %",
      err(w.mean(), 25 / 20e3) < 1e-3 and np.ptp(w) < 1e-6 and np.abs(M).max() < 1e-6, "Solução exata (corpo rígido sobre molas)")

# T08 MOC Joukowsky
rr = MOC.simular(0.0, T=0.5, N=40, atrito=False, perfil=False, H_jus=200.0, cavit=False)
dH = rr["H0"] - (rr["p_bomba"].min() + 0.0)
jk = rr["a"] * rr["v0"] / G
teste("T08", "MOC — parada instantânea, tubo horizontal sem atrito", f"ΔH = a·v/g = {jk:.2f} m",
      f"ΔH = {dH:.2f} m", "< 2 %", err(dH, jk) < 0.02, "Joukowsky; Wylie & Streeter, Fluid Transients")
rr = MOC.simular(1e9, T=2.0, N=40)
var = float(np.ptp(rr["p_bomba"]))
teste("T09", "MOC — regime permanente preservado (sem perturbação)", "variação de pressão nula", f"variação {var:.2e} m", "< 1e-3 m",
      var < 1e-3, "Consistência numérica (Courant = 1)")

# T10 Swamee-Jain × Colebrook
D_ = di_pead(40)
v_, Re, fsj, _ = HD.perda_distribuida(3.0 / 3600, D_, 100)
fc = 0.02
for _ in range(50):
    fc = (-2 * math.log10(RUGOSIDADE_PROJ / (3.7 * D_) + 2.51 / (Re * math.sqrt(fc)))) ** -2
teste("T10", "Fator de atrito — Swamee-Jain × Colebrook-White (iterativa)", f"f Colebrook = {fc:.5f}", f"f Swamee-Jain = {fsj:.5f}",
      "< 1,5 %", err(fsj, fc) < 0.015, "Colebrook (1939); Swamee & Jain (1976)")

# T11 NBR 8800 — sanidade das funções de resistência
sp = EST.props_I("W150x29,8")
MRd, _ = EST.MRd_I(sp, 345, 0.05)
NRd, d = EST.NcRd_I(sp, 345, 0.05, 0.05, 0.05)
teste("T11", "Funções NBR 8800 — limites teóricos (Lb→0, L→0)", "MRd = Zx·fy/γa1; NcRd = A·fy/γa1",
      f"MRd {MRd:.2f} (ref {sp['Zx']*345e3/1.1:.2f}); NcRd {NRd:.1f} (ref {sp['A']*345e3/1.1:.1f})", "< 0,5 %",
      err(MRd, sp["Zx"] * 345e3 / 1.1) < 0.005 and err(NRd, sp["A"] * 345e3 / 1.1) < 0.005, "ABNT NBR 8800 (formulação 2008)")

# T12 GLB
b = open(os.path.join(RAIZ, "modelo3d", "saida", "captacao_caixa_casa.glb"), "rb").read()
mg, ver, tot = struct.unpack("<III", b[:12])
lj, _ = struct.unpack("<II", b[12:20])
js = json.loads(b[20:20 + lj])
lb, _ = struct.unpack("<II", b[20 + lj:28 + lj])
okacc = all(js["bufferViews"][a_["bufferView"]]["byteOffset"] + a_["count"] * 12 <= lb for a_ in js["accessors"])
teste("T12", "Modelo glTF 2.0 (.glb) — integridade binária", "magic glTF, versão 2, tamanhos e acessores dentro do buffer",
      f"versão {ver}; {len(js['nodes'])} nós; {len(js['accessors'])} acessores", "estrutural",
      mg == 0x46546C67 and ver == 2 and tot == len(b) and okacc, "Especificação Khronos glTF 2.0")

# T13 SVG
svgdir = os.path.join(RAIZ, "desenhos", "svg")
oks = []
for fsvg in sorted(os.listdir(svgdir)):
    try:
        xml.dom.minidom.parse(os.path.join(svgdir, fsvg))
        oks.append(True)
    except Exception:
        oks.append(False)
teste("T13", "Desenhos SVG — XML bem formado", "7 folhas válidas", f"{sum(oks)}/{len(oks)} válidas", "100 %", all(oks) and len(oks) == 7, "W3C SVG/XML")

# T14 interferências
cl = json.load(open(os.path.join(RAIZ, "modelo3d", "saida", "interferencias.json"), encoding="utf-8"))
teste("T14", "Modelo 3D — interferências remanescentes tratadas", "somente ocorrências de sequência de montagem com tratamento",
      f"{len(cl)} ocorrências: " + "; ".join(f"{c['a']}×{c['b']}" for c in cl), "0 'A RESOLVER'",
      all(c.get("tratamento", "A RESOLVER") != "A RESOLVER" for c in cl), "Checagem geométrica automática (gerar_modelo.py)")

# T15 reprodutibilidade
arq = os.path.join(RAIZ, "calc", "resultados", "resultados.json")
h1 = hashlib.sha256(open(arq, "rb").read()).hexdigest()
subprocess.run([sys.executable, os.path.join(RAIZ, "calc", "run_all.py")], capture_output=True, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
h2 = hashlib.sha256(open(arq, "rb").read()).hexdigest()
teste("T15", "Reprodutibilidade das memórias de cálculo", "hash idêntico em execuções sucessivas", f"{h1[:12]} = {h2[:12]}", "idêntico", h1 == h2,
      "Determinismo do pipeline")

# T16 balanço de energia da captação (independente)
C_ = CAPTACAO
h_est = NIVEIS["entrada_N1_descarga_livre"] - COTAS["rio_min"]
_, _, _, hf = HD.perda_distribuida(3.0 / 3600, di_pead(40), C_["L_recalque_m"])
hl = sum(C_["K_singular"].values()) * (3.0 / 3600 / (math.pi * di_pead(40) ** 2 / 4)) ** 2 / (2 * G)
H_ind = h_est + 1.1 * (hf + hl) + C_["perda_filtro_sujo_m"] + C_["perda_hidrometro_m"]
Hmc = json.load(open(arq, encoding="utf-8"))["MC-01_hidraulica"]["H1_proj"]
teste("T16", "Hman de P-101 recalculada de forma independente", f"MC-01: {Hmc:.3f} m", f"{H_ind:.3f} m", "< 0,1 %", err(H_ind, Hmc) < 1e-3,
      "Balanço de energia (Bernoulli + perdas)")

# relatório
L = ["# Relatório de testes de comprovação", "", f"Executado em {time.strftime('%Y-%m-%d %H:%M')} com Python {sys.version.split()[0]} / numpy {np.__version__}.",
     f"Resultado: **{sum(r['ok'] for r in R)}/{len(R)} aprovados**.", "",
     "| Código | Teste | Referência | Obtido | Tolerância | Resultado | Fonte da referência |", "|---|---|---|---|---|---|---|"]
for r in R:
    L.append(f"| {r['cod']} | {r['nome']} | {r['ref']} | {r['obtido']} | {r['tol']} | {'✅ PASSOU' if r['ok'] else '❌ FALHOU'} | {r['fonte']} |")
L += ["", "Os testes verificam a **implementação** (software) e a **consistência** dos resultados. Não substituem a revisão "
      "independente por engenheiro habilitado, nem a validação com dados reais de campo e de fornecedores."]
open(os.path.join(RAIZ, "testes", "RELATORIO_TESTES.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
sys.exit(0 if all(r["ok"] for r in R) else 1)
