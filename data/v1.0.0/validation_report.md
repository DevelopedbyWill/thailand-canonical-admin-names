# v1.0.0 Full Validation Report

**ADM1**: 77 rows × 36 columns
**ADM2**: 928 rows × 14 columns
**ADM3**: 7436 rows × 8 columns

**Summary**: 0 FAIL, 0 REVIEW, 14 INFO across 52 checks

### ADM1: 01. Row count = 77

PASS

### ADM1: 02. tis1099_code uniqueness and integer

PASS

### ADM1: 03. tis1099_code in range 10-96

PASS

### ADM1: 04. iso3166_2 format and matches tis1099_code

PASS

### ADM1: 05. iso3166_2 uniqueness

PASS

### ADM1: 06. iso_subdivision_type domain and Bangkok-special-case

PASS

### ADM1: 07. hasc format and uniqueness

PASS

### ADM1: 08. fips_code format and uniqueness

PASS

### ADM1: 09. wikidata_qid format, uniqueness, and Bangkok=Q1861

PASS

### ADM1: 10. geonames_id positive integer and uniqueness

PASS

### ADM1: 11. osm_relation_id format and uniqueness (optional)

PASS

### ADM1: 12. wikipedia_article_url format and uniqueness

PASS

### ADM1: 13. name_en_canonical Latin-only, non-empty, unique

PASS

### ADM1: 14. name_th pure-Thai, non-empty, unique

PASS

### ADM1: 15. name_alternates_en pipe-separated, no self-equals

PASS

### ADM1: 16. region domain and Royal Institute distribution counts

PASS

### ADM1: 17. capital and capital_th non-empty; Thai script for capital_th

PASS

### ADM1: 18. established_year traces to a CONFIRMED row in established_years.csv

PASS

### ADM1: 19. predecessor_tis1099_code references valid row, matches historical_mappings.csv, no self-ref

PASS

### ADM1: 20. centroid coordinates inside Thailand bounding box

PASS

### ADM1: 21. centroid lies inside the row's own bbox

PASS

### ADM1: 22. bbox: min < max for both lat and lon

PASS

### ADM1: 23. area_km2 and area_rai positive; rai = km2 * 625

PASS

### ADM1: 24. sum of area_km2 within ±5% of Thailand total (~513,120 km²)

- **INFO** — sum of area_km2 = 514,192 (+0.21% from RFD published total)

### ADM1: 25. distance_to_bangkok_km matches Haversine recomputation; Bangkok=0

PASS

### ADM1: 26. all neighbors exist as TIS-1099 codes in the table; no self-ref

PASS

### ADM1: 27. neighbors symmetry: A->B implies B->A

PASS

### ADM1: 28. border consistency: has_international_border ↔ bordering_countries non-empty; sorted; valid country names

PASS

### ADM1: 29. coastal consistency: is_coastal ↔ coastline_length_km > 0

PASS

### ADM1: 30. postal_code_prefixes 2-digit format

PASS

### ADM1: 31. telephone_area_codes 2-3 digit format

PASS

### ADM1: 32. num_amphoe > 0, num_tambon > num_amphoe; totals within published ranges

- **INFO** — sum num_amphoe = 928 (within expected 878-928)
- **INFO** — sum num_tambon = 7436 (within expected 7000-7500)

### ADM1: 33. capital-vs-province-name alignment with notes-field documentation

- **INFO** — TIS-64: capital differs from name (expected, documented)

### ADM1: 34. name_en_canonical cross-check against four MIT input sources (excludes overrides)

PASS

### ADM1: 35. capital matches Wikidata after documented normalizations

PASS

### ADM1: 36. Bangkok-specific invariants (TIS-10, Q1861, special-area, distance=0, notes-field)

PASS

### ADM2: A1. row count = 928

PASS

### ADM2: A2. primary-key uniqueness and range

PASS

### ADM2: A3. parent_province FK consistency

PASS

### ADM2: A4. names populated and Thai pure

PASS

### ADM2: A5. geometry consistency (centroid in bbox; area positive)

- **INFO** — ADM2 geometry coverage: 928/928 rows with polygon geometry

### ADM2: A6. admin counts (num_tambon)

- **INFO** — ADM2 sum of num_tambon = 7436

### ADM3: B1. row count = 7,436

PASS

### ADM3: B2. primary-key uniqueness and range

PASS

### ADM3: B3. parent FK consistency (district + province)

PASS

### ADM3: B4. names populated

PASS

### ADM3: B5. postal_code format

PASS

### ADM3: B6. geometry coverage (mapthai vintage difference acknowledged)

- **INFO** — ADM3 geometry coverage: 7422/7436 rows with polygon geometry

### Cross-level: C1. FK existence (ADM2→ADM1, ADM3→ADM2, ADM3→ADM1)

- **INFO** — All 928 ADM2 rows reference valid ADM1 provinces
- **INFO** — All 7,436 ADM3 rows reference valid ADM2 districts
- **INFO** — All 7,436 ADM3 rows reference valid ADM1 provinces

### Cross-level: C2. ADM1 admin counts match ADM2/ADM3 row counts per province

- **INFO** — ADM1 sum num_amphoe = 928; ADM2 row count = 928
- **INFO** — ADM1 sum num_tambon = 7436; ADM3 row count = 7436

### Cross-level: C3. ADM3.parent_province matches ADM2[parent_district].parent_province

PASS

### Statistical: S1. ADM1 area total within ±5% of RFD published

- **INFO** — ADM1 total area = 514,192 km² (RFD published: 513,120; diff +0.21%)
- **INFO** — ADM2 total area = 514,693 km² (sum of all districts)
