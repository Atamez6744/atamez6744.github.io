#!/usr/bin/env python3
"""
Builds the Spanish version of the site (es/) from the English pages.

How it works, in one analogy: the English pages are the master recipe,
i18n/es.txt is the translation dictionary, and this script is the cook.
It copies every English page into es/, swaps each English sentence for
its Spanish translation, fixes links so they point to the Spanish pages
(and to the shared images, styles, and resume), and adds the EN | ES
switch to the corner of every page in both languages.

Because the design lives only in the English pages, any design change
shows up in Spanish automatically. Only new *text* needs translating.

Usage:
    python3 scripts/build_spanish.py            # build es/ and update switches
    python3 scripts/build_spanish.py --missing  # also list every untranslated sentence

Dictionary format (i18n/es.txt): pairs of lines, separated by a blank line.
    en: Work With Me
    es: Trabaja conmigo
Use "es: =" when the text stays the same in Spanish (names, emails, brands).
Lines starting with # are comments.
"""
import glob
import html
import os
import re
import shutil
import sys
from urllib.parse import urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TM_PATH = os.path.join(ROOT, "i18n", "es.txt")
ES_DIR = "es"
SITE = "https://alejandratamez.com/"
EXCLUDE = {"404.html"}
# A page gets a Spanish version once at least this share of its text is translated.
# Pages already published in Spanish stay published; untranslated bits fall back to English.
MIN_COVERAGE = 0.9

INLINE = {"a", "strong", "em", "b", "i", "span", "br", "small", "sup", "sub", "code",
          "abbr", "mark", "u", "s", "time", "label", "q", "cite"}
