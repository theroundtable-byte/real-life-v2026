# Real Life v2026

A satirical, self-updating daily recap for real life in the United States. Real headlines, trends, markets, and official notices, written like a daily update — clear first, with a light wink at patch notes.

**Live site:** https://theroundtable-byte.github.io/real-life-v2026/

This is satire. Every item is based on a real, linked source. The joke is the framing, not the facts. Events are never invented.

## Schedule

A GitHub Actions workflow runs at **8:00 AM and 6:00 PM US Eastern** (13:00 and 23:00 UTC), plus manual runs from the Actions tab. During daylight time those UTC clocks fall at 9:00 AM and 7:00 PM Eastern.

Each build is versioned like `v2026.11 · Week 4 · Nov 23 · Evening Patch`. The homepage shows one daily update (Leveling Up, Took a Hit, Fixed, What's New, Still Broken, Happening Now, and Markets), with older updates listed below as history. The last 60 updates stay in the archive. Older stored files that still use the original game-section names (`Buffs`, `Nerfs`, and so on) are mapped to the new labels when the site is built.

Crypto prices (BTC, ETH, SOL, XRP, DOGE, ADA) refresh in the visitor’s browser about every minute from [CoinGecko](https://www.coingecko.com/). They do not require a rebuild.


## Featured items (hand-written)

Auto-collected headlines stay factual, but they cannot really rewrite a news story as a punchy spoken line. To feature that voice, add a JSON file at:

`content/patches/YYYY-MM-DD-am.json` or `content/patches/YYYY-MM-DD-pm.json`

Use `am` for the morning edition and `pm` for the evening edition, with the date in America/New_York. If that file is present when the site is generated, its items become the **featured** set for that update. The automatic feed still fills **The rest of today's update**. If the file has fewer than about 18 items, standout auto lines are added so the featured list stays a short, readable set. Duplicate URLs are skipped.

```json
{
  "items": [
    {
      "section": "Leveling Up",
      "tag": "News & Politics",
      "text": "Leveling Up: NYC lawmaker unlocks the Lizard Eye-Roll skill after a viral video.",
      "url": "https://www.example.com/article",
      "source": "The Daily Beast"
    }
  ]
}
```

Fields:

- `section` (required): one of `Leveling Up`, `Took a Hit`, `Fixed`, `What's New`, `Still Broken`, `Happening Now`, `Markets`. The older names (`Buffs`, `Nerfs`, `Hotfixes`, `New Content`, `Known Bugs`, `Limited-Time Events`) are still accepted and displayed under the new labels.
- `tag` (required): the broad filter pill shown on the line: `News & Politics`, `Tech & Science`, `Entertainment`, `Sports`, `Life`, or `Markets`.
- `text` (required): the line as it should appear, joke first, fact intact. Do not invent events.
- `url` (required): a real source link for that line.
- `source` (optional): the publication or agency name.
- `category` (optional): unused for display; the `tag` is what readers filter on.

Filters on the site are: All, plus those six tags. Life covers weather, holidays, health/recalls, gas and grocery, slang, and culture.

## Weekly recap (hand-written)

A Sunday recap can be added by dropping a Markdown file into `content/weekly/YYYY-MM-DD.md`, where the date is the **Sunday** of that recap. Then commit and push (or run the workflow).

Optional front matter:

```markdown
---
title: This week — Week of Nov 16, 2026
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

## Thumbnails

The first item in each category gets a thumbnail when a source image is available. The builder first checks the feed (`media:thumbnail`, `media:content`, or an image enclosure), then fetches the article page for `og:image` or `twitter:image`. Images are resized locally to WebP under `site/assets/thumbs/` and the thumbnail links back to the source article. If no usable image is found, the category icon is shown instead.

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

Then open `site/index.html`. The script uses the Python standard library, plus Pillow to resize source thumbnails at build time (also installed in the GitHub Actions workflow).
