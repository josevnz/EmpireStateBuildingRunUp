"""
Unit tests for data loading
"""
import unittest
import warnings

from pandas import Series

from empirestaterunup.analyze import find_fastest, FastestFilters
from empirestaterunup.data import \
    df_to_list_of_tuples, load_country_details, lookup_country_by_code, get_times, get_positions, \
    get_categories, series_to_list_of_tuples, \
    CountryColumns, load_json_data, RACE_RESULTS_JSON_FULL_LEVEL, RaceFields


class DataTestCase(unittest.TestCase):
    """
    Uni tests for data loading
    """

    def test_load_json_data(self):
        """
        Load data in JSON format from https://github.com/josevnz/athlinks-races/
        """
        for year in RACE_RESULTS_JSON_FULL_LEVEL:
            warnings.warn(UserWarning(f"Loading {year}={RACE_RESULTS_JSON_FULL_LEVEL[year]}"))
            data = load_json_data(RACE_RESULTS_JSON_FULL_LEVEL[year])
            self.assertIsNotNone(data)
            for row in data:
                self.assertIsNotNone(row)

    def test_load_json_data2(self):
        """
        Load data in CSV format, using defaults
        """
        data = load_json_data()
        self.assertIsNotNone(data)
        for row in data:
            self.assertIsNotNone(row)

    def test_to_list_of_tuples(self):
        """
        Conversion
        """
        data = load_json_data(data_file=RACE_RESULTS_JSON_FULL_LEVEL[2023])
        self.assertIsNotNone(data)

        header, rows = df_to_list_of_tuples(data)
        self.assertIsNotNone(header)
        self.assertIsNotNone(rows)
        self.assertEqual(376, len(rows))

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
        for data_file in RACE_RESULTS_JSON_FULL_LEVEL.values():
            data = load_json_data(data_file=data_file)
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
        country_data = load_country_details()
        self.assertIsNotNone(country_data)
        for country_code in ["US", "USA", "VE", "VEN", "IT"]:
            name, details = lookup_country_by_code(country_data=country_data, letter_code=country_code)
            self.assertIsNotNone(name)
            self.assertIsNotNone(details)
            for column in [country.value for country in CountryColumns if country.value != CountryColumns.NAME.value]:
                self.assertIsNotNone(details[column])

        for country_code in ["XX", "XXX"]:
            self.assertIsNone(lookup_country_by_code(country_data=country_data, letter_code=country_code))

        try:
            _ = lookup_country_by_code(country_data=country_data, letter_code="XXXX")
            self.fail("I was expected an exception for an invalid country code!")
        except ValueError:
            pass

    def test_get_times(self):
        """
        Get times from the data
        """
        run_data = load_json_data(data_file=RACE_RESULTS_JSON_FULL_LEVEL[2023])
        self.assertIsNotNone(run_data)
        df = get_times(run_data)
        self.assertIsNotNone(df)
        self.assertEqual(376, df.shape[0])

    def test_get_positions(self):
        """
        Get positions from the data
        """
        run_data = load_json_data(data_file=RACE_RESULTS_JSON_FULL_LEVEL[2023])
        self.assertIsNotNone(run_data)
        df = get_positions(run_data)
        self.assertIsNotNone(df)
        self.assertEqual(376, df.shape[0])

    def test_get_categories(self):
        """
        Get categories from the data
        """
        run_data = load_json_data(data_file=RACE_RESULTS_JSON_FULL_LEVEL[2023])
        self.assertIsNotNone(run_data)
        df = get_categories(run_data)
        self.assertIsNotNone(df)
        self.assertEqual(376, df.shape[0])

    def test_find_fastest(self):
        """
        Get the fastest runners on the dataset
        """
        run_data = load_json_data(data_file=RACE_RESULTS_JSON_FULL_LEVEL[2023])
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
