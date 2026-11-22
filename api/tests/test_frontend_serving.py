import unittest

from fastapi.testclient import TestClient

from app.main import app


class FrontendServingTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_serves_mobile_app(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("Jyoti", response.text)

    def test_pwa_png_icons_are_served(self):
        for path in ("/icon-192.png", "/icon-512.png", "/icon-maskable-512.png", "/apple-touch-icon.png"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn("image/png", response.headers.get("content-type", ""))
