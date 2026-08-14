#!/usr/bin/env python3
"""Autonomous promotional / indexing helpers for FreeConvert.

Run from the repo root:
    python3 promo.py indexnow      # re-submit ALL sitemap URLs to IndexNow
    python3 promo.py social         # print ready-to-post social snippets

Nothing here needs the user's login — IndexNow proves ownership via the
key file deployed by build.py; social snippets are just text to copy.

Requires: build.py (for SITE / INDEXNOW_KEY / sitemap path).
"""
import os, json, sys, urllib.request
import build  # reuses SITE, INDEXNOW_KEY, PUB

SITEMAP = os.path.join(build.PUB, "sitemap.xml")
BATCH = 10000  # IndexNow allows up to 10k URLs per request


def _urls():
    import xml.etree.ElementTree as ET
    if not os.path.isfile(SITEMAP):
        build.main()  # generate if missing
    txt = open(SITEMAP, encoding="utf-8").read()
    return [loc.text for loc in ET.fromstring(txt).iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]


def indexnow():
    urls = _urls()
    print(f"IndexNow: {len(urls)} URLs total, submitting in batches of {BATCH}")
    sent = 0
    for i in range(0, len(urls), BATCH):
        chunk = urls[i:i + BATCH]
        payload = json.dumps({
            "host": build.SITE.split("//", 1)[1],
            "key": build.INDEXNOW_KEY,
            "keyLocation": f"{build.SITE}/{build.INDEXNOW_KEY}.txt",
            "urlList": chunk,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow", data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
        try:
            urllib.request.urlopen(req, timeout=30)
            sent += len(chunk)
            print(f"  batch {i // BATCH + 1}: OK ({len(chunk)} URLs)")
        except Exception as e:
            print(f"  batch {i // BATCH + 1}: FAILED {e}")
    print(f"IndexNow done: {sent}/{len(urls)} URLs submitted.")


def social():
    s = build.SITE
    print("# Copy-paste promo snippets\n")
    print("## X / Twitter")
    print(f"Free unit converters & calculators — 17,000+ instant pages (length, weight, temp, crypto, etc). No ads clutter, no signup. {s}")
    print("\n## Reddit (r/software, r/productivity, r/learnprogramming)")
    print(f"I built a free converter + calculator hub with 17k static SEO pages. Fast, no tracking, runs in-browser. Feedback welcome: {s}")
    print("\n## Hacker News (Show HN)")
    print(f"Show HN: FreeConvert — a $0 static-site unit converter & calculator hub (17k pages, GitHub Pages, Monetag ads). Source in comments.")
    print("\n## LinkedIn / Facebook")
    print(f"Looking for a no-nonsense unit converter? FreeConvert covers length, weight, temperature, volume, digital storage + everyday calculators — all free, no account needed: {s}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "social"
    {"indexnow": indexnow, "social": social}.get(cmd, social)()
