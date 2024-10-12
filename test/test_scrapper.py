"""
Scrapper unit tests
"""
import logging
import pprint
import unittest

from empirestaterunup.data import RaceFields, YearResults
from empirestaterunup.scraper import RacerLinksScraper, RacerDetailsScraper

logger = logging.getLogger('selenium')
logger.setLevel(logging.DEBUG)


class RacerLinksScraperTestCase(unittest.TestCase):
    """
    Run different unit tests
    """
    def test_link_scraper_2023(self):
        """
        Scrape links for 2023. This test takes a while to run
        """
        with RacerLinksScraper(headless=True, debug=False, year=YearResults.RESULTS_2023) as esc:
            self.assertIsNotNone(esc)
            self.assertEqual(377, len(esc.racers))
            self.assertEqual(377, len(esc.rank_to_bib))

    def test_link_scraper_2024(self):
        """
        Scrape links for 2024. This test takes a while to run
        """
        with RacerLinksScraper(headless=True, debug=False, year=YearResults.RESULTS_2024) as esc:
            self.assertIsNotNone(esc)
            self.assertEqual(377, len(esc.racers))
            self.assertEqual(377, len(esc.rank_to_bib))

    def test_runner_detail(self):
        """
        Scraper for runner details
        """
        racer_details = [
            {
                RaceFields.NAME.value: 'David Kilgore',
                RaceFields.URL.value: 'https://www.athlinks.com/event/382111/results/Event/1062909/Course/2407855/Bib/106'
            },
            {
                RaceFields.NAME.value: 'Alejandra Sanchez',
                RaceFields.URL.value: 'https://www.athlinks.com/event/382111/results/Event/1062909/Course/2407855/Bib/40'
            },
            {
                RaceFields.NAME.value: 'Alessandro Manrique',
                RaceFields.URL.value: 'https://www.athlinks.com/event/382111/results/Event/1062909/Course/2407855/Bib/562'
            },
            {
                RaceFields.NAME.value: 'HARPREET Sethi',
                RaceFields.URL.value: 'https://www.athlinks.com/event/382111/results/Event/1062909/Course/2407855/Bib/434'
            }
        ]
        for racer in racer_details:
            name = racer[RaceFields.NAME.value]
            print(f"name={name}, url={racer[RaceFields.URL.value]}")
            with RacerDetailsScraper(
                racer=racer,
                debug_level=0,
            ) as rds:
                self.assertIsNotNone(rds)
                self.assertIsNotNone(rds.racer)
                for field in [
                    RaceFields.TIME.value,
                    RaceFields.PACE.value
                ]:
                    self.assertRegex(rds.racer[field], "\\d+:\\d+", f"{name}: {field}={rds.racer[field]}")
                pprint.pp(rds.racer)


if __name__ == '__main__':
    unittest.main()
