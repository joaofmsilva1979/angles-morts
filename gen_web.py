"""
gen_web.py — génère index.html (hub) + marque.html (guide 13 chapitres)
Usage: uv run python gen_web.py
"""

import re
import sys
from pathlib import Path
from html import escape

SRC = Path.home() / "Library/CloudStorage/GoogleDrive-davisthe8th@gmail.com/My Drive/JOAO/ANGLES_MORTS/LinkedIn/SEMAINE/Construire-une-marque-qui-tient/TOUT/construire-une-marque-qui-tient-COMPLET.md"
SRC_4P    = Path.home() / "Library/CloudStorage/GoogleDrive-davisthe8th@gmail.com/My Drive/JOAO/ANGLES_MORTS/angles-morts-web/4p-COMPLET.md"
OUT_HUB   = Path(__file__).parent / "index.html"
OUT_GUIDE = Path(__file__).parent / "marque.html"
OUT_4P    = Path(__file__).parent / "mix-marketing.html"

BORDEAUX = "#8B1A1A"
GRAY = "#6B6B6B"

# ─────────────────────────────────────────────────────────────────────────────
# SHARED CSS
# ─────────────────────────────────────────────────────────────────────────────

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:ital,wght@0,400;0,500;0,600;1,400&display=swap" rel="stylesheet">"""

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
    text = re.sub(r'\s*—\s*', ' ; ', text)
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
:root{--cream:#F0EAE2;--dark:#1C1C1A}
body{font-size:16px;line-height:1.65;background:var(--cream)}
/* ── NAV ── */
.site-nav{
  background:var(--cream);
  border-bottom:1px solid rgba(0,0,0,.08);
  position:sticky;top:0;z-index:100;
}
.nav-inner{
  max-width:1100px;margin:0 auto;
  padding:0 40px;
  display:flex;align-items:center;
  height:52px;gap:0;
}
.nav-logo{
  font-family:'Cormorant Garamond',serif;
  font-size:17px;font-weight:600;color:var(--ink);
  margin-right:40px;white-space:nowrap;
}
.nav-links{display:flex;gap:4px;flex:1}
.nav-link{
  font-size:13px;font-weight:500;color:var(--gray);
  padding:6px 12px;border-radius:4px;
  transition:color .15s,background .15s;
}
.nav-link:hover{color:var(--ink);background:rgba(0,0,0,.05)}
.nav-cta{
  background:var(--bx);color:#fff;
  font-size:13px;font-weight:600;
  padding:8px 18px;border-radius:4px;
  transition:background .15s;
  white-space:nowrap;
}
.nav-cta:hover{background:#6B1212}
/* ── HERO ── */
.hero{
  max-width:1100px;margin:0 auto;
  padding:72px 40px 80px;
  display:grid;grid-template-columns:1fr 340px;
  gap:60px;align-items:center;
}
.hero-label{
  font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:var(--bx);margin-bottom:20px;
}
.hero-title{
  font-family:'Playfair Display',serif;
  font-size:62px;font-weight:700;line-height:1.05;
  color:var(--ink);letter-spacing:-.02em;
  margin-bottom:20px;
}
.hero-title em{font-style:italic;color:var(--bx)}
.hero-desc{
  font-size:17px;color:#444;line-height:1.7;
  max-width:500px;margin-bottom:32px;
}
.hero-actions{display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.btn-primary{
  background:var(--bx);color:#fff;
  font-size:14px;font-weight:600;
  padding:11px 22px;border-radius:4px;
  transition:background .15s;
}
.btn-primary:hover{background:#6B1212}
.btn-secondary{
  font-size:14px;font-weight:500;color:var(--gray);
  border-bottom:1px solid currentColor;
  padding-bottom:1px;
  transition:color .15s;
}
.btn-secondary:hover{color:var(--bx)}
/* ── PHOTO ── */
.hero-photo-wrap{
  width:280px;justify-self:center;
}
.hero-photo{
  width:100%;aspect-ratio:1;
  object-fit:cover;object-position:center top;
  border-radius:6px;
  filter:grayscale(100%);
  display:block;
}
.hero-photo-caption{
  margin-top:10px;
  font-size:10px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--gray2);text-align:center;
}
/* ── FEATURED SERIES (dark block) ── */
.featured{
  background:var(--dark);
  padding:56px 0;
}
.featured-inner{
  max-width:1100px;margin:0 auto;padding:0 40px;
  display:grid;grid-template-columns:1fr auto;
  gap:48px;align-items:center;
}
.feat-label{
  font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:var(--bx);margin-bottom:14px;
}
.feat-title{
  font-family:'Playfair Display',serif;
  font-size:42px;font-weight:700;color:#fff;
  line-height:1.1;margin-bottom:12px;letter-spacing:-.01em;
}
.feat-desc{font-size:15px;color:rgba(255,255,255,.55);line-height:1.6;max-width:460px;margin-bottom:24px}
.feat-cta{
  display:inline-flex;align-items:center;gap:8px;
  font-size:14px;font-weight:600;color:#fff;
  border:1px solid rgba(255,255,255,.2);
  padding:10px 20px;border-radius:4px;
  transition:border-color .15s,background .15s;
}
.feat-cta:hover{border-color:var(--bx);background:rgba(139,26,26,.15)}
.feat-badge{
  background:var(--bx);color:#fff;
  font-size:11px;font-weight:700;letter-spacing:.06em;
  padding:4px 10px;border-radius:3px;align-self:start;margin-top:4px;
}
/* ── ARTICLES ── */
.articles-section{
  max-width:1100px;margin:0 auto;padding:72px 40px;
}
.sec-label{
  font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:var(--gray2);margin-bottom:36px;
  padding-bottom:16px;border-bottom:1px solid var(--rule);
}
.article-list{display:flex;flex-direction:column}
.article-card{
  display:grid;grid-template-columns:1fr auto;
  gap:24px;align-items:center;
  padding:28px 0;
  border-bottom:1px solid var(--rule);
  text-decoration:none;color:inherit;
}
.article-card.soon{cursor:default}
.card-meta{font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:var(--gray2);margin-bottom:6px}
.card-title{
  font-family:'Playfair Display',serif;
  font-size:22px;font-weight:600;color:var(--ink);
  line-height:1.2;margin-bottom:6px;
  transition:color .15s;
}
.article-card:not(.soon):hover .card-title{color:var(--bx)}
.card-desc{font-size:14px;color:var(--gray);line-height:1.55;max-width:600px}
.badge{
  font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  padding:5px 12px;border-radius:3px;white-space:nowrap;
}
.badge-live{background:rgba(139,26,26,.1);color:var(--bx)}
.badge-soon{background:rgba(0,0,0,.06);color:var(--gray2)}
/* ── ABOUT ── */
.about-section{
  background:#E8E0D6;
  padding:72px 0;
}
.about-inner{
  max-width:1100px;margin:0 auto;padding:0 40px;
  display:grid;grid-template-columns:1fr 1fr;gap:64px;
}
.about-heading{
  font-family:'Cormorant Garamond',serif;
  font-size:32px;font-weight:500;color:var(--ink);margin-bottom:14px;
}
.about-text{font-size:15px;color:#555;line-height:1.75}
.about-links{margin-top:20px;display:flex;flex-direction:column;gap:8px}
.about-link{
  font-size:14px;font-weight:500;color:var(--bx);
  display:inline-flex;align-items:center;gap:6px;
}
.about-link::after{content:'↗';font-size:11px}
.about-link:hover{text-decoration:underline}
/* ── FOOTER ── */
.site-footer{
  background:var(--dark);
  padding:40px;
}
.footer-inner{
  max-width:1100px;margin:0 auto;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;
}
.footer-brand{
  font-family:'Cormorant Garamond',serif;
  font-size:16px;color:rgba(255,255,255,.5);
}
.footer-links{display:flex;gap:20px}
.footer-link{font-size:13px;color:rgba(255,255,255,.4);transition:color .15s}
.footer-link:hover{color:#fff}
/* ── RESPONSIVE ── */
@media(max-width:800px){
  .hero{grid-template-columns:1fr;padding:48px 24px 56px;gap:40px}
  .hero-photo-wrap{width:200px}
  .hero-title{font-size:44px}
  .featured-inner{grid-template-columns:1fr;padding:0 24px}
  .feat-badge{display:none}
  .articles-section{padding:48px 24px}
  .about-inner{grid-template-columns:1fr;gap:36px;padding:0 24px}
  .about-section{padding:48px 0}
  .nav-inner{padding:0 20px}
  .nav-links{display:none}
  .footer-inner{padding:0}
}
"""

def build_hub() -> str:
    articles = [
        {
            'meta': 'Série · 13 chapitres',
            'title': 'Construire une marque qui tient',
            'desc': 'Du pourquoi une marque à la gestion d\'une crise de réputation : treize questions pour piloter ce que vous représentez — pas juste le communiquer.',
            'url': 'marque.html',
            'status': 'live',
            'label': 'Disponible',
        },
        {
            'meta': 'Article · Essai',
            'title': 'Du 4P au 10P : un cadre ne donne pas de sens',
            'desc': 'McCarthy, Booms &amp; Bitner, Godin. Soixante ans d\'additions. Et si le problème n\'était pas le nombre de P, mais ce qu\'un cadre ne peut pas faire à ta place ?',
            'url': 'mix-marketing.html',
            'status': 'live',
            'label': 'Disponible',
        },
    ]

    cards = []
    for a in articles:
        badge_cls = 'badge-live' if a['status']=='live' else 'badge-soon'
        card_cls = 'article-card' + (' soon' if a['status']=='soon' else '')
        tag = f'a href="{a["url"]}"' if a['url'] else 'div'
        tag_close = 'a' if a['url'] else 'div'
        cards.append(f"""<{tag} class="{card_cls}">
  <div>
    <div class="card-meta">{a['meta']}</div>
    <div class="card-title">{a['title']}</div>
    <div class="card-desc">{a['desc']}</div>
  </div>
  <span class="badge {badge_cls}">{a['label']}</span>
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

<!-- NAV -->
<nav class="site-nav">
  <div class="nav-inner">
    <span class="nav-logo">Angles Morts</span>
    <div class="nav-links">
      <a href="#series" class="nav-link">Séries</a>
      <a href="#about" class="nav-link">À propos</a>
      <a href="https://joaosilva1979.substack.com" target="_blank" rel="noopener" class="nav-link">Substack</a>
    </div>
    <a href="https://joaosilva1979.substack.com" target="_blank" rel="noopener" class="nav-cta">S'abonner</a>
  </div>
</nav>

<!-- HERO -->
<section class="hero">
  <div>
    <div class="hero-label">Marque · Marketing · Nouvelles technologies · Curiosités</div>
    <h1 class="hero-title">Ce qu'on ne voit pas,<br>même quand on <em>regarde</em>.</h1>
    <p class="hero-desc">Des séries longues sur la marque, le marketing et la gouvernance de ce qu'on représente. Pas des conseils génériques. Des questions qui font un peu mal.</p>
    <div class="hero-actions">
      <a href="marque.html" class="btn-primary">Lire la série →</a>
      <a href="#series" class="btn-secondary">Voir toutes les séries</a>
    </div>
  </div>
  <div class="hero-photo-wrap">
    <img src="joao.png" alt="João Silva" class="hero-photo">
    <p class="hero-photo-caption">Éternel curieux</p>
  </div>
</section>

<!-- FEATURED -->
<div class="featured">
  <div class="featured-inner">
    <div>
      <div class="feat-label">La série en cours</div>
      <h2 class="feat-title">Construire une marque qui tient</h2>
      <p class="feat-desc">Treize chapitres. Treize questions qu'on évite parce qu'elles obligent à répondre. De la brand equity à la gestion de crise — le fil conducteur est toujours le même : qui décide, qui fait vivre, qui répond ?</p>
      <a href="marque.html" class="feat-cta">Lire les 13 chapitres →</a>
    </div>
    <span class="feat-badge">13 chapitres</span>
  </div>
</div>

<!-- ARTICLES LIST -->
<section class="articles-section" id="series">
  <div class="sec-label">Toutes les séries &amp; articles</div>
  <div class="article-list">
    {''.join(cards)}
  </div>
</section>

<!-- ABOUT -->
<section class="about-section" id="about">
  <div class="about-inner">
    <div>
      <h2 class="about-heading">João Silva</h2>
      <p class="about-text">J'écris depuis l'intérieur d'une organisation ; pas depuis un cabinet conseil.<br><br>La question n'est pas <em>comment tu communiques</em>. Elle est <em>qui décide, qui fait vivre, qui répond quand ça craque.</em></p>
      <div class="about-links">
        <a href="https://joaosilva1979.substack.com" target="_blank" rel="noopener" class="about-link">Substack</a>
        <a href="https://www.linkedin.com/in/joaosilva-commarketeer/" target="_blank" rel="noopener" class="about-link">LinkedIn</a>
      </div>
    </div>
    <div>
      <h2 class="about-heading">Le projet</h2>
      <p class="about-text">Angles Morts, c'est le nom de la newsletter. Un angle mort, ce n'est pas ce qu'on fait mal. C'est ce qu'on ne voit pas, même quand on est concentré, même quand on fait correctement son travail.<br><br>Chaque série part d'une question qu'on évite souvent — parce qu'elle oblige à répondre. Pas de conseils applicables à n'importe qui. Un angle qui déplace.</p>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer class="site-footer">
  <div class="footer-inner">
    <span class="footer-brand">Angles Morts — João Silva</span>
    <div class="footer-links">
      <a href="https://joaosilva1979.substack.com" target="_blank" rel="noopener" class="footer-link">Substack</a>
      <a href="https://www.linkedin.com/in/joaosilva-commarketeer/" target="_blank" rel="noopener" class="footer-link">LinkedIn</a>
    </div>
  </div>
</footer>

</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
# GUIDE PAGE (marque.html)
# ─────────────────────────────────────────────────────────────────────────────

GUIDE_CSS = BASE_CSS + """
body{font-size:18px;line-height:1.78}
/* ── top bar ── */
.topbar{
  position:fixed;top:0;left:0;right:0;
  height:52px;background:rgba(250,250,248,.95);
  backdrop-filter:blur(8px);
  border-bottom:1px solid var(--rule);
  display:flex;align-items:center;
  padding:0 36px;gap:24px;
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
.layout{display:grid;grid-template-columns:220px 1fr;min-height:100vh;margin-top:52px}
/* ── sidebar ── */
nav#sidebar{
  position:fixed;top:52px;left:0;
  width:220px;height:calc(100vh - 52px);
  overflow-y:auto;
  background:#fff;
  border-right:1px solid var(--rule);
  padding:32px 0 60px;
}
nav#sidebar::-webkit-scrollbar{width:2px}
nav#sidebar::-webkit-scrollbar-thumb{background:#D8D8D4}
.sidebar-section{
  padding:20px 22px 6px;
  font-size:10px;letter-spacing:.1em;text-transform:uppercase;
  color:#C0C0BC;font-weight:600;
}
.sidebar-intro{
  display:block;padding:7px 22px;
  font-size:13px;color:var(--gray);
  transition:color .15s;
}
.sidebar-intro:hover{color:var(--bx)}
a.cl{
  display:flex;align-items:baseline;gap:8px;
  padding:6px 22px;font-size:13px;line-height:1.4;
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
  padding:80px 80px 140px 72px;
}
.content{max-width:800px}
/* ── hero ── */
.guide-hero{margin-bottom:64px}
.back-label{
  display:inline-flex;align-items:center;gap:6px;
  font-size:12px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--bx);font-weight:600;margin-bottom:28px;
}
.back-label::before{content:'←';font-size:10px}
.guide-title{
  font-family:'Cormorant Garamond',serif;
  font-size:76px;font-weight:500;line-height:1.0;
  color:var(--ink);margin-bottom:16px;
  letter-spacing:-.03em;
}
.guide-sub{
  font-family:'Cormorant Garamond',serif;
  font-style:italic;font-size:26px;
  color:var(--gray);margin-bottom:10px;
}
.guide-author{
  font-size:14px;color:var(--gray2);
  display:flex;align-items:center;gap:12px;margin-bottom:0;
}
.guide-author::after{content:'';flex:1;height:1px;background:var(--rule)}
/* ── intro ── */
.intro-block{font-size:17px;line-height:1.82;color:#333;margin-bottom:0}
.intro-block p+p{margin-top:20px}
/* ── chapter ── */
.chapter{padding-top:96px;border-top:1px solid var(--rule);margin-top:88px}
.chapter:first-of-type{border-top:none;margin-top:0;padding-top:72px}
.ch-num{
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--bx);font-weight:600;margin-bottom:10px;
}
.ch-title{
  font-family:'Cormorant Garamond',serif;
  font-size:52px;font-weight:500;line-height:1.1;
  color:var(--ink);margin-bottom:24px;letter-spacing:-.02em;
}
.tl{
  border-left:2px solid var(--bx);padding:6px 0 6px 22px;
  font-family:'Cormorant Garamond',serif;
  font-size:22px;font-style:italic;color:var(--gray);
  margin-bottom:44px;line-height:1.5;
}
/* ── body ── */
.ch-body h3{
  font-family:'Cormorant Garamond',serif;
  font-size:26px;font-weight:600;color:var(--ink);
  margin-top:44px;margin-bottom:14px;line-height:1.25;
}
.ch-body p{margin-bottom:20px;color:#2A2A2A}
.ch-body p:last-child{margin-bottom:0}
.ch-body strong{font-weight:600;color:var(--ink)}
.ch-body em{font-style:italic}
.ch-body ul,.ch-body ol{padding-left:24px;margin-bottom:20px}
.ch-body li{margin-bottom:8px}
.ch-body a{color:var(--bx);text-decoration:underline;text-underline-offset:2px}
/* ── 4 questions ── */
.qbox{
  background:#fff;border:1px solid var(--rule);
  border-top:3px solid var(--bx);border-radius:2px;
  padding:32px 36px;margin-top:48px;
}
.qbox h3{
  font-size:12px!important;letter-spacing:.1em;text-transform:uppercase;
  color:var(--bx)!important;font-weight:600;
  margin-top:0!important;margin-bottom:18px!important;
}
.qbox ol{padding-left:22px;margin-bottom:0}
.qbox li{font-size:16px;color:#333;line-height:1.65;margin-bottom:12px}
/* ── conclusion / resources ── */
.conclusion{
  margin-top:96px;padding:60px;
  background:#fff;border:1px solid var(--rule);border-radius:2px;
}
.conclusion h2{
  font-family:'Cormorant Garamond',serif;
  font-size:40px;font-weight:500;color:var(--ink);margin-bottom:28px;
}
.conclusion h3{
  font-family:'Cormorant Garamond',serif;
  font-size:26px;font-weight:600;margin-top:32px;margin-bottom:14px;
}
.conclusion p{margin-bottom:18px;color:#2A2A2A}
.conclusion a{color:var(--bx);text-decoration:underline;text-underline-offset:2px}
.resources{margin-top:96px}
.resources h2{
  font-family:'Cormorant Garamond',serif;
  font-size:32px;font-weight:500;margin-bottom:28px;
}
.resources h3{
  font-size:12px!important;letter-spacing:.08em;text-transform:uppercase;
  color:var(--bx)!important;font-weight:600;
  margin-top:32px!important;margin-bottom:12px!important;
}
.resources ul{padding-left:22px;margin-bottom:14px}
.resources li{font-size:15px;color:#444;margin-bottom:6px;line-height:1.6}
.resources a{color:var(--bx);text-decoration:none}
.resources a:hover{text-decoration:underline}
/* ── footer ── */
footer{
  margin-top:120px;padding-top:36px;border-top:1px solid var(--rule);
  font-size:13px;color:var(--gray2);
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;
}
footer a{color:var(--bx)}
footer a:hover{text-decoration:underline}
/* ── responsive ── */
@media(max-width:960px){
  .layout{grid-template-columns:1fr}
  nav#sidebar{display:none}
  main{padding:40px 28px 80px;max-width:100%}
  .guide-title{font-size:48px}
  .ch-title{font-size:38px}
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
# 4P ARTICLE
# ─────────────────────────────────────────────────────────────────────────────

def slugify(t: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', t.lower().strip()).strip('-')

def build_4p(src: Path) -> str:
    raw = src.read_text(encoding='utf-8')
    lines = raw.splitlines()

    title = ''; author = ''; opening_quote = ''
    sections: list[dict] = []  # {id, title, lines}
    cur_lines: list[str] = []
    cur_title = ''; cur_id = ''
    in_resources = False

    for line in lines:
        if line.startswith('# ') and not title:
            title = line[2:].strip(); continue
        if line.startswith('*') and not author:
            author = line.strip('*').strip(); continue
        if line.startswith('> ') and not opening_quote and not sections:
            opening_quote = line[2:].strip(); continue
        if line.startswith('## '):
            if cur_title:
                sections.append({'id': cur_id, 'title': cur_title, 'lines': cur_lines, 'resources': in_resources})
            cur_title = line[3:].strip()
            cur_id = slugify(cur_title)
            in_resources = any(k in cur_title for k in ('Sources', 'Ressources', 'Références'))
            cur_lines = []
        else:
            if cur_title: cur_lines.append(line)

    if cur_title:
        sections.append({'id': cur_id, 'title': cur_title, 'lines': cur_lines, 'resources': in_resources})

    def render_section_body(slines: list[str]) -> str:
        out: list[str] = []
        buf: list[str] = []
        in_ul = in_ol = False

        def flush():
            nonlocal in_ul, in_ol
            if in_ul: out.append('</ul>'); in_ul = False
            if in_ol: out.append('</ol>'); in_ol = False
            if buf:
                out.append(f'<p>{inline_md(" ".join(buf))}</p>')
                buf.clear()

        for line in slines:
            s = line.strip()
            if not s:
                flush(); continue
            if s.startswith('> '):
                flush()
                out.append(f'<blockquote class="pull">{inline_md(s[2:])}</blockquote>')
                continue
            if s.startswith(('- ', '* ')):
                if buf: flush()
                if not in_ul: out.append('<ul>'); in_ul = True
                out.append(f'<li>{inline_md(s[2:])}</li>')
                continue
            m = re.match(r'^\d+\.\s+(.*)', s)
            if m:
                if buf: flush()
                if not in_ol: out.append('<ol>'); in_ol = True
                out.append(f'<li>{inline_md(m.group(1))}</li>')
                continue
            if s in ('---', '***'):
                flush(); continue
            if in_ul or in_ol: flush()
            buf.append(s)
        flush()
        return '\n'.join(out)

    # sidebar
    content_sections = [s for s in sections if not s['resources']]
    resource_sections = [s for s in sections if s['resources']]

    sb = ['<nav id="sidebar">']
    sb.append('<div class="sidebar-section">Article</div>')
    for s in content_sections:
        sb.append(f'<a href="#{s["id"]}" class="cl"><span>{s["title"]}</span></a>')
    if resource_sections:
        sb.append('<a href="#sources" class="sidebar-intro">Sources</a>')
    sb.append('</nav>')

    # body
    parts = [f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} — João Silva</title>
{FONTS}
<style>{GUIDE_CSS}
.opening-quote{{
  font-family:'Cormorant Garamond',serif;
  font-size:22px;font-style:italic;line-height:1.55;
  color:var(--bx);border-left:3px solid var(--bx);
  padding:12px 24px;margin:40px 0 64px;
}}
.section-block{{margin-bottom:104px}}
.section-block h2{{
  font-family:'Playfair Display',serif;
  font-size:32px;font-weight:700;line-height:1.2;
  color:var(--ink);margin:0 0 36px;
  padding-bottom:16px;border-bottom:1px solid var(--rule);
}}
.section-block p{{margin-bottom:28px;color:#2A2A2A;line-height:1.85}}
.section-block p:last-child{{margin-bottom:0}}
.section-block ul,.section-block ol{{padding-left:24px;margin:0 0 28px}}
.section-block li{{margin-bottom:10px;line-height:1.7}}
.section-block .pull{{
  border-left:2px solid var(--bx);
  padding:6px 0 6px 22px;
  font-family:'Cormorant Garamond',serif;
  font-size:22px;font-style:italic;color:var(--gray);
  margin:36px 0;line-height:1.5;
}}
</style>
</head>
<body>

<div class="topbar">
  <a href="index.html" class="topbar-home">Angles Morts</a>
  <span class="topbar-title">{escape(title)}</span>
</div>

<div class="layout">
{''.join(sb)}
<main>
<div class="content">
"""]

    # hero
    parts.append(f"""<div class="guide-hero">
  <a href="index.html" class="back-label">Angles Morts</a>
  <h1 class="guide-title">{escape(title)}</h1>
  <p class="guide-meta">{escape(author)}</p>
</div>""")

    if opening_quote:
        parts.append(f'<div class="opening-quote">{inline_md(opening_quote)}</div>')

    for s in content_sections:
        body = render_section_body(s['lines'])
        parts.append(f'<section class="section-block" id="{s["id"]}"><h2>{escape(s["title"])}</h2>{body}</section>')

    if resource_sections:
        parts.append('<section class="resources" id="sources">')
        for s in resource_sections:
            parts.append(f'<h2>{escape(s["title"])}</h2>')
            parts.append(render_section_body(s['lines']))
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

    article_4p = build_4p(SRC_4P)
    OUT_4P.write_text(article_4p, encoding='utf-8')
    print(f"✓ {OUT_4P}  ({len(article_4p):,} chars)")
