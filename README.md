# Real Life v2026

A satirical, self-updating changelog for real life in the United States. Real headlines, Google Trends, stock movers, and live crypto prices, written like video-game patch notes.

**Live site:** https://theroundtable-byte.github.io/real-life-v2026/

This is satire. Every item is based on a real, linked source. The joke is the framing, not the facts. Events are never invented.

## Schedule

A GitHub Actions workflow runs at **8:00 AM and 6:00 PM US Eastern** (13:00 and 23:00 UTC), plus manual runs from the Actions tab. During daylight time those UTC clocks fall at 9:00 AM and 7:00 PM Eastern.

Each build is versioned like `v2026.11 · Week 4 · Nov 23 (Evening patch)`. The last 60 patches stay in the archive.

Crypto prices (BTC, ETH, SOL, XRP, DOGE, ADA) refresh in the visitor’s browser about every minute from [CoinGecko](https://www.coingecko.com/)’s free public API. They do not require a rebuild.

## Sources

- US headlines: Google News RSS (top stories, nation, technology, entertainment, science, politics, business) and NPR RSS (news, culture, music, science)
- Trending searches: [Google Trends RSS for the US](https://trends.google.com/trending/rss?geo=US)
- Stock movers: Yahoo Finance day gainers / losers (falls back to major US index ETFs if the screener is unavailable)
- Crypto: CoinGecko, client-side

No API keys. Hosting is GitHub Pages (free).

## Run locally

```bash
python3 generate.py
```

Then open `site/index.html`. The script uses only the Python standard library.
