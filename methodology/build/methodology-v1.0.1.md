---
title: "Thailand Canonical Administrative-Names Reference"
subtitle: "Methodology"
author:
  - "William J. Reynolds"
  - "ORCID: 0009-0005-1217-7465"
date: "v1.0.1 — 6 May 2026 — DOI: 10.5281/zenodo.20049930"
header-includes:
  - \usepackage{hyperref}
  - \hypersetup{pdftitle={Thailand Canonical Administrative-Names Reference}, pdfauthor={William J. Reynolds}, pdfsubject={Methodology}, pdfkeywords={Thailand, administrative divisions, TIS-1099, ISO 3166-2, RTGS, gazetteer}}
abstract: |
  This document specifies the methodology behind the Thailand Canonical Administrative-Names Reference, a CC BY 4.0 dataset of Thailand's administrative divisions at all three levels (77 provinces, 928 districts, 7,436 subdistricts). The artifact ships cross-system identifiers, normalized English and Thai names, an override registry with audit trail, and computed geographic columns. It composites four MIT-licensed upstream Thai-province repositories with reconciliation rules, override resolution, and validation against published government totals. Bundled polygon geometries (GeoJSON at all three levels) accompany the tabular outputs. The release is intended as community infrastructure for the broader Thai data-engineering and academic-research community.
toc: true
toc-depth: 2
numbersections: false
geometry: margin=1in
fontsize: 11pt
mainfont: "DejaVu Serif"
sansfont: "DejaVu Sans"
monofont: "DejaVu Sans Mono"
linkcolor: "MidnightBlue"
urlcolor: "MidnightBlue"
toccolor: "black"
---

\newpage

# 1. Purpose

This document specifies the methodology behind the Thailand Canonical Administrative-Names Reference, a CC BY 4.0 dataset of Thailand's administrative divisions at all three levels (77 provinces, 928 districts, 7,436 subdistricts). The artifact ships, per row, cross-system identifiers, normalized English and Thai names, override registries with audit trails, and computed geographic columns. The release also bundles polygon geometries: GeoJSON files for each administrative level plus the HDX Royal Thai Survey Department (RTSD) shapefiles. It composites four MIT-licensed upstream repositories: [`thailand-geography-data`](https://github.com/thailand-geography-data/thailand-geography-json), [`kongvut/thai-province-data`](https://github.com/kongvut/thai-province-data), [`GeoThai/data`](https://github.com/GeoThai/data), and [`mapthai`](https://github.com/piyayut-ch/mapthai). Methodology covers four passes: composition over the upstream sources, override resolution where sources diverge, computation of derived geographic columns, and validation against published Thai-government totals. Subsequent sections specify each pass.

