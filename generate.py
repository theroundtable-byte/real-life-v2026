#!/usr/bin/env python3
"""Build Real Life v2026: satirical US patch notes from real, linked sources."""

from __future__ import annotations

import hashlib
import html
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DATA = SITE / "data"
PATCHES = DATA / "patches"
ARCHIVE = SITE / "archive"
TZ = ZoneInfo("America/New_York")
SITE_URL = "https://theroundtable-byte.github.io/real-life-v2026"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
CTX = ssl.create_default_context()
MAX_ARCHIVE = 60
YAHOO_BLOCKED = False

FEEDS = [
    {"id": "gn_top", "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", "category": "News", "limit": 8},
    {"id": "gn_nat", "url": "https://news.google.com/rss/headlines/section/topic/NATION?hl=en-US&gl=US&ceid=US:en", "category": "News", "limit": 6},
    {"id": "npr_news", "url": "https://feeds.npr.org/1001/rss.xml", "category": "News", "limit": 5},
    {"id": "gn_tech", "url": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en", "category": "Tech", "limit": 8},
    {"id": "gn_ent", "url": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en", "category": "Culture", "limit": 7},
    {"id": "npr_culture", "url": "https://feeds.npr.org/1008/rss.xml", "category": "Culture", "limit": 4},
    {"id": "npr_music", "url": "https://feeds.npr.org/1039/rss.xml", "category": "Music", "limit": 6},
    {"id": "gn_sci", "url": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-US&gl=US&ceid=US:en", "category": "Science & Nature", "limit": 7},
    {"id": "npr_science", "url": "https://feeds.npr.org/1007/rss.xml", "category": "Science & Nature", "limit": 4},
    {"id": "gn_pol", "url": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=en-US&gl=US&ceid=US:en", "category": "Politics", "limit": 8},
    {"id": "gn_biz", "url": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en", "category": "Markets", "limit": 6},
]

TRENDS_URL = "https://trends.google.com/trending/rss?geo=US"
TRENDS_NS = "https://trends.google.com/trending/rss"

MUSIC_WORDS = re.compile(
    r"\b(album|song|songs|single|ep\b|tour|concert|grammy|billboard|"
    r"rapper|rap\b|singer|band|musician|soundtrack|spotify|playlist|"
    r"tiny desk|guitar|orchestra|opera|hip-?hop|country music|pop star|"
    r"mixtape|debut album|new album|music)\b",
    re.I,
)
SCIENCE_WORDS = re.compile(
    r"\b(species|bird|whale|genome|nasa|planet|asteroid|climate|"
    r"dinosaur|fossil|scientist|biology|physics|telescope|moon|"
    r"earthquake|volcano|wildlife|animal|ocean|coral)\b",
    re.I,
)

TEMPLATES = {
    "News": [
        ("HOTFIX", "Hotfix applied: {title}"),
        ("UPDATED", "World state updated: {title}"),
        ("PATCH", "Incident report filed: {title}"),
        ("UPDATED", "Server announcement: {title}"),
        ("FIXED", "Stability pass addressing: {title}"),
        ("KNOWN ISSUE", "Known issue logged: {title}"),
    ],
    "Tech": [
        ("ADDED", "New feature rolled out: {title}"),
        ("PATCH", "Vendor pushed a patch: {title}"),
        ("UPDATED", "Experimental build notes: {title}"),
        ("BUFFED", "Hardware / software buff: {title}"),
        ("HOTFIX", "Engineering hotfix: {title}"),
        ("KNOWN ISSUE", "Known bug reported: {title}"),
    ],
    "Culture": [
        ("ADDED", "Seasonal event added: {title}"),
        ("UPDATED", "Cosmetic update: {title}"),
        ("ADDED", "New storyline unlocked: {title}"),
        ("PATCH", "Lore codex expanded: {title}"),
        ("BUFFED", "Cultural meta shift: {title}"),
    ],
    "Music": [
        ("ADDED", "Audio DLC dropped: {title}"),
        ("ADDED", "New soundtrack entry: {title}"),
        ("UPDATED", "Now playing, per the patch notes: {title}"),
        ("BUFFED", "Sound mix buffed: {title}"),
        ("PATCH", "Listening queue updated: {title}"),
    ],
    "Science & Nature": [
        ("ADDED", "Path notes: {title}"),
        ("ADDED", "Bestiary updated: {title}"),
        ("UPDATED", "Physics engine tweak: {title}"),
        ("PATCH", "Field research patch: {title}"),
        ("ADDED", "New species / system documented: {title}"),
        ("HOTFIX", "Nature deployed a hotfix: {title}"),
    ],
    "Slang": [
        ("ADDED", "Players are now searching for: {title}"),
        ("ADDED", "New slang added to the vocabulary: {title}"),
        ("UPDATED", "Search meta update: {title} is climbing"),
        ("ADDED", "Cultural ping logged: {title}"),
        ("PATCH", "Trend compiled into today's build: {title}"),
        ("BUFFED", "Vocabulary buff: {title}"),
    ],
    "Politics": [
        ("UPDATED", "Faction balance update: {title}"),
        ("PATCH", "Governance patch: {title}"),
        ("UPDATED", "Policy tree changed: {title}"),
        ("HOTFIX", "Civic hotfix: {title}"),
        ("NERFED", "Power ranking shuffle: {title}"),
        ("KNOWN ISSUE", "Debate thread marked open: {title}"),
    ],
    "Markets": [
        ("UPDATED", "Economy rebalance: {title}"),
        ("PATCH", "Market bulletin: {title}"),
        ("HOTFIX", "Trading-floor hotfix: {title}"),
        ("BUFFED", "Risk-on patch: {title}"),
        ("NERFED", "Risk-off patch: {title}"),
        ("UPDATED", "Ledger updated: {title}"),
    ],
}

CATEGORIES = [
    "News",
    "Tech",
    "Culture",
    "Music",
    "Science & Nature",
    "Slang",
    "Politics",
    "Markets",
]


def log(msg: str) -> None:
    print(msg, flush=True)


def now_et() -> datetime:
    return datetime.now(TZ)


def week_of_month(dt: datetime) -> int:
    return (dt.day - 1) // 7 + 1


def patch_kind(dt: datetime) -> str:
    return "Morning" if dt.hour < 12 else "Evening"


def patch_meta(dt: datetime) -> dict:
    kind = patch_kind(dt)
    pid = f"{dt:%Y-%m-%d}-{kind.lower()}"
    label = f"v{dt:%Y}.{dt.month} · Week {week_of_month(dt)} · {dt:%b} {dt.day} ({kind} patch)"
    return {
        "id": pid,
        "label": label,
        "kind": kind,
        "year": dt.year,
        "month": dt.month,
        "week": week_of_month(dt),
        "day": dt.day,
        "iso": dt.isoformat(timespec="seconds"),
        "display_date": dt.strftime("%A, %B %-d, %Y, %-I:%M %p ET"),
    }


def fetch(url: str, timeout: int = 25, retries: int = 2) -> bytes | None:
    global YAHOO_BLOCKED
    is_yahoo = "finance.yahoo.com" in url
    if is_yahoo and YAHOO_BLOCKED:
        return None
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/rss+xml, application/xml, text/xml, application/json, text/csv, */*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    last_err = None
    attempts = 1 if is_yahoo else retries
    for attempt in range(attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 — we want the build to continue
            last_err = exc
            if "429" in str(exc) and is_yahoo:
                if attempt < attempts:
                    time.sleep(15)
                    continue
                YAHOO_BLOCKED = True
                break
            if attempt < attempts:
                time.sleep(1.5)
    log(f"  FAIL {url} ({type(last_err).__name__}: {last_err})")
    return None


def local(tag: str) -> str:
    return tag.split("}", 1)[-1] if tag.startswith("{") else tag


def text_of(el: ET.Element | None) -> str:
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def parse_rss(data: bytes) -> list[dict]:
    items: list[dict] = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return items
    for item in root.iter():
        if local(item.tag) != "item":
            continue
        title = ""
        link = ""
        source = ""
        published = ""
        for child in list(item):
            name = local(child.tag)
            if name == "title":
                title = text_of(child)
            elif name == "link":
                link = text_of(child)
            elif name == "pubDate":
                published = text_of(child)
            elif name == "source":
                source = text_of(child)
        if not title:
            continue
        for sep in (" - ", " – ", " — "):
            if sep in title:
                maybe_title, maybe_source = title.rsplit(sep, 1)
                maybe_source = maybe_source.strip()
                if source and maybe_source.lower() == source.lower():
                    title = maybe_title.strip()
                    break
                if not source and 1 < len(maybe_source) < 48:
                    title, source = maybe_title.strip(), maybe_source
                    break
        items.append(
            {
                "title": re.sub(r"\s+", " ", title).strip(),
                "link": link.strip(),
                "source": source.strip(),
                "published": published.strip(),
            }
        )
    return items


def norm_key(title: str) -> str:
    t = title.lower()
    t = re.sub(r"['’]", "", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()[:96]


def pick_template(category: str, title: str) -> tuple[str, str]:
    options = TEMPLATES[category]
    idx = int(hashlib.sha1(title.encode("utf-8")).hexdigest(), 16) % len(options)
    tag, tmpl = options[idx]
    return tag, tmpl.format(title=title)


def recategorize(category: str, title: str) -> str:
    if category in ("Culture", "News") and MUSIC_WORDS.search(title):
        return "Music"
    if category in ("News", "Tech") and SCIENCE_WORDS.search(title) and category != "Tech":
        return "Science & Nature"
    return category


def collect_headlines() -> tuple[list[dict], list[str]]:
    used: set[str] = set()
    notes: list[dict] = []
    sources_ok: list[str] = []
    for feed in FEEDS:
        log(f"Fetching {feed['id']}…")
        raw = fetch(feed["url"])
        if not raw:
            continue
        entries = parse_rss(raw)
        if not entries:
            log(f"  empty: {feed['id']}")
            continue
        sources_ok.append(feed["id"])
        kept = 0
        for entry in entries:
            key = norm_key(entry["title"])
            if not key or key in used:
                continue
            if not entry["link"]:
                continue
            category = recategorize(feed["category"], entry["title"])
            tag, line = pick_template(category, entry["title"])
            notes.append(
                {
                    "id": hashlib.sha1(key.encode()).hexdigest()[:12],
                    "category": category,
                    "tag": tag,
                    "line": line,
                    "title": entry["title"],
                    "url": entry["link"],
                    "source": entry["source"] or feed["id"].replace("_", " "),
                    "kind": "headline",
                }
            )
            used.add(key)
            kept += 1
            if kept >= feed["limit"]:
                break
        log(f"  {feed['id']}: {len(entries)} items, kept {kept}")
    return notes, sources_ok


def parse_trends(data: bytes) -> list[dict]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return []
    out = []
    for item in root.iter():
        if local(item.tag) != "item":
            continue
        title = ""
        traffic = ""
        news_url = ""
        news_source = ""
        for child in list(item):
            name = local(child.tag)
            ns = child.tag[1:].split("}", 1)[0] if child.tag.startswith("{") else ""
            if name == "title":
                title = text_of(child)
            elif name == "approx_traffic" and ns == TRENDS_NS:
                traffic = text_of(child)
            elif name == "news_item" and ns == TRENDS_NS and not news_url:
                for sub in list(child):
                    sn = local(sub.tag)
                    if sn == "news_item_url":
                        news_url = text_of(sub)
                    elif sn == "news_item_source":
                        news_source = text_of(sub)
        if not title:
            continue
        query = urllib.parse.quote_plus(title)
        out.append(
            {
                "title": title,
                "traffic": traffic,
                "url": f"https://trends.google.com/trends/explore?geo=US&q={query}",
                "news_url": news_url,
                "news_source": news_source,
            }
        )
    return out


def collect_trends() -> tuple[list[dict], list[dict], bool]:
    log("Fetching Google Trends US…")
    raw = fetch(TRENDS_URL)
    if not raw:
        return [], [], False
    trends = parse_trends(raw)[:12]
    notes = []
    for t in trends:
        tag, line = pick_template("Slang", t["title"])
        source = "Google Trends (US)"
        if t.get("traffic"):
            source = f"Google Trends (US) · {t['traffic']} searches"
        notes.append(
            {
                "id": hashlib.sha1(f"trend:{t['title']}".encode()).hexdigest()[:12],
                "category": "Slang",
                "tag": tag,
                "line": line,
                "title": t["title"],
                "url": t["url"],
                "source": source,
                "kind": "trend",
                "related": t.get("news_url") or "",
                "related_source": t.get("news_source") or "",
            }
        )
    log(f"  trends: {len(trends)}")
    return notes, trends, True


def _quotes_from_screener(payload: dict) -> list[dict]:
    try:
        return payload["finance"]["result"][0].get("quotes") or []
    except (KeyError, IndexError, TypeError):
        return []


def _pct(q: dict) -> float | None:
    val = q.get("regularMarketChangePercent")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _stock_note(q: dict, force: str | None = None) -> dict | None:
    symbol = q.get("symbol")
    price = q.get("regularMarketPrice")
    pct = _pct(q)
    if not symbol or price is None or pct is None:
        return None
    name = q.get("shortName") or q.get("displayName") or q.get("longName") or symbol
    direction = force or ("BUFFED" if pct >= 0 else "NERFED")
    verb = "buffed" if direction == "BUFFED" else "nerfed"
    sign = "+" if pct >= 0 else ""
    line = f"{name} ({symbol}) {verb} {sign}{pct:.2f}%  ·  last ${float(price):,.2f}"
    return {
        "id": hashlib.sha1(f"stock:{symbol}".encode()).hexdigest()[:12],
        "category": "Markets",
        "tag": direction,
        "line": line,
        "title": f"{name} ({symbol}) {sign}{pct:.2f}%",
        "url": f"https://finance.yahoo.com/quote/{urllib.parse.quote(symbol)}",
        "source": "Yahoo Finance",
        "kind": "stock",
        "symbol": symbol,
        "price": float(price),
        "change_pct": pct,
    }


def _normalize_percents(quotes: list[dict]) -> list[dict]:
    pcts = [p for q in quotes if (p := _pct(q)) is not None]
    if pcts and max(abs(p) for p in pcts) <= 1.5:
        for q in quotes:
            if q.get("regularMarketChangePercent") is not None:
                q = q  # copy not needed; mutate a shadow below
        out = []
        for q in quotes:
            q = dict(q)
            if q.get("regularMarketChangePercent") is not None:
                q["regularMarketChangePercent"] = float(q["regularMarketChangePercent"]) * 100
            out.append(q)
        return out
    return quotes


def _chart_quote(symbol: str) -> dict | None:
    enc = urllib.parse.quote(symbol, safe="")
    raw = fetch(f"https://query1.finance.yahoo.com/v8/finance/chart/{enc}?interval=1d&range=2d")
    if not raw:
        raw = fetch(f"https://query2.finance.yahoo.com/v8/finance/chart/{enc}?interval=1d&range=2d")
    if not raw:
        return None
    try:
        payload = json.loads(raw)
        meta = payload["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        prev = meta.get("previousClose") or meta.get("chartPreviousClose")
        if price is None or not prev:
            return None
        pct = (float(price) - float(prev)) / float(prev) * 100
        return {
            "symbol": meta.get("symbol") or symbol,
            "shortName": meta.get("shortName") or symbol,
            "regularMarketPrice": float(price),
            "regularMarketChangePercent": pct,
        }
    except Exception:  # noqa: BLE001
        return None


def collect_stocks() -> tuple[list[dict], str, bool]:
    log("Fetching stock movers…")
    notes: list[dict] = []
    mode = "movers"

    def screener(scr_id: str) -> list[dict]:
        for host in ("query1", "query2"):
            time.sleep(0.4)
            url = (
                f"https://{host}.finance.yahoo.com/v1/finance/screener/predefined/saved"
                f"?formatted=false&lang=en-US&region=US&scrIds={scr_id}&count=8"
            )
            raw = fetch(url)
            if not raw:
                continue
            try:
                quotes = _quotes_from_screener(json.loads(raw))
            except json.JSONDecodeError:
                continue
            if quotes:
                return _normalize_percents(quotes)
        return []

    gainers = screener("day_gainers")
    losers = screener("day_losers")
    for q in gainers:
        note = _stock_note(q, "BUFFED")
        if note:
            notes.append(note)
    for q in losers:
        note = _stock_note(q, "NERFED")
        if note:
            notes.append(note)

    if notes:
        log(f"  movers: {len(notes)} (gainers={len(gainers)} losers={len(losers)})")
        return notes, mode, True

    log("  movers unavailable; falling back to major index ETFs")
    mode = "indexes"
    for sym, name in (
        ("SPY", "S&P 500 ETF"),
        ("QQQ", "Nasdaq-100 ETF"),
        ("DIA", "Dow Jones ETF"),
        ("IWM", "Russell 2000 ETF"),
        ("^GSPC", "S&P 500"),
        ("^DJI", "Dow Jones"),
        ("^IXIC", "Nasdaq Composite"),
    ):
        time.sleep(0.7)
        q = _chart_quote(sym)
        if not q:
            continue
        q["shortName"] = name
        note = _stock_note(q)
        if note:
            notes.append(note)
    if notes:
        return notes, mode, True
    log("  no stock data")
    return [], "unavailable", False


def load_archive() -> list[dict]:
    path = DATA / "archive.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def render_page(
    *,
    title: str,
    description: str,
    canonical: str,
    prefix: str,
    body: str,
    updated: str | None = None,
) -> str:
    esc = html.escape
    og_title = esc(title)
    og_desc = esc(description)
    canon = esc(canonical)
    pre = esc(prefix)
    updated_meta = f'\n  <meta property="og:updated_time" content="{esc(updated)}">' if updated else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{og_title}</title>
  <meta name="description" content="{og_desc}">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{canon}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Real Life v2026">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{og_desc}">
  <meta property="og:url" content="{canon}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{og_title}">
  <meta name="twitter:description" content="{og_desc}">
  <meta name="theme-color" content="#10150f">{updated_meta}
  <link rel="icon" href="{pre}assets/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{pre}assets/style.css">
  <script type="application/ld+json">
  {json.dumps({
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "Real Life v2026",
      "url": SITE_URL + "/",
      "description": "Satirical patch notes for real life in the United States. Every item is based on a real, linked source.",
      "inLanguage": "en-US",
  })}
  </script>
</head>
<body>
  <a class="skip" href="#main">Skip to patch notes</a>
  <header class="top">
    <div class="wrap top-row">
      <a class="brand" href="{pre}index.html">
        <span class="logo" aria-hidden="true">RL</span>
        <span>
          <strong>Real Life</strong>
          <em>v2026</em>
        </span>
      </a>
      <p class="satire-flag">Satire — real news, written as video-game patch notes. Nothing here is invented; every item links to its source.</p>
    </div>
    <div class="ticker-wrap" aria-live="polite">
      <div class="wrap ticker" id="crypto-ticker" data-endpoint="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple,dogecoin,cardano&amp;vs_currencies=usd&amp;include_24hr_change=true">
        <span class="ticker-label">Crypto (live)</span>
        <span class="ticker-status">Loading prices…</span>
      </div>
    </div>
  </header>
  {body}
  <footer class="site-foot">
    <div class="wrap">
      <p><strong>Real Life v2026</strong> is a satirical changelog for life in the United States. Headlines, trends, and market moves are pulled from public feeds and framed as patch notes. The joke is the framing, not the facts. We do not invent events.</p>
      <p>Updated automatically at 8:00 AM and 6:00 PM Eastern (13:00 and 23:00 UTC). Crypto prices refresh in your browser from CoinGecko and are not part of the written patch. This site is unofficial and not affiliated with any newsroom, company, or platform it links to.</p>
      <nav>
        <a href="{pre}index.html">Latest patch</a>
        <a href="{pre}archive/index.html">Archive</a>
        <a href="https://github.com/theroundtable-byte/real-life-v2026">Source</a>
      </nav>
    </div>
  </footer>
  <script src="{pre}assets/app.js" defer></script>
</body>
</html>
"""


def note_article(item: dict) -> str:
    cat = html.escape(item["category"])
    tag = html.escape(item["tag"])
    slug = re.sub(r"[^a-z0-9]+", "-", item["tag"].lower()).strip("-")
    line = html.escape(item["line"])
    source = html.escape(item["source"])
    url = html.escape(item["url"], quote=True)
    related = ""
    if item.get("related"):
        rtitle = html.escape(item.get("related_source") or "related story")
        rurl = html.escape(item["related"], quote=True)
        related = f' · <a href="{rurl}" rel="noopener noreferrer">Related: {rtitle}</a>'
    text = html.escape((item["line"] + " " + item["title"] + " " + item["category"]).lower())
    return (
        f'<article class="note" data-category="{cat}" data-text="{text}">'
        f'<div class="note-meta"><span class="tag tag-{slug}">{tag}</span>'
        f'<span class="cat">{cat}</span></div>'
        f"<h3>{line}</h3>"
        f'<p class="src">Source: <a href="{url}" rel="noopener noreferrer">{source}</a>{related}</p>'
        f"</article>"
    )


def filters_html() -> str:
    chips = ['<button type="button" class="chip is-on" data-filter="all">All</button>']
    for cat in CATEGORIES:
        chips.append(
            f'<button type="button" class="chip" data-filter="{html.escape(cat)}">{html.escape(cat)}</button>'
        )
    return (
        '<div class="tools">'
        '<label class="search"><span class="sr">Search patch notes</span>'
        '<input id="q" type="search" placeholder="Search patch notes…" autocomplete="off"></label>'
        f'<div class="chips" role="tablist" aria-label="Filter by category">{"".join(chips)}</div>'
        "</div>"
    )


def render_index(meta: dict, notes: list[dict], trends: list[dict], stock_mode: str, archive: list[dict]) -> str:
    groups = {c: [] for c in CATEGORIES}
    for n in notes:
        groups.setdefault(n["category"], []).append(n)

    trend_block = ""
    if trends:
        pills = []
        for t in trends:
            q = urllib.parse.quote_plus(t["title"])
            href = html.escape(f"https://trends.google.com/trends/explore?geo=US&q={q}", quote=True)
            traffic = f' <small>{html.escape(t["traffic"])}</small>' if t.get("traffic") else ""
            pills.append(f'<a class="trend" href="{href}" rel="noopener noreferrer">{html.escape(t["title"])}{traffic}</a>')
        trend_block = (
            '<section class="trends" aria-labelledby="trends-h">'
            "<h2 id=\"trends-h\">Trending in the US today</h2>"
            "<p class=\"lede\">What people are searching on Google, snapped into this build.</p>"
            f'<div class="trend-row">{"".join(pills)}</div>'
            "</section>"
        )

    sections = []
    for cat in CATEGORIES:
        items = groups.get(cat) or []
        if not items:
            continue
        cards = "".join(note_article(n) for n in items)
        sections.append(
            f'<section class="cat-section" data-category="{html.escape(cat)}" aria-labelledby="h-{html.escape(cat)}">'
            f'<h2 id="h-{html.escape(cat)}">{html.escape(cat)} <span>{len(items)}</span></h2>'
            f'<div class="notes">{cards}</div>'
            "</section>"
        )

    if stock_mode == "movers":
        market_note = (
            '<p class="lede">Top US day gainers and losers, logged as buffs and nerfs. '
            "Quotes via Yahoo Finance.</p>"
        )
    elif stock_mode == "indexes":
        market_note = (
            '<p class="callout">Major US indexes and ETFs are shown this run. '
            "A full day-movers list was not available from the free feed.</p>"
        )
    else:
        market_note = (
            '<p class="callout">Stock quotes were unavailable this run. '
            "Market headlines from public news feeds still appear below, and crypto prices stay live in the ticker.</p>"
        )

    prev = ""
    others = [p for p in archive if p.get("id") != meta["id"]][:10]
    if others:
        lis = []
        for p in others:
            lis.append(
                f'<li><a href="archive/{html.escape(p["id"])}.html">{html.escape(p["label"])}</a></li>'
            )
        prev = (
            '<section class="prior">'
            "<h2>Previous patches</h2>"
            f'<ul>{"".join(lis)}</ul>'
            '<p><a href="archive/index.html">Browse the full archive</a></p>'
            "</section>"
        )

    body = f"""
  <main id="main">
    <div class="wrap">
      <section class="hero">
        <p class="kicker">Patch notes for America</p>
        <h1>{html.escape(meta["label"])}</h1>
        <p class="when">Published {html.escape(meta["display_date"])} · {len(notes)} entries</p>
        <p class="intro">A constantly updating changelog for real life in the United States: news, tech, culture, music, science, slang, politics, and markets. Written like a game update. Sourced like a newspaper.</p>
      </section>
      {trend_block}
      {filters_html()}
      <p class="market-head">Markets this patch</p>
      {market_note}
      <div id="notes">{"".join(sections)}</div>
      <p class="empty" id="empty" hidden>No patch notes match that filter. Try another category or clear the search.</p>
      {prev}
    </div>
  </main>
"""
    desc = (
        f"Satirical US patch notes for {meta['label']}. Real headlines, Google Trends, "
        "stocks, and live crypto, framed as a video-game changelog."
    )
    return render_page(
        title=f"Real Life {meta['label']} — Patch Notes for America",
        description=desc,
        canonical=f"{SITE_URL}/",
        prefix="",
        body=body,
        updated=meta["iso"],
    )


def render_archive_index(archive: list[dict]) -> str:
    if not archive:
        lis = "<p>No patches stored yet.</p>"
    else:
        items = []
        for p in archive:
            items.append(
                f'<li><a href="{html.escape(p["id"])}.html"><strong>{html.escape(p["label"])}</strong>'
                f'<span>{html.escape(p.get("display_date", ""))} · {p.get("count", 0)} entries</span></a></li>'
            )
        lis = f'<ol class="archive-list">{"".join(items)}</ol>'
    body = f"""
  <main id="main">
    <div class="wrap">
      <section class="hero">
        <p class="kicker"><a href="../index.html">← Latest patch</a></p>
        <h1>Patch archive</h1>
        <p class="intro">The last {MAX_ARCHIVE} builds, newest first. Each one is a real snapshot of that morning or evening.</p>
      </section>
      {lis}
    </div>
  </main>
"""
    return render_page(
        title="Archive — Real Life v2026",
        description="Browse past satirical US patch notes, morning and evening builds of Real Life v2026.",
        canonical=f"{SITE_URL}/archive/",
        prefix="../",
        body=body,
    )


def render_archive_patch(meta: dict, notes: list[dict], trends: list[dict], stock_mode: str) -> str:
    groups = {c: [] for c in CATEGORIES}
    for n in notes:
        groups.setdefault(n["category"], []).append(n)
    sections = []
    for cat in CATEGORIES:
        items = groups.get(cat) or []
        if not items:
            continue
        cards = "".join(note_article(n) for n in items)
        sections.append(
            f'<section class="cat-section" data-category="{html.escape(cat)}">'
            f"<h2>{html.escape(cat)} <span>{len(items)}</span></h2>"
            f'<div class="notes">{cards}</div>'
            "</section>"
        )
    trend_block = ""
    if trends:
        pills = []
        for t in trends:
            q = urllib.parse.quote_plus(t["title"])
            href = html.escape(f"https://trends.google.com/trends/explore?geo=US&q={q}", quote=True)
            pills.append(f'<a class="trend" href="{href}" rel="noopener noreferrer">{html.escape(t["title"])}</a>')
        trend_block = f'<section class="trends"><h2>Trending that day</h2><div class="trend-row">{"".join(pills)}</div></section>'
    body = f"""
  <main id="main">
    <div class="wrap">
      <section class="hero">
        <p class="kicker"><a href="../index.html">Latest patch</a> · <a href="index.html">Archive</a></p>
        <h1>{html.escape(meta["label"])}</h1>
        <p class="when">Published {html.escape(meta["display_date"])} · {len(notes)} entries</p>
      </section>
      {trend_block}
      {filters_html()}
      <div id="notes">{"".join(sections)}</div>
      <p class="empty" id="empty" hidden>No patch notes match that filter.</p>
    </div>
  </main>
"""
    return render_page(
        title=f"Real Life {meta['label']} — Archive",
        description=f"Archived satirical US patch notes for {meta['label']}.",
        canonical=f"{SITE_URL}/archive/{meta['id']}.html",
        prefix="../",
        body=body,
        updated=meta["iso"],
    )


def write_robots_and_sitemap(archive: list[dict], now: datetime) -> None:
    (SITE / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    urls = [
        (f"{SITE_URL}/", now, "hourly"),
        (f"{SITE_URL}/archive/", now, "daily"),
    ]
    for p in archive:
        urls.append((f"{SITE_URL}/archive/{p['id']}.html", p.get("iso") or now.isoformat(), "weekly"))
    chunks = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, freq in urls:
        lm = lastmod if isinstance(lastmod, str) else lastmod.isoformat()
        chunks.append(
            f"  <url><loc>{html.escape(loc)}</loc><lastmod>{html.escape(str(lm)[:25])}</lastmod>"
            f"<changefreq>{freq}</changefreq></url>"
        )
    chunks.append("</urlset>\n")
    (SITE / "sitemap.xml").write_text("\n".join(chunks), encoding="utf-8")


def write_site(meta: dict, notes: list[dict], trends: list[dict], stock_mode: str) -> None:
    for path in (SITE, DATA, PATCHES, ARCHIVE, SITE / "assets"):
        path.mkdir(parents=True, exist_ok=True)

    archive = load_archive()
    summary = {
        "id": meta["id"],
        "label": meta["label"],
        "kind": meta["kind"],
        "iso": meta["iso"],
        "display_date": meta["display_date"],
        "count": len(notes),
        "stock_mode": stock_mode,
    }
    archive = [p for p in archive if p.get("id") != meta["id"]]
    archive.insert(0, summary)
    dropped = archive[MAX_ARCHIVE:]
    archive = archive[:MAX_ARCHIVE]
    for old in dropped:
        for p in (ARCHIVE / f"{old['id']}.html", PATCHES / f"{old['id']}.json"):
            if p.exists():
                p.unlink()

    payload = {"meta": meta, "stock_mode": stock_mode, "trends": trends, "notes": notes}
    (DATA / "latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (PATCHES / f"{meta['id']}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (DATA / "archive.json").write_text(json.dumps(archive, indent=2), encoding="utf-8")

    (SITE / "index.html").write_text(
        render_index(meta, notes, trends, stock_mode, archive), encoding="utf-8"
    )
    (ARCHIVE / "index.html").write_text(render_archive_index(archive), encoding="utf-8")
    (ARCHIVE / f"{meta['id']}.html").write_text(
        render_archive_patch(meta, notes, trends, stock_mode), encoding="utf-8"
    )

    # Refresh other archive pages so nav stays consistent; skip rewrite of huge history.
    write_robots_and_sitemap(archive, now_et())
    log(f"Wrote site for {meta['label']} ({len(notes)} notes, archive={len(archive)})")


def main() -> int:
    dt = now_et()
    meta = patch_meta(dt)
    log(f"Generating {meta['label']}")
    headlines, ok_feeds = collect_headlines()
    trend_notes, trends, trends_ok = collect_trends()
    stock_notes, stock_mode, stocks_ok = collect_stocks()
    notes = headlines + trend_notes + stock_notes
    if not notes:
        log("No content collected; aborting so we do not overwrite a good build.")
        return 1
    write_site(meta, notes, trends, stock_mode)
    log("Sources OK: " + ", ".join(ok_feeds + (["trends"] if trends_ok else []) + (["stocks"] if stocks_ok else [])))
    log(f"Stock mode: {stock_mode}")
    return 0


if __name__ == "__main__":
    # %-d / %-I is Linux-only; provide a portable fallback for display dates.
    if sys.platform == "win32":
        pass
    try:
        sys.exit(main())
    except Exception:
        raise
