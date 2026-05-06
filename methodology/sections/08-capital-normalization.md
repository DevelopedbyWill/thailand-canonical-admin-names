# 8. Capital normalization

Wikidata returns province-capital labels via the Q50198 (province of Thailand) → P36 (capital) → label query path. Three normalization rules apply to the returned values before they populate `capital` and `capital_th` in the artifact, plus one preservation exception. The rules and the exception are implemented in `bin/build_v1_0_0.py` and exercised by the validation suite (Section 9).

## 8.1 English-side rules

**Strip the *Mueang* prefix.** Wikidata's capital-of-province entity for several provinces is the *Mueang* district that serves as the administrative center, returned with "Mueang" prefixed (e.g., `Mueang Phrae` for Phrae's capital, `Mueang Lamphun` for Lamphun's). The artifact strips "Mueang " and uses the bare place name. Phrae (TIS-54) provides the worked example in 8.3.

**Normalize spacing variants where the capital matches the province.** Wikidata sometimes returns a capital spelling that differs from the province's `name_en_canonical` only by spacing or capitalization. Examples: `Chonburi` (Wikidata) for Chon Buri (canonical) at TIS-20; `Phang Nga` (Wikidata) for Phangnga (canonical) at TIS-82. The artifact normalizes these to match the province's chosen spelling so that cross-row joins between province and capital fields stay consistent. The comparison is case-and-space-insensitive: if `wikidata_capital.replace(" ", "").lower() == province_name.replace(" ", "").lower()`, the artifact substitutes the province spelling.

**Preserve genuinely distinct capital names.** A small number of provinces have capitals that are not just the province name. Sukhothai (TIS-64) has a capital named `Sukhothai Thani`. Bangkok (TIS-10) has a capital named `Bangkok` (the self-as-capital pattern). The artifact preserves these without normalization, and the `notes` field at the affected rows carries an inline explanation. The validator's capital-vs-province-name alignment check treats these rows as REVIEW-not-FAIL findings, with the notes-field documentation as the resolution.

## 8.2 Thai-side rule

**Strip the municipality prefix.** Wikidata's capital labels in Thai prefix the municipality designation: เทศบาลนคร (city municipality), เทศบาลเมือง (town municipality), or เทศบาลตำบล (subdistrict municipality). For example, Wikidata returns `เทศบาลเมืองภูเก็ต` for Phuket's capital city. The artifact strips these prefixes via the `THAI_MUNICIPALITY_PREFIXES` constant in the build script and stores the bare place name in `capital_th` (here, `ภูเก็ต`). The Thai-side equivalent of "Mueang" (เมือง) does not need separate handling: Wikidata's Thai capital labels carry the municipality designation rather than the เมือง prefix, so the single municipality-prefix strip is sufficient.

## 8.3 Worked example: Phrae (TIS-54)

Wikidata's Q50198 → P36 query returns the following raw values for TIS-54:

| Field | Wikidata raw | After normalization | Stored in artifact |
|---|---|---|---|
| `cap_en` | `Mueang Phrae` | strip `Mueang ` → `Phrae` | `capital = Phrae` |
| `cap_th` | `เทศบาลเมืองแพร่` | strip `เทศบาลเมือง` prefix → `แพร่` | `capital_th = แพร่` |
| `name_en_canonical` | (from `thailand-geography-data`) | (no change) | `Phrae` |
| `name_th` | `แพร่` | (PyThaiNLP-normalized; no character change at this row) | `แพร่` |

After normalization, `capital` and `name_en_canonical` both read `Phrae`; `capital_th` and `name_th` both read `แพร่`. The validator's capital-against-Wikidata round-trip check confirms the consistency.

The Sukhothai (TIS-64) case sits at the other end of the rule set. The Wikidata raw `cap_en` is `Sukhothai Thani`. The Mueang-prefix rule does not apply (no `Mueang ` prefix). The spacing-variant rule does not apply (`Sukhothai Thani` is not a spacing variant of `Sukhothai`). The artifact preserves `capital = Sukhothai Thani`, and the `notes` field at TIS-64 carries: "Provincial capital is Sukhothai Thani (สุโขทัยธานี), genuinely a different name from the province itself rather than a spelling variant; preserved as-is per the capital-name normalization rule."
