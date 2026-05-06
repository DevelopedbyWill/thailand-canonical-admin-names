# 15. Community review and corrections

The artifact uses post-publication community review via GitHub issues and pull requests in place of named pre-publication peer review. The model matches genre precedent (pycountry, ISO 3166-2 community releases, GeoNames) and is appropriate for a single-maintainer reference-data project where the methodology is documentary rather than analytical.

Maintainer review of issues happens within four weeks of submission. Pull requests get reviewed in the next monthly patch cycle (Section 12).

## 15.1 Why community review, not pre-publication peer review

Pre-publication peer review is a journal-publishing pattern. It works when an artifact has a single authoritative author, a fixed length, and a publication moment after which corrections become expensive. Reference-data artifacts have neither of those properties: maintenance is continuous and patch releases are cheap. Authority comes from documented sources rather than author credentials.

Community review post-publication serves the same goal of surfacing errors, contesting overrides, expanding alternates, and verifying claims. The work distributes across the user base over time rather than concentrating with a single reviewer. The validator and test suite (Section 9) prevent regressions: any pull request that breaks an existing check fails continuous integration before merge.

## 15.2 Contribution channels

Four issue templates plus a pull-request template cover the typical contribution shapes:

| Template | Purpose | Maintainer action |
|---|---|---|
| Spelling correction | Propose a different `name_en_canonical`, `name_alternates_en` addition, or capital-name fix | Verify against named government tables; update `overrides.csv` with audit-trail line; merge in next patch release |
| Verification upgrade | Promote an `established_year` from PARTIAL to CONFIRMED with a primary-source citation (Royal Gazette publication, Royal Decree, etc.) | Verify the cited source; update `established_years.csv` `verification_status` column from PARTIAL to CONFIRMED; the value flows to the main table on next build |
| Polygon-derived correction | Surface `centroid_lat`/`centroid_lon`, `area_km2`, `bbox_*`, or `coastline_length_km` values that diverge materially from authoritative sources | Re-run polygon computation with verification; document in `notes` if upstream polygon vintage is the cause |
| Methodology clarification | Question or correction request against the methodology PDF or `NOTICE.md` | Respond in the issue thread; pull-request an amendment if the issue surfaces a real ambiguity |
| Pull request | Direct edit to data, registry, code, or documentation files | Review for accuracy and brand-voice compliance; merge when CI passes and content is correct |

The contribution flow uses standard GitHub mechanics. An issue is opened, labeled by the maintainer or by automated triage, assigned a milestone (next patch release or annual baseline), and closed when the corresponding pull request merges or when the maintainer decides not to act with a documented reason. Issue authors retain edit rights on their submissions.

## 15.3 Worked example: a community-submitted spelling correction

A community contributor opens an issue against the `name_alternates_en` column at TIS-31 (Buri Ram), proposing the addition of `Buriram` (no space) as an alternate spelling alongside `Buri Ram` (the chosen spelling).

The contribution flow:

1. Issue opened with the spelling-correction template. Title: "Add 'Buriram' as an alternate at TIS-31 (Buri Ram)". Body cites four downstream datasets (a real-estate platform, an academic paper, a Thai-news website, and a transit timetable) using the no-space form.
2. Maintainer triages within one week. Verifies that the cited sources do use `Buriram`. Confirms that adding the alternate does not collide with another row's `name_en_canonical`.
3. Maintainer comments on the issue with a planned patch-release entry. No override is needed because the chosen spelling does not change; only `name_alternates_en` updates.
4. Pull request opened by the maintainer or the contributor: changes `name_alternates_en` at TIS-31 from empty to `Buriram`. Validator runs in continuous integration; the alternates-format check passes.
5. PR merges. The next monthly patch release ships v1.0.x with the updated alternate. Adopters joining on `Buriram` find the row.

The contribution flow took approximately two weeks from issue submission to patch release. The audit trail lives in the GitHub issue, the merge commit, and the changelog entry for the patch version.
