"""
Live drift detection against cached upstream sources.

For each cached upstream file under `data/inputs/`, re-fetch the canonical raw
URL and compare the SHA-256 hash of the fresh content against the cached copy.
Hashes that differ indicate the upstream has changed since the v1.0 cache was
populated. Differences are listed in the report; the script exits 0 when no
drift is detected and 1 when at least one source has drifted.

Designed for weekly execution under GitHub Actions.

Usage:
    python3 bin/check_upstream_drift.py             # write report, exit 1 on drift
    python3 bin/check_upstream_drift.py --quiet     # write report, suppress per-file logs

Reads:
    data/inputs/<source>/<file>     # cached canonical file content

Writes:
    data/upstream_drift_report.md   # per-source pass/fail with hashes and sizes
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "data" / "inputs"
REPORT = ROOT / "data" / "upstream_drift_report.md"

USER_AGENT = (
    "ThailandCanonicalNamesReference/1.0 "
    "(https://github.com/ReynoldsWJ55; william.reynolds01+tli@gmail.com)"
)

# Canonical raw-content URLs for each cached upstream file. Each entry maps
# the local cached path to the source URL that bin/build_v1_0_0.py originally
# fetched. Keep this table in sync with the build script.
SOURCES: list[tuple[str, str]] = [
    # thailand-geography-data/thailand-geography-json — MIT
    (
        "thailand-geography-data/provinces.json",
        "https://raw.githubusercontent.com/thailand-geography-data/thailand-geography-json/main/src/provinces.json",
    ),
    (
        "thailand-geography-data/districts.json",
        "https://raw.githubusercontent.com/thailand-geography-data/thailand-geography-json/main/src/districts.json",
    ),
    (
        "thailand-geography-data/subdistricts.json",
        "https://raw.githubusercontent.com/thailand-geography-data/thailand-geography-json/main/src/subdistricts.json",
    ),
    # kongvut/thai-province-data — MIT
    (
        "kongvut/province.json",
        "https://raw.githubusercontent.com/kongvut/thai-province-data/master/api/latest/province.json",
    ),
    (
        "kongvut/district.json",
        "https://raw.githubusercontent.com/kongvut/thai-province-data/master/api/latest/district.json",
    ),
    (
        "kongvut/sub_district.json",
        "https://raw.githubusercontent.com/kongvut/thai-province-data/master/api/latest/sub_district.json",
    ),
    # GeoThai/data — MIT
    (
        "geothai/provinces_v1.json",
        "https://raw.githubusercontent.com/GeoThai/data/main/data/v1/provinces.json",
    ),
    (
        "geothai/provinces_v2.json",
        "https://raw.githubusercontent.com/GeoThai/data/main/data/v2/provinces.json",
    ),
    # mapthai — MIT, OCHA-derived polygons
    (
        "mapthai/th_adm1.geojson",
        "https://raw.githubusercontent.com/piyayut-ch/mapthai/master/data-raw/geojson/th_adm1.geojson",
    ),
    (
        "mapthai/th_adm2.geojson",
        "https://raw.githubusercontent.com/piyayut-ch/mapthai/master/data-raw/geojson/th_adm2.geojson",
    ),
    (
        "mapthai/th_adm3.geojson",
        "https://raw.githubusercontent.com/piyayut-ch/mapthai/master/data-raw/geojson/th_adm3.geojson",
    ),
    # pmdscully/thailand_province_border_adjacency — MIT
    (
        "pmdscully/thailand_province_relations.txt",
        "https://raw.githubusercontent.com/pmdscully/thailand_province_border_adjacency/master/thailand_province_relations.txt",
    ),
    # Natural Earth admin-0 country polygons — public domain
    (
        "naturalearth/ne_50m_admin_0_countries.geojson",
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
    ),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fetch_bytes(url: str, timeout: int = 60) -> tuple[bytes | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(), None
    except Exception as exc:
        return None, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="suppress per-file logs")
    args = parser.parse_args()

    results = []
    drift_count = 0
    error_count = 0

    for rel_path, url in SOURCES:
        local = INPUTS / rel_path
        if not args.quiet:
            print(f"check {rel_path}", flush=True)
        if not local.exists():
            results.append(
                {
                    "path": rel_path,
                    "url": url,
                    "status": "missing",
                    "cached_sha256": None,
                    "fresh_sha256": None,
                    "cached_size": None,
                    "fresh_size": None,
                    "error": "cached file not found",
                }
            )
            error_count += 1
            continue

        cached_bytes = local.read_bytes()
        cached_hash = sha256_bytes(cached_bytes)
        fresh, err = fetch_bytes(url)

        if err is not None:
            results.append(
                {
                    "path": rel_path,
                    "url": url,
                    "status": "fetch-error",
                    "cached_sha256": cached_hash,
                    "fresh_sha256": None,
                    "cached_size": len(cached_bytes),
                    "fresh_size": None,
                    "error": err,
                }
            )
            error_count += 1
            continue

        fresh_hash = sha256_bytes(fresh)
        status = "match" if fresh_hash == cached_hash else "drift"
        results.append(
            {
                "path": rel_path,
                "url": url,
                "status": status,
                "cached_sha256": cached_hash,
                "fresh_sha256": fresh_hash,
                "cached_size": len(cached_bytes),
                "fresh_size": len(fresh),
                "error": None,
            }
        )
        if status == "drift":
            drift_count += 1

    # Build report
    today = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append("# Upstream drift report")
    lines.append("")
    lines.append(f"Run: {today}")
    lines.append("")
    lines.append(f"- Sources checked: {len(SOURCES)}")
    lines.append(f"- Drifted: {drift_count}")
    lines.append(f"- Errors: {error_count}")
    lines.append(
        f"- Status: {'DRIFT DETECTED' if drift_count else 'all match'}"
        f"{' (with errors)' if error_count else ''}"
    )
    lines.append("")
    lines.append("| Status | Source | Cached SHA-256 | Fresh SHA-256 | Δ size |")
    lines.append("|---|---|---|---|---:|")
    for r in results:
        c_h = (r["cached_sha256"] or "")[:12]
        f_h = (r["fresh_sha256"] or "")[:12]
        if r["cached_size"] is not None and r["fresh_size"] is not None:
            d_size = r["fresh_size"] - r["cached_size"]
            d_str = f"{d_size:+,}"
        else:
            d_str = "—"
        status_marker = {
            "match": "✓ match",
            "drift": "⚠ DRIFT",
            "fetch-error": "✗ fetch-error",
            "missing": "✗ missing",
        }[r["status"]]
        lines.append(
            f"| {status_marker} | `{r['path']}` | `{c_h}` | `{f_h}` | {d_str} |"
        )
    lines.append("")

    drifts = [r for r in results if r["status"] == "drift"]
    errors = [r for r in results if r["status"] in ("fetch-error", "missing")]
    if drifts:
        lines.append("## Drifted sources")
        lines.append("")
        for r in drifts:
            lines.append(f"### `{r['path']}`")
            lines.append("")
            lines.append(f"- URL: {r['url']}")
            lines.append(f"- Cached SHA-256: `{r['cached_sha256']}`")
            lines.append(f"- Fresh SHA-256:  `{r['fresh_sha256']}`")
            lines.append(
                f"- Size: cached {r['cached_size']:,} bytes → "
                f"fresh {r['fresh_size']:,} bytes "
                f"({r['fresh_size'] - r['cached_size']:+,})"
            )
            lines.append("")
        lines.append("Action: review the upstream change, decide whether the cached copy needs refreshing, and document any schema or content shift in CHANGELOG.md before incorporating into a v1.x release.")
        lines.append("")

    if errors:
        lines.append("## Errors")
        lines.append("")
        for r in errors:
            lines.append(f"- `{r['path']}`: {r['error']}")
        lines.append("")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nreport: {REPORT}")
    print(
        f"sources: {len(SOURCES)} | drift: {drift_count} | errors: {error_count}"
    )

    if drift_count > 0:
        return 1
    if error_count > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
