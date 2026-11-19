"""End-to-end smoke test against the pinned real vedic-calc dependency.

This is deliberately a smoke/shape test, not proof of astrological accuracy.
Reference-chart cross-validation is a separate release gate.
"""
import unittest
from datetime import date, time

from app.engine import generate_chart
from app.schemas import ChartRequest
from app.timezones import resolve_local_birth


class RealEngineIntegrationTests(unittest.TestCase):
    def test_real_pinned_engine_generates_full_chart_and_dasha(self):
        request = ChartRequest(
            birth_date=date(1990, 3, 15),
            birth_time=time(10, 30),
            timezone="Asia/Kolkata",
            latitude=19.0760,
            longitude=72.8777,
            ayanamsa="lahiri",
        )
        local_birth, utc_birth, offset = resolve_local_birth(
            request.birth_date, request.birth_time, request.timezone
        )
        result = generate_chart(request, local_birth, utc_birth, offset)

        self.assertEqual(result["calculation"]["engine"], "vedic-calc")
        self.assertEqual(result["calculation"]["engine_commit"], "620d54560ee7e108496495eeb17054a52630a0bf")
        self.assertEqual(result["birth"]["utc_datetime"], "1990-03-15T05:00:00+00:00")
        self.assertEqual(len(result["planets"]), 9)
        self.assertEqual(len(result["houses"]), 12)
        self.assertEqual(len(result["vimshottari_mahadashas"]), 9)
        self.assertTrue(all(0 <= planet["longitude"] < 360 for planet in result["planets"]))
        self.assertTrue(all(1 <= planet["pada"] <= 4 for planet in result["planets"]))
        self.assertEqual(result["planets"][-1]["planet"], "Ketu")
        self.assertTrue(result["planets"][-1]["retrograde"])
        self.assertIn("ephemeris_by_planet", result["calculation"])
        self.assertTrue(result["calculation"]["ephemeris_by_planet"])


if __name__ == "__main__":
    unittest.main()
