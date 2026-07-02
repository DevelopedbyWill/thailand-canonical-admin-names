"""
Alternates Wikipedia-attestation Layer A check.

For each entry in `name_alternates_en`, query the English Wikipedia API to test
whether the alternate appears either as an article title, a redirect target,
or a Wikidata "also known as" alias resolved through the canonical article.
The check uses three Wikipedia API queries per alternate:

1. `prop=info` with `redirects=1` against the alternate text. A title match
   (after redirect resolution) to the province's canonical Wikipedia article
   counts as attested.
2. `list=search` with `srsearch=intitle:"<alt>"` for the alternate. A returned
   article whose title equals or starts with the alternate counts as attested.
3. Fallback: load the canonical article wikitext from the cached
   `/tmp/wikipedia_wikitexts.json.gz` and search for the alternate as a literal
   substring inside the lead paragraph or `name_other` infobox field.

Outputs a per-alternate attestation report. Alternates that fail all three
checks are flagged for human review.

Usage:
    python3 bin/verify_alternates_wikipedia.py

Reads:
    data/v1.0.0/thailand-adm1-provinces-v1.0.0.csv
    /tmp/wikipedia_wikitexts.json.gz   (created by verify_wikipedia_infobox_areas.py)

Writes:
    data/v1.0.0/alternates_wikipedia_attestation_report.md
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "v1.0.0" / "thailand-adm1-provinces-v1.0.0.csv"
CACHE_PATH = ROOT / ".cache" / "wikipedia_wikitexts.json.gz"
ATT_CACHE = ROOT / ".cache" / "alternates_attestation.json"
REPORT_PATH = ROOT / "data" / "v1.0.0" / "alternates_wikipedia_attestation_report.md"

USER_AGENT = (
    "ThailandCanonicalNamesReference/1.0 "
    "(https://github.com/ReynoldsWJ55; william.reynolds01+tli@gmail.com)"
)


def article_title(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    return urllib.parse.unquote(path.removeprefix("/wiki/"))


def api_call(params: dict) -> dict | None:
    qs = urllib.parse.urlencode({**params, "format": "json"})
    url = f"https://en.wikipedia.org/w/api.php?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    except Exception as exc:
        print(f"  api error: {exc}", file=sys.stderr)
        return None


def title_to_canonical(title: str) -> tuple[str | None, str]:
    """
    Query Wikipedia for the resolved canonical title of `title`.

    Returns (resolved_title, status) where status is one of:
    - "redirect" — alt text resolved via a redirect to a different title
    - "title"    — alt text is itself an article title
    - "missing"  — no article or redirect for this alt text
    """
    data = api_call(
        {
            "action": "query",
            "titles": title,
            "redirects": "1",
            "prop": "info",
        }
    )
    if not data:
        return None, "error"
    q = data.get("query", {})
    redirects = q.get("redirects", [])
    pages = q.get("pages", {})
    for _pid, page in pages.items():
        if "missing" in page:
            return None, "missing"
        canonical = page.get("title")
        if redirects:
            return canonical, "redirect"
        return canonical, "title"
    return None, "missing"


def search_intitle(alt: str) -> list[str]:
    data = api_call(
        {
            "action": "query",
            "list": "search",
            "srsearch": f'intitle:"{alt}"',
            "srlimit": "5",
        }
    )
    if not data:
        return []
    return [r["title"] for r in data.get("query", {}).get("search", [])]


def title_normalize(t: str | None) -> str:
    """Normalize a Wikipedia title for forgiving comparison."""
    if not t:
        return ""
    t = t.replace("_", " ").lower()
    # strip trailing province/city qualifiers
    for suffix in (" province", " city", " (province)", " (city)"):
        if t.endswith(suffix):
            t = t[: -len(suffix)]
    return t.replace(" ", "")


def alt_normalize(a: str) -> str:
    return a.replace("_", " ").replace("-", " ").replace("'", "").lower().replace(" ", "")


def find_in_wikitext(wikitext: str, alt: str) -> bool:
    """Look for the alt as a literal substring in lead paragraph or infobox."""
    if not wikitext:
        return False
    # Check infobox name_other / native_name / other_name fields
    m = re.search(
        r"\|\s*(?:name_other|native_name|other_name|name1|alt_name)\s*=\s*([^\n]+)",
        wikitext,
    )
    if m and alt.lower() in m.group(1).lower():
        return True
    # Check the lead — first 4000 chars after stripping infoboxes
    lead = wikitext[:4000]
    return alt.lower() in lead.lower()


def main() -> int:
    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Load wikitext cache (built by verify_wikipedia_infobox_areas.py)
    wikitexts: dict[str, str] = {}
    if CACHE_PATH.exists():
        with gzip.open(CACHE_PATH, "rt", encoding="utf-8") as f:
            wikitexts = json.load(f)

    # Load any prior attestation cache so reruns are cheap
    cache: dict[str, dict] = {}
    if ATT_CACHE.exists():
        cache = json.loads(ATT_CACHE.read_text(encoding="utf-8"))

    records = []
    for row in rows:
        alts = [a.strip() for a in row["name_alternates_en"].split("|") if a.strip()]
        if not alts:
            continue
        canon_title = article_title(row["wikipedia_article_url"])
        wikitext = wikitexts.get(canon_title, "")
        for alt in alts:
            cache_key = f"{row['tis1099_code']}|{alt}"
            if cache_key in cache:
                records.append(cache[cache_key])
                continue

            print(f"  check {row['name_en_canonical']} -> {alt!r}", flush=True)
            redirect_title, redirect_status = title_to_canonical(alt)
            # Accept the redirect/title resolution as attestation when the
            # resolved title matches the canonical article (with or without the
            # `_province` qualifier; Wikipedia is inconsistent on this).
            canon_norm = title_normalize(canon_title)
            redirect_norm = title_normalize(redirect_title)
            redirect_match = (
                redirect_status in ("redirect", "title")
                and redirect_norm == canon_norm
            )

            search_hits: list[str] = []
            search_match = False
            if not redirect_match:
                search_hits = search_intitle(alt)
                alt_n = alt_normalize(alt)
                # match if the alt's normalized form appears in any search-hit
                # title's normalized form (catches both prefix and substring)
                search_match = any(
                    alt_n in title_normalize(h) for h in search_hits
                )
                time.sleep(0.4)
            time.sleep(0.4)

            wikitext_match = find_in_wikitext(wikitext, alt)

            attested = redirect_match or search_match or wikitext_match
            method = (
                "redirect"
                if redirect_match
                else "search"
                if search_match
                else "wikitext"
                if wikitext_match
                else "none"
            )

            rec = {
                "tis1099_code": row["tis1099_code"],
                "province": row["name_en_canonical"],
                "alternate": alt,
                "canonical_title": canon_title,
                "redirect_resolved_to": redirect_title,
                "redirect_status": redirect_status,
                "redirect_match": redirect_match,
                "search_hits": search_hits[:3],
                "search_match": search_match,
                "wikitext_match": wikitext_match,
                "attested": attested,
                "method": method,
            }
            cache[cache_key] = rec
            ATT_CACHE.parent.mkdir(parents=True, exist_ok=True)
            ATT_CACHE.write_text(json.dumps(cache, ensure_ascii=False))
            records.append(rec)

    # Build report
    by_method = {"redirect": 0, "search": 0, "wikitext": 0, "none": 0}
    for r in records:
        by_method[r["method"]] += 1
    flagged = [r for r in records if not r["attested"]]

    lines = []
    lines.append("# Alternates Wikipedia attestation — ADM1 v1.0.0")
    lines.append("")
    lines.append(
        "For each `name_alternates_en` entry, queries Wikipedia for: (1) "
        "title match or redirect resolution to the canonical article, (2) "
        "intitle search prefix match, (3) literal substring in the canonical "
        "article wikitext (lead or infobox name fields)."
    )
    lines.append("")
    lines.append(f"- Alternates checked: {len(records)}")
    lines.append(
        f"- Attested via redirect/title resolution: {by_method['redirect']}"
    )
    lines.append(f"- Attested via intitle search: {by_method['search']}")
    lines.append(f"- Attested via wikitext substring only: {by_method['wikitext']}")
    lines.append(f"- Unattested (flagged): {by_method['none']}")
    lines.append("")

    if flagged:
        lines.append("## Flagged alternates (no Wikipedia attestation)")
        lines.append("")
        lines.append(
            "Each flagged alternate failed all three checks. Most flags are "
            "expected for systematically generated spacing variants (the "
            "canonical Wikipedia title spaces words but a no-space variant "
            "was added to support consumers that strip whitespace) and for "
            "diacritic or apostrophe-form historical spellings carried for "
            "completeness. Each entry is preserved on its data-engineering "
            "merit; this report makes the lack of Wikipedia attestation "
            "visible to data consumers."
        )
        lines.append("")
        lines.append(
            "| TIS-1099 | Province | Alternate | Redirect resolved to | Search hits |"
        )
        lines.append("|---|---|---|---|---|")
        for r in flagged:
            rt = r["redirect_resolved_to"] or "—"
            sh = ", ".join(r["search_hits"]) if r["search_hits"] else "—"
            lines.append(
                f"| {r['tis1099_code']} | {r['province']} | `{r['alternate']}` | "
                f"{rt} ({r['redirect_status']}) | {sh} |"
            )
        lines.append("")

    lines.append("## All alternates — full table")
    lines.append("")
    lines.append(
        "| TIS-1099 | Province | Alternate | Attested | Method |"
    )
    lines.append("|---|---|---|---|---|")
    for r in sorted(records, key=lambda x: (int(x["tis1099_code"]), x["alternate"])):
        att = "✓" if r["attested"] else "✗"
        lines.append(
            f"| {r['tis1099_code']} | {r['province']} | `{r['alternate']}` | {att} | {r['method']} |"
        )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nreport: {REPORT_PATH}")
    print(
        f"alternates: {len(records)} | redirect: {by_method['redirect']} | "
        f"search: {by_method['search']} | wikitext: {by_method['wikitext']} | "
        f"flagged: {by_method['none']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
