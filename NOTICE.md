# Third-party notices

## vedic-calc

This project imports and calls `vedic-calc`, Copyright its respective contributors, distributed under AGPL-3.0-or-later. Source: https://github.com/atolat/vedic-calc. The dependency is pinned in `api/pyproject.toml`. Retain all upstream copyright and licence notices when redistributing.

## Swiss Ephemeris / pyswisseph

The calculation dependency uses Swiss Ephemeris. Swiss Ephemeris is dual-licensed under AGPL or a separate Professional Licence. This project chooses the AGPL route and does not claim a Professional Licence. Preserve all upstream notices and check the exact dependency licence files shipped in the environment/build artifact.

## OpenStreetMap Nominatim

The optional one-shot birthplace search uses the public Nominatim service only after a user submits a search. It is not autocomplete. Before enabling it, the operator must identify the application with a real User-Agent, stay under one request per second, cache results, provide a way to switch providers, and display “© OpenStreetMap contributors”. The starter's in-memory limiter/cache is per process only; a multi-worker or multi-replica production deployment needs a shared limiter/cache. See https://operations.osmfoundation.org/policies/nominatim/. OSM data is provided under ODbL; do not bulk-download or resell results.

## timezonefinder / timezonefinder-data (optional)

The `timezonefinder` source code is MIT-licensed. The separate `timezonefinder-data==4.2026.6` boundary dataset is ODbL-licensed. The dataset is pinned for reproducibility. Preserve attribution and review ODbL obligations before redistribution. See https://timezonefinder.readthedocs.io/en/latest/3_about.html.

## Branding

This project is independent and is not endorsed by Astrodienst, the Swiss Ephemeris authors, or the `vedic-calc` maintainers.
