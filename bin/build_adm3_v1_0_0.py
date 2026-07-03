#!/usr/bin/env python3
"""
Build ADM3 (subdistrict / tambon) table for v1.0.

Sources:
- thailand-geography-data subdistricts.json: TIS-1099 codes, English and Thai names, parent district + province codes, postal codes
- mapthai th_adm3.geojson: polygons for centroid computation

Schema (8 columns):
  tis1099_subdistrict_code, parent_district_tis1099_code, parent_province_tis1099_code,
  name_en, name_th, centroid_lat, centroid_lon, postal_code

Output:
  data/v1.0.0/thailand-adm3-subdistricts-v1.0.0.csv
  data/v1.0.0/thailand-adm3-subdistricts-v1.0.0.parquet

Usage:
  python3 bin/build_adm3_v1_0_0.py
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, '/tmp/pylibs')

import pandas as pd
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "data" / "inputs"
OUTPUT_CSV = ROOT / "data" / "v1.0.0" / "thailand-adm3-subdistricts-v1.0.0.csv"
OUTPUT_PARQUET = ROOT / "data" / "v1.0.0" / "thailand-adm3-subdistricts-v1.0.0.parquet"

SCHEMA = [
    "tis1099_subdistrict_code", "parent_district_tis1099_code", "parent_province_tis1099_code",
    "name_en", "name_th",
    "centroid_lat", "centroid_lon",
    "postal_code",
]


def main():
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with open(INPUTS / "thailand-geography-data" / "subdistricts.json", encoding="utf-8") as f:
        subdistricts = json.load(f)
    print(f"Loaded {len(subdistricts)} ADM3 rows from thailand-geography-data")

    # Polygon source
    with open(INPUTS / "mapthai" / "th_adm3.geojson", encoding="utf-8") as f:
        gj = json.load(f)
    polys_by_pcode = {}
    for feat in gj["features"]:
        pcode = feat["properties"].get("ADM3_PCODE", "")
        if pcode.startswith("TH"):
            try:
                code = int(pcode[2:])
            except ValueError:
                continue
            polys_by_pcode[code] = shape(feat["geometry"])
    print(f"Loaded {len(polys_by_pcode)} ADM3 polygons from mapthai")

    rows = []
    matched_polys = 0
    for sd in subdistricts:
        code = sd.get("subdistrictCode")
        if code is None:
            continue
        district_code = sd.get("districtCode")
        province_code = sd.get("provinceCode")

        row = {
            "tis1099_subdistrict_code": code,
            "parent_district_tis1099_code": district_code,
            "parent_province_tis1099_code": province_code,
            "name_en": (sd.get("subdistrictNameEn") or "").strip(),
            "name_th": (sd.get("subdistrictNameTh") or "").strip(),
            "postal_code": sd.get("postalCode") or "",
        }

        poly = polys_by_pcode.get(code)
        if poly is not None:
            matched_polys += 1
            centroid = poly.centroid
            row["centroid_lat"] = round(centroid.y, 5)
            row["centroid_lon"] = round(centroid.x, 5)
        else:
            row["centroid_lat"] = ""
            row["centroid_lon"] = ""

        rows.append(row)

    print(f"Matched polygons: {matched_polys}/{len(rows)}")
    if matched_polys < len(rows):
        print(f"  {len(rows) - matched_polys} ADM3 rows have no polygon (mapthai vintage differs from thailand-geography-data)")

    # Write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote CSV: {OUTPUT_CSV}")

    df = pd.read_csv(OUTPUT_CSV, dtype=str)
    INT_COLS = ["tis1099_subdistrict_code", "parent_district_tis1099_code",
                "parent_province_tis1099_code", "postal_code"]
    FLOAT_COLS = ["centroid_lat", "centroid_lon"]
    for c in INT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in FLOAT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Float64")
    df.to_parquet(OUTPUT_PARQUET, engine="pyarrow", compression="snappy", index=False)
    print(f"Wrote Parquet: {OUTPUT_PARQUET}")


if __name__ == "__main__":
    main()
