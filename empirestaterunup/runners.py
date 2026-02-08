#!/usr/bin/env python
"""
I wrote this script to normalize the data results from the 'Empire State Building Run-Up', October 4, 2023.

Author Jose Vicente Nunez (kodegeek.com@protonmail.com)
"""
import json
import logging
from argparse import ArgumentParser
from pathlib import Path

from matplotlib import pyplot as plt

from empirestaterunup.apps import BrowserApp, FiveNumberApp, OutlierApp, Plotter
from empirestaterunup.data import (
    DEFAULT_YEAR,
    RACE_RESULTS_JSON_FULL_LEVEL,
    load_country_details,
    load_json_data,
)
from empirestaterunup.devtools import enrich_race_results

logging.basicConfig(format='%(asctime)s %(message)s', encoding='utf-8', level=logging.INFO)
RESULTS = list(RACE_RESULTS_JSON_FULL_LEVEL.keys())


def run_5_number():
    """
    Entry point for 5 number app
    """
    parser = ArgumentParser(description="5 key indicators report")
    parser.add_argument(
        "results",
        action="store",
        type=int,
        choices=RESULTS,
        default=DEFAULT_YEAR,
        nargs='?',
        help="Race results."
    )
    options = parser.parse_args()
    if options.results:
        FiveNumberApp.DF = load_json_data(data_file=RACE_RESULTS_JSON_FULL_LEVEL[options.results])
    else:
        FiveNumberApp.DF = load_json_data()
    app = FiveNumberApp()
    app.title = "Five Number Summary".title()
    app.sub_title = f"Runners: {FiveNumberApp.DF.shape[0]} (Year: {options.results})"
    app.run()


def run_outlier():
    """
    Entry point for outlier app
    """
    parser = ArgumentParser(description="Show race outliers")
    parser.add_argument(
        "results",
        action="store",
        type=int,
        choices=RESULTS,
        default=DEFAULT_YEAR,
        nargs='?',
        help="Race results."
    )
    options = parser.parse_args()
    if options.results:
        OutlierApp.DF = load_json_data(data_file=RACE_RESULTS_JSON_FULL_LEVEL[options.results], use_pretty=False)
    else:
        OutlierApp.DF = load_json_data(use_pretty=False)
    app = OutlierApp()
    app.title = "Outliers Summary".title()
    app.sub_title = f"Runners: {OutlierApp.DF.shape[0]} (Year: {options.results})"
    app.run()


def simple_plot():
    """
    Entry point for simple plot
    """
    parser = ArgumentParser(description="Different Age plots for Empire State RunUp")
    parser.add_argument(
        "--type",
        action="store",
        default="box",
        choices=["box", "hist"],
        help="Plot type. Not all reports honor this choice (like country)"
    )
    parser.add_argument(
        "--report",
        action="store",
        default="age",
        choices=["age", "country", "gender"],
        help="Report type"
    )
    parser.add_argument(
        "results",
        action="store",
        type=int,
        choices=RESULTS,
        default=DEFAULT_YEAR,
        nargs='?',
        help="Race results."
    )
    options = parser.parse_args()
    plt.style.use('fivethirtyeight')  # Common style for all the plots
    if options.results:
        pzs = Plotter(data_file=RACE_RESULTS_JSON_FULL_LEVEL[options.results], year=options.results)
    else:
        pzs = Plotter(year=options.results)
    if options.report == 'age':
        pzs.plot_age(options.type)
    elif options.report == 'country':
        pzs.plot_country()
    elif options.report == 'gender':
        pzs.plot_gender()
    plt.show()


def run_browser():
    """
    Entry point for runner browser app
    """
    parser = ArgumentParser(description="Browse user results")
    parser.add_argument(
        "--country",
        action="store",
        type=Path,
        required=False,
        help="Country details"
    )
    parser.add_argument(
        "results",
        action="store",
        type=int,
        choices=RESULTS,
        default=DEFAULT_YEAR,
        nargs='?',
        help="Race results."
    )
    options = parser.parse_args()
    country_df = None
    df = load_json_data(data_file=RACE_RESULTS_JSON_FULL_LEVEL[options.results], use_pretty=True)
    if options.country:
        country_df = load_country_details(data_file=options.country)
    app = BrowserApp(df=df, country_data=country_df)
    app.title = "Race runners".title()
    app.sub_title = f"Browse details: {app.df.shape[0]} (Year: {options.results})"
    app.run()


def run_enricher():
    """
    Entry point to run race results raw data enricher
    """
    parser = ArgumentParser(description="Enrich race results")
    parser.add_argument(
        "--location-lookup-file",
        action="store",
        type=Path,
        required=True,
        help="Location lookup toml file "
    )
    parser.add_argument(
        "--raw-race-results-file",
        action="store",
        type=Path,
        required=True,
        help="Location of raw race results"
    )
    parser.add_argument(
        "enriched_race_results_file",
        action="store",
        type=Path,
        help="Destination of enriched race results"
    )
    options = parser.parse_args()
    if options.enriched_race_results_file == options.raw_race_results_file:
        raise ValueError("Raw race results cannot be the same as the enriched file!")

    enriched_data = enrich_race_results(
        race_results_file=options.raw_race_results_file,
        location_lookup_file=options.location_lookup_file
    )
    with open(options.enriched_race_results_file.as_posix(), 'w') as outfile:
        for race_result in enriched_data:
            print(json.dumps(race_result), file=outfile)
