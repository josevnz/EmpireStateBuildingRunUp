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
    Convert to sorted dict. For DataFrames, sorts by the 'Count' column if present,
    otherwise by the last column. For Series, sorts by values.
    """
    if isinstance(df, DataFrame):
        # For DataFrame, convert to records and sort by 'Count' column or last column
        sort_column = 'Count' if 'Count' in df.columns else df.columns[-1]
        sorted_df = df.sort_values(by=sort_column, ascending=False)
        return dict(zip(sorted_df.iloc[:, 0], sorted_df.iloc[:, 1], strict=True))
    else:
        # For Series, sort by values
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
    time_col = RaceFields.TIME.value
    name_col = RaceFields.NAME.value
    age_col = RaceFields.AGE.value

    if criteria == FastestFilters.AGE:
        # Bin ages and find fastest per bin using groupby
        bins = pd.cut(df[age_col], range(10, 110, 10), right=False)
        # Get index of minimum time per age bin - use observed=True to skip unobserved categories
        fastest_idx = df.groupby(bins, observed=True)[time_col].idxmin()
        fastest_runners = df.loc[fastest_idx]
        for bucket, runner in fastest_runners.iterrows():
            results[str(bucket)] = {
                "name": runner[name_col],
                "age": int(runner[age_col]),
                "time": runner[time_col]
            }
    elif criteria == FastestFilters.GENDER:
        # Find fastest per gender using groupby
        gender_col = RaceFields.GENDER.value
        fastest_idx = df.groupby(gender_col, observed=True)[time_col].idxmin()
        fastest_runners = df.loc[fastest_idx]
        for gender, runner in fastest_runners.iterrows():
            results[gender] = {
                "name": runner[name_col],
                "time": runner[time_col]
            }
    elif criteria == FastestFilters.COUNTRY:
        # Find fastest per country using groupby
        country_col = RaceFields.COUNTRY.value
        fastest_idx = df.groupby(country_col, observed=True)[time_col].idxmin()
        fastest_runners = df.loc[fastest_idx]
        for country, runner in fastest_runners.iterrows():
            results[country] = {
                "name": runner[name_col],
                "time": runner[time_col]
            }
    return results