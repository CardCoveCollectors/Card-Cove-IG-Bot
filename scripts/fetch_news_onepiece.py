"""
Pulls One Piece Card Game news headlines from the free Google News RSS
search feed configured in config_news_onepiece.py, filters for newsworthy
keywords, and returns fresh candidates newest-first.

No API key, no LLM call — pure RSS + keyword matching, so this costs
nothing to run.

Dedup against what's already been posted happens in main_news_onepiece.py
(it owns state_news_onepiece.json), not here — this module only knows
about "is this fresh and relevant," not "have we posted it before."
"""
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import requests

from config_news_onepiece import NEWS_FEEDS, MAX_AGE_HOURS, KEYWORDS, BLOCKLIST

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CardCoveNewsBot/1.0)"}


def _fetch_feed(url):
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return ElementTree.fromstring(resp.content)


def _parse_items(root, topic):
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = item.findtext("pubDate")
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else ""
        guid = (item.findtext("guid") or link).strip()

        pub_date = None
        if pub_date_raw:
            try:
                pub_date = parsedate_to_datetime(pub_date_raw)
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
            except Exception:
                pub_date = None

        if not title:
            continue

        items.append({
            "topic": topic,
            "title": title,
            "link": link,
            "guid": guid,
            "source": source,
            "pub_date": pub_date,
        })
    return items


def _is_recent(item, max_age_hours):
    if item["pub_date"] is None:
        return True
    age = datetime.now(timezone.utc) - item["pub_date"]
    return age.total_seconds() <= max_age_hours * 3600


def _is_relevant(item):
    title_lower = item["title"].lower()
    if any(bad in title_lower for bad in BLOCKLIST):
        return False
    return any(kw in title_lower for kw in KEYWORDS)


def dedup_key(item):
    normalized = re.sub(r"[^a-z0-9 ]", "", item["title"].lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def fetch_candidates():
    """Returns every fresh, relevant One Piece Card Game news item, newest
    first, deduped by normalized headline (Google News often surfaces the
    same story from several outlets)."""
    all_items = []
    for feed in NEWS_FEEDS:
        try:
            root = _fetch_feed(feed["url"])
        except Exception as e:
            print(f"WARNING: failed to fetch '{feed['topic']}' feed: {e}")
            continue
        all_items.extend(_parse_items(root, feed["topic"]))

    seen_keys = set()
    candidates = []
    for item in all_items:
        if not _is_recent(item, MAX_AGE_HOURS):
            continue
        if not _is_relevant(item):
            continue
        key = dedup_key(item)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        candidates.append(item)

    epoch = datetime.min.replace(tzinfo=timezone.utc)
    candidates.sort(key=lambda i: i["pub_date"] or epoch, reverse=True)
    return candidates


if __name__ == "__main__":
    for c in fetch_candidates():
        print(f"[{c['topic']}] {c['title']}  ({c['source']})")
