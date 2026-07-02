#!/usr/bin/env python3
"""
Mutation test suite for the v0.3.0 validator.

For each validator check, deliberately corrupt the data and assert the validator
detects the corruption with a FAIL finding. This proves the validator catches
errors rather than silently passing.

Also runs:
  - Round-trip test: validator on the live table reports zero FAILs
  - Test that every column has at least one validation rule

Usage:
  python3 bin/test_v0_3_0.py
  (exits 0 on success, non-zero on test failure)
"""

import csv
import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "data" / "v0.3.0" / "thailand-adm-names-v0.3.0.csv"

# Load validator module dynamically
spec = importlib.util.spec_from_file_location("validator", ROOT / "bin" / "validate_v0_3_0.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def load_rows():
    with open(TABLE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fails_in(findings):
    """Count FAIL-severity findings."""
    return sum(1 for sev, _ in findings if sev == "FAIL")


def warns_in(findings):
    return sum(1 for sev, _ in findings if sev == "REVIEW")


# ---------------------------------------------------------------------------
# Round-trip test
# ---------------------------------------------------------------------------
class TestLiveTable(unittest.TestCase):
    """The live table must pass all checks with zero FAIL findings."""

    @classmethod
    def setUpClass(cls):
        cls.rows = load_rows()

    def test_row_count(self):
        self.assertEqual(len(self.rows), 77)

    def test_no_fails_on_live_table(self):
        for name, fn in validator.ALL_CHECKS:
            findings = fn(copy.deepcopy(self.rows))
            with self.subTest(check=name):
                self.assertEqual(
                    fails_in(findings), 0,
                    f"Live table FAILed check '{name}': {findings}"
                )


# ---------------------------------------------------------------------------
# Mutation tests — each mutates a copy of the data and asserts the validator
# detects the corruption.
# ---------------------------------------------------------------------------
class TestMutationDetection(unittest.TestCase):
    """For each validator check, mutate the data and prove the validator catches it."""

    @classmethod
    def setUpClass(cls):
        cls.original = load_rows()

    def _mutate(self, mutation_fn):
        """Apply a mutation to a deep copy and return the mutated rows."""
        rows = copy.deepcopy(self.original)
        mutation_fn(rows)
        return rows

    def test_check_01_row_count_drop(self):
        rows = self._mutate(lambda r: r.pop())
        self.assertGreater(fails_in(validator.check_01_row_count(rows)), 0)

    def test_check_02_tis_duplicate(self):
        def mutate(r):
            r[0]["tis1099_code"] = r[1]["tis1099_code"]
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_02_tis_uniqueness(rows)), 0)

    def test_check_03_tis_out_of_range(self):
        def mutate(r): r[0]["tis1099_code"] = "999"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_03_tis_range(rows)), 0)

    def test_check_04_iso_malformed(self):
        def mutate(r): r[0]["iso3166_2"] = "XX-99"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_04_iso_format_and_match(rows)), 0)

    def test_check_04_iso_does_not_match_tis(self):
        def mutate(r): r[0]["iso3166_2"] = "TH-99"  # tis is 10
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_04_iso_format_and_match(rows)), 0)

    def test_check_05_iso_duplicate(self):
        def mutate(r): r[0]["iso3166_2"] = r[1]["iso3166_2"]
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_05_iso_uniqueness(rows)), 0)

    def test_check_06_iso_type_invalid(self):
        def mutate(r): r[0]["iso_subdivision_type"] = "Region"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_06_iso_type(rows)), 0)

    def test_check_06_bangkok_iso_type_wrong(self):
        def mutate(r):
            for row in r:
                if int(row["tis1099_code"]) == 10:
                    row["iso_subdivision_type"] = "Province"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_06_iso_type(rows)), 0)

    def test_check_07_hasc_malformed(self):
        def mutate(r): r[0]["hasc"] = "XX.YY"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_07_hasc_format_and_uniqueness(rows)), 0)

    def test_check_07_hasc_duplicate(self):
        def mutate(r): r[0]["hasc"] = r[1]["hasc"]
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_07_hasc_format_and_uniqueness(rows)), 0)

    def test_check_08_fips_malformed(self):
        def mutate(r): r[0]["fips_code"] = "AB12"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_08_fips_format_and_uniqueness(rows)), 0)

    def test_check_09_qid_malformed(self):
        def mutate(r): r[0]["wikidata_qid"] = "X123"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_09_wikidata_qid(rows)), 0)

    def test_check_09_bangkok_qid_wrong(self):
        def mutate(r):
            for row in r:
                if int(row["tis1099_code"]) == 10:
                    row["wikidata_qid"] = "Q9999999"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_09_wikidata_qid(rows)), 0)

    def test_check_10_geonames_negative(self):
        def mutate(r): r[0]["geonames_id"] = "-1"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_10_geonames_id(rows)), 0)

    def test_check_11_osm_negative(self):
        def mutate(r): r[0]["osm_relation_id"] = "-5"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_11_osm_relation_id(rows)), 0)

    def test_check_12_wikipedia_url_malformed(self):
        def mutate(r): r[0]["wikipedia_article_url"] = "http://wrong.com"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_12_wikipedia_url(rows)), 0)

    def test_check_13_name_en_non_latin(self):
        def mutate(r): r[0]["name_en_canonical"] = "ภูเก็ต"  # Thai instead of Latin
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_13_name_en_canonical(rows)), 0)

    def test_check_14_name_th_not_thai(self):
        def mutate(r): r[0]["name_th"] = "Bangkok"  # Latin instead of Thai
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_14_name_th(rows)), 0)

    def test_check_15_alternate_equals_canonical(self):
        def mutate(r):
            r[0]["name_alternates_en"] = r[0]["name_en_canonical"]
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_15_name_alternates(rows)), 0)

    def test_check_16_region_invalid(self):
        def mutate(r): r[0]["region"] = "Atlantis"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_16_region(rows)), 0)

    def test_check_16_region_count_off(self):
        # Move one province from North to Central
        def mutate(r):
            for row in r:
                if row["region"] == "North":
                    row["region"] = "Central"
                    break
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_16_region(rows)), 0)

    def test_check_17_capital_th_empty(self):
        def mutate(r): r[0]["capital_th"] = ""
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_17_capital(rows)), 0)

    def test_check_18_established_year_unsupported(self):
        # Add an established_year on a row that has no CONFIRMED entry
        def mutate(r):
            for row in r:
                if not row["established_year"] and int(row["tis1099_code"]) != 10:
                    row["established_year"] = "1850"
                    return
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_18_established_year(rows)), 0)

    def test_check_19_predecessor_invalid(self):
        def mutate(r): r[0]["predecessor_tis1099_code"] = "999"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_19_predecessor(rows)), 0)

    def test_check_20_centroid_outside_thailand(self):
        def mutate(r):
            r[0]["centroid_lat"] = "0.0"
            r[0]["centroid_lon"] = "0.0"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_20_centroid_coordinates(rows)), 0)

    def test_check_21_centroid_outside_own_bbox(self):
        def mutate(r):
            row = r[0]
            row["centroid_lat"] = str(float(row["bbox_maxlat"]) + 1.0)
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_21_centroid_inside_bbox(rows)), 0)

    def test_check_22_bbox_inverted(self):
        def mutate(r):
            r[0]["bbox_minlat"], r[0]["bbox_maxlat"] = r[0]["bbox_maxlat"], r[0]["bbox_minlat"]
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_22_bbox_consistency(rows)), 0)

    def test_check_23_area_rai_mismatch(self):
        def mutate(r):
            # Set rai to wrong value (should be km2 * 625)
            r[0]["area_rai"] = "1.0"  # nowhere near km2 * 625
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_23_area_positive_and_rai(rows)), 0)

    def test_check_24_area_total_off(self):
        def mutate(r):
            # Halve all areas — sum will be way off
            for row in r:
                row["area_km2"] = str(float(row["area_km2"]) / 2)
                row["area_rai"] = str(float(row["area_km2"]) * 625)
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_24_total_area(rows)), 0)

    def test_check_25_distance_wrong(self):
        def mutate(r):
            for row in r:
                if int(row["tis1099_code"]) != 10:
                    row["distance_to_bangkok_km"] = "1.0"  # implausibly small for non-Bangkok
                    return
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_25_distance_to_bangkok(rows)), 0)

    def test_check_25_bangkok_distance_nonzero(self):
        def mutate(r):
            for row in r:
                if int(row["tis1099_code"]) == 10:
                    row["distance_to_bangkok_km"] = "100.0"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_25_distance_to_bangkok(rows)), 0)

    def test_check_26_neighbor_nonexistent(self):
        def mutate(r): r[0]["neighbors"] = "999"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_26_neighbors_membership(rows)), 0)

    def test_check_26_self_neighbor(self):
        def mutate(r): r[0]["neighbors"] = r[0]["tis1099_code"]
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_26_neighbors_membership(rows)), 0)

    def test_check_27_neighbors_asymmetric(self):
        def mutate(r):
            # Drop one neighbor from row 0's list to break symmetry
            n = r[0]["neighbors"].split("|")
            if n:
                r[0]["neighbors"] = "|".join(n[1:])
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_27_neighbors_symmetry(rows)), 0)

    def test_check_28_invalid_country(self):
        def mutate(r):
            for row in r:
                if row["bordering_countries"]:
                    row["bordering_countries"] = "Atlantis"
                    return
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_28_border_consistency(rows)), 0)

    def test_check_28_border_consistency_violated(self):
        def mutate(r):
            for row in r:
                if row["bordering_countries"]:
                    row["has_international_border"] = "false"
                    return
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_28_border_consistency(rows)), 0)

    def test_check_29_coastal_inconsistency(self):
        def mutate(r):
            for row in r:
                if row["is_coastal"] == "true":
                    row["coastline_length_km"] = "0"
                    return
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_29_coastal_consistency(rows)), 0)

    def test_check_30_postal_malformed(self):
        def mutate(r): r[0]["postal_code_prefixes"] = "ABC"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_30_postal_prefixes(rows)), 0)

    def test_check_31_telephone_malformed(self):
        def mutate(r): r[0]["telephone_area_codes"] = "abcd"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_31_telephone_codes(rows)), 0)

    def test_check_32_admin_count_implausible(self):
        def mutate(r): r[0]["num_amphoe"] = "0"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_32_admin_counts(rows)), 0)

    def test_check_32_tambon_less_than_amphoe(self):
        def mutate(r):
            r[0]["num_amphoe"] = "100"
            r[0]["num_tambon"] = "10"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_32_admin_counts(rows)), 0)

    def test_check_36_bangkok_invariant_qid(self):
        def mutate(r):
            for row in r:
                if int(row["tis1099_code"]) == 10:
                    row["wikidata_qid"] = "Q9999999"
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_36_bangkok_invariants(rows)), 0)

    def test_check_36_bangkok_missing_notes(self):
        def mutate(r):
            for row in r:
                if int(row["tis1099_code"]) == 10:
                    row["notes"] = ""
        rows = self._mutate(mutate)
        self.assertGreater(fails_in(validator.check_36_bangkok_invariants(rows)), 0)


