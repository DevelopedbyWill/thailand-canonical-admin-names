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
