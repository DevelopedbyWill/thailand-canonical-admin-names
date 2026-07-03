#!/usr/bin/env python3
"""
Build v0.3.0 of the Thailand canonical administrative-names reference.

Composes the full enrichment pass over v0.1.0:
- name_en_canonical: thailand-geography-data, with Lopburi override applied per overrides.csv
- name_th: thailand-geography-data
- iso3166_2: computed from TIS-1099 code
- region: kongvut geography_id mapped to Royal Institute six-region grouping
- capital + capital_th: Wikidata Q50198 query (76 provinces) + Bangkok one-off (Q1861)
- established_year: Wikidata P571 where available (5 provinces); empty otherwise with methodology note
- centroid_lat + centroid_lon: kongvut subdistrict lat/long aggregated by median per province; Bangkok from Wikidata Q1861 P625
- name_alternates_en: cross-source spelling differences logged in overrides.csv (Loburi for Lopburi at v0.3.0)
- notes: Bangkok administrative-distinction line; other notes added in subsequent passes

Inputs:
    data/inputs/thailand-geography-data/provinces.json
    data/inputs/kongvut/province.json
    data/inputs/wikidata/wd_capitals.json
    data/inputs/wikidata/wd_provinces_modern.json
    data/inputs/wikidata/wd_bangkok_coords.json
    data/inputs/computed/centroids_kongvut_subdistricts.json
    data/overrides.csv

Output:
    data/v0.3.0/thailand-adm-names-v0.3.0.csv
    data/v0.3.0/build_report.md

Usage:
    python3 bin/build_v0_2_0.py
"""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "data" / "inputs"
OVERRIDES = ROOT / "data" / "overrides.csv"
OUTPUT_CSV = ROOT / "data" / "v0.3.0" / "thailand-adm-names-v0.3.0.csv"
OUTPUT_REPORT = ROOT / "data" / "v0.3.0" / "build_report.md"

# v1.0.x release outputs. The same row set ships under the v1.0.0 filename for
# downstream consumers; the v0.3.0 path is preserved as a historical artifact
# for any tool still pinned to that filename. The orchestrator (build_v1_0_0.py)
# calls this script for its "adm1" stage; before this dual-write was added the
# v1.0.0 ADM1 file was hand-promoted at release time and the smoke test's
# byte-identical contract was hollow for ADM1.
RELEASE_CSV = ROOT / "data" / "v1.0.0" / "thailand-adm1-provinces-v1.0.0.csv"
RELEASE_PARQUET = ROOT / "data" / "v1.0.0" / "thailand-adm1-provinces-v1.0.0.parquet"

SCHEMA = [
    # Core identifiers
    "tis1099_code", "iso3166_2", "iso_subdivision_type",
    "hasc", "fips_code", "wikidata_qid", "geonames_id", "osm_relation_id",
    "wikipedia_article_url",
    # Names
    "name_en_canonical", "name_th", "name_alternates_en",
    # Grouping and capital
    "region", "capital", "capital_th",
    # History
    "established_year", "predecessor_tis1099_code",
    # Geography
    "centroid_lat", "centroid_lon",
    "area_km2", "area_rai",
    "bbox_minlat", "bbox_minlon", "bbox_maxlat", "bbox_maxlon",
    "distance_to_bangkok_km",
    # Borders and coastline
    "neighbors", "has_international_border", "bordering_countries",
    "is_coastal", "coastline_length_km",
    # Operational lookups
    "postal_code_prefixes", "telephone_area_codes",
    # Administrative counts
    "num_amphoe", "num_tambon",
    # Notes
    "notes",
]

REGION_MAP = {
    1: "North", 2: "Central", 3: "Northeast",
    4: "West",  5: "East",    6: "South",
}

BANGKOK_NOTE = (
    "Bangkok is administratively a special administrative area "
    "(เขตการปกครองพิเศษ), "
    "not a province. Treated as ADM1 here for compatibility with the dominant "
    "downstream join pattern."
)

PER_TIS_NOTES = {
    64: ("Provincial capital is Sukhothai Thani (สุโขทัยธานี), genuinely a different "
         "name from the province itself rather than a spelling variant; preserved "
         "as-is per the capital-name normalization rule."),
}

THAI_MUNICIPALITY_PREFIXES = (
    "เทศบาลนคร",   # เทศบาลนคร (city municipality)
    "เทศบาลเมือง", # เทศบาลเมือง (town municipality)
    "เทศบาลตำบล",      # เทศบาลตำบล (subdistrict municipality)
)

EN_MUEANG_PREFIX = "Mueang "


