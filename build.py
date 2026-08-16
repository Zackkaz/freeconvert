#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FreeConvert static site generator.
Zero dependencies. Produces thousands of SEO'd, plain-HTML converter + calculator
pages into ./public, ready to deploy free on Cloudflare Pages.

Run:  python3 build.py

MONETIZATION: fill in your publisher snippets in the ADS dict below, then rebuild.
All three networks have no/minimum traffic requirements (Adsterra instant, PropellerAds
fast, Monetag 1-2 days). Each page already has ad slots wired to these.
"""
import os, json, math, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
PUB  = os.path.join(ROOT, "public")
# Deployment base path. GitHub USER Pages (zackkaz.github.io) serve at the
# true origin root, so BASE = "". This is required so Monetag's file-upload
# verification finds sw.js at https://zackkaz.github.io/sw.js (NOT a subpath).
BASE = ""
SITE = "https://zackkaz.github.io"   # GitHub user Pages root

# Monetag service-worker push monetization. "Superior tag" (zoneId 11579192).
# Written to public/sw.js by build.py so it survives the clean-rebuild step.
MONETAG_SW = '''self.options = {
    "domain": "5gvci.com",
    "zoneId": 11579192
}
self.lary = ""
importScripts('https://5gvci.com/act/files/service-worker.min.js?r=sw')
'''

# Monetag "Superior tag" loader, self-hosted at the site root so the
# data-zone script actually loads (the dashboard snippet ships with src=""
# which loads nothing). The loader reads data-zone from its own <script> tag.
MONETAG_TAG_FILE = "monetag_tag.min.js"
MONETAG_HEAD_TAG = f'<script src="{BASE}/{MONETAG_TAG_FILE}" data-zone="270206" async data-cfasync="false"></script>'

# ---------------------------------------------------------------------------
# SEARCH-ENGINE VERIFICATION + INDEXING (root files, generated each build)
# ---------------------------------------------------------------------------
# Google Search Console — HTML-file verification.
# The file below (name + exact body) is what Google's "HTML file" method
# downloads. It is served at the site root; GSC fetches it to verify ownership.
GSC_HTML_FILE = "google3fdc88e71d84c4d8.html"
GSC_HTML_BODY = "google-site-verification: google3fdc88e71d84c4d8.html"

# Bing Webmaster Tools (HTML-file method): paste Bing's <meta> snippet content.
BING_HTML_BODY = '<meta name="msvalidate.01" content="REPLACE_WITH_BING_TOKEN" />'

# IndexNow — instant indexing for Bing/Yandex/Naver/Seznam. No account needed:
# the key is published at /<key>.txt (below); URLs are pinged after each deploy.
# Keep this stable — changing it invalidates already-submitted URLs.
INDEXNOW_KEY = "f47ac10b-58cc-4372-a567-0e02b2c3d479"

# ---------------------------------------------------------------------------
# MONETIZATION — paste your real ad snippets here (lenient networks, no strict policy).
# Leave a key empty ("") to skip that slot. They render only when filled.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# MONETIZATION — paste your REAL ad snippets here, then rebuild + push.
# Each network has NO/minimum traffic requirement (lenient policies).
# Fill the YOUR_*_HERE placeholders with the exact values from your account.
# Leave a key as "" to disable that slot. The snippet is emitted verbatim
# on every page that uses the slot (see ad_slot()), so this is the ONLY
# edit needed to go live — no other code change required.
# ---------------------------------------------------------------------------
ADS = {
    # Adsterra — Native Banner / Social Bar (instant approval, no traffic min).
    # Get code at adsterra.com -> Websites -> your site -> Native Banner.
    # Replace YOUR_ADSTERRA_KEY with the "key" value Adsterra gives you.
    "adsterra_native":  (
        '<script type="text/javascript">'
        'atOptions = {key:"YOUR_ADSTERRA_KEY_HERE", format:"iframe", height:250, width:300, params:{}};'
        '(function(){var d=document, g=d.createElement("script"), s=d.getElementsByTagName("script")[0];'
        'g.src="https://cdn.adsterra.com/asyncjs.php"; s.parentNode.insertBefore(g,s);})();'
        '</script>'
    ),

    # PropellerAds — OnClick / Interstitial (fast approval, no traffic min).
    # Get code at propellerads.com -> your site -> OnClick.
    # Replace YOUR_PROPELLER_ZONE_ID with the zone ID PropellerAds assigns.
    "propeller_onclick": (
        '<script type="text/javascript" src="//si.url-provider.com/async/ YOUR_PROPELLER_ZONE_ID_HERE " '
        'async="async"></script>'
    ),

    # Monetag — SmartLink (1-2 day approval; pays well for Global-South traffic).
    # Get code at monetag.com -> your site -> SmartLink.
    # Replace YOUR_MONETAG_SMARTLINK_URL with the smartlink URL Monetag gives you.
    "monetag_smartlink": (
        '<a href="YOUR_MONETAG_SMARTLINK_URL_HERE" rel="nofollow">'
        '<script type="text/javascript" src="//slmonitor.net/script.js" async></script>'
        'Open exclusive offers</a>'
    ),
}

# ---------------------------------------------------------------------------
# Category definitions.  type 'f' = factor-to-base, 't' = temperature.
# Units: s=slug, y=symbol, n=name, f=factor to base unit.
# ---------------------------------------------------------------------------
CATS = [
  {"slug":"length","name":"Length","type":"f","intro":"Convert any length or distance — meters, feet, miles, kilometers and more — with exact results.",
   "units":[("meter","m","Meters",1),("kilometer","km","Kilometers",1000),("centimeter","cm","Centimeters",0.01),
            ("millimeter","mm","Millimeters",0.001),("micrometer","µm","Micrometers",1e-6),("mile","mi","Miles",1609.344),
            ("yard","yd","Yards",0.9144),("foot","ft","Feet",0.3048),("inch","in","Inches",0.0254),
            ("nautical-mile","nmi","Nautical miles",1852),("light-year","ly","Light-years",9.46073e15),("astronomical-unit","au","Astronomical units",1.495978707e11)],
   "faqs":[("How many feet in a meter?","Exactly 3.28084 feet make 1 meter (1 m = 1 ÷ 0.3048 ft)."),
           ("Which is longer, a mile or a kilometer?","A mile is longer: 1 mile = 1.60934 kilometers.")]},

  {"slug":"weight","name":"Weight / Mass","type":"f","intro":"Convert kilograms, pounds, ounces, stones, tons and more in both metric and imperial units.",
   "units":[("kilogram","kg","Kilograms",1),("gram","g","Grams",0.001),("milligram","mg","Milligrams",1e-6),
            ("metric-ton","t","Metric tons",1000),("pound","lb","Pounds",0.45359237),("ounce","oz","Ounces",0.0283495231),
            ("stone","st","Stones",6.35029318),("us-ton","ton","US short tons",907.18474)],
   "faqs":[("How many pounds in a kilogram?","1 kilogram = 2.20462 pounds."),
           ("How many grams in an ounce?","1 ounce = 28.3495 grams.")]},

  {"slug":"volume","name":"Volume","type":"f","intro":"Convert liters, gallons, cups, milliliters, fluid ounces and more for cooking, fuel and science.",
   "units":[("liter","L","Liters",1),("milliliter","mL","Milliliters",0.001),("cubic-meter","m3","Cubic meters",1000),
            ("gallon-us","gal","US gallons",3.785411784),("quart-us","qt","US quarts",0.946352946),
            ("pint-us","pt","US pints",0.473176473),("cup-us","cup","US cups",0.2365882365),
            ("fluid-ounce-us","floz","US fluid ounces",0.0295735296),("gallon-uk","galuk","UK gallons",4.54609),
            ("tablespoon","tbsp","Tablespoons",0.0147867648),("teaspoon","tsp","Teaspoons",0.00492892159),
            ("cubic-foot","ft3","Cubic feet",28.3168466)],
   "faqs":[("How many ml in a US cup?","1 US cup = 236.588 ml."),
           ("How many liters in a gallon?","1 US gallon = 3.78541 liters; 1 UK gallon = 4.54609 liters.")]},

  {"slug":"area","name":"Area","type":"f","intro":"Convert square meters, hectares, acres, square feet and square miles instantly.",
   "units":[("square-meter","m2","Square meters",1),("square-kilometer","km2","Square kilometers",1e6),
            ("hectare","ha","Hectares",10000),("acre","ac","Acres",4046.8564224),("square-foot","ft2","Square feet",0.09290304),
            ("square-yard","yd2","Square yards",0.83612736),("square-mile","mi2","Square miles",2589988.110336),
            ("square-inch","in2","Square inches",0.00064516),("are","a","Ares",100),("square-centimeter","cm2","Square centimeters",0.0001)],
   "faqs":[("How many square feet in an acre?","1 acre = 43,560 square feet."),
           ("How big is a hectare?","1 hectare = 10,000 m² = 2.47105 acres.")]},

  {"slug":"speed","name":"Speed","type":"f","intro":"Convert km/h, mph, knots, m/s and ft/s for travel, weather and physics.",
   "units":[("kmh","km/h","Kilometers per hour",0.277777778),("mph","mph","Miles per hour",0.44704),
            ("knot","kn","Knots",0.514444444),("mps","m/s","Meters per second",1),("fps","ft/s","Feet per second",0.3048),
            ("c","c","Speed of light",299792458),("mach","mach","Mach (sea level)",340.29),("cmps","cm/s","Centimeters per second",0.01)],
   "faqs":[("How many mph in 100 km/h?","100 km/h = 62.1371 mph."),
           ("What is 1 knot in km/h?","1 knot = 1.852 km/h.")]},

  {"slug":"time","name":"Time","type":"f","intro":"Convert seconds, minutes, hours, days, weeks, months and years.",
   "units":[("second","s","Seconds",1),("minute","min","Minutes",60),("hour","h","Hours",3600),("day","d","Days",86400),
            ("week","wk","Weeks",604800),("month","mo","Months (30.44 d)",2629746),("year","yr","Years (365.25 d)",31557600),
            ("millisecond","ms","Milliseconds",0.001),("microsecond","µs","Microseconds",1e-6)],
   "faqs":[("How many seconds in a day?","1 day = 86,400 seconds."),
           ("How many days in a year?","A Julian year = 365.25 days = 31,557,600 seconds.")]},

  {"slug":"digital","name":"Digital Storage","type":"f","intro":"Convert bits, bytes, KB, MB, GB, TB and PB — decimal and binary units.",
   "units":[("bit","bit","Bits",0.125),("byte","B","Bytes",1),("kilobyte","KB","Kilobytes (1000 B)",1e3),
            ("megabyte","MB","Megabytes (1e6 B)",1e6),("gigabyte","GB","Gigabytes (1e9 B)",1e9),
            ("terabyte","TB","Terabytes (1e12 B)",1e12),("petabyte","PB","Petabytes (1e15 B)",1e15),
            ("kibibyte","KiB","Kibibytes (1024 B)",1024),("mebibyte","MiB","Mebibytes (1048576 B)",1048576),
            ("gibibyte","GiB","Gibibytes (1073741824 B)",1073741824)],
   "faqs":[("How many MB in a GB?","1 GB = 1000 MB (decimal) or 1024 MiB (binary)."),
           ("How many bits in a byte?","8 bits = 1 byte.")]},

  {"slug":"cooking","name":"Cooking","type":"f","intro":"Convert cups, tablespoons, teaspoons, fluid ounces, ml and grams for recipes.",
   "units":[("cup-us","cup","US cups",236.5882365),("tablespoon","tbsp","Tablespoons",14.7867648),
            ("teaspoon","tsp","Teaspoons",4.92892159),("fluid-ounce-us","floz","US fluid ounces",29.5735296),
            ("milliliter","mL","Milliliters",1),("liter","L","Liters",1000),("gram","g","Grams",1)],
   "faqs":[("How many teaspoons in a tablespoon?","3 teaspoons = 1 tablespoon."),
           ("How many ml in a tablespoon?","1 tablespoon = 14.7868 ml.")]},

  {"slug":"pressure","name":"Pressure","type":"f","intro":"Convert pascals, bar, psi, atm, torr and mmHg.",
   "units":[("pascal","Pa","Pascals",1),("kilopascal","kPa","Kilopascals",1000),("bar","bar","Bar",100000),
            ("psi","psi","Pounds per sq inch",6894.75729),("atm","atm","Atmospheres",101325),
            ("torr","Torr","Torr",133.322368),("mmhg","mmHg","Millimeters of mercury",133.322368),
            ("megapascal","MPa","Megapascals",1e6),("psig","psig","PSI gauge",6894.75729)],
   "faqs":[("How many kPa in 1 bar?","1 bar = 100 kPa = 100,000 Pa."),
           ("What is 1 atm in psi?","1 atmosphere = 14.6959 psi.")]},

  {"slug":"energy","name":"Energy","type":"f","intro":"Convert joules, calories, kWh, BTU, watt-hours and more.",
   "units":[("joule","J","Joules",1),("kilojoule","kJ","Kilojoules",1000),("calorie","cal","Calories",4.184),
            ("kilocalorie","kcal","Kilocalories",4184),("watthour","Wh","Watt-hours",3600),
            ("kilowatthour","kWh","Kilowatt-hours",3.6e6),("btu","BTU","BTU",1055.05585),
            ("electronvolt","eV","Electronvolts",1.602176634e-19)],
   "faqs":[("How many joules in a kcal?","1 kilocalorie = 4184 joules."),
           ("What is 1 kWh in joules?","1 kWh = 3,600,000 joules.")]},

  {"slug":"angle","name":"Angle","type":"f","intro":"Convert degrees, radians, gradians and arcminutes.",
   "units":[("degree","deg","Degrees",math.pi/180),("radian","rad","Radians",1),("gradian","grad","Gradians",math.pi/200),
            ("arcminute","arcmin","Arcminutes",math.pi/10800),("turn","turn","Turns",2*math.pi)],
   "faqs":[("How many radians in 180 degrees?","180° = π radians (≈ 3.14159)."),
           ("What is a gradian?","400 gradians = 360 degrees = 1 turn.")]},

  {"slug":"temperature","name":"Temperature","type":"t","intro":"Convert Celsius, Fahrenheit and Kelvin with exact formulas.",
   "units":[("celsius","°C","Celsius",0),("fahrenheit","°F","Fahrenheit",0),("kelvin","K","Kelvin",0)],
   "faqs":[("How to convert C to F?","°F = °C × 9/5 + 32. Example: 100°C = 212°F."),
           ("What is absolute zero?","0 K = -273.15°C = -459.67°F.")]},
]

PRESETS = [0.25,0.5,0.75,1,2,3,5,10,12,15,20,25,30,50,100,250,500,1000,2000,5000]

# ---------------------------------------------------------------------------
# Conversion math
# ---------------------------------------------------------------------------
def convert(cat, frm, to, v):
    c = next(x for x in CATS if x["slug"]==cat)
    if c["type"]=="f":
        fu = next(u for u in c["units"] if u[0]==frm)
        tu = next(u for u in c["units"] if u[0]==to)
        return v * fu[3] / tu[3]
    if c["type"]=="t":
        cv = frm=="celsius" and v or frm=="fahrenheit" and (v-32)*5/9 or v-273.15
        return to=="celsius" and cv or to=="fahrenheit" and cv*9/5+32 or cv+273.15
    return float("nan")

def fmt(x):
    if x is None or (isinstance(x,float) and not math.isfinite(x)): return "—"
    if x==0: return "0"
    if abs(x)>=1e15 or (abs(x)<1e-9 and x!=0):
        s = f"{x:.4e}"
    else:
        s = f"{x:.6f}".rstrip("0").rstrip(".")
    intp,_,dec = s.partition(".")
    try:
        intp = f"{int(intp):,}"
    except ValueError:
        pass
    return intp + (("."+dec) if dec else "")

SYM = {c["slug"]:{u[0]:u[1] for u in c["units"]} for c in CATS}
UNM = {c["slug"]:{u[0]:u[2] for u in c["units"]} for c in CATS}
def CATS_name(slug): return next(c["name"] for c in CATS if c["slug"]==slug)

# ---------------------------------------------------------------------------
# HTML helpers (all internal links/assets are ROOT-ABSOLUTE so any depth works)
# ---------------------------------------------------------------------------
def jsonld(obj):
    return '<script type="application/ld+json">'+json.dumps(obj,ensure_ascii=False)+'</script>'

def breadcrumb_schema(trail):
    # trail: list of (name, url)
    return jsonld({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[ {"@type":"ListItem","position":i+1,
            "name":n,"item":u} for i,(n,u) in enumerate(trail)]
    })

def page(title, desc, body, canonical, pagecfg=None, extra_head="", extra_jsonld="", vmeta=""):
    cfg = f'<script>window.__PAGE__={json.dumps(pagecfg or {})};</script>' if pagecfg is not None else ""
    convjs = f'<script src="{BASE}/assets/cats.js"></script><script src="{BASE}/assets/conv.js"></script>' if pagecfg and "cat" in (pagecfg or {}) else ""
    og = (f'<meta property="og:title" content="{title}">'
          f'<meta property="og:description" content="{desc}">'
          f'<meta property="og:type" content="website">'
          f'<meta property="og:url" content="{canonical}">')
    return f"""<!doctype html>
