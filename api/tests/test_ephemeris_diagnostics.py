import unittest

import swisseph as swe

from app.engine import _ephemeris_name


class EphemerisDiagnosticsTests(unittest.TestCase):
    def test_reports_one_of_the_actual_sources(self):
        jd = swe.julday(1990, 3, 15, 5.0)
        _, flags = swe.calc_ut(jd, swe.SUN, 0)
        self.assertIn(_ephemeris_name(flags), {
            "JPL", "Swiss Ephemeris", "Moshier analytical fallback"
        })

    def test_speed_flag_returns_nonzero_planetary_motion(self):
        jd = swe.julday(1990, 3, 15, 5.0)
        position_without_speed, _ = swe.calc_ut(jd, swe.MARS, 0)
        position_with_speed, flags = swe.calc_ut(jd, swe.MARS, swe.FLG_SPEED)
        self.assertEqual(position_without_speed[3], 0.0)
        self.assertNotEqual(position_with_speed[3], 0.0)
        self.assertTrue(flags & swe.FLG_SPEED)


if __name__ == "__main__":
    unittest.main()
