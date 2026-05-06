# v1.0.0 Enrichment-Layer Verification Report

This report verifies the artifact's value-add layer — every column whose values come from our work (overrides, identifier lookups, polygon computation, normalization rules, primary-source verification, alternates harvesting). Upstream-source row content is verified separately by the comprehensive validator.

**Summary**: 0 FAIL · 0 REVIEW · 16 INFO across 8 verification suites

### E1. Identifier round-trip (HASC, FIPS, GeoNames, Wikidata) against cached sources

- **INFO** — HASC + FIPS round-trip: 77 rows match Statoids cache exactly
- **INFO** — GeoNames ID round-trip: 77 rows match cached admin1 dump (joined via FIPS)
- **INFO** — Wikidata QID round-trip: 77 rows match cached SPARQL response

### E2. Anchor-value spot checks (Bangkok, Phuket, Chiang Mai, Bueng Kan, etc.)

- **INFO** — All 9 anchor-value spot-checks passed

### E3. Geographic anomaly detection (areas, centroids, distances, area_rai derivation)

- **INFO** — No geographic anomalies detected

### E4. Override registry audit (every cross-source disagreement has an override)

- **INFO** — Source disagreements found: 1
- **INFO** — Overrides registered: 1
- **INFO** — Override-to-chosen-spelling matches: 1

### E5. Established_year primary-source verification (table values trace to CONFIRMED registry)

- **INFO** — Table established_year populated rows: 4
- **INFO** — established_years.csv CONFIRMED rows: 4
- **INFO** — established_years.csv PARTIAL rows: 5 (intentionally not flowed to table)
- **INFO** — All 4 table-populated established_year values trace to CONFIRMED registry rows

### E6. Border + coastal flags against known Thai geography

- **INFO** — All 31 has_international_border=true rows match known border-province set
- **INFO** — All 24 is_coastal=true rows match known coastal-province set

### E7. Wikipedia article URL format

- **INFO** — All 77 Wikipedia URLs follow expected format

### E8. Alternates plausibility (non-empty, not canonical, valid format)

- **INFO** — Alternates populated: 50/77 rows, 71 total alternates
