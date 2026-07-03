#!/usr/bin/env python3
"""
Build ADM2 (district / amphoe) table for v1.0.

Sources:
- thailand-geography-data districts.json: TIS-1099 codes, English and Thai names, parent province codes
- thailand-geography-data subdistricts.json: postal codes (for prefix derivation), tambon counts
- mapthai th_adm2.geojson: polygons for centroid / area / bbox computation (UTM-projected per Section 9)

Schema (14 columns):
  tis1099_district_code, parent_province_tis1099_code, name_en, name_th,
  centroid_lat, centroid_lon, area_km2,
  bbox_minlat, bbox_minlon, bbox_maxlat, bbox_maxlon,
  num_tambon, postal_code_prefixes, notes

Output:
  data/v1.0.0/thailand-adm2-districts-v1.0.0.csv
  data/v1.0.0/thailand-adm2-districts-v1.0.0.parquet

Usage:
  python3 bin/build_adm2_v1_0_0.py
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

# Make optional dependencies importable from /tmp/pylibs
sys.path.insert(0, '/tmp/pylibs')

import pandas as pd
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "data" / "inputs"
OUTPUT_CSV = ROOT / "data" / "v1.0.0" / "thailand-adm2-districts-v1.0.0.csv"
OUTPUT_PARQUET = ROOT / "data" / "v1.0.0" / "thailand-adm2-districts-v1.0.0.parquet"

SCHEMA = [
    "tis1099_district_code", "parent_province_tis1099_code",
    "name_en", "name_th",
    "centroid_lat", "centroid_lon", "area_km2",
    "bbox_minlat", "bbox_minlon", "bbox_maxlat", "bbox_maxlon",
    "num_tambon", "postal_code_prefixes", "notes",
]

trans_47 = Transformer.from_crs("EPSG:4326", "EPSG:32647", always_xy=True)
trans_48 = Transformer.from_crs("EPSG:4326", "EPSG:32648", always_xy=True)


def project_for_area(geom, lon_centroid):
    t = trans_47 if lon_centroid < 102.0 else trans_48
    return transform(lambda x, y, z=None: t.transform(x, y), geom)


def main():
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Load primary source: districts from thailand-geography-data
    with open(INPUTS / "thailand-geography-data" / "districts.json", encoding="utf-8") as f:
        districts = json.load(f)
    print(f"Loaded {len(districts)} ADM2 rows from thailand-geography-data")

    # Load subdistricts to compute num_tambon and postal prefix per district
    with open(INPUTS / "thailand-geography-data" / "subdistricts.json", encoding="utf-8") as f:
        subdistricts = json.load(f)
    print(f"Loaded {len(subdistricts)} ADM3 rows for tambon-count and postal-prefix derivation")

    tambon_count_by_district = defaultdict(int)
    postal_prefixes_by_district = defaultdict(set)
    for sd in subdistricts:
        d = sd.get("districtCode")
        if d is None:
            continue
        tambon_count_by_district[d] += 1
        pc = sd.get("postalCode")
        if pc:
            postal_prefixes_by_district[d].add(str(pc)[:4])  # 4-digit prefix at ADM2

    # Load polygon source
    with open(INPUTS / "mapthai" / "th_adm2.geojson", encoding="utf-8") as f:
        gj = json.load(f)
    polys_by_pcode = {}
    for feat in gj["features"]:
        pcode = feat["properties"].get("ADM2_PCODE", "")
        if pcode.startswith("TH"):
            try:
                code = int(pcode[2:])
            except ValueError:
                continue
            polys_by_pcode[code] = shape(feat["geometry"])

    print(f"Loaded {len(polys_by_pcode)} ADM2 polygons from mapthai")

    rows = []
    matched_polys = 0
    for d in districts:
        code = d.get("districtCode")
        if code is None:
            continue
        province_code = d.get("provinceCode")

        row = {
            "tis1099_district_code": code,
            "parent_province_tis1099_code": province_code,
            "name_en": (d.get("districtNameEn") or "").strip(),
            "name_th": (d.get("districtNameTh") or "").strip(),
            "num_tambon": tambon_count_by_district.get(code, 0),
            "postal_code_prefixes": "|".join(sorted(postal_prefixes_by_district.get(code, []))),
            "notes": "",
        }

        # Geometry from mapthai
        poly = polys_by_pcode.get(code)
        if poly is not None:
            matched_polys += 1
            centroid = poly.centroid
            minx, miny, maxx, maxy = poly.bounds
            poly_utm = project_for_area(poly, centroid.x)
            row["centroid_lat"] = round(centroid.y, 5)
            row["centroid_lon"] = round(centroid.x, 5)
            row["area_km2"] = round(poly_utm.area / 1_000_000.0, 1)
            row["bbox_minlat"] = round(miny, 5)
            row["bbox_minlon"] = round(minx, 5)
            row["bbox_maxlat"] = round(maxy, 5)
            row["bbox_maxlon"] = round(maxx, 5)
        else:
            for col in ("centroid_lat", "centroid_lon", "area_km2",
                        "bbox_minlat", "bbox_minlon", "bbox_maxlat", "bbox_maxlon"):
                row[col] = ""

        rows.append(row)

    print(f"Matched polygons: {matched_polys}/{len(rows)}")
    unmatched = sum(1 for r in rows if r["centroid_lat"] == "")
    if unmatched:
        print(f"  {unmatched} ADM2 rows have no polygon (mapthai vintage differs from thailand-geography-data)")

    # Write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote CSV: {OUTPUT_CSV}")

    # Write Parquet
    df = pd.read_csv(OUTPUT_CSV, dtype=str)
    INT_COLS = ["tis1099_district_code", "parent_province_tis1099_code", "num_tambon"]
    FLOAT_COLS = ["centroid_lat", "centroid_lon", "area_km2",
                  "bbox_minlat", "bbox_minlon", "bbox_maxlat", "bbox_maxlon"]
    for c in INT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in FLOAT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Float64")
    df.to_parquet(OUTPUT_PARQUET, engine="pyarrow", compression="snappy", index=False)
    print(f"Wrote Parquet: {OUTPUT_PARQUET}")


if __name__ == "__main__":
    main()
