# Vedic AI API

Install with `pip install -e ".[geo]"` from this folder, then run:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `POST /v1/chart` accepts local birth date/time, IANA timezone, coordinates and ayanamsa. It returns D1 placements, houses, birth-time Panchanga, 15 standard varga sign maps, Vimshottari Mahadasha periods and ephemeris diagnostics.
- `POST /v1/panchanga` accepts a calendar date, IANA timezone and coordinates. It returns the daily five Panchanga limbs at local sunrise (Lahiri ayanamsa) plus sunrise/sunset. The timezone offset is resolved at local noon; this matches the sunrise offset for ordinary civil days with conventional DST transitions. At locations/dates with no computed sunrise, the engine labels its solar-noon fallback.
- `GET /v1/timezones` filters the available IANA timezone names.
- `GET /v1/places` is an optional one-shot birthplace search, not autocomplete.
- `GET /v1/place-timezone` resolves a coordinate pair to an IANA timezone using the optional offline boundary dataset.
- `GET /health` reports API and calculation-engine readiness.

The API processes each request without creating a saved birth profile or persisting request bodies. The daily Panchanga endpoint serializes its Swiss Ephemeris calls with birth-chart calculations.
