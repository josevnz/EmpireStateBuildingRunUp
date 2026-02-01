import unittest
from pathlib import Path

from empirestaterunup.data import LOCATION_DETAILS, RaceFields
from empirestaterunup.devtools import enrich_race_results

TEST_RACE_FILE = Path(__file__).parent.joinpath("results-raw-2025.jsonl")


class DevtoolsTestCase(unittest.TestCase):
    def test_enrich_race_results(self):
        rr = enrich_race_results(race_results_file=TEST_RACE_FILE, location_lookup_file=LOCATION_DETAILS)
        self.assertIsNotNone(rr)
        for rs in rr:
            self.assertNotEquals('', rs[RaceFields.COUNTRY.value])


if __name__ == '__main__':
    unittest.main()
