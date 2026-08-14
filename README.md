# FreeConvert — free, SEO-optimized converter + calculator site

A zero-cost website that pulls organic search traffic via **programmatic SEO** and
monetizes with **lenient ad networks** (Adsterra / PropellerAds / Monetag).

- ~17,300 static HTML pages (12 categories × unit pairs + long-tail values + 6 calculators)
- Hosting cost: **$0** (Cloudflare Pages, unlimited bandwidth, free SSL + analytics)
- No backend, no database, no API keys. Pure static = instant, crawlable, cheap.

## Local preview
```
python3 verify.py          # rebuild + assert math/SEO/schema/assets all pass
python3 -m http.server 8099 --directory public
# open http://localhost:8099
```

## Deploy free (Cloudflare Pages)
1. Create a GitHub repo and `git push` this folder (assets/ are committed — do not delete).
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
Sign up (no minimum traffic for these), then paste their ad snippets into the `ADS`
dict at the top of `build.py` and rebuild. Each page already has ad slots wired:

| Slot key            | Network      | Approval  | Min payout | Good format            |
|---------------------|--------------|-----------|------------|------------------------|
| `adsterra_native`   | Adsterra     | Instant   | $5         | Native / Social Bar    |
| `propeller_onclick` | PropellerAds | Fast      | $5         | OnClick / Interstitial |
| `monetag_smartlink` | Monetag      | 1–2 days  | $25        | SmartLink              |

Example Adsterra Native Banner snippet to paste into `ADS["adsterra_native"]`:
```html
<script type="text/javascript">
  atOptions = { key: "YOUR_KEY", format: "iframe", height: 250, width: 300,
    params: {} };
  document.write('<scr'+'ipt type="text/javascript" src="https://cdn.adsterra.com/'+...+'"></scr'+'ipt>');
</script>
```
(Replace with the exact code Adsterra gives you for your site.) Leave a key as `""`
to skip that slot. Tip: layer two networks (Native + Push) so every visitor earns.

## Notes / risks
- Google rewards genuinely useful, fast, schema'd pages. Every page shows a real
  computed answer (that's the value) — never spin low-value text.
- `public/assets/` (style.css, cats.js, conv.js, calc.js) are **hand-written and
  git-tracked**. `build.py` only regenerates `cats.js`; the clean-rebuild step
  preserves `assets/`. Do NOT `rm -rf public/assets`.
- Cloudflare free file cap ≈ 20k; this site uses ~17.3k. To grow, add unit pairs in
  `CATS` or `PRESETS`, or thin `PRESETS` if you approach the cap.