# ---------------------------------------------------------------------------
# Coverage check: ensure every column has at least one validator rule
# ---------------------------------------------------------------------------
class TestColumnCoverage(unittest.TestCase):
    """Every column declared in the schema should have at least one validator
    check that references it."""

    EXPECTED_COLUMNS = {
        "tis1099_code", "iso3166_2", "iso_subdivision_type",
        "hasc", "fips_code", "wikidata_qid", "geonames_id", "osm_relation_id",
        "wikipedia_article_url",
        "name_en_canonical", "name_th", "name_alternates_en",
        "region", "capital", "capital_th",
        "established_year", "predecessor_tis1099_code",
        "centroid_lat", "centroid_lon",
        "area_km2", "area_rai",
        "bbox_minlat", "bbox_minlon", "bbox_maxlat", "bbox_maxlon",
        "distance_to_bangkok_km",
        "neighbors", "has_international_border", "bordering_countries",
        "is_coastal", "coastline_length_km",
        "postal_code_prefixes", "telephone_area_codes",
        "num_amphoe", "num_tambon", "notes",
    }

    def test_columns_present(self):
        rows = load_rows()
        actual = set(rows[0].keys())
        self.assertEqual(actual, self.EXPECTED_COLUMNS,
                         f"Schema mismatch.\nMissing: {self.EXPECTED_COLUMNS - actual}\nExtra: {actual - self.EXPECTED_COLUMNS}")

    def test_every_column_has_a_validator_reference(self):
        """Read the validator source and assert every expected column appears in it."""
        with open(ROOT / "bin" / "validate_v0_3_0.py", encoding="utf-8") as f:
            src = f.read()
        for col in self.EXPECTED_COLUMNS:
            with self.subTest(column=col):
                self.assertIn(col, src,
                              f"Column '{col}' is not referenced in validator source")


