"""
Multiple tests for data analysis
"""
import unittest
from typing import List

from pandas import DataFrame

from empirestaterunup.analyze import get_5_number, SUMMARY_METRICS, count_by_age, count_by_gender, \
    get_zscore, get_outliers, age_bins, time_bins, get_country_counts
from empirestaterunup.data import load_json_data, RACE_RESULTS_JSON_FULL_LEVEL


class AnalyzeTestCase(unittest.TestCase):
    """
    Unit tests for analyze functions
    """
    df_list: List[DataFrame] = []

    @classmethod
    def setUpClass(cls) -> None:
        """
        Refresh data setup, class level
        """
        for _, data_file in RACE_RESULTS_JSON_FULL_LEVEL.items():
            AnalyzeTestCase.df_list.append(load_json_data(data_file=data_file))

    def test_get_5_number(self):
        """
        Get 5 number metrics
        """
        for df in self.df_list:
            for key in SUMMARY_METRICS:
                ndf = get_5_number(criteria=key.value, data=df)
                self.assertIsNotNone(ndf)

    def test_count_by_age(self):
        """
        Test counts by age
        """
        for df in self.df_list:
            ndf, _ = count_by_age(df)
            self.assertIsNotNone(ndf)

    def test_count_by_gender(self):
        """
        Counters by gender
        """
        for df in self.df_list:
            ndf, _ = count_by_gender(df)
            self.assertIsNotNone(ndf)

    def test_get_zscore(self):
        """
        Get the z-score for summary
        """
        for df in self.df_list:
            z_score = get_zscore(df=df, column=SUMMARY_METRICS[0].value)
            self.assertIsNotNone(z_score)

    def test_get_outliers(self):
        """
        Analyze outliers
        """
        for column in SUMMARY_METRICS:
            outliers = get_outliers(df=self.df_list[0], column=column.value, std_threshold=3)
            self.assertIsNotNone(outliers)
            self.assertLess(0, outliers.shape[0])
            for bib, value in outliers.items():
                print(f"{column} {bib}: {value}")

    def test_age_bins(self):
        """
        make sure age bins are accurate
        """
        for df in self.df_list:
            cat, _ = age_bins(df=df)
            self.assertIsNotNone(cat)
            val_counts = cat.value_counts()
            self.assertIsNotNone(val_counts)
            for category, count in val_counts.items():
                self.assertIsNotNone(category)
                self.assertIsNotNone(count)

    def test_time_bins(self):
        """
        Make sure time bins are accurate
        """
        for df in self.df_list:
            cat, _ = time_bins(df=df)
            self.assertIsNotNone(cat)
            val_counts = cat.value_counts()
            self.assertIsNotNone(val_counts)
            for category, count in val_counts.items():
                self.assertIsNotNone(category)
                self.assertIsNotNone(count)

    def test_get_country_counts(self):
        """
        Check if country counts match
        """
        country_counts, min_countries, max_countries = get_country_counts(self.df_list[0])
        self.assertIsNotNone(country_counts)
        self.assertEqual(2, country_counts['Japan'])
        self.assertIsNotNone(min_countries)
        self.assertEqual(3, min_countries.shape[0])
        self.assertIsNotNone(max_countries)
        self.assertEqual(14, max_countries.shape[0])


if __name__ == '__main__':
    unittest.main()
