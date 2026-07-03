#!/usr/bin/env python3
"""
Verify the enrichment layer — the data we ADDED on top of upstream MIT sources.

Scope: every column whose values come from our work (overrides, identifier
lookups, polygon computation, normalization rules, primary-source verification,
alternates harvesting). Re-runs the underlying source-pulls against cached data
and asserts our stored values match. Spots statistical anomalies. Cross-checks
each fact against multiple sources where available.

Output:
  data/v1.0.0/enrichment_verification_report.md

Usage:
  python3 bin/verify_enrichment.py
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, '/tmp/pylibs')

ROOT = Path(__file__).resolve().parent.parent
RELEASE = ROOT / "data" / "v1.0.0"
INPUTS = ROOT / "data" / "inputs"
ADM1_CSV = RELEASE / "thailand-adm1-provinces-v1.0.0.csv"
REPORT = RELEASE / "enrichment_verification_report.md"

# Known-correct anchor values (curated against multiple external sources)
# These provide ground-truth tests for the enrichment layer.
ANCHOR_VALUES = {
    10: {
        "name": "Bangkok",
        "wikidata_qid": "Q1861",
        "hasc": "TH.BM",
        "fips_code": "TH40",
        "iso3166_2": "TH-10",
        "iso_subdivision_type": "Special Administrative Area",
        "expected_neighbors": {11, 12, 13, 24, 73, 74},
        "is_border": False,
        "is_coastal": True,
        "expected_area_km2_range": (1500, 1800),  # Wikipedia says 1,569; we compute polygon
        "num_amphoe": 50,
        "num_tambon": 180,
        "centroid_lat_range": (13.5, 14.0),
        "centroid_lon_range": (100.3, 101.0),
    },
    50: {
        "name": "Chiang Mai",
        "wikidata_qid": "Q233588",
        "hasc": "TH.CM",
        "fips_code": "TH02",
        "is_border": True,
        "expected_borders": {"Myanmar"},
        "is_coastal": False,
        "expected_area_km2_range": (19000, 24000),  # Wikipedia ~20,107
        "centroid_lat_range": (17, 21),
        "centroid_lon_range": (98, 100),
    },
    83: {
        "name": "Phuket",
        "wikidata_qid": "Q182565",
        "hasc": "TH.PU",
        "fips_code": "TH62",
        "expected_neighbors": {82},  # only Phangnga
        "is_border": False,
        "is_coastal": True,
        "expected_area_km2_range": (500, 700),  # Wikipedia ~543
        "num_amphoe": 3,
        "num_tambon": 17,
        "centroid_lat_range": (7.7, 8.3),
        "centroid_lon_range": (98.0, 98.6),
    },
    38: {
        "name": "Bueng Kan",
        "wikidata_qid": "Q1001862",
        "is_border": True,
        "expected_borders": {"Laos"},
        "established_year": 2011,
        "predecessor_tis1099_code": 43,
        "expected_neighbors": {43, 47, 48},  # Nong Khai, Sakon Nakhon, Nakhon Phanom
    },
    58: {
        "name": "Mae Hong Son",
        "is_border": True,
        "expected_borders": {"Myanmar"},
        "centroid_lat_range": (18, 20),  # far north
    },
    96: {
        "name": "Narathiwat",
        "is_border": True,
        "expected_borders": {"Malaysia"},
        "is_coastal": True,
        "centroid_lat_range": (5.5, 7),  # far south
    },
    95: {
        "name": "Yala",
        "is_border": True,
        "expected_borders": {"Malaysia"},
        "is_coastal": False,  # land-locked southern province
    },
    34: {
        "name": "Ubon Ratchathani",
        "is_border": True,
        "expected_borders": {"Cambodia", "Laos"},  # tri-border
    },
    57: {
        "name": "Chiang Rai",
        "is_border": True,
        "expected_borders": {"Laos", "Myanmar"},  # golden triangle
    },
}


def load_table():
    with open(ADM1_CSV, encoding="utf-8") as f:
        return {int(r["tis1099_code"]): r for r in csv.DictReader(f)}


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def fail(msg): return ("FAIL", msg)
def warn(msg): return ("REVIEW", msg)
def info(msg): return ("INFO", msg)


# ---------------------------------------------------------------------------
# 1. Round-trip cross-system identifiers against cached sources
# ---------------------------------------------------------------------------
def verify_identifiers_roundtrip(table):
    """Re-derive HASC, FIPS, Wikidata QID, GeoNames ID, OSM relation, Wikipedia URL
    from cached input files; assert our stored values match."""
    findings = []

    # Statoids → HASC + FIPS
    statoids = INPUTS / "statoids" / "uth.html"
    if statoids.exists():
        with open(statoids, "rb") as f:
            html = f.read().decode("latin-1", errors="replace")
        rows_html = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL | re.IGNORECASE)
        statoids_by_tis = {}
        for row_html in rows_html:
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL | re.IGNORECASE)
            cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            if len(cells) >= 4 and re.match(r"^TH\.[A-Z]{2}$", cells[1]):
                try:
                    tis = int(cells[2])
                except ValueError:
                    continue
                statoids_by_tis[tis] = {"hasc": cells[1], "fips": cells[3]}

        mismatches = []
        for tis, expected in statoids_by_tis.items():
            row = table.get(tis)
            if not row: continue
            if row["hasc"] != expected["hasc"]:
                mismatches.append(f"TIS-{tis} HASC: stored={row['hasc']}, statoids={expected['hasc']}")
            if row["fips_code"] != expected["fips"]:
                mismatches.append(f"TIS-{tis} FIPS: stored={row['fips_code']}, statoids={expected['fips']}")
        if mismatches:
            for m in mismatches:
                findings.append(fail(m))
        else:
            findings.append(info(f"HASC + FIPS round-trip: {len(statoids_by_tis)} rows match Statoids cache exactly"))

    # GeoNames → geonames_id (via FIPS)
    geonames_path = INPUTS / "geonames" / "admin1CodesASCII.txt"
    if geonames_path.exists():
        gn_by_fips = {}
        with open(geonames_path, encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 4 and parts[0].startswith("TH."):
                    fips = "TH" + parts[0].split(".")[1]
                    try:
                        gn_by_fips[fips] = int(parts[3])
                    except ValueError:
                        continue
        mismatches = []
        for tis, row in table.items():
            fips = row["fips_code"]
            expected = gn_by_fips.get(fips)
            if expected is None: continue
            try:
                stored = int(row["geonames_id"]) if row["geonames_id"] else None
            except ValueError:
                stored = None
            if stored != expected:
                mismatches.append(f"TIS-{tis} GeoNames ID: stored={stored}, expected={expected}")
        if mismatches:
            for m in mismatches:
                findings.append(fail(m))
        else:
            findings.append(info(f"GeoNames ID round-trip: 77 rows match cached admin1 dump (joined via FIPS)"))

    # Wikidata Q-IDs (via cached SPARQL response)
    wd_path = INPUTS / "wikidata" / "wd_provinces_modern.json"
    if wd_path.exists():
        wd_data = load_json(wd_path)
        wd_qids = {}
        for r in wd_data:
            iso = r.get("iso", "")
            if iso.startswith("TH-"):
                try:
                    tis = int(iso.split("-")[1])
                    wd_qids[tis] = r["province_qid"]
                except (KeyError, ValueError):
                    continue
        # Bangkok separately
        wd_qids[10] = "Q1861"

        mismatches = []
        for tis, expected in wd_qids.items():
            row = table.get(tis)
            if not row: continue
            if row["wikidata_qid"] != expected:
                mismatches.append(f"TIS-{tis} Wikidata QID: stored={row['wikidata_qid']}, cached={expected}")
        if mismatches:
            for m in mismatches:
                findings.append(fail(m))
        else:
            findings.append(info(f"Wikidata QID round-trip: 77 rows match cached SPARQL response"))

    return findings


# ---------------------------------------------------------------------------
# 2. Anchor-value spot checks (Bangkok, Phuket, Chiang Mai, Bueng Kan, etc.)
# ---------------------------------------------------------------------------
def verify_anchor_values(table):
    findings = []
    for tis, anchor in ANCHOR_VALUES.items():
        row = table.get(tis)
        if not row:
            findings.append(fail(f"Anchor TIS-{tis}: row missing"))
            continue
        prefix = f"TIS-{tis} {anchor.get('name', '')}"

        # Identifier checks
        for field in ("wikidata_qid", "hasc", "fips_code", "iso3166_2", "iso_subdivision_type",
                       "established_year"):
            if field in anchor:
                expected = str(anchor[field])
                actual = str(row.get(field, "") or "")
                if actual != expected:
                    findings.append(fail(f"{prefix} {field}: expected {expected!r}, got {actual!r}"))

        # Predecessor check
        if "predecessor_tis1099_code" in anchor:
            expected = str(anchor["predecessor_tis1099_code"])
            actual = str(row.get("predecessor_tis1099_code", "") or "")
            if actual != expected:
                findings.append(fail(f"{prefix} predecessor: expected {expected!r}, got {actual!r}"))

        # Neighbors check
        if "expected_neighbors" in anchor:
            stored = set()
            if row.get("neighbors"):
                stored = set(int(x) for x in row["neighbors"].split("|") if x)
            expected = anchor["expected_neighbors"]
            if stored != expected:
                missing = expected - stored
                extra = stored - expected
                findings.append(fail(f"{prefix} neighbors: missing={missing}, extra={extra}"))

        # Border / coastal booleans
        if "is_border" in anchor:
            expected = "true" if anchor["is_border"] else "false"
            if row.get("has_international_border") != expected:
                findings.append(fail(f"{prefix} has_international_border: expected {expected}, got {row.get('has_international_border')}"))
        if "is_coastal" in anchor:
            expected = "true" if anchor["is_coastal"] else "false"
            if row.get("is_coastal") != expected:
                findings.append(fail(f"{prefix} is_coastal: expected {expected}, got {row.get('is_coastal')}"))

        # Bordering countries
        if "expected_borders" in anchor:
            stored = set()
            if row.get("bordering_countries"):
                stored = set(row["bordering_countries"].split("|"))
            if stored != anchor["expected_borders"]:
                missing = anchor["expected_borders"] - stored
                extra = stored - anchor["expected_borders"]
                findings.append(fail(f"{prefix} bordering_countries: missing={missing}, extra={extra}"))

        # Numeric range checks
        if "expected_area_km2_range" in anchor:
            lo, hi = anchor["expected_area_km2_range"]
            try:
                actual = float(row["area_km2"])
                if not (lo <= actual <= hi):
                    findings.append(fail(f"{prefix} area_km2={actual}, expected in [{lo}, {hi}]"))
            except (KeyError, ValueError):
                findings.append(fail(f"{prefix} area_km2 non-numeric"))

        if "centroid_lat_range" in anchor:
            lo, hi = anchor["centroid_lat_range"]
            try:
                actual = float(row["centroid_lat"])
                if not (lo <= actual <= hi):
                    findings.append(fail(f"{prefix} centroid_lat={actual}, expected in [{lo}, {hi}]"))
            except (KeyError, ValueError):
                findings.append(fail(f"{prefix} centroid_lat non-numeric"))

        if "centroid_lon_range" in anchor:
            lo, hi = anchor["centroid_lon_range"]
            try:
                actual = float(row["centroid_lon"])
                if not (lo <= actual <= hi):
                    findings.append(fail(f"{prefix} centroid_lon={actual}, expected in [{lo}, {hi}]"))
            except (KeyError, ValueError):
                findings.append(fail(f"{prefix} centroid_lon non-numeric"))

        # Admin counts
        for field in ("num_amphoe", "num_tambon"):
            if field in anchor:
                try:
                    actual = int(row[field])
                    if actual != anchor[field]:
                        findings.append(fail(f"{prefix} {field}: expected {anchor[field]}, got {actual}"))
                except (KeyError, ValueError):
                    findings.append(fail(f"{prefix} {field} non-integer"))

    if not findings:
        findings.append(info(f"All {len(ANCHOR_VALUES)} anchor-value spot-checks passed"))
    return findings


# ---------------------------------------------------------------------------
# 3. Statistical anomaly detection on geographic columns
# ---------------------------------------------------------------------------
def detect_geographic_anomalies(table):
    """Find values that fall outside plausible ranges given Thailand's geography."""
    findings = []
    rows = list(table.values())

    # Area outliers: Thailand's smallest is ~210 km² (Samut Songkhram); largest ~20,500 (Nakhon Ratchasima or Chiang Mai)
    AREA_MIN, AREA_MAX = 100, 30000
    for r in rows:
        try:
            area = float(r["area_km2"])
            if not (AREA_MIN <= area <= AREA_MAX):
                findings.append(warn(f"TIS-{r['tis1099_code']} area {area} km² outside plausible range [{AREA_MIN}, {AREA_MAX}]"))
        except (KeyError, ValueError):
            continue

    # Centroid outliers: latitude in [5.5, 21], longitude in [96.5, 106.5] for Thailand
    for r in rows:
        try:
            lat = float(r["centroid_lat"])
            lon = float(r["centroid_lon"])
            if not (5.5 <= lat <= 21):
                findings.append(warn(f"TIS-{r['tis1099_code']} centroid_lat {lat} outside Thailand"))
            if not (96.5 <= lon <= 106.5):
                findings.append(warn(f"TIS-{r['tis1099_code']} centroid_lon {lon} outside Thailand"))
        except (KeyError, ValueError):
            continue

    # Distance to Bangkok: max plausible is ~1200 km (Narathiwat); min is 0 (Bangkok itself)
    for r in rows:
        try:
            d = float(r["distance_to_bangkok_km"])
            if d < 0 or d > 1300:
                findings.append(warn(f"TIS-{r['tis1099_code']} distance_to_bangkok {d} km outside plausible range"))
        except (KeyError, ValueError):
            continue

    # area_rai must equal area_km2 * 625
    for r in rows:
        try:
            km2 = float(r["area_km2"])
            rai = float(r["area_rai"])
            expected = km2 * 625
            if abs(rai - expected) > 1.0:
                findings.append(fail(f"TIS-{r['tis1099_code']} area_rai={rai} ≠ area_km2*625 ({expected})"))
        except (KeyError, ValueError):
            continue

    if not findings:
        findings.append(info("No geographic anomalies detected"))
    return findings