SKIP_CONTENT = {"script", "style", "svg", "noscript"}
TRANSLATABLE_ATTRS = ("alt", "aria-label", "placeholder", "title")
HEAD_META = {"description", "og:title", "og:description", "twitter:title", "twitter:description"}
TOKEN_RE = re.compile(r"(<!--.*?-->|<[^>]+>)", re.S)
LETTERS_RE = re.compile(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]")


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def load_tm():
    tm = {}
    if not os.path.exists(TM_PATH):
        return tm
    en = None
    with open(TM_PATH, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("#") or not line.strip():
                continue
            if line.startswith("en: "):
                en = norm(line[4:])
            elif line.startswith("es: ") and en is not None:
                es = line[4:].strip()
                tm[en] = en if es == "=" else es  # "es: =" means "same in both languages"
                en = None
    return tm


def tag_name(tok):
    m = re.match(r"</?\s*([a-zA-Z0-9-]+)", tok)
    return m.group(1).lower() if m else ""


def is_end(tok):
    return tok.startswith("</")


def is_selfclosing(tok):
    return tok.endswith("/>") or tag_name(tok) in {"br", "img", "input", "meta", "link", "hr", "source"}


class Translator:
    def __init__(self, tm):
        self.tm = tm
        self.missing = []
        self.total = 0
        self.hits = 0

    def lookup(self, text):
        key = norm(text)
        if not key or not LETTERS_RE.search(re.sub(r"<[^>]+>|&[a-z]+;", "", key)):
            return None
        self.total += 1
        found = self.tm.get(key) or self.piecewise(text)
        if found:
            self.hits += 1
            return found
        self.missing.append(key)
        return None

    def piecewise(self, text):
        """Fallback: translate each run of text between tags on its own.

        Lets one dictionary entry like "Projects" cover every variation of a
        menu link, whatever folder its href points to.
        """
        parts = TOKEN_RE.split(text)
        if len(parts) < 2:
            return None
        out = []
        for part in parts:
            if part.startswith("<") or not LETTERS_RE.search(re.sub(r"&[a-z]+;", "", part)):
                out.append(self.attrs_quiet(part) if part.startswith("<") else part)
                continue
            t = self.tm.get(norm(part))
            if t is None:
                return None
            lead = part[: len(part) - len(part.lstrip())]
            trail = part[len(part.rstrip()):]
            out.append(lead + t + trail)
        return "".join(out)

    def attrs_quiet(self, tok):
        def repl(m):
            name, quote, value = m.group(1), m.group(2), m.group(3)
            t = self.tm.get(norm(html.unescape(value))) if name.lower() in TRANSLATABLE_ATTRS else None
            return f'{name}={quote}{html.escape(t, quote=True)}{quote}' if t else m.group(0)
        return re.sub(r'([a-zA-Z-]+)=(["\'])(.*?)\2', repl, tok)

    def attrs(self, tok):
        def repl(m):
            name, quote, value = m.group(1), m.group(2), m.group(3)
            if name.lower() not in TRANSLATABLE_ATTRS:
                return m.group(0)
            t = self.lookup(html.unescape(value))
            return f'{name}={quote}{html.escape(t, quote=True) if t else value}{quote}'
        return re.sub(r'([a-zA-Z-]+)=(["\'])(.*?)\2', repl, tok)

    def translate_page(self, src):
        tokens = TOKEN_RE.split(src)
        out, seg = [], []
        in_head = False
        skip_stack = []  # tags whose content we leave alone (script, style, svg, JS-translated blocks)

        def flush():
            if not seg:
                return
            joined = "".join(seg)
            seg.clear()
            core = joined.strip()
            text_only = re.sub(r"<[^>]+>", "", core)
            if not LETTERS_RE.search(text_only):
                out.append("".join(self.attrs(t) if t.startswith("<") else t for t in TOKEN_RE.split(joined)))
                return
            t = self.lookup(core)
            lead = joined[: len(joined) - len(joined.lstrip())]
            trail = joined[len(joined.rstrip()):]
            out.append(lead + t + trail if t else joined)

        for tok in tokens:
            if not tok:
                continue
            is_tag = tok.startswith("<") and not tok.startswith("<!--")
            name = tag_name(tok) if is_tag else ""

            if skip_stack:
                out.append(tok)
                if is_tag and name == skip_stack[-1][0]:
                    if is_end(tok):
                        skip_stack[-1][1] -= 1
                        if skip_stack[-1][1] == 0:
                            skip_stack.pop()
                    elif not is_selfclosing(tok):
                        skip_stack[-1][1] += 1
                continue

            if is_tag and name == "head":
                flush()
                in_head = not is_end(tok)
                out.append(tok)
                continue

            if in_head:
                out.append(self.head_tag(tok) if is_tag else tok)
                continue

            if is_tag and not is_end(tok) and (name in SKIP_CONTENT or re.search(r"\sdata-i18n(-html)?=", tok)):
                flush()
                out.append(self.attrs(tok))
                if not is_selfclosing(tok):
                    skip_stack.append([name, 1])
                continue

            if not is_tag and not tok.startswith("<!--"):
                seg.append(tok)
            elif is_tag and name in INLINE:
                seg.append(tok)
            else:
                flush()
                out.append(self.attrs(tok) if is_tag else tok)
        flush()
        result = "".join(out)
        # <title> text lives in the head; translate it separately.
        result = re.sub(r"<title>(.*?)</title>",
                        lambda m: f"<title>{self.lookup(m.group(1)) or m.group(1)}</title>", result, count=1, flags=re.S)
        return result

    def head_tag(self, tok):
        if tag_name(tok) != "meta":
            return tok
        key = re.search(r'(?:name|property)="([^"]+)"', tok)
        content = re.search(r'content="([^"]*)"', tok)
        if not key or not content or key.group(1) not in HEAD_META:
            return tok
        t = self.lookup(html.unescape(content.group(1)))
        if not t:
            return tok
        return tok.replace(content.group(0), f'content="{html.escape(t, quote=True)}"')


# ---------------------------------------------------------------- links

def resolve(page_rel, link):
    """Return (root-relative target path, suffix) for an internal link, or None for external."""
    p = urlparse(link)
    if p.scheme or link.startswith(("#", "//", "/")) or not p.path:
        return None
    target = os.path.normpath(os.path.join(os.path.dirname(page_rel), p.path)).replace(os.sep, "/")
    if p.path.endswith("/") or os.path.isdir(os.path.join(ROOT, target)):
        target = (target + "/index.html").lstrip("./") if target != "." else "index.html"
    suffix = ("?" + p.query if p.query else "") + ("#" + p.fragment if p.fragment else "")
    return target, suffix


def relpath(target, from_page):
    rel = os.path.relpath(os.path.join(ROOT, target), os.path.dirname(os.path.join(ROOT, from_page)))
    return rel.replace(os.sep, "/")


def rewrite_links(es_html, en_rel, es_pages):
    es_rel = f"{ES_DIR}/{en_rel}"

    def repl(m):
        attr, quote, link = m.group(1), m.group(2), m.group(3)
        r = resolve(en_rel, html.unescape(link))
        if not r:
            return m.group(0)
        target, suffix = r
        if target.endswith(".html") and target in es_pages:
            new = relpath(f"{ES_DIR}/{target}", es_rel)
            if new.endswith("index.html") and not urlparse(link).path.endswith("index.html"):
                new = new[: -len("index.html")] or "./"
        else:
            new = relpath(target, es_rel)
        return f"{attr}={quote}{new}{suffix}{quote}"

    return re.sub(r'\b(href|src)=(["\'])(.*?)\2', repl, es_html)


# ---------------------------------------------------------------- switch + hreflang

SWITCH_CSS = """<style id="lang-switch-css">
    .lang-switch { display: inline-flex; align-items: center; margin-left: 28px; border: 1.5px solid rgba(29,27,24,.18); border-radius: 50px; padding: 3px; font-size: .74rem; font-weight: 600; letter-spacing: .08em; line-height: 1; flex-shrink: 0; }
    .lang-switch a, .lang-switch span { padding: 6px 10px; border-radius: 50px; text-decoration: none; }
    .lang-switch span { background: #1D1B18; color: #fff; }
    .lang-switch a { color: #3A3631; }
    .lang-switch a:hover { color: #1D1B18; background: rgba(29,27,24,.07); }
    #navbar .nav-links, nav .nav-links { margin-left: auto; }
    @media (max-width: 768px) { .lang-switch { margin-left: auto; margin-right: 12px; } }
  </style>"""


def page_url(rel):
    if rel == "index.html":
        return SITE
    return SITE + (rel[: -len("index.html")] if rel.endswith("/index.html") else rel)


def switch_html(current, other_href):
    if current == "en":
        return (f'<div class="lang-switch" role="group" aria-label="Language / Idioma"><span aria-current="true">EN</span>'
                f'<a href="{other_href}" hreflang="es" lang="es" aria-label="Ver en español">ES</a></div>')
    return (f'<div class="lang-switch" role="group" aria-label="Idioma / Language"><a href="{other_href}" hreflang="en" lang="en" '
            f'aria-label="View in English">EN</a><span aria-current="true">ES</span></div>')


def strip_i18n(page_html):
    """Remove anything a previous build added, so running this twice changes nothing."""
    page_html = re.sub(r"\s*<!-- i18n:switch -->.*?<!-- /i18n:switch -->", "", page_html, flags=re.S)
    return re.sub(r"\s*<!-- i18n:head -->.*?<!-- /i18n:head -->", "", page_html, flags=re.S)


def inject(page_html, switch, alternates):
    page_html = strip_i18n(page_html)
    head_block = f"\n  <!-- i18n:head -->\n  {alternates}\n  {SWITCH_CSS}\n  <!-- /i18n:head -->"
    page_html = page_html.replace("</head>", head_block + "\n</head>", 1)
    # Put the switch right after the nav links list, inside the nav bar.
    m = re.search(r'(<ul class="nav-links"[^>]*>.*?</ul>)', page_html, re.S)
    if m:
        block = f"\n      <!-- i18n:switch -->{switch}<!-- /i18n:switch -->"
        page_html = page_html[: m.end()] + block + page_html[m.end():]
    return page_html


def alternates_html(en_rel):
    en, es = page_url(en_rel), page_url(f"{ES_DIR}/{en_rel}")
    return (f'<link rel="alternate" hreflang="en" href="{en}">\n  '
            f'<link rel="alternate" hreflang="es" href="{es}">\n  '
            f'<link rel="alternate" hreflang="x-default" href="{en}">')


# ---------------------------------------------------------------- main

def main():
    show_missing = "--missing" in sys.argv
    tm = load_tm()
    pages = sorted(
        os.path.relpath(p, ROOT).replace(os.sep, "/")
        for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
    )
    pages = [p for p in pages if not p.startswith(ES_DIR + "/") and p not in EXCLUDE and "/." not in p]

    # Pass 1: translate everything and decide which pages are ready for Spanish.
    built, report = {}, []
    for rel in pages:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
            src = strip_i18n(f.read())
        tr = Translator(tm)
        es_html = tr.translate_page(src)
        coverage = tr.hits / tr.total if tr.total else 1
        already = os.path.exists(os.path.join(ROOT, ES_DIR, rel))
        if coverage >= MIN_COVERAGE or already:
            built[rel] = es_html
        report.append((rel, coverage, tr.missing, rel in built))

    # Pass 2: fix links, add the switch, write files.
    es_pages = set(built)
    out_dir = os.path.join(ROOT, ES_DIR)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    for rel, es_html in built.items():
        es_html = es_html.replace('<html lang="en">', '<html lang="es">', 1)
        es_html = es_html.replace(f'content="{page_url(rel)}"', f'content="{page_url(ES_DIR + "/" + rel)}"')
        es_html = rewrite_links(es_html, rel, es_pages)
        es_html = inject(es_html, switch_html("es", relpath(rel, f"{ES_DIR}/{rel}")), alternates_html(rel))
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(es_html)

    # English pages get the switch too: to their Spanish twin, or to the Spanish home page.
    for rel in pages:
        path = os.path.join(ROOT, rel)
        with open(path, encoding="utf-8") as f:
            src = f.read()
        target = f"{ES_DIR}/{rel}" if rel in es_pages else f"{ES_DIR}/index.html"
        href = relpath(target, rel)
        alt = alternates_html(rel) if rel in es_pages else ""
        new = inject(src, switch_html("en", href), alt)
        if new != src:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new)

    print(f"Spanish site: {len(es_pages)} of {len(pages)} pages built into {ES_DIR}/")
    for rel, cov, missing, ok in report:
        flag = "✓" if ok else "·"
        print(f"  {flag} {rel:52s} {cov:6.0%} translated" + (f"  ({len(missing)} missing)" if missing else ""))
        if show_missing:
            for m in missing:
                print(f"        en: {m}")


if __name__ == "__main__":
    main()
