# -*- coding: utf-8 -*-
"""Gera o modelo 3D a partir de componentes.py e checa interferências.

Uso:  python modelo3d/gerar_modelo.py
Saídas (pasta modelo3d/saida):
  captacao_caixa_casa.FCMacro   macro FreeCAD (modelo EDITÁVEL paramétrico; gera e salva .FCStd)
  captacao_caixa_casa.obj/.mtl  malha por componente (Blender, SketchUp, FreeCAD, Navisworks...)
  captacao_caixa_casa.glb       glTF 2.0 binário (visualização compartilhável)
  visualizador_3d.html          visualizador web (three.js) com camadas, status e interferências
  interferencias.md / .json     relatório de interferências e zonas livres
Convenção OBJ/GLB/HTML: Y para cima; origem no centro da caixa na cota 112,00
  (X' = X − 79,60 ; Y' = Z − 112,00 ; Z' = −Y). FreeCAD: coordenadas reais em mm (Z = cota).
"""
import base64
import json
import math
import os
import struct
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import componentes as C  # noqa: E402

OUT = os.path.join(AQUI, "saida")
os.makedirs(OUT, exist_ok=True)
X0, Y0, Z0 = C.X_CAIXA, 0.0, 112.0
TOL = 0.003
NOME = "captacao_caixa_casa"


# ===================================================================== tesselação
def tri_box(p):
    (x0, y0, z0), (x1, y1, z1) = p["min"], p["max"]
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    return v, f


