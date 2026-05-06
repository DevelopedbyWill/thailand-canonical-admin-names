# 11. Operational lookups

The artifact ships four operational-lookup columns at ADM1: `postal_code_prefixes`, `telephone_area_codes`, `num_amphoe`, `num_tambon`. Each comes from a documented source via a documented derivation. These columns serve consumers doing address-bucketing, phone-number routing, count-aggregation validation, and admin-level navigation.

| Column | Source | Derivation |
|---|---|---|
| `postal_code_prefixes` | `thailand-geography-data` subdistricts.json `postalCode` field | Group all subdistrict postal codes by province; take first 2 digits; deduplicate; sort; pipe-join |
| `telephone_area_codes` | [Wikipedia "Telephone numbers in Thailand"](https://en.wikipedia.org/wiki/Telephone_numbers_in_Thailand) "Geographic area codes" section | Parse the area-code → province table; reverse-index to province → area-codes; pipe-join sorted codes per province |
| `num_amphoe` | `thailand-geography-data` districts.json | Count districts per `provinceCode` |
| `num_tambon` | `thailand-geography-data` subdistricts.json | Count subdistricts per `provinceCode` |

**Postal code prefixes.** Thai postal codes are 5 digits. The first 2 identify a province; the remaining 3 identify the local sorting facility within the province. The build script reads every subdistrict's 5-digit `postalCode`, groups by `provinceCode`, takes the 2-digit prefix, deduplicates, sorts, and joins with `|`. Most provinces have a single prefix matching their TIS-1099 code (Phuket TIS-83 → prefix `83`). A few carry multiple prefixes due to upstream data-source attribution quirks (Chiang Mai's row carries `50|58` because some northern subdistricts attributed to Chiang Mai in `thailand-geography-data` carry 58-prefix postal codes; this is a known artifact of the upstream attribution and is preserved unchanged in v1.0).

**Telephone area codes.** Thailand's fixed-line area codes are 2 to 3 digits with a leading zero. The `02` code covers Bangkok plus four neighbor provinces (Nonthaburi, Pathum Thani, Samut Prakan, plus the Phutthamonthon area of Nakhon Pathom). Other codes (032, 034, 035, etc.) cover groups of three to four provinces each. Multiple provinces can share one code, and one province can carry multiple codes. The build script parses the Wikipedia area-code table, builds a province-to-code reverse index, and pipe-joins sorted codes per province. 77 of 77 provinces resolve via this method at v1.0.

**Administrative subunit counts.** `num_amphoe` is the count of ADM2 rows whose parent province equals the row's `tis1099_code`. `num_tambon` is the same count at ADM3. The sums across the ADM1 table equal the totals published by Thailand's Department of Provincial Administration: 928 amphoe and 7,436 tambon. The validator's admin-counts statistical-sanity check enforces these totals fall within published-range tolerances. Bangkok's counts (50 districts, 180 subdistricts) match Bangkok Metropolitan Administration figures.

## 11.1 Worked example: Nakhon Pathom (TIS-73)

Nakhon Pathom illustrates the multi-area-code pattern that single-area-code provinces do not show:

| Column | Value | Source detail |
|---|---|---|
| `postal_code_prefixes` | `73` | All Nakhon Pathom subdistricts in `thailand-geography-data` carry postal codes starting `73`. Single prefix. |
| `telephone_area_codes` | `02\|034` | Wikipedia: `02` covers the Phutthamonthon area (Bangkok-suburban integration); `034` covers the rest of Nakhon Pathom. Both codes reverse-index to TIS-73. |
| `num_amphoe` | 7 | `thailand-geography-data`: 7 districts under provinceCode 73. |
| `num_tambon` | 109 | `thailand-geography-data`: 109 subdistricts under provinceCode 73. |

The pipe-joined `telephone_area_codes` field allows downstream consumers to do exact-match lookups for either code. A phone-routing system fielding an `034`-prefix call can map to TIS-73 for province-level enrichment without further normalization.
