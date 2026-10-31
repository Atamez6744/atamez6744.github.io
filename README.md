# alejandratamez.com

**Alejandra (Ale) Tamez de la Garza**: GenAI Enablement Lead · Change Catalyst · Bridge Builder · Austin, TX

> *I translate complex systems into human possibility.*

This repository is my personal website, portfolio, and working toolkit. It's live at **[alejandratamez.com](https://alejandratamez.com)**, hosted on GitHub Pages, and hand-built with plain HTML, CSS, and JavaScript, with no frameworks.

I lead Generative AI enablement and change management, including taking Microsoft Copilot to **97% adoption across 10,000+ users** with a **200+ person Champions network** and **70+ training sessions**. This repo is where I build in public.

---

## 🧰 The Toolkit: frameworks you can click

The frameworks I use to drive AI adoption, rebuilt as free, interactive tools. No sign-up, no tracking, and nothing typed ever leaves the visitor's browser.

| Tool | What it answers | Flywheel phase |
|---|---|---|
| **[AI Adoption Flywheel Check](https://alejandratamez.com/tools/flywheel-readiness.html)** | *"Is our AI rollout building momentum or quietly losing it?"* A 16-question assessment with a momentum score, a radial chart, and a phase-by-phase action plan. | Listen |
| **[Prompt Builder (EN / ES)](https://alejandratamez.com/tools/prompt-builder.html)** | *"Why does Copilot keep giving me generic answers?"* A bilingual prompt coach using Goal, Context, Source, and Expectations, with live scoring, role templates, and follow-up prompts. | Enable |
| **[AI Value Calculator](https://alejandratamez.com/tools/ai-value-calculator.html)** | *"We hit 92% adoption. Why can't we show ROI?"* Follows the money from licenses to value, and prices the gap between *activated* and *habitual* users. | Measure |
| **[AI Use Case Prioritizer](https://alejandratamez.com/tools/use-case-prioritizer.html)** | *"We have 40 AI ideas. Which five first?"* Weighted scoring, an Impact vs. Ease map, editable weights, and CSV export. | Amplify |

The four tools map to the **Enablement Flywheel** (Listen → Enable → Measure → Amplify), the methodology behind my [Copilot Enablement at Scale case study](https://alejandratamez.com/case-studies/copilot-enablement-at-scale.html).

**How they're built:** single-file pages that share one stylesheet and one helper script ([`tools/toolkit.css`](tools/toolkit.css), [`tools/toolkit.js`](tools/toolkit.js)). Charts are hand-drawn SVG. State is saved to `localStorage` so work survives a refresh. Every tool is responsive down to phone width, keyboard-accessible, and prints cleanly to PDF.

---

## ⚙️ Automation

Part of my 2026 learning goal: automate anything I do more than twice.

| Workflow | What it does |
|---|---|
| [`publish-blog-posts.yml`](.github/workflows/publish-blog-posts.yml) | When I upload a new post to `blog/`, a Python script ([`update_blog_index.py`](scripts/update_blog_index.py)) reads its title, tags, date, and excerpt, adds a card to the blog index, rebuilds the sitemap, and commits the result. Publishing is just an upload. |
| [`site-quality.yml`](.github/workflows/site-quality.yml) | Runs on every pull request and push. [`check_site.py`](scripts/check_site.py) verifies that every internal link resolves and that every page has a title, meta description, viewport tag, language attribute, image alt text, and safe external links. It works like a spell checker for the website. |
| [`build_sitemap.py`](scripts/build_sitemap.py) | Generates `sitemap.xml` from every page, with real last-modified dates from git history, so search engines find new content automatically. |

All scripts use only the Python standard library, with no dependencies to install or maintain.

```bash
python3 scripts/check_site.py      # run the quality check locally
python3 scripts/build_sitemap.py   # regenerate the sitemap
python3 -m http.server             # preview the site at http://localhost:8000
```

---

## 🗺️ What's inside

```
├── index.html                  Home: who I am, how I work, featured work
├── about.html                  Story, experience, certifications
├── projects.html               Portfolio of projects and impact
├── case-studies/               Long-form project write-ups
├── blog/                       Writing on AI, people, and change
├── tools/                      The interactive Toolkit (4 tools + hub)
├── scripts/                    Python automation (blog publishing, QA, sitemap)
├── .github/workflows/          GitHub Actions that run the automation
├── 404.html                    A friendlier dead end
└── Alejandra_Tamez_Resume.pdf
```

---

## 🤝 Let's connect

- 🌐 [alejandratamez.com](https://alejandratamez.com)
- 💼 [LinkedIn](https://www.linkedin.com/in/alejandra-tamez-delagarza/)
- ✉️ [hola@alejandratamez.com](mailto:hola@alejandratamez.com)
- 📄 [Resume (PDF)](Alejandra_Tamez_Resume.pdf)

*"My superpower is connection. Everything else is just logistics."*

© 2026 Alejandra Tamez de la Garza. All rights reserved.
