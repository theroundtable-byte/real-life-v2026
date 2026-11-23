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
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DATA = SITE / "data"
PATCHES = DATA / "patches"
ARCHIVE = SITE / "archive"
WEEKLY_OUT = SITE / "weekly"
CONTENT = ROOT / "content"
WEEKLY_DIR = CONTENT / "weekly"
WATCHLIST_PATH = CONTENT / "watchlist.json"
PATCH_IN = CONTENT / "patches"
TZ = ZoneInfo("America/New_York")
SITE_URL = "https://theroundtable-byte.github.io/real-life-v2026"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
NWS_UA = "(RealLifeV2026; https://theroundtable-byte.github.io/real-life-v2026/)"
CTX = ssl.create_default_context()
MAX_ARCHIVE = 60
YAHOO_BLOCKED = False

FEEDS = [
    {"id": "gn_top", "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", "category": "News", "limit": 6},
    {"id": "gn_nat", "url": "https://news.google.com/rss/headlines/section/topic/NATION?hl=en-US&gl=US&ceid=US:en", "category": "News", "limit": 5},
    {"id": "npr_news", "url": "https://feeds.npr.org/1001/rss.xml", "category": "News", "limit": 4},
    {"id": "gn_tech", "url": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en", "category": "Tech", "limit": 6},
    {"id": "gn_ent", "url": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en", "category": "Culture", "limit": 5},
    {"id": "npr_culture", "url": "https://feeds.npr.org/1008/rss.xml", "category": "Culture", "limit": 3},
    {"id": "npr_music", "url": "https://feeds.npr.org/1039/rss.xml", "category": "Music", "limit": 5},
    {"id": "gn_sci", "url": "https://news.google.com/rss/headlines/section/topic/SCIENCE?hl=en-US&gl=US&ceid=US:en", "category": "Science & Nature", "limit": 6},
    {"id": "npr_science", "url": "https://feeds.npr.org/1007/rss.xml", "category": "Science & Nature", "limit": 3},
    {"id": "gn_species", "url": "https://news.google.com/rss/search?q=%22new+species%22+when:2d&hl=en-US&gl=US&ceid=US:en", "category": "Science & Nature", "limit": 5, "weird": True},
    {"id": "gn_discover", "url": "https://news.google.com/rss/search?q=%22scientists+discover%22+OR+%22scientists+have+found%22+when:2d&hl=en-US&gl=US&ceid=US:en", "category": "Science & Nature", "limit": 4, "weird": True},
    {"id": "gn_weird", "url": "https://news.google.com/rss/search?q=bizarre+OR+odd+OR+viral+OR+%22scientists+discover%22+US+when:2d&hl=en-US&gl=US&ceid=US:en", "category": "News", "limit": 4, "weird": True},
    {"id": "gn_pol", "url": "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=en-US&gl=US&ceid=US:en", "category": "Politics", "limit": 6},
    {"id": "gn_biz", "url": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en", "category": "Markets", "limit": 5},
    {"id": "ign", "url": "https://feeds.ign.com/ign/all", "category": "Gaming", "limit": 6},
    {"id": "polygon", "url": "https://www.polygon.com/rss/index.xml", "category": "Gaming", "limit": 5},
    {"id": "kotaku", "url": "https://kotaku.com/rss", "category": "Gaming", "limit": 4},
    {"id": "gamespot", "url": "https://www.gamespot.com/feeds/news/", "category": "Gaming", "limit": 4},
    {"id": "gn_gaming", "url": "https://news.google.com/rss/search?q=PlayStation+OR+Xbox+OR+Nintendo+OR+%22GTA+6%22+OR+%22video+game%22+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "Gaming", "limit": 4},
    {"id": "variety", "url": "https://variety.com/feed/", "category": "Movies & TV", "limit": 5},
    {"id": "hollywood", "url": "https://www.hollywoodreporter.com/feed/", "category": "Movies & TV", "limit": 4},
    {"id": "deadline", "url": "https://deadline.com/feed/", "category": "Movies & TV", "limit": 4},
    {"id": "gn_movies", "url": "https://news.google.com/rss/search?q=movie+OR+film+OR+%22TV+series%22+OR+Netflix+OR+trailer+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "Movies & TV", "limit": 5},
    {"id": "ann_news", "url": "https://www.animenewsnetwork.com/news/rss.xml", "category": "Anime & Manga", "limit": 6},
    {"id": "crunchyroll", "url": "https://cr-news-api-service.prd.crunchyrollsvc.com/v1/en-US/rss", "category": "Anime & Manga", "limit": 5},
    {"id": "mal", "url": "https://myanimelist.net/rss/news.xml", "category": "Anime & Manga", "limit": 5},
    {"id": "gn_anime", "url": "https://news.google.com/rss/search?q=anime+OR+manga+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "Anime & Manga", "limit": 4},
    {"id": "gn_sports", "url": "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=en-US&gl=US&ceid=US:en", "category": "Sports", "limit": 8},
    {"id": "espn", "url": "https://www.espn.com/espn/rss/news", "category": "Sports", "limit": 6},
    {"id": "gn_weather", "url": "https://news.google.com/rss/search?q=US+storm+OR+hurricane+OR+flood+OR+blizzard+OR+wildfire+OR+%22weather+alert%22+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "Weather & Disasters", "limit": 5},
    {"id": "gn_travel", "url": "https://news.google.com/rss/search?q=Thanksgiving+travel+OR+%22Black+Friday%22+OR+holiday+when:1d&hl=en-US&gl=US&ceid=US:en", "category": "Holidays & Events", "limit": 6},
    {"id": "fda_food", "url": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/food-safety-recalls/rss.xml", "category": "Health & Recalls", "limit": 8},
    {"id": "cdc_new", "url": "https://tools.cdc.gov/api/v2/resources/media/316422.rss", "category": "Health & Recalls", "limit": 5, "title_re": r"recall|outbreak|advisory|contamination|undeclared|foodborne"},
    {"id": "gn_gas", "url": "https://news.google.com/rss/search?q=%22gas+prices%22+OR+%22grocery+prices%22+OR+%22egg+prices%22+US+when:7d&hl=en-US&gl=US&ceid=US:en", "category": "Gas & Grocery", "limit": 6},
]

TRENDS_URL = "https://trends.google.com/trending/rss?geo=US"
TRENDS_NS = "https://trends.google.com/trending/rss"

MUSIC_WORDS = re.compile(r"\b(album|song|songs|single|ep\b|tour|concert|grammy|billboard|rapper|singer|band|musician|soundtrack|spotify|playlist|tiny desk|guitar|hip-?hop|mixtape|new album|music)\b", re.I)
SCIENCE_WORDS = re.compile(r"\b(species|bird|whale|genome|nasa|planet|asteroid|climate|dinosaur|fossil|scientist|telescope|wildlife|animal|ocean|coral)\b", re.I)
GAMING_WORDS = re.compile(r"\b(video game|videogame|playstation|xbox|nintendo|steam|esports|fortnite|gta\b|rpg\b|game of the year|gaming)\b", re.I)
MOVIE_WORDS = re.compile(r"\b(movie|film|box office|netflix|hulu|disney\+|trailer|tv series|season \d|oscars|emmy|hollywood|streaming series)\b", re.I)
ANIME_WORDS = re.compile(r"\b(anime|manga|shonen|shounen|crunchyroll|studio ghibli|seiyuu|ova\b|manhwa)\b", re.I)

CATEGORIES = [
    "News", "Sports", "Weather & Disasters", "Holidays & Events",
    "Health & Recalls", "Gas & Grocery", "Gaming", "Movies & TV",
    "Anime & Manga", "Music", "Culture", "Tech", "Science & Nature",
    "Politics", "Slang", "Markets",
]
FILTERS = [
    ("News & Politics", ["News", "Politics"]),
    ("Tech & Science", ["Tech", "Science & Nature"]),
    ("Entertainment", ["Gaming", "Movies & TV", "Anime & Manga", "Music"]),
    ("Sports", ["Sports"]),
    ("Life", ["Weather & Disasters", "Holidays & Events", "Health & Recalls", "Gas & Grocery", "Slang", "Culture"]),
    ("Markets", ["Markets"]),
]
SECTIONS = ["Buffs", "Nerfs", "Hotfixes", "New Content", "Known Bugs", "Limited-Time Events", "Markets"]
# Terminal badge, CSS hook, compact icon for section headers.
SECTION_UI = {
    "Buffs": ("BUFF", "buff", "↑"),
    "Nerfs": ("NERF", "nerf", "↓"),
    "Hotfixes": ("HOTFIX", "hotfix", "✚"),
    "New Content": ("NEW", "new", "+"),
    "Known Bugs": ("BUG", "bug", "!"),
    "Limited-Time Events": ("EVENT", "event", "◈"),
    "Markets": ("MKT", "mkt", "▣"),
}
SECTION_FOR_TAG = {
    "BUFFED": "Buffs", "BALANCE": "Buffs", "ROSTER": "Buffs", "META": "Buffs",
    "NERFED": "Nerfs",
    "HOTFIX": "Hotfixes", "FIXED": "Hotfixes", "UPDATED": "Hotfixes", "PATCH": "Hotfixes",
    "ADDED": "New Content", "DLC": "New Content", "WATCHLIST": "New Content",
    "KNOWN ISSUE": "Known Bugs", "RECALL": "Known Bugs",
    "EVENT": "Limited-Time Events",
}
TAG_LABELS = {
    "BUFFED": "Buffs", "NERFED": "Nerfs", "HOTFIX": "Hotfix",
    "KNOWN ISSUE": "Known bug", "ADDED": "New content", "FIXED": "Fixed",
    "UPDATED": "Patch", "PATCH": "Patch", "DLC": "DLC",
    "ROLLBACK": "Rollback", "META": "Meta", "ROSTER": "Roster update",
    "BALANCE": "Balance change", "EVENT": "Server event",
    "RECALL": "Recall", "WATCHLIST": "Watchlist",
}
FEATURED_LIMIT = 18

# (tag, line, digest). No redundant "Buffs:" / "New content:" prefix — the section header covers that.
TEMPLATES = {
    "News": [
        ("HOTFIX", "World state: {title}", "World state: {title}"),
        ("UPDATED", "World state: {title}", "World state: {title}"),
        ("PATCH", "{title}", "{title}"),
        ("KNOWN ISSUE", "{title}", "{title}"),
        ("FIXED", "{title}", "{title}"),
    ],
    "Tech": [
        ("ADDED", "{title}", "{title}"),
        ("HOTFIX", "{title}", "{title}"),
        ("BUFFED", "{title}", "{title}"),
        ("KNOWN ISSUE", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
        ("UPDATED", "Experimental build: {title}", "Experimental build: {title}"),
    ],
    "Culture": [
        ("ADDED", "{title}", "{title}"),
        ("UPDATED", "Cosmetic: {title}", "Cosmetic: {title}"),
        ("BUFFED", "Meta shift: {title}", "Meta shift: {title}"),
        ("PATCH", "{title}", "{title}"),
    ],
    "Music": [
        ("ADDED", "Soundtrack: {title}", "Soundtrack: {title}"),
        ("BUFFED", "{title}", "{title}"),
        ("UPDATED", "Now playing: {title}", "Now playing: {title}"),
        ("PATCH", "{title}", "{title}"),
    ],
    "Science & Nature": [
        ("ADDED", "Bestiary: {title}", "Bestiary: {title}"),
        ("UPDATED", "{title}", "{title}"),
        ("HOTFIX", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
    ],
    "Slang": [
        ("ADDED", "Players are now searching for: {title}", "Players are now searching for: {title}"),
        ("UPDATED", "{title} is climbing the search meta.", "{title} is climbing the search meta."),
        ("BUFFED", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
    ],
    "Politics": [
        ("BALANCE", "Faction balance: {title}", "Faction balance: {title}"),
        ("PATCH", "{title}", "{title}"),
        ("HOTFIX", "{title}", "{title}"),
        ("KNOWN ISSUE", "{title}", "{title}"),
        ("UPDATED", "{title}", "{title}"),
        ("ROSTER", "Roster: {title}", "Roster: {title}"),
    ],
    "Markets": [
        ("UPDATED", "{title}", "{title}"),
        ("BUFFED", "{title}", "{title}"),
        ("NERFED", "{title}", "{title}"),
        ("HOTFIX", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
    ],
    "Gaming": [
        ("ADDED", "{title}", "{title}"),
        ("BALANCE", "{title}", "{title}"),
        ("HOTFIX", "{title}", "{title}"),
        ("META", "Meta shift: {title}", "Meta shift: {title}"),
        ("KNOWN ISSUE", "{title}", "{title}"),
        ("BUFFED", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
        ("DLC", "DLC: {title}", "DLC: {title}"),
    ],
    "Movies & TV": [
        ("ADDED", "{title}", "{title}"),
        ("DLC", "Season pass: {title}", "Season pass: {title}"),
        ("UPDATED", "Trailer: {title}", "Trailer: {title}"),
        ("PATCH", "{title}", "{title}"),
        ("BUFFED", "{title}", "{title}"),
    ],
    "Anime & Manga": [
        ("ADDED", "{title}", "{title}"),
        ("DLC", "Upcoming: {title}", "Upcoming: {title}"),
        ("UPDATED", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
        ("BUFFED", "{title}", "{title}"),
        ("WATCHLIST", "Watchlist: {title}", "Watchlist: {title}"),
    ],
    "Sports": [
        ("BALANCE", "{title}", "{title}"),
        ("ROSTER", "Roster: {title}", "Roster: {title}"),
        ("BUFFED", "{title}", "{title}"),
        ("NERFED", "{title}", "{title}"),
        ("UPDATED", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
        ("META", "{title}", "{title}"),
    ],
    "Weather & Disasters": [
        ("EVENT", "Server event: {title}", "Server event: {title}"),
        ("HOTFIX", "{title}", "{title}"),
        ("UPDATED", "{title}", "{title}"),
        ("KNOWN ISSUE", "Travel advisory: {title}", "Travel advisory: {title}"),
    ],
    "Holidays & Events": [
        ("ADDED", "{title}", "{title}"),
        ("UPDATED", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
        ("HOTFIX", "{title}", "{title}"),
        ("EVENT", "{title}", "{title}"),
    ],
    "Health & Recalls": [
        ("NERFED", "{title}", "{title}"),
        ("KNOWN ISSUE", "{title}", "{title}"),
        ("RECALL", "{title}", "{title}"),
        ("HOTFIX", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
    ],
    "Gas & Grocery": [
        ("NERFED", "{title}", "{title}"),
        ("BUFFED", "{title}", "{title}"),
        ("UPDATED", "{title}", "{title}"),
        ("PATCH", "{title}", "{title}"),
        ("HOTFIX", "{title}", "{title}"),
    ],
}

KEYWORD_RULES = [
    (re.compile(r"\b(new species|species of|flying frog|fungus)\b", re.I), "ADDED",
     "Bestiary: {title}", "Bestiary: {title}"),
    (re.compile(r"\b(snake|slither|serpent)\b", re.I), "BUFFED",
     "Movement tech: {title}", "Movement tech: {title}"),
    (re.compile(r"\b(frog|whale|bird|lizard|mealybug|chimpanzee)\b", re.I), "ADDED",
     "Bestiary: {title}", "Bestiary: {title}"),
    (re.compile(r"\b(storm|blizzard|hurricane|flood|wildfire|tornado)\b", re.I), "EVENT",
     "Server event: {title}", "Server event: {title}"),
    (re.compile(r"\b(recall|undeclared)\b", re.I), "RECALL",
     "{title}", "{title}"),
    (re.compile(r"\b(trade|traded|signs with|agrees with|releasing|released)\b", re.I), "ROSTER",
     "Roster: {title}", "Roster: {title}"),
    (re.compile(r"\b(upset|blowout|beats|comeback)\b", re.I), "BALANCE",
     "{title}", "{title}"),
    (re.compile(r"\b(black friday|cyber monday|thanksgiving)\b", re.I), "ADDED",
     "{title}", "{title}"),
    (re.compile(r"\b(gas prices?|grocery prices?|egg prices?)\b", re.I), "UPDATED",
     "{title}", "{title}"),
    (re.compile(r"\b(reinstated|returns as|respawn)\b", re.I), "BUFFED",
     "Respawn: {title}", "Respawn: {title}"),
    (re.compile(r"\b(ai\b|chatgpt|chatbot|artificial intelligence)\b", re.I), "UPDATED",
     "{title}", "{title}"),
    (re.compile(r"\b(chapter|volume)\b", re.I), "ADDED",
     "New chapter: {title}", "New chapter: {title}"),
    (re.compile(r"\b(anime announced|anime adaptation|gets an anime)\b", re.I), "DLC",
     "Upcoming anime: {title}", "Upcoming anime: {title}"),
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
    label = f"v{dt:%Y}.{dt.month} · Week {week_of_month(dt)} · {dt:%b} {dt.day} · {kind} Patch"
    return {
        "id": pid, "label": label, "kind": kind, "year": dt.year,
        "month": dt.month, "week": week_of_month(dt), "day": dt.day,
        "iso": dt.isoformat(timespec="seconds"),
        "display_date": dt.strftime("%A, %B %-d, %Y, %-I:%M %p ET"),
    }

def last_sunday(d: date) -> date:
    return d - timedelta(days=(d.weekday() + 1) % 7)

def fetch(url: str, timeout: int = 25, retries: int = 2, headers: dict | None = None) -> bytes | None:
    global YAHOO_BLOCKED
    is_yahoo = "finance.yahoo.com" in url
    if is_yahoo and YAHOO_BLOCKED:
        return None
    h = {
        "User-Agent": NWS_UA if "weather.gov" in url else UA,
        "Accept": "application/geo+json, application/rss+xml, application/xml, text/xml, application/json, text/html, */*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    last_err = None
    attempts = 1 if is_yahoo else retries
    for attempt in range(attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001
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
        name = local(item.tag)
        if name not in {"item", "entry"}:
            continue
        title = link = source = published = ""
        for child in list(item):
            cname = local(child.tag)
            if cname == "title":
                title = text_of(child)
            elif cname == "link":
                link = text_of(child) or (child.get("href") or "").strip()
            elif cname in {"pubDate", "published", "updated", "date"}:
                published = text_of(child)
            elif cname == "source":
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
        items.append({
            "title": re.sub(r"\s+", " ", title).strip(),
            "link": link.strip(),
            "source": source.strip(),
            "published": published.strip(),
        })
    return items

def norm_key(title: str) -> str:
    t = title.lower()
    t = re.sub(r"['’]", "", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()[:96]

def hash_idx(title: str, n: int) -> int:
    return int(hashlib.sha1(title.encode("utf-8")).hexdigest(), 16) % max(n, 1)

def stylize(category: str, title: str) -> tuple[str, str, str]:
    for cre, tag, line_t, digest_t in KEYWORD_RULES:
        if cre.search(title):
            return tag, line_t.format(title=title), digest_t.format(title=title)
    options = TEMPLATES.get(category) or TEMPLATES["News"]
    tag, line_t, digest_t = options[hash_idx(title, len(options))]
    return tag, line_t.format(title=title), digest_t.format(title=title)

def load_watchlist() -> list[str]:
    if not WATCHLIST_PATH.exists():
        return []
    try:
        data = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
        series = data.get("series") or []
        return [s.strip() for s in series if isinstance(s, str) and s.strip()]
    except json.JSONDecodeError:
        return []

def match_watchlist(title: str, series: list[str]) -> str | None:
    low = title.lower()
    for name in series:
        if name.lower() in low:
            return name
    return None

def watchlist_style(title: str, series: str) -> tuple[str, str, str]:
    low = title.lower()
    if re.search(r"\b(chapter|volume|issue)\b", low):
        line = f"{series}: {title}"
        return "ADDED", line, line
    if re.search(r"\b(announce|announced|greenlit|adaptation)\b", low) and "anime" in low:
        line = f"Upcoming anime: {title}"
        return "DLC", line, line
    if re.search(r"\b(delay|hiatus|cancelled|canceled)\b", low):
        return "KNOWN ISSUE", title, title
    line = f"Watchlist: {title}"
    return "WATCHLIST", line, line

def recategorize(category: str, title: str) -> str:
    if category != "Health & Recalls" and (ANIME_WORDS.search(title) or match_watchlist(title, load_watchlist())):
        return "Anime & Manga"
    if category in {"Culture", "News", "Movies & TV"} and GAMING_WORDS.search(title):
        return "Gaming"
    if category in {"Culture", "News"} and MOVIE_WORDS.search(title):
        return "Movies & TV"
    if category in {"Culture", "News"} and MUSIC_WORDS.search(title):
        return "Music"
    if category == "News" and SCIENCE_WORDS.search(title):
        return "Science & Nature"
    return category

def make_note(title: str, url: str, source: str, category: str, kind: str = "headline", extra: dict | None = None) -> dict:
    series = match_watchlist(title, load_watchlist())
    if series:
        category = "Anime & Manga"
        tag, line, digest = watchlist_style(title, series)
    else:
        tag, line, digest = stylize(category, title)
    note = {
        "id": hashlib.sha1(f"{kind}:{norm_key(title)}".encode()).hexdigest()[:12],
        "category": category, "tag": tag, "line": line, "digest": digest,
        "title": title, "url": url, "source": source, "kind": kind,
    }
    if series:
        note["watchlist"] = series
    if extra:
        note.update(extra)
    return note

def collect_headlines() -> tuple[list[dict], list[str]]:
    used: set[str] = set()
    notes: list[dict] = []
    sources_ok: list[str] = []
    title_re_cache: dict[str, re.Pattern] = {}
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
        pat = None
        if feed.get("title_re"):
            pat = title_re_cache.setdefault(feed["id"], re.compile(feed["title_re"], re.I))
        kept = 0
        for entry in entries:
            if not entry["title"] or not entry["link"]:
                continue
            if pat and not pat.search(entry["title"]):
                continue
            key = norm_key(entry["title"])
            if not key or key in used:
                continue
            category = recategorize(feed["category"], entry["title"])
            note = make_note(
                entry["title"], entry["link"],
                entry["source"] or feed["id"].replace("_", " "),
                category, extra={"weird": bool(feed.get("weird"))},
            )
            notes.append(note)
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
        title = traffic = news_url = news_source = ""
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
        out.append({
            "title": title, "traffic": traffic,
            "url": f"https://trends.google.com/trends/explore?geo=US&q={query}",
            "news_url": news_url, "news_source": news_source,
        })
    return out

def collect_trends() -> tuple[list[dict], list[dict], bool]:
    log("Fetching Google Trends US…")
    raw = fetch(TRENDS_URL)
    if not raw:
        return [], [], False
    trends = parse_trends(raw)[:12]
    notes = []
    for t in trends:
        source = "Google Trends (US)"
        if t.get("traffic"):
            source = f"Google Trends (US) · {t['traffic']} searches"
        note = make_note(t["title"], t["url"], source, "Slang", kind="trend")
        if t.get("news_url"):
            note["related"] = t["news_url"]
            note["related_source"] = t.get("news_source") or ""
        notes.append(note)
    log(f"  trends: {len(trends)}")
    return notes, trends, True

def _parse_num(value) -> float | None:
    if value is None:
        return None
    s = str(value).replace(",", "").replace("$", "").replace("+", "").replace("%", "").strip()
    if not s or s in {"--", "N/A", "n/a"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None

def sanitize_move(symbol: str, price: float | None, prev: float | None, reported_pct: float | None) -> tuple[float, float | None, float] | None:
    if price is None or price <= 0:
        return None
    if prev is not None and prev > 0:
        calc = (price - prev) / prev * 100
        if reported_pct is not None and abs(calc - reported_pct) > 2.5:
            log(f"  {symbol}: reported {reported_pct:.2f}% vs calc {calc:.2f}%; using last vs previous close")
        pct = calc
        if abs(pct) > 90:
            log(f"  skip {symbol}: implausible daily move {pct:.1f}%")
            return None
        return price, prev, pct
    if reported_pct is None or abs(reported_pct) > 25:
        log(f"  skip {symbol}: unverified move {reported_pct}")
        return None
    return price, None, reported_pct

def _stock_note(q: dict, force: str | None = None) -> dict | None:
    symbol = q.get("symbol")
    price = q.get("regularMarketPrice")
    prev = q.get("regularMarketPreviousClose")
    reported = q.get("regularMarketChangePercent")
    if isinstance(price, str):
        price = _parse_num(price)
    if isinstance(prev, str):
        prev = _parse_num(prev)
    if isinstance(reported, str):
        reported = _parse_num(reported)
    if price is not None:
        price = float(price)
    if prev is not None:
        prev = float(prev)
    if reported is not None:
        reported = float(reported)
    sane = sanitize_move(str(symbol or "?"), price, prev, reported)
    if not sane:
        return None
    price, prev, pct = sane
    name = q.get("shortName") or q.get("displayName") or q.get("longName") or symbol
    direction = force or ("BUFFED" if pct >= 0 else "NERFED")
    verb = "buffed" if direction == "BUFFED" else "nerfed"
    sign = "+" if pct >= 0 else ""
    path = f"${prev:,.2f} → ${price:,.2f}" if prev else f"last ${price:,.2f}"
    line = f"{name} ({symbol}) {sign}{pct:.2f}%  ·  {path}"
    digest = line
    return {
        "id": hashlib.sha1(f"stock:{symbol}".encode()).hexdigest()[:12],
        "category": "Markets", "tag": direction, "line": line, "digest": digest,
        "title": f"{name} ({symbol}) {sign}{pct:.2f}%",
        "url": q.get("_url") or f"https://finance.yahoo.com/quote/{urllib.parse.quote(str(symbol))}",
        "source": q.get("_source") or "Yahoo Finance",
        "kind": "stock", "symbol": symbol, "price": price,
        "previous_close": prev, "change_pct": pct,
    }

def _quotes_from_screener(payload: dict) -> list[dict]:
    try:
        return payload["finance"]["result"][0].get("quotes") or []
    except (KeyError, IndexError, TypeError):
        return []

def _normalize_percents(quotes: list[dict]) -> list[dict]:
    pcts = []
    for q in quotes:
        p = q.get("regularMarketChangePercent")
        if p is not None:
            try:
                pcts.append(abs(float(p)))
            except (TypeError, ValueError):
                pass
    if pcts and max(pcts) <= 1.5:
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
        return {
            "symbol": meta.get("symbol") or symbol,
            "shortName": meta.get("shortName") or symbol,
            "regularMarketPrice": float(price),
            "regularMarketPreviousClose": float(prev),
            "regularMarketChangePercent": (float(price) - float(prev)) / float(prev) * 100,
        }
    except Exception:  # noqa: BLE001
        return None

def collect_cnbc() -> list[dict]:
    symbols = [
        "SPY", "QQQ", "DIA", "IWM", ".SPX", ".DJI", ".IXIC",
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO",
        "JPM", "V", "UNH", "XOM", "JNJ", "WMT", "PG", "MA", "HD", "COST",
        "NFLX", "AMD", "ORCL", "KO", "BAC", "DIS", "ADBE", "CSCO", "INTC",
        "CRM", "PEP", "ABBV", "LLY", "MRK", "TSM", "PLTR", "UBER", "COIN",
        "QCOM", "AMAT", "INTU", "IBM", "GE", "CAT", "BA", "GS",
    ]
    joined = "%7C".join(symbols)
    url = (
        "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
        f"?symbols={joined}&requestMethod=quick&exthrs=1&noform=1&partnerId=2"
        "&fundamentals=0&output=json"
    )
    raw = fetch(url)
    if not raw:
        return []
    try:
        payload = json.loads(raw)
        quotes = payload["FormattedQuoteResult"]["FormattedQuote"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []
    if isinstance(quotes, dict):
        quotes = [quotes]
    parsed = []
    for q in quotes:
        symbol = q.get("symbol")
        price = _parse_num(q.get("last"))
        prev = _parse_num(q.get("previous_day_closing"))
        pct = _parse_num(q.get("change_pct"))
        if not symbol or price is None:
            continue
        if q.get("changetype") == "DOWN" and pct is not None and pct > 0:
            pct = -pct
        elif str(q.get("change") or "").startswith("-") and pct is not None and pct > 0:
            pct = -pct
        parsed.append({
            "symbol": symbol,
            "shortName": q.get("name") or q.get("shortName") or symbol,
            "regularMarketPrice": price,
            "regularMarketPreviousClose": prev,
            "regularMarketChangePercent": pct,
            "_source": "CNBC",
            "_url": f"https://www.cnbc.com/quotes/{urllib.parse.quote(symbol)}",
        })
    scored = []
    for r in parsed:
        sane = sanitize_move(r["symbol"], r["regularMarketPrice"], r.get("regularMarketPreviousClose"), r.get("regularMarketChangePercent"))
        if not sane:
            continue
        r = dict(r)
        r["regularMarketPrice"], r["regularMarketPreviousClose"], r["regularMarketChangePercent"] = sane
        scored.append(r)
    scored.sort(key=lambda r: r["regularMarketChangePercent"], reverse=True)
    picked, seen = [], set()
    indexes = {".SPX", ".DJI", ".IXIC", "SPY", "QQQ", "DIA", "IWM"}
    for row in scored[:8] + list(reversed(scored[-8:])):
        if row["symbol"] in seen:
            continue
        seen.add(row["symbol"])
        picked.append(row)
    for row in scored:
        if row["symbol"] in indexes and row["symbol"] not in seen:
            picked.append(row)
            seen.add(row["symbol"])
    notes = []
    for row in picked:
        note = _stock_note(row)
        if note:
            notes.append(note)
    return notes

def collect_stocks() -> tuple[list[dict], str, bool]:
    log("Fetching stock movers…")
    cnbc_notes = collect_cnbc()
    if cnbc_notes:
        log(f"  cnbc majors: {len(cnbc_notes)}")
        return cnbc_notes, "majors", True

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

    notes: list[dict] = []
    gainers, losers = screener("day_gainers"), screener("day_losers")
    for q in gainers:
        n = _stock_note(q, "BUFFED")
        if n:
            notes.append(n)
    for q in losers:
        n = _stock_note(q, "NERFED")
        if n:
            notes.append(n)
    if notes:
        log(f"  movers: {len(notes)}")
        return notes, "movers", True
    log("  movers unavailable; falling back to major index ETFs")
    for sym, name in (("SPY", "S&P 500 ETF"), ("QQQ", "Nasdaq-100 ETF"), ("DIA", "Dow Jones ETF"), ("IWM", "Russell 2000 ETF"), ("^GSPC", "S&P 500"), ("^DJI", "Dow Jones"), ("^IXIC", "Nasdaq Composite")):
        time.sleep(0.7)
        q = _chart_quote(sym)
        if not q:
            continue
        q["shortName"] = name
        n = _stock_note(q)
        if n:
            notes.append(n)
    if notes:
        return notes, "indexes", True
    log("  no stock data")
    return [], "unavailable", False

def collect_nws() -> list[dict]:
    log("Fetching NWS alerts…")
    raw = fetch(
        "https://api.weather.gov/alerts/active?status=actual&severity=Severe,Extreme",
        headers={"User-Agent": NWS_UA, "Accept": "application/geo+json"},
    )
    if not raw:
        return []
    try:
        feats = json.loads(raw).get("features") or []
    except json.JSONDecodeError:
        return []
    notes, seen = [], set()
    for feat in feats:
        p = feat.get("properties") or {}
        event = (p.get("event") or "").strip()
        headline = (p.get("headline") or event).strip()
        if not headline:
            continue
        key = norm_key(event + " " + (p.get("areaDesc") or "")[:80])
        if key in seen:
            continue
        seen.add(key)
        sev = p.get("severity") or ""
        url = p.get("@id") or "https://www.weather.gov"
        source = p.get("senderName") or "National Weather Service"
        extra = {"weird": False, "severity": sev}
        note = make_note(headline, url, source, "Weather & Disasters", kind="alert", extra=extra)
        if sev == "Extreme" or re.search(r"Tornado|Hurricane|Tsunami", event, re.I):
            note["tag"] = "EVENT"
            note["line"] = f"World boss: {headline}"
            note["digest"] = f"Server event: {headline}"
        notes.append(note)
        if len(notes) >= 8:
            break
    log(f"  nws alerts kept {len(notes)} (from {len(feats)})")
    return notes

def _eia_row(page: str, label: str) -> tuple[float, float | None] | None:
    start = page.find(f'DataStub1">{label}</td>')
    if start < 0:
        return None
    cur = re.search(r'class="Current2">([0-9.]+)</td>', page[start:start + 1800])
    if not cur:
        return None
    row_html = page[start:start + cur.end()]
    prevs = re.findall(r'class="DataB">([0-9.]+)</td>', row_html)
    current = float(cur.group(1))
    prev = float(prevs[-1]) if prevs else None
    return current, prev

def collect_eia() -> tuple[list[dict], dict | None]:
    log("Fetching EIA gasoline prices…")
    url = "https://www.eia.gov/dnav/pet/pet_pri_gnd_dcus_nus_w.htm"
    raw = fetch(url)
    if not raw:
        return [], None
    page = raw.decode("utf-8", "replace")
    notes = []
    snapshot = {}
    for label, pretty in (("Regular", "U.S. regular gasoline"), ("Ultra Low Sulfur (15 ppm and Under)", "U.S. diesel (ultra-low sulfur)")):
        row = _eia_row(page, label)
        if not row:
            continue
        current, prev = row
        snapshot[label.lower()] = {"price": current, "prev": prev}
        if prev:
            chg = current - prev
            pct = chg / prev * 100
            path = f"${prev:.3f} → ${current:.3f}/gal"
            sign = "+" if chg >= 0 else ""
            if chg < 0:
                tag, verb = "BUFFED", "buffed"
            else:
                tag, verb = "NERFED", "nerfed"
            title = f"{pretty} averaged ${current:.3f}/gal this week ({sign}{chg:.3f}, {sign}{pct:.1f}%)"
            line = f"{title}  ·  {path}"
            digest = line
        else:
            tag = "UPDATED"
            title = f"{pretty} averaged ${current:.3f}/gal this week"
            line = f"Price check: {title}"
            digest = f"Patch: {title}"
        notes.append({
            "id": hashlib.sha1(f"eia:{label}".encode()).hexdigest()[:12],
            "category": "Gas & Grocery", "tag": tag, "line": line, "digest": digest,
            "title": title, "url": "https://www.eia.gov/petroleum/gasdiesel/",
            "source": "U.S. EIA", "kind": "eia",
        })
    log(f"  eia rows: {len(notes)}")
    return notes, snapshot or None

def collect_anilist() -> dict:
    log("Fetching AniList top and upcoming…")
    query = (
        "query { trending: Page(page: 1, perPage: 8) { media(type: ANIME, sort: TRENDING_DESC, status: RELEASING) "
        "{ title { romaji english } siteUrl averageScore season seasonYear format } } "
        "upcoming: Page(page: 1, perPage: 8) { media(type: ANIME, sort: POPULARITY_DESC, status: NOT_YET_RELEASED) "
        "{ title { romaji english } siteUrl season seasonYear format startDate { year month day } } } }"
    )
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://graphql.anilist.co", data=body,
        headers={"User-Agent": UA, "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20, context=CTX) as resp:
            payload = json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        log(f"  FAIL AniList ({type(exc).__name__}: {exc})")
        return {"trending": [], "upcoming": []}

    def pack(nodes):
        out = []
        for a in nodes or []:
            t = (a.get("title") or {})
            title = t.get("english") or t.get("romaji") or "Untitled"
            out.append({
                "title": title, "romaji": t.get("romaji") or "",
                "url": a.get("siteUrl") or "https://anilist.co",
                "score": a.get("averageScore"), "season": a.get("season"),
                "year": a.get("seasonYear"), "format": a.get("format"),
            })
        return out

    data = (payload.get("data") or {}) if isinstance(payload, dict) else {}
    result = {
        "trending": pack((data.get("trending") or {}).get("media")),
        "upcoming": pack((data.get("upcoming") or {}).get("media")),
    }
    log(f"  anilist trending={len(result['trending'])} upcoming={len(result['upcoming'])}")
    return result

def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    count = 0
    while True:
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
        d += timedelta(days=1)

def last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        d = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d

def holiday_calendar(today: date) -> list[dict]:
    years = {today.year, today.year + 1}
    events: list[tuple[date, str]] = []
    for y in years:
        events.extend([
            (date(y, 1, 1), "New Year's Day"),
            (nth_weekday(y, 1, 0, 3), "Martin Luther King Jr. Day"),
            (date(y, 2, 14), "Valentine's Day"),
            (nth_weekday(y, 2, 0, 3), "Presidents' Day"),
            (last_weekday(y, 5, 0), "Memorial Day"),
            (date(y, 6, 19), "Juneteenth"),
            (date(y, 7, 4), "Independence Day"),
            (nth_weekday(y, 9, 0, 1), "Labor Day"),
            (nth_weekday(y, 10, 0, 2), "Columbus Day / Indigenous Peoples' Day"),
            (date(y, 10, 31), "Halloween"),
            (date(y, 11, 11), "Veterans Day"),
            (nth_weekday(y, 11, 3, 4), "Thanksgiving"),
            (nth_weekday(y, 11, 3, 4) + timedelta(days=1), "Black Friday"),
            (nth_weekday(y, 11, 3, 4) + timedelta(days=4), "Cyber Monday"),
            (date(y, 12, 24), "Christmas Eve"),
            (date(y, 12, 25), "Christmas Day"),
            (date(y, 12, 31), "New Year's Eve"),
        ])
    start, end = today - timedelta(days=1), today + timedelta(days=16)
    notes = []
    for day, name in sorted(set(events)):
        if not (start <= day <= end):
            continue
        if day == today:
            when = "today"
        elif day == today + timedelta(days=1):
            when = "tomorrow"
        else:
            when = day.strftime("%A, %B %-d")
        title = f"{name} is {when}" if when in {"today", "tomorrow"} else f"{name} — {when}"
        notes.append({
            "id": hashlib.sha1(f"holiday:{day}:{name}".encode()).hexdigest()[:12],
            "category": "Holidays & Events", "tag": "ADDED",
            "line": title,
            "digest": title,
            "title": title, "url": "https://www.usa.gov/holidays",
            "source": "U.S. holiday calendar", "kind": "holiday",
        })
    return notes

WEIRD_RE = re.compile(r"species|discover|viral|bizarre|odd|weird|frog|snake|whale|fungus|genome|lizard|mealybug|bestiary", re.I)
SKIP_HIGHLIGHT_RE = re.compile(r"black friday deals?|% off|coupon|premarket|shopper|bundle deal", re.I)

def highlight_score(note: dict) -> int:
    if note.get("kind") in {"stock"}:
        return -50
    title = note.get("title") or ""
    cat = note.get("category") or ""
    score = 0
    if note.get("weird"):
        score += 8
    if note.get("watchlist"):
        score += 10
    if cat == "Science & Nature":
        score += 6
    if cat in {"Weather & Disasters", "Health & Recalls"} and note.get("kind") in {"alert", "headline"}:
        score += 3
    if cat in {"Gaming", "Anime & Manga", "Slang", "Holidays & Events"}:
        score += 2
    if WEIRD_RE.search(title):
        score += 5
    if SKIP_HIGHLIGHT_RE.search(title):
        score -= 12
    if note.get("kind") in {"holiday", "eia", "alert"}:
        score += 2
    if len(title) > 180:
        score -= 2
    return score

def pick_highlights(notes: list[dict], n: int = 10) -> list[dict]:
    ranked = sorted(notes, key=highlight_score, reverse=True)
    out, seen = [], set()
    for note in ranked:
        if highlight_score(note) <= 0 and len(out) >= 6:
            continue
        key = norm_key(note.get("title") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(note)
        if len(out) >= n:
            break
    return out

def load_week_notes(now: datetime, current: list[dict]) -> list[dict]:
    cutoff = now - timedelta(days=7)
    collected = list(current)
    if PATCHES.exists():
        for path in PATCHES.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            iso = (data.get("meta") or {}).get("iso") or ""
            try:
                when = datetime.fromisoformat(iso)
            except ValueError:
                continue
            if when.tzinfo is None:
                when = when.replace(tzinfo=TZ)
            if when < cutoff:
                continue
            collected.extend(data.get("notes") or [])
    return collected

def simple_md(text: str) -> str:
    text = text.replace("\r\n", "\n").strip()
    if not text:
        return ""
    chunks, buf, in_list = [], [], False

    def flush_p():
        nonlocal buf
        if buf:
            chunks.append("<p>" + " ".join(buf) + "</p>")
            buf = []

    def inline(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" rel="noopener noreferrer">\1</a>', s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
        return s

    for raw in text.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush_p()
            if in_list:
                chunks.append("</ul>")
                in_list = False
            continue
        if line.startswith("#"):
            flush_p()
            if in_list:
                chunks.append("</ul>")
                in_list = False
            hashes = len(line) - len(line.lstrip("#"))
            body = line[hashes:].strip()
            level = min(max(hashes, 1), 3) + 1
            chunks.append(f"<h{level}>{inline(body)}</h{level}>")
            continue
        if line.lstrip().startswith(("- ", "* ")):
            flush_p()
            if not in_list:
                chunks.append("<ul>")
                in_list = True
            chunks.append("<li>" + inline(line.lstrip()[2:].strip()) + "</li>")
            continue
        if in_list:
            chunks.append("</ul>")
            in_list = False
        buf.append(inline(line.strip()))
    flush_p()
    if in_list:
        chunks.append("</ul>")
    return "\n".join(chunks)

def parse_weekly_file(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    title = None
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm, body = parts[1], parts[2]
            m = re.search(r"^title:\s*(.+)$", fm, re.M)
            if m:
                title = m.group(1).strip().strip('"').strip("'")
    try:
        day = date.fromisoformat(path.stem)
    except ValueError:
        return None
    if not title:
        title = f"Weekly Patch Notes — {day.strftime('%B %-d, %Y')}"
    return {"date": day.isoformat(), "title": title, "html": simple_md(body), "id": path.stem}

def load_handwritten_weeklies() -> list[dict]:
    if not WEEKLY_DIR.exists():
        return []
    recaps = []
    for path in sorted(WEEKLY_DIR.glob("*.md"), reverse=True):
        parsed = parse_weekly_file(path)
        if parsed and parsed.get("html"):
            recaps.append(parsed)
    return recaps

def current_handwritten(recaps: list[dict], today: date) -> dict | None:
    target = last_sunday(today).isoformat()
    for r in recaps:
        if r["date"] == target:
            return r
    week_start = last_sunday(today)
    for r in recaps:
        d = date.fromisoformat(r["date"])
        if week_start <= d <= week_start + timedelta(days=6):
            return r
    return None


def broad_filter(category: str) -> str:
    for name, cats in FILTERS:
        if category in cats:
            return name
    return "Life"

def note_section(note: dict) -> str:
    if note.get("section") in SECTIONS:
        return note["section"]
    if note.get("kind") in {"stock", "eia"} or note.get("category") == "Markets":
        return "Markets"
    if note.get("kind") == "holiday" or note.get("category") == "Holidays & Events":
        return "Limited-Time Events"
    if note.get("kind") == "alert" or note.get("tag") == "EVENT" or note.get("category") == "Weather & Disasters":
        return "Limited-Time Events"
    if note.get("category") == "Health & Recalls" and note.get("tag") in {"RECALL", "KNOWN ISSUE"}:
        return "Known Bugs"
    return SECTION_FOR_TAG.get(note.get("tag") or "", "Hotfixes")

_REDUNDANT = re.compile(
    r"^(Buffs|Nerfs|Hotfix|New content|Known bug|Recall|Patch|Limited-time event|DLC|Upcoming DLC|Watchlist|Roster update|Balance change|Meta|Cost-of-living (?:buff|nerf)):\s*",
    re.I,
)

def annotate(note: dict) -> dict:
    note["filter"] = note.get("filter") or broad_filter(note.get("category") or "")
    note["section"] = note_section(note)
    text = (note.get("text") or note.get("digest") or note.get("line") or note.get("title") or "").strip()
    text = _REDUNDANT.sub("", text).strip()
    note["text"] = text
    return note

def load_written_patch(meta: dict) -> list[dict]:
    suffix = "am" if meta.get("kind") == "Morning" else "pm"
    day = f"{meta.get('year')}-{meta.get('month'):02d}-{meta.get('day'):02d}" if meta.get("year") else ""
    if not day and meta.get("id"):
        day = meta["id"][:10]
        suffix = "am" if "morning" in meta["id"] else "pm"
    path = PATCH_IN / f"{day}-{suffix}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log(f"  invalid written patch: {path}")
        return []
    items = data.get("items") or []
    notes = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        text = (raw.get("text") or "").strip()
        url = (raw.get("url") or "").strip()
        if not text or not url:
            continue
        tag = (raw.get("tag") or raw.get("filter") or "News & Politics").strip()
        section = raw.get("section") or "Hotfixes"
        if section not in SECTIONS:
            section = "Hotfixes"
        filt = tag if tag in {name for name, _ in FILTERS} else "Life"
        notes.append(annotate({
            "id": hashlib.sha1(f"written:{text}".encode()).hexdigest()[:12],
            "category": raw.get("category") or filt,
            "tag": "ADDED",
            "line": text,
            "digest": text,
            "text": text,
            "title": text,
            "url": url,
            "source": (raw.get("source") or "").strip() or "Source",
            "kind": "written",
            "section": section,
            "filter": filt,
            "featured": True,
        }))
    log(f"  written patch {path.name}: {len(notes)} items")
    return notes

def organize_sections(notes: list[dict]) -> list[tuple[str, list[dict]]]:
    buckets = {s: [] for s in SECTIONS}
    for n in notes:
        annotate(n)
        buckets.setdefault(n["section"], []).append(n)
    return [(s, buckets[s]) for s in SECTIONS if buckets[s]]

def load_archive() -> list[dict]:
    path = DATA / "archive.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []

def render_page(*, title: str, description: str, canonical: str, prefix: str, body: str, updated: str | None = None) -> str:
    esc = html.escape
    updated_meta = f'\n  <meta property="og:updated_time" content="{esc(updated)}">' if updated else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{esc(canonical)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Real Life v2026">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="theme-color" content="#eef4e6">{updated_meta}
  <link rel="icon" href="{esc(prefix)}assets/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{esc(prefix)}assets/style.css">
  <script>
    (function () {{
      try {{
        var t = localStorage.getItem("rlv2026:theme");
        if (!t && window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches) t = "night";
        if (t === "night") document.documentElement.setAttribute("data-theme", "night");
      }} catch (e) {{}}
    }})();
  </script>
  <script type="application/ld+json">
  {json.dumps({"@context": "https://schema.org", "@type": "WebSite", "name": "Real Life v2026", "url": SITE_URL + "/", "description": "Satirical patch notes for real life in the United States. Every item is based on a real, linked source.", "inLanguage": "en-US"})}
  </script>
</head>
<body>
  <a class="skip" href="#main">Skip to patch notes</a>
  <header class="top">
    <div class="scanlines" aria-hidden="true"></div>
    <div class="wrap top-row">
      <a class="brand" href="{esc(prefix)}index.html">
        <span class="logo" aria-hidden="true">RL</span>
        <span><strong>Real Life</strong><em>v2026</em></span>
      </a>
      <p class="satire-flag">Satire. Real news, written as patch notes. Every item links to its source — we don’t invent events.</p>
      <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Switch to night mode" title="Day / night">
        <span class="theme-day">Day</span><span class="theme-sep" aria-hidden="true">/</span><span class="theme-night">Night</span>
      </button>
    </div>
  </header>
  {body}
  <footer class="site-foot">
    <div class="wrap">
      <p><strong>Real Life v2026</strong> is a satirical changelog for life in the United States. The joke is the framing, not the facts. Health and recall items are worded carefully and always link to the official notice.</p>
      <p>Updated automatically at 8:00 AM and 6:00 PM Eastern (13:00 and 23:00 UTC). Crypto prices refresh in your browser from CoinGecko. This site is unofficial and not affiliated with the sources it links to.</p>
      <nav>
        <a href="{esc(prefix)}index.html">Latest patch</a>
        <a href="{esc(prefix)}archive/index.html">Archive</a>
        <a href="{esc(prefix)}weekly/index.html">Weekly recaps</a>
        <a href="https://github.com/theroundtable-byte/real-life-v2026">Source</a>
      </nav>
    </div>
  </footer>
  <script src="{esc(prefix)}assets/app.js" defer></script>
</body>
</html>
"""


def filters_html() -> str:
    chips = ['<button type="button" class="chip is-on" data-filter="all">All</button>']
    for name, _cats in FILTERS:
        chips.append(f'<button type="button" class="chip" data-filter="{html.escape(name)}">{html.escape(name)}</button>')
    return (
        '<div class="tools">'
        '<label class="search"><span class="sr">Search patch notes</span>'
        '<input id="q" type="search" placeholder="Search this patch…" autocomplete="off"></label>'
        f'<div class="chips" role="group" aria-label="Filter patch notes">{"".join(chips)}</div>'
        "</div>"
    )

def section_badge(name: str) -> str:
    tag, hook, icon = SECTION_UI.get(name, ("PATCH", "patch", "•"))
    return (
        f'<span class="sec-badge sec-{hook}" aria-hidden="true">'
        f'<span class="sec-ico">{icon}</span>[{html.escape(tag)}]</span>'
    )

def entry_item(item: dict, tier: str = "featured") -> str:
    text_raw = item.get("text") or item.get("digest") or item.get("line") or item.get("title") or ""
    text = html.escape(text_raw)
    url = item.get("url") or ""
    url_esc = html.escape(url, quote=True)
    source = html.escape(item.get("source") or "Source")
    filt = html.escape(item.get("filter") or broad_filter(item.get("category") or ""))
    section = item.get("section") or note_section(item)
    tag, hook, _icon = SECTION_UI.get(section, ("PATCH", "patch", "•"))
    nid = html.escape(str(item.get("id") or ""))
    data = html.escape(" ".join([
        text_raw, item.get("title") or "", item.get("source") or "",
        item.get("filter") or "", item.get("category") or "",
    ]).lower())
    tweet = urllib.parse.quote(f"{text_raw} — via Real Life v2026 {url}".strip())
    share_text = html.escape(text_raw, quote=True)
    return (
        f'<li class="entry" id="n-{nid}" data-id="{nid}" data-filter="{filt}" data-section="{html.escape(section)}" '
        f'data-tier="{html.escape(tier)}" data-text="{data}">'
        f'<span class="line-tag sec-{hook}" aria-hidden="true">[{html.escape(tag)}]</span> '
        f'<a href="{url_esc}" rel="noopener noreferrer">{text}</a>'
        f'<span class="meta"><span class="pill">{filt}</span> · {source}'
        f'<span class="share-group">'
        f'<button type="button" class="share" data-share-text="{share_text}" data-share-url="{url_esc}" aria-label="Copy this patch line">Share</button>'
        f'<a class="share-x" href="https://twitter.com/intent/tweet?text={tweet}" target="_blank" rel="noopener noreferrer" aria-label="Share this line on X">X</a>'
        f"</span></span>"
        f"</li>"
    )

def sections_html(groups: list[tuple[str, list[dict]]], tier: str = "featured") -> str:
    chunks = []
    for name, items in groups:
        if not items:
            continue
        hook = SECTION_UI.get(name, ("PATCH", "patch", "•"))[1]
        lis = "".join(entry_item(it, tier) for it in items)
        chunks.append(
            f'<section class="patch-section sec-{hook}" data-section="{html.escape(name)}">'
            f"<h2>{section_badge(name)} {html.escape(name)}</h2><ul class=\"log\">{lis}</ul></section>"
        )
    return "".join(chunks)

def ticker_html(stocks: list[dict], eia: dict | None) -> str:
    parts = []
    if eia and eia.get("regular"):
        r = eia["regular"]
        price = r["price"]
        prev = r.get("prev")
        cls = "up" if prev and price <= prev else "down" if prev and price > prev else ""
        delta = f" {price-prev:+.3f}" if prev else ""
        parts.append(f'<span class="coin {cls}"><b>Gas</b> ${price:.2f}/gal{delta}</span>')
    indexes = [s for s in stocks if s.get("symbol") in {".SPX", ".DJI", ".IXIC", "SPY", "QQQ", "DIA", "IWM"}]
    movers = [s for s in stocks if s.get("symbol") not in {".SPX", ".DJI", ".IXIC", "SPY", "QQQ", "DIA", "IWM"}]
    seen = set()
    for s in indexes[:4] + movers[:6]:
        sym = s.get("symbol")
        if not sym or sym in seen:
            continue
        seen.add(sym)
        pct = s.get("change_pct") or 0
        cls = "up" if pct >= 0 else "down"
        sign = "+" if pct >= 0 else ""
        parts.append(f'<span class="coin {cls}"><b>{html.escape(str(sym))}</b> {sign}{pct:.2f}%</span>')
    stock_bits = "".join(parts)
    return f"""
    <div class="ticker-wrap hud">
      <div class="wrap ticker">
        <span class="hud-corner" aria-hidden="true">⌜</span>
        <span class="ticker-label">Markets</span>
        {stock_bits or '<span class="ticker-status">Market quotes unavailable this run.</span>'}
        <span class="ticker-label">Crypto</span>
        <span id="crypto-ticker" class="crypto" data-endpoint="https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple,dogecoin,cardano&amp;vs_currencies=usd&amp;include_24hr_change=true">
          <span class="ticker-status">Loading prices…</span>
        </span>
        <span class="hud-corner" aria-hidden="true">⌝</span>
      </div>
    </div>
    """

def world_state_html(notes: list[dict], stocks: list[dict], eia: dict | None) -> str:
    ups = downs = 0
    for s in stocks:
        pct = s.get("change_pct")
        if pct is None:
            continue
        if pct >= 0:
            ups += 1
        else:
            downs += 1
    if ups > downs:
        mkt = f'<span class="ws-item"><b>Markets</b> <span class="up">▲ {ups} up</span> / {downs} down</span>'
    elif downs > ups:
        mkt = f'<span class="ws-item"><b>Markets</b> <span class="down">▼ {downs} down</span> / {ups} up</span>'
    elif ups or downs:
        mkt = f'<span class="ws-item"><b>Markets</b> mixed · {ups} up / {downs} down</span>'
    else:
        mkt = '<span class="ws-item"><b>Markets</b> quotes unavailable</span>'
    alerts = sum(1 for n in notes if n.get("kind") == "alert")
    if alerts:
        weather = f'<span class="ws-item"><b>Weather</b> {alerts} alert{"s" if alerts != 1 else ""}</span>'
    else:
        weather = '<span class="ws-item"><b>Weather</b> clear</span>'
    bugs = sum(1 for n in notes if n.get("section") == "Known Bugs" or n.get("tag") == "RECALL")
    bug_bit = f'<span class="ws-item"><b>Known bugs</b> {bugs}</span>'
    gas = ""
    if eia and eia.get("regular"):
        r = eia["regular"]
        price = r["price"]
        prev = r.get("prev")
        cls = "up" if prev and price <= prev else "down" if prev and price > prev else ""
        arrow = "▼" if cls == "up" else "▲" if cls == "down" else ""
        gas = f'<span class="ws-item"><b>Gas</b> <span class="{cls}">${price:.2f}/gal {arrow}</span></span>'
    return (
        '<aside class="world-state" aria-label="World state">'
        '<div class="wrap world-row">'
        '<span class="ws-live"><span class="status-dot" aria-hidden="true"></span> World state · Online</span>'
        f"{mkt}{weather}{bug_bit}{gas}"
        "</div></aside>"
    )

def anime_boards_html(anilist: dict, watch_notes: list[dict], series: list[str]) -> str:
    def col(heading: str, items: list[dict], score: bool) -> str:
        if not items:
            return f'<div class="board"><h3>{html.escape(heading)}</h3><p class="lede">Nothing listed this run.</p></div>'
        lis = []
        for a in items[:8]:
            title = html.escape(a["title"])
            url = html.escape(a["url"], quote=True)
            meta = []
            if score and a.get("score"):
                meta.append(str(a["score"]))
            if a.get("season") and a.get("year"):
                meta.append(f"{a['season'].title()} {a['year']}")
            extra = f' <small>{html.escape(" · ".join(meta))}</small>' if meta else ""
            lis.append(f'<li><a href="{url}" rel="noopener noreferrer">{title}</a>{extra}</li>')
        return f'<div class="board"><h3>{html.escape(heading)}</h3><ol>{"".join(lis)}</ol><p class="src">Source: <a href="https://anilist.co" rel="noopener noreferrer">AniList</a></p></div>'

    follows = ", ".join(html.escape(s) for s in series) or "none yet"
    if watch_notes:
        watch = f'<div class="watchlist"><h3>Watchlist</h3><p class="lede">Following: {follows}</p><ul class="log">{"".join(entry_item(n) for n in watch_notes)}</ul></div>'
    else:
        watch = f'<div class="watchlist"><h3>Watchlist</h3><p class="lede">Following: {follows}. No new pings in this patch.</p></div>'
    return '<div class="anime-extra">' + watch + '<div class="boards">' + col("Top airing", anilist.get("trending") or [], True) + col("New & upcoming", anilist.get("upcoming") or [], False) + "</div></div>"

def market_blurb(mode: str) -> str:
    if mode == "movers":
        return "Top US day gainers and losers via Yahoo Finance. Percents are checked against the previous close."
    if mode == "majors":
        return "Movers among major US stocks and indexes, via CNBC. Percents are checked against the previous close."
    if mode == "indexes":
        return "Major US indexes and ETFs are shown this run. A full movers list was not available."
    return "Stock quotes were unavailable this run. Crypto still updates live in the ticker."

def patch_post_html(meta, featured, rest, prefix="", extras="", blurb=""):
    feat_html = sections_html(organize_sections(featured), "featured")
    rest_html = sections_html(organize_sections(rest), "more") if rest else ""
    more_btn = ""
    more_wrap = ""
    if rest:
        more_btn = f'<button type="button" class="more" id="full-changelog" aria-expanded="false" aria-controls="full-log">Full changelog ({len(rest)} more)</button>'
        more_wrap = f'<div id="full-log" class="full-log" hidden><h2 class="full-h">Full changelog</h2>{rest_html}</div>'
    label = html.escape(meta["label"])
    return f"""
    <article class="patch-post" id="latest" data-patch-id="{html.escape(meta.get("id") or "")}">
      <header class="patch-head">
        <p class="kicker">Patch notes</p>
        <h1 class="ver" data-text="{label}">{label}</h1>
        <p class="when">Published {html.escape(meta["display_date"])}</p>
        <p class="intro">A satirical changelog for real life in the United States. Every line is based on a real, linked source. The joke is the framing, not the facts.</p>
        {f'<p class="lede market-note">{html.escape(blurb)}</p>' if blurb else ""}
      </header>
      {filters_html()}
      <div id="notes" class="patch-body">
        {feat_html}
      </div>
      {more_btn}
      {more_wrap}
      <p class="empty" id="empty" hidden>No notes match that filter. Try All or clear the search.</p>
      {extras}
    </article>
    """


def story_tokens(note: dict) -> set[str]:
    raw = f"{note.get('title') or ''} {note.get('text') or ''}"
    raw = _REDUNDANT.sub("", raw)
    return set(re.findall(r"[a-z0-9]{4,}", raw.lower()))

def is_near_dup(note: dict, pool: list[dict]) -> bool:
    a = story_tokens(note)
    if len(a) < 3:
        return False
    for other in pool:
        b = story_tokens(other)
        if not b:
            continue
        inter = len(a & b)
        if inter >= 3 or (inter and inter / min(len(a), len(b)) >= 0.5):
            return True
    return False

def split_featured(auto_notes: list[dict], written: list[dict]) -> tuple[list[dict], list[dict]]:
    auto = [annotate(n) for n in auto_notes]
    seen_urls: set[str] = set()
    featured: list[dict] = []
    for n in written:
        featured.append(annotate(n))
        if n.get("url"):
            seen_urls.add(n["url"])

    def acceptable(n: dict) -> bool:
        url = n.get("url") or ""
        if url and url in seen_urls:
            return False
        if any(n["id"] == f["id"] for f in featured):
            return False
        if is_near_dup(n, featured):
            return False
        return True

    def take(cands: list[dict], limit: int) -> None:
        for n in cands:
            if len(featured) >= limit:
                return
            if not acceptable(n):
                continue
            featured.append(n)
            if n.get("url"):
                seen_urls.add(n["url"])

    take(pick_highlights(auto, FEATURED_LIMIT + 12), FEATURED_LIMIT)

    if not any(f.get("section") == "Markets" for f in featured):
        stocks = sorted(
            [n for n in auto if n.get("kind") == "stock"],
            key=lambda n: abs(n.get("change_pct") or 0),
            reverse=True,
        )
        eia = [n for n in auto if n.get("kind") == "eia"]
        pick = next((n for n in stocks + eia if acceptable(n)), None)
        if pick:
            if len(featured) >= FEATURED_LIMIT:
                # Drop a padded auto line, never a written item or another Markets line.
                for i in range(len(featured) - 1, -1, -1):
                    if featured[i].get("kind") != "written" and featured[i].get("section") != "Markets":
                        dropped = featured.pop(i)
                        seen_urls.discard(dropped.get("url") or "")
                        break
            featured.append(pick)
            if pick.get("url"):
                seen_urls.add(pick["url"])

    featured_ids = {n["id"] for n in featured}
    featured_urls = {n.get("url") for n in featured}
    rest = [n for n in auto if n["id"] not in featured_ids and n.get("url") not in featured_urls]
    return featured, rest


def history_html(archive: list[dict], current_id: str, prefix: str) -> str:
    others = [p for p in archive if p.get("id") != current_id][:10]
    if not others:
        return ""
    items = []
    for p in others:
        payload = {}
        path = PATCHES / f"{p['id']}.json"
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {}
        notes = [annotate(n) for n in (payload.get("notes") or [])]
        written = payload.get("written") or []
        feat, rest = split_featured(notes, [annotate(n) for n in written] if written else [])
        if not feat and notes:
            feat, rest = notes[:FEATURED_LIMIT], notes[FEATURED_LIMIT:]
        body = sections_html(organize_sections(feat or notes[:FEATURED_LIMIT]), "featured")
        href = f"{html.escape(prefix)}archive/{html.escape(p['id'])}.html"
        items.append(
            f'<details class="history-item">'
            f'<summary><strong>{html.escape(p.get("label") or p["id"])}</strong>'
            f'<span>{html.escape(p.get("display_date") or "")} · {p.get("count", len(notes))} entries</span></summary>'
            f'<div class="history-body">{body}<p class="src"><a href="{href}">Open this patch</a></p></div>'
            f"</details>"
        )
    return f'<section class="history" id="history"><h2>Update history</h2>{"".join(items)}<p class="src"><a href="{html.escape(prefix)}archive/index.html">Browse the full archive</a></p></section>'

def extras_html(anilist, notes, series, trends, prefix=""):
    watch_notes = [n for n in notes if n.get("watchlist")]
    trend_block = ""
    if trends:
        pills = []
        for t in trends:
            q = urllib.parse.quote_plus(t["title"])
            href = html.escape(f"https://trends.google.com/trends/explore?geo=US&q={q}", quote=True)
            traffic = f' <small>{html.escape(t["traffic"])}</small>' if t.get("traffic") else ""
            pills.append(f'<a class="trend" href="{href}" rel="noopener noreferrer">{html.escape(t["title"])}{traffic}</a>')
        trend_block = f'<div class="trends"><h3>Trending in the US</h3><div class="trend-row">{"".join(pills)}</div></div>'
    inner = trend_block + anime_boards_html(anilist, watch_notes, series)
    return f'<details class="extras"><summary>Watchlist, top anime, and trends</summary>{inner}</details>'

def render_index(meta, notes, trends, stock_mode, archive, highlights, weekly_auto, handwritten, anilist, eia, series, written=None) -> str:
    written = written or []
    stocks = [n for n in notes if n.get("kind") == "stock"]
    featured, rest = split_featured(notes, written)
    extras = extras_html(anilist, notes, series, trends)
    weekly = ""
    if handwritten:
        weekly = (
            '<section class="weekly handwritten" id="weekly">'
            '<p class="kicker">Sunday recap</p>'
            f'<h2>{html.escape(handwritten["title"])}</h2>'
            f'<div class="prose">{handwritten["html"]}</div>'
            '<p class="src"><a href="weekly/index.html">Past weekly recaps</a></p>'
            "</section>"
        )
    elif weekly_auto:
        weekly = (
            '<section class="weekly" id="weekly">'
            '<p class="kicker">This week</p>'
            "<h2>Weekly Patch Notes</h2>"
            '<p class="lede">An automatic rollup of standout items from the last 7 days, until a hand-written Sunday recap is added.</p>'
            + sections_html(organize_sections([annotate(n) for n in weekly_auto]), "featured")
            + '<p class="src"><a href="weekly/index.html">Weekly recap archive</a></p></section>'
        )
    body = f"""
  {ticker_html(stocks, eia)}
  {world_state_html(notes, stocks, eia)}
  <main id="main">
    <div class="wrap">
      {weekly}
      {patch_post_html(meta, featured, rest, prefix="", extras=extras, blurb=market_blurb(stock_mode))}
      {history_html(archive, meta["id"], "")}
    </div>
  </main>
"""
    desc = f"Satirical US patch notes for {meta['label']}. Real headlines framed as a game update, with every line linked to its source."
    return render_page(title=f"Real Life {meta['label']} — Patch Notes for America", description=desc, canonical=f"{SITE_URL}/", prefix="", body=body, updated=meta["iso"])

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
  <main id="main"><div class="wrap">
    <section class="hero">
      <p class="kicker"><a href="../index.html">← Latest patch</a></p>
      <h1>Patch archive</h1>
      <p class="intro">The last {MAX_ARCHIVE} builds, newest first.</p>
    </section>
    {lis}
  </div></main>
"""
    return render_page(title="Archive — Real Life v2026", description="Browse past satirical US patch notes.", canonical=f"{SITE_URL}/archive/", prefix="../", body=body)

def render_archive_patch(meta, notes, anilist, series, stock_mode, written=None, trends=None, eia=None) -> str:
    written = written or []
    featured, rest = split_featured(notes, written)
    extras = extras_html(anilist, notes, series, trends or [])
    body = f"""
  <main id="main"><div class="wrap">
    <p class="crumb"><a href="../index.html">← Latest patch</a> · <a href="index.html">Archive</a></p>
    {patch_post_html(meta, featured, rest, prefix="../", extras=extras, blurb=market_blurb(stock_mode))}
  </div></main>
"""
    return render_page(title=f"Real Life {meta['label']} — Archive", description=f"Archived satirical US patch notes for {meta['label']}.", canonical=f"{SITE_URL}/archive/{meta['id']}.html", prefix="../", body=body, updated=meta.get("iso"))


def render_weekly_index(recaps: list[dict]) -> str:
    if not recaps:
        lis = "<p>No hand-written Sunday recaps yet. Until one is added, the homepage shows an automatic weekly rollup.</p>"
    else:
        items = [f'<li><a href="{html.escape(r["id"])}.html"><strong>{html.escape(r["title"])}</strong><span>{html.escape(r["date"])}</span></a></li>' for r in recaps]
        lis = f'<ol class="archive-list">{"".join(items)}</ol>'
    body = f"""
  <main id="main"><div class="wrap">
    <section class="hero">
      <p class="kicker"><a href="../index.html">← Latest patch</a></p>
      <h1>Weekly recaps</h1>
      <p class="intro">Hand-written Sunday patch notes, when they exist. The automatic weekly rollup lives on the homepage the rest of the time.</p>
    </section>
    {lis}
  </div></main>
"""
    return render_page(title="Weekly recaps — Real Life v2026", description="Hand-written weekly patch notes for Real Life v2026.", canonical=f"{SITE_URL}/weekly/", prefix="../", body=body)

def render_weekly_page(recap: dict) -> str:
    body = f"""
  <main id="main"><div class="wrap">
    <section class="hero">
      <p class="kicker"><a href="../index.html">Latest patch</a> · <a href="index.html">Weekly recaps</a></p>
      <h1>{html.escape(recap["title"])}</h1>
      <p class="when">{html.escape(recap["date"])}</p>
    </section>
    <section class="weekly handwritten"><div class="prose">{recap["html"]}</div></section>
  </div></main>
"""
    return render_page(title=f"{recap['title']} — Real Life v2026", description=f"Weekly patch notes recap for {recap['date']}.", canonical=f"{SITE_URL}/weekly/{recap['id']}.html", prefix="../", body=body)

def write_robots_and_sitemap(archive: list[dict], recaps: list[dict], now: datetime) -> None:
    (SITE / "robots.txt").write_text("User-agent: *\nAllow: /\n" f"Sitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    urls = [
        (f"{SITE_URL}/", now, "hourly"),
        (f"{SITE_URL}/archive/", now, "daily"),
        (f"{SITE_URL}/weekly/", now, "weekly"),
    ]
    for p in archive:
        urls.append((f"{SITE_URL}/archive/{p['id']}.html", p.get("iso") or now.isoformat(), "weekly"))
    for r in recaps:
        urls.append((f"{SITE_URL}/weekly/{r['id']}.html", r["date"], "monthly"))
    chunks = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, freq in urls:
        lm = lastmod if isinstance(lastmod, str) else lastmod.isoformat()
        chunks.append(f"  <url><loc>{html.escape(loc)}</loc><lastmod>{html.escape(str(lm)[:25])}</lastmod><changefreq>{freq}</changefreq></url>")
    chunks.append("</urlset>\n")
    (SITE / "sitemap.xml").write_text("\n".join(chunks), encoding="utf-8")

def write_site(meta, notes, trends, stock_mode, highlights, weekly_auto, handwritten, recaps, anilist, eia, series, written) -> None:
    for path in (SITE, DATA, PATCHES, ARCHIVE, WEEKLY_OUT, SITE / "assets"):
        path.mkdir(parents=True, exist_ok=True)
    notes = [annotate(n) for n in notes]
    written = [annotate(n) for n in written]
    archive = load_archive()
    summary = {"id": meta["id"], "label": meta["label"], "kind": meta["kind"], "iso": meta["iso"], "display_date": meta["display_date"], "count": len(notes), "stock_mode": stock_mode, "written": bool(written)}
    archive = [p for p in archive if p.get("id") != meta["id"]]
    archive.insert(0, summary)
    dropped = archive[MAX_ARCHIVE:]
    archive = archive[:MAX_ARCHIVE]
    for oldp in dropped:
        for path in (ARCHIVE / f"{oldp['id']}.html", PATCHES / f"{oldp['id']}.json"):
            if path.exists():
                path.unlink()
    payload = {
        "meta": meta,
        "stock_mode": stock_mode,
        "trends": trends,
        "notes": notes,
        "written": written,
        "highlights": [{"id": h["id"], "digest": h.get("digest") or h.get("text"), "title": h.get("title"), "text": h.get("text")} for h in highlights],
        "anilist": anilist,
        "eia": eia,
    }
    (DATA / "latest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (PATCHES / f"{meta['id']}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (DATA / "archive.json").write_text(json.dumps(archive, indent=2), encoding="utf-8")
    (SITE / "index.html").write_text(render_index(meta, notes, trends, stock_mode, archive, highlights, weekly_auto, handwritten, anilist, eia, series, written), encoding="utf-8")
    (ARCHIVE / "index.html").write_text(render_archive_index(archive), encoding="utf-8")
    (ARCHIVE / f"{meta['id']}.html").write_text(render_archive_patch(meta, notes, anilist, series, stock_mode, written, trends, eia), encoding="utf-8")
    (WEEKLY_OUT / "index.html").write_text(render_weekly_index(recaps), encoding="utf-8")
    for recap in recaps:
        (WEEKLY_OUT / f"{recap['id']}.html").write_text(render_weekly_page(recap), encoding="utf-8")
    write_robots_and_sitemap(archive, recaps, now_et())
    log(f"Wrote site for {meta['label']} ({len(notes)} notes, featured written={len(written)}, archive={len(archive)})")


def main() -> int:
    dt = now_et()
    meta = patch_meta(dt)
    log(f"Generating {meta['label']}")
    series = load_watchlist()
    headlines, ok_feeds = collect_headlines()
    trend_notes, trends, trends_ok = collect_trends()
    stock_notes, stock_mode, stocks_ok = collect_stocks()
    weather_notes = collect_nws()
    eia_notes, eia = collect_eia()
    holiday_notes = holiday_calendar(dt.date())
    anilist = collect_anilist()
    notes = headlines + trend_notes + stock_notes + weather_notes + eia_notes + holiday_notes
    if not notes:
        log("No content collected; aborting so we do not overwrite a good build.")
        return 1
    notes = [annotate(n) for n in notes]
    written = load_written_patch(meta)
    highlights = pick_highlights(notes, 10)
    recaps = load_handwritten_weeklies()
    handwritten = current_handwritten(recaps, dt.date())
    weekly_auto = []
    if not handwritten:
        week_pool = [annotate(n) for n in load_week_notes(dt, notes)]
        exclude = {h["id"] for h in highlights}
        weekly_auto = [n for n in pick_highlights(week_pool, 16) if n["id"] not in exclude][:10]
        if not weekly_auto:
            weekly_auto = pick_highlights(week_pool, 8)
    write_site(meta, notes, trends, stock_mode, highlights, weekly_auto, handwritten, recaps, anilist, eia, series, written)
    extras = (["trends"] if trends_ok else []) + (["stocks"] if stocks_ok else [])
    if weather_notes:
        extras.append("nws")
    if eia_notes:
        extras.append("eia")
    if anilist.get("trending") or anilist.get("upcoming"):
        extras.append("anilist")
    if written:
        extras.append(f"written:{len(written)}")
    log("Sources OK: " + ", ".join(ok_feeds + extras))
    log(f"Stock mode: {stock_mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
