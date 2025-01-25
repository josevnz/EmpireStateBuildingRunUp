"""
Data loading logic, after web scraping process is completed.
author: Jose Vicente Nunez <kodegeek.com@protonmail.com>
"""
import datetime
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Tuple, Union, List

import pandas
import tomlkit
from pandas import DataFrame, Series
from tomlkit import TOMLDocument

logging.basicConfig(format='%(asctime)s %(message)s', encoding='utf-8', level=logging.INFO)

"""
Runners started on waves, but for basic analysis we will assume all runners were able to run
at the same time.
"""
BASE_RACE_DATETIME = datetime.datetime(
    year=2023,
    month=9,
    day=4,
    hour=20,
    minute=0,
    second=0,
    microsecond=0
)

"""
Interested only in people who completed the 86 floors. So is either full course or dnf
"""


class Level(Enum):
    """
    Course levels
    """
    FULL = "Full Course"
    DNF = "DNF"


class RaceFields(Enum):
    """
    Race fields, sorted by interest
    """
    BIB = "bib"
    NAME = "name"
    OVERALL_POSITION = "overall position"
    TIME = "time"
    GENDER = "gender"
    GENDER_POSITION = "gender position"
    AGE = "age"
    DIVISION_POSITION = "division position"
    COUNTRY = "country"
    STATE = "state"
    CITY = "city"
    PACE = "pace"
    TWENTY_FLOOR_POSITION = "20th floor position"
    TWENTY_FLOOR_GENDER_POSITION = "20th floor gender position"
    TWENTY_FLOOR_DIVISION_POSITION = "20th floor division position"
    TWENTY_FLOOR_PACE = '20th floor pace'
    TWENTY_FLOOR_TIME = '20th floor time'
    SIXTY_FLOOR_POSITION = "65th floor position"
    SIXTY_FIVE_FLOOR_GENDER_POSITION = "65th floor gender position"
    SIXTY_FIVE_FLOOR_DIVISION_POSITION = "65th floor division position"
    SIXTY_FIVE_FLOOR_PACE = '65th floor pace'
    SIXTY_FIVE_FLOOR_TIME = '65th floor time'
    LEVEL = "level"
    URL = "url"


FIELD_NAMES = [x.value for x in RaceFields if x != RaceFields.URL]
FIELD_NAMES_FOR_SCRAPING = [x.value for x in RaceFields]
FIELD_NAMES_AND_POS: Dict[RaceFields, int] = {}
POS = 0
for field in RaceFields:
    FIELD_NAMES_AND_POS[field] = POS
    POS += 1


RACE_RESULTS_FULL_LEVEL = Path(__file__).parent.joinpath("results-full-level-2023.csv")
COUNTRY_DETAILS = Path(__file__).parent.joinpath("country_codes.toml")


