# Third-party notices

## vedic-calc

This project imports and calls `vedic-calc`, Copyright its respective contributors, distributed under AGPL-3.0-or-later. Source: https://github.com/atolat/vedic-calc. The dependency is pinned in `api/pyproject.toml`. Retain the upstream copyright and licence notices when redistributing.

## Swiss Ephemeris / pyswisseph

The calculation dependency uses Swiss Ephemeris. Swiss Ephemeris is dual-licensed under AGPL or a separate Professional Licence. This project chooses AGPL and does not claim a Professional Licence. Preserve all upstream notices and check the exact dependency licence files shipped in the environment/build artifact.

## OpenStreetMap Nominatim

The optional one-shot birthplace search uses the public Nominatim service only after a user submits a search. It is not autocomplete. The app must identify itself, stay under one request per second across the whole app, cache results, allow switching providers, and display “© OpenStreetMap contributors”. See https://operations.osmfoundation.org/policies/nominatim/. OSM data is provided under ODbL; do not bulk-download or resell results.

## timezonefinder / timezonefinder-data (optional)

The `timezonefinder` source code is MIT-licensed. Its separately distributed boundary dataset is ODbL-licensed. This project uses it only as an optional coordinate-to-IANA-timezone lookup; preserve attribution and the dataset licence terms. See https://timezonefinder.readthedocs.io/en/latest/3_about.html.

## Branding

This project is independent and is not endorsed by Astrodienst, the Swiss Ephemeris authors, or the `vedic-calc` maintainers.