def frame(a, b):
    a, b = np.array(a, float), np.array(b, float)
    w = b - a
    L = np.linalg.norm(w)
    w = w / L
    ref = np.array([0, 0, 1.0]) if abs(w[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(w, ref)
    u /= np.linalg.norm(u)
    vv = np.cross(w, u)
    return a, b, w, u, vv, L


def tri_cyl(p):
    a, b, w, u, vv, L = frame(p["a"], p["b"])
    n, r = p["n"], p["r"]
    v = []
    for i in range(n):
        ang = 2 * math.pi * i / n
        d = r * (math.cos(ang) * u + math.sin(ang) * vv)
        v.append(tuple(a + d))
        v.append(tuple(b + d))
    v.append(tuple(a))
    v.append(tuple(b))
    ca, cb = 2 * n, 2 * n + 1
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [(2 * i, 2 * j, 2 * j + 1), (2 * i, 2 * j + 1, 2 * i + 1), (ca, 2 * j, 2 * i), (cb, 2 * i + 1, 2 * j + 1)]
    return v, f


def tesselar(comp):
    V, F = [], []
    for p in comp["prims"]:
        if p["t"] == "box":
            v, f = tri_box(p)
        elif p["t"] == "cyl":
            v, f = tri_cyl(p)
        else:
            v, f = [tuple(x) for x in p["v"]], [tuple(x) for x in p["f"]]
        o = len(V)
        V += v
        F += [(a + o, b + o, c + o) for a, b, c in f]
    return V, F


def to_yup(v):
    x, y, z = v
    return (x - X0, z - Z0, -(y - Y0))


# ===================================================================== interferências
def aabb_prim(p):
    if p["t"] == "box":
        return np.array(p["min"]), np.array(p["max"])
    if p["t"] == "cyl":
        a, b = np.array(p["a"]), np.array(p["b"])
        return np.minimum(a, b) - p["r"], np.maximum(a, b) + p["r"]
    v = np.array(p["v"])
    return v.min(0), v.max(0)


def pontos_cyl(p, passo=0.04):
    a, b, w, u, vv, L = frame(p["a"], p["b"])
    r = p["r"]
    nt = max(3, int(L / passo) + 1)
    ts = np.linspace(TOL * 2, L - TOL * 2, nt)
    nr = max(1, int(math.ceil((r - TOL) / 0.05)))
    pts = [np.zeros(3)]
    for k in range(1, nr + 1):
        rk = (r - 2 * TOL) * k / nr
        m = max(8, int(2 * math.pi * rk / 0.05))
        for i in range(m):
            ang = 2 * math.pi * i / m
            pts.append(rk * (math.cos(ang) * u + math.sin(ang) * vv))
    pts = np.array(pts)
    return (a[None, None, :] + ts[:, None, None] * w[None, None, :] + pts[None, :, :]).reshape(-1, 3)


def dentro_box(P, p):
    mn, mx = np.array(p["min"]) + TOL, np.array(p["max"]) - TOL
    return np.all((P > mn) & (P < mx), axis=1)


def dentro_cyl(P, p):
    a, b, w, u, vv, L = frame(p["a"], p["b"])
    d = P - a
    t = d @ w
    rad = np.linalg.norm(d - np.outer(t, w), axis=1)
    return (t > TOL) & (t < L - TOL) & (rad < p["r"] - TOL)


def colide_prim(p, q):
    """Retorna ponto aproximado de interferência ou None."""
    amn, amx = aabb_prim(p)
    bmn, bmx = aabb_prim(q)
    if np.any(amx - TOL < bmn) or np.any(bmx - TOL < amn):
        return None
    if p["t"] == "mesh" or q["t"] == "mesh":
        return None
    if p["t"] == "box" and q["t"] == "box":
        lo, hi = np.maximum(amn, bmn), np.minimum(amx, bmx)
        if np.all(hi - lo > TOL):
            return (lo + hi) / 2
        return None
    if p["t"] == "box":
        p, q = q, p
    P = pontos_cyl(p)
    ins = dentro_box(P, q) if q["t"] == "box" else dentro_cyl(P, q)
    if q["t"] == "cyl" and not ins.any():
        P2 = pontos_cyl(q)
        ins2 = dentro_cyl(P2, p)
        if ins2.any():
            return P2[ins2].mean(0)
    if ins.any():
        return P[ins].mean(0)
    return None


def aabb_comp(c):
    mins, maxs = zip(*[aabb_prim(p) for p in c["prims"]])
    return np.min(mins, 0), np.max(maxs, 0)


IGNORAR = {"TER-01", "RIO-MIN", "RIO-NOR", "RIO-MAX", "AREA-8x8", "AREA-AMP"}


def checar(comps):
    res = []
    bb = {c["tag"]: aabb_comp(c) for c in comps}
    for i, A in enumerate(comps):
        for B in comps[i + 1:]:
            if A["tag"] in IGNORAR or B["tag"] in IGNORAR:
                continue
            if A["zona"] and B["zona"]:
                continue
            if B["tag"] in A["permite"] or A["tag"] in B["permite"]:
                continue
            amn, amx = bb[A["tag"]]
            bmn, bmx = bb[B["tag"]]
            if np.any(amx - TOL < bmn) or np.any(bmx - TOL < amn):
                continue
            pts = []
            for p in A["prims"]:
                for q in B["prims"]:
                    r = colide_prim(p, q)
                    if r is not None:
                        pts.append(r)
            if pts:
                tipo = "zona livre obstruída" if (A["zona"] or B["zona"]) else "interferência física"
                res.append(dict(a=A["tag"], b=B["tag"], tipo=tipo, ponto=np.mean(pts, 0).round(3).tolist(), n=len(pts)))
    return res


TRATAMENTO = {
    ("PT-01", "ZN-04"): "Sequência de montagem: patamar superior entra no envelope de içamento — montar o patamar e a prumada N1 após posicionar e ancorar a caixa (ou torná-los desmontáveis).",
    ("TB-102", "ZN-04"): "Sequência de montagem: trecho horizontal da entrada sobre o teto — instalar após o içamento.",
}


# ===================================================================== exportadores
def hex2rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def exporta_obj(comps, malhas):
    mtl = []
    for cat, (nome, cor) in C.CATEGORIAS.items():
        r, g, b = hex2rgb(cor)
        d = 0.35 if cat in ("zonas", "rio") else 1.0
        mtl.append(f"newmtl {cat}\nKd {r:.3f} {g:.3f} {b:.3f}\nd {d}\n")
    open(os.path.join(OUT, NOME + ".mtl"), "w", encoding="utf-8").write("\n".join(mtl))
    L = [f"# {NOME}.obj — gerado por modelo3d/gerar_modelo.py (Y para cima, origem centro da caixa @112,00)", f"mtllib {NOME}.mtl"]
    o = 1
    for c in comps:
        V, F = malhas[c["tag"]]
        L.append(f"g {c['tag']}__{c['status']}")
        L.append(f"usemtl {c['cat']}")
        for v in V:
            x, y, z = to_yup(v)
            L.append(f"v {x:.4f} {y:.4f} {z:.4f}")
        for a, b, cc in F:
            L.append(f"f {a + o} {b + o} {cc + o}")
        o += len(V)
    open(os.path.join(OUT, NOME + ".obj"), "w", encoding="utf-8").write("\n".join(L) + "\n")


def flat_arrays(V, F):
    pos = []
    nor = []
    for a, b, c in F:
        pa, pb, pc = [np.array(to_yup(V[k])) for k in (a, b, c)]
        n = np.cross(pb - pa, pc - pa)
        nn = np.linalg.norm(n)
        n = n / nn if nn > 0 else np.array([0, 1.0, 0])
        for p in (pa, pb, pc):
            pos += list(p)
            nor += list(n)
    return np.array(pos, np.float32), np.array(nor, np.float32)


def exporta_glb(comps, malhas):
    buf = bytearray()
    views, accs, meshes, nodes, mats = [], [], [], [], []
    mat_idx = {}
    for cat, (nome, cor) in C.CATEGORIAS.items():
        r, g, b = hex2rgb(cor)
        transp = cat in ("zonas", "rio")
        m = {"name": cat, "pbrMetallicRoughness": {"baseColorFactor": [r, g, b, 0.35 if transp else 1.0],
                                                   "metallicFactor": 0.1, "roughnessFactor": 0.8}, "doubleSided": True}
        if transp:
            m["alphaMode"] = "BLEND"
        mat_idx[cat] = len(mats)
        mats.append(m)
    for c in comps:
        V, F = malhas[c["tag"]]
        pos, nor = flat_arrays(V, F)
        for arr, tipo in ((pos, "POS"), (nor, "NOR")):
            while len(buf) % 4:
                buf.append(0)
            off = len(buf)
            buf += arr.tobytes()
            views.append({"buffer": 0, "byteOffset": off, "byteLength": arr.nbytes, "target": 34962})
            acc = {"bufferView": len(views) - 1, "componentType": 5126, "count": len(arr) // 3, "type": "VEC3"}
            if tipo == "POS":
                p3 = arr.reshape(-1, 3)
                acc["min"] = p3.min(0).tolist()
                acc["max"] = p3.max(0).tolist()
            accs.append(acc)
        meshes.append({"name": c["tag"], "primitives": [{"attributes": {"POSITION": len(accs) - 2, "NORMAL": len(accs) - 1},
                                                          "material": mat_idx[c["cat"]]}]})
        nodes.append({"name": c["tag"], "mesh": len(meshes) - 1,
                      "extras": {"descricao": c["desc"], "status": c["status"], "pendencia": c["pend"], "categoria": c["cat"]}})
    while len(buf) % 4:
        buf.append(0)
    gltf = {"asset": {"version": "2.0", "generator": "gerar_modelo.py (estudo captação/caixa/casa)"},
            "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": meshes,
            "materials": mats, "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(buf)}]}
    js = json.dumps(gltf, ensure_ascii=False).encode("utf-8")
    while len(js) % 4:
        js += b" "
    total = 12 + 8 + len(js) + 8 + len(buf)
    with open(os.path.join(OUT, NOME + ".glb"), "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, total))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        fh.write(struct.pack("<II", len(buf), 0x004E4942) + bytes(buf))
    return total


def exporta_freecad(comps):
    dados = []
    for c in comps:
        prims = []
        for p in c["prims"]:
            if p["t"] == "box":
                prims.append(["box", [round(k * 1000, 1) for k in p["min"]], [round(k * 1000, 1) for k in p["max"]]])
            elif p["t"] == "cyl":
                prims.append(["cyl", [round(k * 1000, 1) for k in p["a"]], [round(k * 1000, 1) for k in p["b"]], round(p["r"] * 1000, 1)])
            else:
                prims.append(["mesh", [[round(k * 1000, 1) for k in v] for v in p["v"]], p["f"]])
        dados.append({"tag": c["tag"], "desc": c["desc"], "cat": c["cat"], "status": c["status"], "pend": c["pend"], "prims": prims})
    cats = {k: [v[0], hex2rgb(v[1])] for k, v in C.CATEGORIAS.items()}
    macro = f'''# -*- coding: utf-8 -*-
# Macro FreeCAD escrita para a API do FreeCAD 0.21 / 1.0 — NÃO executada no ambiente de geração (FreeCAD indisponível); validada apenas sintaticamente.
# Modelo EDITÁVEL do estudo
# "Captação, caixa 50 m³ e abastecimento não potável".
# Uso: FreeCAD > Macro > Macros... > executar este arquivo (ou: FreeCADCmd {NOME}.FCMacro)
# Gera um documento com grupos por disciplina, um objeto Part por componente (Label = TAG),
# propriedades Descricao/Status/Pendencia e salva {NOME}.FCStd na mesma pasta.
# Unidades: mm; coordenadas reais do estudo (X ao longo do traçado, Y norte, Z = cota × 1000).
import json, os
import FreeCAD as App
import Part, Mesh
DADOS = json.loads(r"""{json.dumps(dados, ensure_ascii=False)}""")
CATS = json.loads(r"""{json.dumps(cats, ensure_ascii=False)}""")
V = App.Vector
doc = App.newDocument("CaptacaoCaixaCasa")
grupos = {{}}
for k, (nome, cor) in CATS.items():
    g = doc.addObject("App::DocumentObjectGroup", "G_" + k.replace("-", "_"))
    g.Label = nome
    grupos[k] = g
for c in DADOS:
    shapes = []
    malha = None
    for p in c["prims"]:
        if p[0] == "box":
            (x0, y0, z0), (x1, y1, z1) = p[1], p[2]
            shapes.append(Part.makeBox(max(x1 - x0, 0.1), max(y1 - y0, 0.1), max(z1 - z0, 0.1), V(x0, y0, z0)))
        elif p[0] == "cyl":
            a, b, r = V(*p[1]), V(*p[2]), p[3]
            d = b - a
            if d.Length > 0.1:
                shapes.append(Part.makeCylinder(r, d.Length, a, d))
        else:
            vs, fs = p[1], p[2]
            malha = Mesh.Mesh([[vs[i] for i in f] for f in fs])
    if malha is not None:
        o = doc.addObject("Mesh::Feature", c["tag"].replace("-", "_"))
        o.Mesh = malha
    else:
        o = doc.addObject("Part::Feature", c["tag"].replace("-", "_"))
        o.Shape = Part.makeCompound(shapes)
    o.Label = c["tag"]
    for prop, val in (("Descricao", c["desc"]), ("Status", c["status"]), ("Pendencia", c["pend"])):
        o.addProperty("App::PropertyString", prop, "Estudo")
        setattr(o, prop, val)
    grupos[c["cat"]].addObject(o)
    if App.GuiUp:
        cor = tuple(CATS[c["cat"]][1])
        try:
            o.ViewObject.ShapeColor = cor
            if c["cat"] in ("zonas", "rio"):
                o.ViewObject.Transparency = 65
            if c["tag"] == "TQ-101":
                o.ViewObject.Transparency = 40
        except Exception:
            pass
doc.recompute()
try:
    pasta = os.path.dirname(os.path.abspath(__file__))
except NameError:
    pasta = os.getcwd()
doc.saveAs(os.path.join(pasta, "{NOME}.FCStd"))
if App.GuiUp:
    import FreeCADGui as Gui
    Gui.SendMsgToActiveView("ViewFit")
    Gui.activeDocument().activeView().viewIsometric()
print("Modelo gerado:", len(DADOS), "componentes")
'''
    open(os.path.join(OUT, NOME + ".FCMacro"), "w", encoding="utf-8").write(macro)


def exporta_html(comps, malhas, clashes):
    itens = []
    for c in comps:
        V, F = malhas[c["tag"]]
        pos, _ = flat_arrays(V, F)
        itens.append({"tag": c["tag"], "desc": c["desc"], "cat": c["cat"], "status": c["status"], "pend": c["pend"],
                      "zona": c["zona"], "pos": base64.b64encode(pos.round(3).astype(np.float32).tobytes()).decode()})
    marc = []
    for k in clashes:
        x, y, z = to_yup(k["ponto"])
        marc.append({"a": k["a"], "b": k["b"], "tipo": k["tipo"], "p": [round(x, 3), round(y, 3), round(z, 3)],
                     "trat": k.get("tratamento", "")})
    dados = {"itens": itens, "cats": {k: v for k, v in C.CATEGORIAS.items()}, "status": C.STATUS_COR, "clashes": marc}
    tpl = open(os.path.join(AQUI, "visualizador_template.html"), encoding="utf-8").read()
    html = tpl.replace("/*__DADOS__*/null", json.dumps(dados, ensure_ascii=False))
    cab = ['<!doctype html>', '<html lang="pt-BR">',
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">']
    html = "\n".join(cab) + "\n" + html
    open(os.path.join(OUT, "visualizador_3d.html"), "w", encoding="utf-8").write(html)
    return len(html)


def relatorio_clash(clashes, comps):
    tags = {c["tag"]: c for c in comps}
    L = ["# Relatório de interferências e zonas livres", "",
         "Gerado automaticamente por `modelo3d/gerar_modelo.py` a partir da geometria de `componentes.py`.",
         "Critério: penetração > 3 mm entre sólidos (caixas por AABB exata; cilindros por amostragem volumétrica a cada 4 cm), "
         "excluídos os contatos intencionais declarados em `permite` de cada componente (ex.: viga apoiada em pilar, tubo "
         "conectado a bocal, tubo atravessando piso grade). Zonas livres (ZN-xx) representam espaços de operação, circulação, "
         "subida, içamento e retirada de equipamentos e não podem ser ocupadas.", "",
         f"Componentes verificados: {len(comps)}. Ocorrências: {len(clashes)}.", "",
         "Histórico: a 1ª execução encontrou 8 ocorrências, corrigidas no arranjo — (1) recalque do booster atravessava o "
         "compartimento de cloração → passou sob o piso; (2) suporte do extravasor dentro da caixa de recepção CP-301 → "
         "deslocado com bloco próprio; (3) escada marinheiro sobre os pedestais do patamar e (4) espaço de subida obstruído → "
         "escada afastada para X = 83,40 e largura 0,40 m; (5–6) guarda-corpo/escada e faixa de circulação → ajuste de "
         "limites; (7) contato mangueira × recalque na caixa de válvulas → conexão declarada; (8) pé da escada → ajuste da "
         "zona. As ocorrências remanescentes abaixo são de sequência de montagem e estão tratadas.", ""]
    if clashes:
        L += ["| # | Componente A | Componente B | Tipo | Ponto (X; Y; Z) real | Tratamento |", "|---|---|---|---|---|---|"]
        for i, k in enumerate(clashes, 1):
            p = k["ponto"]
            L.append(f"| {i} | {k['a']} | {k['b']} | {k['tipo']} | {p[0]:.2f}; {p[1]:.2f}; {p[2]:.2f} | {k.get('tratamento','—')} |")
    else:
        L.append("Nenhuma interferência física ou zona obstruída além das tratadas.")
    L += ["", "## Contatos intencionais declarados (não reportados)", ""]
    for c in comps:
        if c["permite"]:
            L.append(f"- **{c['tag']}** ↔ {', '.join(c['permite'])}")
    L += ["", "## Limitações", "",
          "- Geometria simplificada (perfis sem raios, conexões e válvulas como trechos retos; bocais com posição hipotética).",
          "- Bocais, teto, boca de visita e acessórios da caixa dependem do desenho certificado do fornecedor — refazer a checagem com ele.",
          "- Terreno é um perfil hipotético extrudado em Y; interferências com o terreno não são verificadas (dependem de topografia).",
          "- Itens dentro da casa não modelados (projeto interno de terceiros)."]
    open(os.path.join(OUT, "interferencias.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    json.dump(clashes, open(os.path.join(OUT, "interferencias.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    comps = C.construir()
    malhas = {c["tag"]: tesselar(c) for c in comps}
    ntri = sum(len(F) for _, F in malhas.values())
    clashes = checar(comps)
    for k in clashes:
        k["tratamento"] = TRATAMENTO.get((k["a"], k["b"]), TRATAMENTO.get((k["b"], k["a"]), "A RESOLVER"))
    exporta_obj(comps, malhas)
    tam = exporta_glb(comps, malhas)
    exporta_freecad(comps)
    th = exporta_html(comps, malhas, clashes)
    relatorio_clash(clashes, comps)
    json.dump([{k: v for k, v in c.items() if k != "prims"} | {"aabb": [x.round(3).tolist() for x in aabb_comp(c)]} for c in comps],
              open(os.path.join(OUT, "componentes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(comps)} componentes, {ntri} triângulos; GLB {tam/1024:.0f} kB; HTML {th/1024:.0f} kB")
    for k in clashes:
        print("  CLASH", k["a"], "x", k["b"], k["tipo"], k["ponto"], "->", k["tratamento"][:60])


if __name__ == "__main__":
    main()
