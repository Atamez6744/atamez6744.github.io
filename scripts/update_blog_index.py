#!/usr/bin/env python3
"""
Scans blog/*.html for posts that aren't yet linked from blog/index.html and
appends a card for each one it finds. Existing cards are never touched or
reordered - this only adds what's missing, so any hand-curated ordering or
featured post stays exactly as-is.
"""
import datetime
import glob
import html
import os
import re
import sys

BLOG_DIR = os.path.join(os.path.dirname(__file__), "..", "blog")
INDEX_PATH = os.path.join(BLOG_DIR, "index.html")
ACCENTS = ["accent-terracotta", "accent-navy", "accent-sage"]

CARD_TEMPLATE = """        <!-- Post (auto-published) -->
        <a href="{href}" class="blog-card">
            <div class="card-accent {accent}"></div>
            <div class="card-body">
                <div class="card-tags">
{tags}
                </div>
                <h2 class="card-title">{title}</h2>
                <p class="card-excerpt">{excerpt}</p>
                <div class="card-footer">
                    <span class="card-read-time">{read_time}</span>
                    <span class="card-link">Read post <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></span>
                </div>
            </div>
        </a>
"""


def strip_tags(text):
    return re.sub(r"<[^>]+>", "", text).strip()


def parse_post(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    title_match = re.search(r"<title>(.*?)\s*\|\s*Ale Tamez</title>", content)
    title = html.unescape(title_match.group(1)).strip() if title_match else os.path.basename(path)

    tags_block_match = re.search(r'<div class="article-tags">(.*?)</div>', content, re.DOTALL)
    tags = re.findall(r"<span>(.*?)</span>", tags_block_match.group(1)) if tags_block_match else []

    read_time_match = re.search(r'<span class="read-time">(.*?)</span>', content)
    read_time = read_time_match.group(1).strip() if read_time_match else ""

    date = None
    if read_time:
        date_str = read_time.split("&middot;")[0].strip()
        try:
            date = datetime.datetime.strptime(date_str, "%B %d, %Y")
        except ValueError:
            pass

    excerpt = ""
    body_match = re.search(r'<div class="article-body">(.*)', content, re.DOTALL)
    if body_match:
        p_match = re.search(r"<p>(.*?)</p>", body_match.group(1), re.DOTALL)
        if p_match:
            excerpt = strip_tags(p_match.group(1))
            if len(excerpt) > 200:
                excerpt = excerpt[:197].rsplit(" ", 1)[0] + "..."

    return {
        "title": title,
        "tags": tags,
        "read_time": read_time,
        "date": date,
        "excerpt": excerpt,
    }


def build_card(href, post, seed):
    accent = ACCENTS[hash(seed) % len(ACCENTS)]
    tags_html = "\n".join(f'                    <span class="card-tag">{html.escape(t)}</span>' for t in post["tags"]) \
        or '                    <span class="card-tag">Blog</span>'
    return CARD_TEMPLATE.format(
        href=href,
        accent=accent,
        tags=tags_html,
        title=html.escape(post["title"]),
        excerpt=html.escape(post["excerpt"]) or "New post.",
        read_time=post["read_time"] or "",
    )


def main():
    with open(INDEX_PATH, encoding="utf-8") as f:
        index_content = f.read()

    linked = set(re.findall(r'href="([a-zA-Z0-9\-_. ]+\.html)"\s+class="blog-card', index_content))

    all_posts = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(BLOG_DIR, "*.html"))
        if os.path.basename(p) != "index.html"
    )
    new_posts = [p for p in all_posts if p not in linked]

    if not new_posts:
        print("No new blog posts to publish.")
        return

    cards = []
    for filename in new_posts:
        post = parse_post(os.path.join(BLOG_DIR, filename))
        cards.append(build_card(filename, post, filename))
        print(f"Publishing: {filename} -> {post['title']}")

    insertion = "\n" + "\n".join(cards)
    new_content, count = re.subn(
        r'(\n\s*</div>\n\n\s*<!-- FOOTER -->)',
        insertion + r"\1",
        index_content,
        count=1,
    )
    if count == 0:
        print("ERROR: could not find blog grid closing tag to insert into.", file=sys.stderr)
        sys.exit(1)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    # Expose the list of newly published posts for the workflow's commit message.
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"published={', '.join(new_posts)}\n")


if __name__ == "__main__":
    main()
