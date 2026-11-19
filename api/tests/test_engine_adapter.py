import sys
import types
import unittest
from datetime import date, datetime, time
from enum import IntEnum
from types import SimpleNamespace
from unittest.mock import patch

from app.engine import generate_chart
from app.schemas import ChartRequest
from app.timezones import resolve_local_birth


class FakePlanet(IntEnum):
    SUN = 0
    MOON = 1
    MARS = 2
    MERCURY = 3
    JUPITER = 4
    VENUS = 5
    SATURN = 6
    RAHU = 7
    KETU = 8


class FakeAyanamsa(IntEnum):
    LAHIRI = 1
    RAMAN = 3
    KP = 5
    TRUE_CHITRAPAKSHA = 27


class EngineAdapterTests(unittest.TestCase):
    def test_adapter_shapes_chart_and_uses_speed_flag_status(self):
        class Sign(IntEnum):
            ARIES = 1
        class Nakshatra(IntEnum):
            ASHWINI = 1
        class Position:
            def __init__(self, planet):
                self.longitude = 12.345
                self.sign = Sign.ARIES
                self.degree_in_sign = 12.345
                self.nakshatra_info = SimpleNamespace(
                    nakshatra=Nakshatra.ASHWINI, pada=1, lord=FakePlanet.KETU
                )
                self.is_retrograde = False
        class House:
            def __init__(self, number):
                self.house_number = number
                self.sign = Sign.ARIES
                self.lord = FakePlanet.MARS

        chart = SimpleNamespace(
            planets={planet: Position(planet) for planet in FakePlanet},
            houses=[House(number) for number in range(1, 13)],
            ascendant=Position(None),
            ayanamsa_degrees=23.7,
        )
        class DivisionalPlanet(IntEnum):
            SUN = 0
            MOON = 1
        class DivisionalSign(IntEnum):
            ARIES = 1
            TAURUS = 2
        def fake_divisional(chart_arg, division):
            return SimpleNamespace(
                division=division,
                name=f"Division {division}",
                ascendant_sign=DivisionalSign.ARIES,
                planets={
                    DivisionalPlanet.SUN: DivisionalSign.ARIES,
                    DivisionalPlanet.MOON: DivisionalSign.TAURUS,
                },
            )
        dasha = [SimpleNamespace(
            level="mahadasha", lord=FakePlanet.JUPITER,
            start=datetime(1990, 1, 1), end=datetime(2006, 1, 1), duration_years=16.0
        )]

        fake_package = types.ModuleType("vedic_calc")
        fake_package.__path__ = []
        fake_package.calculate_chart = lambda **kwargs: chart
        fake_package.calculate_dasha = lambda chart_arg, levels=1: dasha
        fake_chart_pkg = types.ModuleType("vedic_calc.chart")
        fake_chart_pkg.__path__ = []
        fake_divisional = types.ModuleType("vedic_calc.chart.divisional")
        fake_divisional.calculate_divisional_chart = fake_divisional if False else lambda chart_arg, division: fake_divisional_chart(chart_arg, division)
        fake_divisional_chart = fake_divisional_factory if False else fake_divisional
        def fake_divisional_factory(chart_arg, division):
            return SimpleNamespace(
                division=division,
                name=f"Division {division}",
                ascendant_sign=Sign.ARIES,
                planets={FakePlanet.SUN: Sign.ARIES, FakePlanet.MOON: Sign.ARIES},
            )
        fake_divisional.calculate_divisional_chart = fake_divisional_factory

        fake_core = types.ModuleType("vedic_calc.core")
        fake_core.__path__ = []
        fake_constants = types.ModuleType("vedic_calc.core.constants")
        fake_constants.Ayanamsa = FakeAyanamsa
        fake_constants.Planet = FakePlanet

        request = ChartRequest(
            birth_date=date(1990, 3, 15), birth_time=time(10, 30),
            timezone="Asia/Kolkata", latitude=19.076, longitude=72.878,
            ayanamsa="lahiri",
        )
        local, utc, offset = resolve_local_birth(
            request.birth_date, request.birth_time, request.timezone
        )
        with patch.dict(sys.modules, {
            "vedic_calc": fake_package,
            "vedic_calc.chart": fake_chart_pkg,
            "vedic_calc.chart.divisional": fake_divisional,
            "vedic_calc.core": fake_core,
            "vedic_calc.core.constants": fake_constants,
        }):
            result = generate_chart(request, local, utc, offset)

        self.assertEqual(result["calculation"]["engine"], "vedic-calc")
        self.assertEqual(len(result["planets"]), 9)
        self.assertEqual(len(result["houses"]), 12)
        self.assertEqual(result["planets"][-1]["planet"], "Ketu")
        self.assertTrue(result["planets"][-1]["retrograde"])
        self.assertEqual(result["vimshottari_mahadashas"][0]["lord"], "Jupiter")
        self.assertEqual(len(result["divisional_charts"]), 16)
        self.assertEqual(result["divisional_charts"]["D9"]["division"], 9)
        self.assertEqual(result["divisional_charts"]["D60"]["planets"][0]["planet"], "Sun")
        self.assertEqual(result["birth"]["utc_datetime"], "1990-03-15T05:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
