"""
Analyze original race results and give back canned reports
author: Jose Vicente Nunez <kodegeek.com@protonmail.com>
"""
from datetime import timedelta
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from pandas import Categorical, DataFrame, Series

from empirestaterunup.data import RaceFields

SUMMARY_METRICS = (RaceFields.AGE, RaceFields.TIME)


class FastestFilters(Enum):
    """
    Enum to track important filter features
    """
    GENDER = 0
    AGE = 1
    COUNTRY = 2


def get_5_number(criteria: str, data: DataFrame) -> DataFrame:
    """
    Get the 5 number stats using Pandas
    """
    return data[criteria].describe()


def count_by_age(data: DataFrame) -> tuple[DataFrame, tuple[str, str]]:
    """
    Counts by age
    """
    counts = data[RaceFields.AGE.value].value_counts().sort_index()
    return counts.rename_axis(RaceFields.AGE.value).reset_index(name='Count'), ('Age', 'Count')


def count_by_gender(data: DataFrame) -> tuple[DataFrame, tuple[str, str]]:
    """
    Counts by gender
    """
    counts = data[RaceFields.GENDER.value].value_counts().sort_index()
    return counts.rename_axis(RaceFields.GENDER.value).reset_index(name='Count'), ('Gender', 'Count')


def dt_to_sorted_dict(df: DataFrame | Series) -> dict[str, Any]:
    """
    Convert to sorted dict
    """
    return dict(sorted(df.to_dict().items(), key=lambda item: item[1], reverse=True))


def get_zscore(df: DataFrame, column: str):
    """
    Get Z-score for given column
    """
    filtered = df[column]
    mean = filtered.mean()
    std = filtered.std(ddof=0)
    return (filtered - mean) / std


def get_outliers(df: DataFrame, column: str, std_threshold: int = 3) -> Series:
    """
    Use the z-score, anything further away than 3 standard deviations is considered an outlier.
    """
    z_scores = get_zscore(df=df, column=column)
    return df[column][np.abs(z_scores) > std_threshold]


def age_bins(df: DataFrame) -> tuple[Categorical, tuple[str, str]]:
    """
    Group ages into age buckets
    """
    bins = pd.cut(df[RaceFields.AGE.value], range(10, 110, 10), right=False)
    return bins.rename('Age Bucket'), ('Age', 'Count')


def time_bins(df: DataFrame) -> tuple[Categorical, tuple[str, str]]:
    """
    Group finish times into time buckets
    """
    bins = pd.cut(df[RaceFields.TIME.value], [timedelta(minutes=i * 10) for i in range(13)], right=False)
    return bins.rename('Time Bucket'), ('Time', 'Count')


def get_country_counts(df: DataFrame, min_participants: int = 5, max_participants: int = 5) -> tuple[Series, Series, Series]:
    """
    Gen interesting country counts
    :param df DataFrame to query
    :param min_participants Minimum number of participants, filter out above this value
    :param max_participants Maximum number of participants, filter out below this value
    :return country counts (unfiltered), countries, which countries with less than max_participants grouped under 'Others'
    """
    countries = df[RaceFields.COUNTRY.value]
    counts = countries.value_counts()
    min_count_filter = counts[counts > min_participants]
    max_count_filter = counts[counts < max_participants]
    others = pd.Series({'Others': counts.sum()})
    return counts, pd.concat([min_count_filter, others]), max_count_filter


def find_fastest(df: DataFrame, criteria: FastestFilters) -> dict[str, Any]:
    """
    Find the fastest runners, per category
    :param df Dataframe to analyze
    :param criteria Filtering rules
    :return Dictionary with the fastest runners, includes criteria and value
    """
    results = {}
    if criteria == FastestFilters.AGE:
        bins = pd.cut(df[RaceFields.AGE.value], range(10, 110, 10), right=False)
        for bucket in bins.unique():
            runners_by_bucket = df[bins == bucket]
            fastest_time = runners_by_bucket[RaceFields.TIME.value].min()
            fastest_runner = runners_by_bucket[runners_by_bucket[RaceFields.TIME.value] == fastest_time]
            results[str(bucket)] = {
                "name": fastest_runner.iloc[0][RaceFields.NAME.value],
                "age": int(fastest_runner.iloc[0][RaceFields.AGE.value]),
                "time": fastest_time
            }
    elif criteria == FastestFilters.GENDER:
        for gender in df[RaceFields.GENDER.value].unique():
            runners_by_gender = df[df[RaceFields.GENDER.value] == gender]
            fastest_time = runners_by_gender[RaceFields.TIME.value].min()
            fastest_runner = runners_by_gender[runners_by_gender[RaceFields.TIME.value] == fastest_time]
            results[gender] = {
                "name": fastest_runner.iloc[0][RaceFields.NAME.value],
                "time": fastest_time
            }
    elif criteria == FastestFilters.COUNTRY:
        for country in df[RaceFields.COUNTRY.value].unique():
            runners_by_country = df[df[RaceFields.COUNTRY.value] == country]
            fastest_time = runners_by_country[RaceFields.TIME.value].min()
            fastest_runner = runners_by_country[runners_by_country[RaceFields.TIME.value] == fastest_time]
            results[country] = {
                "name": fastest_runner.iloc[0][RaceFields.NAME.value],
                "time": fastest_time
            }
    return results
