#!/usr/bin/env python3
"""
Generates sitemap.xml so search engines can find every page on the site,
including new blog posts and tools, without anyone updating it by hand.

Run it locally with:   python3 scripts/build_sitemap.py
"""
import datetime
import glob
import os
import subprocess
from urllib.parse import quote

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE_URL = "https://alejandratamez.com/"
EXCLUDE = {"404.html"}
PRIORITY = {"index.html": "1.0", "about.html": "0.9", "projects.html": "0.9", "tools/index.html": "0.9", "blog/index.html": "0.8"}


def last_modified(path):
    """Use the last git commit date for the file; fall back to today."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if out:
            return out
    except (OSError, subprocess.CalledProcessError):
        pass
    return datetime.date.today().isoformat()


def url_for(rel):
    if rel == "index.html":
        return BASE_URL
    if rel.endswith("/index.html"):
        return BASE_URL + quote(rel[: -len("index.html")])
    return BASE_URL + quote(rel)


def main():
    pages = []
    for path in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if rel in EXCLUDE or rel.startswith(".") or "/." in rel:
            continue
        pages.append(rel)
    pages.sort(key=lambda r: (PRIORITY.get(r) is None, r))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for rel in pages:
        lines += [
            "  <url>",
            f"    <loc>{url_for(rel)}</loc>",
            f"    <lastmod>{last_modified(rel)}</lastmod>",
            f"    <priority>{PRIORITY.get(rel, '0.7')}</priority>",
            "  </url>",
        ]
    lines.append("</urlset>")

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote sitemap.xml with {len(pages)} pages.")


if __name__ == "__main__":
    main()