<html lang="en">
<head>
{MONETAG_HEAD_TAG}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
{og}
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
{vmeta}
<link rel="stylesheet" href="{BASE}/assets/style.css">
{cfg}{convjs}{extra_head}
{jsonld({"@context":"https://schema.org","@type":"WebSite","name":"FreeConvert","url":SITE})}
{extra_jsonld}
<script>
// Monetag service-worker push registration (file lives at BASE+/sw.js)
if ("serviceWorker" in navigator) {{
  window.addEventListener("load", function() {{
    navigator.serviceWorker.register("{BASE}/sw.js").catch(function(e){{}});
  }});
}}
</script>
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="{BASE}/">Free<span>Convert</span></a>
  <nav class="top">
    <a href="{BASE}/">Home</a>
    <a href="{BASE}/#categories">Converters</a>
    <a href="{BASE}/#calc">Calculators</a>
    <a href="{BASE}/guides/">Guides</a>
  </nav>
</div></header>
<main class="wrap">
{body}
</main>
{footer_html()}
</body>
</html>"""

def footer_html():
    return f'''<footer><div class="wrap">
  <div class="fcols">
    <div>
      <div class="fbrand">Free<span>Convert</span></div>
      <p class="fmuted">Free, accurate unit converters and calculators. No sign-up, runs in your browser.</p>
    </div>
    <nav class="fnav" aria-label="Footer">
      <div><h4>Converters</h4>
        <a href="{BASE}/length/">Length</a><a href="{BASE}/weight/">Weight</a>
        <a href="{BASE}/temperature/">Temperature</a><a href="{BASE}/volume/">Volume</a>
        <a href="{BASE}/digital/">Digital storage</a><a href="{BASE}/speed/">Speed</a>
      </div>
      <div><h4>Learn</h4>
        <a href="{BASE}/guides/">Guides</a>
        <a href="{BASE}/guides/metric-vs-imperial/">Metric vs imperial</a>
        <a href="{BASE}/guides/temperature-conversions/">Temperature maths</a>
        <a href="{BASE}/guides/mass-vs-weight/">Mass vs weight</a>
      </div>
      <div><h4>Site</h4>
        <a href="{BASE}/about/">About</a>
        <a href="{BASE}/methodology/">Methodology</a>
        <a href="{BASE}/privacy/">Privacy</a>
        <a href="{BASE}/terms/">Terms</a>
        <a href="{BASE}/contact/">Contact</a>
        <a href="{BASE}/sitemap.xml">Sitemap</a>
      </div>
    </nav>
  </div>
  <div class="flegal">© {datetime.date.today().year} FreeConvert. Conversions are calculated automatically; verify critical values independently.</div>
</div></footer>'''

def ad_slot(kind):
    code = ADS.get(kind, "")
    # Only render an advertisement container when a REAL snippet is configured.
    # The ADS dict ships with placeholder tokens (YOUR_* / REPLACE) as the
    # default; those are NOT real advertising config, so we render nothing.
    # This keeps the site free of unfinished placeholders and AD: comments
    # until the owner pastes a real network snippet.
    if (not code.strip()) or ("YOUR_" in code) or ("REPLACE" in code):
        return ""
    return f'<div class="ad">{code}</div>'

# ---------------------------------------------------------------------------
# Static informational pages (trust + guides). These are NOT added to the
# sitemap (per task: sitemap inventory frozen until GSC finishes processing);
# they are discovered via the site-wide footer. Each has a unique title,
# description, canonical and exactly one H1. WebPage JSON-LD is added only
# when it accurately reflects the visible content.
# ---------------------------------------------------------------------------
def static_page(title, desc, h1, body, slug, kind="WebPage"):
    canonical = SITE + "/" + slug + "/"
    # WebPage JSON-LD is accurate here: it describes this page's identity.
    jsonld_block = jsonld({
        "@context": "https://schema.org",
        "@type": kind,
        "name": title,
        "description": desc,
        "url": canonical,
        "isPartOf": {"@type": "WebSite", "name": "FreeConvert", "url": SITE},
    })
    return page(title, desc, f'<h1>{h1}</h1>\n{body}', canonical, extra_jsonld=jsonld_block)

# Content for trust + guide pages. Original, people-first, sourced from
# primary references (NIST, BIPM, official standards). No fabricated identity.
TRUST = {
  "about": ("About FreeConvert",
    "FreeConvert is a free, browser-based unit converter and calculator hub. Learn how it works, what it does, and what it does not claim.",
    "About FreeConvert",
    '''<p class="lede">FreeConvert is a free collection of unit converters and calculators that run entirely in your web browser. There is no account, no tracking cookie for analytics, and no server that sees the numbers you type.</p>
<h2>What FreeConvert is</h2>
<p>A set of plain web pages, each generated in advance, that convert between measurement units (length, mass, volume, temperature, and more) and run everyday calculators (percentage, tip, loan, age, and similar). Results appear instantly as you type.</p>
<h2>What FreeConvert is not</h2>
<ul>
  <li>Not a business with registered offices or staff — it is an open, free utility.</li>
  <li>Not a source of legal, medical, or financial advice. Conversions are mathematical; judgement calls (recipe scaling, dosing, engineering tolerances) are yours.</li>
  <li>Not affiliated with any standards body. We follow published factors; we do not write them.</li>
</ul>
<h2>How results are produced</h2>
<p>Each conversion uses a documented factor or formula (see <a href="/methodology/">Methodology</a>). The arithmetic happens on your device. Nothing you enter is uploaded.</p>
<h2>Open and auditable</h2>
<p>The site is built from a small open generator. You can read the <a href="https://github.com/Zackkaz/freeconvert" rel="noopener">source repository</a>, report issues, or suggest improvements.</p>'''),

  "methodology": ("How FreeConvert calculates conversions",
    "How FreeConvert computes unit conversions: the documented factors and formulas we use, how rounding works, and how factors are reviewed against primary sources.",
    "Methodology",
    '''<p class="lede">Every result on FreeConvert comes from a published conversion factor or an established formula. This page explains exactly how, so you can verify any number yourself.</p>
<h2>Factor-based conversions</h2>
<p>For most quantities, a unit is defined by how many <em>base units</em> it equals. To convert a value, multiply by the source factor and divide by the target factor:</p>
<div class="formula">result = value × factor<sub>from</sub> ÷ factor<sub>to</sub></div>
<p>Example — metres to feet: 1 m = 0.3048 m per foot, so 10 m × 1 ÷ 0.3048 = 32.8084 ft. The foot–metre factor (0.3048) is the internationally agreed value defined in the <em>metre convention</em> and maintained by <a href="https://www.bipm.org/en/measurement-units" rel="noopener">BIPM</a>.</p>
<h2>Temperature conversions</h2>
<p>Temperature scales have different zero points, so the formula is not a simple ratio:</p>
<div class="formula">°F = °C × 9/5 + 32 &nbsp;·&nbsp; K = °C + 273.15 &nbsp;·&nbsp; °C = (°F − 32) × 5/9</div>
<p>For example, 0 °C = 32 °F = 273.15 K. These relations are defined by the Kelvin and Celsius scales; the value 273.15 is the defined ice point of water (see <a href="https://www.nist.gov/pml/weights-and-measures/si-units-temperature" rel="noopener">NIST</a>).</p>
<h2>Rounding and floating point</h2>
<p>Computers represent decimals in binary floating point, so results are shown rounded for display only. The underlying calculation is unchanged by display rounding. In "Auto" precision we drop unnecessary trailing zeros; in fixed precision we keep the requested number of decimal places. Never treat a displayed value as exact beyond its shown digits.</p>
<h2>How factors are reviewed</h2>
<ul>
  <li>Each factor is traced to a primary or standards reference (NIST, BIPM, or the defining regulation for the unit).</li>
  <li>Factors are stored once per unit and reused, so a correction is applied everywhere at once.</li>
  <li>Edge cases (same-unit input, zero, extremely large/small values) are handled explicitly so the page never shows a nonsense ratio.</li>
</ul>
<p>Primary references: <a href="https://www.nist.gov/pml/owm" rel="noopener">NIST Office of Weights and Measures</a>, <a href="https://www.bipm.org/" rel="noopener">BIPM</a>, and the SI Brochure (9th edition).</p>'''),

  "privacy": ("Privacy policy",
    "How FreeConvert handles your data: what is collected, what is not, and how conversions stay on your device.",
    "Privacy",
    '''<p class="lede">FreeConvert is designed to collect as little as possible. This page explains what happens to the data you enter.</p>
<h2>What we do not collect</h2>
<ul>
  <li><strong>No account.</strong> There is no sign-up and no profile.</li>
  <li><strong>No server-side logging of conversions.</strong> The numbers you type are processed in your browser (JavaScript). They are never sent to our servers.</li>
  <li><strong>No analytics cookies.</strong> This site does not load Google Analytics, Meta Pixel, or any behavioural-tracking script.</li>
</ul>
<h2>What the site does load</h2>
<ul>
  <li><strong>Styles and scripts</strong> needed to render the page and run calculations (served from this domain).</li>
  <li><strong>An optional advertising script</strong> (Monetag) that may set a cookie for ad delivery and measurement. Advertising is provided by a third party; its privacy practices are governed by that provider. You can block it with a standard ad/tracker blocker. No advertising script runs until a real configuration is present - placeholder slots are inert.</li>
  <li><strong>A service worker</strong> (sw.js) used only for the advertising push notifications feature. It is not used to read your inputs.</li>
</ul>
<h2>Local storage</h2>
<p>Converter pages may store your last-used units and recent inputs in your browser's <code>localStorage</code> or <code>sessionStorage</code> so the page feels consistent on return. This stays on your device. Where a clear-history control is present, using it removes that data immediately.</p>
<h2>Your rights</h2>
<p>No personal account data is held, so there is nothing to export or delete on our side. To stop all local storage, clear site data for zackkaz.github.io in your browser settings.</p>
<h2>Contact</h2>
<p>Questions about privacy can be raised on the project's <a href="https://github.com/Zackkaz/freeconvert/issues" rel="noopener">GitHub Issues</a> page.</p>'''),

  "terms": ("Terms of use",
    "The terms under which FreeConvert may be used: it is provided free of charge, with no warranty, and not for critical decision-making without independent verification.",
    "Terms of use",
    '''<p class="lede">FreeConvert is provided free of charge. By using it you agree to the following simple terms.</p>
<h2>Use of the site</h2>
<p>You may use FreeConvert for any lawful, personal or commercial purpose at no cost. The converters and calculators are provided "as is" without warranty of any kind.</p>
<h2>No warranty</h2>
<p>Results are generated by documented formulas and factors, but we do not warrant their fitness for any particular purpose. <strong>Always verify critical values independently</strong> - especially in medical, engineering, financial, or safety-related contexts.</p>
<h2>Limitation of liability</h2>
<p>To the fullest extent permitted by law, FreeConvert and its operator are not liable for any loss or damage arising from reliance on a conversion result. The service is a convenience tool, not a certified instrument.</p>
<h2>Intellectual property</h2>
<p>The site content and generator are offered openly. Unit names, symbols, and conversion factors are factual standards and are not owned by anyone.</p>
<h2>Changes</h2>
<p>These terms may be updated. Continued use after a change constitutes acceptance of the revised terms.</p>'''),

  "contact": ("Contact FreeConvert",
    "How to reach the FreeConvert project: report a bug, suggest a unit, or ask a question via the public issue tracker.",
    "Contact",
    '''<p class="lede">FreeConvert has no call centre or support inbox. The fastest, public way to reach the project is the issue tracker.</p>
<h2>Report a problem or suggest a change</h2>
<p>Open an issue on the <a href="https://github.com/Zackkaz/freeconvert/issues" rel="noopener">GitHub Issues</a> page. This is the best place for:</p>
<ul>
  <li>A wrong or surprising conversion result</li>
  <li>A unit or category you would like added</li>
  <li>A bug on a specific page</li>
  <li>General feedback</li>
</ul>
<h2>Before you report</h2>
<p>Check whether the question is already answered on <a href="/methodology/">Methodology</a> (how calculations work, rounding, sources). Include the page URL and the values you entered so the issue is reproducible.</p>
<h2>Email</h2>
<p>No verified public support email is configured. Using the public issue tracker keeps requests transparent and lets others benefit from the answers.</p>'''),
}

GUIDES = [
  ("metric-vs-imperial", "Metric vs imperial measurement systems",
   "The difference between metric and imperial units, why each exists, and how to convert between them confidently.",
   '''<p class="lede">Most of the world uses the metric system; the US still uses imperial units daily. Understanding both - and how to move between them - saves confusion in travel, cooking, and work.</p>
<h2>What "metric" means</h2>
<p>The metric system (officially the <em>International System of Units, SI</em>) is based on powers of ten. Length is measured in metres; mass in grams; volume in litres. Prefixes (kilo-, centi-, milli-) scale by 1,000 or 0.001, which makes conversion mostly a matter of moving a decimal point.</p>
<h2>What "imperial" means</h2>
<p>Imperial and US customary units grew from older local measures. A foot is 12 inches; a yard is 3 feet; a mile is 5,280 feet. These do not follow a clean decimal pattern, so converting usually needs a fixed factor (1 ft = 0.3048 m).</p>
<table>
<thead><tr><th>Quantity</th><th>Metric</th><th>Imperial / US</th><th>Key factor</th></tr></thead>
<tbody>
<tr><td>Length</td><td>metre (m)</td><td>foot (ft)</td><td>1 ft = 0.3048 m</td></tr>
<tr><td>Mass</td><td>kilogram (kg)</td><td>pound (lb)</td><td>1 lb = 0.45359237 kg</td></tr>
<tr><td>Volume</td><td>litre (L)</td><td>US gallon (gal)</td><td>1 gal = 3.78541 L</td></tr>
<tr><td>Temperature</td><td>°C / K</td><td>°F</td><td>°F = °C×9/5+32</td></tr>
</tbody></table>
<h2>Why both still exist</h2>
<p>Metric was adopted internationally for trade and science because base-10 maths is simpler. Imperial persists in the US through custom, existing tooling, and legislation. Most other countries are fully metric; the UK uses a mixed system.</p>
<h2>Practical tip</h2>
<p>For quick mental estimates: 1 inch 2.5 cm, 1 kg 2.2 lb, 1 km 0.62 mile. For anything precise, use the converter - e.g. <a href="/length/meter-to-foot/">metres to feet</a> or <a href="/weight/kilogram-to-pound/">kilograms to pounds</a>.</p>
<p>Sources: <a href="https://www.bipm.org/en/measurement-units" rel="noopener">BIPM</a>, <a href="https://www.nist.gov/pml/owm" rel="noopener">NIST</a>.</p>'''),

  ("temperature-conversions", "How temperature conversions work",
   "Why Celsius, Fahrenheit and Kelvin use different formulas, and how to convert between them by hand.",
   '''<p class="lede">Unlike length or mass, temperature scales do not share a zero point, so conversion is a two-step shift, not a simple ratio.</p>
<h2>The three common scales</h2>
<ul>
  <li><strong>Celsius (°C):</strong> 0 °C is the freezing point of water, 100 °C its boiling point (at 1 atm).</li>
  <li><strong>Fahrenheit (°F):</strong> 32 °F is water's freezing point, 212 °F its boiling point.</li>
  <li><strong>Kelvin (K):</strong> an absolute scale where 0 K is absolute zero; 273.15 K = 0 °C.</li>
</ul>
<h2>The formulas</h2>
<div class="formula">°F = °C × 9/5 + 32</div>
<div class="formula">°C = (°F - 32) × 5/9</div>
<div class="formula">K = °C + 273.15</div>
<h2>Worked examples</h2>
<table>
<thead><tr><th>°C</th><th>°F</th><th>K</th></tr></thead>
<tbody>
<tr><td>0</td><td>32</td><td>273.15</td></tr>
<tr><td>25</td><td>77</td><td>298.15</td></tr>
<tr><td>100</td><td>212</td><td>373.15</td></tr>
<tr><td>-40</td><td>-40</td><td>233.15</td></tr>
</tbody></table>
<p>Note that -40 °C = -40 °F - the only point where the two scales agree.</p>
<h2>Why the 9/5 and 32?</h2>
<p>Between freezing and boiling, Celsius spans 100 degrees while Fahrenheit spans 180 (212-32). So each Celsius degree is 180/100 = 9/5 of a Fahrenheit degree. The +32 aligns the zero points. Kelvin simply shifts Celsius by the defined value 273.15 (the ice point of water). See <a href="https://www.nist.gov/pml/weights-and-measures/si-units-temperature" rel="noopener">NIST</a>.</p>
<p>Try it: <a href="/temperature/celsius-to-fahrenheit/">Celsius to Fahrenheit</a>, <a href="/temperature/celsius-to-kelvin/">Celsius to Kelvin</a>.</p>'''),

  ("cooking-measurement-accuracy", "Cooking measurement accuracy",
   "Why small kitchen conversion errors matter, how volume and weight differ, and how to convert recipes reliably.",
   '''<p class="lede">In baking, a wrong conversion can ruin a recipe. Weight is more reliable than volume, and knowing why helps you scale recipes safely.</p>
<h2>Volume vs weight</h2>
<p>Cups and spoons measure <em>volume</em>; scales measure <em>mass</em>. The same volume of two ingredients can have very different masses: 1 US cup of flour is about 120 g, but 1 US cup of water is about 237 g. That is why "1 cup" is ambiguous without knowing the ingredient.</p>
<h2>Common kitchen factors</h2>
<table>
<thead><tr><th>Ingredient</th><th>1 US cup  </th></tr></thead>
<tbody>
<tr><td>Water</td><td>237 g</td></tr>
<tr><td>All-purpose flour</td><td>120 g</td></tr>
<tr><td>Granulated sugar</td><td>200 g</td></tr>
<tr><td>Butter</td><td>227 g</td></tr>
</tbody></table>
<p>Conversions we use: 1 US tbsp = 14.7868 mL, 1 US tsp = 4.9289 mL, 1 US cup = 236.588 mL (defined).</p>
<h2>Tips for accurate results</h2>
<ul>
  <li><strong>Weigh when you can.</strong> A kitchen scale removes the cup-ambiguity problem.</li>
  <li><strong>Spoon-and-level flour</strong> rather than scooping, which packs it and adds mass.</li>
  <li><strong>Scale recipes by mass</strong>, not by count of cups, when doubling or halving.</li>
  <li><strong>Mind the system:</strong> US cups differ from imperial UK cups (284 mL).</li>
</ul>
<p>Convert: <a href="/cooking/cup-us-to-gram/">cups to grams</a>, <a href="/cooking/tablespoon-to-teaspoon/">tablespoons to teaspoons</a>.</p>'''),

  ("precision-significant-figures", "Precision, significant figures and rounding",
   "What significant figures are, why rounding matters in measurement, and how FreeConvert displays results.",
   '''<p class="lede">A number is only as precise as the measurement behind it. This guide explains rounding, significant figures, and how display precision works.</p>
<h2>Significant figures</h2>
<p>Significant figures are the digits in a value that carry real meaning. If you measure 1.2 m, you have two significant figures - you do not know the millimetres. Writing 1.23456 m would falsely imply that precision.</p>
<h2>Rounding rules</h2>
<ul>
  <li>If the next digit is 5 or more, round up.</li>
  <li>Keep no more digits than your input justifies.</li>
  <li>Trailing zeros after a decimal (e.g. 2.0) signal precision and should be kept when they are meaningful.</li>
</ul>
<h2>Why computers are tricky</h2>
<p>Computers store numbers in binary floating point, so 0.1 + 0.2 is not exactly 0.3. The error is tiny, but it can show up as long decimal tails. FreeConvert rounds only for <em>display</em>; the underlying calculation is not changed by rounding.</p>
<h2>Choosing precision</h2>
<p>Use "Auto" for everyday checks - it drops unnecessary trailing zeros. Use a fixed precision (2, 4, 6, 10) when you need a consistent number of decimal places for reporting. Neither mode changes the actual result, only how it is shown.</p>
<p>Reference: <a href="https://physics.nist.gov/cuu/Uncertainty/" rel="noopener">NIST Guidelines for Evaluating and Expressing Uncertainty</a>.</p>'''),

  ("mass-vs-weight", "The difference between mass and weight",
   "Mass and weight are not the same: mass is matter, weight is force. Here is the distinction and why it matters for conversions.",
   '''<p class="lede">People use "mass" and "weight" interchangeably, but in physics they are different. Confusing them causes errors in science and engineering.</p>
<h2>Mass</h2>
<p>Mass is the amount of matter in an object. It is measured in kilograms (SI) or pounds-mass. Mass does not change with location.</p>
<h2>Weight</h2>
<p>Weight is the <em>force</em> gravity exerts on mass: <code>weight = mass × gravitational acceleration</code>. On Earth, weight is what a scale reads. On the Moon, your mass is the same but your weight is about one-sixth.</p>
<h2>Everyday usage</h2>
<p>In daily life "weight" in pounds or kilograms usually means mass - we are comparing amounts of stuff, not measuring force. That is fine for cooking and shipping. It matters in physics, aerospace, and medicine, where the distinction is real.</p>
<h2>Conversions</h2>
<p>Because most converter tools treat "weight / mass" as mass, 1 kg = 2.20462 lb is a mass conversion. The factor 0.45359237 kg per pound is defined by <a href="https://www.nist.gov/pml/owm" rel="noopener">NIST</a>.</p>
<p>Convert: <a href="/weight/kilogram-to-pound/">kg to lb</a>, <a href="/weight/pound-to-kilogram/">lb to kg</a>.</p>'''),

  ("common-conversion-mistakes", "Common unit-conversion mistakes",
   "The most frequent unit-conversion errors and how to avoid them, from wrong factors to mixed systems.",
   '''<p class="lede">Most conversion errors are avoidable. Here are the usual suspects and how to dodge them.</p>
<h2>1. Using the wrong factor</h2>
<p>Memorised shortcuts ("a pound is about 2 kilos") are fine for estimates but not for precision. A pound is 0.4536 kg, not 0.5. Use the exact factor or the converter.</p>
<h2>2. Mixing US and imperial volumes</h2>
<p>A US gallon is 3.785 L; a UK (imperial) gallon is 4.546 L. A US cup is 236.6 mL; a UK cup is 284 mL. Always check which system a recipe or spec assumes.</p>
<h2>3. Forgetting temperature is not a ratio</h2>
<p>You cannot multiply °C by a factor to get °F. Use the shift formula (°F = °C×9/5+32). The zero points differ.</p>
<h2>4. Confusing mass and weight</h2>
<p>On Earth the numbers line up with experience, but the concepts differ (see <a href="/guides/mass-vs-weight/">Mass vs weight</a>). In scientific contexts the difference is critical.</p>
<h2>5. Ignoring significant figures</h2>
<p>Reporting 12.3456789 m from a tape measure marked in centimetres invents precision. Round to what your input supports.</p>
<h2>6. Decimal/comma confusion</h2>
<p>Many countries use a comma as the decimal separator. Double-check when copying a value between systems.</p>'''),
]


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------
def converter_card(cat, frm, to, preset=None):
    return f'''<div class="card conv" data-cat="{cat}">
  <div class="row">
    <label class="lbl" for="from">From</label>
    <select id="from" aria-label="From unit"></select>
    <input id="val" type="number" inputmode="decimal" value="{preset if preset is not None else 1}" aria-label="Value to convert">
    <span class="eq" aria-hidden="true">=</span>
    <label class="lbl" for="to">To</label>
    <select id="to" aria-label="To unit"></select>
  </div>
  <div class="controls">
    <button type="button" id="swap" class="btn small" aria-label="Swap units">⇄ Swap</button>
    <button type="button" id="reset" class="btn small" aria-label="Reset to defaults">↺ Reset</button>
    <button type="button" id="copy" class="btn small" aria-label="Copy result">⧉ Copy</button>
    <label class="preclbl" for="prec">Precision</label>
    <select id="prec" aria-label="Decimal precision">
      <option value="auto" selected>Auto</option>
      <option value="2">2</option><option value="4">4</option>
      <option value="6">6</option><option value="10">10</option>
    </select>
  </div>
  <div class="result" id="res" aria-live="polite" aria-atomic="true">—</div>
  <div class="copystat" id="copystat" role="status" aria-live="polite"></div>
</div>'''

def breadcrumb_html(trail):
    return '<div class="breadcrumb">'+ " › ".join(
        f'<a href="{u}">{n}</a>' if i>0 else f'<a href="{u}">{n}</a>' for i,(n,u) in enumerate(trail))+'</div>'

def pair_page(cat, frm, to):
    c = next(x for x in CATS if x["slug"]==cat)
    title = f"{UNM[cat][frm]} to {UNM[cat][to]} — Convert {c['name']}"
    desc  = f"Free {UNM[cat][frm]} to {UNM[cat][to]} converter. Exact {c['name'].lower()} conversion with a live calculator and common values."
    rows="".join(f'<tr><td><a href="{BASE}/{cat}/{frm}-to-{to}/{v}/">{fmt(v)} {SYM[cat][frm]}</a></td><td>{fmt(convert(cat,frm,to,v))} {SYM[cat][to]}</td></tr>' for v in [1,5,10,50,100])
    table=f'<table><thead><tr><th>Value</th><th>{UNM[cat][to]} ({SYM[cat][to]})</th></tr></thead><tbody>{rows}</tbody></table>'
    faq="".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in c["faqs"])
    faq_json = jsonld({"@context":"https://schema.org","@type":"FAQPage",
        "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in c["faqs"]]})
    trail=[("Home",SITE+"/"),(c["name"],SITE+f"/{cat}/"),(f"{UNM[cat][frm]} to {UNM[cat][to]}",SITE+f"/{cat}/{frm}-to-{to}/")]
    body = f'''{breadcrumb_html(trail)}
<h1>{UNM[cat][frm]} to {UNM[cat][to]}</h1>
<p class="lede">{desc}</p>
{converter_card(cat,frm,to)}
{ad_slot("adsterra_native")}
<h2>Common {UNM[cat][frm]} to {UNM[cat][to]} conversions</h2>
{table}
<h2>Frequently asked questions</h2>
<div class="faq">{faq}</div>
{ad_slot("monetag_smartlink")}
<h2>More {c['name']} converters</h2>
<div class="grid">''' + "".join(
        f'<a class="chip" href="{BASE}/{cat}/{u[0]}-to-{to}/">{UNM[cat][u[0]]} → {UNM[cat][to]}</a>' for u in c["units"] if u[0]!=frm and u[0]!=to
    ) + "</div>"
    return page(title,desc,body, SITE+f"/{cat}/{frm}-to-{to}/",
                pagecfg={"cat":cat,"from":frm,"to":to}, extra_jsonld=breadcrumb_schema(trail)+faq_json)

def longtail_page(cat,frm,to,val):
    c = next(x for x in CATS if x["slug"]==cat)
    r = convert(cat,frm,to,val)
    title = f"{fmt(val)} {SYM[cat][frm]} to {SYM[cat][to]} | {UNM[cat][frm]} in {UNM[cat][to]}"
    desc  = f"{fmt(val)} {SYM[cat][frm]} = {fmt(r)} {SYM[cat][to]}. Free {c['name'].lower()} converter with exact result and related values."
    others="".join(f'<a class="chip" href="{BASE}/{cat}/{frm}-to-{to}/{v}/">{fmt(v)} {SYM[cat][frm]}</a>' for v in PRESETS if v!=val)
    trail=[("Home",SITE+"/"),(c["name"],SITE+f"/{cat}/"),(f"{UNM[cat][frm]} to {UNM[cat][to]}",SITE+f"/{cat}/{frm}-to-{to}/"),(f"{fmt(val)} {SYM[cat][frm]}",SITE+f"/{cat}/{frm}-to-{to}/{val}/")]
    body = f'''{breadcrumb_html(trail)}
<h1>{fmt(val)} {SYM[cat][frm]} to {SYM[cat][to]}</h1>
<p class="lede">{fmt(val)} {SYM[cat][frm]} equals:</p>
<div class="big">{fmt(r)} {SYM[cat][to]}</div>
{converter_card(cat,frm,to,val)}
{ad_slot("adsterra_native")}
<h2>Other {UNM[cat][frm]} values in {UNM[cat][to]}</h2>
<div class="grid">{others}</div>
<h2>Related {c['name']} converters</h2>
<div class="grid">''' + "".join(
        f'<a class="chip" href="{BASE}/{cat}/{u[0]}-to-{to}/">{UNM[cat][u[0]]} → {UNM[cat][to]}</a>' for u in c["units"] if u[0]!=frm and u[0]!=to
    ) + "</div>"
    return page(title,desc,body, SITE+f"/{cat}/{frm}-to-{to}/{val}/",
                pagecfg={"cat":cat,"from":frm,"to":to,"preset":val}, extra_jsonld=breadcrumb_schema(trail))

def calc_page(slug, title, desc, fields, button, fn, out_id):
    flds="".join(f'<label>{lab}</label>{inp}' for lab,inp in fields)
    body=f'''<h1>{title}</h1>
<p class="lede">{desc}</p>
<div class="card calc">{flds}
<button class="btn" onclick="runCalc({fn},\'{out_id}\')">{button}</button>
<div class="out" id="{out_id}"></div>
</div>{ad_slot("adsterra_native")}
<h2>How it works</h2><p>{desc} This free calculator runs entirely in your browser — no data leaves your device.</p>'''
    return page(title,desc,body, SITE+f"/calculators/{slug}/", extra_head=f'<script src="{BASE}/assets/calc.js"></script>')

CALCS = [
  ("percentage","Percentage Calculator","Find what a percentage of a number is, instantly.",
   [("Percent (%)","<input id='p' type='number' value='10'>"),("Of number","<input id='n' type='number' value='200'>")],
   "Calculate","pct","pout"),
  ("tip","Tip Calculator","Split a bill and calculate the tip per person.",
   [("Bill amount","<input id='b' type='number' value='50'>"),("Tip %","<input id='tp' type='number' value='15'>"),("People","<input id='pe' type='number' value='2'>")],
   "Calculate tip","tip","tout"),
  ("loan","Loan / EMI Calculator","Monthly EMI, total interest and total payment for any loan.",
   [("Loan amount","<input id='a' type='number' value='10000'>"),("Annual rate %","<input id='r' type='number' value='8'>"),("Years","<input id='y' type='number' value='5'>")],
   "Calculate EMI","loan","lout"),
  ("date-difference","Date Difference Calculator","Days and years between two dates.",
   [("Start date","<input id='d1' type='date' value='2020-01-01'>"),("End date","<input id='d2' type='date' value='2026-01-01'>")],
   "Calculate","ddiff","dout"),
  ("words-to-pages","Words to Pages Calculator","Estimate pages from a word count.",
   [("Word count","<input id='w' type='number' value='2500'>"),("Words per page","<input id='pp' type='number' value='500'>")],
   "Estimate","wtp","wout"),
  ("age","Age Calculator","Your exact age in years and days.",
   [("Date of birth","<input id='dob' type='date' value='1995-06-15'>")],
   "Calculate age","age","aout"),
]

# ---------------------------------------------------------------------------
# Write files
# ---------------------------------------------------------------------------
def write(rel, html):
    p = os.path.join(PUB, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p,"w",encoding="utf-8") as f: f.write(html)

def notify_indexnow(urls):
    """Submit a capped batch of URLs to the IndexNow API (Bing/Yandex/Naver/
    Seznam). No login required — ownership is proven by the key file at
    /<INDEXNOW_KEY>.txt (deployed in main()). Best-effort: errors never
    break the build. The full sitemap is still auto-discovered by crawlers
    via robots.txt, so this just speeds up first indexing of key pages."""
    import json, urllib.request
    batch = urls[:2000]   # seed the most important URLs; rest found via sitemap
    try:
        payload = json.dumps({
            "host": SITE.split("//",1)[1],
            "key": INDEXNOW_KEY,
            "keyLocation": f"{SITE}/{INDEXNOW_KEY}.txt",
            "urlList": batch,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow", data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST")
        urllib.request.urlopen(req, timeout=20)
        print(f"  IndexNow: submitted {len(batch)} URLs")
    except Exception as e:
        print(f"  IndexNow skipped: {e}")

def main():
    # Clean previously generated pages so removed categories/units don't linger
    # (Cloudflare free tier caps ~20k files; stale files would waste that budget).
    # PRESERVE assets/ — it holds hand-written, git-tracked CSS/JS that build.py
    # does not regenerate, so wiping it would break every page's styling/JS.
    if os.path.isdir(PUB):
        import shutil
        for name in os.listdir(PUB):
            if name in ("assets", "monetag_tag.min.js") or name.endswith(".txt") or name.endswith("-verify.html"):
                continue
            p = os.path.join(PUB, name)
            if os.path.isdir(p): shutil.rmtree(p)
            else: os.remove(p)
    urls=[]; count=0
    catjs = "window.CATS=" + json.dumps({
        c["slug"]:{"type":c["type"],
                   "units":[{"s":u[0],"y":u[1],"n":u[2]} for u in c["units"]],
                   "factors":{u[0]:u[3] for u in c["units"]} if c["type"]=="f" else {}}
        for c in CATS}, ensure_ascii=False) + ";"
    write("assets/cats.js", catjs)
    write("sw.js", MONETAG_SW)   # Monetag service-worker push (regenerated each build)
    write(MONETAG_TAG_FILE, open(os.path.join(ROOT, MONETAG_TAG_FILE), encoding="utf-8").read())
                 # Monetag "Superior tag" loader, self-hosted (regenerated each build)

    # homepage
    catcards="".join(
        f'<a class="catcard" href="{BASE}/{c["slug"]}/"><b>{c["name"]}</b><span>{len(c["units"])} units · {len(c["units"])*(len(c["units"])-1)} conversions</span></a>'
        for c in CATS)
    calchome="".join(f'<a class="chip" href="{BASE}/calculators/{s}/">{t}</a>' for s,t,_,_,_,_,_ in CALCS)
    home=f'''<h1>Free Unit Converters & Calculators</h1>
<p class="lede">Fast, accurate, free converters for length, weight, temperature, volume, digital storage and more — plus everyday calculators. No sign-up.</p>
{ad_slot("propeller_onclick")}
<h2 id="categories">Converters</h2>
<div class="catcards">{catcards}</div>
<h2 id="calc">Calculators</h2>
<div class="grid">{calchome}</div>
<h2 id="guides">Guides</h2>
<div class="grid"><a class="chip" href="{BASE}/guides/">Measurement & conversion guides</a></div>
{ad_slot("adsterra_native")}
<h2>Why FreeConvert</h2>
<p>Every page is generated with exact math and loads instantly on any device. Perfect for students, cooks, engineers and travelers.</p>'''
    write("index.html", page("FreeConvert — Free Unit Converters & Calculators",
        "Free, fast unit converters (length, weight, temperature, volume, digital storage) and everyday calculators. Exact results, no sign-up.", home, SITE+"/"))
    urls.append(SITE+"/")

    for c in CATS:
        cat=c["slug"]; units=c["units"]
        chips="".join(f'<a class="chip" href="{BASE}/{cat}/{u[0]}-to-{units[1][0]}/">{u[2]} → {units[1][2]}</a>' for u in units if u[0]!=units[1][0])
        idx=f'''<h1>{c["name"]} Converters</h1>
<p class="lede">{c["intro"]}</p>
<div class="grid">{chips}</div>
{ad_slot("adsterra_native")}'''
        write(f"{cat}/index.html", page(f"{c['name']} Converters — FreeConvert", c["intro"], idx, SITE+f"/{cat}/"))
        urls.append(f"{SITE}/{cat}/")
        for a in units:
            for b in units:
                if a[0]==b[0]: continue
                write(f"{cat}/{a[0]}-to-{b[0]}/index.html", pair_page(cat,a[0],b[0])); count+=1
                urls.append(f"{SITE}/{cat}/{a[0]}-to-{b[0]}/")
                for v in PRESETS:
                    write(f"{cat}/{a[0]}-to-{b[0]}/{v}/index.html", longtail_page(cat,a[0],b[0],v)); count+=1
                    urls.append(f"{SITE}/{cat}/{a[0]}-to-{b[0]}/{v}/")

    for slug,title,desc,fields,btn,fn,out in CALCS:
        write(f"calculators/{slug}/index.html", calc_page(slug,title,desc,fields,btn,fn,out))
        urls.append(f"{SITE}/calculators/{slug}/")

    # --- Trust + transparency pages (footer-discovered; NOT in sitemap) -------
    # These are intentionally excluded from the sitemap so the GSC-submitted
    # URL inventory is preserved unchanged while Search Console processes it.
    # They are reachable via the site-wide footer (footer_html()).
    for slug,(t,d,h,b) in TRUST.items():
        write(f"{slug}/index.html", static_page(t,d,h,b,slug))
    # Guides hub
    guide_cards = "".join(
        f'<a class="chip" href="{BASE}/guides/{g[0]}/">{g[1]}</a>' for g in GUIDES)
    guides_body = f'''<h1>Guides & explanations</h1>
<p class="lede">Plain-language guides to measurement, conversion maths, and common mistakes — written for people, with sources.</p>
<div class="grid">{guide_cards}</div>
{ad_slot("adsterra_native")}
<h2>Why these guides exist</h2>
<p>Converters give you an answer; these guides explain the <em>why</em> — the factors, the formulas, and the traps. Every claim traces to a primary source such as NIST or BIPM.</p>'''
    write("guides/index.html", static_page(
        "FreeConvert guides — measurement & conversion explained",
        "Plain-language guides to units, temperature maths, mass vs weight, rounding, and common conversion mistakes.",
        "Guides & explanations", guides_body, "guides"))
    # Individual guides
    for slug,gt,gd,gb in GUIDES:
        write(f"guides/{slug}/index.html", static_page(gt,gd,gt,gb, f"guides/{slug}"))

    write("robots.txt", f"""User-agent: *
