"""
Internal helper: fetch one chunk of Wikipedia wikitexts and append to cache.

Designed for chunked execution under tight per-call timeouts. Each invocation
processes up to CHUNK_SIZE missing titles, persists progress to
`/tmp/wikipedia_wikitexts.json.gz` after each fetch, then exits.

Usage:
    python3 bin/_fetch_wikitexts_chunk.py [chunk_size]
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "v1.0.0" / "thailand-adm1-provinces-v1.0.0.csv"
CACHE_PATH = Path("/tmp/wikipedia_wikitexts.json.gz")

USER_AGENT = (
    "ThailandCanonicalNamesReference/1.0 "
    "(https://github.com/ReynoldsWJ55; william.reynolds01+tli@gmail.com)"
)


def article_title(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    return urllib.parse.unquote(path.removeprefix("/wiki/"))


def fetch_wikitext(title: str) -> str | None:
    api = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "titles": title,
        "redirects": "1",
    }
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{api}?{qs}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except Exception as exc:
        print(f"  fetch failed: {exc}", file=sys.stderr)
        return None
    pages = data.get("query", {}).get("pages", {})
    for _pid, page in pages.items():
        if "missing" in page:
            return ""  # mark as fetched-but-missing
        revisions = page.get("revisions", [])
        if not revisions:
            return ""
        return revisions[0].get("slots", {}).get("main", {}).get("*", "")
    return None


def main() -> int:
    chunk_size = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    cache: dict[str, str] = {}
    if CACHE_PATH.exists():
        with gzip.open(CACHE_PATH, "rt", encoding="utf-8") as f:
            cache = json.load(f)

    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))
    titles = [article_title(r["wikipedia_article_url"]) for r in rows]
    missing = [t for t in titles if t not in cache]

    print(f"cache: {len(cache)} | missing: {len(missing)}")
    if not missing:
        print("all fetched")
        return 0

    todo = missing[:chunk_size]
    for i, title in enumerate(todo, 1):
        print(f"  [{i}/{len(todo)}] {title}", flush=True)
        wt = fetch_wikitext(title)
        if wt is not None:
            cache[title] = wt
            with gzip.open(CACHE_PATH, "wt", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
        time.sleep(0.4)

    print(f"done. cache: {len(cache)} / {len(titles)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
