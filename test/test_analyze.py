"""
Multiple tests for data analysis
"""
import unittest

from pandas import DataFrame

from empirestaterunup.analyze import get_5_number, SUMMARY_METRICS, count_by_age, count_by_gender, count_by_wave, \
    dt_to_sorted_dict, get_zscore, get_outliers, age_bins, time_bins, get_country_counts
from empirestaterunup.data import load_data, RaceFields


class AnalyzeTestCase(unittest.TestCase):
    """
    Unit tests for analyze functions
    """
    df: DataFrame

    @classmethod
    def setUpClass(cls) -> None:
        """
        Refresh data setup, class level
        """
        cls.df = load_data()

    def test_get_5_number(self):
        """
        Get 5 number metrics
        """
        for key in SUMMARY_METRICS:
            ndf = get_5_number(criteria=key, data=AnalyzeTestCase.df)
            self.assertIsNotNone(ndf)

    def test_count_by_age(self):
        """
        Test counts by age
        """
        ndf, _ = count_by_age(AnalyzeTestCase.df)
        self.assertIsNotNone(ndf)

    def test_count_by_gender(self):
        """
        Counters by gender
        """
        ndf, _ = count_by_gender(AnalyzeTestCase.df)
        self.assertIsNotNone(ndf)

    def test_count_by_wave(self):
        """
        Test Counts by wave
        """
        ndf, _ = count_by_wave(AnalyzeTestCase.df)
        self.assertIsNotNone(ndf)

    def test_dt_to_sorted_dict(self):
        """
        Test transformation
        """
        ndf, _ = count_by_wave(AnalyzeTestCase.df)
        ndf_dict = dt_to_sorted_dict(ndf)
        self.assertIsNotNone(ndf_dict)
        self.assertLess(0, len(ndf_dict))

    def test_get_zscore(self):
        """
        Get the z-score for summary
        """
        z_score = get_zscore(df=AnalyzeTestCase.df, column=SUMMARY_METRICS[0])
        self.assertIsNotNone(z_score)

    def test_get_outliers(self):
        """
        Analyze outliers
        """
        for column in SUMMARY_METRICS:
            outliers = get_outliers(df=AnalyzeTestCase.df, column=column, std_threshold=3)
            self.assertIsNotNone(outliers)
            self.assertLess(0, outliers.shape[0])
            # print(f"Column {column.title()}:\n{outliers}")
            if column != RaceFields.AGE.value:
                for bib, timedelta in outliers.items():
                    print(f"{column} {bib}: {timedelta.total_seconds()/60.0}")

    def test_age_bins(self):
        """
        make sure age bins are accurate
        """
        cat, _ = age_bins(df=AnalyzeTestCase.df)
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
        cat, _ = time_bins(df=AnalyzeTestCase.df)
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
        country_counts, min_countries, max_countries = get_country_counts(df=AnalyzeTestCase.df)
        self.assertIsNotNone(country_counts)
        self.assertEqual(2, country_counts['JPN'])
        self.assertIsNotNone(min_countries)
        self.assertEqual(3, min_countries.shape[0])
        self.assertIsNotNone(max_countries)
        self.assertEqual(14, max_countries.shape[0])


if __name__ == '__main__':
    unittest.main()
