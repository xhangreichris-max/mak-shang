#!/usr/bin/env python3
"""
Tool: fetch_trends

Fetches paint and interior-design trend candidates from Brave Search and RSS feeds.
Deduplicates against recently covered topics in trend-topic-log.json.

Primary function:
    fetch_trends() -> list[dict]

    Returns a list of fresh candidate dicts:
        {"title": str, "url": str, "snippet": str, "source": str, "published_date": str}

    Writes the result to trend_candidates.json in the pipeline directory.
    Reads BRAVE_SEARCH_API_KEY from .env; falls back to RSS-only if the key is absent.

    Raises RuntimeError (with ABORT: prefix) if fewer than MINIMUM_CANDIDATES are found.
    Also writes fetch_trends_failed.json as a failure marker in that case.
    Clears fetch_trends_failed.json on a successful run.
"""

import json, ssl, time, datetime, os, sys
import urllib.request, urllib.parse
import xml.etree.ElementTree as ET

PIPELINE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Minimum fresh candidates required before the pipeline may proceed.
# Must be >= 3 to fill 3 post slots with distinct topics.
MINIMUM_CANDIDATES = 3

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SEARCH_QUERIES = [
    "interior paint trends 2026 India",
    "home wall paint color trends 2026",
    "paint finish types guide homeowners India",
    "textured wall paint ideas 2026",
    "best interior paint colors 2026 Asia",
    "paint maintenance tips tropical climate India",
    "Manipur northeast India interior design homes",
    "earthy tone paint colors 2026",
    "Asian Paints Royale new shades 2026",
    "monsoon proof wall paint tips India",
    "wall paint colors trending Indian homes 2026",
    "Berger paints interior colour guide 2026",
]

RSS_FEEDS = [
    # International — high reliability
    {"url": "https://www.architecturaldigest.com/feed/rss",    "source": "Architectural Digest"},
    {"url": "https://www.dezeen.com/feed/",                    "source": "Dezeen"},
    {"url": "https://designmilk.com/feed/",                    "source": "Design Milk"},
    {"url": "https://www.yankodesign.com/feed/",               "source": "Yanko Design"},
    {"url": "https://www.interiordesign.net/feed/",            "source": "Interior Design"},
    # India-specific
    {"url": "https://www.architecturaldigest.in/feed/rss",     "source": "AD India"},
    {"url": "https://www.livspace.com/in/magazine/feed/",      "source": "Livspace India"},
    {"url": "https://www.designcafe.com/blog/feed/",           "source": "Design Cafe"},
    # Original feeds — kept in rotation; may return 404 intermittently
    {"url": "https://www.elledecor.com/feed/rss",              "source": "Elle Decor"},
    {"url": "https://www.housebeautiful.com/feed/rss",         "source": "House Beautiful"},
    {"url": "https://www.livingetc.com/feeds/all.atom",        "source": "Living Etc"},
]

