# FreeConvert — free, SEO-optimized converter + calculator site

A zero-cost website that pulls organic search traffic via **programmatic SEO** and
monetizes with **lenient ad networks** (Adsterra / PropellerAds / Monetag).

- ~17,700 static HTML pages (11 categories × unit pairs + long-tail values + 6 calculators)
- Hosting cost: **$0** (Cloudflare Pages, unlimited bandwidth, free SSL + analytics)
- No backend, no database, no API keys. Pure static = instant, crawlable, cheap.

## Local preview
```
python3 build.py            # regenerate /public
python3 -m http.server 8099 --directory public
# open http://localhost:8099
```

## Deploy free (Cloudflare Pages)
1. Create a GitHub repo and `git push` this folder.
2. Cloudflare Dashboard → Workers & Pages → Create → Pages → connect the repo.
3. Build settings: **Framework = None**, Build command = `python3 build.py`,
   Build output directory = `public`.
4. Deploy. You get a `*.pages.dev` domain free, unlimited bandwidth.
5. (Optional) Buy a custom domain at Cloudflare Registrar (~$1–10/yr .xyz), add it,
   and update `SITE` in `build.py` before rebuilding so sitemap URLs match.

## Submit to search engines
- Cloudflare Pages gives free analytics (no setup).
- Google Search Console → add site → submit `https://<yours>/sitemap.xml`.
- Bing Webmaster Tools → same.

## Monetize (lenient networks — instant/no traffic minimum)
Sign up (no minimum traffic for these), then paste their ad `<script>`/tag into the
`AD SPACE` placeholder in `build.py` (`ad_slot()` function) and rebuild.

| Network | Approval | Min payout | Good formats |
|---|---|---|---|
| Adsterra   | Instant  | $5   | Native, Social Bar, Popunder, Interstitial |
| PropellerAds | Fast   | $5   | Interstitial, Push, Native, Dialog |
| Monetag    | 1–2 days | $25  | SmartLink, Push, Popunder |

Tip: layer two (e.g. Adsterra Native + PropellerAds Push) so every visitor type earns.
These networks pay for global traffic incl. Africa/Asia/LatAm — keep pages useful & fast.

## Notes / risks
- Google rewards genuinely useful, fast, schema'd pages. Don't spin low-value text —
  every page here shows a real computed answer (that's the value).
- To scale traffic: add more unit categories in `build.py` → `CATS`, or more `PRESETS`.
- Keep the ~20k file cap in mind (Cloudflare free limit); 17.7k is comfortably under.
