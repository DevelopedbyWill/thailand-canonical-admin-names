#!/usr/bin/env python3
"""
Full v1.0 validator — covers all three administrative levels plus cross-level integrity.

Reuses the v0.3.0 ADM1 checks. Adds ADM2 and ADM3 schema/format checks. Adds
cross-level foreign-key checks. Adds statistical sanity at the multi-level scale.

Outputs:
  data/v1.0.0/validation_report.md (consolidated)

Usage:
  python3 bin/validate_v1_0_0_full.py
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = ROOT / "data" / "v1.0.0"
REPORT = RELEASE / "validation_report.md"

ADM1_CSV = RELEASE / "thailand-adm1-provinces-v1.0.0.csv"
ADM2_CSV = RELEASE / "thailand-adm2-districts-v1.0.0.csv"
ADM3_CSV = RELEASE / "thailand-adm3-subdistricts-v1.0.0.csv"

THAILAND_BBOX = (5.5, 21.0, 96.5, 106.5)
THAILAND_TOTAL_AREA_KM2 = 513120
PAT_THAI = re.compile(r"^[฀-๿\s\-]+$")  # allow Latin hyphens (Sungai Kolok = สุไหงโก-ลก)
PAT_EN_NAME = re.compile(r"^[A-Za-z][A-Za-z \-'.]*$")


def fail(msg): return ("FAIL", msg)
def warn(msg): return ("REVIEW", msg)
def info(msg): return ("INFO", msg)


def load(p):
    with open(p) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# ADM1 checks (delegate to existing v0.3.0 validator)
# ---------------------------------------------------------------------------
def run_adm1_checks(rows):
    """Return list of (check_name, findings)."""
    sys.path.insert(0, str(ROOT / "bin"))
    # The existing validator hard-codes its TABLE path; rebind it
    import importlib.util
    spec = importlib.util.spec_from_file_location("v3_validator", ROOT / "bin" / "validate_v0_3_0.py")
    v3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v3)
    out = []
    for name, fn in v3.ALL_CHECKS:
        try:
            out.append((f"ADM1: {name}", fn(rows)))
        except Exception as e:
            out.append((f"ADM1: {name}", [fail(f"check raised exception: {e}")]))
    return out


# ---------------------------------------------------------------------------
# ADM2 checks
# ---------------------------------------------------------------------------
def adm2_row_count(rows):
    return [] if len(rows) == 928 else [fail(f"ADM2 row count: expected 928, got {len(rows)}")]


def adm2_primary_key(rows):
    out, seen = [], set()
    for r in rows:
        try:
            code = int(r["tis1099_district_code"])
        except (KeyError, ValueError):
            out.append(fail(f"ADM2: non-integer tis1099_district_code"))
            continue
        if code in seen:
            out.append(fail(f"ADM2: duplicate tis1099_district_code {code}"))
        seen.add(code)
        # Range check: 4-digit codes from 1001 to 9601 (province * 100 + district)
        if not (1001 <= code <= 9999):
            out.append(fail(f"ADM2: tis1099_district_code out of range: {code}"))
    return out


def adm2_parent_fk_consistency(rows):
    """parent_province_tis1099_code = first 2 digits of tis1099_district_code."""
    out = []
    for r in rows:
        try:
            code = int(r["tis1099_district_code"])
            parent = int(r["parent_province_tis1099_code"])
        except (KeyError, ValueError):
            continue
        expected_parent = code // 100
        if parent != expected_parent:
            out.append(fail(f"ADM2: TIS-{code} parent_province={parent} but expected {expected_parent}"))
    return out


def adm2_names_populated(rows):
    out = []
    for r in rows:
        if not r.get("name_en"):
            out.append(fail(f"ADM2: TIS-{r['tis1099_district_code']} name_en empty"))
        if not r.get("name_th"):
            out.append(fail(f"ADM2: TIS-{r['tis1099_district_code']} name_th empty"))
        if r.get("name_th") and not PAT_THAI.match(r["name_th"]):
            out.append(fail(f"ADM2: TIS-{r['tis1099_district_code']} name_th not pure Thai: {r['name_th']!r}"))
    return out


def adm2_geometry_consistency(rows):
    """Centroids inside Thailand bbox; bbox min<max; area positive."""
    out = []
    lat_min, lat_max, lon_min, lon_max = THAILAND_BBOX
    geo_present = 0
    for r in rows:
        if not r.get("centroid_lat"):
            continue
        geo_present += 1
        try:
            lat = float(r["centroid_lat"])
            lon = float(r["centroid_lon"])
            mn_lat, mx_lat = float(r["bbox_minlat"]), float(r["bbox_maxlat"])
            mn_lon, mx_lon = float(r["bbox_minlon"]), float(r["bbox_maxlon"])
            area = float(r["area_km2"])
        except (KeyError, ValueError):
            out.append(fail(f"ADM2: TIS-{r['tis1099_district_code']} geo non-numeric"))
            continue
        if not (lat_min < lat < lat_max and lon_min < lon < lon_max):
            out.append(fail(f"ADM2: TIS-{r['tis1099_district_code']} centroid outside bbox: ({lat},{lon})"))
        if mn_lat >= mx_lat or mn_lon >= mx_lon:
            out.append(fail(f"ADM2: TIS-{r['tis1099_district_code']} bbox inverted"))
        if area <= 0:
            out.append(fail(f"ADM2: TIS-{r['tis1099_district_code']} area non-positive {area}"))
    out.append(info(f"ADM2 geometry coverage: {geo_present}/{len(rows)} rows with polygon geometry"))
    return out


def adm2_admin_counts(rows):
    """num_tambon should be positive."""
    out = []
    total = 0
    for r in rows:
        try:
            n = int(r.get("num_tambon", 0) or 0)
        except ValueError:
            out.append(fail(f"ADM2: TIS-{r['tis1099_district_code']} num_tambon non-integer"))
            continue
        if n <= 0:
            out.append(warn(f"ADM2: TIS-{r['tis1099_district_code']} num_tambon = {n} (no subdistricts?)"))
        total += n
    out.append(info(f"ADM2 sum of num_tambon = {total}"))
    return out


# ---------------------------------------------------------------------------
# ADM3 checks
# ---------------------------------------------------------------------------
def adm3_row_count(rows):
    return [] if len(rows) == 7436 else [fail(f"ADM3 row count: expected 7436, got {len(rows)}")]


def adm3_primary_key(rows):
    out, seen = [], set()
    for r in rows:
        try:
            code = int(r["tis1099_subdistrict_code"])
        except (KeyError, ValueError):
            out.append(fail("ADM3: non-integer tis1099_subdistrict_code"))
            continue
        if code in seen:
            out.append(fail(f"ADM3: duplicate tis1099_subdistrict_code {code}"))
        seen.add(code)
        if not (100101 <= code <= 999999):
            out.append(fail(f"ADM3: code out of range: {code}"))
    return out


def adm3_parent_fk_consistency(rows):
    """parent_district = code // 100; parent_province = code // 10000."""
    out = []
    for r in rows:
        try:
            code = int(r["tis1099_subdistrict_code"])
            parent_d = int(r["parent_district_tis1099_code"])
            parent_p = int(r["parent_province_tis1099_code"])
        except (KeyError, ValueError):
            continue
        expected_d = code // 100
        expected_p = code // 10000
        if parent_d != expected_d:
            out.append(fail(f"ADM3: TIS-{code} parent_district={parent_d} expected {expected_d}"))
        if parent_p != expected_p:
            out.append(fail(f"ADM3: TIS-{code} parent_province={parent_p} expected {expected_p}"))
    return out


