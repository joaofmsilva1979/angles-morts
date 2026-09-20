"""
gen_book.py — PDF print-ready A5 "Construire une marque qui tient"
Usage: uv run --with playwright python3 gen_book.py
"""

import re, sys
from pathlib import Path
from html import escape

ROOT     = Path.home() / "Library/CloudStorage/GoogleDrive-davisthe8th@gmail.com/My Drive/JOAO/ANGLES_MORTS/angles-morts-web"
MD       = ROOT / "marque-COMPLET.md"
OUT_HTML = Path(__file__).parent / "book.html"
OUT_PDF  = ROOT / "construire-une-marque-qui-tient-v2.pdf"

BX = "#8B1A1A"

# ── Inline markdown ──────────────────────────────────────────────────────────

def md(text: str) -> str:
    text = escape(text)
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'(?<!href=")(https?://[^\s<>"\']+)', r'<a href="\1">\1</a>', text)
    return text

CH_RE = re.compile(r'^## Chapitre (\d+)\s*[:—–-]+\s*(.+)')
H3_RE = re.compile(r'^### (.+)')
H2_RE = re.compile(r'^## (.+)')
Q_RE  = re.compile(r'^###\s*4 questions', re.I)

# ── Parser ───────────────────────────────────────────────────────────────────

def parse(text: str) -> dict:
    lines = text.splitlines()
    result = {'title':'','subtitle':'','author':'','intro':[],'chapters':[],'conclusion':[],'resources':[]}
    state = 'preamble'
    cur = None
    sec = []
    in_q = False

    def flush():
        nonlocal sec, in_q
        if cur is None: return
        block = '\n'.join(sec).strip()
        if not block: sec=[]; return
        if in_q:
            cur['questions_raw'] = block
        else:
            cur['body_parts'].append(block)
        sec=[]; in_q=False

    def flush_intro():
        nonlocal sec
        b = '\n'.join(sec).strip()
        if b: result['intro'].append(b)
        sec=[]

    i=0
    while i < len(lines):
        line = lines[i]
        if line.startswith('# ') and state=='preamble':
            result['title']=line[2:].strip(); i+=1; continue
        if state=='preamble' and line.startswith('## Guide'):
            result['subtitle']=line[3:].strip(); i+=1; continue
        if state=='preamble' and line.startswith('*João'):
            result['author']=line.strip('*').strip(); i+=1; continue
        if line.startswith('### À qui s'):
            state='intro'; i+=1; continue

        m2 = CH_RE.match(line)
        if m2:
            if state=='intro': flush_intro()
            elif state=='chapter': flush()
            cur={'num':int(m2.group(1)),'title':m2.group(2).strip(),'tagline':'','body_parts':[],'questions_raw':''}
            result['chapters'].append(cur)
            state='chapter'; in_q=False; sec=[]; i+=1; continue

        if state=='chapter' and line.startswith('> ') and not cur.get('tagline') and not sec:
            cur['tagline']=line[2:].strip(); i+=1; continue

        m3=H2_RE.match(line)
        if m3 and state=='chapter':
            flush()
            h=m3.group(1).strip()
            if any(k in h for k in ('Conclusion','gouvernance','Pour aller')):
                state='conclusion'; result['conclusion'].append({'type':'h2','text':h})
            elif any(k in h for k in ('Sources','Ressources','Bibliographie','Série Substack')):
                state='resources'; result['resources'].append({'type':'h2','text':h})
            i+=1; continue

        if state=='chapter' and H3_RE.match(line):
            flush()
            heading=H3_RE.match(line).group(1).strip()
            in_q=bool(Q_RE.match(line))
            sec=[f'<h3>{md(heading)}</h3>'] if not in_q else []
            i+=1; continue

        if state=='intro': sec.append(line); i+=1; continue
        if state=='chapter': sec.append(line); i+=1; continue
        if state=='conclusion':
            if H3_RE.match(line): result['conclusion'].append({'type':'h3','text':H3_RE.match(line).group(1).strip()})
            elif line.strip(): result['conclusion'].append({'type':'p','text':line})
            i+=1; continue
        if state=='resources':
            if H3_RE.match(line): result['resources'].append({'type':'h3','text':H3_RE.match(line).group(1).strip()})
            elif H2_RE.match(line): result['resources'].append({'type':'h2','text':H2_RE.match(line).group(1).strip()})
            elif line.startswith('- '): result['resources'].append({'type':'li','text':line[2:].strip()})
            i+=1; continue
        i+=1

    if state=='chapter': flush()
    elif state=='intro': flush_intro()
    return result

