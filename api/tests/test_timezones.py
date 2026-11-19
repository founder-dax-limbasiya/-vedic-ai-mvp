import unittest
from datetime import date, time, timezone

from app.timezones import (
    AmbiguousLocalTimeError,
    NonexistentLocalTimeError,
    TimezoneInputError,
    resolve_local_birth,
)


class TimezoneResolutionTests(unittest.TestCase):
    def test_india_offset_and_utc_conversion(self):
        local, utc, offset = resolve_local_birth(date(1990, 3, 15), time(10, 30), "Asia/Kolkata")
        self.assertEqual(offset, 5.5)
        self.assertEqual(local.isoformat(), "1990-03-15T10:30:00+05:30")
        self.assertEqual(utc, local.astimezone(timezone.utc))
        self.assertEqual(utc.isoformat(), "1990-03-15T05:00:00+00:00")

    def test_new_york_nonexistent_spring_time_rejected(self):
        with self.assertRaises(NonexistentLocalTimeError):
            resolve_local_birth(date(2026, 3, 8), time(2, 30), "America/New_York")

    def test_new_york_ambiguous_fall_time_requires_fold(self):
        with self.assertRaises(AmbiguousLocalTimeError):
            resolve_local_birth(date(2026, 11, 1), time(1, 30), "America/New_York")

    def test_new_york_ambiguous_fold_changes_offset(self):
        _, first_utc, first_offset = resolve_local_birth(date(2026, 11, 1), time(1, 30), "America/New_York", 0)
        _, second_utc, second_offset = resolve_local_birth(date(2026, 11, 1), time(1, 30), "America/New_York", 1)
        self.assertEqual(first_offset, -4.0)
        self.assertEqual(second_offset, -5.0)
        self.assertEqual((second_utc - first_utc).total_seconds(), 3600)

    def test_invalid_timezone_rejected(self):
        with self.assertRaises(TimezoneInputError):
            resolve_local_birth(date(1990, 1, 1), time(12, 0), "Mars/Olympus")

    def test_invalid_fold_rejected(self):
        with self.assertRaises(TimezoneInputError):
            resolve_local_birth(date(1990, 1, 1), time(12, 0), "Asia/Kolkata", 2)


if __name__ == "__main__":
    unittest.main()
