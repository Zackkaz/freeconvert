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
        # Explicit branches matter here: 0 is falsy in Python, so a chained
        # and/or expression sends 0°C through the Kelvin branch.
        if frm == "celsius":
            cv = v
        elif frm == "fahrenheit":
            cv = (v - 32) * 5 / 9
        else:
            cv = v - 273.15
        if to == "celsius":
            return cv
        if to == "fahrenheit":
            return cv * 9 / 5 + 32
        return cv + 273.15
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

def conversion_formula(cat, frm, to):
    """Return a readable formula and a plain-English instruction."""
    c = next(x for x in CATS if x["slug"] == cat)
    fs, ts = SYM[cat][frm], SYM[cat][to]
    if c["type"] == "f":
        rate = convert(cat, frm, to, 1)
        return (f"{ts} = {fs} × {fmt(rate)}",
                f"Multiply the {UNM[cat][frm].lower()} value by {fmt(rate)} to get {UNM[cat][to].lower()}.")
    formulas = {
        ("celsius", "fahrenheit"): ("°F = (°C × 9/5) + 32", "Multiply Celsius by 9/5, then add 32."),
        ("fahrenheit", "celsius"): ("°C = (°F − 32) × 5/9", "Subtract 32 from Fahrenheit, then multiply by 5/9."),
        ("celsius", "kelvin"): ("K = °C + 273.15", "Add 273.15 to Celsius."),
        ("kelvin", "celsius"): ("°C = K − 273.15", "Subtract 273.15 from Kelvin."),
        ("fahrenheit", "kelvin"): ("K = (°F − 32) × 5/9 + 273.15", "Subtract 32, multiply by 5/9, then add 273.15."),
        ("kelvin", "fahrenheit"): ("°F = (K − 273.15) × 9/5 + 32", "Subtract 273.15, multiply by 9/5, then add 32."),
    }
    return formulas[(frm, to)]

def worked_calculation(cat, frm, to, value):
    result = convert(cat, frm, to, value)
    c = next(x for x in CATS if x["slug"] == cat)
    if c["type"] == "f":
        rate = convert(cat, frm, to, 1)
        return f"{fmt(value)} {SYM[cat][frm]} × {fmt(rate)} = {fmt(result)} {SYM[cat][to]}"
    formula, _ = conversion_formula(cat, frm, to)
    return f"Using {formula}: {fmt(value)} {SYM[cat][frm]} = {fmt(result)} {SYM[cat][to]}"

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
    convjs = f'<script src="{BASE}/assets/cats.js" defer></script><script src="{BASE}/assets/conv.js" defer></script>' if pagecfg and "cat" in (pagecfg or {}) else ""
    site_schema = jsonld({"@context":"https://schema.org","@type":"WebSite","@id":SITE+"/#website",
        "name":"FreeConvert","alternateName":"Free Convert","url":SITE+"/"}) if canonical == SITE+"/" else ""
    og = (f'<meta property="og:title" content="{title}">'
          f'<meta property="og:description" content="{desc}">'
          f'<meta property="og:type" content="website">'
          f'<meta property="og:url" content="{canonical}">'
          f'<meta property="og:site_name" content="FreeConvert">')
    return f"""<!doctype html>
<html lang="en">
<head>
{MONETAG_HEAD_TAG}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{canonical}">
{og}
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
{vmeta}
<link rel="stylesheet" href="{BASE}/assets/style.css">
{cfg}{convjs}{extra_head}
{site_schema}
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
<a class="skip-link" href="#main-content">Skip to content</a>
<header class="top"><div class="wrap">
  <a class="brand" href="{BASE}/">Free<span>Convert</span></a>
  <nav class="top">
    <a href="{BASE}/">Home</a>
    <a href="{BASE}/#categories">Converters</a>
    <a href="{BASE}/#calc">Calculators</a>
  </nav>
</div></header>
<main class="wrap" id="main-content">
{body}
</main>
<footer><div class="wrap">
  <div>© {datetime.date.today().year} FreeConvert — free unit converters & calculators.</div>
  <div><a href="{BASE}/sitemap.xml">Sitemap</a> · <a href="{BASE}/robots.txt">Robots</a></div>
</div></footer>
</body>
</html>"""

