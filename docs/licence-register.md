# Licence register — initial release

| Component | Version / pin | Licence | Notes |
|---|---|---|---|
| vedic-calc | Commit `620d54560ee7e108496495eeb17054a52630a0bf` | AGPL-3.0-or-later | Core Vedic calculations and traditional rule modules; retain upstream notices. |
| Swiss Ephemeris / pyswisseph | Transitive dependency; resolved at build | AGPL-3.0 or separate Professional licence | This project chooses AGPL; do not accidentally combine with a closed-source proprietary distribution. |
| FastAPI | Compatible release in `pyproject.toml` | MIT | Keep dependency metadata. |
| Pydantic | Compatible release in `pyproject.toml` | MIT | Keep dependency metadata. |
| Uvicorn | Compatible release in `pyproject.toml` | BSD-3-Clause | Keep dependency metadata. |
| tzdata | Compatible release in `pyproject.toml` | Apache-2.0 | Verify installed wheel notices in final SBOM. |
| timezonefinder | Optional `geo` extra | MIT | Source code licence; see separate data row. |
| timezonefinder-data | Transitive dependency of timezonefinder | ODbL-1.0 | Boundary dataset is separately licensed. Do not alter/redistribute without reviewing ODbL obligations. |
| OpenStreetMap Nominatim | Optional user-triggered geocoder | ODbL data / service policy | No autocomplete; max 1 request/sec across the application, identifying User-Agent, cache, attribution, replaceable provider. |

This is an initial register, not a complete legal audit. At build time, generate an SBOM and inspect all transitive packages, binary wheels, ephemeris files, and any future interpretation corpus.
