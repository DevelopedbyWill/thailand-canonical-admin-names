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