def adm3_names_populated(rows):
    out = []
    for r in rows:
        if not r.get("name_en"):
            out.append(fail(f"ADM3: TIS-{r['tis1099_subdistrict_code']} name_en empty"))
        if not r.get("name_th"):
            out.append(fail(f"ADM3: TIS-{r['tis1099_subdistrict_code']} name_th empty"))
    return out


def adm3_postal_code(rows):
    out = []
    for r in rows:
        pc = r.get("postal_code", "")
        if not pc:
            continue
        if not re.match(r"^\d{5}$", pc):
            out.append(fail(f"ADM3: TIS-{r['tis1099_subdistrict_code']} postal_code malformed: {pc!r}"))
    return out


def adm3_geometry_coverage(rows):
    out = []
    geo_present = sum(1 for r in rows if r.get("centroid_lat"))
    out.append(info(f"ADM3 geometry coverage: {geo_present}/{len(rows)} rows with polygon geometry"))
    if geo_present < 7400:
        out.append(warn(f"ADM3 geometry coverage below threshold (got {geo_present})"))
    return out


# ---------------------------------------------------------------------------
# Cross-level integrity
# ---------------------------------------------------------------------------
def cross_level_fk_existence(adm1, adm2, adm3):
    """Every ADM2.parent_province exists in ADM1; every ADM3.parent_district exists in ADM2."""
    out = []
    adm1_keys = {int(r["tis1099_code"]) for r in adm1}
    adm2_keys = {int(r["tis1099_district_code"]) for r in adm2}

    # ADM2 → ADM1
    missing_adm1 = []
    for r in adm2:
        try:
            p = int(r["parent_province_tis1099_code"])
        except (KeyError, ValueError):
            continue
        if p not in adm1_keys:
            missing_adm1.append((r["tis1099_district_code"], p))
    if missing_adm1:
        for code, p in missing_adm1[:5]:
            out.append(fail(f"ADM2 TIS-{code} references non-existent province TIS-{p}"))
        if len(missing_adm1) > 5:
            out.append(fail(f"... and {len(missing_adm1) - 5} more ADM2 → ADM1 FK violations"))
    else:
        out.append(info("All 928 ADM2 rows reference valid ADM1 provinces"))

    # ADM3 → ADM2 and ADM3 → ADM1
    missing_adm2 = []
    missing_adm1_from_adm3 = []
    for r in adm3:
        try:
            d = int(r["parent_district_tis1099_code"])
            p = int(r["parent_province_tis1099_code"])
        except (KeyError, ValueError):
            continue
        if d not in adm2_keys:
            missing_adm2.append((r["tis1099_subdistrict_code"], d))
        if p not in adm1_keys:
            missing_adm1_from_adm3.append((r["tis1099_subdistrict_code"], p))
    if missing_adm2:
        for code, d in missing_adm2[:5]:
            out.append(fail(f"ADM3 TIS-{code} references non-existent district TIS-{d}"))
        if len(missing_adm2) > 5:
            out.append(fail(f"... and {len(missing_adm2) - 5} more ADM3 → ADM2 FK violations"))
    else:
        out.append(info("All 7,436 ADM3 rows reference valid ADM2 districts"))
    if missing_adm1_from_adm3:
        out.append(fail(f"{len(missing_adm1_from_adm3)} ADM3 rows reference non-existent provinces"))
    else:
        out.append(info("All 7,436 ADM3 rows reference valid ADM1 provinces"))
    return out


