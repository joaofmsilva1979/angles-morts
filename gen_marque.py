#!/usr/bin/env python3
"""
Génère "Construire une marque qui tient" — Word éditorial v3
Polices : Cormorant Garamond (affichage) + Inter (corps)
Visuels : logo, photo, slides carousels (slide 1 opener + slide 2 mid-ch), page de fin
"""
import re, os, subprocess, glob as globmod
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

EP_ROOT = (
    "/Users/joao.silva/Library/CloudStorage/"
    "GoogleDrive-davisthe8th@gmail.com/My Drive/JOAO/ANGLES_MORTS/"
    "LinkedIn/SEMAINE/Construire-une-marque-qui-tient"
)
BASE  = f"{EP_ROOT}/TOUT"
MD    = f"{BASE}/construire-une-marque-qui-tient-COMPLET.md"
OUT   = f"{BASE}/construire-une-marque-qui-tient-v2.docx"
LOGO  = f"{BASE}/anglesmorts_logo.png"
PHOTO = f"{BASE}/joao_phone.png"
SLIDES = f"{BASE}/slides"

INK   = RGBColor(0x1A, 0x1A, 0x1A)
RED   = RGBColor(0x8B, 0x1A, 0x1A)
GRAY  = RGBColor(0x88, 0x88, 0x88)
LGRAY = RGBColor(0xCC, 0xCC, 0xCC)
LINK  = RGBColor(0x1B, 0x4F, 0x8C)
F_SER = "Cormorant Garamond"
F_SAN = "Inter"
_HL   = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink'


# ── Extraction slides ────────────────────────────────────

def extract_slides():
    os.makedirs(SLIDES, exist_ok=True)
    for ep in range(1, 14):
        ep_dir = f"{EP_ROOT}/{ep:02d}"
        pdfs   = globmod.glob(f"{ep_dir}/*.pdf")
        if not pdfs:
            continue
        pdf = pdfs[0]

        # Slide 1 via qlmanage (haute résolution)
        s1 = f"{SLIDES}/ep{ep:02d}_s1.png"
        if not os.path.exists(s1):
            subprocess.run(["qlmanage", "-t", "-s", "1500", "-o", SLIDES, pdf],
                           capture_output=True)
            gen = globmod.glob(f"{SLIDES}/*.pdf.png")
            if gen:
                os.rename(gen[0], s1)
                print(f"  ✓ ep{ep:02d} slide 1")

        # Slide 2 via pdftoppm
        s2 = f"{SLIDES}/ep{ep:02d}_s2.png"
        if not os.path.exists(s2):
            prefix = f"{SLIDES}/ep{ep:02d}_s2_tmp"
            subprocess.run(
                ["pdftoppm", "-png", "-r", "200", "-f", "2", "-l", "2", pdf, prefix],
                capture_output=True
            )
            gen = globmod.glob(f"{prefix}*.png")
            if gen:
                os.rename(gen[0], s2)
                print(f"  ✓ ep{ep:02d} slide 2")


# ── Primitives ──────────────────────────────────────────

def rn(p, text, font, size, bold=False, italic=False, color=None, caps=False):
    r = p.add_run(text)
    r.font.name = font; r.font.size = Pt(size)
    r.font.bold = bold; r.font.italic = italic; r.font.all_caps = caps
    if color: r.font.color.rgb = color
    return r

def fmt(p, before=0, after=0, ls=None, align=None, indent=None):
    pf = p.paragraph_format
    pf.space_before = Pt(before); pf.space_after = Pt(after)
    if ls:     pf.line_spacing = Pt(ls)
    if align is not None: pf.alignment = align
    if indent is not None: pf.left_indent = Cm(indent)

def inline(p, text, font, size, color=None, bold=False, italic=False):
    pos = 0
    for m in re.finditer(r'\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*', text):
        if m.start() > pos:
            rn(p, text[pos:m.start()], font, size, bold=bold, italic=italic, color=color)
        g1,g2,g3 = m.group(1),m.group(2),m.group(3)
        if g1:   rn(p, g1, font, size, bold=True,  italic=True,   color=color)
        elif g2: rn(p, g2, font, size, bold=True,  italic=italic, color=color)
        else:    rn(p, g3, font, size, bold=bold,  italic=True,   color=color)
        pos = m.end()
    if pos < len(text):
        rn(p, text[pos:], font, size, bold=bold, italic=italic, color=color)

def pg_break(doc):
    p = doc.add_paragraph()
    r = OxmlElement('w:r'); br = OxmlElement('w:br')
    br.set(qn('w:type'), 'page'); r.append(br); p._p.append(r)

