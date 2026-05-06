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