# ---------------------------------------------------------------------------
# Statistical sanity: compare totals against authoritative published figures
# ---------------------------------------------------------------------------
class TestStatisticalSanity(unittest.TestCase):
    """Cross-checks: aggregates of derived columns must match published totals
    within tolerance."""

    @classmethod
    def setUpClass(cls):
        cls.rows = load_rows()

    def test_total_area_within_5pct(self):
        total = sum(float(r["area_km2"]) for r in self.rows)
        published = 513120  # km², RFD figure
        diff_pct = abs(total - published) / published * 100
        self.assertLess(diff_pct, 5.0,
                        f"Province area total {total:.0f} km² is {diff_pct:.1f}% from published {published:,}")

    def test_total_amphoe_within_published_range(self):
        total = sum(int(r["num_amphoe"]) for r in self.rows)
        self.assertGreaterEqual(total, 850, f"sum num_amphoe = {total}, below expected range")
        self.assertLessEqual(total, 950, f"sum num_amphoe = {total}, above expected range")

    def test_total_tambon_within_published_range(self):
        total = sum(int(r["num_tambon"]) for r in self.rows)
        self.assertGreaterEqual(total, 7000, f"sum num_tambon = {total}, below expected range")
        self.assertLessEqual(total, 7500, f"sum num_tambon = {total}, above expected range")

    def test_region_distribution_exact(self):
        from collections import Counter
        counts = Counter(r["region"] for r in self.rows)
        for region, expected in [("North", 9), ("Central", 22), ("Northeast", 20),
                                  ("West", 5), ("East", 7), ("South", 14)]:
            self.assertEqual(counts[region], expected,
                             f"region {region}: expected {expected}, got {counts[region]}")

    def test_neighbors_graph_total_edges(self):
        """Sum of neighbor counts should be even (each edge counted twice)."""
        total = sum(len(r["neighbors"].split("|")) if r["neighbors"] else 0 for r in self.rows)
        self.assertEqual(total % 2, 0, f"Total neighbor count {total} is odd; symmetry violated")

    def test_borders_count(self):
        """Thailand has 31 international-border provinces."""
        bordered = sum(1 for r in self.rows if r["has_international_border"] == "true")
        self.assertEqual(bordered, 31, f"Expected 31 border provinces, got {bordered}")

    def test_coastal_count(self):
        """Thailand has 23-25 coastal provinces (varies by source)."""
        coastal = sum(1 for r in self.rows if r["is_coastal"] == "true")
        self.assertGreaterEqual(coastal, 22)
        self.assertLessEqual(coastal, 26)


if __name__ == "__main__":
    unittest.main(verbosity=2)
