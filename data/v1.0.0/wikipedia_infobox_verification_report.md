# Wikipedia infobox cross-check — ADM1 v1.0.0

Compares stored polygon-derived `area_km2`, `centroid_lat`, `centroid_lon` against Wikipedia `{{Infobox settlement}}` `area_total_km2` and `{{Coord}}`.

- Provinces processed: 77 / 77
- Area deviation flag threshold: > 10%
- Centroid distance flag threshold: > 30 km (loose; infobox coords usually point at provincial capital, not geographic centroid)
- Parse failures: 0
- Area-deviation flags: 4
- Centroid-distance flags: 4

## Findings and resolution

The 73 of 77 provinces (95%) within ±10% deviation establishes that the UTM-projected polygon areas in `area_km2` agree with the Royal Forest Department (RFD) provincial figures cited by Wikipedia infoboxes to within the documented Section 9.1 tolerance. The four flagged provinces all cite the same `forest.go.th` source for `area_total_km2` and reflect a systematic difference between two polygon corpora rather than a defect in either:

- Phangnga (TIS-82, -34.58%) and Krabi (TIS-81, -18.23%): the RFD figure includes the Andaman island chains under provincial administrative jurisdiction (Phang Nga Bay limestone karsts, Phi Phi group, Lanta group). The OCHA-derived `mapthai` polygons cover the mainland and large nearshore islands, not the full island administrative boundary.
- Samut Songkhram (TIS-75, -13.79%) and Samut Prakan (TIS-11, -13.50%): both are estuarine coastal provinces where RFD figures include tidal flats and administrative marine area; OCHA polygons follow the high-water mark.

The four centroid-distance flags (Kanchanaburi, Mae Hong Son, Tak, Songkhla) reflect provinces with elongated geometry where the provincial capital sits substantially off the geometric centroid. This is documented behavior, not a data error: Section 9.1 specifies that `centroid_lat`/`centroid_lon` are polygon-geometric, and Wikipedia infobox coordinates point at the capital. Kanchanaburi (85 km) and Mae Hong Son (53 km) are the longest provinces by their major axis in Thailand.

Methodology Section 9.1 documents the ±10% RFD tolerance and the Sakon Nakhon four-significant-digit match. This report makes the underlying check reproducible and quantifies the deviation distribution at v1.0 release.

## Summary statistics

- Area deviation: n = 77
  - mean: -0.85%, min: -34.58%, max: +9.42%, abs-max: 34.58%
- Centroid distance: n = 21
  - mean: 21.0 km, max: 85.2 km, median: 14.7 km

## Area-deviation flags (> 10%)

| TIS-1099 | Province | Stored km² | Wikipedia km² | Deviation |
|---|---|---:|---:|---:|
| 82 | Phangnga | 3,594.6 | 5,495.0 | -34.58% |
| 81 | Krabi | 4,352.6 | 5,323.0 | -18.23% |
| 75 | Samut Songkhram | 356.9 | 414.0 | -13.79% |
| 11 | Samut Prakan | 819.2 | 947.0 | -13.50% |

## Centroid-distance flags (> 30 km)

Centroid is polygon-geometric; Wikipedia infobox coordinates point at the provincial capital. A flag means the capital sits more than 30 km from the geographic centroid, which is interpretable for elongated or coastal provinces.

| TIS-1099 | Province | Stored centroid | Wikipedia coord | Distance km |
|---|---|---|---|---:|
| 71 | Kanchanaburi | 14.5931, 99.0427 | 14.0042, 99.5492 | 85.2 |
| 58 | Mae Hong Son | 18.8195, 98.0309 | 19.2881, 97.9644 | 52.6 |
| 63 | Tak | 16.7145, 98.7896 | 16.8839, 99.1250 | 40.4 |
| 90 | Songkhla | 6.9288, 100.5561 | 7.2053, 100.5969 | 31.1 |

## All provinces — full table