def rule(doc, hex_color="BBBBBB", sz=4, before=6, after=6):
    p = doc.add_paragraph(); fmt(p, before=before, after=after)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr'); bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'),'single'); bot.set(qn('w:sz'),str(sz))
    bot.set(qn('w:space'),'1');   bot.set(qn('w:color'),hex_color)
    pBdr.append(bot); pPr.append(pBdr)

def spacer(doc, pt=12):
    p = doc.add_paragraph(); fmt(p, after=pt)

def add_img(doc, path, width_cm, align=WD_ALIGN_PARAGRAPH.CENTER, before=0, after=12):
    p = doc.add_paragraph(); fmt(p, before=before, after=after, align=align)
    p.add_run().add_picture(path, width=Cm(width_cm))

def no_border_table(table):
    tbl = table._tbl
    tblPr = tbl.find(qn('w:tblPr')) or OxmlElement('w:tblPr')
    tblBorders = OxmlElement('w:tblBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
        el = OxmlElement(f'w:{side}'); el.set(qn('w:val'),'none')
        tblBorders.append(el)
    ex = tblPr.find(qn('w:tblBorders'))
    if ex is not None: tblPr.remove(ex)
    tblPr.append(tblBorders)


# ── Cover ───────────────────────────────────────────────

def cover(doc):
    # Logo Angles Morts
    if os.path.exists(LOGO):
        add_img(doc, LOGO, 2.2, WD_ALIGN_PARAGRAPH.LEFT, before=10, after=28)

    # Grand titre
    for line in ["CONSTRUIRE", "UNE MARQUE", "QUI TIENT"]:
        p = doc.add_paragraph()
        rn(p, line, F_SER, 76, bold=True, color=INK); fmt(p, after=0)

    rule(doc, "8B1A1A", sz=8, before=18, after=18)

    # Slogan partie 1
    p = doc.add_paragraph()
    rn(p, "LE CADRE FAIT LA DIFFÉRENCE.", F_SER, 18, bold=True, color=INK, caps=True)
    fmt(p, after=8)

    # Slogan partie 2
    p = doc.add_paragraph()
    rn(p, "…et une crise ne teste jamais votre communication.\n"
          "Elle teste tout ce qu'il y avait derrière,\n"
          "depuis le premier épisode.",
       F_SER, 13, italic=True, color=GRAY)
    fmt(p, after=30)

    p = doc.add_paragraph()
    rn(p, "Guide complet — 13 chapitres", F_SER, 12, color=GRAY); fmt(p, after=30)

    # Signature : photo + nom
    table = doc.add_table(rows=1, cols=2)
    no_border_table(table)
    table.columns[0].width = Cm(3.5)
    table.columns[1].width = Cm(12)

    if os.path.exists(PHOTO):
        pp = table.cell(0,0).paragraphs[0]
        fmt(pp, align=WD_ALIGN_PARAGRAPH.LEFT)
        pp.add_run().add_picture(PHOTO, width=Cm(3.0))

    tp = table.cell(0,1).paragraphs[0]; fmt(tp, before=10)
    rn(tp, "João Silva\n",                                        F_SER, 14, color=INK)
    rn(tp, "joaosilva1979.substack.com\n",                       F_SAN, 9,  color=GRAY)
    rn(tp, "linkedin.com/in/joaosilva-commarketeer\n",           F_SAN, 9,  color=GRAY)
    rn(tp, "joaofmsilva1979.github.io/angles-morts\n",           F_SAN, 9,  color=GRAY)
    rn(tp, "#MarqueQuiTient",                                     F_SAN, 9,  color=RED)

    pg_break(doc)


# ── TOC ─────────────────────────────────────────────────

def toc(doc, chapters):
    spacer(doc, 36)
    p = doc.add_paragraph()
    rn(p, "TABLE DES MATIÈRES", F_SAN, 9, color=GRAY, caps=True, bold=True); fmt(p, after=28)

    for num, title in chapters:
        p = doc.add_paragraph()
        rn(p, f"{num:02d}  ", F_SER, 13, bold=True, color=LGRAY)
        rn(p, title,          F_SER, 13, color=INK); fmt(p, before=3, after=3)

    for extra in ["Conclusion", "Sources de référence"]:
        p = doc.add_paragraph()
        rn(p, f"      {extra}", F_SER, 13, color=GRAY); fmt(p, before=3, after=3)

    pg_break(doc)


# ── Chapter opener ───────────────────────────────────────

def ch_opener(doc, num, title, s1=None):
    p = doc.add_paragraph()
    rn(p, f"{num:02d}", F_SER, 108, color=LGRAY); fmt(p, before=20, after=0)

    p = doc.add_paragraph()
    inline(p, title, F_SER, 27, color=INK, bold=True); fmt(p, before=4, after=14)

    rule(doc, "1A1A1A", sz=6, before=0, after=16)

    if s1 and os.path.exists(s1):
        add_img(doc, s1, 8, before=0, after=20)
    else:
        spacer(doc, 10)


def title_block(doc, text):
    p = doc.add_paragraph()
    inline(p, text, F_SER, 27, color=INK, bold=True); fmt(p, before=28, after=18)
    rule(doc, "1A1A1A", sz=6, before=0, after=0); spacer(doc, 14)


# ── Blocs corps ─────────────────────────────────────────

def section_h(doc, text):
    p = doc.add_paragraph()
    inline(p, text, F_SER, 15, color=INK, bold=True); fmt(p, before=20, after=5)

def body_p(doc, text):
    p = doc.add_paragraph()
    inline(p, text, F_SAN, 10.5, color=INK); fmt(p, after=7, ls=16.5)

def add_hyperlink(para, url, size=10.5):
    """Insère un hyperlien cliquable (bleu souligné)."""
    r_id = para.part.relate_to(url, _HL, is_external=True)
    hl   = OxmlElement('w:hyperlink')
    hl.set(qn('r:id'), r_id)
    run  = OxmlElement('w:r')
    rPr  = OxmlElement('w:rPr')
    for tag, attrs in [
        ('w:rFonts', {qn('w:ascii'): F_SAN, qn('w:hAnsi'): F_SAN}),
        ('w:sz',     {qn('w:val'): str(int(size * 2))}),
        ('w:color',  {qn('w:val'): '1B4F8C'}),
        ('w:u',      {qn('w:val'): 'single'}),
    ]:
        el = OxmlElement(tag)
        for k, v in attrs.items(): el.set(k, v)
        rPr.append(el)
    run.append(rPr)
    t = OxmlElement('w:t')
    t.text = url
    t.set(qn('xml:space'), 'preserve')
    run.append(t)
    hl.append(run)
    para._p.append(hl)

def tagline_p(doc, text):
    """Tagline 'Celui où...' — Cormorant Garamond, gris, italique, avant le premier H3."""
    p = doc.add_paragraph()
    inline(p, text, F_SER, 14, color=GRAY, italic=True)
    fmt(p, before=0, after=20)

def bullet_p(doc, text):
    """Bullet avec détection URL → hyperlien cliquable."""
    p = doc.add_paragraph()
    rn(p, "–  ", F_SAN, 10.5, color=GRAY)
    url_m = re.search(r'(https?://\S+)$', text)
    if url_m:
        inline(p, text[:url_m.start()].rstrip(' :'), F_SAN, 10.5, color=INK)
        rn(p, " : ", F_SAN, 10.5, color=GRAY)
        add_hyperlink(p, url_m.group(1), size=10.5)
    else:
        inline(p, text, F_SAN, 10.5, color=INK)
    fmt(p, before=2, after=2, ls=15, indent=0.3)

def questions(doc, items):
    rule(doc, "8B1A1A", sz=3, before=18, after=0)
    p = doc.add_paragraph()
    rn(p, "4 QUESTIONS POUR COMMENCER", F_SAN, 8, color=RED, caps=True, bold=True)
    fmt(p, before=10, after=10)
    for i, q in enumerate(items, 1):
        p = doc.add_paragraph()
        rn(p, f"{i}.  ", F_SER, 12, bold=True, color=RED)
        rn(p, q, F_SER, 12, italic=True, color=INK); fmt(p, before=3, after=5, ls=17)
    spacer(doc, 6)


# ── Parser ───────────────────────────────────────────────

def render_body(doc, lines, start, end, mid_img=None):
    """
    Rend les lignes [start, end[.
    mid_img : chemin slide 2, inséré après le 1er heading ### de contenu.
    """
    i = start; q_buf = []; in_q = False; mid_done = False

    def flush_q():
        nonlocal q_buf, in_q
        if q_buf: questions(doc, q_buf); q_buf = []
        in_q = False

    while i < end:
        line = lines[i].rstrip(); i += 1

        if line.strip() == '---': flush_q(); continue
        if line.startswith('## '): flush_q(); continue
        if line.startswith('> '):
            flush_q(); tagline_p(doc, line[2:].strip()); continue

        if line.startswith('### '):
            text = line[4:].strip()
            if re.search(r'4 questions?', text, re.I):
                flush_q(); in_q = True
            else:
                flush_q(); section_h(doc, text)
                # Insérer slide 2 après le 1er vrai heading
                if not mid_done and mid_img and os.path.exists(mid_img):
                    add_img(doc, mid_img, 9, before=14, after=14)
                    mid_done = True
            continue

        if not line: continue

        m_num = re.match(r'^(\d+)\.\s+(.*)', line)
        if m_num:
            text = m_num.group(2).strip()
            if in_q: q_buf.append(text)
            else: body_p(doc, f"{m_num.group(1)}.  {text}")
            continue

        if re.match(r'^[-•]\s+', line):
            flush_q(); bullet_p(doc, re.sub(r'^[-•]\s+', '', line)); continue

        flush_q(); body_p(doc, line)

    flush_q()


# ── Page de fin ─────────────────────────────────────────

def end_page(doc):
    pg_break(doc)

    # Photo João — pleine largeur
    if os.path.exists(PHOTO):
        add_img(doc, PHOTO, 10, before=20, after=28)

    rule(doc, "8B1A1A", sz=6, before=0, after=18)

    # Slogan partie 1
    p = doc.add_paragraph()
    rn(p, "LE CADRE FAIT LA DIFFÉRENCE.", F_SER, 22, bold=True, color=INK, caps=True)
    fmt(p, after=14, align=WD_ALIGN_PARAGRAPH.CENTER)

    # Slogan partie 2
    p = doc.add_paragraph()
    rn(p, "…et une crise ne teste jamais votre communication.\n"
          "Elle teste tout ce qu'il y avait derrière,\n"
          "depuis le premier épisode.",
       F_SER, 15, italic=True, color=GRAY)
    fmt(p, after=36, align=WD_ALIGN_PARAGRAPH.CENTER)

    # Logo
    if os.path.exists(LOGO):
        add_img(doc, LOGO, 2.8, before=0, after=12)

    # URL
    p = doc.add_paragraph()
    rn(p, "joaosilva1979.substack.com", F_SAN, 9, color=GRAY)
    fmt(p, after=2, align=WD_ALIGN_PARAGRAPH.CENTER)
    p = doc.add_paragraph()
    rn(p, "#MarqueQuiTient", F_SAN, 9, color=RED)
    fmt(p, after=0, align=WD_ALIGN_PARAGRAPH.CENTER)


# ── Main ─────────────────────────────────────────────────

def main():
    print("Extraction slides…")
    extract_slides()

    with open(MD, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')

    chapters = []; specials = []
    for i, line in enumerate(lines):
        m = re.match(r'^## Chapitre (\d+)\s*[:—–-]+\s*(.+)', line)
        if m:
            chapters.append((int(m.group(1)), m.group(2).strip(), i)); continue
        if line.startswith('## '):
            label = line[3:].strip()
            if any(k in label.lower() for k in ('conclusion', 'sources')):
                specials.append((label, i))

    intro_start = next(i for i, l in enumerate(lines) if l.startswith('### '))
    intro_end   = chapters[0][2] if chapters else len(lines)

    all_sec = [(n, t, idx, 'ch') for n, t, idx in chapters]
    all_sec += [(0, lbl, idx, 'sp') for lbl, idx in specials]
    all_sec.sort(key=lambda x: x[2])

    doc = Document()
    for sec in doc.sections:
        sec.page_width = Cm(21); sec.page_height = Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(2.8)
        sec.top_margin  = sec.bottom_margin = Cm(2.6)

    sty = doc.styles['Normal']
    sty.font.name = F_SAN; sty.font.size = Pt(10.5)
    sty.paragraph_format.space_before = Pt(0)
    sty.paragraph_format.space_after  = Pt(0)

    cover(doc)
    toc(doc, [(n, t) for n, t, _, k in all_sec if k == 'ch'])

    # Introduction (sans slide)
    p = doc.add_paragraph()
    rn(p, "Introduction", F_SER, 27, bold=True, color=INK); fmt(p, before=20, after=18)
    rule(doc, "1A1A1A", sz=6, before=0, after=0); spacer(doc, 14)
    render_body(doc, lines, intro_start, intro_end)

    # Chapitres
    for idx_s, (num, title, line_i, kind) in enumerate(all_sec):
        pg_break(doc)
        end_i = all_sec[idx_s+1][2] if idx_s+1 < len(all_sec) else len(lines)

        if kind == 'ch':
            s1 = f"{SLIDES}/ep{num:02d}_s1.png"
            s2 = f"{SLIDES}/ep{num:02d}_s2.png"
            ch_opener(doc, num, title, s1)
            render_body(doc, lines, line_i+1, end_i, mid_img=s2)
        else:
            title_block(doc, title)
            render_body(doc, lines, line_i+1, end_i)

    end_page(doc)
    doc.save(OUT)
    print(f"\n✓  {OUT}")

if __name__ == '__main__':
    main()
