"""Coordinate-to-timezone lookups use the pinned offline boundary dataset."""
import unittest

from fastapi.testclient import TestClient

from app.main import app


class LocationTimezoneTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_jamnagar_coordinates_resolve_to_iana_timezone(self):
        response = self.client.get(
            "/v1/place-timezone",
            params={"latitude": 22.4707, "longitude": 70.0577},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["timezone"], "Asia/Kolkata")

    def test_out_of_range_coordinates_rejected(self):
        response = self.client.get(
            "/v1/place-timezone",
            params={"latitude": 122.0, "longitude": 70.0577},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
