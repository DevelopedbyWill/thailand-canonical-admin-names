# 16. TLI dependency disclosure

The Thailand Livability Index (TLI) consumes this artifact as its source-of-truth join key for province identifiers and English/Thai names. The dependency direction is one-way: this artifact is upstream infrastructure; TLI is one consumer among many. The artifact's authority comes from documented sources and the override registry (Section 6), not from TLI usage.

This section is the disclosure obligation specified by design-question Q7 in the workstream brief (Reynolds, 2026c). The same disclosure appears in TLI's own methodology document, which names this artifact as the canonical source for `tis1099_code` and `name_en_canonical` joins.

The disclosure pattern matches ISO 3166-2 precedent. The standards body publishes the codes. Many downstream consumers (subnational government products, GeoNames, OpenStreetMap, Natural Earth, and others) consume them. The same standards body's own internal data products consume their own published codes; this is the same role TLI plays here. The dependency is acknowledged in both methodology documents; it does not create circularity because the codes' authority is rooted in the publishing body's source-attribution discipline, not in adoption.

## 16.1 How TLI consumes the artifact

TLI's pipeline pulls the artifact's ADM1 CSV at build time and joins downstream tables on `tis1099_code`. The artifact's `name_en_canonical` column populates TLI's display name; the `name_th` column populates TLI's Thai-language version. The audit-script join-key patch that closed the DOPA-WorldPop cross-validation symptom (Reynolds, 2026a) uses `tis1099_code` as the canonical join key for indicator cross-checks. TLI's province-page URL slugs derive from `name_en_canonical` (lowercased, hyphenated); when the artifact updates a spelling via override, TLI's URL slugs change in the corresponding TLI release. TLI's public API endpoints reference rows by `tis1099_code`.

The dependency is loose. TLI pulls from the artifact's released CSV (a stable URL or DOI-pinned version), not from internal build artifacts. A TLI release ships against a specific artifact version (concept-DOI or version-specific DOI per Section 13). Schema-breaking changes in the artifact (major-version bumps) trigger a TLI methodology revision before the next TLI release.

## 16.2 No circular dependency

The artifact does not depend on TLI for any of its data. The composition pass (Section 5) reads the four MIT-licensed upstream sources, the identifier reference services (Section 10), and the geographic boundary sources (Section 9). None of these is TLI. The override registry (Section 6) is authored by the artifact's maintainer against named Thai government tables and the international literature; the maintainer's authorship is independent of TLI's product needs.

Maintaining this independence is a methodology requirement. If a future TLI product need pushed for a non-RTGS spelling that is not supported by the government-practice-majority and international-literature-majority test, the override would not be made. The artifact's discipline trumps any single consumer's preference, including TLI's.
