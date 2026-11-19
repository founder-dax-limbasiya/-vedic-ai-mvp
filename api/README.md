# Vedic AI API

Install with `pip install -e ".[geo]"` from this folder, then run:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`POST /v1/chart` accepts local birth date/time, an IANA timezone, coordinates, and an ayanamsa. It returns:
- D1 planetary placements, ascendant and whole-sign houses.
- 15 standard divisional chart sign maps (D2–D60).
- Birth-time Panchanga (Vara, Tithi, Nakshatra, Yoga and Karana) and local sunrise/sunset.
- Vimshottari Mahadasha periods.
- Per-planet ephemeris source and retrograde-speed diagnostics.

The API processes each chart request without creating a saved birth profile or persisting request bodies.