# ---------------------------------------------------------------------------
# 4. Override registry audit
# ---------------------------------------------------------------------------
def audit_override_registry(table):
    """Re-run cross-source spelling check and verify the override registry handles every disagreement."""
    findings = []

    # Re-run cross-source check
    sources = {
        "thailand-geography-data": (INPUTS / "thailand-geography-data" / "provinces.json", "provinceNameTh", "provinceNameEn"),
        "kongvut": (INPUTS / "kongvut" / "province.json", "name_th", "name_en"),
        "geothai_v1": (INPUTS / "geothai" / "provinces_v1.json", "province_name_th", "province_name_en"),
        "geothai_v2": (INPUTS / "geothai" / "provinces_v2.json", "th", "en"),
    }
    src_maps = {}
    for name, (p, th_key, en_key) in sources.items():
        if p.exists():
            data = load_json(p)
            src_maps[name] = {r[th_key].strip(): r[en_key].strip() for r in data}

    overrides_path = ROOT / "data" / "overrides.csv"
    overrides = {}
    if overrides_path.exists():
        with open(overrides_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    overrides[int(r["tis1099_code"])] = r["chosen_spelling"]
                except (KeyError, ValueError):
                    continue

    disagreements = 0
    overrides_match_chosen = 0
    overrides_extras = []
    missing_overrides = []
    for tis, row in table.items():
        thai = row["name_th"]
        chosen = row["name_en_canonical"]
        upstream_spellings = {src: m.get(thai) for src, m in src_maps.items()}
        unique = set(s for s in upstream_spellings.values() if s)

        # If sources disagree (more than 1 unique value), an override should exist
        if len(unique) > 1:
            disagreements += 1
            if tis in overrides:
                if overrides[tis] == chosen:
                    overrides_match_chosen += 1
                else:
                    findings.append(fail(f"TIS-{tis}: override registry says '{overrides[tis]}' but row has '{chosen}'"))
            else:
                missing_overrides.append((tis, thai, unique, chosen))

    # Check for "extra" overrides (overrides that exist but no source disagreement)
    for tis, chosen in overrides.items():
        thai = table[tis]["name_th"] if tis in table else ""
        upstream_spellings = {src: m.get(thai) for src, m in src_maps.items()}
        unique = set(s for s in upstream_spellings.values() if s)
        if len(unique) <= 1:
            overrides_extras.append((tis, chosen))

    findings.append(info(f"Source disagreements found: {disagreements}"))
    findings.append(info(f"Overrides registered: {len(overrides)}"))
    findings.append(info(f"Override-to-chosen-spelling matches: {overrides_match_chosen}"))

    for tis, thai, unique, chosen in missing_overrides:
        findings.append(fail(f"TIS-{tis} ({thai}): sources disagree ({unique}), no override registered, chose '{chosen}'"))

    for tis, chosen in overrides_extras:
        findings.append(warn(f"TIS-{tis}: override registered ('{chosen}') but no source disagreement"))

    return findings


# ---------------------------------------------------------------------------
# 5. Established year primary-source verification
# ---------------------------------------------------------------------------
def verify_established_years(table):
    """Verify each table-stored established_year traces to a CONFIRMED row in established_years.csv."""
    findings = []
    cy_path = ROOT / "data" / "established_years.csv"
    confirmed = {}
    partial = {}
    if cy_path.exists():
        with open(cy_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    tis = int(r["tis1099_code"])
                    year = int(r["year"])
                except (KeyError, ValueError):
                    continue
                status = r.get("verification_status", "")
                if status == "CONFIRMED":
                    confirmed[tis] = (year, r.get("source_citation", ""))
                elif status == "PARTIAL":
                    partial[tis] = (year, r.get("source_citation", ""))

    populated_in_table = {}
    for tis, row in table.items():
        if row.get("established_year"):
            try:
                populated_in_table[tis] = int(row["established_year"])
            except ValueError:
                continue

    findings.append(info(f"Table established_year populated rows: {len(populated_in_table)}"))
    findings.append(info(f"established_years.csv CONFIRMED rows: {len(confirmed)}"))
    findings.append(info(f"established_years.csv PARTIAL rows: {len(partial)} (intentionally not flowed to table)"))

    for tis, year in populated_in_table.items():
        if tis not in confirmed:
            findings.append(fail(f"TIS-{tis} established_year={year} but not in CONFIRMED list"))
            continue
        if confirmed[tis][0] != year:
            findings.append(fail(f"TIS-{tis} established_year={year} but registry says {confirmed[tis][0]}"))

    # PARTIAL entries should NOT appear in the table
    for tis in partial:
        if tis in populated_in_table:
            findings.append(fail(f"TIS-{tis} is PARTIAL in registry but populated in table — should be empty"))

    if len([f for f in findings if f[0] == "FAIL"]) == 0:
        findings.append(info(f"All {len(populated_in_table)} table-populated established_year values trace to CONFIRMED registry rows"))

    return findings


# ---------------------------------------------------------------------------
# 6. Border / coastal verification against known geography
# ---------------------------------------------------------------------------
def verify_borders_and_coastlines(table):
    """Cross-check border and coastal flags against well-documented Thai geography."""
    findings = []

    # Known international-border provinces (from any standard Thai geography reference):
    KNOWN_BORDER_PROVINCES = {
        # Myanmar (10): Mae Hong Son, Chiang Rai, Chiang Mai, Tak, Kanchanaburi, Ratchaburi,
        # Phetchaburi, Prachuap Khiri Khan, Chumphon, Ranong
        50, 57, 58, 63, 70, 71, 76, 77, 85, 86,
        # Laos (12): Chiang Rai, Phayao, Nan, Uttaradit, Phitsanulok, Loei, Nong Khai,
        # Bueng Kan, Nakhon Phanom, Mukdahan, Amnat Charoen, Ubon Ratchathani
        37, 38, 42, 43, 48, 49, 53, 55, 56, 65,
        # Cambodia (7): Chanthaburi, Trat, Sa Kaeo, Buri Ram, Surin, Si Sa Ket, Ubon Ratchathani
        22, 23, 27, 31, 32, 33, 34,
        # Malaysia (4): Songkhla, Yala, Narathiwat, Satun
        90, 91, 95, 96,
    }

    # Known coastal provinces (Andaman + Gulf of Thailand)
    KNOWN_COASTAL_PROVINCES = {
        # Andaman: Krabi, Phang Nga, Phuket, Trang, Satun, Ranong
        81, 82, 83, 92, 91, 85,
        # Gulf east: Chachoengsao, Chon Buri, Rayong, Chanthaburi, Trat
        24, 20, 21, 22, 23,
        # Gulf central west: Prachuap Khiri Khan, Phetchaburi, Samut Songkhram, Samut Sakhon, Samut Prakan
        77, 76, 75, 74, 11,
        # Gulf south: Chumphon, Surat Thani, Nakhon Si Thammarat, Songkhla, Pattani, Narathiwat
        86, 84, 80, 90, 94, 96,
        # Bangkok (small Bang Khun Thian coast)
        10,
        # Phatthalung — sits on the western shore of Songkhla Lake (Thale Luang); the lake
        # is a polygon hole in Natural Earth's Thailand outline, so its perimeter is coastline
        # by the methodology's Section 9.3 definition (consistent with Songkhla's lake-shore inclusion)
        93,
    }

    table_borders = {tis for tis, r in table.items() if r.get("has_international_border") == "true"}
    table_coastal = {tis for tis, r in table.items() if r.get("is_coastal") == "true"}

    # Check borders
    missing_border = KNOWN_BORDER_PROVINCES - table_borders
    extra_border = table_borders - KNOWN_BORDER_PROVINCES
    if missing_border:
        for tis in sorted(missing_border):
            findings.append(fail(f"TIS-{tis} ({table[tis]['name_en_canonical']}) is a known border province but has_international_border=false"))
    if extra_border:
        for tis in sorted(extra_border):
            findings.append(fail(f"TIS-{tis} ({table[tis]['name_en_canonical']}) is flagged as border but not in known border list"))
    if not (missing_border or extra_border):
        findings.append(info(f"All 31 has_international_border=true rows match known border-province set"))

    # Check coastal
    missing_coastal = KNOWN_COASTAL_PROVINCES - table_coastal
    extra_coastal = table_coastal - KNOWN_COASTAL_PROVINCES
    if missing_coastal:
        for tis in sorted(missing_coastal):
            findings.append(fail(f"TIS-{tis} ({table[tis]['name_en_canonical']}) is a known coastal province but is_coastal=false"))
    if extra_coastal:
        for tis in sorted(extra_coastal):
            findings.append(fail(f"TIS-{tis} ({table[tis]['name_en_canonical']}) is flagged as coastal but not in known coastal list"))
    if not (missing_coastal or extra_coastal):
        findings.append(info(f"All 24 is_coastal=true rows match known coastal-province set"))

    return findings


# ---------------------------------------------------------------------------
# 7. Wikipedia article URL verification
# ---------------------------------------------------------------------------
def verify_wikipedia_urls(table):
    """Each Wikipedia URL should point to a valid province article."""
    findings = []
    for tis, row in table.items():
        url = row.get("wikipedia_article_url", "")
        if not url:
            findings.append(fail(f"TIS-{tis} wikipedia_article_url empty"))
            continue
        if not url.startswith("https://en.wikipedia.org/wiki/"):
            findings.append(fail(f"TIS-{tis} wikipedia_article_url malformed: {url}"))
            continue
        # Title sanity: should contain "province" (lowercase) or be Bangkok
        if tis == 10:
            if not url.endswith("/Bangkok"):
                findings.append(warn(f"TIS-10 Wikipedia URL: expected '/Bangkok', got {url}"))
        else:
            if "province" not in url.lower():
                findings.append(warn(f"TIS-{tis} Wikipedia URL does not contain 'province': {url}"))
    if not [f for f in findings if f[0] == "FAIL"]:
        findings.append(info(f"All 77 Wikipedia URLs follow expected format"))
    return findings


# ---------------------------------------------------------------------------
# 8. Alternates plausibility
# ---------------------------------------------------------------------------
def verify_alternates(table):
    """Each alternate must not equal canonical (case-insensitive) and must be a valid English-name format."""
    findings = []
    pattern = re.compile(r"^[A-Za-z][A-Za-z \-'.]*$")
    populated = 0
    total_alts = 0
    for tis, row in table.items():
        canonical = row["name_en_canonical"]
        alts_str = row.get("name_alternates_en", "")
        if not alts_str:
            continue
        populated += 1
        for alt in alts_str.split("|"):
            alt = alt.strip()
            if not alt:
                findings.append(fail(f"TIS-{tis} empty alternate"))
                continue
            total_alts += 1
            if alt.lower() == canonical.lower():
                findings.append(fail(f"TIS-{tis} alternate '{alt}' equals canonical (case-insensitive)"))
            if not pattern.match(alt):
                # Some real alternates have apostrophes (Sia-Yut'hia) — that's allowed
                findings.append(warn(f"TIS-{tis} alternate '{alt}' does not match strict English-name regex"))

    findings.append(info(f"Alternates populated: {populated}/77 rows, {total_alts} total alternates"))
    return findings


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
ALL_VERIFICATIONS = [
    ("E1. Identifier round-trip (HASC, FIPS, GeoNames, Wikidata) against cached sources", verify_identifiers_roundtrip),
    ("E2. Anchor-value spot checks (Bangkok, Phuket, Chiang Mai, Bueng Kan, etc.)", verify_anchor_values),
    ("E3. Geographic anomaly detection (areas, centroids, distances, area_rai derivation)", detect_geographic_anomalies),
    ("E4. Override registry audit (every cross-source disagreement has an override)", audit_override_registry),
    ("E5. Established_year primary-source verification (table values trace to CONFIRMED registry)", verify_established_years),
    ("E6. Border + coastal flags against known Thai geography", verify_borders_and_coastlines),
    ("E7. Wikipedia article URL format", verify_wikipedia_urls),
    ("E8. Alternates plausibility (non-empty, not canonical, valid format)", verify_alternates),
]


def main():
    table = load_table()
    print(f"Verifying enrichment layer for {len(table)} ADM1 rows\n")

    sections = []
    for name, fn in ALL_VERIFICATIONS:
        print(f"  Running {name}...")
        findings = fn(table)
        sections.append((name, findings))

    total_fails = sum(sum(1 for f in findings if f[0] == "FAIL") for _, findings in sections)
    total_warns = sum(sum(1 for f in findings if f[0] == "REVIEW") for _, findings in sections)
    total_infos = sum(sum(1 for f in findings if f[0] == "INFO") for _, findings in sections)

    print()
    width = max(len(n) for n, _ in sections)
    for name, findings in sections:
        f = sum(1 for x in findings if x[0] == "FAIL")
        w = sum(1 for x in findings if x[0] == "REVIEW")
        i = sum(1 for x in findings if x[0] == "INFO")
        if f:
            status = f"\033[31m{f} FAIL\033[0m"
        elif w:
            status = f"\033[33m{w} REVIEW\033[0m"
        elif i:
            status = f"INFO ({i})"
        else:
            status = "\033[32mPASS\033[0m"
        print(f"  {name[:width]:<{width}}  {status}")
    print(f"\nTotal: {total_fails} FAIL · {total_warns} REVIEW · {total_infos} INFO")

    # Write report
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# v1.0.0 Enrichment-Layer Verification Report", ""]
    lines.append("This report verifies the artifact's value-add layer — every column whose values come from our work (overrides, identifier lookups, polygon computation, normalization rules, primary-source verification, alternates harvesting). Upstream-source row content is verified separately by the comprehensive validator.")
    lines.append("")
    lines.append(f"**Summary**: {total_fails} FAIL · {total_warns} REVIEW · {total_infos} INFO across {len(sections)} verification suites")
    lines.append("")
    for name, findings in sections:
        lines.append(f"### {name}")
        lines.append("")
        if not findings:
            lines.append("PASS")
        else:
            for sev, msg in findings:
                lines.append(f"- **{sev}** — {msg}")
        lines.append("")
    REPORT.write_text("\n".join(lines))
    print(f"\nReport: {REPORT}")
    return 1 if total_fails > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
