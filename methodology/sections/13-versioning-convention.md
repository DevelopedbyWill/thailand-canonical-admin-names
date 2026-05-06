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
