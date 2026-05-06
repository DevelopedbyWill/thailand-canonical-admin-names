"""
Wikipedia infobox cross-check for ADM1 v1.0.0.

For each of the 77 provinces, fetch the Wikipedia article wikitext (cached on
disk after first fetch), extract `area_total_km2` and `coordinates` from the
{{Infobox settlement}} block, and compare to the stored polygon-derived values
in `thailand-adm1-provinces-v1.0.0.csv`.

Outputs a per-province deviation report flagging rows where
- |area_km2 deviation| exceeds 10%
- centroid distance from Wikipedia coordinate exceeds 30 km

The 10% area threshold is documented in methodology Section 9.1: UTM-projected
polygon areas land within +/-10% of Wikipedia infobox values for tested
provinces. Centroid threshold is loose because Wikipedia infobox coordinates
typically point at the provincial capital, not the geographic centroid.

Usage:
    python3 bin/verify_wikipedia_infobox_areas.py

Reads:
    data/v1.0.0/thailand-adm1-provinces-v1.0.0.csv
    /tmp/wikipedia_wikitexts.json.gz  (created on first run)

Writes:
    data/v1.0.0/wikipedia_infobox_verification_report.md
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "v1.0.0" / "thailand-adm1-provinces-v1.0.0.csv"
CACHE_PATH = Path("/tmp/wikipedia_wikitexts.json.gz")
REPORT_PATH = ROOT / "data" / "v1.0.0" / "wikipedia_infobox_verification_report.md"

USER_AGENT = (
    "ThailandCanonicalNamesReference/1.0 "
    "(https://github.com/ReynoldsWJ55; william.reynolds01+tli@gmail.com)"
)

AREA_DEVIATION_THRESHOLD = 0.10  # 10%
CENTROID_DISTANCE_THRESHOLD_KM = 30.0


def load_csv() -> list[dict]:
    with CSV_PATH.open() as f:
        return list(csv.DictReader(f))


def article_title(url: str) -> str:
    """Extract the title from an en.wikipedia.org/wiki/<title> URL."""
    path = urllib.parse.urlparse(url).path
    return urllib.parse.unquote(path.removeprefix("/wiki/"))


def fetch_wikitext(title: str) -> str | None:
    """Fetch raw wikitext for a Wikipedia article title via the API."""
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
    except Exception as exc:
        print(f"  fetch failed: {exc}", file=sys.stderr)
        return None
    pages = data.get("query", {}).get("pages", {})
    for _pid, page in pages.items():
        if "missing" in page:
            return None
        revisions = page.get("revisions", [])
        if not revisions:
            return None
        return revisions[0].get("slots", {}).get("main", {}).get("*", "")
    return None


def load_or_fetch_wikitexts(rows: list[dict]) -> dict[str, str]:
    """Load cached wikitexts or fetch missing entries from Wikipedia."""
    cache: dict[str, str] = {}
    if CACHE_PATH.exists():
        with gzip.open(CACHE_PATH, "rt", encoding="utf-8") as f:
            cache = json.load(f)
        print(f"loaded {len(cache)} wikitexts from cache")

    titles_needed = [article_title(r["wikipedia_article_url"]) for r in rows]
    missing = [t for t in titles_needed if t not in cache]
    if missing:
        print(f"fetching {len(missing)} missing wikitexts...")
        for i, title in enumerate(missing, 1):
            print(f"  [{i}/{len(missing)}] {title}")
            wt = fetch_wikitext(title)
            if wt is not None:
                cache[title] = wt
            time.sleep(0.5)  # be nice to Wikipedia
        # save cache
        with gzip.open(CACHE_PATH, "wt", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
        print(f"saved {len(cache)} wikitexts to {CACHE_PATH}")
    return cache


# Robust extractor for {{Infobox settlement|...}}: balances braces.
def extract_infobox(wikitext: str) -> str | None:
    """Return the body of the first {{Infobox settlement ...}} template."""
    m = re.search(r"\{\{\s*Infobox\s+settlement", wikitext, re.IGNORECASE)
    if not m:
        return None
    start = m.start()
    depth = 0
    i = start
    while i < len(wikitext):
        if wikitext[i : i + 2] == "{{":
            depth += 1
            i += 2
            continue
        if wikitext[i : i + 2] == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return wikitext[start:i]
            continue
        i += 1
    return None


def parse_area_km2(infobox: str) -> float | None:
    """Extract area_total_km2 from infobox body, handling number formatting."""
    m = re.search(r"\|\s*area_total_km2\s*=\s*([0-9,.\s]+)", infobox)
    if not m:
        return None
    raw = m.group(1).strip().rstrip("|").strip()
    raw = raw.replace(",", "").replace(" ", "")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_coord_template(infobox: str) -> tuple[float, float] | None:
    """Extract decimal lat/lon from {{Coord|...}} inside the infobox."""
    # Search the whole infobox for the first Coord template.
    m = re.search(r"\{\{\s*[Cc]oord\s*\|([^}]+)\}\}", infobox)
    if not m:
        return None
    parts = [p.strip() for p in m.group(1).split("|")]
    # Strip named params like "display=inline,title" or "region:TH_type:..."
    nums = []
    direction = None
    for p in parts:
        if "=" in p or ":" in p:
            continue
        if p.upper() in ("N", "S", "E", "W"):
            direction = p.upper()
            nums.append(direction)
            continue
        try:
            nums.append(float(p))
        except ValueError:
            continue

    # Decimal form: lat, lon
    decimal = [x for x in nums if isinstance(x, float)]
    letters = [x for x in nums if isinstance(x, str)]

    if len(decimal) == 2 and not letters:
        return decimal[0], decimal[1]
    # DMS form: deg min sec NS deg min sec EW
    if len(decimal) == 6 and len(letters) == 2:
        lat = decimal[0] + decimal[1] / 60 + decimal[2] / 3600
        if letters[0] == "S":
            lat = -lat
        lon = decimal[3] + decimal[4] / 60 + decimal[5] / 3600
        if letters[1] == "W":
            lon = -lon
        return lat, lon
    # Deg min NS deg min EW
    if len(decimal) == 4 and len(letters) == 2:
        lat = decimal[0] + decimal[1] / 60
        if letters[0] == "S":
            lat = -lat
        lon = decimal[2] + decimal[3] / 60
        if letters[1] == "W":
            lon = -lon
        return lat, lon
    # Deg NS deg EW
    if len(decimal) == 2 and len(letters) == 2:
        lat = decimal[0]
        if letters[0] == "S":
            lat = -lat
        lon = decimal[1]
        if letters[1] == "W":
            lon = -lon
        return lat, lon
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main() -> int:
    rows = load_csv()
    cache = load_or_fetch_wikitexts(rows)

    results = []
    area_flags = []
    coord_flags = []
    parse_failures = []

    for row in rows:
        title = article_title(row["wikipedia_article_url"])
        wikitext = cache.get(title)
        if not wikitext:
            parse_failures.append((title, "no wikitext"))
            continue
        infobox = extract_infobox(wikitext)
        if not infobox:
            parse_failures.append((title, "no Infobox settlement"))
            continue

        wiki_area = parse_area_km2(infobox)
        wiki_coord = parse_coord_template(infobox)
        stored_area = float(row["area_km2"])
        stored_lat = float(row["centroid_lat"])
        stored_lon = float(row["centroid_lon"])

        area_dev = None
        if wiki_area is not None and wiki_area > 0:
            area_dev = (stored_area - wiki_area) / wiki_area

        coord_dist = None
        if wiki_coord is not None:
            coord_dist = haversine_km(
                stored_lat, stored_lon, wiki_coord[0], wiki_coord[1]
            )

        rec = {
            "tis1099_code": row["tis1099_code"],
            "name_en": row["name_en_canonical"],
            "stored_area_km2": stored_area,
            "wiki_area_km2": wiki_area,
            "area_deviation": area_dev,
            "stored_centroid": (stored_lat, stored_lon),
            "wiki_coord": wiki_coord,
            "centroid_distance_km": coord_dist,
        }
        results.append(rec)

        if area_dev is not None and abs(area_dev) > AREA_DEVIATION_THRESHOLD:
            area_flags.append(rec)
        if coord_dist is not None and coord_dist > CENTROID_DISTANCE_THRESHOLD_KM:
            coord_flags.append(rec)

    # Build report
    lines = []
    lines.append("# Wikipedia infobox cross-check — ADM1 v1.0.0")
    lines.append("")
    lines.append(
        "Compares stored polygon-derived `area_km2`, `centroid_lat`, "
        "`centroid_lon` against Wikipedia `{{Infobox settlement}}` "
        "`area_total_km2` and `{{Coord}}`."
    )
    lines.append("")
    lines.append(f"- Provinces processed: {len(results)} / {len(rows)}")
    lines.append(f"- Area deviation flag threshold: > {AREA_DEVIATION_THRESHOLD:.0%}")
    lines.append(
        f"- Centroid distance flag threshold: > {CENTROID_DISTANCE_THRESHOLD_KM:.0f} km "
        "(loose; infobox coords usually point at provincial capital, not geographic centroid)"
    )
    lines.append(f"- Parse failures: {len(parse_failures)}")
    lines.append(f"- Area-deviation flags: {len(area_flags)}")
    lines.append(f"- Centroid-distance flags: {len(coord_flags)}")
    lines.append("")

    if parse_failures:
        lines.append("## Parse failures")
        lines.append("")
        for t, reason in parse_failures:
            lines.append(f"- {t}: {reason}")
        lines.append("")

    lines.append("## Summary statistics")
    lines.append("")
    area_devs = [
        r["area_deviation"] for r in results if r["area_deviation"] is not None
    ]
    coord_dists = [
        r["centroid_distance_km"]
        for r in results
        if r["centroid_distance_km"] is not None
    ]
    if area_devs:
        lines.append(f"- Area deviation: n = {len(area_devs)}")
        lines.append(
            f"  - mean: {sum(area_devs) / len(area_devs):+.2%}, "
            f"min: {min(area_devs):+.2%}, "
            f"max: {max(area_devs):+.2%}, "
            f"abs-max: {max(abs(d) for d in area_devs):.2%}"
        )
    if coord_dists:
        lines.append(f"- Centroid distance: n = {len(coord_dists)}")
        lines.append(
            f"  - mean: {sum(coord_dists) / len(coord_dists):.1f} km, "
            f"max: {max(coord_dists):.1f} km, "
            f"median: {sorted(coord_dists)[len(coord_dists) // 2]:.1f} km"
        )
    lines.append("")

    if area_flags:
        lines.append(
            f"## Area-deviation flags (> {AREA_DEVIATION_THRESHOLD:.0%})"
        )
        lines.append("")
        lines.append(
            "| TIS-1099 | Province | Stored km² | Wikipedia km² | Deviation |"
        )
        lines.append("|---|---|---:|---:|---:|")
        for r in sorted(area_flags, key=lambda x: -abs(x["area_deviation"])):
            lines.append(
                f"| {r['tis1099_code']} | {r['name_en']} | "
                f"{r['stored_area_km2']:,.1f} | {r['wiki_area_km2']:,.1f} | "
                f"{r['area_deviation']:+.2%} |"
            )
        lines.append("")

    if coord_flags:
        lines.append(
            f"## Centroid-distance flags (> {CENTROID_DISTANCE_THRESHOLD_KM:.0f} km)"
        )
        lines.append("")
        lines.append(
            "Centroid is polygon-geometric; Wikipedia infobox coordinates point "
            "at the provincial capital. A flag means the capital sits more than "
            f"{CENTROID_DISTANCE_THRESHOLD_KM:.0f} km from the geographic centroid, "
            "which is interpretable for elongated or coastal provinces."
        )
        lines.append("")
        lines.append(
            "| TIS-1099 | Province | Stored centroid | Wikipedia coord | Distance km |"
        )
        lines.append("|---|---|---|---|---:|")
        for r in sorted(coord_flags, key=lambda x: -x["centroid_distance_km"]):
            sc = r["stored_centroid"]
            wc = r["wiki_coord"]
            lines.append(
                f"| {r['tis1099_code']} | {r['name_en']} | "
                f"{sc[0]:.4f}, {sc[1]:.4f} | "
                f"{wc[0]:.4f}, {wc[1]:.4f} | "
                f"{r['centroid_distance_km']:.1f} |"
            )
        lines.append("")

    lines.append("## All provinces — full table")
    lines.append("")
    lines.append(
        "| TIS-1099 | Province | Stored km² | Wiki km² | Area dev | "
        "Centroid dist km |"
    )
    lines.append("|---|---|---:|---:|---:|---:|")
    for r in sorted(results, key=lambda x: int(x["tis1099_code"])):
        wa = (
            f"{r['wiki_area_km2']:,.1f}"
            if r["wiki_area_km2"] is not None
            else "—"
        )
        ad = (
            f"{r['area_deviation']:+.2%}"
            if r["area_deviation"] is not None
            else "—"
        )
        cd = (
            f"{r['centroid_distance_km']:.1f}"
            if r["centroid_distance_km"] is not None
            else "—"
        )
        lines.append(
            f"| {r['tis1099_code']} | {r['name_en']} | "
            f"{r['stored_area_km2']:,.1f} | {wa} | {ad} | {cd} |"
        )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nreport: {REPORT_PATH}")
    print(
        f"area flags: {len(area_flags)} | coord flags: {len(coord_flags)} | "
        f"parse failures: {len(parse_failures)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