# ── Body renderer ────────────────────────────────────────────────────────────

def render_body(raw: str) -> str:
    out=[]; buf=[]; in_ul=False; in_ol=False
    def flush_buf():
        nonlocal in_ul,in_ol
        if in_ul: out.append('</ul>'); in_ul=False
        if in_ol: out.append('</ol>'); in_ol=False
        if buf:
            t=' '.join(buf).strip()
            if t: out.append(f'<p>{md(t)}</p>')
            buf.clear()
    for line in raw.splitlines():
        s=line.strip()
        if not s: flush_buf(); continue
        if s.startswith('<h3'): flush_buf(); out.append(s); continue
        if s.startswith('> '): flush_buf(); out.append(f'<blockquote class="pull">{md(s[2:])}</blockquote>'); continue
        if s.startswith(('- ','* ')):
            if buf: flush_buf()
            if not in_ul: out.append('<ul>'); in_ul=True
            out.append(f'<li>{md(s[2:])}</li>'); continue
        m=re.match(r'^\d+\.\s+(.*)',s)
        if m:
            if buf: flush_buf()
            if not in_ol: out.append('<ol>'); in_ol=True
            out.append(f'<li>{md(m.group(1))}</li>'); continue
        if s in('---','***'): flush_buf(); out.append('<div class="section-ornament">◆ ◆ ◆</div>'); continue
        if in_ul or in_ol: flush_buf()
        buf.append(s)
    flush_buf()
    return '\n'.join(out)

def render_questions(raw: str) -> str:
    items=[]; buf=[]
    for line in raw.splitlines():
        s=line.strip()
        m=re.match(r'^\d+\.\s+(.*)',s)
        if m:
            if buf and items: items[-1]+=' '+' '.join(buf); buf.clear()
            items.append(m.group(1))
        elif s and s!='---' and items: buf.append(s)
    if buf and items: items[-1]+=' '+' '.join(buf)
    li=''.join(f'<li>{md(it)}</li>' for it in items)
    return f'<div class="qbox"><p class="qbox-label">4 questions pour commencer</p><ol>{li}</ol></div>'

# ── TOC builder ──────────────────────────────────────────────────────────────

def build_toc(data: dict) -> str:
    rows=[]
    rows.append('<li class="toc-intro"><span class="toc-title">Introduction</span><span class="toc-dots"></span></li>')
    for ch in data['chapters']:
        short = ch['title']
        rows.append(f'<li><span class="toc-num">{ch["num"]:02d}</span><span class="toc-title">{escape(short)}</span><span class="toc-dots"></span></li>')
    if data['conclusion']:
        rows.append('<li class="toc-intro"><span class="toc-title">Conclusion</span><span class="toc-dots"></span></li>')
    if data['resources']:
        rows.append('<li class="toc-intro"><span class="toc-title">Sources &amp; Ressources</span><span class="toc-dots"></span></li>')
    return '<ul class="toc-list">'+''.join(rows)+'</ul>'

# ── HTML builder ─────────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@400;500;600&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

:root{
  --bx:#8B1A1A;
  --ink:#111;
  --gray:#555;
  --rule:#D8D4CE;
  --cream:#FAFAF8;
}

