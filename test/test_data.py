"""
Unit tests for data loading
"""
import unittest

from pandas import Series

from empirestaterunup.analyze import find_fastest, FastestFilters
from empirestaterunup.data import load_data, Waves, get_wave_from_bib, get_description_for_wave, get_wave_start_time, \
    df_to_list_of_tuples, load_country_details, lookup_country_by_code, get_times, get_positions, \
    get_categories, RaceFields, series_to_list_of_tuples, \
    FIELD_NAMES_AND_POS, CountryColumns


class DataTestCase(unittest.TestCase):
    """
    Uni tests for data loading
    """
    def test_load_data(self):
        """
        Load data
        """
        data = load_data()
        self.assertIsNotNone(data)
        for row in data:
            self.assertIsNotNone(row)

    def test_get_wave_from_bib(self):
        """
        Get the wave, based on the BIB
        """
        self.assertEqual(Waves.ELITE_MEN, get_wave_from_bib(1))
        self.assertEqual(Waves.ELITE_WOMEN, get_wave_from_bib(26))
        self.assertEqual(Waves.PURPLE, get_wave_from_bib(100))
        self.assertEqual(Waves.GREEN, get_wave_from_bib(200))
        self.assertEqual(Waves.ORANGE, get_wave_from_bib(300))
        self.assertEqual(Waves.GREY, get_wave_from_bib(400))
        self.assertEqual(Waves.GOLD, get_wave_from_bib(500))
        self.assertEqual(Waves.BLACK, get_wave_from_bib(600))

    def test_get_description_for_wave(self):
        """
        Get the description for the wave
        """
        self.assertEqual(Waves.ELITE_MEN.value[0], get_description_for_wave(Waves.ELITE_MEN))

    def test_get_wave_start_time(self):
        """
        Get the wave start time
        """
        self.assertEqual(Waves.ELITE_MEN.value[-1], get_wave_start_time(Waves.ELITE_MEN))

    def test_to_list_of_tuples(self):
        """
        Conversion
        """
        data = load_data()
        self.assertIsNotNone(data)

        header, rows = df_to_list_of_tuples(data)
        self.assertIsNotNone(header)
        self.assertIsNotNone(rows)
        self.assertEqual(375, len(rows))

        header, rows = df_to_list_of_tuples(data, bibs=[537, 19])
        self.assertIsNotNone(header)
        self.assertIsNotNone(rows)
        self.assertEqual(2, len(rows))

        header, rows = df_to_list_of_tuples(data, bibs=[999, 10004])
        self.assertIsNotNone(header)
        self.assertIsNotNone(rows)
        self.assertEqual(0, len(rows))

    def test_series_to_list_of_tuples(self):
        """
        Conversion
        """
        data = load_data()
        self.assertIsNotNone(data)
        countries: Series = data[RaceFields.COUNTRY.value]
        rows = series_to_list_of_tuples(countries)
        self.assertIsNotNone(rows)

    def test_load_country_details(self):
        """
        Load country details
        """
        countries = load_country_details()
        self.assertIsNotNone(countries)
        for name, data in countries.items():
            self.assertIsNotNone(name)
            self.assertIsNotNone(data)

    def test_country_lookup(self):
        """
        Lookup country codes. Also checks than the country data is complete
        """
        run_data = load_data()
        self.assertIsNotNone(run_data)
        country_data = load_country_details()
        self.assertIsNotNone(country_data)
        _, rows = df_to_list_of_tuples(run_data)
        country_idx = FIELD_NAMES_AND_POS[RaceFields.COUNTRY]
        for row in rows:
            country_code = row[country_idx]
            name, details = lookup_country_by_code(
                country_data=country_data,
                three_letter_code=country_code
            )
            self.assertIsNotNone(name)
            self.assertIsNotNone(details)
            for column in [country.value for country in CountryColumns if country.value != CountryColumns.NAME.value]:
                self.assertIsNotNone(details[column])

    def test_get_times(self):
        """
        Get times from the data
        """
        run_data = load_data()
        self.assertIsNotNone(run_data)
        df = get_times(run_data)
        self.assertIsNotNone(df)
        self.assertEqual(375, df.shape[0])

    def test_get_positions(self):
        """
        Get positions from the data
        """
        run_data = load_data()
        self.assertIsNotNone(run_data)
        df = get_positions(run_data)
        self.assertIsNotNone(df)
        self.assertEqual(375, df.shape[0])

    def test_get_categories(self):
        """
        Get categories from the data
        """
        run_data = load_data()
        self.assertIsNotNone(run_data)
        df = get_categories(run_data)
        self.assertIsNotNone(df)
        self.assertEqual(375, df.shape[0])

    def test_find_fastest(self):
        """
        Get the fastest runners on the dataset
        """
        run_data = load_data()
        self.assertIsNotNone(run_data)

        fastest = find_fastest(run_data, FastestFilters.GENDER)
        self.assertIsNotNone(fastest)
        self.assertTrue(fastest)
        self.assertEqual(3, len(fastest))

        fastest = find_fastest(run_data, FastestFilters.COUNTRY)
        self.assertIsNotNone(fastest)
        self.assertTrue(fastest)
        self.assertEqual(18, len(fastest))

        fastest = find_fastest(run_data, FastestFilters.AGE)
        self.assertIsNotNone(fastest)
        self.assertTrue(fastest)
        self.assertEqual(7, len(fastest))


if __name__ == '__main__':
    unittest.main()