RSS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/atom+xml, text/xml, */*",
}

PAINT_KEYWORDS = [
    "paint", "color", "colour", "interior", "wall", "finish", "decor",
    "home design", "renovation", "texture", "coating", "shade", "hue",
    "palette", "room", "living room", "bedroom", "kitchen",
]


def _load_env():
    env = dict(os.environ)
    env_path = os.path.join(PIPELINE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _load_topic_log():
    path = os.path.join(PIPELINE_DIR, "trend-topic-log.json")
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _is_recently_covered(title, log, window_days=14):
    cutoff = datetime.date.today() - datetime.timedelta(days=window_days)
    title_lower = title.lower()
    for entry in log:
        try:
            entry_date = datetime.date.fromisoformat(entry.get("date", "2000-01-01"))
        except ValueError:
            continue
        if entry_date >= cutoff:
            covered_words = set(entry.get("topic", "").lower().split())
            title_words = set(title_lower.split())
            meaningful = {w for w in covered_words & title_words if len(w) > 4}
            if len(meaningful) >= 3:
                return True
    return False


def _is_relevant(candidate):
    text = (candidate.get("title", "") + " " + candidate.get("snippet", "")).lower()
    return any(kw in text for kw in PAINT_KEYWORDS)


def _brave_search(query, api_key, count=5):
    url = "https://api.search.brave.com/res/v1/web/search"
    params = urllib.parse.urlencode({"q": query, "count": count, "freshness": "pm"})
    req = urllib.request.Request(
        f"{url}?{params}",
        headers={"Accept": "application/json", "X-Subscription-Token": api_key},
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("description", ""),
                "source": item.get("profile", {}).get("name", "Web"),
                "published_date": item.get("age", ""),
            })
        return results
    except Exception as e:
        print(f"  Brave search error for '{query}': {e}")
        return []


def _fetch_rss(feed_url, source_name):
    req = urllib.request.Request(feed_url, headers=RSS_HEADERS)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            raw = r.read()
        # Strip BOM and leading whitespace that breaks ET.fromstring on some feeds (e.g. Dezeen)
        content = raw.decode("utf-8", errors="replace").lstrip("﻿ \t\r\n")
        # If the feed starts with a byte-order marker in the raw bytes, re-strip
        if content and content[0] != "<":
            idx = content.find("<")
            content = content[idx:] if idx != -1 else content
        root = ET.fromstring(content)
        items = []
        # RSS 2.0
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            pub = item.findtext("pubDate", "").strip()
            if title and link:
                items.append({
                    "title": title, "url": link,
                    "snippet": desc[:200] if desc else "",
                    "source": source_name, "published_date": pub,
                })
        # Atom
        atom_ns = "http://www.w3.org/2005/Atom"
        for entry in root.findall(f"{{{atom_ns}}}entry"):
            title_el = entry.find(f"{{{atom_ns}}}title")
            link_el = entry.find(f"{{{atom_ns}}}link")
            summary_el = entry.find(f"{{{atom_ns}}}summary")
            updated_el = entry.find(f"{{{atom_ns}}}updated")
            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            link = link_el.get("href", "") if link_el is not None else ""
            summary = summary_el.text.strip() if summary_el is not None and summary_el.text else ""
            updated = updated_el.text.strip() if updated_el is not None and updated_el.text else ""
            if title and link:
                items.append({
                    "title": title, "url": link,
                    "snippet": summary[:200],
                    "source": source_name, "published_date": updated,
                })
        return items[:10]
    except Exception as e:
        print(f"  RSS fetch error ({source_name}): {e}")
        return []


def _write_failure_marker(candidates_found, message):
    path = os.path.join(PIPELINE_DIR, "fetch_trends_failed.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.date.today().isoformat(),
            "candidates_found": candidates_found,
            "message": message,
        }, f, indent=2)


def _clear_failure_marker():
    path = os.path.join(PIPELINE_DIR, "fetch_trends_failed.json")
    if os.path.exists(path):
        os.remove(path)


def fetch_trends():
    """
    Fetch fresh trend candidates from Brave Search + RSS feeds.

    Returns list of candidate dicts filtered for paint relevance and topic recency.
    Also writes the result to trend_candidates.json in the pipeline directory.

    Raises RuntimeError with an ABORT: prefix if fewer than MINIMUM_CANDIDATES
    fresh candidates are found. The caller must treat this as a hard stop —
    do NOT proceed with content generation when this exception is raised.
    """
    env = _load_env()
    topic_log = _load_topic_log()
    brave_key = env.get("BRAVE_SEARCH_API_KEY", "")
    all_candidates = []
    seen_urls = set()

    if brave_key:
        print(f"Running {len(SEARCH_QUERIES)} Brave Search queries...")
        for query in SEARCH_QUERIES:
            print(f"  Searching: {query}")
            results = _brave_search(query, brave_key, count=5)
            for r in results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_candidates.append(r)
            time.sleep(0.5)
    else:
        print("WARNING: BRAVE_SEARCH_API_KEY not set — RSS-only mode. "
              "Candidate pool may be smaller. Set the key in .env for reliable results.")

    print(f"\nFetching {len(RSS_FEEDS)} RSS feeds...")
    rss_ok = 0
    for feed in RSS_FEEDS:
        print(f"  Fetching: {feed['source']}")
        items = _fetch_rss(feed["url"], feed["source"])
        if items:
            rss_ok += 1
        for item in items:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_candidates.append(item)
        time.sleep(0.3)
    print(f"  RSS: {rss_ok}/{len(RSS_FEEDS)} feeds returned results")

    relevant = [c for c in all_candidates if _is_relevant(c)]
    fresh = [c for c in relevant if not _is_recently_covered(c["title"], topic_log)]

    print(f"\nTotal fetched: {len(all_candidates)}")
    print(f"After relevance filter: {len(relevant)}")
    print(f"After dedup against topic log: {len(fresh)}")

    out_path = os.path.join(PIPELINE_DIR, "trend_candidates.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fresh, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(fresh)} candidates to trend_candidates.json")

    if len(fresh) < MINIMUM_CANDIDATES:
        msg = (
            f"ABORT: fetch_trends found only {len(fresh)} fresh candidate(s) "
            f"(minimum required: {MINIMUM_CANDIDATES}). "
            f"RSS feeds live: {rss_ok}/{len(RSS_FEEDS)}. "
            f"Do NOT proceed with content generation or publishing."
        )
        print(msg)
        _write_failure_marker(len(fresh), msg)
        raise RuntimeError(msg)

    _clear_failure_marker()
    return fresh


if __name__ == "__main__":
    try:
        fetch_trends()
    except RuntimeError:
        sys.exit(1)
