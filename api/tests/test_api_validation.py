import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class ApiValidationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_timezone_list_is_available(self):
        response = self.client.get("/v1/timezones?q=Asia/Kolkata")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Asia/Kolkata", response.json()["timezones"])

    def test_invalid_timezone_rejected_before_chart_engine(self):
        response = self.client.post("/v1/chart", json={
            "birth_date": "1990-03-15",
            "birth_time": "10:30",
            "timezone": "Mars/Olympus",
            "latitude": 19.076,
            "longitude": 72.878,
            "ayanamsa": "lahiri",
        })
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["code"], "invalid_timezone")

    def test_future_birth_date_is_rejected(self):
        response = self.client.post("/v1/chart", json={
            "birth_date": "2999-03-15",
            "birth_time": "10:30",
            "timezone": "Asia/Kolkata",
            "latitude": 19.076,
            "longitude": 72.878,
            "ayanamsa": "lahiri",
        })
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["code"], "future_birth_date")

    def test_place_search_is_disabled_without_identifying_user_agent(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get("/v1/places?q=Jamnagar")
        self.assertEqual(response.status_code, 503)
        self.assertIn("NOMINATIM_USER_AGENT", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
