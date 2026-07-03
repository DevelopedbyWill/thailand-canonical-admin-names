#!/usr/bin/env python3
"""
Comprehensive validator for v0.3.0 of the Thailand canonical names reference.

Runs ~35 checks covering:
  - Per-column format and population (every column)
  - Per-column uniqueness where applicable
  - Range / domain checks for numeric and enum columns
  - Cross-column consistency (derived columns match source)
  - Cross-source verification against cached MIT inputs
  - Referential integrity (neighbors, predecessor exist in table)
  - Geographic plausibility (centroids inside bbox, bbox inside Thailand)
  - Statistical sanity (province area sum matches Thailand total)
  - Special-row checks (Bangkok TIS-10 invariants)

Outputs:
  data/v0.3.0/validation_report.md  (detailed)

Usage:
  python3 bin/validate_v0_3_0.py
"""

import csv
import json
import re
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "data" / "inputs"
TABLE  = ROOT / "data" / "v0.3.0" / "thailand-adm-names-v0.3.0.csv"
REPORT = ROOT / "data" / "v0.3.0" / "validation_report.md"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
THAILAND_BBOX = (5.5, 21.0, 96.5, 106.5)  # lat_min, lat_max, lon_min, lon_max
EXPECTED_REGION_COUNTS = {"North": 9, "Central": 22, "Northeast": 20, "West": 5, "East": 7, "South": 14}
VALID_NEIGHBOR_COUNTRIES = {"Myanmar", "Laos", "Cambodia", "Malaysia"}
VALID_ISO_TYPES = {"Province", "Special Administrative Area"}
VALID_REGIONS = set(EXPECTED_REGION_COUNTS.keys())

# Thailand published total area (RFD figures): ~513,120 km² (varies slightly by source)
THAILAND_TOTAL_AREA_KM2 = 513120
AREA_TOLERANCE_PCT = 5.0

# Thailand published administrative-subunit totals
THAILAND_TOTAL_AMPHOE_EXPECTED = (878, 928)  # range; varies by year/source
THAILAND_TOTAL_TAMBON_EXPECTED = (7000, 7500)

# Bangkok-specific invariants
BANGKOK_TIS = 10
BANGKOK_QID = "Q1861"

