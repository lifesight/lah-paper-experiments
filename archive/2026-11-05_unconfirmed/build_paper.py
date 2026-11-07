"""Markdown (paper flavour) -> academic HTML; two outputs: artifact fragment and printable document.

Usage: build_paper.py <in.md> <out_artifact.html> <out_print.html>
Front matter: the first lines up to a line '---' hold `key: value` pairs (title, authors, affiliation, date,
keywords). The '## Abstract' section is rendered as the abstract box. Supports h2-h4, paragraphs, pipe tables,
lists, fenced code, raw HTML passthrough (lines starting with <figure, <svg, <div, until the closing tag),
inline code, bold, italics, links, and $...$ / $$...$$ math left for KaTeX.
"""
import html
import re
import sys

src, out_art, out_print = sys.argv[1:4]
text = open(src, encoding="utf-8").read()
fm, body = text.split("\n---\n", 1)
meta = {}
for line in fm.splitlines():
    if ":" in line:
        k, v = line.split(":", 1)
        meta[k.strip().lower()] = v.strip()
lines = body.splitlines()


def latex_to_html(tex, display=False):
    t = tex
    t = re.sub(r"\\(?:mathrm|text|operatorname)\{([^}]*)\}", r"\1", t)
    t = t.replace("\\quad", " ").replace("\\,", " ")
    t = t.replace("\\log_{10}", "log\u2081\u2080").replace("\\log", "log")
    t = t.replace("\\tfrac{1}{2}", "½").replace("\\frac{1}{2}", "½")
    syms = {"\\le": "≤", "\\ge": "≥", "\\in": "∈", "\\subseteq": "⊆", "\\ldots": "…", "\\pm": "±",
            "\\cdot": "·", "\\beta": "β", "\\approx": "≈", "\\sum": "∑", "\\qquad": "\u2003\u2003", "\\quad": "\u2003", "\\tau": "τ", "\\ell": "ℓ", "\\sigma": "σ", "\\lfloor": "⌊", "\\rfloor": "⌋",
            "\\{": "{", "\\}": "}", "\\times": "×", "\\infty": "∞", "\\to": "→"}
    for k, v in syms.items():
        t = t.replace(k, v)
    t = re.sub(r"\\bar\s*([A-Za-z])", lambda m: m.group(1) + "\u0304", t)
    t = t.replace("\\_", "\x01")
    t = html.escape(t, quote=False)
    # subscripts and superscripts
    t = re.sub(r"_\{([^}]*)\}", r"<sub>\1</sub>", t)
    t = re.sub(r"\^\{([^}]*)\}", r"<sup>\1</sup>", t)
    t = re.sub(r"_([^\s{<])", r"<sub>\1</sub>", t)
    t = re.sub(r"\^([A-Za-z0-9])", r"<sup>\1</sup>", t)
    # italicise single-letter variables (not inside tags)
    t = re.sub(r"(?<![A-Za-z<>/])([A-Za-z])(?![A-Za-z>])", r"<i>\1</i>", t)
    t = t.replace("\x01", "_")
    cls = "math-display" if display else "math"
    return f'<span class="{cls}">{t}</span>'


def protect_math(s):
    spans = []
    def keep_display(m):
        spans.append(latex_to_html(m.group(1).strip(), display=True)); return f"\x00{len(spans)-1}\x00"
    def keep_inline(m):
        spans.append(latex_to_html(m.group(1).strip())); return f"\x00{len(spans)-1}\x00"
    s = re.sub(r"\$\$(.+?)\$\$", keep_display, s, flags=re.S)
    s = re.sub(r"\$([^$\n]+?)\$", keep_inline, s)
    return s, spans


def inline(s):
    s, spans = protect_math(s)
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], s)
    return s