def ad_slot(kind):
    code = ADS.get(kind,"")
    if code.strip() and "YOUR_" not in code:
        return f'<div class="ad">{code}</div>'
    # Missing ad credentials should never create broken scripts or visible
    # placeholders. Real snippets render automatically once configured.
    return ""

# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------
def converter_card(cat, frm, to, preset=None):
    return f'''<div class="card conv">
  <div class="row">
    <label class="sr-only" for="from">From unit</label>
    <select id="from" aria-label="From unit"></select>
    <label class="sr-only" for="val">Value to convert</label>
    <input id="val" type="number" inputmode="decimal" aria-label="Value to convert" value="{preset if preset is not None else 1}">
    <span class="eq">=</span>
    <label class="sr-only" for="to">To unit</label>
    <select id="to" aria-label="To unit"></select>
  </div>
  <div class="result" id="res" aria-live="polite">—</div>
</div>'''

def breadcrumb_html(trail):
    return '<nav class="breadcrumb" aria-label="Breadcrumb">'+ " › ".join(
        f'<a href="{u}">{n}</a>' for n,u in trail)+'</nav>'

def pair_page(cat, frm, to):
    c = next(x for x in CATS if x["slug"]==cat)
    rate = convert(cat, frm, to, 1)
    formula, instruction = conversion_formula(cat, frm, to)
    title = f"{UNM[cat][frm]} to {UNM[cat][to]} Converter ({SYM[cat][frm]} to {SYM[cat][to]}) | FreeConvert"
    desc  = f"Convert {UNM[cat][frm].lower()} to {UNM[cat][to].lower()}. 1 {SYM[cat][frm]} = {fmt(rate)} {SYM[cat][to]}. Includes the exact formula, calculator, table and worked example."
    rows="".join(f'<tr><td><a href="{BASE}/{cat}/{frm}-to-{to}/{v}/">{fmt(v)} {SYM[cat][frm]}</a></td><td>{fmt(convert(cat,frm,to,v))} {SYM[cat][to]}</td></tr>' for v in [1,5,10,50,100])
    table=f'<table><thead><tr><th>Value</th><th>{UNM[cat][to]} ({SYM[cat][to]})</th></tr></thead><tbody>{rows}</tbody></table>'
    faq_items = [
        (f"How do I convert {UNM[cat][frm].lower()} to {UNM[cat][to].lower()}?", f"{instruction} The formula is {formula}."),
        (f"How many {UNM[cat][to].lower()} are in 1 {SYM[cat][frm]}?", f"1 {SYM[cat][frm]} equals {fmt(rate)} {SYM[cat][to]}."),
    ]
    faq="".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in faq_items)
    faq_json = jsonld({"@context":"https://schema.org","@type":"FAQPage",
        "mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_items]})
    trail=[("Home",SITE+"/"),(c["name"],SITE+f"/{cat}/"),(f"{UNM[cat][frm]} to {UNM[cat][to]}",SITE+f"/{cat}/{frm}-to-{to}/")]
    body = f'''{breadcrumb_html(trail)}
<h1>{UNM[cat][frm]} to {UNM[cat][to]}</h1>
<p class="lede">{desc}</p>
{converter_card(cat,frm,to)}
{ad_slot("adsterra_native")}
<h2>{UNM[cat][frm]} to {UNM[cat][to]} formula</h2>
<div class="formula"><strong>{formula}</strong><span>{instruction}</span></div>
<h2>Worked example</h2>
<p>To convert 10 {SYM[cat][frm]} to {SYM[cat][to]}:</p>
<p class="calculation">{worked_calculation(cat,frm,to,10)}</p>
<h2>Common {UNM[cat][frm]} to {UNM[cat][to]} conversions</h2>
{table}
<h2>Accuracy and rounding</h2>
<p>The calculator keeps more precision internally than it displays. For everyday use, round the result to the number of decimal places your measurement supports. Keep extra digits for scientific or engineering calculations.</p>
<p><a href="{BASE}/{cat}/{to}-to-{frm}/">Convert {UNM[cat][to]} back to {UNM[cat][frm]} →</a></p>
<h2>Frequently asked questions</h2>
<div class="faq">{faq}</div>
{ad_slot("monetag_smartlink")}
<h2>More {c['name']} converters</h2>
<div class="grid">''' + "".join(
        f'<a class="chip" href="{BASE}/{cat}/{u[0]}-to-{to}/">{UNM[cat][u[0]]} → {UNM[cat][to]}</a>' for u in c["units"] if u[0] not in (frm,to)
    ) + "</div>"
    return page(title,desc,body, SITE+f"/{cat}/{frm}-to-{to}/",
                pagecfg={"cat":cat,"from":frm,"to":to}, extra_jsonld=breadcrumb_schema(trail)+faq_json)

def longtail_page(cat,frm,to,val):
    c = next(x for x in CATS if x["slug"]==cat)
    r = convert(cat,frm,to,val)
    formula, instruction = conversion_formula(cat, frm, to)
    title = f"{fmt(val)} {UNM[cat][frm]} to {UNM[cat][to]} ({fmt(r)} {SYM[cat][to]})"
    desc  = f"Convert {fmt(val)} {SYM[cat][frm]} to {SYM[cat][to]}: {fmt(val)} {SYM[cat][frm]} = {fmt(r)} {SYM[cat][to]}. See the formula, calculation steps and nearby values."
    others="".join(f'<a class="chip" href="{BASE}/{cat}/{frm}-to-{to}/{v}/">{fmt(v)} {SYM[cat][frm]}</a>' for v in PRESETS if v!=val)
    nearby = [-1, 0, 1] if val == 0 else [val * 0.5, val, val * 1.5]
    nearby_rows = "".join(f'<tr><td>{fmt(v)} {SYM[cat][frm]}</td><td>{fmt(convert(cat,frm,to,v))} {SYM[cat][to]}</td></tr>' for v in nearby)
    trail=[("Home",SITE+"/"),(c["name"],SITE+f"/{cat}/"),(f"{UNM[cat][frm]} to {UNM[cat][to]}",SITE+f"/{cat}/{frm}-to-{to}/"),(f"{fmt(val)} {SYM[cat][frm]}",SITE+f"/{cat}/{frm}-to-{to}/{val}/")]
    body = f'''{breadcrumb_html(trail)}
<h1>{fmt(val)} {UNM[cat][frm]} to {UNM[cat][to]}</h1>
<p class="lede">{fmt(val)} {SYM[cat][frm]} equals {fmt(r)} {SYM[cat][to]}.</p>
<div class="big">{fmt(r)} {SYM[cat][to]}</div>
{converter_card(cat,frm,to,val)}
{ad_slot("adsterra_native")}
<h2>Conversion formula</h2>
<div class="formula"><strong>{formula}</strong><span>{instruction}</span></div>
<h2>Calculation</h2>
<p class="calculation">{worked_calculation(cat,frm,to,val)}</p>
<h2>Nearby values</h2>
<table><thead><tr><th>{UNM[cat][frm]} ({SYM[cat][frm]})</th><th>{UNM[cat][to]} ({SYM[cat][to]})</th></tr></thead><tbody>{nearby_rows}</tbody></table>
<h2>Result precision</h2>
<p>The displayed result is rounded to six decimal places when needed. The converter calculates with full floating-point precision, so you can enter a more precise value in the calculator above.</p>
<p><a href="{BASE}/{cat}/{to}-to-{frm}/">Reverse this conversion: {UNM[cat][to]} to {UNM[cat][frm]} →</a></p>
<h2>Other {UNM[cat][frm]} values in {UNM[cat][to]}</h2>
<div class="grid">{others}</div>
<h2>Related {c['name']} converters</h2>
<div class="grid">''' + "".join(
        f'<a class="chip" href="{BASE}/{cat}/{u[0]}-to-{to}/">{UNM[cat][u[0]]} → {UNM[cat][to]}</a>' for u in c["units"] if u[0] not in (frm,to)
    ) + "</div>"
    return page(title,desc,body, SITE+f"/{cat}/{frm}-to-{to}/{val}/",
                pagecfg={"cat":cat,"from":frm,"to":to,"preset":val}, extra_jsonld=breadcrumb_schema(trail))

CALC_GUIDES = {
    "percentage": {
        "formula":"Result = (percentage ÷ 100) × number",
        "example":"10% of 200 = (10 ÷ 100) × 200 = 20.",
        "notes":"Percent means “per hundred.” Convert the percentage to a decimal by dividing by 100, then multiply by the original number."
    },
    "tip": {
        "formula":"Tip = bill × (tip percentage ÷ 100); per person = (bill + tip) ÷ people",
        "example":"A 15% tip on a 50 bill is 7.50. Split between two people, the total is 28.75 each.",
        "notes":"Enter the pre-tip bill amount, desired tip percentage and number of people. The calculator shows the tip, total and equal share per person."
    },
    "loan": {
        "formula":"EMI = P × r × (1 + r)ⁿ ÷ ((1 + r)ⁿ − 1)",
        "example":"For a 10,000 loan at 8% annually over 5 years, r is the monthly rate and n is 60 monthly payments.",
        "notes":"P is principal, r is the monthly interest rate and n is the number of monthly payments. Results are estimates and may differ from a lender’s fees or rounding."
    },
    "date-difference": {
        "formula":"Difference in days = end date − start date",
        "example":"From 1 January to 11 January is 10 elapsed days.",
        "notes":"The result uses elapsed calendar days. The year estimate uses 365.25 days to account for leap years over long periods."
    },
    "words-to-pages": {
        "formula":"Estimated pages = word count ÷ words per page",
        "example":"2,500 words at 500 words per page is approximately 5 pages.",
        "notes":"Actual page count depends on font, spacing, margins, headings and images. Change the words-per-page value to match your document format."
    },
    "age": {
        "formula":"Approximate age = elapsed days ÷ 365.25",
        "example":"The calculator measures elapsed time from the birth date to today and reports years and total days.",
        "notes":"The decimal-year figure is an estimate based on 365.25 days per year; the total elapsed days is also shown."
    },
}

def calc_page(slug, title, desc, fields, button, fn, out_id):
    def labeled_field(label, input_html):
        marker = "id='"
        field_id = input_html.split(marker, 1)[1].split("'", 1)[0]
        return f'<label for="{field_id}">{label}</label>{input_html}'
    flds="".join(labeled_field(lab, inp) for lab,inp in fields)
    guide = CALC_GUIDES[slug]
    trail=[("Home",SITE+"/"),("Calculators",SITE+"/#calc"),(title,SITE+f"/calculators/{slug}/")]
    body=f'''{breadcrumb_html(trail)}
<h1>{title}</h1>
<p class="lede">{desc}</p>
<div class="card calc">{flds}
<button class="btn" onclick="runCalc({fn},\'{out_id}\')">{button}</button>
<div class="out" id="{out_id}" aria-live="polite"></div>
</div>{ad_slot("adsterra_native")}
<h2>Formula</h2>
<div class="formula"><strong>{guide["formula"]}</strong><span>{guide["notes"]}</span></div>
<h2>Worked example</h2><p>{guide["example"]}</p>
<h2>How this calculator works</h2>
<p>{desc} The calculation runs entirely in your browser, so the values you enter are not sent to a server.</p>
<h2>Using the result</h2>
<p>Check that your inputs use the intended units and assumptions. Round only the final result so intermediate rounding does not introduce avoidable error.</p>'''
    page_desc = f"{desc} Includes the formula, a worked example and an instant browser-based result."
    return page(f"{title} | FreeConvert",page_desc,body, SITE+f"/calculators/{slug}/",
                extra_head=f'<script src="{BASE}/assets/calc.js" defer></script>',
                extra_jsonld=breadcrumb_schema(trail))

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
    popular = [
        ("Meters to Feet", "/length/meter-to-foot/"),
        ("Kilometers to Miles", "/length/kilometer-to-mile/"),
        ("Kilograms to Pounds", "/weight/kilogram-to-pound/"),
        ("Celsius to Fahrenheit", "/temperature/celsius-to-fahrenheit/"),
        ("Liters to US Gallons", "/volume/liter-to-gallon-us/"),
        ("Megabytes to Gigabytes", "/digital/megabyte-to-gigabyte/"),
    ]
    popular_links = "".join(f'<a class="chip" href="{BASE}{url}">{label}</a>' for label,url in popular)
    home=f'''<h1>Free Unit Converters & Calculators</h1>
<p class="lede">Fast, accurate, free converters for length, weight, temperature, volume, digital storage and more — plus everyday calculators. No sign-up.</p>
{ad_slot("propeller_onclick")}
<h2 id="categories">Converters</h2>
<div class="catcards">{catcards}</div>
<h2>Popular conversions</h2>
<div class="grid">{popular_links}</div>
<h2 id="calc">Calculators</h2>
<div class="grid">{calchome}</div>
{ad_slot("adsterra_native")}
<h2>How to use FreeConvert</h2>
<ol class="steps"><li>Choose a converter or calculator.</li><li>Enter a value and select the units.</li><li>Read the instant result, formula and worked example.</li></ol>
<h2>Accurate conversions, clearly explained</h2>
<p>FreeConvert calculates metric, imperial and specialist unit conversions from defined conversion factors and established temperature formulas. Converter pages show the formula, a worked calculation, a common-values table and guidance about rounding so you can understand and verify the result.</p>
<p>Calculations run in your browser and require no account. The site is designed for quick checks by students, cooks, engineers, travelers and anyone comparing measurement systems.</p>'''
    write("index.html", page("FreeConvert — Free Unit Converters & Calculators",
        "Free, fast unit converters (length, weight, temperature, volume, digital storage) and everyday calculators. Exact results, no sign-up.", home, SITE+"/"))
    urls.append(SITE+"/")

    for c in CATS:
        cat=c["slug"]; units=c["units"]
        links=[]
        for u in units:
            target = units[0] if u[0] != units[0][0] else units[1]
            links.append(f'<a class="chip" href="{BASE}/{cat}/{u[0]}-to-{target[0]}/">{u[2]} → {target[2]}</a>')
        chips="".join(links)
        trail=[("Home",SITE+"/"),(f"{c['name']} converters",SITE+f"/{cat}/")]
        idx=f'''{breadcrumb_html(trail)}
<h1>{c["name"]} Converters</h1>
<p class="lede">{c["intro"]}</p>
<h2>Choose a {c["name"].lower()} conversion</h2>
<div class="grid">{chips}</div>
{ad_slot("adsterra_native")}
<h2>How {c["name"].lower()} conversion works</h2>
<p>{c["intro"]} Select a starting unit above to open a calculator with the exact conversion formula, worked example and common-value table.</p>
<p>This category contains {len(units)} supported units and {len(units)*(len(units)-1)} direct unit-to-unit converters. Reverse-conversion links make it easy to check the calculation in both directions.</p>'''
        category_desc = f"Free {c['name'].lower()} converters for {len(units)} units, with exact formulas, worked examples and conversion tables."
        write(f"{cat}/index.html", page(f"{c['name']} Conversion Calculators | FreeConvert", category_desc, idx,
              SITE+f"/{cat}/", extra_jsonld=breadcrumb_schema(trail)))
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