/* ── PAGE SETUP ── */
@page{
  size:148mm 210mm;
  margin:22mm 16mm 24mm 20mm;
}
@page:left{margin-left:16mm;margin-right:20mm}
@page:right{margin-left:20mm;margin-right:16mm}

html,body{
  font-family:'Cormorant Garamond',Georgia,serif;
  font-size:11.5pt;
  line-height:1.82;
  color:var(--ink);
  background:#fff;
  -webkit-print-color-adjust:exact;
  print-color-adjust:exact;
}

a{color:inherit;text-decoration:none}

/* ── PAGES ── */
.page{
  page-break-after:always;
  min-height:162mm; /* 210 - 22 - 24 = 164 available */
  display:flex;
  flex-direction:column;
}
.page-break{page-break-before:always}

/* ── HALF TITLE ── */
.half-title{
  justify-content:center;
  align-items:center;
  text-align:center;
}
.half-title h2{
  font-family:'Playfair Display',serif;
  font-size:18pt;font-weight:400;
  color:var(--ink);letter-spacing:.02em;
}

/* ── TITLE PAGE ── */
.title-page{justify-content:flex-end;padding-bottom:8mm}
.title-series{
  font-family:'Inter',sans-serif;
  font-size:8pt;font-weight:600;
  letter-spacing:.16em;text-transform:uppercase;
  color:var(--bx);margin-bottom:10mm;
}
.title-main{
  font-family:'Playfair Display',serif;
  font-size:34pt;font-weight:700;
  line-height:1.05;color:var(--ink);
  letter-spacing:-.02em;margin-bottom:6mm;
}
.title-sub{
  font-family:'Cormorant Garamond',serif;
  font-size:13pt;font-style:italic;color:var(--gray);
  margin-bottom:16mm;
}
.title-author{
  font-family:'Playfair Display',serif;
  font-size:13pt;font-weight:600;color:var(--ink);
  padding-top:6mm;border-top:1pt solid var(--rule);
}
.title-author small{
  display:block;
  font-family:'Inter',sans-serif;
  font-size:8pt;font-weight:400;letter-spacing:.06em;
  text-transform:uppercase;color:var(--gray);
  margin-bottom:2mm;
}

/* ── COPYRIGHT ── */
.copyright-page{
  justify-content:flex-end;
  padding-bottom:4mm;
}
.copyright-page p{
  font-family:'Inter',sans-serif;
  font-size:8pt;color:var(--gray);
  line-height:1.6;margin-bottom:2mm;
}

/* ── TOC ── */
.toc-page h2{
  font-family:'Playfair Display',serif;
  font-size:20pt;font-weight:700;
  margin-bottom:10mm;color:var(--ink);
}
.toc-list{list-style:none;padding:0}
.toc-list li{
  display:flex;align-items:baseline;
  padding:3pt 0;
  border-bottom:0.5pt dotted var(--rule);
  font-size:10.5pt;
}
.toc-intro .toc-title{font-style:italic;color:var(--gray)}
.toc-num{
  font-family:'Playfair Display',serif;
  font-size:11pt;font-weight:600;color:var(--bx);
  width:8mm;flex-shrink:0;
}
.toc-title{flex:1;padding:0 3mm}
.toc-dots{
  font-family:'Inter',sans-serif;
  font-size:7pt;color:var(--rule);
  letter-spacing:2pt;
  content:'· · · · · · · · · ·';
  flex-shrink:0;
}

/* ── INTRO HEADING ── */
.intro-heading{
  font-family:'Playfair Display',serif;
  font-size:18pt;font-weight:700;
  color:var(--ink);margin-bottom:8mm;
}

