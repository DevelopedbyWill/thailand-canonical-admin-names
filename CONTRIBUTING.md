# Contributing

Community contributions are welcome. The artifact uses post-publication community review via GitHub issues and pull requests in place of named pre-publication peer review (see Section 15 of the methodology PDF for the rationale).

## Issue templates

Four issue templates cover the typical contribution shapes. Please use the relevant template; this helps the maintainer triage and respond within the SLA.

- **Spelling correction** — propose a different `name_en_canonical`, an addition to `name_alternates_en`, or a capital-name fix
- **Verification upgrade** — promote an `established_year` from PARTIAL to CONFIRMED with a primary-source citation (Royal Gazette publication, Royal Decree, Revolutionary Council Announcement, or equivalent)
- **Polygon-derived correction** — surface centroid, area, bounding-box, or coastline values that diverge materially from authoritative sources
- **Methodology clarification** — question or correction request against the methodology PDF or `NOTICE.md`

## Pull requests

Pull requests are welcome for any of the above plus direct documentation edits. Each PR should:

- Pass continuous integration (the validator and mutation test suite run on every push and PR via `.github/workflows/validate.yml`)
- Include an updated entry in `CHANGELOG.md` under the unreleased section
- For data corrections, include a row added to `overrides.csv`, `historical_mappings.csv`, or `established_years.csv` with a complete audit-trail line (chosen value, source citation, decision date, decision author, notes)
- For methodology corrections, preserve brand-voice compliance per `voice-guide-v1.3.docx` Section B.1.2 (full technical register, APA 7, no first person, active voice)

## Maintainer review SLA

The maintainer commits to:

- Reviewing issues within four weeks of submission
- Reviewing pull requests in the next monthly patch cycle (Section 12 of the methodology)
- Documenting reasons when an issue is declined, before closing

## Maintainer succession

The artifact is currently single-maintainer. If you would consider co-maintainer-ship and have demonstrable expertise in Thai administrative geography, Royal Gazette archival research, or open-source data-product maintenance, please open an issue with the `co-maintainer-interest` label.

## License

By contributing, you agree that your contributions will be licensed under the same terms as the corresponding file:

- Code (`bin/`, `.github/workflows/`): MIT
- Data and registries (`data/*.csv`, `data/v1.0.0/*`): CC BY 4.0
- Methodology document (`methodology/`): CC BY 4.0
- Bundled polygons: upstream licenses preserved (see `NOTICE.md`)
