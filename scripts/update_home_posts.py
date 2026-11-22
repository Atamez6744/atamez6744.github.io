#!/usr/bin/env python3
"""
Copies the newest posts from blog/index.html onto the home page.

The home page shows the first card on the blog page as a large featured post
and the next three as smaller cards. It rewrites only the part of index.html
between <!-- home-posts --> and <!-- /home-posts -->, so the home page stays in
step with the blog every time a post is added.
"""
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
BLOG_INDEX = os.path.join(ROOT, "blog", "index.html")
HOME = os.path.join(ROOT, "index.html")
COUNT = 4

ARROW = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"/></svg>'


def parse_cards(html):
    cards = []
    for m in re.finditer(r'<a href="([^"]+)" class="blog-card[^"]*">(.*?)</a>', html, re.S):
        href, body = m.group(1), m.group(2)
        img = re.search(r'<img src="\.\./([^"]+)" alt="([^"]*)"([^>]*)>', body)
        if img:
            size = re.search(r'width="(\d+)" height="(\d+)"', img.group(3))
            img = (img.group(1), img.group(2)) + (size.groups() if size else (None, None))
        cards.append({
            "href": "blog/" + href,
            "tags": re.findall(r'<span class="card-tag">(.*?)</span>', body),
            "title": re.search(r'<h2 class="card-title">(.*?)</h2>', body, re.S).group(1).strip(),
            "excerpt": re.search(r'<p class="card-excerpt">(.*?)</p>', body, re.S).group(1).strip(),
            "date": re.search(r'<span class="card-read-time">(.*?)</span>', body).group(1).strip(),
            "img": img,
        })
    return cards


def render(card, featured):
    cls = "home-post featured" if featured else "home-post"
    if card["img"]:
        cls += " has-image"
    out = [f'        <a href="{card["href"]}" class="{cls}">']
    if card["img"]:
        src, alt, w, h = card["img"]
        size = f' width="{w}" height="{h}"' if w else ""
        out.append(f'          <img src="{src}" alt="{alt}" class="home-post-image"{size} loading="lazy">')
    out.append('          <div class="home-post-body">')
    out.append('            <div class="blog-card-tags">')
    for t in card["tags"][:2]:
        out.append(f'              <span class="blog-tag">{t}</span>')
    out.append('            </div>')
    out.append(f'            <h3>{card["title"]}</h3>')
    out.append(f'            <p>{card["excerpt"]}</p>')
    out.append('            <div class="blog-card-footer">')
    out.append(f'              <span class="read-time">{card["date"]}</span>')
    out.append(f'              <span class="read-more">Read post {ARROW}</span>')
    out.append('            </div>')
    out.append('          </div>')
    out.append('        </a>')
    return "\n".join(out)


def main():
    cards = parse_cards(open(BLOG_INDEX, encoding="utf-8").read())[:COUNT]
    if not cards:
        sys.exit("No blog cards found in blog/index.html")
    block = "\n".join(render(c, i == 0) for i, c in enumerate(cards))
    home = open(HOME, encoding="utf-8").read()
    new = re.sub(r"<!-- home-posts -->.*?<!-- /home-posts -->",
                 lambda m: "<!-- home-posts -->\n" + block + "\n        <!-- /home-posts -->",
                 home, flags=re.S)
    if new == home:
        print("Home page posts already up to date.")
        return
    open(HOME, "w", encoding="utf-8").write(new)
    print("Home page now shows: " + ", ".join(c["href"] for c in cards))


if __name__ == "__main__":
    main()