def cross_level_count_consistency(adm1, adm2, adm3):
    """ADM1.num_amphoe sum equals ADM2 row count; ADM1.num_tambon sum equals ADM3 row count.
    Per-province counts also match."""
    out = []
    # Total counts
    adm1_amphoe_sum = sum(int(r.get("num_amphoe", 0) or 0) for r in adm1)
    adm1_tambon_sum = sum(int(r.get("num_tambon", 0) or 0) for r in adm1)
    out.append(info(f"ADM1 sum num_amphoe = {adm1_amphoe_sum}; ADM2 row count = {len(adm2)}"))
    out.append(info(f"ADM1 sum num_tambon = {adm1_tambon_sum}; ADM3 row count = {len(adm3)}"))
    if adm1_amphoe_sum != len(adm2):
        out.append(fail(f"ADM1.num_amphoe sum ({adm1_amphoe_sum}) != ADM2 row count ({len(adm2)})"))
    if adm1_tambon_sum != len(adm3):
        out.append(fail(f"ADM1.num_tambon sum ({adm1_tambon_sum}) != ADM3 row count ({len(adm3)})"))

    # Per-province count consistency
    adm2_count_by_province = defaultdict(int)
    for r in adm2:
        try:
            p = int(r["parent_province_tis1099_code"])
            adm2_count_by_province[p] += 1
        except (KeyError, ValueError):
            continue
    adm3_count_by_province = defaultdict(int)
    for r in adm3:
        try:
            p = int(r["parent_province_tis1099_code"])
            adm3_count_by_province[p] += 1
        except (KeyError, ValueError):
            continue

    for r in adm1:
        try:
            tis = int(r["tis1099_code"])
            n_amphoe = int(r.get("num_amphoe", 0) or 0)
            n_tambon = int(r.get("num_tambon", 0) or 0)
        except (KeyError, ValueError):
            continue
        actual_amphoe = adm2_count_by_province.get(tis, 0)
        actual_tambon = adm3_count_by_province.get(tis, 0)
        if n_amphoe != actual_amphoe:
            out.append(fail(f"ADM1 TIS-{tis}: num_amphoe={n_amphoe} but ADM2 has {actual_amphoe} rows"))
        if n_tambon != actual_tambon:
            out.append(fail(f"ADM1 TIS-{tis}: num_tambon={n_tambon} but ADM3 has {actual_tambon} rows"))
    return out