/* ── CHAPTER OPENER (page entière dédiée) ── */
.chapter{page-break-before:always}
.ch-opener{
  page-break-before:always;
  page-break-after:always;
  min-height:162mm;
  display:flex;flex-direction:column;
  justify-content:flex-end;
  padding-bottom:12mm;
  position:relative;
}
.ch-ghost-num{
  position:absolute;
  top:-8mm;right:-4mm;
  font-family:'Playfair Display',serif;
  font-size:160pt;font-weight:700;
  color:rgba(139,26,26,.05);
  line-height:1;letter-spacing:-.04em;
}
.ch-label{
  font-family:'Inter',sans-serif;
  font-size:7pt;font-weight:600;
  letter-spacing:.18em;text-transform:uppercase;
  color:var(--bx);margin-bottom:5mm;
}
.ch-title{
  font-family:'Playfair Display',serif;
  font-size:26pt;font-weight:700;
  line-height:1.1;color:var(--ink);
  letter-spacing:-.02em;margin-bottom:7mm;
}
.ch-tagline{
  font-family:'Cormorant Garamond',serif;
  font-size:12.5pt;font-style:italic;color:var(--gray);
  line-height:1.6;
  padding-top:5mm;
  border-top:0.5pt solid var(--rule);
}

/* ── BODY ── */
.ch-body p{
  margin-bottom:0;
  margin-top:0;
  text-align:justify;
  hyphens:auto;
  line-height:1.85;
}
.ch-body p+p{text-indent:5mm}
.ch-body p:first-child::first-letter{
  font-family:'Playfair Display',serif;
  font-size:42pt;font-weight:700;
  float:left;line-height:.78;
  margin:4pt 4pt -4pt 0;
  color:var(--bx);
}
.ch-body h3{
  font-family:'Playfair Display',serif;
  font-size:12.5pt;font-weight:700;
  color:var(--ink);
  margin-top:9mm;margin-bottom:3mm;
  line-height:1.25;
  padding-bottom:1.5mm;
  border-bottom:0.5pt solid var(--rule);
}
.ch-body strong{font-weight:600}
.ch-body em{font-style:italic}
.ch-body ul,.ch-body ol{
  padding-left:6mm;margin:3mm 0 3mm;
}
.ch-body li{
  margin-bottom:1.5mm;text-align:left;
  line-height:1.65;
}
.pull{
  margin:9mm 0;
  padding:5mm 0;
  border-top:1pt solid var(--bx);
  border-bottom:1pt solid var(--bx);
  text-align:center;
  font-family:'Cormorant Garamond',serif;
  font-size:13pt;font-style:italic;
  color:var(--ink);line-height:1.55;
}
.section-ornament{
  text-align:center;
  color:var(--bx);
  font-size:9pt;
  margin:7mm 0;
  letter-spacing:.4em;
}

/* ── 4 QUESTIONS ── */
.qbox{
  background:#F7F4F1;
  border-left:3pt solid var(--bx);
  padding:5mm 6mm 5mm 7mm;
  margin-top:9mm;
  page-break-inside:avoid;
}
.qbox-label{
  font-family:'Inter',sans-serif;
  font-size:7pt;font-weight:600;
  letter-spacing:.12em;text-transform:uppercase;
  color:var(--bx);margin-bottom:3.5mm;
}
.qbox ol{padding-left:5mm;margin:0}
.qbox li{
  font-size:10.5pt;margin-bottom:2.5mm;
  line-height:1.6;text-align:left;
  color:#222;
}

/* ── CONCLUSION ── */
.conclusion h2{
  font-family:'Playfair Display',serif;
  font-size:22pt;font-weight:700;
  color:var(--ink);margin-bottom:8mm;
}
.conclusion h3{
  font-family:'Playfair Display',serif;
  font-size:13pt;font-weight:600;
  margin-top:6mm;margin-bottom:3mm;
}
.conclusion p{margin-bottom:4mm;text-align:justify;hyphens:auto}
.conclusion a{color:var(--bx)}

