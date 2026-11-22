import unittest

from fastapi.testclient import TestClient

from app.main import app


class DailyPanchangaTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_jamnagar_daily_panchanga_uses_sunrise(self):
        response = self.client.post("/v1/panchanga", json={
            "calendar_date": "2026-03-08",
            "timezone": "Asia/Kolkata",
            "latitude": 22.4707,
            "longitude": 70.0577,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["date"], "2026-03-08")
        self.assertEqual(data["timezone"], "Asia/Kolkata")
        self.assertEqual(data["calculation_time"], "Local sunrise")
        self.assertTrue(data["vara"])
        self.assertTrue(data["tithi_name"])
        self.assertTrue(data["nakshatra"])
        self.assertTrue(data["yoga_name"])
        self.assertTrue(data["karana_name"])
        self.assertTrue(data["sunrise_local"])
        self.assertTrue(data["sunset_local"])

    def test_jamnagar_transition_times_are_ordered_between_sunrises(self):
        response = self.client.post("/v1/panchanga/transitions", json={
            "calendar_date": "2026-03-08",
            "timezone": "Asia/Kolkata",
            "latitude": 22.4707,
            "longitude": 70.0577,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["date"], "2026-03-08")
        self.assertEqual(data["timezone"], "Asia/Kolkata")
        self.assertTrue(data["sunrise_local"])
        self.assertTrue(data["next_sunrise_local"])
        self.assertEqual(data["ayanamsa"], "lahiri")
        self.assertTrue(data["transitions"])
        times = [item["transition_time_local"] for item in data["transitions"]]
        self.assertEqual(times, sorted(times))
        self.assertTrue(all(item["element"] in {"tithi", "nakshatra", "yoga", "karana"} for item in data["transitions"]))
        self.assertTrue(all(item["from_name"] and item["to_name"] for item in data["transitions"]))
        self.assertIn("Vara changes at sunrise", data["vara_note"])

    def test_invalid_timezone_is_rejected(self):
        response = self.client.post("/v1/panchanga", json={
            "calendar_date": "2026-03-08",
            "timezone": "Mars/Olympus",
            "latitude": 22.4707,
            "longitude": 70.0577,
        })
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["code"], "invalid_local_date")


if __name__ == "__main__":
    unittest.main()
