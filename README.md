# Thailand Canonical Administrative-Names Reference

[![DOI](https://zenodo.org/badge/1230711905.svg)](https://doi.org/10.5281/zenodo.20049930)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![License: MIT (code)](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)

> Canonical English and Thai administrative names for Thailand at all three levels (77 provinces, 928 districts, 7,436 subdistricts), with TIS-1099 codes, ISO 3166-2 codes, alternates, capitals, regions, verified establishment years, polygon-derived geographic columns, and a documented override registry with a per-row audit trail. Published with a 36-page methodology PDF and bundled GeoJSON polygons.

**Status:** v1.0.2 released ([Zenodo DOI](https://doi.org/10.5281/zenodo.20049930)).
**Maintainer:** William J. Reynolds ([ORCID: 0009-0005-1217-7465](https://orcid.org/0009-0005-1217-7465))
**License:** CC BY 4.0 on the data and methodology. MIT on the build code.

## Citation

```
Reynolds, W. J. (2026). Thailand Canonical Administrative-Names Reference
[Data set]. Zenodo. https://doi.org/10.5281/zenodo.20049930
```

The DOI above is the **concept DOI** — it always resolves to the latest published version. Cite a specific version-DOI (visible on each Zenodo deposit page under "Versions") when reproducibility against a specific release matters.

---

## What this is

A defended canonical reference for Thai administrative-division names and codes. The Thai data ecosystem has multiple high-quality MIT-licensed name lists ([`thailand-geography-data`](https://github.com/thailand-geography-data/thailand-geography-json), [`kongvut/thai-province-data`](https://github.com/kongvut/thai-province-data), [`GeoThai/data`](https://github.com/GeoThai/data)), but none documents:

- The source-authority order behind chosen English spellings
- An audit trail per override
- Capitals (English and Thai)
- The year each province was constituted
- Alternate English spellings for join-friendliness
- A separate historical-mapping table (Bueng Kan / Nong Khai 2011 split)
- Polygon-derived centroids, areas, bounding boxes, and coastline lengths
- Cross-system identifiers (HASC, FIPS, Wikidata Q-ID, GeoNames ID, OSM relation ID)
- A peer-reviewable methodology PDF

This artifact composites those upstream sources, layers the methodology, and publishes the result under CC BY 4.0 with a Zenodo DOI.

## Schema

The artifact ships at three administrative levels (ADM1 / ADM2 / ADM3). Each level is its own CSV and Parquet file plus a bundled GeoJSON polygon file. Cross-level joins use the parent-code columns. Full per-column documentation lives in [Section 4 of the methodology PDF](methodology/build/methodology-v1.0.2.pdf).

### ADM1 — 77 provinces, 36 columns

The richest schema. Cross-system identifiers, names, geography, and operational lookups.

| Group | Columns |
|---|---|
| Identifiers | `tis1099_code`, `iso3166_2`, `iso_subdivision_type`, `hasc`, `fips_code`, `wikidata_qid`, `geonames_id`, `osm_relation_id`, `wikipedia_article_url` |
| Names | `name_en_canonical`, `name_th`, `name_alternates_en` |
| Administrative | `region`, `capital`, `capital_th`, `established_year`, `predecessor_tis1099_code` |
| Geography | `centroid_lat`, `centroid_lon`, `area_km2`, `area_rai`, `bbox_minlat`, `bbox_minlon`, `bbox_maxlat`, `bbox_maxlon`, `distance_to_bangkok_km` |
| Adjacency | `neighbors`, `has_international_border`, `bordering_countries`, `is_coastal`, `coastline_length_km` |
| Operational | `postal_code_prefixes`, `telephone_area_codes`, `num_amphoe`, `num_tambon` |
| Edge cases | `notes` |

> **Coverage note:** `osm_relation_id` is populated for 76 of 77 ADM1 rows; Phangnga (TIS-82) ships empty pending community correction. `predecessor_tis1099_code` is populated for 4 of 77 ADM1 rows (the CONFIRMED-established subset: Yasothon, Bueng Kan, Mukdahan, Phayao). Empty cells are documented gaps, not assertions of completeness — see [Section 17 of the methodology PDF](methodology/build/methodology-v1.0.2.pdf) for the full coverage table and the verification-upgrade path for the three PARTIAL-grade splits in the backlog.

### ADM2 — 928 districts, 14 columns

`tis1099_district_code`, `parent_province_tis1099_code`, `name_en`, `name_th`, `centroid_lat`, `centroid_lon`, `area_km2`, `bbox_minlat`, `bbox_minlon`, `bbox_maxlat`, `bbox_maxlon`, `num_tambon`, `postal_code_prefixes`, `notes`.

### ADM3 — 7,436 subdistricts, 8 columns

`tis1099_subdistrict_code`, `parent_district_tis1099_code`, `parent_province_tis1099_code`, `name_en`, `name_th`, `centroid_lat`, `centroid_lon`, `postal_code`.

## Files

### Data tables

- `data/v1.0.0/thailand-adm1-provinces-v1.0.0.csv` and `.parquet` — 77 rows × 36 columns
- `data/v1.0.0/thailand-adm2-districts-v1.0.0.csv` and `.parquet` — 928 rows × 14 columns
- `data/v1.0.0/thailand-adm3-subdistricts-v1.0.0.csv` and `.parquet` — 7,436 rows × 8 columns

### Polygon geometries

- `data/v1.0.0/thailand-adm1-polygons-v1.0.0.geojson` — 77 ADM1 polygons (96 KB)
- `data/v1.0.0/thailand-adm2-polygons-v1.0.0.geojson` — 928 ADM2 polygons (913 KB)
- `data/v1.0.0/thailand-adm3-polygons-v1.0.0.geojson` — 7,436 ADM3 polygons (7.1 MB)

Polygons are derived from `mapthai` (OCHA CODs lineage). The authoritative HDX RTSD shapefile distribution is linked rather than bundled (175 MB compressed).

### Auxiliary registries

- `data/overrides.csv` — per-row audit trail for every English-spelling override (one entry at v1.0: Lopburi / Loburi)
- `data/historical_mappings.csv` — boundary-change records (Bueng Kan / Nong Khai 2011 split)
- `data/established_years.csv` — verified-establishment-year registry with citation status (4 CONFIRMED + 5 PARTIAL)

### Methodology and verification

- `methodology/build/methodology-v1.0.2.pdf` — full methodology, 18 sections, 36 pages
- `methodology/build/methodology-v1.0.2.docx` — Word version of the same document
- `data/v1.0.0/wikipedia_infobox_verification_report.md` — area + centroid cross-check against Wikipedia infoboxes (73 of 77 within ±10%)
- `data/v1.0.0/alternates_wikipedia_attestation_report.md` — alternates verified against Wikipedia (58 of 71 attested)
- `data/v1.0.0/enrichment_verification_report.md` — eight enrichment-spot-check suites
- `data/v1.0.0/validation_report.md` — 49 cross-level integrity checks
- `data/upstream_drift_report.md` — upstream-cache-vs-live diff (refreshed weekly via GitHub Actions)

## Usage examples

### Python (pandas)

```python
import pandas as pd

# Read directly from the GitHub release.
url = "https://github.com/ReynoldsWJ55/thailand-canonical-admin-names/releases/download/v1.0.2"

provinces = pd.read_csv(
    f"{url}/thailand-adm1-provinces-v1.0.0.csv",
    dtype={"tis1099_code": "Int64", "established_year": "Int64"},
)

# Join your provincial dataset on TIS-1099 code.
your_data = pd.read_csv("your_dataset.csv")
joined = your_data.merge(provinces, left_on="province_code", right_on="tis1099_code")
```

### Python (Parquet, faster)

```python
import pandas as pd
url = "https://github.com/ReynoldsWJ55/thailand-canonical-admin-names/releases/download/v1.0.2"
provinces = pd.read_parquet(f"{url}/thailand-adm1-provinces-v1.0.0.parquet")
districts = pd.read_parquet(f"{url}/thailand-adm2-districts-v1.0.0.parquet")
subdistricts = pd.read_parquet(f"{url}/thailand-adm3-subdistricts-v1.0.0.parquet")
```

### SQL (DuckDB — reads remote CSV/Parquet directly)

```sql
INSTALL httpfs; LOAD httpfs;

SELECT
    name_en_canonical,
    region,
    area_km2,
    distance_to_bangkok_km
FROM 'https://github.com/ReynoldsWJ55/thailand-canonical-admin-names/releases/download/v1.0.2/thailand-adm1-provinces-v1.0.0.parquet'
WHERE region = 'Northeast'
ORDER BY area_km2 DESC;
```

### GeoPandas (polygons)

```python
import geopandas as gpd
url = "https://github.com/ReynoldsWJ55/thailand-canonical-admin-names/releases/download/v1.0.2"
provinces_geo = gpd.read_file(f"{url}/thailand-adm1-polygons-v1.0.0.geojson")
provinces_geo.plot(column="name_en_canonical", legend=False)
```

## Reproducing the build

The full build pipeline reproduces byte-identically from the cached upstream inputs in `data/inputs/`. The end-to-end smoke test (`bin/smoke_test_v1_0_0.py`) confirms this on every run.

```bash
git clone https://github.com/ReynoldsWJ55/thailand-canonical-admin-names.git
cd thailand-canonical-admin-names
pip install -r requirements.txt
python3 bin/build_v1_0_0.py
```

For the methodology PDF compile, also install `pandoc` and a TeX distribution (`xelatex`).

## Input sources

This artifact composites tabular data from five MIT-licensed repositories, identifier mappings from four reference services, and polygon boundaries from two geographic-data publishers.

### Tabular sources (MIT)

- [`thailand-geography-data/thailand-geography-json`](https://github.com/thailand-geography-data/thailand-geography-json) — primary names base at all three levels
- [`kongvut/thai-province-data`](https://github.com/kongvut/thai-province-data) — region grouping, subdistrict centroid fallback, English-spelling cross-check
- [`GeoThai/data`](https://github.com/GeoThai/data) — English-spelling cross-check at ADM1
- [`piyayut-ch/mapthai`](https://github.com/piyayut-ch/mapthai) — polygon source for centroid, area, and bounding-box computation; bundled GeoJSON output
- [`pmdscully/thailand_province_border_adjacency`](https://github.com/pmdscully/thailand_province_border_adjacency) — province-to-province adjacency for the `neighbors` column

### Identifier and code references

- Statoids — HASC and FIPS codes for Thai provinces
- Wikidata SPARQL — Q-IDs, capitals, and a subset of established years
- GeoNames `admin1CodesASCII.txt` — GeoNames ID for each ADM1 unit
- OpenStreetMap Nominatim — OSM relation ID for each ADM1 unit

### Geographic boundaries

- OCHA Common Operational Datasets via `mapthai` — bundled at all three ADM levels
- [HDX Royal Thai Survey Department dataset](https://data.humdata.org/dataset/cod-ab-tha) — authoritative Thai-government polygons; linked rather than bundled because the smallest distribution exceeds 175 MB compressed
- [Natural Earth `ne_50m_admin_0_countries`](https://github.com/nvkelso/natural-earth-vector) — neighbor-country polygons used to compute international-border and coastal flags

Per-source license, snapshot date, and contribution detail live in `methodology/build/methodology-v1.0.2.pdf` (Section 3) and `NOTICE.md`.

## Corrections and contributions

Found a spelling that should be reconsidered, an alternate to add, or a boundary-change record to include? Open a GitHub issue using one of the four templates (spelling correction, verification upgrade, polygon correction, methodology clarification) or submit a pull request. The methodology PDF Section 15 documents the corrections workflow and the maintainer SLA (issues triaged within four weeks; pull requests reviewed in the next monthly patch cycle). See [CONTRIBUTING.md](CONTRIBUTING.md) for templates and conventions.

## License

- The data and methodology are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You may share and adapt for any purpose, including commercial, with attribution.
- The build code under `bin/` is licensed under MIT.
- Bundled polygons inherit upstream licenses (CC BY 3.0 IGO via OCHA CODs). See `NOTICE.md` for the full layered-license breakdown and per-file attribution requirements.

## See also

- [Methodology PDF](methodology/build/methodology-v1.0.2.pdf) — full 36-page document covering 18 sections from input sources through limitations, with worked examples for the override rule (Lopburi / Loburi), capital normalization (Phrae), cross-system identifier resolution (Phuket), and the community-correction flow.
- [NOTICE.md](NOTICE.md) — per-file license attribution and upstream-source acknowledgments.
- [CHANGELOG.md](CHANGELOG.md) — release history and what changed between versions.
- [CONTRIBUTING.md](CONTRIBUTING.md) — issue templates, pull-request format, and corrections workflow.
- [Zenodo deposit](https://doi.org/10.5281/zenodo.20049930) — long-term archival copy with the citable concept-DOI.
- [Royal Thai General System of Transcription (RTGS)](http://www.royin.go.th/) — the romanization standard the artifact follows by default.
- [HDX Royal Thai Survey Department dataset](https://data.humdata.org/dataset/cod-ab-tha) — the authoritative Thai-government polygon source. Linked rather than bundled because the smallest distribution exceeds practical repo size at 175 MB compressed.