The artifact addresses a join-time data-quality problem. Official province-name spellings vary across Thai government bodies. The Royal Thai General System of Transcription (RTGS), published by the [Royal Society of Thailand](http://www.royin.go.th/), is the official romanization standard, but application is inconsistent. The Department of Provincial Administration (DOPA) uses one spelling on its English-language tourism content. The National Statistical Office (NSO) uses another in the *Statistical Yearbook*. The Tourism Authority of Thailand (TAT) uses a third in its province directory. The Board of Investment (BOI) uses a fourth in its investment-zone listings. Adopters who join Thai-government datasets together encounter the divergence row by row.

The consequence is concrete. A pipeline joining DOPA registered-population data against WorldPop satellite-derived population on the English province name returns spurious "missing" rows for any province that the two corpora spell differently. Joins onto the TIS-1099 code resolve it, but only when both corpora carry the code in the first place. Many third-party Thai datasets ship the English name as the only stable identifier, and the failure mode propagates to every adopter who joins on that field.

The artifact's discipline is documentary: every spelling choice traces to a named source, and every limitation receives a dedicated note naming the specific gap plus the consequence for downstream use. The override registry at `overrides.csv` carries the per-row audit trail (chosen spelling, strict-rendering candidate, supporting sources, decision date, decision author).

\newpage

# 2. Scope

v1.0.0 ships the full canonical reference in a single release. The release covers Thailand's 77 provinces (administrative level 1, ADM1, including Bangkok as a special administrative area), 928 districts (ADM2, locally amphoe), and 7,436 subdistricts (ADM3, locally tambon). Each level ships as a separate CSV and Parquet file with parent administrative codes for joining to the level above. The release also bundles polygon geometries: GeoJSON files for ADM1, ADM2, and ADM3 derived from the [`mapthai`](https://github.com/piyayut-ch/mapthai) source GeoJSON. The authoritative Thai-government polygon source is the [HDX Royal Thai Survey Department dataset](https://data.humdata.org/dataset/cod-ab-tha), which ships in shapefile, GeoJSON, geodatabase, and XLSX formats; the smallest distribution is 175 MB compressed, which makes direct bundling in a GitHub repository impractical. Adopters requiring the authoritative source download it directly from HDX. License layering is documented in the NOTICE file at the artifact root: tabular content is CC BY 4.0; bundled `mapthai`-derived GeoJSON inherits the OCHA Common Operational Datasets CC BY 3.0 IGO license; the HDX RTSD distributions are CC BY-IGO 3.0 from OCHA when downloaded directly.

Source-attribution discipline applies at all three administrative levels with calibration to row count. ADM1 carries the full audit trail: the source-of-spelling cross-check runs against four MIT-licensed inputs (the upstream repositories listed in Section 3) and four Thai-government tables (DOPA, NSO, TAT, BOI), with overrides logged per row in `overrides.csv` (one entry at v1.0, the Lopburi case detailed in Section 6). ADM2 and ADM3 ship the upstream MIT-licensed names with PyThaiNLP normalization and cross-source de-duplication; row counts at those levels (928 and 7,436) preclude per-row manual cross-checking against government tables in the v1.0 release window. Community corrections at all three levels arrive through the GitHub issues and pull-requests channel and ship in patch releases.

Several items remain out of scope at v1.0.0. The artifact ships English-language methodology only; data tables carry Thai script in their respective name columns, but this methodology document is English at v1.0.0. Time-varying operational data (current population, current GPP, current governor) lives in separate time-series tables that join via admin codes. The artifact does not ship muban (village, ADM4) records; the lowest level included is tambon. Editorial commentary and per-region lifestyle context live elsewhere; the canonical reference is identifier-focused.

\newpage

# 3. Input sources

v1.0 composites tabular data from five MIT-licensed repositories, identifier mappings from four reference services, and polygon boundaries from two geographic-data publishers. The tables below name each source with license, snapshot date, and the columns or fields this artifact derives from it. Each repository's full LICENSE file is preserved alongside the cached input at `data/inputs/<source>/LICENSE` in the artifact repository.

## 3.1 Primary tabular sources (MIT-licensed)

| Source | License | Snapshot | Contributes |
|---|---|---|---|
| [`thailand-geography-data`](https://github.com/thailand-geography-data/thailand-geography-json) (Takara, 2023) | MIT | 2026-05-06 main | TIS-1099 codes, English and Thai names at all three levels, postal codes, parent-code joins |
| [`kongvut/thai-province-data`](https://github.com/kongvut/thai-province-data) (Sangkla, 2025) | MIT | 2026-05-06 master | Region grouping at ADM1 (`geography_id`), subdistrict lat/long for centroid fallback, English-spelling cross-check |
| [`GeoThai/data`](https://github.com/GeoThai/data) | MIT | 2026-05-06 main (v1 and v2) | English-spelling cross-check at ADM1; informational comparator |
| [`mapthai`](https://github.com/piyayut-ch/mapthai) (Chitchumnong, n.d.) | MIT (data layer originates from OCHA CODs CC BY 3.0 IGO) | 2026-05-06 master | ADM1, ADM2, ADM3 polygons in GeoJSON form for centroid, area, and bounding-box computation; bundled in v1.0 distribution |
| [`pmdscully/thailand_province_border_adjacency`](https://github.com/pmdscully/thailand_province_border_adjacency) (Scully, 2021) | MIT | 2026-05-06 main | Province-to-province adjacency relations for the `neighbors` column |

The composition pass uses `thailand-geography-data` as the primary names base for several reasons. The `provinceCode` column is TIS-1099 native, which simplifies join-key creation. ADM1, ADM2, and ADM3 ship in one repository with consistent schema across levels. Maintenance cadence is active. The other three MIT-licensed names sources (`kongvut`, `GeoThai/data` v1, `GeoThai/data` v2) serve as cross-validators rather than primary inputs; their English-name columns confirm or surface divergence from `thailand-geography-data`, with divergences logged in `overrides.csv` per the rule specified in Section 6.

## 3.2 Identifier and code reference sources

| Source | License | Contributes |
|---|---|---|
| [Wikidata](https://www.wikidata.org/) SPARQL endpoint | CC0 on data | `wikidata_qid`, capital labels (English and Thai), inception dates where present (P571) |
| [Statoids](https://statoids.com/uth.html) (Law, n.d.) | website-published reference | HASC and FIPS codes |
| [GeoNames admin1 codes](http://download.geonames.org/export/dump/admin1CodesASCII.txt) | CC BY 4.0 | `geonames_id` per province (joined on FIPS) |
| [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) | ODbL on data; service is fair-use | `osm_relation_id` per province |
| [Wikipedia](https://en.wikipedia.org/) | CC BY-SA 4.0 | Article URLs; verification of `established_year` against article history sections |

Identifier-source responses are cached at build time for reproducibility. Wikidata SPARQL responses live at `data/inputs/wikidata/`. Statoids HTML lives at `data/inputs/statoids/`. GeoNames admin1 dump lives at `data/inputs/geonames/`. OpenStreetMap Nominatim relation lookups live at `data/inputs/computed/osm_relations.json`. Wikipedia article wikitexts live at `data/inputs/wikipedia/` (gzipped to keep the cache size manageable). Re-running the build script with no network access succeeds against the cached inputs.

## 3.3 Geographic boundary sources

| Source | License | Contributes |
|---|---|---|
| [Natural Earth Vector](https://github.com/nvkelso/natural-earth-vector) (Kelso & Patterson, n.d.) | CC0 (public domain) | Neighbor-country polygons (Myanmar, Laos, Cambodia, Malaysia) for international-border detection |
| [HDX Royal Thai Survey Department](https://data.humdata.org/dataset/cod-ab-tha) (OCHA, n.d.) | CC BY 3.0 IGO under OCHA CODs framework | Bundled in v1.0 as the authoritative Thai-government shapefile source |

Natural Earth provides the country polygons used in the polygon-intersection method that populates `bordering_countries`, `has_international_border`, and `coastline_length_km` (specified in Section 9). The HDX Royal Thai Survey Department shapefiles ship in the v1.0 release for consumers requiring the official Thai-government polygon source rather than the OCHA-derived `mapthai` GeoJSON. Both coexist in the release: `mapthai`-derived GeoJSON is the smaller and more accessible polygon source for tabular workflows; HDX RTSD shapefiles are the authoritative source for consumers willing to work in shapefile format.

\newpage

# 4. Schema specification

The artifact ships three CSV files and three Parquet files (one per administrative level), plus the bundled GeoJSON files and HDX RTSD shapefiles. CSV is UTF-8 encoded with a header row. Parquet uses Snappy compression. Pipe character `|` separates list-valued cells. The schemas below specify each column for each level. Foreign-key columns naming a parent administrative code allow cross-level joins without intermediate lookups.

## 4.1 ADM1 schema

File: `thailand-adm1-provinces-v1.0.0.csv` / `.parquet`. Coverage: 77 rows × 36 columns.

| Column | Type | Description |
|---|---|---|
| `tis1099_code` | integer | TIS-1099 ADM1 numeric code; primary key. Range 10–96 with gaps. |
| `iso3166_2` | string | ISO 3166-2 code, format `TH-NN` (matches `tis1099_code` zero-padded). |
| `iso_subdivision_type` | enum | `Province` for 76 rows; `Special Administrative Area` for Bangkok. |
| `hasc` | string | Hierarchical Administrative Subdivision Code (Statoids), format `TH.XX`. |
| `fips_code` | string | FIPS PUB 10-4 code (deprecated 2014, retained for legacy datasets), format `TH\d{2}`. |
| `wikidata_qid` | string | Wikidata entity ID, format `Q\d+`. |
| `geonames_id` | integer | GeoNames numeric ID (joined to GeoNames admin1 dump via FIPS). |
| `osm_relation_id` | integer | OpenStreetMap relation ID; one row (Phangnga, TIS-82) is empty pending community correction. |
| `wikipedia_article_url` | string | English Wikipedia article URL for the province. |
| `name_en_canonical` | string | Recommended English spelling per the override rule (Section 6). |
| `name_th` | string | Thai-script name, normalized via PyThaiNLP. |
| `name_alternates_en` | string | Pipe-separated alternate English spellings. Populated for 50 of 77 rows with 71 total alternates at v1.0, drawn from Wikidata aliases, Wikipedia redirects, the override registry, and systematically generated spacing variants. The accompanying `alternates_wikipedia_attestation_report.md` lists each alternate with its Wikipedia attestation method (redirect, intitle search, or wikitext substring) and flags 13 entries that are deliberately preserved without Wikipedia attestation: 11 are no-space concatenated variants (such as `BuengKan`, `RoiEt`, `NakhonSiThammarat`) added to support consumers that strip whitespace, one is the `Loburi` override-registry entry, and one is the historical `Sia-Yut'hia` Bangkok spelling. |
| `region` | enum | One of: North, Central, Northeast, West, East, South (Royal Institute six-region grouping). |
| `capital` | string | Provincial capital, English. |
| `capital_th` | string | Provincial capital, Thai (municipality prefix stripped). |
| `established_year` | integer | Year the province was established as a modern administrative unit. Populated only where primary-source verified (4 rows at v1.0; the verification threshold is specified in Section 18). |
| `predecessor_tis1099_code` | integer | For provinces carved out of others (e.g., Bueng Kan TIS-38 with predecessor 43, the Nong Khai code). Empty otherwise. |
| `centroid_lat` | float | Polygon-geometric centroid latitude (decimal degrees, EPSG:4326). |
| `centroid_lon` | float | Polygon-geometric centroid longitude. |
| `area_km2` | float | Area in square kilometers (UTM 47N or 48N projected, see Section 9). |
| `area_rai` | float | Area in rai (Thai unit). Derived: `area_km2 × 625`. |
| `bbox_minlat` | float | Polygon bounding-box minimum latitude. |
| `bbox_minlon` | float | Polygon bounding-box minimum longitude. |
| `bbox_maxlat` | float | Polygon bounding-box maximum latitude. |
| `bbox_maxlon` | float | Polygon bounding-box maximum longitude. |
| `distance_to_bangkok_km` | float | Haversine great-circle distance from province centroid to Bangkok centroid. 0.0 for Bangkok itself. |
| `neighbors` | string | Pipe-separated TIS-1099 codes of adjacent Thai provinces. |
| `has_international_border` | boolean | `true` if the province polygon shares a boundary with a neighbor-country polygon. |
| `bordering_countries` | string | Pipe-separated, sorted: subset of `Myanmar`, `Laos`, `Cambodia`, `Malaysia`. |
| `is_coastal` | boolean | `true` if the province polygon shares a boundary with the Gulf of Thailand or Andaman Sea. |
| `coastline_length_km` | float | Coastline length in kilometers; populated only where `is_coastal=true`. |
| `postal_code_prefixes` | string | Pipe-separated 2-digit postal prefixes covering the province. |
| `telephone_area_codes` | string | Pipe-separated telephone area codes. Single province may carry multiple; multiple provinces may share one. |
| `num_amphoe` | integer | District count for the province. Sum across the table = 928. |
| `num_tambon` | integer | Subdistrict count for the province. Sum across the table = 7,436. |
| `notes` | string | Edge-case documentation (e.g., Bangkok's special-administrative-area status; Sukhothai's distinct capital name). Sparse. |

## 4.2 ADM2 schema

File: `thailand-adm2-districts-v1.0.0.csv` / `.parquet`. Coverage: 928 rows × 14 columns.

The ADM2 schema is intentionally smaller than ADM1. Districts inherit most identity metadata from the parent province, and per-district enrichment passes (cross-system identifier mapping, capital lookup) are not in scope at v1.0.

| Column | Type | Description |
|---|---|---|
| `tis1099_district_code` | integer | 4-digit TIS-1099 ADM2 code; primary key. First 2 digits match the parent province code. |
| `parent_province_tis1099_code` | integer | TIS-1099 ADM1 code; foreign key to the ADM1 table. |
| `name_en` | string | District name in English. |
| `name_th` | string | District name in Thai (PyThaiNLP-normalized). |
| `centroid_lat` | float | Polygon-geometric centroid latitude. |
| `centroid_lon` | float | Polygon-geometric centroid longitude. |
| `area_km2` | float | Area in square kilometers (UTM-projected). |
| `bbox_minlat` | float | Bounding-box minimum latitude. |
| `bbox_minlon` | float | Bounding-box minimum longitude. |
| `bbox_maxlat` | float | Bounding-box maximum latitude. |
| `bbox_maxlon` | float | Bounding-box maximum longitude. |
| `num_tambon` | integer | Subdistrict count for this district. |
| `postal_code_prefixes` | string | Pipe-separated 4-digit postal prefixes. |
| `notes` | string | Sparse. |

## 4.3 ADM3 schema

File: `thailand-adm3-subdistricts-v1.0.0.csv` / `.parquet`. Coverage: 7,436 rows × 8 columns.

The ADM3 schema is the smallest in the artifact. Subdistrict-level enrichment is bounded both by the row count and by upstream-source completeness; the v1.0 release ships the cleaned base names and the geometry derivable from the `mapthai` ADM3 GeoJSON, with foreign keys for joining upward.

| Column | Type | Description |
|---|---|---|
| `tis1099_subdistrict_code` | integer | 6-digit TIS-1099 ADM3 code; primary key. First 4 digits match parent district. First 2 digits match parent province. |
| `parent_district_tis1099_code` | integer | TIS-1099 ADM2 code; foreign key to the ADM2 table. |
| `parent_province_tis1099_code` | integer | TIS-1099 ADM1 code; foreign key to the ADM1 table. |
| `name_en` | string | Subdistrict name in English. |
| `name_th` | string | Subdistrict name in Thai. |
| `centroid_lat` | float | Polygon-geometric centroid latitude. |
| `centroid_lon` | float | Polygon-geometric centroid longitude. |
| `postal_code` | integer | 5-digit postal code; one per subdistrict in most cases. |

## 4.4 File format

CSV files are UTF-8 encoded with a single header row carrying the column names exactly as specified above. Empty cells are represented by an empty string in CSV. Parquet files use Snappy compression and represent empty cells as Parquet null. List-valued cells (alternates, neighbors, prefixes) ship as pipe-separated strings in both CSV and Parquet at v1.0 for cross-format consistency; a future release may switch the Parquet encoding to repeated/list types.

GeoJSON files are RFC 7946-compliant. Properties on each feature carry the corresponding `tis1099_code`, `tis1099_district_code`, or `tis1099_subdistrict_code` for joining to the tabular files. The HDX RTSD shapefiles ship in their original ESRI Shapefile format (`.shp` + `.dbf` + `.shx` + `.prj`) under their published license.

\newpage

# 5. Composition pass

The composition pass reads the cached upstream inputs and produces a base table per administrative level before the override and enrichment passes apply. The pass is deterministic: with inputs cached at `data/inputs/`, re-running the build script offline yields a byte-identical base table.

Composition uses Thai script as the language-independent join key. Each upstream repository's English-name column is treated as a candidate spelling rather than an authoritative one until the override pass (Section 6) resolves divergences. Joining on Thai script avoids the circular problem of choosing one English spelling to join on when the artifact's purpose is to specify which English spelling is canonical.

At ADM1, the cross-source comparison produces a per-province agreement matrix. The four MIT-licensed primary sources ([`thailand-geography-data`](https://github.com/thailand-geography-data/thailand-geography-json), [`kongvut/thai-province-data`](https://github.com/kongvut/thai-province-data), [`GeoThai/data`](https://github.com/GeoThai/data) v1, and [`GeoThai/data`](https://github.com/GeoThai/data) v2) are joined on Thai script and their English-name columns are compared cell by cell. The cross-check script `bin/cross_check_inputs.py` produces a markdown report at `data/v1.0.0/cross_check_report.md` reporting 76 of 77 agreements and 1 disagreement. The 76 agreement rows pass through unchanged from `thailand-geography-data`, the primary source. The 1 disagreement is the Lopburi case detailed in Section 6 and resolved via the override registry.

At ADM2 and ADM3, the row counts (928 districts and 7,436 subdistricts) preclude a full inter-source spelling cross-check at v1.0. Composition for these levels takes `thailand-geography-data` as the source-of-record for the English-name column and applies the PyThaiNLP library (PyThaiNLP, 2024) to the Thai-script column for Unicode normalization. Cross-source ADM2 and ADM3 cross-checking is deferred to subsequent releases as community submissions arrive through the GitHub issues channel; the v1.0 release ships these levels with single-source provenance disclosed in the data documentation.

The build script `bin/build_v1_0_0.py` is the canonical implementation. The script reads each cached input from `data/inputs/`, joins on Thai script, applies PyThaiNLP normalization, and writes the per-level base tables to `data/v1.0.0/`. Output regenerates whenever upstream inputs are re-cached or override registry rows change. Determinism guarantees a hash-checkable build artifact, which supports reproducibility claims without requiring downstream consumers to re-run the upstream-source pulls themselves.

\newpage

# 6. Source authority and override rule

v1.0 follows the Royal Thai General System of Transcription (RTGS) by default and overrides RTGS only where a clear majority of authoritative Thai-government tables (DOPA, NSO, RTSD, TAT, BOI) and the international literature agree on a non-RTGS spelling. Every override is logged in `overrides.csv` with a per-row audit trail.

The rule reflects an operational reality: RTGS is the official romanization standard, but Thai government bodies apply it inconsistently. Strictly following RTGS in every cell would produce spellings that no government dataset uses, which defeats the artifact's purpose as a join target. Strictly following government practice without RTGS as the default would lose the formal anchor that justifies the canonical claim. The override rule preserves both: RTGS as the default with a documented exception process for cases where government-practice consensus has diverged.

The override resolution procedure runs at composition time. For each cross-source disagreement surfaced by `bin/cross_check_inputs.py` (Section 5), the maintainer decides between the strict-rendering candidate and the divergent candidate. The decision is logged in `overrides.csv` with the following per-row schema:

| Column | Description |
|---|---|
| `tis1099_code` | The administrative code at which the override applies. |
| `thai_name` | The Thai-script name (the join key). |
| `strict_rendering_candidate` | The RTGS-strict or upstream-default English spelling. |
| `chosen_spelling` | The English spelling adopted in `name_en_canonical`. |
| `resolution_rule` | The rule applied (typically `government-practice-majority + international-literature-majority`). |
| `supporting_sources` | Named tables and sources that support the chosen spelling. |
| `decision_date` | ISO 8601 date the override was committed. |
| `decision_author` | The maintainer or contributor who made the call. |
| `notes` | Free-text contextual notes. |

The strict-rendering candidate also flows into `name_alternates_en`, so adopters joining on the historical or strictly-rendered spelling still find the row.

## 6.1 Worked example: ลพบุรี (TIS-16)

The Lopburi case is the founding entry in `overrides.csv` and is the only override at v1.0 ADM1. The cross-source comparison surfaces ลพบุรี as the only province where the four MIT-licensed inputs disagree:

| Source | English spelling at row TIS-16 |
|---|---|
| `thailand-geography-data` | `Loburi` |
| `kongvut/thai-province-data` | `Lopburi` |
| `GeoThai/data` v1 | `Loburi` |
| `GeoThai/data` v2 | `Loburi` |

The Tourism Authority of Thailand province directory uses `Lopburi`. The Royal Thai Government's English-language tourism content uses `Lopburi`. The English Wikipedia article is titled `Lopburi province`. International travel literature and academic publications on Thai history use `Lopburi`. The strict-rendering candidate `Loburi` is propagated across three of the four MIT-licensed input sources but is not used by the named Thai-government bodies or by the international literature.

The override adopts `Lopburi` as `name_en_canonical` and lists `Loburi` in `name_alternates_en`. The audit-trail line in `overrides.csv` carries:

- `tis1099_code = 16`
- `thai_name = ลพบุรี`
- `strict_rendering_candidate = Loburi`
- `chosen_spelling = Lopburi`
- `resolution_rule = government-practice-majority + international-literature-majority`
- `supporting_sources = TAT province directory; Royal Thai Government English tourism content; English Wikipedia "Lopburi province"; international academic publications on Thai history`
- `decision_date = 2026-05-06`
- `decision_author = William J. Reynolds (ORCID 0009-0005-1217-7465)`
- `notes = Strict rendering "Loburi" propagated across 3 of 4 MIT-licensed input sources but is not used by named Thai-government bodies or international references at the time of the v1.0 build.`

Adopters joining on the historical spelling `Loburi` find the row via `name_alternates_en`. Adopters using `name_en_canonical` get `Lopburi` for cross-source consistency with the named government tables and the international literature.

\newpage

# 7. Bangkok handling

v1.0 treats Bangkok as ADM1 row 10 with `iso_subdivision_type = "Special Administrative Area"` and a `notes`-field flag. Bangkok is administratively a เขตการปกครองพิเศษ (special administrative area) under Thai law, not a จังหวัด (province). The artifact treats it as ADM1 because the dominant downstream join pattern across Thai-government datasets and the international literature treats Thailand's 77 ADM1 units as a single set.

The trade-off is explicit. Strict adherence to Thai administrative law would split the ADM1 table into 76 provinces plus a separate Bangkok table. Strict alignment with downstream practice treats Bangkok as a peer of the 76 provinces. The artifact takes the latter path and flags the deviation in two places: the `iso_subdivision_type` column and the `notes` field. Adopters choosing to honor the legal distinction can filter on `iso_subdivision_type = "Special Administrative Area"` and partition Bangkok separately at query time.

Bangkok-specific values at v1.0 ADM1:

| Field | Value |
|---|---|
| `tis1099_code` | 10 |
| `iso_subdivision_type` | `Special Administrative Area` |
| `wikidata_qid` | `Q1861` |
| `capital` | `Bangkok` |
| `capital_th` | `กรุงเทพมหานคร` |
| `centroid_lat`, `centroid_lon` | 13.766, 100.629 |
| `area_km2` | 1,716.5 |
| `neighbors` | `11\|12\|13\|24\|73\|74` (Samut Prakan, Nonthaburi, Pathum Thani, Chachoengsao, Nakhon Pathom, Samut Sakhon) |
| `notes` | "Bangkok is administratively a special administrative area (เขตการปกครองพิเศษ), not a province. Treated as ADM1 here for compatibility with the dominant downstream join pattern." |

Bangkok requires one build-script special case: the Wikidata SPARQL query that retrieves capitals and inception dates for the other 76 provinces uses the Q50198 (province of Thailand) entity type, which does not match Bangkok. The build script handles Bangkok via a separate Wikidata Q1861 lookup for the centroid coordinates and uses the row's own name as both `capital` and `capital_th`. Other passes (polygon-derived geometry, neighbor adjacency, postal-code prefix aggregation, telephone-area-code mapping) require no Bangkok-specific branching; the Bangkok polygon, adjacency relations, postal codes, and telephone area code (`02`) all flow through the same code paths as the 76 provinces.

ADM2 and ADM3 within Bangkok do not differ from other ADM2 and ADM3 rows. Bangkok contains 50 districts (ADM2 codes 1001 through 1050) and 180 subdistricts (ADM3, distributed across the 50 districts) per `thailand-geography-data`. These ship in the ADM2 and ADM3 tables under the same schema as districts and subdistricts in other provinces. The Thai administrative term *khwaeng* used for Bangkok's subdistricts is not separately flagged in the schema; the underlying structure is captured by the TIS-1099 codes.

\newpage

# 8. Capital normalization

Wikidata returns province-capital labels via the Q50198 (province of Thailand) → P36 (capital) → label query path. Three normalization rules apply to the returned values before they populate `capital` and `capital_th` in the artifact, plus one preservation exception. The rules and the exception are implemented in `bin/build_v1_0_0.py` and exercised by the validation suite (Section 9).

## 8.1 English-side rules

**Strip the *Mueang* prefix.** Wikidata's capital-of-province entity for several provinces is the *Mueang* district that serves as the administrative center, returned with "Mueang" prefixed (e.g., `Mueang Phrae` for Phrae's capital, `Mueang Lamphun` for Lamphun's). The artifact strips "Mueang " and uses the bare place name. Phrae (TIS-54) provides the worked example in 8.3.

**Normalize spacing variants where the capital matches the province.** Wikidata sometimes returns a capital spelling that differs from the province's `name_en_canonical` only by spacing or capitalization. Examples: `Chonburi` (Wikidata) for Chon Buri (canonical) at TIS-20; `Phang Nga` (Wikidata) for Phangnga (canonical) at TIS-82. The artifact normalizes these to match the province's chosen spelling so that cross-row joins between province and capital fields stay consistent. The comparison is case-and-space-insensitive: if `wikidata_capital.replace(" ", "").lower() == province_name.replace(" ", "").lower()`, the artifact substitutes the province spelling.

**Preserve genuinely distinct capital names.** A small number of provinces have capitals that are not just the province name. Sukhothai (TIS-64) has a capital named `Sukhothai Thani`. Bangkok (TIS-10) has a capital named `Bangkok` (the self-as-capital pattern). The artifact preserves these without normalization, and the `notes` field at the affected rows carries an inline explanation. The validator's capital-vs-province-name alignment check treats these rows as REVIEW-not-FAIL findings, with the notes-field documentation as the resolution.

## 8.2 Thai-side rule

**Strip the municipality prefix.** Wikidata's capital labels in Thai prefix the municipality designation: เทศบาลนคร (city municipality), เทศบาลเมือง (town municipality), or เทศบาลตำบล (subdistrict municipality). For example, Wikidata returns `เทศบาลเมืองภูเก็ต` for Phuket's capital city. The artifact strips these prefixes via the `THAI_MUNICIPALITY_PREFIXES` constant in the build script and stores the bare place name in `capital_th` (here, `ภูเก็ต`). The Thai-side equivalent of "Mueang" (เมือง) does not need separate handling: Wikidata's Thai capital labels carry the municipality designation rather than the เมือง prefix, so the single municipality-prefix strip is sufficient.

## 8.3 Worked example: Phrae (TIS-54)

Wikidata's Q50198 → P36 query returns the following raw values for TIS-54:

| Field | Wikidata raw | After normalization | Stored in artifact |
|---|---|---|---|
| `cap_en` | `Mueang Phrae` | strip `Mueang ` → `Phrae` | `capital = Phrae` |
| `cap_th` | `เทศบาลเมืองแพร่` | strip `เทศบาลเมือง` prefix → `แพร่` | `capital_th = แพร่` |
| `name_en_canonical` | (from `thailand-geography-data`) | (no change) | `Phrae` |
| `name_th` | `แพร่` | (PyThaiNLP-normalized; no character change at this row) | `แพร่` |

After normalization, `capital` and `name_en_canonical` both read `Phrae`; `capital_th` and `name_th` both read `แพร่`. The validator's capital-against-Wikidata round-trip check confirms the consistency.

The Sukhothai (TIS-64) case sits at the other end of the rule set. The Wikidata raw `cap_en` is `Sukhothai Thani`. The Mueang-prefix rule does not apply (no `Mueang ` prefix). The spacing-variant rule does not apply (`Sukhothai Thani` is not a spacing variant of `Sukhothai`). The artifact preserves `capital = Sukhothai Thani`, and the `notes` field at TIS-64 carries: "Provincial capital is Sukhothai Thani (สุโขทัยธานี), genuinely a different name from the province itself rather than a spelling variant; preserved as-is per the capital-name normalization rule."

\newpage

# 9. Geographic computation

The geographic columns (centroids, areas, bounding boxes, distances, borders, coastlines) derive from the `mapthai` GeoJSON inputs and the Natural Earth country boundaries. The polygons themselves are bundled in the v1.0 distribution; the columns tabularize the derived values for direct CSV and Parquet consumption without requiring a polygon library at the consumer.

Computation runs at build time via `bin/build_v1_0_0.py`, using the [Shapely](https://github.com/shapely/shapely) library for polygon arithmetic and [PyProj](https://github.com/pyproj4/pyproj) for coordinate-reference-system transformations.

## 9.1 Centroids, area, and bounding box

The `centroid_lat` and `centroid_lon` columns are polygon-geometric centroids, not population-weighted. Each value is the Cartesian centroid of the row's polygon geometry from `mapthai`, computed in EPSG:4326 (WGS 84 latitude / longitude). Polygon-geometric centroids treat the polygon as a uniform-density shape and locate its center of mass. This is the standard geographic center for label placement, distance-from-center ranking, and similar tasks. It is not appropriate for computing distances between population clusters; population-weighted centroids would require a separate computation against population-grid data and lie outside the v1.0 scope.

The `area_km2` column is computed in an equal-area projection. Thailand spans UTM zones 47N (EPSG:32647) and 48N (EPSG:32648). The build script projects each polygon into the zone matching its centroid longitude (zone 47N for centroid longitude under 102°E; zone 48N otherwise), computes area in square meters under that projection, and converts to square kilometers. Cross-zone polygons (the few provinces straddling 102°E) accept small distortion. The resulting areas land within ±10% of Wikipedia infobox values for 73 of 77 provinces (95%), and Sakon Nakhon's value (9,609 km²) matches the published Royal Forest Department (RFD) figure (9,606 km²) to four significant digits. The four provinces exceeding the ±10% band — Phangnga (−34.6%), Krabi (−18.2%), Samut Songkhram (−13.8%), Samut Prakan (−13.5%) — are island-heavy or estuarine-coastal, where the RFD figure cited by Wikipedia includes administrative jurisdiction over Andaman or Gulf islands and tidal flats that the mainland-contiguous OCHA polygons do not enclose. The full per-province deviation table is published in `wikipedia_infobox_verification_report.md` alongside the data.

The `area_rai` column is derived: `area_rai = area_km2 × 625`. The conversion factor is exact (1 km² = 1,000,000 m²; 1 rai = 1,600 m²; 1,000,000 / 1,600 = 625). The area-rai derivation check enforces this cell by cell across all rows.

Bounding-box columns (`bbox_minlat`, `bbox_minlon`, `bbox_maxlat`, `bbox_maxlon`) are taken from the polygon's `.bounds` property in Shapely, which returns `(minx, miny, maxx, maxy)` in the polygon's coordinate system. The artifact stores these in EPSG:4326 (degrees), unprojected.

## 9.2 International borders and bordering countries

The `has_international_border` (boolean) and `bordering_countries` (pipe-separated) columns are computed by polygon intersection against Natural Earth's neighbor-country polygons.

The build script loads Natural Earth's `ne_50m_admin_0_countries.geojson` and extracts the polygons for Myanmar, Laos, Cambodia, and Malaysia. For each Thai province polygon, the script tests whether the province polygon intersects the buffered country polygon (buffer of 0.02 degrees, approximately 2 km). Provinces whose polygon intersects at least one country buffer carry `has_international_border = true` and the matching country names in `bordering_countries` (sorted, pipe-separated). The buffer accommodates small misalignment between the OCHA-derived Thai polygons (`mapthai`) and the Natural Earth country polygons; without the buffer, several true-bordering provinces would be missed because vertices on the international line do not exactly align between the two source polygons.

A known data-quality caveat applies. The OCHA polygon for Chanthaburi (TIS-22) and the Natural Earth Cambodia polygon disagree on a small section of the eastern border, producing an apparent overlap of approximately 197 km². The overlap is a polygon-data-vintage artifact, not territory disputed in fact; the resulting `bordering_countries = Cambodia` for Chanthaburi is accurate (Chanthaburi does border Cambodia at Khao Soi Dao), but the magnitude of the polygon overlap is misleading and would be inappropriate for territory-claim analysis. The methodology accepts this as the cost of using two independently maintained open-source polygon corpora.

At v1.0, 31 of 77 provinces carry `has_international_border = true`. Breakdown: 10 border Myanmar, 12 border Laos, 7 border Cambodia, 4 border Malaysia, with two provinces bordering two countries each (Ubon Ratchathani at TIS-34: Cambodia and Laos; Chiang Rai at TIS-57: Myanmar and Laos).

## 9.3 Coastline length

The `is_coastal` (boolean) and `coastline_length_km` (float, populated only when `is_coastal = true`) columns are derived by subtracting the international-border zone from the Thailand exterior boundary, then intersecting with each province polygon.

The procedure: load Natural Earth's Thailand polygon and take its boundary (the country exterior linestring). Subtract the union of the four buffered neighbor-country polygons; the remainder is Thailand's coastline. For each Thai province polygon, intersect that coastline with the province's buffered polygon. The intersection's length, converted from degrees to kilometers via the 111 km / degree approximation, becomes `coastline_length_km`. Provinces where the intersection length exceeds 1 km carry `is_coastal = true`.

24 provinces carry coastlines at v1.0, ranging from Bangkok's 7.9 km (the Bang Khun Thian shoreline, the smallest in the dataset) to Songkhla's 231.5 km (the longest, which combines Gulf-of-Thailand coast and the inland Songkhla Lake boundary as Natural Earth treats it). Phatthalung (TIS-93) on the western shore of Songkhla Lake is also flagged coastal under the same lake-as-polygon-hole rule; the methodology treats brackish-lake shorelines as coastline where Natural Earth represents the lake as a polygon hole in the country outline. The 111 km / degree approximation introduces small distortion at higher latitudes; for Thailand's range (5.5°N to 21°N), the maximum systematic error is under 1.5%. The methodology accepts this in exchange for not requiring a full coordinate-reference-system reprojection of every coastline-intersection step. The coastal-consistency check enforces that `is_coastal = true` iff `coastline_length_km > 0`.

## 9.4 Distance to Bangkok

The `distance_to_bangkok_km` column is the Haversine great-circle distance from each province's centroid to Bangkok's centroid (TIS-10's `centroid_lat`, `centroid_lon`). Bangkok's row carries `distance_to_bangkok_km = 0.0`.

The Haversine formula is exact on a sphere. The WGS 84 ellipsoid introduces a flattening factor of 1/298.257, producing a maximum error of approximately 0.5% at the longest distances within Thailand. For comparison-and-ranking purposes (which is the column's primary use case), this precision is adequate. The distance-to-Bangkok recomputation check recomputes the Haversine distance row by row and asserts the stored value matches within a 5 km tolerance.

\newpage

# 10. Cross-system identifiers

The artifact ships seven cross-system identifier columns at ADM1: `tis1099_code`, `iso3166_2`, `hasc`, `fips_code`, `wikidata_qid`, `geonames_id`, `osm_relation_id`, plus `wikipedia_article_url`. Each value comes from a documented external source via a documented join key. The composition pass (Section 5) populates these columns at build time from cached external responses; re-running the build offline against the cache produces a hash-checkable result.

| Column | Source | Join key | Cached at |
|---|---|---|---|
| `tis1099_code` | `thailand-geography-data.provinceCode` | (primary key) | `data/inputs/thailand-geography-data/provinces.json` |
| `iso3166_2` | computed: `TH-{tis1099_code zero-padded to 2 digits}` | (derived) | (no external dependency) |
| `hasc` | Statoids HTML table for Thailand | English province name → row | `data/inputs/statoids/uth.html` |
| `fips_code` | Statoids HTML table for Thailand | English province name → row | `data/inputs/statoids/uth.html` |
| `wikidata_qid` | Wikidata SPARQL: `?p wdt:P31 wd:Q50198. ?p wdt:P300 ?iso` (76 rows) plus `Q1861` for Bangkok | `iso3166_2` (Bangkok by direct lookup) | `data/inputs/wikidata/wd_provinces_modern.json` |
| `geonames_id` | GeoNames `admin1CodesASCII.txt` (Thailand subset, 77 rows) | `fips_code` (GeoNames admin1 codes are FIPS-derived, not TIS-1099) | `data/inputs/geonames/admin1CodesASCII.txt` |
| `osm_relation_id` | OpenStreetMap Nominatim search | `q={province name} Province, Thailand` | `data/inputs/computed/osm_relations.json` |
| `wikipedia_article_url` | Wikipedia API article fetch with redirects enabled | `titles={name} province` (lowercase) | `data/inputs/wikipedia/wikipedia_articles.json` |

Each source carries notes worth understanding before consuming the columns.

**[Statoids](https://statoids.com/uth.html)** is Gwillim Law's province-codes reference (Law, n.d.) maintained at `statoids.com`. The Thailand page is the canonical HASC and FIPS source for Thai provinces. The site is stable but not actively maintained; the build script's HTML-table parser is loose enough to tolerate minor markup changes and strict enough to reject malformed responses.

**Wikidata** queries the public SPARQL endpoint at `query.wikidata.org/sparql`. The Q50198 (province of Thailand) entity type returns 76 of 77 provinces; Bangkok carries Q1861 (capital city of Thailand and special administrative area), which the Q50198 query does not match. The build script handles Bangkok via a separate Q1861 lookup and merges the two responses by `tis1099_code`. Wikidata data is CC0; attribution lives in the references list rather than the data file.

**GeoNames** publishes `admin1CodesASCII.txt` containing first-level administrative subdivisions globally. The 77 Thai rows use the format `TH.NN`, where `NN` is the FIPS PUB 10-4 code, not TIS-1099. The build script reads `fips_code` from Statoids first, then joins to GeoNames via the FIPS code to find the numeric `geonames_id`. Joining on TIS-1099 directly would fail because GeoNames does not carry TIS-1099 codes.

**[OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/)** is queried with `q="{province} Province, Thailand"` and `format=json&limit=3`. The Nominatim usage policy requires a maximum of 1 request per second; the build script enforces a 1.05-second delay between calls. 76 of 77 provinces return an OSM relation (the canonical type for administrative boundaries). One province (Phangnga, TIS-82) returns a non-relation type at v1.0 and ships with `osm_relation_id` empty. Community correction via the GitHub channel is expected to populate this row in a patch release.

**Wikipedia** article URLs derive from Wikipedia API responses. The query searches for `{name} province` (lowercase "province" matches Wikipedia's canonical title style for Thai provinces). Some queries hit redirects (`Phuket Province` redirects to `Phuket province`); the API's `redirects=1` flag follows them and returns the canonical title. The stored URL is `https://en.wikipedia.org/wiki/{title with spaces replaced by underscores}`.

## 10.1 Worked example: Phuket (TIS-83)

Phuket end-to-end identifier resolution at v1.0:

| Column | Value | How resolved |
|---|---|---|
| `tis1099_code` | 83 | `thailand-geography-data/provinces.json`: row with `provinceCode = 83` |
| `iso3166_2` | `TH-83` | computed: `TH-` + zero-padded `tis1099_code` |
| `hasc` | `TH.PU` | Statoids table row: `Phuket` → `TH.PU` |
| `fips_code` | `TH62` | Statoids table row: `Phuket` → FIPS column = `TH62` |
| `wikidata_qid` | `Q182565` | Wikidata SPARQL `?p wdt:P31 wd:Q50198. ?p wdt:P300 "TH-83"` returns `Q182565` |
| `geonames_id` | 1151253 | GeoNames admin1 row `TH.62` → `geonameid = 1151253`. Joined via FIPS `TH62` |
| `osm_relation_id` | 2934604 | Nominatim search `Phuket Province, Thailand` → first relation result, `osm_id = 2934604` |
| `wikipedia_article_url` | `en.wikipedia.org/wiki/Phuket_province` | Wikipedia query `Phuket province` with redirects enabled returns canonical title `Phuket province` |

The chain is fully deterministic. Re-running the build script offline against the cached inputs produces the same eight values for TIS-83.

\newpage

# 11. Operational lookups

The artifact ships four operational-lookup columns at ADM1: `postal_code_prefixes`, `telephone_area_codes`, `num_amphoe`, `num_tambon`. Each comes from a documented source via a documented derivation. These columns serve consumers doing address-bucketing, phone-number routing, count-aggregation validation, and admin-level navigation.

| Column | Source | Derivation |
|---|---|---|
| `postal_code_prefixes` | `thailand-geography-data` subdistricts.json `postalCode` field | Group all subdistrict postal codes by province; take first 2 digits; deduplicate; sort; pipe-join |
| `telephone_area_codes` | [Wikipedia "Telephone numbers in Thailand"](https://en.wikipedia.org/wiki/Telephone_numbers_in_Thailand) "Geographic area codes" section | Parse the area-code → province table; reverse-index to province → area-codes; pipe-join sorted codes per province |
| `num_amphoe` | `thailand-geography-data` districts.json | Count districts per `provinceCode` |
| `num_tambon` | `thailand-geography-data` subdistricts.json | Count subdistricts per `provinceCode` |

**Postal code prefixes.** Thai postal codes are 5 digits. The first 2 identify a province; the remaining 3 identify the local sorting facility within the province. The build script reads every subdistrict's 5-digit `postalCode`, groups by `provinceCode`, takes the 2-digit prefix, deduplicates, sorts, and joins with `|`. Most provinces have a single prefix matching their TIS-1099 code (Phuket TIS-83 → prefix `83`). A few carry multiple prefixes due to upstream data-source attribution quirks (Chiang Mai's row carries `50|58` because some northern subdistricts attributed to Chiang Mai in `thailand-geography-data` carry 58-prefix postal codes; this is a known artifact of the upstream attribution and is preserved unchanged in v1.0).

**Telephone area codes.** Thailand's fixed-line area codes are 2 to 3 digits with a leading zero. The `02` code covers Bangkok plus four neighbor provinces (Nonthaburi, Pathum Thani, Samut Prakan, plus the Phutthamonthon area of Nakhon Pathom). Other codes (032, 034, 035, etc.) cover groups of three to four provinces each. Multiple provinces can share one code, and one province can carry multiple codes. The build script parses the Wikipedia area-code table, builds a province-to-code reverse index, and pipe-joins sorted codes per province. 77 of 77 provinces resolve via this method at v1.0.

**Administrative subunit counts.** `num_amphoe` is the count of ADM2 rows whose parent province equals the row's `tis1099_code`. `num_tambon` is the same count at ADM3. The sums across the ADM1 table equal the totals published by Thailand's Department of Provincial Administration: 928 amphoe and 7,436 tambon. The validator's admin-counts statistical-sanity check enforces these totals fall within published-range tolerances. Bangkok's counts (50 districts, 180 subdistricts) match Bangkok Metropolitan Administration figures.

## 11.1 Worked example: Nakhon Pathom (TIS-73)

Nakhon Pathom illustrates the multi-area-code pattern that single-area-code provinces do not show:

| Column | Value | Source detail |
|---|---|---|
| `postal_code_prefixes` | `73` | All Nakhon Pathom subdistricts in `thailand-geography-data` carry postal codes starting `73`. Single prefix. |
| `telephone_area_codes` | `02\|034` | Wikipedia: `02` covers the Phutthamonthon area (Bangkok-suburban integration); `034` covers the rest of Nakhon Pathom. Both codes reverse-index to TIS-73. |
| `num_amphoe` | 7 | `thailand-geography-data`: 7 districts under provinceCode 73. |
| `num_tambon` | 109 | `thailand-geography-data`: 109 subdistricts under provinceCode 73. |

The pipe-joined `telephone_area_codes` field allows downstream consumers to do exact-match lookups for either code. A phone-routing system fielding an `034`-prefix call can map to TIS-73 for province-level enrichment without further normalization.

\newpage

# 12. Update cadence

The artifact follows an annual-baseline-plus-change-event release cadence. Annual baseline releases ship once per year, calendar-aligned to the publication of the National Statistical Office (NSO) *Statistical Yearbook* (typically October through December). Change-event releases ship between annual baselines whenever a documented government boundary change requires immediate update. Patch releases ship asynchronously to address community-submitted corrections.

The cadence reflects two operational realities. Thai government boundary changes at ADM1 are rare; the 2011 creation of Bueng Kan Province is the only ADM1 boundary event in the past three decades. A quarterly or more frequent cadence would not match underlying-data churn. Identifier and reference data also changes occasionally; Wikidata QIDs migrate, OSM relation IDs occasionally renumber, the GeoNames admin1Codes file gets refreshed, and Wikipedia URLs sometimes redirect to renamed articles. An annual sweep against cached external sources catches these without burdening the maintenance workflow.

## 12.1 Annual baseline procedure

The maintainer runs the annual baseline release in October or November, after the NSO *Statistical Yearbook* publishes for the year:

1. Re-fetch all upstream MIT-licensed sources (`thailand-geography-data`, `kongvut`, `GeoThai`, `mapthai`, `pmdscully`) to refresh the cache at `data/inputs/`.
2. Re-fetch external identifier sources (Wikidata SPARQL, Statoids, GeoNames, Nominatim, Wikipedia article URLs) and update cached responses.
3. Run the build script (`bin/build_v{version}.py`) to regenerate the per-level CSV and Parquet outputs.
4. Run the validator and the mutation test suite. All checks must pass before release.
5. Diff the new output against the prior version. Document material changes in `CHANGELOG.md`.
6. Increment the version per Section 13.
7. Mint a new Zenodo deposit linked to the prior concept-DOI.

Annual baselines are the only release type that deliberately re-fetches upstream sources. Patch and change-event releases work against cached inputs unless the change-event explicitly requires fresh upstream data.

## 12.2 Change-event releases

A change-event release is triggered when a Thai government instrument (Royal Decree, Royal Gazette publication, Revolutionary Council Announcement, or Act of Parliament) creates, dissolves, or renames an administrative unit. The procedure differs from an annual baseline in two respects. First, the maintainer authors a row in `historical_mappings.csv` documenting the boundary event before any data work begins; this row carries the audit-trail line for the change. Second, only the directly affected upstream sources are re-fetched; the others run against cached inputs to isolate the change.

A worked example traces from the 2011 Bueng Kan event. If the artifact had existed at v1.0 in early 2011, the change-event release for the Act Establishing Changwat Bueng Kan, BE 2554 (Royal Gazette publication 22 March 2011, effective 23 March 2011) would have:

1. Added a row to `historical_mappings.csv` with `event_type = province_split`, `effective_date = 2011-03-23`, `parent_tis1099_code = 43` (Nong Khai), `child_tis1099_code = 38` (Bueng Kan), citation to the Act with its Royal Gazette entry, and notes naming the eight districts transferred.
2. Re-fetched `thailand-geography-data` to confirm the new TIS-1099 code 38 and the eight transferred districts had been added upstream.
3. Added a new ADM1 row for Bueng Kan with `predecessor_tis1099_code = 43` and `established_year = 2011` (a CONFIRMED entry sourced to the Act).
4. Updated Nong Khai's `num_amphoe`, `num_tambon`, and polygon-derived geography to reflect the loss of the eight districts.
5. Updated the `neighbors` column on every province bordering Nong Khai or Bueng Kan.
6. Re-run the validator. Mint a minor-version Zenodo deposit.

## 12.3 Patch releases

Patch releases address community-submitted corrections via GitHub issues and pull requests. Typical patch content: spelling additions to `name_alternates_en`, corrections to existing spelling decisions with an updated audit-trail line in `overrides.csv`, centroid corrections at ADM2 or ADM3 where polygon-derived values surface as wrong, and established_year additions where Royal Gazette archive verification becomes available for previously-PARTIAL entries.

Patch-release timing is asynchronous. Corrections ship in batched patch releases approximately monthly when the queue has at least one merged correction. The patch version number increments per Section 13.

\newpage

# 13. Versioning convention

The artifact uses semantic versioning (`major.minor.patch`) per [SemVer 2.0.0](https://semver.org/) with adaptations for data-product releases. Each version triplet maps to a Zenodo deposit with its own DOI; Zenodo's concept-DOI links version-specific DOIs into a single citable lineage.

| Version bump | Triggered by | Zenodo behavior |
|---|---|---|
| Major (`x.0.0`) | Schema-breaking change: removing a column, renaming a column, narrowing a column's data type, removing an administrative level | Each major version is a separate Zenodo concept-DOI. Major versions do not inherit downstream-consumer compatibility. |
| Minor (`1.x.0`) | Additive schema change (new column), new ADM level addition, change-event release that adds rows or columns, methodology revision that does not break existing column contracts | Each minor version is a new deposit under the same concept-DOI. The concept-DOI automatically resolves to the latest minor. |
| Patch (`1.0.x`) | Spelling correction, override-rule audit-trail edit, centroid correction, `established_year` promotion from PARTIAL to CONFIRMED, documentation-only update | Each patch is a new deposit under the same concept-DOI. Patches preserve byte-level consumer compatibility for unchanged rows. |

**Schema-breaking change rule.** Removing or renaming a column, narrowing a column's type, or changing the meaning of a column's content (for example, redefining `area_km2` from province area to province-plus-coastal-water area) constitutes a major-version bump. Adding a column, broadening a column's type (`int` to `bigint`, for example), adding new rows, and amending the `notes` field do not break consumers and ship as minor or patch updates.

**Zenodo concept-DOI relationship.** Each release is a separate Zenodo deposit with its own DOI. The first deposit at v1.0.0 establishes a concept-DOI that resolves to the latest version regardless of which version is current. Subsequent deposits register as new versions under the same concept. Citations using the concept-DOI dereference to the latest version automatically; citations using a version-specific DOI pin to that exact release. The recommended citation style for academic use is the version-specific DOI when reproducibility matters and the concept-DOI when the citing document refers to the artifact in general.

## 13.1 Worked example: hypothetical version sequence

A worked example from v1.0.0 forward illustrates how version bumps map to release content:

| Version | Release type | Hypothetical content |
|---|---|---|
| `1.0.0` | Initial release | First public release at all three administrative levels with bundled polygons. Concept-DOI minted on Zenodo. |
| `1.0.1` | Patch | Two community-submitted spelling corrections at ADM3 (Loburi-style override resolutions at two tambon rows). `overrides.csv` updated, CSV/Parquet outputs regenerated, new version-specific DOI under the same concept-DOI. |
| `1.1.0` | Minor | `established_year` column promoted to CONFIRMED for two previously-PARTIAL provinces (Sa Kaeo 1993, Amnat Charoen 1993) after Royal Gazette archive verification by a Thai-language community contributor. `established_years.csv` rows amended. New version-specific DOI. |
| `1.2.0` | Minor | Annual baseline at end of calendar 2026: upstream sources re-fetched, Wikidata SPARQL response refreshed, Wikipedia article URLs refreshed (one redirect change at TIS-49 Mukdahan), validation report updated. New version-specific DOI. |
| `1.3.0` | Minor | Hypothetical change-event: a Royal Decree creates a new ADM2 district from a tambon merger. ADM2 row added; ADM3 rows updated to reflect new parent district code; `historical_mappings.csv` row added documenting the event. New version-specific DOI. |
| `2.0.0` | Major | Schema-breaking change: ADM3 schema gains four new columns and `centroid_lat` / `centroid_lon` precision narrows from 5 decimal places to 4 (consumers parsing as fixed-precision strings would break). New concept-DOI; v1.x consumers are not automatically migrated. |

The concept-DOI for `v1.x.y` resolves to the latest 1.x.y release. The concept-DOI for `v2.x.y` is separate. Pinning citations to specific version DOIs supports reproducibility for academic consumers; pinning to the concept-DOI supports general references.

\newpage

# 14. License posture

The artifact uses three licenses across its file types: Creative Commons Attribution 4.0 International (CC BY 4.0) on the data tables and methodology document, MIT on the build code and validator, and per-file upstream licenses on bundled polygon files. The layered posture is documented in `NOTICE.md` at the artifact root.

| Asset | License | Justification |
|---|---|---|
| Data tables (CSV, Parquet at all three ADM levels) | CC BY 4.0 | Reference-data genre convention (matches ISO 3166-2 community releases, GeoNames, pycountry). |
| Methodology document (this PDF) | CC BY 4.0 | Documentary content; supports academic citation and reuse. |
| Override registry (`overrides.csv`) | CC BY 4.0 | Audit-trail metadata layered on the data. |
| Historical mappings (`historical_mappings.csv`) | CC BY 4.0 | Same. |
| Established-years registry (`established_years.csv`) | CC BY 4.0 | Same. |
| Build script (`bin/build_v{version}.py`) | MIT | Code license; permissive default for derivative tools. |
| Validator and test suite (`bin/validate_*.py`, `bin/test_*.py`) | MIT | Same. |
| Cross-check script (`bin/cross_check_inputs.py`) | MIT | Same. |
| `mapthai`-derived GeoJSON files (bundled at all three ADM levels) | CC BY 3.0 IGO (under OCHA CODs) | Inherits OCHA Common Operational Datasets license; not relicensed by this artifact. |
| HDX RTSD shapefiles (bundled) | CC BY 3.0 IGO under OCHA CODs framework | Original publication license preserved. |

**Why CC BY 4.0 on the data.** Reference-data licenses in this genre are permissive (ISO 3166-2 community releases, GeoNames, pycountry). Locking commercial reuse out would push commercial adopters back to private lists, which is the gap this artifact addresses. The CC BY 4.0 posture preserves the citation requirement (which surfaces back to the methodology and override registry) while removing the commercial-gating barrier that would defeat adoption.

**MIT on build code, CC BY 4.0 on data.** Mixed-license repositories are conventional. Code under MIT permits forking and reuse without burden; data under CC BY 4.0 requires attribution but permits commercial use. The repository's `LICENSE` file resolves to MIT for code; the `LICENSE-DATA` file specifies CC BY 4.0 for data and methodology; the `NOTICE.md` file consolidates per-file license claims and upstream attribution chains.

**Layered licensing on bundled polygons.** The polygons originate from OCHA CODs (Common Operational Datasets), which carry CC BY 3.0 IGO. The artifact does not relicense these files. Consumers using the `mapthai`-derived GeoJSON or the HDX RTSD shapefiles must comply with CC BY 3.0 IGO terms (attribution to OCHA and the originating Thai government body, no implied endorsement). The `NOTICE.md` file at the artifact root carries the full upstream attribution chain. Data tables, override registry, methodology PDF, and code are unaffected by the layered polygon licensing because they are independent files under their own licenses.

## 14.1 Worked example: a downstream consumer's compliance checklist

A downstream consumer using the artifact in a commercial product would, at minimum, comply with the following per asset:

| What they used | License obligation |
|---|---|
| Data tables (CSV / Parquet) | Cite the artifact per CC BY 4.0 using the Zenodo deposit DOI; indicate any modifications; link to the license. |
| Methodology document | Cite the methodology document per CC BY 4.0 using the Zenodo deposit DOI; indicate any modifications. |
| Build script | Preserve the MIT copyright notice and license text in derivative tools. |
| `mapthai`-derived GeoJSON polygons | Attribute OCHA, `mapthai` (Chitchumnong, n.d.), and Natural Earth where applicable. Comply with CC BY 3.0 IGO. |
| HDX RTSD shapefiles | Attribute the Royal Thai Survey Department and OCHA. Comply with CC BY 3.0 IGO. |

Consumers using only the tabular CSV / Parquet outputs and the methodology document interact with a single license (CC BY 4.0). Consumers loading the bundled polygons inherit the layered obligation. The artifact's `NOTICE.md` carries the canonical attribution language consumers can copy directly into their own attribution sections.

\newpage

# 15. Community review and corrections

The artifact uses post-publication community review via GitHub issues and pull requests in place of named pre-publication peer review. The model matches genre precedent (pycountry, ISO 3166-2 community releases, GeoNames) and is appropriate for a single-maintainer reference-data project where the methodology is documentary rather than analytical.

Maintainer review of issues happens within four weeks of submission. Pull requests get reviewed in the next monthly patch cycle (Section 12).

## 15.1 Why community review, not pre-publication peer review

Pre-publication peer review is a journal-publishing pattern. It works when an artifact has a single authoritative author, a fixed length, and a publication moment after which corrections become expensive. Reference-data artifacts have neither of those properties: maintenance is continuous and patch releases are cheap. Authority comes from documented sources rather than author credentials.

Community review post-publication serves the same goal of surfacing errors, contesting overrides, expanding alternates, and verifying claims. The work distributes across the user base over time rather than concentrating with a single reviewer. The validator and test suite (Section 9) prevent regressions: any pull request that breaks an existing check fails continuous integration before merge.

## 15.2 Contribution channels

Four issue templates plus a pull-request template cover the typical contribution shapes:

| Template | Purpose | Maintainer action |
|---|---|---|
| Spelling correction | Propose a different `name_en_canonical`, `name_alternates_en` addition, or capital-name fix | Verify against named government tables; update `overrides.csv` with audit-trail line; merge in next patch release |
| Verification upgrade | Promote an `established_year` from PARTIAL to CONFIRMED with a primary-source citation (Royal Gazette publication, Royal Decree, etc.) | Verify the cited source; update `established_years.csv` `verification_status` column from PARTIAL to CONFIRMED; the value flows to the main table on next build |
| Polygon-derived correction | Surface `centroid_lat`/`centroid_lon`, `area_km2`, `bbox_*`, or `coastline_length_km` values that diverge materially from authoritative sources | Re-run polygon computation with verification; document in `notes` if upstream polygon vintage is the cause |
| Methodology clarification | Question or correction request against the methodology PDF or `NOTICE.md` | Respond in the issue thread; pull-request an amendment if the issue surfaces a real ambiguity |
| Pull request | Direct edit to data, registry, code, or documentation files | Review for accuracy and brand-voice compliance; merge when CI passes and content is correct |

The contribution flow uses standard GitHub mechanics. An issue is opened, labeled by the maintainer or by automated triage, assigned a milestone (next patch release or annual baseline), and closed when the corresponding pull request merges or when the maintainer decides not to act with a documented reason. Issue authors retain edit rights on their submissions.

## 15.3 Worked example: a community-submitted spelling correction

A community contributor opens an issue against the `name_alternates_en` column at TIS-31 (Buri Ram), proposing the addition of `Buriram` (no space) as an alternate spelling alongside `Buri Ram` (the chosen spelling).

The contribution flow:

1. Issue opened with the spelling-correction template. Title: "Add 'Buriram' as an alternate at TIS-31 (Buri Ram)". Body cites four downstream datasets (a real-estate platform, an academic paper, a Thai-news website, and a transit timetable) using the no-space form.
2. Maintainer triages within one week. Verifies that the cited sources do use `Buriram`. Confirms that adding the alternate does not collide with another row's `name_en_canonical`.
3. Maintainer comments on the issue with a planned patch-release entry. No override is needed because the chosen spelling does not change; only `name_alternates_en` updates.
4. Pull request opened by the maintainer or the contributor: changes `name_alternates_en` at TIS-31 from empty to `Buriram`. Validator runs in continuous integration; the alternates-format check passes.
5. PR merges. The next monthly patch release ships v1.0.x with the updated alternate. Adopters joining on `Buriram` find the row.

The contribution flow took approximately two weeks from issue submission to patch release. The audit trail lives in the GitHub issue, the merge commit, and the changelog entry for the patch version.

\newpage

# 16. Limitations

This section aggregates the limitations and caveats specified throughout the methodology into a single dedicated location, per voice-guide convention for major data notes. Adopters should read this section in full before relying on the artifact for any high-stakes use.

## 17.1 Coverage limitations

| Column | v1.0 coverage | Gap | Consequence for downstream use |
|---|---|---|---|
| `established_year` | 4 of 77 (CONFIRMED) | 5 rows are PARTIAL (Sa Kaeo 1993, Amnat Charoen 1993, Nong Bua Lam Phu 1993, Chiang Mai 1910, Lampang 1892); 68 rows have no defensible modern establishment year | Empty cell means "no primary source verified," not "no establishment occurred." See Section 6. |
| `name_alternates_en` | 50 of 77, 71 total alternates | The 27 provinces without alternates are single-word canonicals (Phuket, Trat, Krabi, Yala, Surin, etc.) with no spacing-variant possible and no historical or transliteration variant in Wikidata aliases or Wikipedia redirects. Multi-word canonicals carry the no-space variant (Chon Buri / ChonBuri, Mae Hong Son / MaeHongSon). "Buri"-suffix canonicals carry the split / merged form (Lopburi / Lop Buri, Sing Buri / Singburi, Phetchaburi / Phet Buri). Historical and transliteration variants surface where they exist (Bangkok / Krung Thep / Bang Makok; Nakhon Ratchasima / Khorat / Korat). Some Wikipedia-redirect typo variants are preserved (Lampang / Lambang, Buri Ram / Burirum) for join-completeness. | Adopters joining on alternate spellings — the no-space form, the "-buri" split or merged form, the historical or transliteration variant, or a documented typo redirect — find the row. Rows without alternates require canonical-spelling joins. The community-corrections channel (Section 15) is the path for adding newly-surfaced alternates. |
| `osm_relation_id` | 76 of 77 | Phangnga (TIS-82) returned a non-relation OpenStreetMap type at v1.0 | Adopters joining to OSM data via this column will miss Phangnga. Community correction expected via patch release (Section 12). |
| `num_muban` (village count) | Not shipped at v1.0 | Pending DOPA Local Administration Department extraction | Consumers needing village-level structure must source separately. |
| `num_thesaban` (municipality count) | Not shipped at v1.0 | Same as above | Same. |
| ADM2 and ADM3 cross-source verification | Single-source from `thailand-geography-data` | Cross-source comparison and override registry not in scope at v1.0 | ADM2 and ADM3 spelling carries the upstream's choice unchanged. Patch releases extend cross-checking as community submissions arrive. |

## 17.2 Methodological caveats

The geographic-computation methodology (Section 9) carries several caveats with quantified consequence:

- **Centroids are polygon-geometric, not population-weighted.** Use for label placement and rough geographic ranking. Do not use for population-cluster distance calculations or for purposes requiring population-aware geographic centers.
- **Areas use UTM zones 47N (EPSG:32647) and 48N (EPSG:32648).** Cross-zone polygons accept small distortion. Computed areas land within ±10% of Wikipedia infobox values for tested provinces, with Sakon Nakhon matching the published Royal Forest Department figure to four significant digits.
- **Coastline length uses the 111 km / degree approximation.** Maximum systematic error within Thailand's latitude range is under 1.5%. Use for ranking and rough estimation; do not use for navigation-grade calculations.
- **Distance to Bangkok uses the Haversine formula on a sphere.** WGS 84 ellipsoid distortion produces a maximum error of approximately 0.5% at the longest distances within Thailand. Adequate for ranking; not adequate for purposes requiring sub-percent precision.
- **International-border detection uses a 0.02° (~2 km) buffer.** The Chanthaburi-Cambodia polygon-vintage disagreement produces an apparent 197 km² overlap that is a drawing artifact, not a territorial dispute. The boolean `has_international_border = true` for Chanthaburi is accurate; the overlap magnitude is not interpretable as territory.
- **Postal-code prefix attribution.** Chiang Mai's row carries `50|58` because some upstream subdistricts attributed to Chiang Mai use 58-prefix postal codes. The artifact preserves the upstream attribution unchanged at v1.0.

## 17.3 Source-availability risks

- **Statoids** is the canonical HASC and FIPS source. The site is stable but not actively maintained. The cached HTML at `data/inputs/statoids/uth.html` survives any upstream outage. A future contributor seeking to refresh the cache would need an alternate source if Statoids goes offline; no alternate has been identified at v1.0.
- **Wikipedia** article URLs are subject to rename redirects. The build script's `redirects=1` flag handles current redirects transparently. A future article rename would update on the next annual baseline.
- **Wikidata** SPARQL queries depend on the continued availability of the P31, P300, P36, and P571 properties on Thai-province entities. Wikidata schema changes at this level are rare but not impossible.
- **`mapthai` polygon licensing.** The MIT package wraps OCHA CODs CC BY 3.0 IGO data. License layering is documented in `NOTICE.md`; consumers using the bundled polygons inherit the IGO terms.

## 17.4 Maintainer risk

The artifact has a single maintainer at v1.0. No formal succession plan is in place. If the maintainer becomes unavailable, the cached inputs and the build scripts allow a successor to regenerate releases against existing data, but ongoing community-correction triage and Royal Gazette monitoring would lapse without an active maintainer. The methodology recommends recruiting a co-maintainer before v1.1 and adding a maintainer-succession procedure to `CONTRIBUTING.md`.

## 17.5 Out of scope

The following are deliberately out of scope at v1.0 and have no firm timeline for inclusion:

- Editorial commentary, per-province lifestyle context, and tourism-narrative content
- Time-varying operational data (current population, current GPP, current governor)
- Muban (village, ADM4) records; the lowest level included is tambon
- Thai-language methodology document at v1.0; data tables carry Thai-script columns, but this methodology document is English-only
- License-plate codes (Thai vehicle plates use the full Thai province name on the plate rather than a discrete short code, as discussed in the operational-lookups section)

\newpage

# 17. References

References follow APA 7 conventions. Software, datasets, government instruments, and reference websites are listed alphabetically. Entries with hanging-indent rendering will appear correctly in the typeset PDF; this markdown source uses single-paragraph entries for clarity.

## How to cite this artifact

Reynolds, W. J. (2026). *Thailand Canonical Administrative-Names Reference* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.20049930

The DOI above is the **concept DOI** — it always resolves to the latest published version. Cite a version-specific DOI (visible on each Zenodo deposit page under "Versions") when reproducibility against a particular release matters.

## External references


Chitchumnong, P. (n.d.). *mapthai: An R package storing lightweight polygon data of Thailand* [R package]. https://github.com/piyayut-ch/mapthai

Department of Provincial Administration. (n.d.). *Provincial English-name release*. Ministry of Interior, Thailand. https://www.dopa.go.th/

GeoNames. (n.d.). *admin1CodesASCII.txt: First-level administrative subdivisions* [Data set]. http://download.geonames.org/export/dump/admin1CodesASCII.txt

Government of Thailand. (1972). *Announcement of the Revolutionary Council No. 70 dated 6 February 1972* [Government instrument]. Royal Thai Government Gazette. https://en.wikisource.org/wiki/Translation:Announcement_of_the_Revolutionary_Council_No._70_dated_February_6,_1972

Government of Thailand. (1977). *Phayao Province Act, B.E. 2520 (1977)* [Royal Decree]. Royal Thai Government Gazette.

Government of Thailand. (1982). *Royal Decree elevating Mukdahan to provincial status, B.E. 2525 (1982)* [Royal Decree]. Royal Thai Government Gazette.

Government of Thailand. (2011). *Act Establishing Changwat Bueng Kan, B.E. 2554 (2011)* [Government instrument]. Royal Thai Government Gazette, 128(45 A), 1–8. https://en.wikisource.org/wiki/Act_Establishing_Changwat_Bueng_Kan,_BE_2554_(2011)

Humanitarian Data Exchange. (n.d.). *Thailand: Subnational administrative boundaries* [Data set]. United Nations Office for the Coordination of Humanitarian Affairs (OCHA). https://data.humdata.org/dataset/cod-ab-tha

Kelso, N. V., & Patterson, T. (n.d.). *Natural Earth: 1:50m cultural vectors* [Data set]. https://github.com/nvkelso/natural-earth-vector

Law, G. (n.d.). *Statoids: Provinces of Thailand*. https://statoids.com/uth.html

National Statistical Office of Thailand. (2025). *Statistical Yearbook of Thailand 2025*. Ministry of Digital Economy and Society. https://www.nso.go.th/

OpenStreetMap Foundation. (n.d.). *OpenStreetMap Nominatim API*. https://nominatim.openstreetmap.org/

PyProj contributors. (n.d.). *PyProj: Python interface to PROJ (cartographic projections and coordinate transformations library)* [Software]. https://github.com/pyproj4/pyproj

PyThaiNLP. (2024). *PyThaiNLP: Thai Natural Language Processing in Python* [Software]. https://github.com/PyThaiNLP/pythainlp

Royal Society of Thailand. (n.d.). *Royal Thai General System of Transcription*. http://www.royin.go.th/

Sangkla, K. (2025). *thai-province-data: Province, district, and subdistrict data of Thailand* [Data set]. https://github.com/kongvut/thai-province-data

Scully, P. M. D. (2021). *Thailand Province Border Adjacency Mappings* [Data set]. https://github.com/pmdscully/thailand_province_border_adjacency

Semantic Versioning Initiative. (2013). *Semantic Versioning 2.0.0*. https://semver.org/

Shapely contributors. (n.d.). *Shapely: Manipulation and analysis of geometric objects* [Software]. https://github.com/shapely/shapely

Takara, J. (2023). *thailand-geography-json: Geographic data of Thailand* [Data set]. https://github.com/thailand-geography-data/thailand-geography-json

Tourism Authority of Thailand. (n.d.). *Province directory*. https://www.tourismthailand.org/

Wikidata contributors. (n.d.). *Wikidata*. Wikimedia Foundation. https://www.wikidata.org/

Wikipedia contributors. (n.d.). *English Wikipedia*. Wikimedia Foundation. https://en.wikipedia.org/

## Suggested citation for this artifact

Adopters citing the artifact in academic or professional work should use the version-specific Zenodo DOI when reproducibility matters and the concept-DOI when the citation refers to the artifact in general (see Section 13). The recommended citation format at v1.0.0:

> Reynolds, W. J. (2026d). *Thailand Canonical Administrative-Names Reference* (Version 1.0.0) [Data set and methodology]. Zenodo. https://doi.org/[Zenodo DOI to be minted at release]

The references section will be updated to include the self-citation entry (Reynolds, 2026d) once the Zenodo deposit at v1.0.0 mints its DOI.
