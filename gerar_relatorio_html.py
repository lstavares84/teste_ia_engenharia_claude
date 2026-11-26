# -*- coding: utf-8 -*-
"""Converte ESTUDO_TECNICO.md em HTML (com desenhos SVG embutidos e link para o visualizador 3D).

Uso: python gerar_relatorio_html.py
Saídas: estudo_tecnico.html (documento completo, abre localmente)
        artifact/index.html + artifact/visualizador_3d.html (versão para publicação)
"""
import html
import os
import re
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
MD = open(os.path.join(AQUI, "ESTUDO_TECNICO.md"), encoding="utf-8").read()


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def slug(t):
    t = re.sub(r"<[^>]+>", "", t).lower()
    t = re.sub(r"[^\w\s-]", "", t)
    return re.sub(r"\s+", "-", t.strip())[:60]


def md2html(md):
    out, toc = [], []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("```"):
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].startswith("```"):
                buf.append(lines[j])
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,4}) (.*)$", l)
        if m:
            n = len(m.group(1))
            txt = inline(m.group(2))
            sid = slug(txt)
            if n == 2:
                toc.append((sid, re.sub(r"<[^>]+>", "", txt)))
            out.append(f'<h{n} id="{sid}">{txt}</h{n}>')
            i += 1
            continue
        if l.strip() == "---":
            out.append("<hr>")
            i += 1
            continue
        if l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            head, body = cells[0], [c for c in cells[2:]]
            t = ['<div class="tw"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"]
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if l.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:])
                i += 1
            out.append('<aside class="nota">' + inline(" ".join(buf)) + "</aside>")
            continue
        if re.match(r"^(\s*)([-*]|\d+\.) ", l):
            ordered = bool(re.match(r"^\s*\d+\. ", l))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and re.match(r"^(\s*)([-*]|\d+\.) ", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.) ", "", lines[i]))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        if not l.strip():
            i += 1
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||> |```|---|\s*[-*] |\s*\d+\. )", lines[i]):
            buf.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out), toc


DESENHOS = [
    ("DES-01_implantacao_geral.svg", "DES-01 Implantação geral"),
    ("DES-02_perfil_hidraulico.svg", "DES-02 Perfil longitudinal e linhas piezométricas"),
    ("DES-03_estrutura_fundacao.svg", "DES-03 Estrutura metálica e fundação"),
    ("DES-04_arranjo_area_caixa.svg", "DES-04 Arranjo da área da caixa e ampliação"),
    ("DES-05_fluxograma_PID.svg", "DES-05 Fluxograma de processo e instrumentação"),
    ("DES-06_unifilar.svg", "DES-06 Diagrama unifilar"),
    ("DES-07_captacao_corte.svg", "DES-07 Captação: corte da margem"),
]


def galeria():
    h = ['<section class="galeria" id="desenhos"><h3>13.4 Desenhos</h3>'
         '<p class="leg">Folhas em fundo branco (papel). Role horizontalmente no celular. Os arquivos SVG originais estão em '
         '<code>desenhos/svg/</code>.</p>']
    for f, cap in DESENHOS:
        svg = open(os.path.join(AQUI, "desenhos", "svg", f), encoding="utf-8").read()
        svg = re.sub(r'width="\d+" height="\d+"', 'preserveAspectRatio="xMidYMid meet"', svg, count=1)
        h.append(f'<figure><div class="folha">{svg}</div><figcaption>{html.escape(cap)}</figcaption></figure>')
    h.append("</section>")
    return "\n".join(h)


CSS = """
/* Layout: relatório técnico com índice lateral fixo (desktop) e coluna única (celular) */
:root{
  --bg:#f4f6f8; --paper:#ffffff; --ink:#1b2530; --muted:#5a6774; --line:#d6dde4; --accent:#1d5f99; --accent-2:#7a3fa8;
  --warn:#b42318; --tint:#e8f0f7;
  --f-text:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --f-head:"IBM Plex Sans Condensed","IBM Plex Sans",system-ui,sans-serif;
  --f-mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#11161b; --paper:#171e25; --ink:#e2e8ee; --muted:#9aa7b4; --line:#2a343e; --accent:#6cb0ea; --accent-2:#c29be3;
  --warn:#ff8a7a; --tint:#1c2a37; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#11161b; --paper:#171e25; --ink:#e2e8ee; --muted:#9aa7b4; --line:#2a343e; --accent:#6cb0ea; --accent-2:#c29be3;
  --warn:#ff8a7a; --tint:#1c2a37; color-scheme:dark}
body{background:var(--bg);color:var(--ink);font:15px/1.6 var(--f-text)}
.wrap{display:grid;grid-template-columns:260px minmax(0,1fr);gap:32px;max-width:1280px;margin:0 auto;
  padding-left:max(16px, env(safe-area-inset-left,0px));padding-right:max(16px, env(safe-area-inset-right,0px));padding-block:24px}
nav.toc{position:sticky;top:calc(env(safe-area-inset-top,0px) + 16px);align-self:start;max-height:calc(100vh - 32px);overflow:auto;font-size:13px}
nav.toc h2{font:600 11px var(--f-text);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
nav.toc ol{list-style:none;margin:0;padding:0;display:grid;gap:2px}
nav.toc a{color:var(--ink);text-decoration:none;display:block;padding:4px 8px;border-radius:4px;line-height:1.35}
nav.toc a:hover,nav.toc a:focus-visible{background:var(--tint);outline:none}
nav.toc .cta{display:block;margin-top:14px;padding:9px 10px;border:1px solid var(--accent);color:var(--accent);border-radius:4px;font-weight:600;text-align:center}
main{min-width:0;background:var(--paper);border:1px solid var(--line);border-radius:6px;padding:28px clamp(16px,4vw,48px)}
h1{font:600 clamp(24px,3.2vw,32px)/1.2 var(--f-head);margin:0 0 16px;text-wrap:balance}
h2{font:600 22px/1.25 var(--f-head);margin:44px 0 12px;padding-top:12px;border-top:2px solid var(--ink);text-wrap:balance}
h3{font:600 17px/1.3 var(--f-head);margin:28px 0 8px;color:var(--accent)}
h4{font:600 15px var(--f-text);margin:20px 0 6px}
p,li{max-width:78ch}
a{color:var(--accent)}
code{font:13px var(--f-mono);background:var(--tint);padding:1px 5px;border-radius:3px}
pre{background:var(--tint);padding:12px 14px;border-radius:4px;overflow-x:auto}
pre code{background:none;padding:0}
hr{border:0;border-top:1px solid var(--line);margin:28px 0}
.tw{overflow-x:auto;margin:12px 0 18px;border:1px solid var(--line);border-radius:4px}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}
th{background:var(--tint);text-align:left;font-weight:600;font-size:12.5px;letter-spacing:.01em}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:last-child td{border-bottom:0}
aside.nota{border-left:3px solid var(--accent);background:var(--tint);padding:10px 14px;margin:16px 0;font-size:14px;max-width:none}
strong{font-weight:600}
.selo{display:inline-block;font:600 11px var(--f-mono);letter-spacing:.06em;color:var(--warn);border:1px solid var(--warn);padding:3px 8px;border-radius:3px;margin-bottom:14px}
.galeria figure{margin:18px 0 26px}
.folha{background:#fff;border:1px solid var(--line);border-radius:4px;overflow-x:auto}
.folha svg{display:block;width:100%;min-width:720px;height:auto}
figcaption{font-size:13px;color:var(--muted);margin-top:6px}
.leg{font-size:13.5px;color:var(--muted)}
.abrir3d{display:flex;flex-wrap:wrap;gap:12px;align-items:center;border:1px solid var(--line);background:var(--tint);padding:14px 16px;border-radius:6px;margin:16px 0}
.abrir3d a{font-weight:600}
@media (max-width:900px){.wrap{grid-template-columns:1fr}nav.toc{position:static;max-height:none}}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
"""

FONTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
          '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&'
          'family=IBM+Plex+Sans+Condensed:wght@600&family=IBM+Plex+Sans:wght@400;600&display=swap">')


def corpo():
    h, toc = md2html(MD)
    bloco3d = ('<div class="abrir3d"><span>Modelo 3D interativo: camadas por disciplina, cor por status do dado, '
               'identificação de componentes e interferências.</span>'
               '<a href="visualizador_3d.html" target="_blank" rel="noopener">Abrir o visualizador 3D</a></div>')
    h = h.replace('<h3 id="133-interferências">', bloco3d + '<h3 id="133-interferências">', 1)
    m = re.search(r'<h2 id="14-', h)
    h = h[:m.start()] + galeria() + h[m.start():]
    h = h.replace("<h1", '<span class="selo">ESTUDO PRELIMINAR — NÃO VÁLIDO PARA CONSTRUÇÃO</span>\n<h1', 1)
    nav = ['<nav class="toc" aria-label="Índice"><h2>Índice</h2><ol>']
    for sid, txt in toc:
        nav.append(f'<li><a href="#{sid}">{html.escape(txt)}</a></li>')
        if txt.startswith("13."):
            nav.append('<li><a href="#desenhos">13.4 Desenhos (7 folhas)</a></li>')
    nav.append('</ol><a class="cta" href="visualizador_3d.html" target="_blank" rel="noopener">Visualizador 3D</a></nav>')
    return '<div class="wrap">' + "".join(nav) + f"<main>{h}</main></div>"


def main():
    titulo = "<title>Estudo Captação e Caixa 50 m³</title>"
    meta = '<meta name="claude:viewport-fit-sides" content="cover">'
    conteudo = f"{titulo}\n{meta}\n{FONTES}\n<style>{CSS}</style>\n{corpo()}"
    full = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
            f'{titulo}{FONTES}<style>{CSS}</style></head><body>{corpo()}</body></html>')
    full = full.replace('href="visualizador_3d.html"', 'href="modelo3d/saida/visualizador_3d.html"')
    open(os.path.join(AQUI, "estudo_tecnico.html"), "w", encoding="utf-8").write(full)
    os.makedirs(os.path.join(AQUI, "artifact"), exist_ok=True)
    open(os.path.join(AQUI, "artifact", "index.html"), "w", encoding="utf-8").write(conteudo)
    shutil.copy(os.path.join(AQUI, "modelo3d", "saida", "visualizador_3d.html"), os.path.join(AQUI, "artifact", "visualizador_3d.html"))
    print("ok", len(full) // 1024, "kB")


if __name__ == "__main__":
    main()
