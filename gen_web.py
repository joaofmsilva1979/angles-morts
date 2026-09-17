"""
gen_web.py — génère index.html (hub) + marque.html (guide 13 chapitres)
Usage: uv run python gen_web.py
"""

import re
import sys
from pathlib import Path
from html import escape

SRC = Path.home() / "Library/CloudStorage/GoogleDrive-davisthe8th@gmail.com/My Drive/JOAO/ANGLES_MORTS/LinkedIn/SEMAINE/Construire-une-marque-qui-tient/TOUT/construire-une-marque-qui-tient-COMPLET.md"
OUT_HUB   = Path(__file__).parent / "index.html"
OUT_GUIDE = Path(__file__).parent / "marque.html"

BORDEAUX = "#8B1A1A"
GRAY = "#6B6B6B"

# ─────────────────────────────────────────────────────────────────────────────
# SHARED CSS
# ─────────────────────────────────────────────────────────────────────────────

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">"""

BASE_CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bx:#8B1A1A;
  --bx2:#B8432F;
  --gray:#6B6B6B;
  --gray2:#9A9A9A;
  --ink:#1A1A1A;
  --bg:#FAFAF8;
  --rule:#E5E5E0;
}
html{scroll-behavior:smooth}
body{font-family:'Inter',sans-serif;color:var(--ink);background:var(--bg)}
a{color:inherit;text-decoration:none}
"""

# ─────────────────────────────────────────────────────────────────────────────
# INLINE MARKDOWN
# ─────────────────────────────────────────────────────────────────────────────

def inline_md(text: str) -> str:
    text = escape(text)
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = re.sub(r'(?<!href=")(https?://[^\s<>"\']+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', text)
    return text

CH_RE   = re.compile(r'^## Chapitre (\d+)\s*[:—–-]+\s*(.+)')
H3_RE   = re.compile(r'^### (.+)')
H2_RE   = re.compile(r'^## (.+)')
Q_RE    = re.compile(r'^###\s*4 questions', re.I)

# ─────────────────────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────────────────────

def parse(md: str) -> dict:
    lines = md.splitlines()
    result = {'title':'','subtitle':'','author':'','intro':[],'chapters':[],'conclusion':[],'resources':[]}
    state = 'preamble'
    cur = None
    sec_lines = []
    in_q = False

    def flush_sec():
        nonlocal sec_lines, in_q
        if cur is None: return
        block = '\n'.join(sec_lines).strip()
        if not block: sec_lines=[]; return
        if in_q: cur['questions_raw'] = block
        else: cur['body_parts'].append(block)
        sec_lines=[]; in_q=False

    def flush_intro():
        nonlocal sec_lines
        block = '\n'.join(sec_lines).strip()
        if block: result['intro'].append(block)
        sec_lines=[]

    i,n = 0,len(lines)
    while i < n:
        line = lines[i]

        if line.startswith('# ') and state=='preamble':
            result['title'] = line[2:].strip(); i+=1; continue
        if state=='preamble' and line.startswith('## Guide'):
            result['subtitle'] = line[3:].strip(); i+=1; continue
        if state=='preamble' and line.startswith('*João'):
            result['author'] = line.strip('*').strip(); i+=1; continue
        if line.startswith('### À qui s'):
            state='intro'; i+=1; continue

        m = CH_RE.match(line)
        if m:
            if state=='intro': flush_intro()
            elif state=='chapter': flush_sec()
            cur = {'num':int(m.group(1)),'title':m.group(2).strip(),'tagline':'','body_parts':[],'questions_raw':''}
            result['chapters'].append(cur)
            state='chapter'; in_q=False; sec_lines=[]; i+=1; continue

        if state=='chapter' and line.startswith('> ') and not cur.get('tagline') and not sec_lines:
            cur['tagline'] = line[2:].strip(); i+=1; continue

        m2 = H2_RE.match(line)
        if m2 and state=='chapter':
            flush_sec()
            h = m2.group(1).strip()
            if any(k in h for k in ('Conclusion','gouvernance','Pour aller')):
                state='conclusion'; result['conclusion'].append({'type':'h2','text':h})
            elif any(k in h for k in ('Sources','Ressources','Bibliographie','Série Substack')):
                state='resources'; result['resources'].append({'type':'h2','text':h})
            i+=1; continue

        if state=='chapter' and H3_RE.match(line):
            flush_sec()
            h3m = H3_RE.match(line)
            heading = h3m.group(1).strip()
            in_q = bool(Q_RE.match(line))
            sec_lines = [f'<h3>{inline_md(heading)}</h3>'] if not in_q else []
            i+=1; continue

        if state=='intro': sec_lines.append(line); i+=1; continue
        if state=='chapter': sec_lines.append(line); i+=1; continue

        if state=='conclusion':
            if H3_RE.match(line): result['conclusion'].append({'type':'h3','text':H3_RE.match(line).group(1).strip()})
            elif line.strip(): result['conclusion'].append({'type':'p','text':line})
            i+=1; continue

        if state=='resources':
            if H3_RE.match(line): result['resources'].append({'type':'h3','text':H3_RE.match(line).group(1).strip()})
            elif H2_RE.match(line): result['resources'].append({'type':'h2','text':H2_RE.match(line).group(1).strip()})
            elif line.startswith('- '): result['resources'].append({'type':'li','text':line[2:].strip()})
            elif line.startswith('  - '): result['resources'].append({'type':'li_sub','text':line[4:].strip()})
            i+=1; continue
        i+=1

    if state=='chapter': flush_sec()
    elif state=='intro': flush_intro()
    return result

# ─────────────────────────────────────────────────────────────────────────────
# BODY RENDERERS
# ─────────────────────────────────────────────────────────────────────────────

def render_paragraphs(raw: str) -> str:
    out=[]; buf=[]; in_ul=False; in_ol=False
    def flush():
        nonlocal in_ul,in_ol
        if in_ul: out.append('</ul>'); in_ul=False
        if in_ol: out.append('</ol>'); in_ol=False
        if buf:
            t=' '.join(buf).strip()
            if t: out.append(f'<p>{inline_md(t)}</p>')
            buf.clear()
    for line in raw.splitlines():
        s=line.strip()
        if not s: flush(); continue
        if s.startswith('<h3'): flush(); out.append(s); continue
        if s.startswith('> '): flush(); out.append(f'<blockquote class="tl">{inline_md(s[2:])}</blockquote>'); continue
        if s.startswith(('- ','* ')):
            if buf: flush()
            if not in_ul: out.append('<ul>'); in_ul=True
            out.append(f'<li>{inline_md(s[2:])}</li>'); continue
        m=re.match(r'^\d+\.\s+(.*)',s)
        if m:
            if buf: flush()
            if not in_ol: out.append('<ol>'); in_ol=True
            out.append(f'<li>{inline_md(m.group(1))}</li>'); continue
        if s in('---','***','___'): flush(); continue
        if in_ul or in_ol: flush()
        buf.append(s)
    flush()
    return '\n'.join(out)

def render_questions(raw: str) -> str:
    items=[]; buf=[]
    for line in raw.splitlines():
        s=line.strip()
        m=re.match(r'^\d+\.\s+(.*)',s)
        if m:
            if buf and items: items[-1]+=' '+' '.join(buf); buf.clear()
            items.append(m.group(1))
        elif s and s not in('---',) and items: buf.append(s)
    if buf and items: items[-1]+=' '+' '.join(buf)
    li=''.join(f'<li>{inline_md(it)}</li>' for it in items)
    return f'<div class="qbox"><h3>4 questions pour commencer</h3><ol>{li}</ol></div>'

# ─────────────────────────────────────────────────────────────────────────────
# HUB PAGE (index.html)
# ─────────────────────────────────────────────────────────────────────────────

HUB_CSS = BASE_CSS + """
body{font-size:17px;line-height:1.7}
.site-header{
  max-width:860px;margin:0 auto;
  padding:72px 40px 0;
}
.brand{display:flex;align-items:baseline;gap:16px;margin-bottom:32px}
.brand-name{
  font-family:'Cormorant Garamond',serif;
  font-size:48px;font-weight:500;
  color:var(--ink);letter-spacing:-.02em;
}
.brand-by{
  font-size:14px;color:var(--gray2);
  letter-spacing:.04em;
}
.brand-tagline{
  font-family:'Cormorant Garamond',serif;
  font-style:italic;font-size:20px;
  color:var(--gray);line-height:1.4;
  max-width:540px;margin-bottom:60px;
}
.rule{border:none;border-top:1px solid var(--rule);margin:0 0 64px}
/* ── articles list ── */
.articles{max-width:860px;margin:0 auto;padding:0 40px}
.section-label{
  font-size:11px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--bx);font-weight:600;margin-bottom:32px;
}
.article-list{display:flex;flex-direction:column;gap:0}
/* ── article card ── */
.article-card{
  display:grid;
  grid-template-columns:80px 1fr auto;
  gap:0 32px;
  align-items:start;
  padding:32px 0;
  border-bottom:1px solid var(--rule);
  cursor:default;
  transition:background .15s;
  text-decoration:none;
  color:inherit;
}
.article-card:first-child{border-top:1px solid var(--rule)}
.article-card:hover .card-title{color:var(--bx)}
.card-num{
  font-family:'Cormorant Garamond',serif;
  font-size:52px;font-weight:400;
  color:var(--rule);line-height:1;
  letter-spacing:-.02em;
  padding-top:4px;
}
.card-body{min-width:0}
.card-meta{
  font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--gray2);margin-bottom:8px;
}
.card-title{
  font-family:'Cormorant Garamond',serif;
  font-size:28px;font-weight:500;
  line-height:1.2;color:var(--ink);
  margin-bottom:10px;
  transition:color .15s;
}
.card-desc{font-size:15px;color:var(--gray);line-height:1.6;max-width:520px}
.card-status{
  align-self:center;
  white-space:nowrap;
}
.badge{
  display:inline-block;
  font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  font-weight:600;padding:5px 12px;border-radius:2px;
}
.badge-live{background:rgba(139,26,26,.08);color:var(--bx)}
.badge-soon{background:#F0F0EC;color:var(--gray2)}
.card-arrow{
  font-size:20px;color:var(--bx);opacity:0;
  transition:opacity .15s,transform .15s;
  align-self:center;margin-left:12px;
}
.article-card:hover .card-arrow{opacity:1;transform:translateX(4px)}
/* ── coming soon card ── */
.article-card.soon{cursor:default}
.article-card.soon:hover .card-title{color:inherit}
/* ── about ── */
.about{
  max-width:860px;margin:80px auto 0;
  padding:60px 40px;
  border-top:1px solid var(--rule);
  display:grid;grid-template-columns:1fr 1fr;gap:48px;
}
.about-heading{
  font-family:'Cormorant Garamond',serif;
  font-size:28px;font-weight:500;margin-bottom:16px;
}
.about-text{font-size:15px;color:var(--gray);line-height:1.7}
.about-links{display:flex;flex-direction:column;gap:10px;margin-top:24px}
.about-link{
  display:flex;align-items:center;gap:10px;
  font-size:14px;color:var(--bx);
  text-decoration:none;font-weight:500;
}
.about-link::after{content:'→';font-size:12px}
.about-link:hover{text-decoration:underline}
/* ── footer ── */
footer{
  max-width:860px;margin:0 auto;
  padding:40px 40px 64px;
  font-size:13px;color:var(--gray2);
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;
  border-top:1px solid var(--rule);
  margin-top:80px;
}
footer a{color:var(--bx)}
footer a:hover{text-decoration:underline}
@media(max-width:700px){
  .site-header,.articles{padding:48px 24px 0}
  .article-card{grid-template-columns:48px 1fr;gap:0 16px}
  .card-status{display:none}
  .card-num{font-size:36px}
  .about{grid-template-columns:1fr;padding:48px 24px}
  footer{padding:32px 24px 48px}
  .brand-name{font-size:36px}
}
"""

def build_hub() -> str:
    articles = [
        {
            'num': '13',
            'meta': 'Série · 13 chapitres',
            'title': 'Construire une marque qui tient',
            'desc': 'Du pourquoi une marque à la gestion d\'une crise de réputation : treize questions pour piloter ce que vous représentez — pas juste le communiquer.',
            'url': 'marque.html',
            'status': 'live',
            'label': 'Disponible',
        },
        {
            'num': '—',
            'meta': 'Article · À venir',
            'title': 'Du modèle 4P aux 10P : pourquoi les confondre coûte cher',
            'desc': 'McCarthy, Booms &amp; Bitner, Godin. Trois moments, trois extensions différentes du marketing mix. Ce qu\'on y mélange dit beaucoup sur ce qu\'on ne comprend pas encore.',
            'url': None,
            'status': 'soon',
            'label': 'Bientôt',
        },
    ]

    cards = []
    for a in articles:
        arrow = '<span class="card-arrow">→</span>' if a['url'] else ''
        badge_cls = 'badge-live' if a['status']=='live' else 'badge-soon'
        card_cls = 'article-card' + (' soon' if a['status']=='soon' else '')
        tag = f'a href="{a["url"]}"' if a['url'] else 'div'
        tag_close = 'a' if a['url'] else 'div'
        cards.append(f"""
<{tag} class="{card_cls}">
  <div class="card-num">{a['num']}</div>
  <div class="card-body">
    <div class="card-meta">{a['meta']}</div>
    <div class="card-title">{a['title']}</div>
    <div class="card-desc">{a['desc']}</div>
  </div>
  <div class="card-status">
    <span class="badge {badge_cls}">{a['label']}</span>
    {arrow}
  </div>
</{tag_close}>""")

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Angles Morts — João Silva</title>
{FONTS}
<style>{HUB_CSS}</style>
</head>
<body>

<header class="site-header">
  <div class="brand">
    <span class="brand-name">Angles Morts</span>
    <span class="brand-by">par João Silva</span>
  </div>
  <p class="brand-tagline">Ce qu'on ne voit pas, même quand on regarde — et ce que ça coûte de ne pas le voir.</p>
  <hr class="rule">
</header>

<section class="articles">
  <div class="section-label">Séries &amp; articles</div>
  <div class="article-list">
    {''.join(cards)}
  </div>
</section>

<section class="about">
  <div>
    <h2 class="about-heading">João Silva</h2>
    <p class="about-text">Praticien qui théorise. Service marketing &amp; digital au CIGL Esch (Luxembourg). Master 2 avec Aaker, Kapferer, Coombs réellement étudiés — pas cités pour légitimer une facture.<br><br>La question n'est pas <em>comment tu communiques</em>. Elle est <em>qui décide de ton identité, qui la fait vivre, qui répond quand elle craque.</em></p>
    <div class="about-links">
      <a href="https://joaosilva1979.substack.com" target="_blank" rel="noopener" class="about-link">Substack</a>
      <a href="https://linkedin.com/in/joaosilva1979" target="_blank" rel="noopener" class="about-link">LinkedIn</a>
    </div>
  </div>
  <div>
    <h2 class="about-heading">Le projet</h2>
    <p class="about-text">Angles Morts, c'est le nom de la newsletter. Un angle mort, ce n'est pas ce qu'on fait mal. C'est ce qu'on ne voit pas, même quand on est concentré, même quand on fait correctement son travail.<br><br>Chaque article part d'une question qu'on évite souvent — parce qu'elle oblige à répondre.</p>
  </div>
</section>

<footer>
  <span>© João Silva</span>
  <span><a href="https://joaosilva1979.substack.com" target="_blank" rel="noopener">joaosilva1979.substack.com</a></span>
</footer>

</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
# GUIDE PAGE (marque.html)
# ─────────────────────────────────────────────────────────────────────────────

GUIDE_CSS = BASE_CSS + """
body{font-size:17px;line-height:1.75}
/* ── top bar ── */
.topbar{
  position:fixed;top:0;left:0;right:0;
  height:52px;background:rgba(250,250,248,.95);
  backdrop-filter:blur(8px);
  border-bottom:1px solid var(--rule);
  display:flex;align-items:center;
  padding:0 32px;gap:24px;
  z-index:200;
}
.topbar-home{
  font-size:13px;font-weight:500;color:var(--gray);
  display:flex;align-items:center;gap:6px;
}
.topbar-home::before{content:'←';font-size:11px}
.topbar-home:hover{color:var(--bx)}
.topbar-title{
  font-family:'Cormorant Garamond',serif;
  font-size:17px;font-weight:500;color:var(--ink);
}
/* ── layout ── */
.layout{display:grid;grid-template-columns:240px 1fr;min-height:100vh;margin-top:52px}
/* ── sidebar ── */
nav#sidebar{
  position:fixed;top:52px;left:0;
  width:240px;height:calc(100vh - 52px);
  overflow-y:auto;
  background:#fff;
  border-right:1px solid var(--rule);
  padding:32px 0 60px;
}
nav#sidebar::-webkit-scrollbar{width:2px}
nav#sidebar::-webkit-scrollbar-thumb{background:#D8D8D4}
.sidebar-section{
  padding:20px 24px 6px;
  font-size:10px;letter-spacing:.1em;text-transform:uppercase;
  color:#C0C0BC;font-weight:600;
}
.sidebar-intro{
  display:block;padding:7px 24px;
  font-size:13px;color:var(--gray);
  transition:color .15s;
}
.sidebar-intro:hover{color:var(--bx)}
a.cl{
  display:flex;align-items:baseline;gap:8px;
  padding:6px 24px;font-size:13px;line-height:1.4;
  color:var(--gray);
  border-left:2px solid transparent;
  margin-left:-1px;
  transition:color .15s,border-color .15s;
}
a.cl:hover,a.cl.active{color:var(--bx);border-left-color:var(--bx);background:linear-gradient(90deg,rgba(139,26,26,.04),transparent)}
a.cl .n{
  font-family:'Cormorant Garamond',serif;
  font-size:14px;font-weight:500;
  color:var(--bx);opacity:.5;flex-shrink:0;min-width:20px;
}
a.cl.active .n{opacity:1}
/* ── main ── */
main{
  grid-column:2;
  padding:72px 64px 120px 80px;
  max-width:820px;
}
.content{max-width:680px}
/* ── hero ── */
.guide-hero{margin-bottom:60px}
.back-label{
  display:inline-flex;align-items:center;gap:6px;
  font-size:12px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--bx);font-weight:600;margin-bottom:24px;
}
.back-label::before{content:'←';font-size:10px}
.guide-title{
  font-family:'Cormorant Garamond',serif;
  font-size:52px;font-weight:500;line-height:1.05;
  color:var(--ink);margin-bottom:12px;
  letter-spacing:-.02em;
}
.guide-sub{
  font-family:'Cormorant Garamond',serif;
  font-style:italic;font-size:22px;
  color:var(--gray);margin-bottom:8px;
}
.guide-author{
  font-size:13px;color:var(--gray2);
  display:flex;align-items:center;gap:12px;margin-bottom:0;
}
.guide-author::after{content:'';flex:1;height:1px;background:var(--rule)}
/* ── intro ── */
.intro-block{font-size:16px;line-height:1.8;color:#333;margin-bottom:0}
.intro-block p+p{margin-top:18px}
/* ── chapter ── */
.chapter{padding-top:80px;border-top:1px solid var(--rule);margin-top:72px}
.chapter:first-of-type{border-top:none;margin-top:0;padding-top:60px}
.ch-num{
  font-size:11px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--bx);font-weight:600;margin-bottom:8px;
}
.ch-title{
  font-family:'Cormorant Garamond',serif;
  font-size:38px;font-weight:500;line-height:1.15;
  color:var(--ink);margin-bottom:20px;letter-spacing:-.01em;
}
.tl{
  border-left:2px solid var(--bx);padding:4px 0 4px 18px;
  font-family:'Cormorant Garamond',serif;
  font-size:19px;font-style:italic;color:var(--gray);
  margin-bottom:36px;line-height:1.5;
}
/* ── body ── */
.ch-body h3{
  font-family:'Cormorant Garamond',serif;
  font-size:22px;font-weight:600;color:var(--ink);
  margin-top:36px;margin-bottom:12px;line-height:1.3;
}
.ch-body p{margin-bottom:18px;color:#2A2A2A}
.ch-body p:last-child{margin-bottom:0}
.ch-body strong{font-weight:600;color:var(--ink)}
.ch-body em{font-style:italic}
.ch-body ul,.ch-body ol{padding-left:22px;margin-bottom:18px}
.ch-body li{margin-bottom:6px}
.ch-body a{color:var(--bx);text-decoration:underline;text-underline-offset:2px}
/* ── 4 questions ── */
.qbox{
  background:#fff;border:1px solid var(--rule);
  border-top:3px solid var(--bx);border-radius:2px;
  padding:28px 32px;margin-top:40px;
}
.qbox h3{
  font-size:12px!important;letter-spacing:.1em;text-transform:uppercase;
  color:var(--bx)!important;font-weight:600;
  margin-top:0!important;margin-bottom:16px!important;
}
.qbox ol{padding-left:20px;margin-bottom:0}
.qbox li{font-size:15px;color:#333;line-height:1.6;margin-bottom:10px}
/* ── conclusion / resources ── */
.conclusion{
  margin-top:80px;padding:52px;
  background:#fff;border:1px solid var(--rule);border-radius:2px;
}
.conclusion h2{
  font-family:'Cormorant Garamond',serif;
  font-size:34px;font-weight:500;color:var(--ink);margin-bottom:24px;
}
.conclusion h3{
  font-family:'Cormorant Garamond',serif;
  font-size:22px;font-weight:600;margin-top:28px;margin-bottom:12px;
}
.conclusion p{margin-bottom:16px;color:#2A2A2A}
.conclusion a{color:var(--bx);text-decoration:underline;text-underline-offset:2px}
.resources{margin-top:80px}
.resources h2{
  font-family:'Cormorant Garamond',serif;
  font-size:28px;font-weight:500;margin-bottom:24px;
}
.resources h3{
  font-size:12px!important;letter-spacing:.08em;text-transform:uppercase;
  color:var(--bx)!important;font-weight:600;
  margin-top:28px!important;margin-bottom:10px!important;
}
.resources ul{padding-left:20px;margin-bottom:12px}
.resources li{font-size:14px;color:#444;margin-bottom:5px;line-height:1.5}
.resources a{color:var(--bx);text-decoration:none}
.resources a:hover{text-decoration:underline}
/* ── footer ── */
footer{
  margin-top:100px;padding-top:32px;border-top:1px solid var(--rule);
  font-size:13px;color:var(--gray2);
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;
}
footer a{color:var(--bx)}
footer a:hover{text-decoration:underline}
/* ── responsive ── */
@media(max-width:900px){
  .layout{grid-template-columns:1fr}
  nav#sidebar{display:none}
  main{padding:40px 24px 80px;max-width:100%}
  .guide-title{font-size:38px}
  .topbar{padding:0 20px}
}
"""

GUIDE_JS = """
<script>
const links = document.querySelectorAll('a.cl[href^="#"]');
const targets = [...links].map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
const io = new IntersectionObserver(entries=>{
  entries.forEach(e=>{
    if(e.isIntersecting){
      links.forEach(l=>l.classList.remove('active'));
      const a=document.querySelector('a.cl[href="#'+e.target.id+'"]');
      if(a)a.classList.add('active');
    }
  });
},{threshold:.15,rootMargin:'-52px 0px -60% 0px'});
targets.forEach(t=>io.observe(t));
</script>
"""

def build_guide(data: dict) -> str:
    # Sidebar
    sb = ['<nav id="sidebar">']
    sb.append('<div class="sidebar-section">Introduction</div>')
    sb.append('<a href="#intro" class="sidebar-intro">À qui s\'adresse ce guide</a>')
    sb.append('<div class="sidebar-section">Chapitres</div>')
    for ch in data['chapters']:
        short = ch['title'].split(':')[0].strip() if ':' in ch['title'] else ch['title']
        if len(short)>36: short=short[:34]+'…'
        sb.append(f'<a href="#ch{ch["num"]}" class="cl"><span class="n">{ch["num"]:02d}</span>{escape(short)}</a>')
    if data['conclusion']:
        sb.append('<div class="sidebar-section">Conclusion</div>')
        sb.append('<a href="#conclusion" class="sidebar-intro">Conclusion</a>')
    if data['resources']:
        sb.append('<a href="#resources" class="sidebar-intro">Sources</a>')
    sb.append('</nav>')

    parts = [f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Construire une marque qui tient — João Silva</title>
{FONTS}
<style>{GUIDE_CSS}</style>
</head>
<body>

<div class="topbar">
  <a href="index.html" class="topbar-home">Angles Morts</a>
  <span class="topbar-title">Construire une marque qui tient</span>
</div>

<div class="layout">
{''.join(sb)}
<main>
<div class="content">
"""]

    # Hero
    parts.append('<section id="intro">')
    parts.append('<div class="guide-hero">')
    parts.append('<a href="index.html" class="back-label">Angles Morts</a>')
    parts.append(f'<h1 class="guide-title">{escape(data["title"])}</h1>')
    if data['subtitle']:
        parts.append(f'<p class="guide-sub">{escape(data["subtitle"])}</p>')
    if data['author']:
        parts.append(f'<p class="guide-author">{escape(data["author"])}</p>')
    parts.append('</div>')

    if data['intro']:
        parts.append('<div class="intro-block">')
        for block in data['intro']:
            parts.append(render_paragraphs(block))
        parts.append('</div>')
    parts.append('</section>')

    # Chapters
    for ch in data['chapters']:
        parts.append(f'<section class="chapter" id="ch{ch["num"]}">')
        parts.append(f'<div class="ch-num">Chapitre {ch["num"]}</div>')
        parts.append(f'<h2 class="ch-title">{inline_md(ch["title"])}</h2>')
        if ch['tagline']:
            parts.append(f'<blockquote class="tl">{inline_md(ch["tagline"])}</blockquote>')
        parts.append('<div class="ch-body">')
        for block in ch['body_parts']:
            parts.append(render_paragraphs(block))
        parts.append('</div>')
        if ch['questions_raw']:
            parts.append(render_questions(ch['questions_raw']))
        parts.append('</section>')

    # Conclusion
    if data['conclusion']:
        parts.append('<section class="conclusion" id="conclusion">')
        for item in data['conclusion']:
            if item['type']=='h2': parts.append(f'<h2>{inline_md(item["text"])}</h2>')
            elif item['type']=='h3': parts.append(f'<h3>{inline_md(item["text"])}</h3>')
            elif item['type']=='p':
                t=item['text'].strip()
                if t and t!='---': parts.append(f'<p>{inline_md(t)}</p>')
        parts.append('</section>')

    # Resources
    if data['resources']:
        parts.append('<section class="resources" id="resources">')
        in_ul=False
        for item in data['resources']:
            if item['type'] in('h2','h3'):
                if in_ul: parts.append('</ul>'); in_ul=False
                parts.append(f'<{item["type"]}>{inline_md(item["text"])}</{item["type"]}>')
            elif item['type'] in('li','li_sub'):
                if not in_ul: parts.append('<ul>'); in_ul=True
                parts.append(f'<li>{inline_md(item["text"])}</li>')
        if in_ul: parts.append('</ul>')
        parts.append('</section>')

    parts.append(f"""<footer>
<span>© João Silva — <a href="index.html">Angles Morts</a></span>
<span><a href="https://joaosilva1979.substack.com" target="_blank" rel="noopener">Substack</a></span>
</footer>
</div></main></div>
{GUIDE_JS}
</body>
</html>""")

    return '\n'.join(parts)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if not SRC.exists():
        print(f"Source introuvable : {SRC}", file=sys.stderr); sys.exit(1)

    md = SRC.read_text(encoding='utf-8')
    data = parse(md)

    hub = build_hub()
    OUT_HUB.write_text(hub, encoding='utf-8')
    print(f"✓ {OUT_HUB}  ({len(hub):,} chars)")

    guide = build_guide(data)
    OUT_GUIDE.write_text(guide, encoding='utf-8')
    print(f"✓ {OUT_GUIDE}  ({len(guide):,} chars, {len(data['chapters'])} chapitres)")