def load_data(data_file: Path = None, remove_dnf: bool = True) -> DataFrame:
    """
    * The code remove by default the DNF runners to avoid distortion on the results.
    * Replace unknown/ nan values with the median, to make analysis easier and avoid distortions
    """
    if data_file:
        def_file = data_file
    else:
        def_file = RACE_RESULTS_FULL_LEVEL
    df = pandas.read_csv(
        def_file
    )
    for time_field in [
        RaceFields.PACE.value,
        RaceFields.TIME.value,
        RaceFields.TWENTY_FLOOR_PACE.value,
        RaceFields.TWENTY_FLOOR_TIME.value,
        RaceFields.SIXTY_FIVE_FLOOR_PACE.value,
        RaceFields.SIXTY_FIVE_FLOOR_TIME.value
    ]:
        try:
            df[time_field] = pandas.to_timedelta(df[time_field])
        except ValueError as ve:
            raise ValueError(f'{time_field}={df[time_field]}', ve) from ve
    df['finishtimestamp'] = BASE_RACE_DATETIME + df[RaceFields.TIME.value]
    if remove_dnf:
        df.drop(df[df.level == 'DNF'].index, inplace=True)

    # Normalize Age
    median_age = df[RaceFields.AGE.value].median()
    df[RaceFields.AGE.value] = df[RaceFields.AGE.value].fillna(median_age)
    df[RaceFields.AGE.value] = df[RaceFields.AGE.value].astype(int)

    # Normalize state and city
    df.replace({RaceFields.STATE.value: {'-': ''}}, inplace=True)
    df[RaceFields.STATE.value] = df[RaceFields.STATE.value].fillna('')
    df[RaceFields.CITY.value] = df[RaceFields.CITY.value].fillna('')

    # Normalize overall position, 3 levels
    median_pos = df[RaceFields.OVERALL_POSITION.value].median()
    df[RaceFields.OVERALL_POSITION.value] = df[RaceFields.OVERALL_POSITION.value].fillna(median_pos)
    df[RaceFields.OVERALL_POSITION.value] = df[RaceFields.OVERALL_POSITION.value].astype(int)
    median_pos = df[RaceFields.TWENTY_FLOOR_POSITION.value].median()
    df[RaceFields.TWENTY_FLOOR_POSITION.value] = df[RaceFields.TWENTY_FLOOR_POSITION.value].fillna(median_pos)
    df[RaceFields.TWENTY_FLOOR_POSITION.value] = df[RaceFields.TWENTY_FLOOR_POSITION.value].astype(int)
    median_pos = df[RaceFields.SIXTY_FLOOR_POSITION.value].median()
    df[RaceFields.SIXTY_FLOOR_POSITION.value] = df[RaceFields.SIXTY_FLOOR_POSITION.value].fillna(median_pos)
    df[RaceFields.SIXTY_FLOOR_POSITION.value] = df[RaceFields.SIXTY_FLOOR_POSITION.value].astype(int)

    # Normalize gender position, 3 levels
    median_gender_pos = df[RaceFields.GENDER_POSITION.value].median()
    df[RaceFields.GENDER_POSITION.value] = df[RaceFields.GENDER_POSITION.value].fillna(median_gender_pos)
    df[RaceFields.GENDER_POSITION.value] = df[RaceFields.GENDER_POSITION.value].astype(int)

    median_gender_pos = df[RaceFields.TWENTY_FLOOR_GENDER_POSITION.value].median()
    df[RaceFields.TWENTY_FLOOR_GENDER_POSITION.value] = df[RaceFields.TWENTY_FLOOR_GENDER_POSITION.value].fillna(median_gender_pos)
    df[RaceFields.TWENTY_FLOOR_GENDER_POSITION.value] = df[RaceFields.TWENTY_FLOOR_GENDER_POSITION.value].astype(int)
    median_gender_pos = df[RaceFields.SIXTY_FIVE_FLOOR_GENDER_POSITION.value].median()
    df[RaceFields.SIXTY_FIVE_FLOOR_GENDER_POSITION.value] = df[RaceFields.SIXTY_FIVE_FLOOR_GENDER_POSITION.value].fillna(median_gender_pos)
    df[RaceFields.SIXTY_FIVE_FLOOR_GENDER_POSITION.value] = df[
        RaceFields.SIXTY_FIVE_FLOOR_GENDER_POSITION.value].astype(int)

    # Normalize age/ division position, 3 levels
    median_div_pos = df[RaceFields.DIVISION_POSITION.value].median()
    df[RaceFields.DIVISION_POSITION.value] = df[RaceFields.DIVISION_POSITION.value].fillna(median_div_pos)
    df[RaceFields.DIVISION_POSITION.value] = df[RaceFields.DIVISION_POSITION.value].astype(int)
    median_div_pos = df[RaceFields.TWENTY_FLOOR_DIVISION_POSITION.value].median()
    df[RaceFields.TWENTY_FLOOR_DIVISION_POSITION.value] = df[RaceFields.TWENTY_FLOOR_DIVISION_POSITION.value].fillna(median_div_pos)
    df[RaceFields.TWENTY_FLOOR_DIVISION_POSITION.value] = df[RaceFields.TWENTY_FLOOR_DIVISION_POSITION.value].astype(int)
    median_div_pos = df[RaceFields.SIXTY_FIVE_FLOOR_DIVISION_POSITION.value].median()
    df[RaceFields.SIXTY_FIVE_FLOOR_DIVISION_POSITION.value] = df[RaceFields.SIXTY_FIVE_FLOOR_DIVISION_POSITION.value].fillna(median_div_pos)
    df[RaceFields.SIXTY_FIVE_FLOOR_DIVISION_POSITION.value] = df[
        RaceFields.SIXTY_FIVE_FLOOR_DIVISION_POSITION.value].astype(int)

    # Normalize 65th floor pace and time
    sixty_five_floor_pace_median = df[RaceFields.SIXTY_FIVE_FLOOR_PACE.value].median()
    sixty_five_floor_time_median = df[RaceFields.SIXTY_FIVE_FLOOR_TIME.value].median()
    df[RaceFields.SIXTY_FIVE_FLOOR_PACE.value] = df[RaceFields.SIXTY_FIVE_FLOOR_PACE.value].fillna(sixty_five_floor_pace_median)
    df[RaceFields.SIXTY_FIVE_FLOOR_TIME.value] = df[RaceFields.SIXTY_FIVE_FLOOR_TIME.value].fillna(sixty_five_floor_time_median)

    # Normalize BIB and make it the index
    df[RaceFields.BIB.value] = df[RaceFields.BIB.value].astype(int)
    df.set_index(RaceFields.BIB.value, inplace=True)

    # URL was useful during scraping, not needed for analysis
    df.drop([RaceFields.URL.value], axis=1, inplace=True)

    return df