# Format patterns
PAT_ISO3166_2 = re.compile(r"^TH-\d{2}$")
PAT_HASC = re.compile(r"^TH\.[A-Z]{2}$")
PAT_FIPS = re.compile(r"^TH\d{2}$")
PAT_QID = re.compile(r"^Q\d+$")
PAT_WIKIPEDIA = re.compile(r"^https://en\.wikipedia\.org/wiki/.+$")
PAT_POSTAL_PREFIX = re.compile(r"^\d{2}$")
PAT_PHONE_CODE = re.compile(r"^\d{2,3}$")
PAT_EN_NAME = re.compile(r"^[A-Za-z][A-Za-z \-']*$")
PAT_THAI = re.compile(r"^[฀-๿]+$")
PAT_BOOL = re.compile(r"^(true|false)$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_table():
    with open(TABLE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    rad = math.pi / 180.0
    dlat = (lat2 - lat1) * rad
    dlon = (lon2 - lon1) * rad
    a = math.sin(dlat/2)**2 + math.cos(lat1*rad) * math.cos(lat2*rad) * math.sin(dlon/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))


def fail(msg): return ("FAIL", msg)
def warn(msg): return ("REVIEW", msg)
def info(msg): return ("INFO", msg)


# ---------------------------------------------------------------------------
# CHECK FUNCTIONS — each returns a list of (severity, message) tuples
# ---------------------------------------------------------------------------

def check_01_row_count(rows):
    return [] if len(rows) == 77 else [fail(f"row count: expected 77, got {len(rows)}")]


def check_02_tis_uniqueness(rows):
    out = []
    seen = set()
    for r in rows:
        try:
            tis = int(r["tis1099_code"])
        except (KeyError, ValueError):
            out.append(fail(f"non-integer tis1099_code: {r.get('tis1099_code')}"))
            continue
        if tis in seen:
            out.append(fail(f"duplicate tis1099_code {tis}"))
        seen.add(tis)
    return out


def check_03_tis_range(rows):
    out = []
    for r in rows:
        try: tis = int(r["tis1099_code"])
        except: continue
        if not (10 <= tis <= 96):
            out.append(fail(f"tis1099_code {tis} out of expected range 10-96"))
    return out


def check_04_iso_format_and_match(rows):
    out = []
    for r in rows:
        iso = r.get("iso3166_2", "")
        if not PAT_ISO3166_2.match(iso):
            out.append(fail(f"TIS-{r['tis1099_code']}: malformed iso3166_2 '{iso}'"))
            continue
        try:
            iso_num = int(iso.split("-")[1])
            tis = int(r["tis1099_code"])
            if iso_num != tis:
                out.append(fail(f"TIS-{tis}: iso3166_2 '{iso}' does not match tis1099_code"))
        except ValueError:
            out.append(fail(f"TIS-{r['tis1099_code']}: iso3166_2 numeric parse error"))
    return out


def check_05_iso_uniqueness(rows):
    out = []
    seen = {}
    for r in rows:
        iso = r.get("iso3166_2", "")
        if iso in seen:
            out.append(fail(f"duplicate iso3166_2 {iso} (TIS-{seen[iso]} and TIS-{r['tis1099_code']})"))
        seen[iso] = r["tis1099_code"]
    return out


def check_06_iso_type(rows):
    out = []
    for r in rows:
        t = r.get("iso_subdivision_type", "")
        if t not in VALID_ISO_TYPES:
            out.append(fail(f"TIS-{r['tis1099_code']}: invalid iso_subdivision_type '{t}'"))
        if int(r["tis1099_code"]) == BANGKOK_TIS and t != "Special Administrative Area":
            out.append(fail(f"Bangkok TIS-10 must be Special Administrative Area, got '{t}'"))
        if int(r["tis1099_code"]) != BANGKOK_TIS and t != "Province":
            out.append(fail(f"TIS-{r['tis1099_code']}: non-Bangkok province must be Province, got '{t}'"))
    return out


def check_07_hasc_format_and_uniqueness(rows):
    out = []
    seen = {}
    for r in rows:
        h = r.get("hasc", "")
        if not h:
            out.append(fail(f"TIS-{r['tis1099_code']}: hasc empty"))
            continue
        if not PAT_HASC.match(h):
            out.append(fail(f"TIS-{r['tis1099_code']}: malformed hasc '{h}'"))
            continue
        if h in seen:
            out.append(fail(f"duplicate hasc {h}"))
        seen[h] = r["tis1099_code"]
    return out


def check_08_fips_format_and_uniqueness(rows):
    out = []
    seen = {}
    for r in rows:
        f = r.get("fips_code", "")
        if not f:
            out.append(fail(f"TIS-{r['tis1099_code']}: fips_code empty"))
            continue
        if not PAT_FIPS.match(f):
            out.append(fail(f"TIS-{r['tis1099_code']}: malformed fips_code '{f}'"))
            continue
        if f in seen:
            out.append(fail(f"duplicate fips_code {f}"))
        seen[f] = r["tis1099_code"]
    return out


def check_09_wikidata_qid(rows):
    out = []
    seen = {}
    for r in rows:
        q = r.get("wikidata_qid", "")
        if not q:
            out.append(fail(f"TIS-{r['tis1099_code']}: wikidata_qid empty"))
            continue
        if not PAT_QID.match(q):
            out.append(fail(f"TIS-{r['tis1099_code']}: malformed wikidata_qid '{q}'"))
            continue
        if q in seen:
            out.append(fail(f"duplicate wikidata_qid {q}"))
        seen[q] = r["tis1099_code"]
        if int(r["tis1099_code"]) == BANGKOK_TIS and q != BANGKOK_QID:
            out.append(fail(f"Bangkok wikidata_qid must be {BANGKOK_QID}, got '{q}'"))
    return out


def check_10_geonames_id(rows):
    out = []
    seen = {}
    for r in rows:
        g = r.get("geonames_id", "")
        if not g:
            out.append(fail(f"TIS-{r['tis1099_code']}: geonames_id empty"))
            continue
        try:
            gi = int(g)
        except ValueError:
            out.append(fail(f"TIS-{r['tis1099_code']}: geonames_id non-integer '{g}'"))
            continue
        if gi <= 0:
            out.append(fail(f"TIS-{r['tis1099_code']}: geonames_id non-positive {gi}"))
        if gi in seen:
            out.append(fail(f"duplicate geonames_id {gi}"))
        seen[gi] = r["tis1099_code"]
    return out


def check_11_osm_relation_id(rows):
    """Optional column; when present must be positive integer."""
    out = []
    seen = {}
    populated = 0
    for r in rows:
        o = r.get("osm_relation_id", "")
        if not o:
            continue
        populated += 1
        try:
            oi = int(o)
        except ValueError:
            out.append(fail(f"TIS-{r['tis1099_code']}: osm_relation_id non-integer '{o}'"))
            continue
        if oi <= 0:
            out.append(fail(f"TIS-{r['tis1099_code']}: osm_relation_id non-positive {oi}"))
        if oi in seen:
            out.append(fail(f"duplicate osm_relation_id {oi}"))
        seen[oi] = r["tis1099_code"]
    if populated < 70:
        out.append(warn(f"only {populated}/77 osm_relation_id populated"))
    return out


def check_12_wikipedia_url(rows):
    out = []
    seen = {}
    for r in rows:
        u = r.get("wikipedia_article_url", "")
        if not u:
            out.append(fail(f"TIS-{r['tis1099_code']}: wikipedia_article_url empty"))
            continue
        if not PAT_WIKIPEDIA.match(u):
            out.append(fail(f"TIS-{r['tis1099_code']}: malformed wikipedia_article_url '{u}'"))
        if u in seen:
            out.append(fail(f"duplicate wikipedia_article_url {u}"))
        seen[u] = r["tis1099_code"]
    return out


def check_13_name_en_canonical(rows):
    out = []
    seen = {}
    for r in rows:
        n = r.get("name_en_canonical", "")
        if not n:
            out.append(fail(f"TIS-{r['tis1099_code']}: name_en_canonical empty"))
            continue
        if not PAT_EN_NAME.match(n):
            out.append(fail(f"TIS-{r['tis1099_code']}: name_en_canonical contains non-Latin chars '{n}'"))
        if n in seen:
            out.append(fail(f"duplicate name_en_canonical '{n}'"))
        seen[n] = r["tis1099_code"]
    return out


def check_14_name_th(rows):
    out = []
    seen = {}
    for r in rows:
        n = r.get("name_th", "")
        if not n:
            out.append(fail(f"TIS-{r['tis1099_code']}: name_th empty"))
            continue
        if not PAT_THAI.match(n):
            out.append(fail(f"TIS-{r['tis1099_code']}: name_th not pure Thai script '{n}'"))
        if n in seen:
            out.append(fail(f"duplicate name_th '{n}'"))
        seen[n] = r["tis1099_code"]
    return out


def check_15_name_alternates(rows):
    """Alternates must be Latin, must not equal canonical, pipe-separated."""
    out = []
    for r in rows:
        a = r.get("name_alternates_en", "")
        if not a:
            continue
        for alt in a.split("|"):
            alt = alt.strip()
            if not alt:
                out.append(fail(f"TIS-{r['tis1099_code']}: empty alternate in name_alternates_en"))
                continue
            if alt == r["name_en_canonical"]:
                out.append(fail(f"TIS-{r['tis1099_code']}: alternate '{alt}' equals canonical"))
            if not PAT_EN_NAME.match(alt):
                out.append(fail(f"TIS-{r['tis1099_code']}: alternate '{alt}' contains non-Latin chars"))
    return out


def check_16_region(rows):
    out = []
    counts = {}
    for r in rows:
        rg = r.get("region", "")
        if rg not in VALID_REGIONS:
            out.append(fail(f"TIS-{r['tis1099_code']}: invalid region '{rg}'"))
        counts[rg] = counts.get(rg, 0) + 1
    for region, expected in EXPECTED_REGION_COUNTS.items():
        actual = counts.get(region, 0)
        if actual != expected:
            out.append(fail(f"region '{region}': expected {expected}, got {actual}"))
    return out


def check_17_capital(rows):
    out = []
    for r in rows:
        c = r.get("capital", "")
        ct = r.get("capital_th", "")
        if not c:
            out.append(fail(f"TIS-{r['tis1099_code']}: capital empty"))
        if not ct:
            out.append(fail(f"TIS-{r['tis1099_code']}: capital_th empty"))
        if ct and not PAT_THAI.match(ct):
            out.append(fail(f"TIS-{r['tis1099_code']}: capital_th not pure Thai '{ct}'"))
    return out


def check_18_established_year(rows):
    """Established year must come from established_years.csv with verification_status=CONFIRMED."""
    out = []
    cy_path = ROOT / "data" / "established_years.csv"
    confirmed = {}
    if cy_path.exists():
        with open(cy_path, encoding="utf-8") as f:
            for cr in csv.DictReader(f):
                if cr.get("verification_status") == "CONFIRMED":
                    try:
                        confirmed[int(cr["tis1099_code"])] = int(cr["year"])
                    except (KeyError, ValueError):
                        pass
    for r in rows:
        y = r.get("established_year", "")
        tis = int(r["tis1099_code"])
        if not y:
            continue
        try:
            yi = int(y)
        except ValueError:
            out.append(fail(f"TIS-{tis}: established_year non-integer '{y}'"))
            continue
        if not (1500 < yi < 2030):
            out.append(fail(f"TIS-{tis}: established_year {yi} out of plausible range 1500-2030"))
        expected = confirmed.get(tis)
        if expected is None:
            out.append(fail(f"TIS-{tis}: established_year populated ({yi}) but no CONFIRMED row in established_years.csv"))
        elif expected != yi:
            out.append(fail(f"TIS-{tis}: established_year ({yi}) differs from CONFIRMED row ({expected})"))
    return out


def check_19_predecessor(rows):
    out = []
    by_tis = {int(r["tis1099_code"]): r for r in rows}
    hm_path = ROOT / "data" / "historical_mappings.csv"
    hm_pred = {}
    if hm_path.exists():
        with open(hm_path, encoding="utf-8") as f:
            for hr in csv.DictReader(f):
                if hr.get("event_type") != "province_split": continue
                try:
                    hm_pred[int(hr["child_tis1099_code"])] = int(hr["parent_tis1099_code"])
                except (KeyError, ValueError): pass
    for r in rows:
        v = (r.get("predecessor_tis1099_code") or "").strip()
        if not v: continue
        try: p = int(v)
        except ValueError:
            out.append(fail(f"TIS-{r['tis1099_code']}: predecessor non-integer '{v}'"))
            continue
        if p not in by_tis:
            out.append(fail(f"TIS-{r['tis1099_code']}: predecessor TIS-{p} not in table"))
        tis = int(r["tis1099_code"])
        if tis in hm_pred and hm_pred[tis] != p:
            out.append(fail(f"TIS-{tis}: predecessor mismatch with historical_mappings (table={p}, hm={hm_pred[tis]})"))
        if tis == p:
            out.append(fail(f"TIS-{tis}: predecessor self-reference"))
    return out


def check_20_centroid_coordinates(rows):
    out = []
    lat_min, lat_max, lon_min, lon_max = THAILAND_BBOX
    for r in rows:
        try:
            lat = float(r["centroid_lat"])
            lon = float(r["centroid_lon"])
        except (KeyError, ValueError):
            out.append(fail(f"TIS-{r['tis1099_code']}: centroid non-numeric"))
            continue
        if not (lat_min < lat < lat_max and lon_min < lon < lon_max):
            out.append(fail(f"TIS-{r['tis1099_code']}: centroid ({lat},{lon}) outside Thailand bbox"))
    return out


def check_21_centroid_inside_bbox(rows):
    out = []
    for r in rows:
        try:
            lat = float(r["centroid_lat"])
            lon = float(r["centroid_lon"])
            mn_lat = float(r["bbox_minlat"])
            mn_lon = float(r["bbox_minlon"])
            mx_lat = float(r["bbox_maxlat"])
            mx_lon = float(r["bbox_maxlon"])
        except (KeyError, ValueError):
            continue
        if not (mn_lat <= lat <= mx_lat and mn_lon <= lon <= mx_lon):
            out.append(fail(f"TIS-{r['tis1099_code']}: centroid ({lat},{lon}) outside row's bbox"))
    return out


def check_22_bbox_consistency(rows):
    out = []
    for r in rows:
        try:
            mn_lat = float(r["bbox_minlat"])
            mx_lat = float(r["bbox_maxlat"])
            mn_lon = float(r["bbox_minlon"])
            mx_lon = float(r["bbox_maxlon"])
        except (KeyError, ValueError):
            out.append(fail(f"TIS-{r['tis1099_code']}: bbox non-numeric"))
            continue
        if mn_lat >= mx_lat:
            out.append(fail(f"TIS-{r['tis1099_code']}: bbox_minlat >= bbox_maxlat"))
        if mn_lon >= mx_lon:
            out.append(fail(f"TIS-{r['tis1099_code']}: bbox_minlon >= bbox_maxlon"))
    return out


def check_23_area_positive_and_rai(rows):
    out = []
    for r in rows:
        try:
            km2 = float(r["area_km2"])
            rai = float(r["area_rai"])
        except (KeyError, ValueError):
            out.append(fail(f"TIS-{r['tis1099_code']}: area non-numeric"))
            continue
        if km2 <= 0:
            out.append(fail(f"TIS-{r['tis1099_code']}: area_km2 non-positive {km2}"))
        if rai <= 0:
            out.append(fail(f"TIS-{r['tis1099_code']}: area_rai non-positive {rai}"))
        # Cross-check: 1 km² = 625 rai (within 0.5 rounding)
        expected_rai = km2 * 625
        if abs(rai - expected_rai) > 1.0:
            out.append(fail(f"TIS-{r['tis1099_code']}: area_rai {rai} != area_km2*625 ({expected_rai})"))
    return out


def check_24_total_area(rows):
    out = []
    total = sum(float(r.get("area_km2", 0) or 0) for r in rows)
    diff_pct = abs(total - THAILAND_TOTAL_AREA_KM2) / THAILAND_TOTAL_AREA_KM2 * 100
    if diff_pct > AREA_TOLERANCE_PCT:
        out.append(fail(f"sum of area_km2 = {total:,.0f}, expected ~{THAILAND_TOTAL_AREA_KM2:,} ({diff_pct:.1f}% off)"))
    else:
        out.append(info(f"sum of area_km2 = {total:,.0f} ({diff_pct:+.2f}% from RFD published total)"))
    return out


def check_25_distance_to_bangkok(rows):
    out = []
    bkk_row = next((r for r in rows if int(r["tis1099_code"]) == BANGKOK_TIS), None)
    if not bkk_row:
        return [fail("Bangkok row not found for distance check")]
    bkk_lat, bkk_lon = float(bkk_row["centroid_lat"]), float(bkk_row["centroid_lon"])
    for r in rows:
        tis = int(r["tis1099_code"])
        try:
            d = float(r["distance_to_bangkok_km"])
            lat = float(r["centroid_lat"])
            lon = float(r["centroid_lon"])
        except (KeyError, ValueError):
            out.append(fail(f"TIS-{tis}: distance_to_bangkok_km or centroid non-numeric"))
            continue
        if d < 0:
            out.append(fail(f"TIS-{tis}: distance_to_bangkok_km negative {d}"))
        if tis == BANGKOK_TIS and d != 0:
            out.append(fail(f"Bangkok distance_to_bangkok_km must be 0, got {d}"))
        # Recompute and compare
        computed = haversine_km(bkk_lat, bkk_lon, lat, lon)
        if abs(d - computed) > 5:
            out.append(fail(f"TIS-{tis}: distance_to_bangkok_km {d} differs from recomputed {computed:.1f}"))
    return out


def check_26_neighbors_membership(rows):
    """All listed neighbors exist as rows."""
    out = []
    by_tis = {int(r["tis1099_code"]) for r in rows}
    for r in rows:
        tis = int(r["tis1099_code"])
        n_str = r.get("neighbors", "")
        if not n_str: continue
        for nstr in n_str.split("|"):
            try: n = int(nstr)
            except ValueError:
                out.append(fail(f"TIS-{tis}: non-integer neighbor '{nstr}'"))
                continue
            if n not in by_tis:
                out.append(fail(f"TIS-{tis}: neighbor TIS-{n} not in table"))
            if n == tis:
                out.append(fail(f"TIS-{tis}: self-reference in neighbors"))
    return out


def check_27_neighbors_symmetry(rows):
    out = []
    by_tis = {int(r["tis1099_code"]): r for r in rows}
    for tis, r in by_tis.items():
        if not r["neighbors"]: continue
        for nstr in r["neighbors"].split("|"):
            try: n = int(nstr)
            except: continue
            other = by_tis.get(n)
            if not other: continue
            other_n = set(int(x) for x in (other["neighbors"] or "").split("|") if x)
            if tis not in other_n:
                out.append(fail(f"asymmetric: TIS-{tis} -> TIS-{n} but not reverse"))
    return out


def check_28_border_consistency(rows):
    out = []
    for r in rows:
        tis = int(r["tis1099_code"])
        hb = r.get("has_international_border", "")
        bc = r.get("bordering_countries", "")
        if not PAT_BOOL.match(hb):
            out.append(fail(f"TIS-{tis}: has_international_border invalid '{hb}'"))
            continue
        if hb == "true" and not bc:
            out.append(fail(f"TIS-{tis}: has_international_border=true but bordering_countries empty"))
        if hb == "false" and bc:
            out.append(fail(f"TIS-{tis}: has_international_border=false but bordering_countries='{bc}'"))
        if bc:
            for c in bc.split("|"):
                if c not in VALID_NEIGHBOR_COUNTRIES:
                    out.append(fail(f"TIS-{tis}: invalid bordering country '{c}'"))
            # Sorted check
            parts = bc.split("|")
            if parts != sorted(parts):
                out.append(fail(f"TIS-{tis}: bordering_countries not sorted: '{bc}'"))
    return out


def check_29_coastal_consistency(rows):
    out = []
    for r in rows:
        tis = int(r["tis1099_code"])
        ic = r.get("is_coastal", "")
        cl = r.get("coastline_length_km", "")
        if not PAT_BOOL.match(ic):
            out.append(fail(f"TIS-{tis}: is_coastal invalid '{ic}'"))
            continue
        try: cl_v = float(cl) if cl else 0
        except ValueError:
            out.append(fail(f"TIS-{tis}: coastline_length_km non-numeric '{cl}'"))
            continue
        if ic == "true" and cl_v <= 0:
            out.append(fail(f"TIS-{tis}: is_coastal=true but coastline_length_km={cl}"))
        if ic == "false" and cl_v > 0:
            out.append(fail(f"TIS-{tis}: is_coastal=false but coastline_length_km={cl}"))
    return out


def check_30_postal_prefixes(rows):
    out = []
    for r in rows:
        p = r.get("postal_code_prefixes", "")
        if not p:
            out.append(fail(f"TIS-{r['tis1099_code']}: postal_code_prefixes empty"))
            continue
        for prefix in p.split("|"):
            if not PAT_POSTAL_PREFIX.match(prefix):
                out.append(fail(f"TIS-{r['tis1099_code']}: malformed postal prefix '{prefix}'"))
    return out


def check_31_telephone_codes(rows):
    out = []
    for r in rows:
        p = r.get("telephone_area_codes", "")
        if not p:
            out.append(fail(f"TIS-{r['tis1099_code']}: telephone_area_codes empty"))
            continue
        for c in p.split("|"):
            if not PAT_PHONE_CODE.match(c):
                out.append(fail(f"TIS-{r['tis1099_code']}: malformed telephone code '{c}'"))
    return out


def check_32_admin_counts(rows):
    out = []
    total_amphoe = 0
    total_tambon = 0
    for r in rows:
        try:
            a = int(r["num_amphoe"])
            t = int(r["num_tambon"])
        except (KeyError, ValueError):
            out.append(fail(f"TIS-{r['tis1099_code']}: admin counts non-integer"))
            continue
        if a <= 0:
            out.append(fail(f"TIS-{r['tis1099_code']}: num_amphoe non-positive {a}"))
        if t <= 0:
            out.append(fail(f"TIS-{r['tis1099_code']}: num_tambon non-positive {t}"))
        if t < a:
            out.append(fail(f"TIS-{r['tis1099_code']}: num_tambon ({t}) < num_amphoe ({a}), implausible"))
        total_amphoe += a
        total_tambon += t
    a_lo, a_hi = THAILAND_TOTAL_AMPHOE_EXPECTED
    t_lo, t_hi = THAILAND_TOTAL_TAMBON_EXPECTED
    if not (a_lo <= total_amphoe <= a_hi):
        out.append(fail(f"sum num_amphoe = {total_amphoe}, expected {a_lo}-{a_hi}"))
    else:
        out.append(info(f"sum num_amphoe = {total_amphoe} (within expected {a_lo}-{a_hi})"))
    if not (t_lo <= total_tambon <= t_hi):
        out.append(fail(f"sum num_tambon = {total_tambon}, expected {t_lo}-{t_hi}"))
    else:
        out.append(info(f"sum num_tambon = {total_tambon} (within expected {t_lo}-{t_hi})"))
    return out


def check_33_capital_alignment_review(rows):
    """Capitals should typically equal name_en_canonical, with explicit notes-field
    explanation when they differ."""
    out = []
    for r in rows:
        c = r.get("capital", "")
        n = r.get("name_en_canonical", "")
        if c and n and c != n:
            note = r.get("notes", "")
            if "Sukhothai Thani" in note or "Bangkok" in note:
                out.append(info(f"TIS-{r['tis1099_code']}: capital differs from name (expected, documented)"))
            else:
                out.append(warn(f"TIS-{r['tis1099_code']}: capital '{c}' != name '{n}' without notes explanation"))
    return out


def check_34_cross_check_against_inputs(rows):
    """name_en_canonical must match at least one of the four MIT inputs after override resolution."""
    out = []
    src_paths = {
        "thailand-geography-data": (INPUTS / "thailand-geography-data" / "provinces.json", "provinceNameTh", "provinceNameEn"),
        "kongvut": (INPUTS / "kongvut" / "province.json", "name_th", "name_en"),
        "geothai_v1": (INPUTS / "geothai" / "provinces_v1.json", "province_name_th", "province_name_en"),
        "geothai_v2": (INPUTS / "geothai" / "provinces_v2.json", "th", "en"),
    }
    src_maps = {}
    for name, (p, th_key, en_key) in src_paths.items():
        if p.exists():
            data = load_json(p)
            src_maps[name] = {r[th_key].strip(): r[en_key].strip() for r in data}

    overrides_path = ROOT / "data" / "overrides.csv"
    overrides = set()
    if overrides_path.exists():
        with open(overrides_path, encoding="utf-8") as f:
            for orow in csv.DictReader(f):
                try:
                    overrides.add(int(orow["tis1099_code"]))
                except (KeyError, ValueError):
                    pass

    for r in rows:
        tis = int(r["tis1099_code"])
        if tis in overrides:
            continue  # override means we deliberately diverge from one or more sources
        thai = r["name_th"]
        chosen = r["name_en_canonical"]
        upstream_spellings = {src: m.get(thai) for src, m in src_maps.items()}
        unique = set(s for s in upstream_spellings.values() if s)
        if chosen not in unique:
            out.append(warn(f"TIS-{tis}: name_en_canonical '{chosen}' not in any input source (no override either)"))
    return out


def check_35_capital_against_wikidata(rows):
    """capital matches Wikidata after documented normalizations."""
    wd_caps = load_json(INPUTS / "wikidata" / "wd_capitals.json")
    out = []
    for r in rows:
        iso = r["iso3166_2"]
        if iso == "TH-10":
            continue
        wd_rec = wd_caps.get(iso, {})
        wd_cap = wd_rec.get("cap_en", "")
        if not wd_cap: continue
        wd_norm = wd_cap[len("Mueang "):] if wd_cap.startswith("Mueang ") else wd_cap
        prov = r["name_en_canonical"]
        if wd_norm.replace(" ", "").lower() == prov.replace(" ", "").lower():
            wd_norm = prov
        if r["capital"] != wd_norm:
            out.append(fail(f"TIS-{r['tis1099_code']}: capital '{r['capital']}' != Wikidata normalized '{wd_norm}' (raw '{wd_cap}')"))
    return out


def check_36_bangkok_invariants(rows):
    """Bangkok-specific checks: TIS=10, QID=Q1861, type=Special Administrative Area, distance=0, capital=Bangkok."""
    out = []
    bkk = next((r for r in rows if int(r["tis1099_code"]) == BANGKOK_TIS), None)
    if not bkk:
        return [fail("Bangkok row missing")]
    invariants = {
        "wikidata_qid": BANGKOK_QID,
        "iso_subdivision_type": "Special Administrative Area",
        "iso3166_2": "TH-10",
        "name_en_canonical": "Bangkok",
        "capital": "Bangkok",
        "distance_to_bangkok_km": "0.0",
    }
    for k, expected in invariants.items():
        if str(bkk.get(k, "")) != str(expected):
            out.append(fail(f"Bangkok {k}: expected '{expected}', got '{bkk.get(k)}'"))
    if not bkk.get("notes"):
        out.append(fail("Bangkok must have a notes-field entry explaining its administrative status"))
    return out


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
ALL_CHECKS = [
    ("01. Row count = 77", check_01_row_count),
    ("02. tis1099_code uniqueness and integer", check_02_tis_uniqueness),
    ("03. tis1099_code in range 10-96", check_03_tis_range),
    ("04. iso3166_2 format and matches tis1099_code", check_04_iso_format_and_match),
    ("05. iso3166_2 uniqueness", check_05_iso_uniqueness),
    ("06. iso_subdivision_type domain and Bangkok-special-case", check_06_iso_type),
    ("07. hasc format and uniqueness", check_07_hasc_format_and_uniqueness),
    ("08. fips_code format and uniqueness", check_08_fips_format_and_uniqueness),
    ("09. wikidata_qid format, uniqueness, and Bangkok=Q1861", check_09_wikidata_qid),
    ("10. geonames_id positive integer and uniqueness", check_10_geonames_id),
    ("11. osm_relation_id format and uniqueness (optional)", check_11_osm_relation_id),
    ("12. wikipedia_article_url format and uniqueness", check_12_wikipedia_url),
    ("13. name_en_canonical Latin-only, non-empty, unique", check_13_name_en_canonical),
    ("14. name_th pure-Thai, non-empty, unique", check_14_name_th),
    ("15. name_alternates_en pipe-separated, no self-equals", check_15_name_alternates),
    ("16. region domain and Royal Institute distribution counts", check_16_region),
    ("17. capital and capital_th non-empty; Thai script for capital_th", check_17_capital),
    ("18. established_year traces to a CONFIRMED row in established_years.csv", check_18_established_year),
    ("19. predecessor_tis1099_code references valid row, matches historical_mappings.csv, no self-ref", check_19_predecessor),
    ("20. centroid coordinates inside Thailand bounding box", check_20_centroid_coordinates),
    ("21. centroid lies inside the row's own bbox", check_21_centroid_inside_bbox),
    ("22. bbox: min < max for both lat and lon", check_22_bbox_consistency),
    ("23. area_km2 and area_rai positive; rai = km2 * 625", check_23_area_positive_and_rai),
    ("24. sum of area_km2 within ±5% of Thailand total (~513,120 km²)", check_24_total_area),
    ("25. distance_to_bangkok_km matches Haversine recomputation; Bangkok=0", check_25_distance_to_bangkok),
    ("26. all neighbors exist as TIS-1099 codes in the table; no self-ref", check_26_neighbors_membership),
    ("27. neighbors symmetry: A->B implies B->A", check_27_neighbors_symmetry),
    ("28. border consistency: has_international_border ↔ bordering_countries non-empty; sorted; valid country names", check_28_border_consistency),
    ("29. coastal consistency: is_coastal ↔ coastline_length_km > 0", check_29_coastal_consistency),
    ("30. postal_code_prefixes 2-digit format", check_30_postal_prefixes),
    ("31. telephone_area_codes 2-3 digit format", check_31_telephone_codes),
    ("32. num_amphoe > 0, num_tambon > num_amphoe; totals within published ranges", check_32_admin_counts),
    ("33. capital-vs-province-name alignment with notes-field documentation", check_33_capital_alignment_review),
    ("34. name_en_canonical cross-check against four MIT input sources (excludes overrides)", check_34_cross_check_against_inputs),
    ("35. capital matches Wikidata after documented normalizations", check_35_capital_against_wikidata),
    ("36. Bangkok-specific invariants (TIS-10, Q1861, special-area, distance=0, notes-field)", check_36_bangkok_invariants),
]


def write_report(results, total_rows):
    lines = []
    lines.append("# v0.3.0 Validation Report — Comprehensive")
    lines.append("")
    lines.append(f"Generated by `bin/validate_v0_3_0.py`. Table: `data/v0.3.0/thailand-adm-names-v0.3.0.csv` ({total_rows} rows × 36 columns).")
    lines.append("")

    total_fails = sum(sum(1 for f in findings if f[0] == "FAIL") for _, findings in results)
    total_warns = sum(sum(1 for f in findings if f[0] == "REVIEW") for _, findings in results)
    total_infos = sum(sum(1 for f in findings if f[0] == "INFO") for _, findings in results)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Checks run: **{len(results)}**")
    lines.append(f"- FAIL findings (must resolve): **{total_fails}**")
    lines.append(f"- REVIEW findings (human attention): **{total_warns}**")
    lines.append(f"- INFO findings (informational): **{total_infos}**")
    lines.append("")
    lines.append("## Per-check status")
    lines.append("")
    lines.append("| Check | Status | FAIL | REVIEW | INFO |")
    lines.append("|---|---|---|---|---|")
    for name, findings in results:
        f = sum(1 for x in findings if x[0] == "FAIL")
        w = sum(1 for x in findings if x[0] == "REVIEW")
        i = sum(1 for x in findings if x[0] == "INFO")
        status = "PASS" if not findings else ("FAIL" if f else ("REVIEW" if w else "INFO"))
        lines.append(f"| {name} | {status} | {f} | {w} | {i} |")
    lines.append("")
    lines.append("## Detailed findings")
    lines.append("")
    for name, findings in results:
        lines.append(f"### {name}")
        lines.append("")
        if not findings:
            lines.append("PASS")
        else:
            for sev, msg in findings:
                lines.append(f"- **{sev}** — {msg}")
        lines.append("")
    REPORT.write_text("\n".join(lines))


def main():
    rows = load_table()
    print(f"Loaded {len(rows)} rows from {TABLE.name}")
    print(f"Running {len(ALL_CHECKS)} checks...\n")

    results = []
    width = max(len(name) for name, _ in ALL_CHECKS)
    for name, fn in ALL_CHECKS:
        try:
            findings = fn(rows)
        except Exception as e:
            findings = [fail(f"check raised exception: {type(e).__name__}: {e}")]
        results.append((name, findings))
        f = sum(1 for x in findings if x[0] == "FAIL")
        w = sum(1 for x in findings if x[0] == "REVIEW")
        i = sum(1 for x in findings if x[0] == "INFO")
        if f:
            status = f"\033[31mFAIL ({f})\033[0m"
        elif w:
            status = f"\033[33m{w} REVIEW\033[0m"
        elif i:
            status = f"INFO ({i})"
        else:
            status = "\033[32mPASS\033[0m"
        print(f"  {name:<{width}}  {status}")

    write_report(results, len(rows))

    total_fails = sum(sum(1 for f in findings if f[0] == "FAIL") for _, findings in results)
    print(f"\n{'='*60}")
    print(f"Total FAIL findings: {total_fails}")
    print(f"Report written to {REPORT}")
    return 1 if total_fails > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
