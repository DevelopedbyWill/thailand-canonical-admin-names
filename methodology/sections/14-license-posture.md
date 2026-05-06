# 14. License posture

The artifact uses three licenses across its file types: Creative Commons Attribution 4.0 International (CC BY 4.0) on the data tables and methodology document, MIT on the build code and validator, and per-file upstream licenses on bundled polygon files. The layered posture is documented in `NOTICE.md` at the artifact root.

| Asset | License | Justification |
|---|---|---|
| Data tables (CSV, Parquet at all three ADM levels) | CC BY 4.0 | Reference-data genre convention (matches ISO 3166-2 community releases, GeoNames, pycountry). |
| Methodology document (this PDF) | CC BY 4.0 | Documentary content; supports academic citation and reuse. |
| Override registry (`overrides.csv`) | CC BY 4.0 | Audit-trail metadata layered on the data. |
| Historical mappings (`historical_mappings.csv`) | CC BY 4.0 | Same. |
| Established-years registry (`established_years.csv`) | CC BY 4.0 | Same. |
| Build script (`bin/build_v{version}.py`) | MIT | Code license; permissive default for derivative tools. |
| Validator and test suite (`bin/validate_*.py`, `bin/test_*.py`) | MIT | Same. |
| Cross-check script (`bin/cross_check_inputs.py`) | MIT | Same. |
| `mapthai`-derived GeoJSON files (bundled at all three ADM levels) | CC BY 3.0 IGO (under OCHA CODs) | Inherits OCHA Common Operational Datasets license; not relicensed by this artifact. |
| HDX RTSD shapefiles (bundled) | CC BY 3.0 IGO under OCHA CODs framework | Original publication license preserved. |

**Why CC BY 4.0 on the data.** Reference-data licenses in this genre are permissive (ISO 3166-2 community releases, GeoNames, pycountry). Locking commercial reuse out would push commercial adopters back to private lists, which is the gap this artifact addresses. The CC BY 4.0 posture preserves the citation requirement (which surfaces back to the methodology and override registry) while removing the commercial-gating barrier that would defeat adoption.

**MIT on build code, CC BY 4.0 on data.** Mixed-license repositories are conventional. Code under MIT permits forking and reuse without burden; data under CC BY 4.0 requires attribution but permits commercial use. The repository's `LICENSE` file resolves to MIT for code; the `LICENSE-DATA` file specifies CC BY 4.0 for data and methodology; the `NOTICE.md` file consolidates per-file license claims and upstream attribution chains.

**Layered licensing on bundled polygons.** The polygons originate from OCHA CODs (Common Operational Datasets), which carry CC BY 3.0 IGO. The artifact does not relicense these files. Consumers using the `mapthai`-derived GeoJSON or the HDX RTSD shapefiles must comply with CC BY 3.0 IGO terms (attribution to OCHA and the originating Thai government body, no implied endorsement). The `NOTICE.md` file at the artifact root carries the full upstream attribution chain. Data tables, override registry, methodology PDF, and code are unaffected by the layered polygon licensing because they are independent files under their own licenses.

## 14.1 Worked example: a downstream consumer's compliance checklist

A downstream consumer using the artifact in a commercial product would, at minimum, comply with the following per asset:

| What they used | License obligation |
|---|---|
| Data tables (CSV / Parquet) | Cite the artifact per CC BY 4.0 using the Zenodo deposit DOI; indicate any modifications; link to the license. |
| Methodology document | Cite the methodology document per CC BY 4.0 using the Zenodo deposit DOI; indicate any modifications. |
| Build script | Preserve the MIT copyright notice and license text in derivative tools. |
| `mapthai`-derived GeoJSON polygons | Attribute OCHA, `mapthai` (Chitchumnong, n.d.), and Natural Earth where applicable. Comply with CC BY 3.0 IGO. |
| HDX RTSD shapefiles | Attribute the Royal Thai Survey Department and OCHA. Comply with CC BY 3.0 IGO. |

Consumers using only the tabular CSV / Parquet outputs and the methodology document interact with a single license (CC BY 4.0). Consumers loading the bundled polygons inherit the layered obligation. The artifact's `NOTICE.md` carries the canonical attribution language consumers can copy directly into their own attribution sections.