def strip_thai_municipality_prefix(name):
    for prefix in THAI_MUNICIPALITY_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):].strip()
    return name


def strip_en_mueang_prefix(name):
    """Strip the 'Mueang ' (เมือง = city) administrative prefix from capital names."""
    if name.startswith(EN_MUEANG_PREFIX):
        return name[len(EN_MUEANG_PREFIX):].strip()
    return name


def normalize_capital_to_province(capital, province_name):
    """When the capital differs from the province only by spacing variants
    (e.g., 'Chonburi' vs 'Chon Buri', 'Phang Nga' vs 'Phangnga'), normalize
    the capital to match the province spelling. When the capital is genuinely
    a different place name (e.g., 'Sukhothai Thani' for Sukhothai province,
    'Bangkok' for Bangkok), keep the capital as-is.
    """
    if not capital or not province_name:
        return capital
    # Compare case-insensitively, ignoring spaces
    if capital.replace(" ", "").lower() == province_name.replace(" ", "").lower():
        return province_name
    return capital


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_overrides():
    overrides = {}
    if OVERRIDES.exists():
        with open(OVERRIDES, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    code = int(row["tis1099_code"])
                except (KeyError, ValueError):
                    continue
                overrides[code] = {
                    "chosen": row["chosen_spelling"],
                    "candidate": row["strict_rendering_candidate"],
                }
    return overrides


def parse_year(iso_date):
    match = re.match(r"^(\d{4})", iso_date or "")
    return int(match.group(1)) if match else None


def build():
    tgd = load_json(INPUTS / "thailand-geography-data" / "provinces.json")
    kv = load_json(INPUTS / "kongvut" / "province.json")
    wd_caps = load_json(INPUTS / "wikidata" / "wd_capitals.json")
    wd_modern = load_json(INPUTS / "wikidata" / "wd_provinces_modern.json")
    bkk = load_json(INPUTS / "wikidata" / "wd_bangkok_coords.json")
    centroids_kv = {int(k): v for k, v in load_json(INPUTS / "computed" / "centroids_kongvut_subdistricts.json").items()}

    # Polygon-derived geometry (mapthai source GeoJSON, OCHA CODs underneath).
    # Used for COMPUTATION only — polygons themselves are not redistributed in the
    # artifact, so the artifact's CC BY 4.0 license is unencumbered. Computed
    # numbers (centroid, area, bbox) are not derivative redistribution of the
    # source polygons.
    polygon_geo_path = INPUTS / "computed" / "polygon_geometry_mapthai.json"
    polygon_geo = {}
    if polygon_geo_path.exists():
        polygon_geo = {int(k): v for k, v in load_json(polygon_geo_path).items()}

    # Trivial-computation enrichment (wikidata_qid, wp_url, area_rai, etc.)
    trivial = {}
    trivial_path = INPUTS / "computed" / "enrichment_trivial.json"
    if trivial_path.exists():
        trivial = {int(k): v for k, v in load_json(trivial_path).items()}

    # Code mappings (hasc, fips, geonames, telephone)
    codes = {}
    codes_path = INPUTS / "computed" / "enrichment_codes.json"
    if codes_path.exists():
        codes = {int(k): v for k, v in load_json(codes_path).items()}

    # OSM relation IDs
    osm_data = {}
    osm_path = INPUTS / "computed" / "osm_relations.json"
    if osm_path.exists():
        osm_data = {int(k): v for k, v in load_json(osm_path).items()}

    # Border and coastline data
    borders = {}
    borders_path = INPUTS / "computed" / "borders_and_coastal.json"
    if borders_path.exists():
        borders = {int(k): v for k, v in load_json(borders_path).items()}

    # Adjacency from pmdscully (MIT) — neighbors as TIS-1099 codes per province
    neighbors_raw = load_json(INPUTS / "pmdscully" / "neighbors_by_tis.json")
    neighbors_by_tis = {int(k): v for k, v in neighbors_raw.items()}

    # Predecessor mapping from historical_mappings.csv (hybrid representation:
    # quick column in main file, structured rows in the separate file).
    predecessor_by_tis = {}
    hm_path = ROOT / "data" / "historical_mappings.csv"
    if hm_path.exists():
        with open(hm_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("event_type") != "province_split":
                    continue
                try:
                    parent_tis = int(row["parent_tis1099_code"])
                    child_tis = int(row["child_tis1099_code"])
                except (KeyError, ValueError):
                    continue
                predecessor_by_tis[child_tis] = parent_tis

    # Build kongvut name_th -> region via geography_id
    kv_th_to_region = {p["name_th"].strip(): REGION_MAP.get(p["geography_id"], "")
                       for p in kv}

    # Curated established years (manually verified against Wikipedia History
    # sections with Royal Gazette / Royal Decree citations). Only entries with
    # verification_status == "CONFIRMED" flow into the main table — entries
    # marked "PARTIAL" stay in data/established_years.csv as documentation of
    # widely-cited dates we have not directly verified against a primary source.
    # The methodology PDF Section 11 (Limitations) explains the threshold.
    curated_years = {}
    cy_path = ROOT / "data" / "established_years.csv"
    if cy_path.exists():
        with open(cy_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("verification_status") != "CONFIRMED":
                    continue
                try:
                    tis = int(row["tis1099_code"])
                    year = int(row["year"])
                except (KeyError, ValueError):
                    continue
                curated_years[tis] = year

    # Build Wikidata inception map (TIS code -> year) — secondary source
    wd_inception = {}
    for r in wd_modern:
        iso = r.get("iso", "")
        if not iso.startswith("TH-"):
            continue
        try:
            tis = int(iso.split("-")[1])
        except ValueError:
            continue
        if "inception" in r:
            year = parse_year(r["inception"])
            if year:
                wd_inception[tis] = year

    # Established-year sourcing rule: only curated CONFIRMED entries flow into
    # the main table. Wikidata P571 values are NOT used as a fallback because
    # P571 entries are themselves single-source with potentially weak provenance,
    # and the artifact's standard is primary-source verification (Royal Decree /
    # Royal Gazette). Wikidata is retained as a comparator in
    # data/inputs/wikidata/ but not promoted to the main table.
    established_year_final = dict(curated_years)

    overrides = load_overrides()

    # Bangkok centroid from Wikidata Q1861
    bkk_point = bkk["results"]["bindings"][0]["coord"]["value"]
    m = re.match(r"^Point\(([\d.\-]+)\s+([\d.\-]+)\)$", bkk_point)
    bkk_lon, bkk_lat = float(m.group(1)), float(m.group(2))

    # Name alternates from Wikidata aliases + Wikipedia redirects + the override registry.
    # See data/inputs/computed/name_alternates_en.json. Populated for 13/77 provinces at v1.0;
    # the rest have no defensible alternate spelling surfaced in the upstream sources.
    alternates_path = INPUTS / "computed" / "name_alternates_en.json"
    alternates = {}
    if alternates_path.exists():
        raw_alternates = load_json(alternates_path)
        for k, v in raw_alternates.items():
            if v:
                alternates[int(k)] = "|".join(v)

    rows = []
    for entry in tgd:
        tis = entry["provinceCode"]
        upstream_name_en = entry["provinceNameEn"].strip()
        name_en_canonical = overrides.get(tis, {}).get("chosen", upstream_name_en)
        name_th = entry["provinceNameTh"].strip()

        iso = f"TH-{tis:02d}"
        wd_rec = wd_caps.get(iso, {})
        capital_en_raw = wd_rec.get("cap_en", "")
        # Strip 'Mueang ' administrative prefix, then normalize spacing-variants
        # to the province spelling where the capital is otherwise the same name.
        capital_en = strip_en_mueang_prefix(capital_en_raw) if capital_en_raw else ""
        capital_en = normalize_capital_to_province(capital_en, name_en_canonical)
        capital_th_raw = wd_rec.get("cap_th", "")
        capital_th = strip_thai_municipality_prefix(capital_th_raw) if capital_th_raw else ""

        # Centroid: prefer polygon-derived (mapthai geojson) over kongvut subdistrict median.
        # Polygon centroid is geometrically correct and not population-biased.
        # If polygon data is missing for a row, fall back to kongvut median.
        # Bangkok had no kongvut subdistrict coords; polygon path now covers it.
        poly = polygon_geo.get(tis, {})
        if poly:
            centroid_lat = poly.get("centroid_lat", "")
            centroid_lon = poly.get("centroid_lon", "")
            area_km2 = poly.get("area_km2", "")
            bbox_minlat = poly.get("bbox_minlat", "")
            bbox_minlon = poly.get("bbox_minlon", "")
            bbox_maxlat = poly.get("bbox_maxlat", "")
            bbox_maxlon = poly.get("bbox_maxlon", "")
        else:
            # Fall back to kongvut centroids; no area/bbox without polygon source
            c = centroids_kv.get(tis)
            if c:
                centroid_lat, centroid_lon, _ = c
            else:
                centroid_lat = centroid_lon = ""
            area_km2 = bbox_minlat = bbox_minlon = bbox_maxlat = bbox_maxlon = ""

        # Bangkok one-off Wikidata centroid is no longer needed (polygon covers it)
        # but kept as a verification anchor in input cache.
        if tis == 10:
            capital_en = "Bangkok"
            capital_th = name_th

        # Neighbors as pipe-separated TIS-1099 codes for portability across CSV/Parquet
        n_list = neighbors_by_tis.get(tis, [])
        neighbors_str = "|".join(str(n) for n in n_list)

        # Pull from enrichment files
        triv = trivial.get(tis, {})
        cod = codes.get(tis, {})
        osm = osm_data.get(tis, {})
        bord = borders.get(tis, {})

        rows.append({
            # Core identifiers
            "tis1099_code":             tis,
            "iso3166_2":                iso,
            "iso_subdivision_type":     triv.get("iso_subdivision_type", ""),
            "hasc":                     cod.get("hasc", ""),
            "fips_code":                cod.get("fips_code", ""),
            "wikidata_qid":             triv.get("wikidata_qid", ""),
            "geonames_id":              cod.get("geonames_id", ""),
            "osm_relation_id":          osm.get("osm_id", "") if osm.get("osm_type") == "relation" else "",
            "wikipedia_article_url":    triv.get("wikipedia_article_url", ""),
            # Names
            "name_en_canonical":        name_en_canonical,
            "name_th":                  name_th,
            "name_alternates_en":       alternates.get(tis, ""),
            # Grouping and capital
            "region":                   kv_th_to_region.get(name_th, ""),
            "capital":                  capital_en,
            "capital_th":               capital_th,
            # History
            "established_year":         established_year_final.get(tis, ""),
            "predecessor_tis1099_code": predecessor_by_tis.get(tis, ""),
            # Geography
            "centroid_lat":             centroid_lat,
            "centroid_lon":             centroid_lon,
            "area_km2":                 area_km2,
            "area_rai":                 triv.get("area_rai", ""),
            "bbox_minlat":              bbox_minlat,
            "bbox_minlon":              bbox_minlon,
            "bbox_maxlat":              bbox_maxlat,
            "bbox_maxlon":              bbox_maxlon,
            "distance_to_bangkok_km":   triv.get("distance_to_bangkok_km", ""),
            # Borders and coastline
            "neighbors":                neighbors_str,
            "has_international_border": "true" if bord.get("has_international_border") else "false",
            "bordering_countries":      bord.get("bordering_countries", ""),
            "is_coastal":               "true" if bord.get("is_coastal") else "false",
            "coastline_length_km":      bord.get("coastline_length_km", "") if bord.get("is_coastal") else "",
            # Operational lookups
            "postal_code_prefixes":     triv.get("postal_code_prefixes", ""),
            "telephone_area_codes":     cod.get("telephone_area_codes", ""),
            # Administrative counts
            "num_amphoe":               triv.get("num_amphoe", ""),
            "num_tambon":               triv.get("num_tambon", ""),
            # Notes
            "notes":                    BANGKOK_NOTE if tis == 10 else PER_TIS_NOTES.get(tis, ""),
        })

    return rows, wd_inception, overrides


def write_csv(rows):
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows(rows)


def write_release_outputs(rows):
    """Write the v1.0.0 ADM1 CSV and parquet at the released filenames.

    CSV is byte-identical to OUTPUT_CSV (same writer, same row order, same
    fields); we duplicate the write so consumers that pin to the v1.0.0
    filename get the same content without a separate promotion step.

    Parquet uses engine="pyarrow" and compression="snappy". v1.0.2 switched
    the parquet engine from fastparquet to pyarrow project-wide; see CHANGELOG.
    Numeric columns whose CSV cells may be empty are kept as the pandas Int64
    nullable-integer type so downstream readers see ints (not floats with
    NaN) for established_year and predecessor_tis1099_code.
    """
    RELEASE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RELEASE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA)
        writer.writeheader()
        writer.writerows(rows)

    # Parquet sibling. Imported lazily so consumers running --tables in a
    # minimal environment without pandas/pyarrow still get the CSV.
    try:
        import pandas as pd
    except ImportError:
        print("  (parquet skipped — pandas not available)")
        return
    df = pd.read_csv(RELEASE_CSV)
    for col in ("established_year", "predecessor_tis1099_code"):
        if col in df.columns:
            df[col] = df[col].astype("Int64")
    try:
        df.to_parquet(RELEASE_PARQUET, engine="pyarrow",
                      compression="snappy", index=False)
    except ImportError:
        print("  (parquet skipped — pyarrow not available)")


def write_report(rows, wd_inception, overrides):
    fields = SCHEMA
    fill = {f: sum(1 for r in rows if r[f] not in ("", None)) for f in fields}

    lines = []
    lines.append("# v0.3.0 Build Report")
    lines.append("")
    lines.append("Generated by `bin/build_v0_2_0.py`. This is the enrichment pass over v0.1.0.")
    lines.append("")
    lines.append("## Column fill rates")
    lines.append("")
    lines.append("| Column | Populated rows | Out of |")
    lines.append("|---|---|---|")
    for f in fields:
        lines.append(f"| `{f}` | {fill[f]} | {len(rows)} |")
    lines.append("")
    lines.append("## Per-column source attribution")
    lines.append("")
    lines.append("| Column | Source(s) |")
    lines.append("|---|---|")
    lines.append("| `tis1099_code` | thailand-geography-data |")
    lines.append("| `iso3166_2` | Computed from `tis1099_code` (`TH-` + zero-padded code) |")
    lines.append("| `name_en_canonical` | thailand-geography-data, with overrides.csv applied |")
    lines.append("| `name_th` | thailand-geography-data |")
    lines.append("| `name_alternates_en` | overrides.csv (cross-source spelling divergences) |")
    lines.append("| `region` | kongvut `geography_id`, mapped to Royal Institute six-region names |")
    lines.append("| `capital` | Wikidata Q50198 P36 label (English); Bangkok one-off |")
    lines.append("| `capital_th` | Wikidata Q50198 P36 Thai label, municipality prefix stripped; Bangkok one-off |")
    lines.append("| `established_year` | Wikidata P571 (5 provinces); empty for the rest pending authoritative-source pass |")
    lines.append("| `centroid_lat` / `centroid_lon` | kongvut subdistrict lat/long aggregated by median per province; Bangkok from Wikidata Q1861 P625 |")
    lines.append("| `notes` | Authored per row for edge cases (Bangkok at v0.3.0) |")
    lines.append("")
    lines.append("## Override registry")
    lines.append("")
    if overrides:
        for code, ov in sorted(overrides.items()):
            lines.append(f"- TIS-1099 {code}: `{ov['candidate']}` -> `{ov['chosen']}` (see `data/overrides.csv` for full audit-trail line)")
    lines.append("")
    lines.append("## Established years (Wikidata P571)")
    lines.append("")
    if wd_inception:
        for tis, year in sorted(wd_inception.items()):
            lines.append(f"- TIS-1099 {tis}: {year}")
    lines.append("")
    lines.append(
        "The remaining 71 of 76 modern provinces have no P571 value on Wikidata. "
        "These rows leave `established_year` empty at v0.3.0; full authoring "
        "against authoritative sources (NSO Yearbook, Royal Decree archive) "
        "occurs in a subsequent pass."
    )
    lines.append("")
    lines.append("## Centroid method note")
    lines.append("")
    lines.append(
        "Centroids are not polygon-geometric centroids at v0.3.0. The mapthai "
        "package stores polygons in R `sf` simple-features objects which the "
        "Python `pyreadr` library cannot parse. As the documented OSS-only "
        "fallback, centroids are computed as the median of subdistrict "
        "coordinates per province from `kongvut/thai-province-data` "
        "(7,124 of 7,452 subdistricts have coordinates). Bangkok has no "
        "subdistrict coordinates in kongvut and uses Wikidata Q1861 P625 "
        "(13.75, 100.5167) as a documented one-off. Polygon-geometric "
        "centroids will replace these in v1.0.0 once an R bridge or an "
        "alternative MIT-licensed polygon source is wired."
    )
    lines.append("")

    OUTPUT_REPORT.write_text("\n".join(lines))


def main():
    rows, wd_inception, overrides = build()
    write_csv(rows)
    write_release_outputs(rows)
    write_report(rows, wd_inception, overrides)
    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")
    print(f"Wrote {len(rows)} rows to {RELEASE_CSV}")
    if RELEASE_PARQUET.exists():
        print(f"Wrote parquet to {RELEASE_PARQUET}")
    print(f"Wrote build report to {OUTPUT_REPORT}")
    print()
    print("Column fill rates:")
    for f in SCHEMA:
        n = sum(1 for r in rows if r[f] not in ("", None))
        bar = "#" * int(40 * n / len(rows))
        print(f"  {f:<22} {n:>3}/{len(rows)}  {bar}")


if __name__ == "__main__":
    main()
