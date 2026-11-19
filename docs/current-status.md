# Current build status

Last checked: 2026-11-19

## Implemented in this starter

- Mobile-first installable PWA shell.
- FastAPI endpoints for health, IANA timezone lookup, chart generation adapter, optional one-shot place search, and coordinate-to-timezone lookup.
- Date-aware IANA timezone conversion; nonexistent DST times are rejected and ambiguous DST times require the user to select an occurrence.
- Integration adapter that calls the pinned `vedic-calc` functions `calculate_chart()` and `calculate_dasha()` rather than reimplementing their chart mathematics.
- Independent Swiss Ephemeris speed calls using `SEFLG_SPEED` to avoid the upstream speed-flag issue in retrograde labels.
- Per-planet source reporting for Swiss Ephemeris / JPL / Moshier fallback.
- No saved birth profiles, account database, payment collection, or AI provider yet.
- Initial public GitHub repository created and starter files pushed to `founder-dax-limbasiya/-vedic-ai-mvp`.

## Checks reported from the authoring environment

- 12 Python unit tests: passed.
- Python bytecode compilation: passed.
- FastAPI smoke checks: `/health`, timezone filtering, and truthful `503 engine_unavailable` response when the chart dependency is absent: passed.
- `node --check` for the PWA application script: passed.
- PWA manifest JSON and API `pyproject.toml` parsing: passed.

## Not verified / not done

- Installing the pinned `vedic-calc` dependency failed in the authoring environment because GitHub's hostname could not be resolved there.
- Therefore, a real `vedic-calc` birth chart has **not** been generated end-to-end in that environment. The adapter is mock-tested only.
- No public deployment has been performed.
- AI interpretations, user accounts, cloud sync, payments, report purchasing and multi-language content are not implemented.

## Release blockers

1. Install the exact pinned engine in an environment with package access.
2. Run reference birth charts against at least two independent calculators / reference datasets, with ayanamsa, node and house conventions explicitly matched.
3. Test historical timezone rules and boundary cases, including DST folds, date-line transitions and unknown birth times.
4. Generate and review a full SBOM and all source/data licences.
5. Before public AGPL network deployment, publish the complete corresponding source and set `SOURCE_URL` in `web/config.js`.
6. Add abuse controls and operational monitoring before moving beyond a closed beta.
