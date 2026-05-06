#!/usr/bin/env python3
"""
Build the v0.1.0 base table from thailand-geography-data, projected to the
artifact's schema. Apply the Lopburi override from overrides.csv.

This is the foundation pass authored 2026-05-06. The cross-check across all four
input sources is already complete (see cross_check_inputs.py). The 76-of-77
agreement means 76 rows pass through unchanged from the upstream English column;
the one disagreement (ลพบุรี) resolves to "Lopburi" via the override registry.

Empty enrichment columns (capital, capital_th, established_year, region,
name_alternates_en, centroid_lat, centroid_lon) are scheduled for the post-launch
authoring sprint when government-table cross-references run.

Inputs:
    data/inputs/thailand-geography-data/provinces.json
    data/overrides.csv

Output:
    data/v0.1.0/thailand-adm-names-v0.1.0.csv

Usage:
    python3 bin/build_v0_1_0_base.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "data" / "inputs"
OVERRIDES = ROOT / "data" / "overrides.csv"
OUTPUT = ROOT / "data" / "v0.1.0" / "thailand-adm-names-v0.1.0.csv"

SCHEMA_COLUMNS = [
    "tis1099_code",
    "iso3166_2",
    "name_en_canonical",
    "name_th",
    "name_alternates_en",
    "region",
    "capital",
    "capital_th",
    "established_year",
    "centroid_lat",
    "centroid_lon",
    "notes",
]

# Bangkok-specific notes line; other notes added in post-launch enrichment pass
BANGKOK_NOTE = (
    "Bangkok is administratively a special administrative area "
    "(เขตการปกครองพิเศษ), not a province. Treated as ADM1 here for "
    "compatibility with the dominant downstream join pattern."
)


def load_overrides():
    """Return {tis_code: chosen_spelling} dict from overrides.csv."""
    overrides = {}
    if not OVERRIDES.exists():
        return overrides
    with open(OVERRIDES) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                code = int(row["tis1099_code"])
                overrides[code] = row["chosen_spelling"]
            except (KeyError, ValueError):
                continue
    return overrides


def build_base_table():
    """Project thailand-geography-data provinces to the v0.1.0 schema."""
    with open(INPUTS / "thailand-geography-data" / "provinces.json") as f:
        upstream = json.load(f)

    overrides = load_overrides()

    rows = []
    for entry in upstream:
        tis_code = entry["provinceCode"]
        upstream_name_en = entry["provinceNameEn"].strip()
        chosen_name_en = overrides.get(tis_code, upstream_name_en)

        rows.append({
            "tis1099_code":       tis_code,
            "iso3166_2":          f"TH-{tis_code:02d}",
            "name_en_canonical":  chosen_name_en,
            "name_th":            entry["provinceNameTh"].strip(),
            "name_alternates_en": "",  # post-launch enrichment
            "region":             "",  # post-launch enrichment
            "capital":            "",  # post-launch enrichment
            "capital_th":         "",  # post-launch enrichment
            "established_year":   "",  # post-launch enrichment (2011 for Bueng Kan, etc.)
            "centroid_lat":       "",  # post-launch (mapthai polygon centroids)
            "centroid_lon":       "",  # post-launch
            "notes":              BANGKOK_NOTE if tis_code == 10 else "",
        })

    return rows


def write_csv(rows):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT}")


def main():
    rows = build_base_table()
    overrides = load_overrides()
    print(f"Pulled {len(rows)} provinces from thailand-geography-data")
    print(f"Applied {len(overrides)} override(s) from overrides.csv")
    if overrides:
        for code, name in overrides.items():
            print(f"  TIS-1099 {code} -> {name}")
    write_csv(rows)


if __name__ == "__main__":
    main()
