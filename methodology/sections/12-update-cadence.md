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
