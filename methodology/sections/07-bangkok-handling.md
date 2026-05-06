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