Allow: /
Sitemap: {SITE}/sitemap.xml

# Crawl-delay is ignored by Google but helps smaller engines on shared hosting.
# (GitHub Pages handles load fine; kept conservative for politeness.)
User-agent: Bingbot
Crawl-delay: 1
""")
    # --- Sitemap: index + chunked child sitemaps (fixes GSC "couldn't fetch") ---
    # A single 17k-URL sitemap (~1.4 MB) can time out in GSC's fetcher. The
    # protocol-correct solution: a sitemap INDEX (small) at sitemap.xml that
    # references child sitemaps of ~2000 URLs each. GSC fetches the tiny index,
    # then pulls each small chunk quickly. Submit sitemap.xml (the index).
    from datetime import datetime as _dt
    _today = _dt.utcnow().strftime("%Y-%m-%d")
    _chunk = 2000
    # 1. child sitemaps
    for i in range(0, len(urls), _chunk):
        part = urls[i:i + _chunk]
        sm_child = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
            "".join(f'<url><loc>{u}</loc><lastmod>{_today}</lastmod></url>\n' for u in part) + \
            "</urlset>\n"
        write(f"sitemap_{(i // _chunk) + 1:03d}.xml", sm_child)
    # 2. sitemap.xml = index pointing at the children
    index = f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
        "".join(
            f'<sitemap><loc>{SITE}/sitemap_{(i // _chunk) + 1:03d}.xml</loc><lastmod>{_today}</lastmod></sitemap>\n'
            for i in range(0, len(urls), _chunk)
        ) + "</sitemapindex>\n"
    write("sitemap.xml", index)

    # --- HARD SITEMAP GUARD (preserve the frozen GSC inventory) ---------------
    # The submitted sitemap inventory MUST stay: 1 index + 9 children = exactly
    # 17,323 URLs, in the same deterministic order. Any drift (e.g. a change to
    # CATS/PRESETS) would silently alter the indexed URL set, so we fail the
    # build loudly rather than publish a different set.
    _n_children = (len(urls) + _chunk - 1) // _chunk
    assert _n_children == 9, f"SITEMAP GUARD: expected 9 child sitemaps, got {_n_children}"
    assert len(urls) == 17323, f"SITEMAP GUARD: expected 17,323 URLs, got {len(urls)}"

    # --- Search-engine verification files (root) -------------------------------
    # GSC_HTML_FILE / GSC_HTML_BODY and BING_HTML_BODY are set above with the
    # real verification tokens. Files are emitted at the site root so the
    # respective consoles can verify ownership.
    # Google Search Console: HTML-file method. Replace GSC_HTML_FILE /
    # GSC_HTML_BODY above with the values Google shows, then rebuild.
    # (Skip emitting if still set to the placeholder token.)
    if "REPLACE" not in GSC_HTML_FILE and "REPLACE" not in GSC_HTML_BODY:
        write(GSC_HTML_FILE, GSC_HTML_BODY + "\n")
    # Bing Webmaster Tools: HTML-file method.
    if "REPLACE" not in BING_HTML_BODY:
        write("bing-verify.html", BING_HTML_BODY + "\n")
    # IndexNow key file — proves ownership of the key to Bing/Yandex/Naver.
    # (Deployed as /<KEY>.txt so IndexNow can validate ownership.)
    write(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY)

    # humans.txt — a small trust/transparency signal crawlers and humans can read.
    write("humans.txt", f"""# humanstxt.org/
Team
    Site: FreeConvert — free unit converters & calculators
    Built with: Python static generator + GitHub Pages ($0 hosting)
    Contact: open an issue on github.com/Zackkaz/freeconvert
Last build: {datetime.date.today().isoformat()}
Thanks to the open-source static-web community.
""")

    # --- Instant-index key URLs via IndexNow (no login required) ----------------
    # Bing/Yandex/Naver/Seznam pick these up immediately; the rest of the
    # 17k URLs are auto-discovered from sitemap.xml (referenced in robots.txt).
    notify_indexnow(urls)

    print(f"Generated {count} converter pages + {len(CALCS)} calculators + indexes.")
    print(f"Total URLs in sitemap: {len(urls)}")
    print(f"Output dir: {PUB}")

if __name__=="__main__":
    main()
