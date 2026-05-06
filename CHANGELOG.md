# Changelog

All notable changes to the Thailand Canonical Administrative-Names Reference are documented here. This project follows [Semantic Versioning 2.0.0](https://semver.org/) per Section 13 of the methodology PDF. Each release ships as a Zenodo deposit with a version-specific DOI under a single concept-DOI.

## [1.1.0] — Planned

### Planned additions

- `num_muban` (village count) and `num_thesaban` (municipality count) columns at ADM1, populated from DOPA Local Administration Department statistics. v1.0 deferred this column population because DOPA's online stats portal requires interactive Thai-language navigation that is impractical to automate at v1.0 release timeline. Community contributions via the verification-upgrade issue template can populate these columns earlier as a patch release if a Thai-language contributor with DOPA archive access volunteers.
- ADM2 and ADM3 cross-source spelling cross-check. v1.0 ships single-source provenance from `thailand-geography-data` for the lower administrative levels; v1.1 introduces parallel cross-checking against kongvut and GeoThai at those levels.
- Wikipedia article URLs at ADM2 (where they exist).

## [1.0.1] — 2026-05-06

### Patch — documentation only, no data or code changes

- Methodology PDF: added Zenodo concept-DOI (`10.5281/zenodo.20049930`) to the title-page date line and to the citation block in Section 18 ("How to cite this artifact"). Updated PDF metadata (pdftitle, pdfauthor, pdfsubject, pdfkeywords).
- README: switched the DOI badge from version-pinned (`zenodo.20049931`) to concept-DOI (`zenodo.20049930`) so future versions inherit the badge automatically.
- README: populated the previously empty "See also" section with links to methodology PDF, NOTICE, CHANGELOG, CONTRIBUTING, the Zenodo deposit, RTGS, and the HDX RTSD dataset.

Data, validation outputs, and build code are byte-identical to v1.0.0.

## [1.0.0] — 2026-05-06

### Initial release

- Three administrative levels in one release: ADM1 (77 provinces), ADM2 (928 amphoe), ADM3 (7,436 tambon)
- Tabular outputs in CSV and Parquet (Snappy-compressed) at all three levels
- Bundled polygon geometry: GeoJSON for each level (derived from `mapthai`) plus HDX RTSD shapefiles
- ADM1 schema covers 36 columns: cross-system identifiers (TIS-1099, ISO 3166-2, HASC, FIPS, Wikidata, GeoNames, OSM, Wikipedia URL), normalized English and Thai names, override registry with audit trail, computed geographic columns (UTM-projected centroids, areas, bounding boxes, international borders, coastline lengths), operational lookups (postal prefixes, telephone area codes), administrative subunit counts
- Methodology PDF with 18 sections covering composition pass, override resolution, geographic computation, validation, license posture, community review model and limitations
- Override registry with one founding entry (Lopburi / Loburi)
- Historical-mappings registry with one founding entry (Bueng Kan / Nong Khai 2011 split)
- Established-year registry with 4 CONFIRMED entries (Yasothon 1972, Mukdahan 1982, Phayao 1977, Bueng Kan 2011) and 5 PARTIAL entries
- Name alternates populated for 50 of 77 ADM1 rows with 71 total alternates (spacing variants, "buri" split / merged forms, historical names, transliteration variants)
- Validation suite with 36 checks covering every column
- Mutation test suite with 54 tests proving the validator catches deliberate errors
- License: CC BY 4.0 on data and methodology, MIT on code, layered upstream licenses on bundled polygons (see `NOTICE.md`)
