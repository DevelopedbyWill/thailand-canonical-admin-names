# Thailand Canonical Administrative-Names Reference

> Canonical English and Thai names for Thailand's 77 provinces, with TIS-1099 codes, ISO 3166-2 codes, alternates, capitals, regions, established years, centroids, and a documented override rule. Published with a methodology PDF and a Zenodo DOI under CC BY 4.0.

**Status:** Pre-release foundation, working toward v1.0.0 in Q3 2026.
**Maintainer:** William J. Reynolds ([ORCID: 0009-0005-1217-7465](https://orcid.org/0009-0005-1217-7465))
**Part of:** [Thailand Livability Index (TLI)](https://thailand-livability-index.com)
**License:** CC BY 4.0 on the data and methodology. MIT on the build code.

---

## What this is

A defended canonical reference for Thai administrative-division names and codes. The Thai data ecosystem has multiple high-quality MIT-licensed name lists (`thailand-geography-data`, `kongvut/thai-province-data`, `GeoThai/data`), but none documents:

- The source-authority order behind chosen English spellings
- An audit trail per override
- Capitals (English and Thai)
- The year each province was constituted
- Alternate English spellings for join-friendliness
- A separate historical-mapping table (Bueng Kan / Nong Khai 2011 split)
- Centroid lat/long
- A peer-reviewable methodology PDF

This artifact composites those upstream sources, layers the methodology, and publishes the result under CC BY 4.0 with a Zenodo DOI.

## Schema (v1.0.0 draft)

| Column | Type | Description |
|---|---|---|
| `tis1099_code` | int | Thai Industrial Standard 1099 numeric code (e.g., `10` for Bangkok) |
| `iso3166_2` | string | ISO 3166-2 code (e.g., `TH-10`) |
| `name_en_canonical` | string | Recommended English spelling per the override rule |
| `name_th` | string | Thai-script name (PyThaiNLP-normalized) |
| `name_alternates_en` | string | Pipe-separated alternate English spellings |
| `region` | string | Six-region grouping |
| `capital` | string | Provincial capital, English |
| `capital_th` | string | Provincial capital, Thai |
| `established_year` | int | Year the province was constituted |
| `centroid_lat` | float | Polygon centroid latitude (decimal degrees) |
| `centroid_lon` | float | Polygon centroid longitude (decimal degrees) |
| `notes` | string | Edge-case documentation (e.g., Bangkok's special-administrative-area status) |

## Files

- `data/v1.0.0/thailand-adm-names-v1.0.0.csv` — primary distribution
- `data/v1.0.0/thailand-adm-names-v1.0.0.parquet` — fast-binary distribution
- `data/historical_mappings.csv` — boundary-change history (Bueng Kan / Nong Khai 2011 split)
- `data/overrides.csv` — audit log of every spelling override
- `methodology/thailand-canonical-names-methodology-v1.0.0.pdf` — full methodology document with APA 7 citations

## Citation

Once Zenodo deposit is minted at v1.0.0:

> Reynolds, W. J. (2026). *Thailand Canonical Administrative-Names Reference* (Version 1.0.0) [Data set]. Zenodo. https://doi.org/[TBD]

## Usage examples

### Python (pandas)

```python
import pandas as pd

df = pd.read_csv(
    "https://[TBD]/thailand-adm-names-v1.0.0.csv",
    dtype={"tis1099_code": "int", "established_year": "Int64"},
)

# Join your provincial dataset on TIS-1099 code
your_data = pd.read_csv("your_dataset.csv")
joined = your_data.merge(df, left_on="province_code", right_on="tis1099_code")
```

### Python (parquet, faster for large workflows)

```python
import pandas as pd

df = pd.read_parquet("https://[TBD]/thailand-adm-names-v1.0.0.parquet")
```

### SQL (DuckDB)

```sql
-- DuckDB reads CSV or Parquet directly from a URL
SELECT *
FROM 'https://[TBD]/thailand-adm-names-v1.0.0.parquet'
WHERE region = 'Northeast';
```

### SQL (Postgres COPY)

```sql
CREATE TABLE thailand_adm_names (
    tis1099_code     int      PRIMARY KEY,
    iso3166_2        text,
    name_en          text,
    name_th          text,
    name_alts_en     text,
    region           text,
    capital          text,
    capital_th       text,
    established_year int,
    centroid_lat     float8,
    centroid_lon     float8,
    notes            text
);

\COPY thailand_adm_names FROM 'thailand-adm-names-v1.0.0.csv' WITH (FORMAT csv, HEADER true);
```

## Input sources

This artifact composes data from four MIT-licensed upstream repositories. Each is acknowledged in the methodology PDF, this README, and the NOTICE file.

- [thailand-geography-data/thailand-geography-json](https://github.com/thailand-geography-data/thailand-geography-json) — primary names base (MIT)
- [kongvut/thai-province-data](https://github.com/kongvut/thai-province-data) — region grouping; centroid fallback (MIT)
- [GeoThai/data](https://github.com/GeoThai/data) — cross-validation (MIT)
- [piyayut-ch/mapthai](https://github.com/piyayut-ch/mapthai) — polygon source for centroid computation (MIT)

## Corrections and contributions

Found a spelling that should be reconsidered, an alternate to add, or a boundary-change record to include? Open a GitHub issue or submit a pull request against `data/overrides.csv` or `data/historical_mappings.csv`. The methodology PDF documents the corrections workflow.

## License

- The data and methodology are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You may share and adapt for any purpose, including commercial, with attribution.
- The build code (`bin/`) is licensed under MIT.
- See `NOTICE.md` for upstream MIT-license attributions.

## See also

- [Thailand Livability Index (TLI)](https://thailand-livability-index.com) — the project this artifact is part of (CC BY-NC 4.0 dataset, separate license posture per the methodology PDF rationale)
