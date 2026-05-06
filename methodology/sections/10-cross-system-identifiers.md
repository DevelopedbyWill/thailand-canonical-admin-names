# 10. Cross-system identifier mappings

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