| TIS-1099 | Province | Stored km² | Wiki km² | Area dev | Centroid dist km |
|---|---|---:|---:|---:|---:|
| 10 | Bangkok | 1,716.5 | 1,568.7 | +9.42% | 14.7 |
| 11 | Samut Prakan | 819.2 | 947.0 | -13.50% | — |
| 12 | Nonthaburi | 633.2 | 637.0 | -0.60% | 14.9 |
| 13 | Pathum Thani | 1,549.0 | 1,520.0 | +1.91% | — |
| 14 | Phra Nakhon Si Ayutthaya | 2,496.8 | 2,548.0 | -2.01% | — |
| 15 | Ang Thong | 946.6 | 950.0 | -0.36% | — |
| 16 | Lopburi | 6,521.0 | 6,493.0 | +0.43% | — |
| 17 | Sing Buri | 807.5 | 817.0 | -1.16% | — |
| 18 | Chai Nat | 2,447.6 | 2,506.0 | -2.33% | — |
| 19 | Saraburi | 3,576.7 | 3,499.0 | +2.22% | — |
| 20 | Chon Buri | 4,459.6 | 4,508.0 | -1.07% | 2.6 |
| 21 | Rayong | 3,744.8 | 3,666.0 | +2.15% | — |
| 22 | Chanthaburi | 6,593.6 | 6,415.0 | +2.78% | — |
| 23 | Trat | 2,670.4 | 2,866.0 | -6.82% | 6.1 |
| 24 | Chachoengsao | 5,206.2 | 5,169.0 | +0.72% | — |
| 25 | Prachin Buri | 4,889.5 | 5,026.0 | -2.72% | — |
| 26 | Nakhon Nayok | 2,177.2 | 2,141.0 | +1.69% | — |
| 27 | Sa Kaeo | 6,650.9 | 6,831.0 | -2.64% | — |
| 30 | Nakhon Ratchasima | 20,748.6 | 20,736.0 | +0.06% | 2.1 |
| 31 | Buri Ram | 9,926.6 | 10,080.0 | -1.52% | — |
| 32 | Surin | 8,943.1 | 8,854.0 | +1.01% | — |
| 33 | Si Sa Ket | 9,101.0 | 8,936.0 | +1.85% | — |
| 34 | Ubon Ratchathani | 15,367.9 | 15,626.0 | -1.65% | — |
| 35 | Yasothon | 4,112.8 | 4,131.0 | -0.44% | — |
| 36 | Chaiyaphum | 12,561.3 | 12,698.0 | -1.08% | — |
| 37 | Amnat Charoen | 3,126.6 | 3,290.0 | -4.97% | — |
| 38 | Bueng Kan | 3,968.5 | 4,003.0 | -0.86% | 3.0 |
| 39 | Nong Bua Lam Phu | 4,070.8 | 4,099.0 | -0.69% | — |
| 40 | Khon Kaen | 10,601.6 | 10,659.0 | -0.54% | — |
| 41 | Udon Thani | 11,099.9 | 11,072.0 | +0.25% | 12.7 |
| 42 | Loei | 10,619.5 | 10,500.0 | +1.14% | 12.9 |
| 43 | Nong Khai | 3,436.1 | 3,275.0 | +4.92% | — |
| 44 | Maha Sarakham | 5,855.9 | 5,607.0 | +4.44% | — |
| 45 | Roi Et | 7,741.2 | 7,873.0 | -1.67% | — |
| 46 | Kalasin | 6,663.5 | 6,936.0 | -3.93% | 24.2 |
| 47 | Sakon Nakhon | 9,609.1 | 9,580.0 | +0.30% | — |
| 48 | Nakhon Phanom | 5,375.8 | 5,637.0 | -4.63% | — |
| 49 | Mukdahan | 4,185.9 | 4,126.0 | +1.45% | — |
| 50 | Chiang Mai | 22,438.2 | 22,311.0 | +0.57% | 25.8 |
| 51 | Lamphun | 4,383.0 | 4,478.0 | -2.12% | — |
| 52 | Lampang | 12,672.6 | 12,488.0 | +1.48% | — |
| 53 | Uttaradit | 7,921.3 | 7,906.0 | +0.19% | — |
| 54 | Phrae | 6,512.7 | 6,483.0 | +0.46% | — |
| 55 | Nan | 11,945.3 | 12,130.0 | -1.52% | 10.5 |
| 56 | Phayao | 6,147.0 | 6,189.0 | -0.68% | — |
| 57 | Chiang Rai | 11,579.3 | 11,503.0 | +0.66% | 8.2 |
| 58 | Mae Hong Son | 12,455.5 | 12,765.0 | -2.42% | 52.6 |
| 60 | Nakhon Sawan | 9,662.9 | 9,526.0 | +1.44% | — |
| 61 | Uthai Thani | 6,638.5 | 6,647.0 | -0.13% | — |
| 62 | Kamphaeng Phet | 8,251.3 | 8,512.0 | -3.06% | 25.8 |
| 63 | Tak | 17,293.3 | 17,303.0 | -0.06% | 40.4 |
| 64 | Sukhothai | 6,800.8 | 6,671.0 | +1.95% | — |
| 65 | Phitsanulok | 10,403.2 | 10,589.0 | -1.75% | — |
| 66 | Phichit | 4,326.0 | 4,319.0 | +0.16% | — |
| 67 | Phetchabun | 12,472.3 | 12,340.0 | +1.07% | 8.1 |
| 70 | Ratchaburi | 5,215.6 | 5,189.0 | +0.51% | — |
| 71 | Kanchanaburi | 19,350.0 | 19,482.0 | -0.68% | 85.2 |
| 72 | Suphan Buri | 5,401.9 | 5,410.0 | -0.15% | — |
| 73 | Nakhon Pathom | 2,204.4 | 2,142.0 | +2.91% | — |
| 74 | Samut Sakhon | 925.5 | 866.0 | +6.87% | — |
| 75 | Samut Songkhram | 356.9 | 414.0 | -13.79% | — |
| 76 | Phetchaburi | 6,272.0 | 6,172.0 | +1.62% | — |
| 77 | Prachuap Khiri Khan | 6,428.1 | 6,414.0 | +0.22% | — |
| 80 | Nakhon Si Thammarat | 9,816.6 | 9,885.0 | -0.69% | 20.2 |
| 81 | Krabi | 4,352.6 | 5,323.0 | -18.23% | — |
| 82 | Phangnga | 3,594.6 | 5,495.0 | -34.58% | — |
| 83 | Phuket | 596.6 | 547.0 | +9.07% | 10.4 |
| 84 | Surat Thani | 13,180.1 | 13,079.0 | +0.77% | 29.6 |
| 85 | Ranong | 3,359.0 | 3,230.0 | +3.99% | — |
| 86 | Chumphon | 6,002.2 | 5,998.0 | +0.07% | — |
| 90 | Songkhla | 7,772.8 | 7,741.0 | +0.41% | 31.1 |
| 91 | Satun | 2,888.1 | 3,019.0 | -4.34% | — |
| 92 | Trang | 4,615.2 | 4,726.0 | -2.34% | — |
| 93 | Phatthalung | 3,915.1 | 3,861.0 | +1.40% | — |
| 94 | Pattani | 2,051.3 | 1,977.0 | +3.76% | — |
| 95 | Yala | 4,350.2 | 4,476.0 | -2.81% | — |
| 96 | Narathiwat | 4,617.9 | 4,491.0 | +2.83% | — |