def cross_level_adm3_to_adm2_province_consistency(adm3, adm2):
    """ADM3.parent_province should equal ADM2[ADM3.parent_district].parent_province."""
    out = []
    adm2_parent_by_district = {int(r["tis1099_district_code"]): int(r["parent_province_tis1099_code"])
                                for r in adm2}
    for r in adm3:
        try:
            d = int(r["parent_district_tis1099_code"])
            p = int(r["parent_province_tis1099_code"])
        except (KeyError, ValueError):
            continue
        adm2_p = adm2_parent_by_district.get(d)
        if adm2_p is None: continue
        if p != adm2_p:
            out.append(fail(f"ADM3 TIS-{r['tis1099_subdistrict_code']}: claims province {p} but ADM2 says {adm2_p}"))
    return out


# ---------------------------------------------------------------------------
# Statistical sanity
# ---------------------------------------------------------------------------
def statistical_sanity(adm1, adm2, adm3):
    out = []
    # Total area
    total_area = sum(float(r.get("area_km2", 0) or 0) for r in adm1)
    diff_pct = abs(total_area - THAILAND_TOTAL_AREA_KM2) / THAILAND_TOTAL_AREA_KM2 * 100
    out.append(info(f"ADM1 total area = {total_area:,.0f} km² (RFD published: {THAILAND_TOTAL_AREA_KM2:,}; diff {diff_pct:+.2f}%)"))
    if diff_pct > 5:
        out.append(fail(f"ADM1 total area off by {diff_pct:.1f}% — exceeds 5% tolerance"))
    # ADM2 area sum (should also approximate Thailand total)
    adm2_area_sum = sum(float(r.get("area_km2", 0) or 0) for r in adm2 if r.get("area_km2"))
    out.append(info(f"ADM2 total area = {adm2_area_sum:,.0f} km² (sum of all districts)"))
    return out


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def main():
    print("Loading tables...")
    adm1 = load(ADM1_CSV)
    adm2 = load(ADM2_CSV)
    adm3 = load(ADM3_CSV)
    print(f"  ADM1: {len(adm1)} rows × {len(adm1[0])} cols")
    print(f"  ADM2: {len(adm2)} rows × {len(adm2[0])} cols")
    print(f"  ADM3: {len(adm3)} rows × {len(adm3[0])} cols")
    print()

    sections = []
    print("Running ADM1 checks (36 from v0.3.0 validator)...")
    sections.extend(run_adm1_checks(adm1))

    print("Running ADM2 checks...")
    sections.append(("ADM2: A1. row count = 928", adm2_row_count(adm2)))
    sections.append(("ADM2: A2. primary-key uniqueness and range", adm2_primary_key(adm2)))
    sections.append(("ADM2: A3. parent_province FK consistency", adm2_parent_fk_consistency(adm2)))
    sections.append(("ADM2: A4. names populated and Thai pure", adm2_names_populated(adm2)))
    sections.append(("ADM2: A5. geometry consistency (centroid in bbox; area positive)", adm2_geometry_consistency(adm2)))
    sections.append(("ADM2: A6. admin counts (num_tambon)", adm2_admin_counts(adm2)))

    print("Running ADM3 checks...")
    sections.append(("ADM3: B1. row count = 7,436", adm3_row_count(adm3)))
    sections.append(("ADM3: B2. primary-key uniqueness and range", adm3_primary_key(adm3)))
    sections.append(("ADM3: B3. parent FK consistency (district + province)", adm3_parent_fk_consistency(adm3)))
    sections.append(("ADM3: B4. names populated", adm3_names_populated(adm3)))
    sections.append(("ADM3: B5. postal_code format", adm3_postal_code(adm3)))
    sections.append(("ADM3: B6. geometry coverage (mapthai vintage difference acknowledged)", adm3_geometry_coverage(adm3)))

    print("Running cross-level integrity checks...")
    sections.append(("Cross-level: C1. FK existence (ADM2→ADM1, ADM3→ADM2, ADM3→ADM1)", cross_level_fk_existence(adm1, adm2, adm3)))
    sections.append(("Cross-level: C2. ADM1 admin counts match ADM2/ADM3 row counts per province", cross_level_count_consistency(adm1, adm2, adm3)))
    sections.append(("Cross-level: C3. ADM3.parent_province matches ADM2[parent_district].parent_province", cross_level_adm3_to_adm2_province_consistency(adm3, adm2)))

    print("Running statistical sanity...")
    sections.append(("Statistical: S1. ADM1 area total within ±5% of RFD published", statistical_sanity(adm1, adm2, adm3)))

    # Aggregate
    total_fails = sum(sum(1 for f in findings if f[0] == "FAIL") for _, findings in sections)
    total_warns = sum(sum(1 for f in findings if f[0] == "REVIEW") for _, findings in sections)
    total_infos = sum(sum(1 for f in findings if f[0] == "INFO") for _, findings in sections)

    # Console summary
    width = max(len(name) for name, _ in sections)
    for name, findings in sections:
        f_count = sum(1 for x in findings if x[0] == "FAIL")
        w_count = sum(1 for x in findings if x[0] == "REVIEW")
        i_count = sum(1 for x in findings if x[0] == "INFO")
        if f_count:
            status = f"\033[31m{f_count} FAIL\033[0m"
        elif w_count:
            status = f"\033[33m{w_count} REVIEW\033[0m"
        elif i_count:
            status = f"INFO ({i_count})"
        else:
            status = "\033[32mPASS\033[0m"
        print(f"  {name[:width]:<{width}}  {status}")
    print()
    print(f"Total: {total_fails} FAIL · {total_warns} REVIEW · {total_infos} INFO")
    print()

    # Write report
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# v1.0.0 Full Validation Report", ""]
    lines.append(f"**ADM1**: {len(adm1)} rows × {len(adm1[0])} columns")
    lines.append(f"**ADM2**: {len(adm2)} rows × {len(adm2[0])} columns")
    lines.append(f"**ADM3**: {len(adm3)} rows × {len(adm3[0])} columns")
    lines.append("")
    lines.append(f"**Summary**: {total_fails} FAIL, {total_warns} REVIEW, {total_infos} INFO across {len(sections)} checks")
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
    print(f"Report: {REPORT}")
    return 1 if total_fails > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
