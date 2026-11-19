# Vedic AI API

Install with `pip install -e ".[geo]"` from this folder, then run:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`POST /v1/chart` accepts local birth date/time, an IANA timezone, coordinates, and an ayanamsa. It returns calculated chart facts and the upstream engine/ephemeris metadata. It does not persist request bodies.