/* ── RESOURCES ── */
.resources h2{
  font-family:'Playfair Display',serif;
  font-size:18pt;font-weight:700;
  color:var(--ink);margin-bottom:7mm;
}
.resources h3{
  font-family:'Inter',sans-serif;
  font-size:7.5pt;font-weight:600;
  letter-spacing:.1em;text-transform:uppercase;
  color:var(--bx);
  margin-top:6mm;margin-bottom:2mm;
  padding-bottom:1.5mm;
  border-bottom:0.5pt solid var(--rule);
}
.resources ul{padding-left:4mm;margin-bottom:3mm}
.resources li{font-size:9.5pt;color:var(--gray);margin-bottom:1.5mm;line-height:1.5}
.resources a{color:var(--bx)}

/* ── AUTHOR PAGE ── */
.author-page{justify-content:center}
.author-page h2{
  font-family:'Playfair Display',serif;
  font-size:18pt;font-weight:700;margin-bottom:6mm;
}
.author-page p{
  font-size:10.5pt;color:var(--gray);
  line-height:1.75;margin-bottom:3mm;
}
.author-rule{
  border:none;border-top:0.5pt solid var(--rule);
  margin:6mm 0;
}

/* ── PRINT ONLY ── */
@media screen{
  body{max-width:148mm;margin:0 auto;padding:22mm 20mm 24mm;background:#eee}
  .page{background:#fff;margin-bottom:10mm;padding:22mm 20mm 24mm;box-shadow:0 2px 8px rgba(0,0,0,.15)}
  .chapter{margin-bottom:10mm}
}
"""

def build_html(data: dict) -> str:
    parts = []

    parts.append(f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{escape(data['title'])}</title>
<style>{CSS}</style>
</head>
<body>""")

    # ── HALF TITLE ──
    parts.append(f"""
<div class="page half-title">
  <h2>{escape(data['title'])}</h2>
</div>""")

    # ── TITLE PAGE ──
    parts.append(f"""
<div class="page title-page">
  <div class="title-series">Angles Morts</div>
  <h1 class="title-main">{escape(data['title'])}</h1>
  <p class="title-sub">{escape(data['subtitle'])}</p>
  <div class="title-author">
    <small>Auteur</small>
    João Silva
  </div>
</div>""")

    # ── COPYRIGHT ──
    parts.append("""
<div class="page copyright-page">
  <p>© João Silva, 2026</p>
  <p>Tous droits réservés.</p>
  <p style="margin-top:4mm">Série publiée sur LinkedIn et Substack entre mai et août 2026.</p>
  <p>joaosilva1979.substack.com</p>
  <p style="margin-top:4mm;font-style:italic">
    Ce guide a été rédigé depuis l'intérieur d'une organisation ;<br>
    pas depuis un cabinet conseil.
  </p>
</div>""")

    # ── TABLE DES MATIÈRES ──
    parts.append(f"""
<div class="page toc-page">
  <h2>Table des matières</h2>
  {build_toc(data)}
</div>""")

    # ── INTRODUCTION ──
    parts.append('<div class="page-break"><h2 class="intro-heading">À qui s\'adresse ce guide</h2><div class="ch-body">')
    for block in data['intro']:
        parts.append(render_body(block))
    parts.append('</div></div>')

    # ── CHAPTERS ──
    for ch in data['chapters']:
        num_str = f"{ch['num']:02d}"
        # Opener page — full page dedicated to chapter
        parts.append(f'<div class="ch-opener" id="ch{ch["num"]}">')
        parts.append(f'<div class="ch-ghost-num">{num_str}</div>')
        parts.append(f'<div class="ch-label">Chapitre {ch["num"]}</div>')
        parts.append(f'<h2 class="ch-title">{md(ch["title"])}</h2>')
        if ch['tagline']:
            parts.append(f'<blockquote class="ch-tagline">{md(ch["tagline"])}</blockquote>')
        parts.append('</div>')
        # Body — continues on next page
        parts.append('<div class="ch-body">')
        for block in ch['body_parts']:
            parts.append(render_body(block))
        parts.append('</div>')
        if ch['questions_raw']:
            parts.append(render_questions(ch['questions_raw']))

    # ── CONCLUSION ──
    if data['conclusion']:
        parts.append('<div class="chapter conclusion">')
        for item in data['conclusion']:
            if item['type']=='h2': parts.append(f'<h2>{md(item["text"])}</h2>')
            elif item['type']=='h3': parts.append(f'<h3>{md(item["text"])}</h3>')
            elif item['type']=='p':
                t=item['text'].strip()
                if t and t!='---': parts.append(f'<p>{md(t)}</p>')
        parts.append('</div>')

    # ── AUTHOR PAGE ──
    parts.append("""
<div class="chapter author-page">
  <div>
    <h2>João Silva</h2>
    <hr class="author-rule">
    <p>J'écris depuis l'intérieur d'une organisation ; pas depuis un cabinet conseil.</p>
    <p>Marketing &amp; digital au Luxembourg. La question n'est pas <em>comment tu communiques</em>. Elle est <em>qui décide, qui fait vivre, qui répond quand ça craque.</em></p>
    <hr class="author-rule">
    <p><strong>Newsletter</strong> : joaosilva1979.substack.com</p>
    <p><strong>LinkedIn</strong> : <a href="https://www.linkedin.com/in/joaosilva-commarketeer/">linkedin.com/in/joaosilva-commarketeer</a></p>
    <p><strong>Site</strong> : <a href="https://joaofmsilva1979.github.io/angles-morts/">joaofmsilva1979.github.io/angles-morts</a></p>
  </div>
</div>""")

    # ── RESOURCES ──
    if data['resources']:
        parts.append('<div class="chapter resources">')
        in_ul=False
        for item in data['resources']:
            if item['type'] in('h2','h3'):
                if in_ul: parts.append('</ul>'); in_ul=False
                parts.append(f'<{item["type"]}>{md(item["text"])}</{item["type"]}>')
            elif item['type'] in('li','li_sub'):
                if not in_ul: parts.append('<ul>'); in_ul=True
                parts.append(f'<li>{md(item["text"])}</li>')
        if in_ul: parts.append('</ul>')
        parts.append('</div>')

    parts.append('</body></html>')
    return '\n'.join(parts)

# ── PDF via Playwright ────────────────────────────────────────────────────────

def to_pdf(html_path: Path, pdf_path: Path):
    from playwright.sync_api import sync_playwright
    print("  Lancement Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f'file://{html_path}', wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(2000)   # laisse les fonts Google charger
        page.pdf(
            path=str(pdf_path),
            format='A5',
            print_background=True,
            margin={'top':'22mm','bottom':'24mm','left':'20mm','right':'16mm'},
            display_header_footer=True,
            header_template="""
              <div style="width:100%;font-size:6.5pt;color:#bbb;
                font-family:Georgia,serif;letter-spacing:.06em;
                display:flex;justify-content:space-between;
                padding:0 20mm;margin-bottom:3mm;">
                <span>João Silva</span>
                <span style="font-style:italic">Construire une marque qui tient</span>
              </div>""",
            footer_template="""
              <div style="width:100%;font-size:7pt;color:#999;
                font-family:'Cormorant Garamond',Georgia,serif;
                display:flex;justify-content:space-between;
                padding:0 20mm 0 20mm;margin-top:2mm;">
                <span>Angles Morts</span>
                <span class="pageNumber"></span>
              </div>""",
        )
        browser.close()

# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if not MD.exists():
        print(f"Source introuvable : {MD}", file=sys.stderr); sys.exit(1)

    print("Parsing COMPLET.md...")
    data = parse(MD.read_text(encoding='utf-8'))
    print(f"  {len(data['chapters'])} chapitres trouvés")

    print("Génération book.html...")
    html = build_html(data)
    OUT_HTML.write_text(html, encoding='utf-8')
    print(f"  {OUT_HTML}  ({len(html):,} chars)")

    print("Export PDF A5...")
    to_pdf(OUT_HTML.resolve(), OUT_PDF)
    print(f"\n✓ {OUT_PDF}")