def df_to_list_of_tuples(
        df: DataFrame,
        bibs: list[int] = None
) -> Union[Tuple | list[Tuple]]:
    """
    Take a DataFrame and return a more friendly structure to be used by a DataTable
    :param df DataFrame to convert
    :param bibs List of racing BIB to filter
    :return list of Tuple of rows, Tuple with columns
    """
    bib_as_column = df.reset_index(level=0, inplace=False)
    if not bibs:
        filtered = bib_as_column
    else:
        filtered = bib_as_column[bib_as_column[RaceFields.BIB.value].isin(bibs)]
    column_names = FIELD_NAMES
    rows = []
    for _, r in filtered.iterrows():
        ind_row: List[Any] = []
        for col in column_names:
            ind_row.append(r[col])
        tpl = tuple(ind_row)
        rows.append(tpl)

    return tuple(column_names), rows


def series_to_list_of_tuples(series: Series) -> list[Tuple]:
    """
    Helper series to list of tuples
    """
    dct = series.to_dict()
    rows = []
    for key, value in dct.items():
        rows.append(tuple([key, value]))
    return rows


def load_country_details(data_file: Path = None) -> TOMLDocument:
    """
    Args:
        data_file (Path): Path to data file in TOML format
    [ISOCountryCodes]
    name = "United States of America"
    alpha-2 = "US"
    alpha-3 = "USA"
    country-code = "840"
    iso_3166-2 = "ISO 3166-2:US"
    region = "Americas"
    sub-region = "Northern America"
    intermediate-region = ""
    region-code = "019"
    sub-region-code = "021"
    intermediate-region-code = ""

    """
    def_file = COUNTRY_DETAILS if data_file is None else data_file
    with open(def_file, 'r', encoding='utf-8') as f:
        data = tomlkit.load(fp=f)
        return data


class CountryColumns(Enum):
    """
    Country columns
    """
    NAME = "name"
    ALPHA_2 = "alpha-2"
    ALPHA_3 = "alpha-3"
    COUNTRY_CODE = "country-code"
    ISO_3166_2 = "iso_3166-2"
    REGION = "region"
    SUB_REGION = "sub-region"
    INTERMEDIATE_REGION = "intermediate-region"
    REGION_CODE = "region-code"
    SUB_REGION_CODE = "sub-region-code"
    INTERMEDIATE_REGION_CODE = "intermediate-region-code"


COUNTRY_COLUMNS = [country.value for country in CountryColumns]


def lookup_country_by_code(country_data: TOMLDocument, three_letter_code: str) -> Union[Tuple[str, TOMLDocument], None]:
    """
    Args:
        country_data (TOMLDocument): TOML document with country details
        three_letter_code: 3-letter ISO code used to filter country
    Returns:
        TOML document with country details, none if the lookup fails
    """
    if not isinstance(three_letter_code, str):
        raise ValueError(f"Invalid type for three letter country code: '{three_letter_code}'")
    if len(three_letter_code) != 3:
        raise ValueError(f"Invalid three letter country code: '{three_letter_code}'")
    for country_name, country_details in country_data.items():
        if three_letter_code == country_details['alpha-3']:
            return country_name, country_details
    return None


def get_times(df: DataFrame) -> DataFrame:
    """
    Get times from dataframe
    """
    return df.select_dtypes(include=['timedelta64', 'datetime64'])


def get_positions(df: DataFrame) -> DataFrame:
    """
    Get positions from dataframe
    """
    return df.select_dtypes(include=['int64'])


def get_categories(df: DataFrame) -> DataFrame:
    """
    Get categories from dataframe
    """
    return df.select_dtypes(include=['object'])


def beautify_race_times(time: datetime.timedelta) -> str:
    """
    Formatting for provided time
    """
    mm, ss = divmod(time.total_seconds(), 60)
    hh, mm = divmod(mm, 60)  # Ignore days part as the race doesn't last more than 24 hours
    return f"{int(hh)}:{int(mm)}:{int(ss)}"
