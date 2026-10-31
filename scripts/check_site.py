#!/usr/bin/env python3
"""
Site quality check: a small, dependency-free "spell checker" for the website.

For every HTML page in the repo it verifies:
  * every internal link (href / src) points to a file that actually exists
  * the page has a <title>, a meta description, a viewport tag, and lang=""
  * every <img> has alt text (accessibility)
  * links that open a new tab use rel="noopener" (security)

Run it locally with:   python3 scripts/check_site.py
It exits with status 1 if anything is broken, which makes the GitHub Action fail.
"""
import glob
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP_SCHEMES = ("http", "https", "mailto", "tel", "data", "javascript")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.imgs_missing_alt, self.unsafe_blank = [], [], []
        self.has_title = self.has_desc = self.has_viewport = self.has_lang = False
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and a.get("lang"):
            self.has_lang = True
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            if a.get("name") == "description" and a.get("content"):
                self.has_desc = True
            if a.get("name") == "viewport":
                self.has_viewport = True
        if tag == "img" and not a.get("alt"):
            self.imgs_missing_alt.append(a.get("src", "?"))
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in (a.get("rel") or ""):
            self.unsafe_blank.append(a.get("href", "?"))
        for key in ("href", "src"):
            if a.get(key) and tag in ("a", "link", "script", "img", "source", "iframe"):
                self.links.append(a[key])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and data.strip():
            self.has_title = True


def resolve(page, link):
    """Return the filesystem path an internal link points to, or None for external links."""
    parsed = urlparse(link)
    if parsed.scheme in SKIP_SCHEMES or link.startswith("//") or link.startswith("#"):
        return None
    path = unquote(parsed.path)
    if not path:
        return None
    base = ROOT if path.startswith("/") else os.path.dirname(page)
    target = os.path.normpath(os.path.join(base, path.lstrip("/")))
    if path.endswith("/") or os.path.isdir(target):
        target = os.path.join(target, "index.html")
    return target


def main():
    pages = sorted(
        p for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
        if "/.git/" not in p and "/node_modules/" not in p
    )
    problems = []
    for page in pages:
        rel = os.path.relpath(page, ROOT)
        parser = PageParser()
        with open(page, encoding="utf-8") as f:
            parser.feed(f.read())

        is_redirect_or_404 = rel == "404.html"
        for check, ok in (
            ("missing <title>", parser.has_title),
            ("missing meta description", parser.has_desc or is_redirect_or_404),
            ("missing viewport meta tag", parser.has_viewport),
            ("missing lang attribute on <html>", parser.has_lang),
        ):
            if not ok:
                problems.append(f"{rel}: {check}")
        for src in parser.imgs_missing_alt:
            problems.append(f"{rel}: <img src=\"{src}\"> has no alt text")
        for href in parser.unsafe_blank:
            problems.append(f"{rel}: target=_blank link without rel=noopener -> {href}")
        for link in parser.links:
            target = resolve(page, link)
            if target and not os.path.exists(target):
                problems.append(f"{rel}: broken link -> {link}")

    print(f"Checked {len(pages)} pages.")
    if problems:
        print(f"\nFound {len(problems)} problem(s):")
        for p in problems:
            print("  ✗ " + p)
        return 1
    print("✓ All internal links resolve and every page passes the basics.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
