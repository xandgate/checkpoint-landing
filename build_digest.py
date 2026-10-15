#!/usr/bin/env python3
"""
build_digest.py — Render Heed's Agentic Ops Digest from vault markdown into
static pages on the takeheed.ai landing site.

Input :  ~/vault/100 - Projects/Heed/Newsletter Drafts/*.md  (YYYY-MM-DD.md)
Output:  digest/<date>.html, digest/index.html, digest/rss.xml
Style :  mirrors index.html design tokens (dark, Inter, green accent).

Usage: python3 build_digest.py [--vault PATH] [--out PATH]
"""
import argparse
import html as htmllib
import os
import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime

try:
    import markdown
except ImportError:
    sys.exit("pip install markdown")

SITE = "https://takeheed.ai"
DEFAULT_VAULT = os.path.expanduser("~/vault/100 - Projects/Heed/Newsletter Drafts")

# ── parsing ────────────────────────────────────────────────────────────────

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)

def parse_issue(path):
    raw = open(path, encoding="utf-8").read()
    fm = {}
    m = FRONTMATTER_RE.match(raw)
    body = raw
    if m:
        body = raw[m.end():]
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    # strip cron-transcript scaffolding ("# Cron Job: ... / ## Prompt / ## Response")
    # so internal prompt text never reaches the public site
    if re.search(r"^#\s*Cron Job:", body, re.M):
        resp = re.search(r"^## Response\s*$", body, re.M)
        body = body[resp.end():] if resp else ""
    date_str = fm.get("createdAt") or os.path.splitext(os.path.basename(path))[0]
    try:
        date = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        sys.exit(f"bad date in {path}: {date_str}")
    h1 = H1_RE.search(body)
    title = h1.group(1).strip() if h1 else f"Agentic Ops Digest — {date_str}"
    # strip the leading H1 so it isn't duplicated by the template
    if h1:
        body = (body[:h1.start()] + body[h1.end():]).lstrip("\n")
    # first italic-only line as deck/tagline
    deck = None
    dm = re.search(r"^\*(.+?)\*\s*$", body, re.MULTILINE)
    if dm and len(dm.group(1)) < 200:
        deck = dm.group(1).strip()
        body = body[:dm.start()] + body[dm.end():]
    md = markdown.Markdown(extensions=["extra", "sane_lists", "smarty"])
    content = md.convert(body)
    return {"date": date, "date_str": date_str, "title": title,
            "deck": deck, "content": content, "slug": date.strftime("%Y-%m-%d")}

# ── templates ──────────────────────────────────────────────────────────────

