# 17. Limitations

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
