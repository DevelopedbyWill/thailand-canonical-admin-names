# 6. Source authority order and override rule

v1.0 follows the Royal Thai General System of Transcription (RTGS) by default and overrides RTGS only where a clear majority of authoritative Thai-government tables (DOPA, NSO, RTSD, TAT, BOI) and the international literature agree on a non-RTGS spelling. Every override is logged in `overrides.csv` with a per-row audit trail.

The rule reflects an operational reality: RTGS is the official romanization standard, but Thai government bodies apply it inconsistently. Strictly following RTGS in every cell would produce spellings that no government dataset uses, which defeats the artifact's purpose as a join target. Strictly following government practice without RTGS as the default would lose the formal anchor that justifies the canonical claim. The override rule preserves both: RTGS as the default with a documented exception process for cases where government-practice consensus has diverged.

The override resolution procedure runs at composition time. For each cross-source disagreement surfaced by `bin/cross_check_inputs.py` (Section 5), the maintainer decides between the strict-rendering candidate and the divergent candidate. The decision is logged in `overrides.csv` with the following per-row schema:

| Column | Description |
|---|---|
| `tis1099_code` | The administrative code at which the override applies. |
| `thai_name` | The Thai-script name (the join key). |
| `strict_rendering_candidate` | The RTGS-strict or upstream-default English spelling. |
| `chosen_spelling` | The English spelling adopted in `name_en_canonical`. |
| `resolution_rule` | The rule applied (typically `government-practice-majority + international-literature-majority`). |
| `supporting_sources` | Named tables and sources that support the chosen spelling. |
| `decision_date` | ISO 8601 date the override was committed. |
| `decision_author` | The maintainer or contributor who made the call. |
| `notes` | Free-text contextual notes. |

The strict-rendering candidate also flows into `name_alternates_en`, so adopters joining on the historical or strictly-rendered spelling still find the row.

## 6.1 Worked example: ลพบุรี (TIS-16)

The Lopburi case is the founding entry in `overrides.csv` and is the only override at v1.0 ADM1. The cross-source comparison surfaces ลพบุรี as the only province where the four MIT-licensed inputs disagree:

| Source | English spelling at row TIS-16 |
|---|---|
| `thailand-geography-data` | `Loburi` |
| `kongvut/thai-province-data` | `Lopburi` |
| `GeoThai/data` v1 | `Loburi` |
| `GeoThai/data` v2 | `Loburi` |

The Tourism Authority of Thailand province directory uses `Lopburi`. The Royal Thai Government's English-language tourism content uses `Lopburi`. The English Wikipedia article is titled `Lopburi province`. International travel literature and academic publications on Thai history use `Lopburi`. The strict-rendering candidate `Loburi` is propagated across three of the four MIT-licensed input sources but is not used by the named Thai-government bodies or by the international literature.

The override adopts `Lopburi` as `name_en_canonical` and lists `Loburi` in `name_alternates_en`. The audit-trail line in `overrides.csv` carries:

- `tis1099_code = 16`
- `thai_name = ลพบุรี`
- `strict_rendering_candidate = Loburi`
- `chosen_spelling = Lopburi`
- `resolution_rule = government-practice-majority + international-literature-majority`
- `supporting_sources = TAT province directory; Royal Thai Government English tourism content; English Wikipedia "Lopburi province"; international academic publications on Thai history`
- `decision_date = 2026-05-06`
- `decision_author = William J. Reynolds (ORCID 0009-0005-1217-7465)`
- `notes = Strict rendering "Loburi" propagated across 3 of 4 MIT-licensed input sources but is not used by named Thai-government bodies or international references at the time of the v1.0 build.`

Adopters joining on the historical spelling `Loburi` find the row via `name_alternates_en`. Adopters using `name_en_canonical` get `Lopburi` for cross-source consistency with the named government tables and the international literature.