CSS = """
:root {
  --bg:#080808; --surface:#101010; --surface-2:#161616; --border:#1f1f1f;
  --border-2:#2a2a2a; --text:#f0f0f0; --muted:#606060; --muted-2:#888;
  --accent:#4ade80; --accent-dim:rgba(74,222,128,.08); --code-bg:#0c0c0c;
  --radius:8px;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;
     font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.container{max-width:760px;margin:0 auto;padding:0 24px}
nav{border-bottom:1px solid var(--border);background:rgba(8,8,8,.85);backdrop-filter:blur(12px)}
.nav-inner{display:flex;align-items:center;justify-content:space-between;height:60px}
.logo{font-size:1.1rem;font-weight:700;color:var(--text);text-decoration:none}
.logo span{color:var(--accent)}
.nav-links{display:flex;gap:24px}
.nav-links a{font-size:.88rem;color:var(--muted-2);text-decoration:none}
.nav-links a:hover{color:var(--text)}
.label{display:inline-block;font-size:.72rem;font-weight:600;letter-spacing:.1em;
       text-transform:uppercase;color:var(--accent);margin-bottom:12px}
.issue-date{color:var(--muted);font-size:.85rem;margin-bottom:32px;font-family:'JetBrains Mono',monospace}
h1{font-size:clamp(1.7rem,4vw,2.4rem);font-weight:700;line-height:1.15;letter-spacing:-.02em;margin-bottom:12px}
.deck{color:var(--muted-2);font-style:italic;margin-bottom:40px}
.prose{padding:48px 0 32px}
.prose h2{font-size:1.4rem;font-weight:700;letter-spacing:-.02em;margin:48px 0 16px;
          padding-bottom:10px;border-bottom:1px solid var(--border)}
.prose h3{font-size:1.1rem;font-weight:600;margin:32px 0 10px}
.prose p{color:var(--muted-2);line-height:1.75;margin-bottom:16px}
.prose a{color:var(--accent);text-decoration:none}
.prose a:hover{text-decoration:underline}
.prose ul,.prose ol{margin:0 0 16px 24px;color:var(--muted-2)}
.prose li{margin-bottom:6px;line-height:1.7}
.prose blockquote{border-left:3px solid var(--accent);background:var(--accent-dim);
                  padding:14px 18px;border-radius:0 var(--radius) var(--radius) 0;
                  margin:0 0 16px;color:var(--muted-2)}
.prose code{font-family:'JetBrains Mono',monospace;font-size:.85em;background:var(--code-bg);
            border:1px solid var(--border);border-radius:4px;padding:2px 6px;color:#a7f3d0}
.prose pre{background:var(--code-bg);border:1px solid var(--border);border-radius:var(--radius);
           padding:16px;overflow-x:auto;margin-bottom:16px}
.prose pre code{border:none;padding:0;background:transparent}
.prose table{width:100%;border-collapse:collapse;margin:0 0 20px;font-size:.9rem}
.prose th{text-align:left;color:var(--text);font-weight:600;border-bottom:1px solid var(--border-2);padding:8px 12px 8px 0}
.prose td{color:var(--muted-2);border-bottom:1px solid var(--border);padding:8px 12px 8px 0}
.cta{background:var(--surface);border:1px solid var(--border);border-radius:14px;
     padding:28px;margin:24px 0 80px;display:flex;justify-content:space-between;
     align-items:center;gap:24px;flex-wrap:wrap}
.cta h3{font-size:1.05rem;margin-bottom:4px}
.cta p{font-size:.85rem;color:var(--muted)}
.btn{display:inline-flex;align-items:center;font-size:.9rem;font-weight:600;
     padding:10px 20px;border-radius:var(--radius);text-decoration:none;
     background:var(--accent);color:#000;white-space:nowrap}
.btn:hover{opacity:.9}
.issue-list{list-style:none;padding:8px 0 80px}
.issue-list li{border-bottom:1px solid var(--border);padding:20px 0;display:flex;
               justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap}
.issue-list a{color:var(--text);text-decoration:none;font-weight:600;font-size:1.05rem}
.issue-list a:hover{color:var(--accent)}
.issue-list .meta{color:var(--muted);font-family:'JetBrains Mono',monospace;font-size:.8rem}
.hero{padding:80px 0 24px}
.hero p{margin-top:12px;max-width:560px}
footer{border-top:1px solid var(--border);padding:28px 0 40px;color:var(--muted);font-size:.82rem}
footer a{color:var(--muted-2);text-decoration:none}
@media (max-width:640px){.cta{flex-direction:column;align-items:flex-start}}
"""

def page_head(title, desc):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Heed</title>
  <meta name="description" content="{desc}" />
  <link rel="alternate" type="application/rss+xml" title="Agentic Ops Digest" href="{SITE}/digest/rss.xml" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>{CSS}</style>
</head>
<body>
<nav><div class="container nav-inner">
  <a class="logo" href="/">heed<span>.</span></a>
  <div class="nav-links">
    <a href="/">Product</a>
    <a href="/digest/">Digest</a>
    <a href="{SITE}/#pricing">Pricing</a>
  </div>
</div></nav>
<main class="container">
"""

FOOT = f"""</main>
<footer><div class="container">
  Heed — enforced governance for AI agents · <a href="{SITE}">takeheed.ai</a> ·
  <a href="mailto:hello@takeheed.ai">hello@takeheed.ai</a> ·
  <a href="/digest/rss.xml">RSS</a>
</div></footer>
</body>
</html>
"""

def cta_block():
    return f"""