out, toc, i, n = [], [], 0, len(lines)
abstract = []
in_abstract = False
while i < n:
    line = lines[i]
    if not line.strip():
        i += 1; continue
    if re.match(r"^<(figure|svg|div)\b", line):
        tag = re.match(r"^<(\w+)", line).group(1)
        block = []
        while i < n:
            block.append(lines[i])
            if re.search(rf"</{tag}>\s*$", lines[i]):
                i += 1; break
            i += 1
        out.append("\n".join(block)); continue
    if line.startswith("```"):
        code = []; i += 1
        while i < n and not lines[i].startswith("```"):
            code.append(lines[i]); i += 1
        i += 1
        out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>"); continue
    m = re.match(r"^(#{2,4}) (.+)$", line)
    if m:
        level, t = len(m.group(1)), m.group(2).strip()
        if level == 2 and t.lower() == "abstract":
            in_abstract = True; i += 1; continue
        if in_abstract and level == 2:
            in_abstract = False
        sid = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
        if level == 2:
            toc.append((t, sid))
        out.append(f'<h{level} id="{sid}">{inline(t)}</h{level}>'); i += 1; continue
    if line.strip() == "---":
        out.append("<hr>"); i += 1; continue
    if line.startswith("|"):
        rows = []
        while i < n and lines[i].startswith("|"):
            rows.append(lines[i]); i += 1
        cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
        head = cells[0]
        bodyrows = [r for r in cells[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
        t = ['<div class="tablewrap"><table><thead><tr>'] + [f"<th>{inline(c)}</th>" for c in head] + ["</tr></thead><tbody>"]
        for r in bodyrows:
            t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
        t.append("</tbody></table></div>")
        out.append("".join(t)); continue
    if re.match(r"^- ", line):
        items = []
        while i < n and re.match(r"^- ", lines[i]):
            items.append(lines[i][2:]); i += 1
        out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>"); continue
    if re.match(r"^\d+\. ", line):
        items = []
        while i < n and re.match(r"^\d+\. ", lines[i]):
            items.append(re.sub(r"^\d+\. ", "", lines[i])); i += 1
        start = re.match(r"^(\d+)\. ", line).group(1)
        out.append(f'<ol start="{start}">' + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>"); continue
    para = []
    while i < n and lines[i].strip() and not re.match(r"^(#{2,4} |\||- |\d+\. |---$|```|<(figure|svg|div)\b)", lines[i]):
        para.append(lines[i].strip()); i += 1
    t = " ".join(para)
    if in_abstract:
        abstract.append(inline(t)); continue
    cls = ' class="caption"' if re.match(r"^(Table|Figure) \d+\.", t) else ""
    out.append(f"<p{cls}>{inline(t)}</p>")

body_html = "\n".join(out)
abstract_html = "".join(f"<p>{a}</p>" for a in abstract)
title = meta.get("title", "Paper")
authors = meta.get("authors", "")
affil = meta.get("affiliation", "")
date = meta.get("date", "")
keywords = meta.get("keywords", "")
toc_html = "".join(f'<li><a href="#{sid}">{html.escape(t)}</a></li>' for t, sid in toc)

css = """
:root { --bg:#f6f7f9; --paper:#ffffff; --fg:#111418; --muted:#5b6572; --line:#d6dce4; --accent:#0f4c81; --code-bg:#eef1f5;
  --serif:"Source Serif 4", Georgia, "Times New Roman", serif; --sans:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif; --mono:"IBM Plex Mono",Menlo,Consolas,monospace; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#111720; --paper:#171e29; --fg:#e4e9f0; --muted:#9aa6b5; --line:#2a3443; --accent:#8ab4dd; --code-bg:#212b38; color-scheme:dark; } }
:root[data-theme="dark"] { --bg:#111720; --paper:#171e29; --fg:#e4e9f0; --muted:#9aa6b5; --line:#2a3443; --accent:#8ab4dd; --code-bg:#212b38; color-scheme:dark; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font-family:var(--serif); font-size:16.5px; line-height:1.55;
  padding-left:max(16px, env(safe-area-inset-left,0px)); padding-right:max(16px, env(safe-area-inset-right,0px)); }
.sheet { max-width: 860px; margin: 0 auto; padding: 40px 0 64px; }
header.title { text-align:center; margin-bottom: 28px; }
header.title p { text-align:center; }
header.title h1 { font-size: clamp(24px, 3.4vw, 32px); line-height:1.2; margin:0 0 12px; font-weight:700; text-wrap:balance; }
.authors { font-size:16px; margin:0 0 4px; }
.affil { color:var(--muted); font-size:14px; margin:0; }
.date { color:var(--muted); font-size:14px; margin:6px 0 0; }
.abstract { margin: 0 auto 22px; max-width: 760px; border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding: 14px 8px; font-size:15.5px; }
.abstract h2 { font-family:var(--sans); font-size:13px; letter-spacing:.12em; text-transform:uppercase; text-align:center; margin:0 0 8px; border:0; padding:0; }
.abstract p { margin:0 0 10px; text-align:justify; hyphens:auto; }
.keywords { font-family:var(--sans); font-size:13px; color:var(--muted); margin-top: 8px; }
nav.toc { font-family:var(--sans); font-size:13px; border:1px solid var(--line); border-radius:6px; padding:10px 14px; margin:0 0 28px; background:var(--paper); }
nav.toc b { display:block; margin-bottom:4px; letter-spacing:.08em; text-transform:uppercase; font-size:12px; color:var(--muted); }
nav.toc ul { margin:0; padding:0; list-style:none; columns: 2; column-gap: 24px; }
nav.toc li { break-inside: avoid; margin: 2px 0; }
nav.toc a { color:inherit; text-decoration:none; }
nav.toc a:hover { color:var(--accent); text-decoration:underline; }
h2 { font-size:21px; margin: 34px 0 10px; line-height:1.25; }
h3 { font-size:17.5px; margin: 24px 0 8px; }
h4 { font-family:var(--sans); font-size:15px; margin: 18px 0 6px; }
p { margin: 0 0 12px; text-align: justify; hyphens: auto; }
p.caption { font-family:var(--sans); font-size:13.5px; color:var(--muted); text-align:left; margin: 14px 0 6px; }
ul, ol { margin: 0 0 12px; padding-left: 24px; }
li { margin-bottom: 4px; }
code { font-family:var(--mono); font-size:.86em; background:var(--code-bg); padding:1px 4px; border-radius:3px; overflow-wrap:anywhere; }
pre { background:var(--code-bg); border:1px solid var(--line); border-radius:6px; padding:10px 12px; overflow-x:auto; font-family:var(--mono); font-size:12.5px; line-height:1.4; margin:0 0 14px; }
pre code { background:none; padding:0; font-size:inherit; }
.tablewrap { overflow-x:auto; margin: 0 0 16px; }
table { border-collapse: collapse; width:100%; font-family:var(--sans); font-size:13px; line-height:1.4; }
th, td { text-align:left; vertical-align:top; padding: 6px 8px; border-bottom:1px solid var(--line); }
th { border-top: 2px solid var(--fg); border-bottom: 1px solid var(--fg); font-weight:600; }
tbody tr:last-child td { border-bottom: 2px solid var(--fg); }
td { font-variant-numeric: tabular-nums; }
figure { margin: 18px 0 20px; text-align:center; }
figure svg { max-width:100%; height:auto; }
figcaption { font-family:var(--sans); font-size:13.5px; color:var(--muted); text-align:left; margin-top:8px; }
hr { border:0; border-top:1px solid var(--line); margin: 28px 0; }
a { color: var(--accent); }
.math, .math-display { font-family: var(--serif); font-style: normal; white-space: nowrap; }
.math-display { display:block; text-align:center; margin: 8px 0 14px; white-space: normal; }
.math i { font-style: italic; }
@media print {
  @page { size: A4; margin: 20mm 18mm; }
  body { background:#fff; color:#000; font-size:11pt; }
  .sheet { max-width:none; padding:0; }
  nav.toc, .noprint { display:none; }
  h2 { break-after: avoid; } figure, table, pre { break-inside: avoid; }
  a { color:#000; text-decoration:none; }
}
"""

head_common = f"""<title>{html.escape(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}</style>
"""
body_block = f"""<div class="sheet">
<header class="title">
  <h1>{html.escape(title)}</h1>
  <p class="authors">{html.escape(authors)}</p>
  <p class="affil">{html.escape(affil)}</p>
  <p class="date">{html.escape(date)}</p>
</header>
<section class="abstract"><h2>Abstract</h2>{abstract_html}<p class="keywords"><strong>Keywords:</strong> {html.escape(keywords)}</p></section>
<nav class="toc"><b>Contents</b><ul>{toc_html}</ul></nav>
<article>
{body_html}
</article>
</div>
"""
open(out_art, "w", encoding="utf-8").write(head_common + body_block)
open(out_print, "w", encoding="utf-8").write('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">' + head_common + "</head><body>" + body_block + "</body></html>")
print(out_art, len(head_common + body_block), "bytes;", len(toc), "sections;", len(abstract), "abstract paragraphs")
