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

**Why CC BY 4.0 on the data, not TLI's CC BY-NC 4.0.** The Thailand Livability Index (TLI) scored dataset is licensed CC BY-NC 4.0 with a separate commercial license (Reynolds, 2026b). The canonical-names artifact diverges from that posture and uses CC BY 4.0 (no NC clause) for two main reasons. First, the artifact is community infrastructure rather than the TLI scored dataset; adoption is the primary success metric, and commercial gating would defeat that. Second, reference-data licenses in this genre are permissive (ISO 3166-2 community releases, GeoNames, pycountry); locking commercial reuse out would push commercial adopters back to private lists, which is the problem this artifact addresses. The methodology PDF and the Zenodo deposit metadata both name the deviation explicitly so downstream consumers understand the divergence from TLI's main dataset license.

**MIT on build code, CC BY 4.0 on data.** Mixed-license repositories are conventional. Code under MIT permits forking and reuse without burden; data under CC BY 4.0 requires attribution but permits commercial use. The repository's `LICENSE` file resolves to MIT for code; the `LICENSE-DATA` file specifies CC BY 4.0 for data and methodology; the `NOTICE.md` file consolidates per-file license claims and upstream attribution chains.

**Layered licensing on bundled polygons.** The polygons originate from OCHA CODs (Common Operational Datasets), which carry CC BY 3.0 IGO. The artifact does not relicense these files. Consumers using the `mapthai`-derived GeoJSON or the HDX RTSD shapefiles must comply with CC BY 3.0 IGO terms (attribution to OCHA and the originating Thai government body, no implied endorsement). The `NOTICE.md` file at the artifact root carries the full upstream attribution chain. Data tables, override registry, methodology PDF, and code are unaffected by the layered polygon licensing because they are independent files under their own licenses.

## 14.1 Worked example: a downstream consumer's compliance checklist

A downstream consumer using the artifact in a commercial product would, at minimum, comply with the following per asset:

| What they used | License obligation |
|---|---|
| Data tables (CSV / Parquet) | Cite the artifact (Reynolds, 2026a) per CC BY 4.0; indicate any modifications; link to the license. |
| Methodology document | Cite the methodology document (Reynolds, 2026a) per CC BY 4.0; indicate any modifications. |
| Build script | Preserve the MIT copyright notice and license text in derivative tools. |
| `mapthai`-derived GeoJSON polygons | Attribute OCHA, `mapthai` (Chitchumnong, n.d.), and Natural Earth where applicable. Comply with CC BY 3.0 IGO. |
| HDX RTSD shapefiles | Attribute the Royal Thai Survey Department and OCHA. Comply with CC BY 3.0 IGO. |

Consumers using only the tabular CSV / Parquet outputs and the methodology document interact with a single license (CC BY 4.0). Consumers loading the bundled polygons inherit the layered obligation. The artifact's `NOTICE.md` carries the canonical attribution language consumers can copy directly into their own attribution sections.
