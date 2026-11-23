# Real Life v2026

A satirical, self-updating changelog for real life in the United States. Real headlines, trends, markets, and official notices, written like video-game patch notes.

**Live site:** https://theroundtable-byte.github.io/real-life-v2026/

This is satire. Every item is based on a real, linked source. The joke is the framing, not the facts. Events are never invented.

## Schedule

A GitHub Actions workflow runs at **8:00 AM and 6:00 PM US Eastern** (13:00 and 23:00 UTC), plus manual runs from the Actions tab. During daylight time those UTC clocks fall at 9:00 AM and 7:00 PM Eastern.

Each build is versioned like `v2026.11 · Week 4 · Nov 23 (Evening patch)`. The last 60 patches stay in the archive.

Crypto prices (BTC, ETH, SOL, XRP, DOGE, ADA) refresh in the visitor’s browser about every minute from [CoinGecko](https://www.coingecko.com/). They do not require a rebuild.

## Weekly Patch Notes (hand-written)

A Sunday recap can be added by dropping a Markdown file into `content/weekly/YYYY-MM-DD.md`, where the date is the **Sunday** of that recap. Then commit and push (or run the workflow).

Optional front matter:

```markdown
---
title: Weekly Patch Notes — Week of Nov 16, 2026
---

A short recap in simple Markdown: paragraphs, lists, links, **bold**, and headings.

- Keep facts tied to real stories; this is still satire in framing only.
```

The generator uses the most recent Sunday file for the homepage. Older files appear in the [weekly archive](https://theroundtable-byte.github.io/real-life-v2026/weekly/). If no file exists for the current week, the homepage shows an automatic rollup of the week’s best items instead.

## Anime watchlist

Edit `content/watchlist.json` to follow series. Matches in incoming headlines show up in the Anime & Manga watchlist.

```json
{
  "series": ["Kagurabachi", "Gachiakuta", "Fool Night", "Bass Machina"]
}
```

## Sources

- US headlines: Google News RSS and NPR RSS
- Offbeat / science: Google News searches for new species and discoveries
- Gaming: IGN, Polygon, Kotaku, GameSpot, plus a Google News gaming search
- Movies & TV: Variety, The Hollywood Reporter, Deadline, Google News
- Anime & Manga: Anime News Network, Crunchyroll News, MyAnimeList, Google News; top/upcoming lists from AniList
- Sports: Google News Sports and ESPN RSS
- Weather: National Weather Service alerts, plus Google News weather/disaster coverage
- Health & recalls: FDA food-safety recall RSS, and matching CDC “what’s new” items (USDA FSIS RSS was blocked)
- Gas & grocery: official U.S. EIA weekly retail gasoline/diesel prices, plus Google News price stories
- Holidays: a small U.S. holiday calendar combined with seasonal travel/event news
- Trending searches: [Google Trends RSS for the US](https://trends.google.com/trending/rss?geo=US)
- Stock movers: CNBC public quotes for major US stocks and indexes (Yahoo Finance day gainers / losers, then index ETFs, as fallbacks)
- Crypto: CoinGecko, client-side

No API keys. Hosting is GitHub Pages (free).

## Run locally

```bash
python3 generate.py
```

Then open `site/index.html`. The script uses only the Python standard library.