<div class="cta">
  <div>
    <h3>Get the Agentic Ops Digest weekly</h3>
    <p>The agent-governance landscape, with the enforcement angle. No spam.</p>
  </div>
  <a class="btn" href="mailto:hello@takeheed.ai?subject=Subscribe%20to%20the%20Agentic%20Ops%20Digest">Subscribe</a>
</div>
<!-- TODO: replace mailto CTA with Buttondown/Loops embed once the list tool is chosen -->
"""

def render_issue(i):
    head = page_head(htmllib.escape(i["title"]),
                     htmllib.escape(i["deck"] or i["title"]))
    date_h = i["date"].strftime("%b %-d, %Y")
    return f"""{head}
<div class="hero">
  <span class="label">Agentic Ops Digest</span>
  <h1>{htmllib.escape(i["title"])}</h1>
  <div class="issue-date">{date_h}</div>
  {f'<div class="deck">{htmllib.escape(i["deck"])}</div>' if i["deck"] else ''}
</div>
<article class="prose">{i["content"]}</article>
{cta_block()}
{FOOT}"""

def render_index(issues):
    head = page_head("Agentic Ops Digest",
                     "Weekly curation of the AI-agent governance landscape, with the enforcement angle.")
    lis = "\n".join(
        f'<li><a href="/digest/{i["slug"]}">{htmllib.escape(i["title"])}</a>'
        f'<span class="meta">{i["date"].strftime("%Y-%m-%d")}</span></li>'
        for i in issues)
    return f"""{head}
<div class="hero">
  <span class="label">The Heed Digest</span>
  <h1>Agentic Ops Digest</h1>
  <p>Weekly curation of the AI-agent governance landscape — new tools, incidents,
     and research — each read through the question that actually matters:
     is it <em>enforceable</em>, or just cooperative?</p>
</div>
<ul class="issue-list">
{lis}
</ul>
{cta_block()}
{FOOT}"""

def render_rss(issues):
    now = format_datetime(datetime.now(timezone.utc))
    items = []
    for i in issues:
        link = f"{SITE}/digest/{i['slug']}"
        desc = i["deck"] or re.sub(r"<[^>]+>", " ", i["content"])[:200].strip()
        items.append(f"""    <item>
      <title>{htmllib.escape(i["title"])}</title>
      <link>{link}</link>
      <guid isPermaLink="true">{link}</guid>
      <pubDate>{format_datetime(i["date"])}</pubDate>
      <description>{htmllib.escape(desc)}</description>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Agentic Ops Digest — Heed</title>
    <link>{SITE}/digest/</link>
    <description>Weekly curation of the AI-agent governance landscape, with the enforcement angle.</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{SITE}/digest/rss.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""

# ── main ───────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=DEFAULT_VAULT)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "digest"))
    args = ap.parse_args()

    if not os.path.isdir(args.vault):
        sys.exit(f"vault dir not found: {args.vault}")

    files = sorted(f for f in os.listdir(args.vault) if f.endswith(".md"))
    issues = [parse_issue(os.path.join(args.vault, f)) for f in files]
    issues.sort(key=lambda i: i["date"], reverse=True)
    seen, deduped = set(), []
    for i in issues:  # stable sort ⇒ newest revision of a duplicate day wins
        if i["slug"] not in seen:
            seen.add(i["slug"])
            deduped.append(i)
    issues = deduped
    if not issues:
        sys.exit("no issues found")

    os.makedirs(args.out, exist_ok=True)
    open(os.path.join(args.out, "index.html"), "w", encoding="utf-8").write(render_index(issues))
    open(os.path.join(args.out, "rss.xml"), "w", encoding="utf-8").write(render_rss(issues))
    for i in issues:
        open(os.path.join(args.out, f"{i['slug']}.html"), "w", encoding="utf-8").write(render_issue(i))

    print(f"rendered {len(issues)} issues → {args.out}")
    for i in issues[:3]:
        print(f"  /digest/{i['slug']}  {i['title']}")

if __name__ == "__main__":
    main()
