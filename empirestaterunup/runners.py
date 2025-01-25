#!/usr/bin/env python
"""
I wrote this script to normalize the data results from the 'Empire State Building Run-Up', October 4, 2023.
The race results website doesn't offer an export option and quite honestly writing a web scraper seemed to be overkill.
So just coping and pasting the 8 pages of results took less time, the data normalizer is quite simple and was used
to generate a nicer CSV file.

Author Jose Vicente Nunez (kodegeek.com@protonmail.com)
"""
from pathlib import Path
from argparse import ArgumentParser
import logging

from matplotlib import pyplot as plt

from empirestaterunup.apps import FiveNumberApp, OutlierApp, Plotter, BrowserApp
from empirestaterunup.data import load_data, load_country_details

logging.basicConfig(format='%(asctime)s %(message)s', encoding='utf-8', level=logging.INFO)


def run_5_number():
    """
    Entry point for 5 number app
    """
    parser = ArgumentParser(description="5 key indicators report")
    parser.add_argument(
        "results",
        action="store",
        type=Path,
        nargs="*",
        help="Race results."
    )
    options = parser.parse_args()
    app = FiveNumberApp()
    if options.results:
        FiveNumberApp.DF = load_data(options.results[0])
    else:
        FiveNumberApp.DF = load_data()
    app.title = "Five Number Summary".title()
    app.sub_title = f"Runners: {FiveNumberApp.DF.shape[0]}"
    app.run()


def run_outlier():
    """
    Entry point for outlier app
    """
    parser = ArgumentParser(description="Show race outliers")
    parser.add_argument(
        "results",
        action="store",
        type=Path,
        nargs="*",
        help="Race results."
    )
    options = parser.parse_args()
    if options.results:
        OutlierApp.DF = load_data(options.results[0])
    else:
        OutlierApp.DF = load_data()
    app = OutlierApp()
    app.title = "Outliers Summary".title()
    app.sub_title = f"Runners: {OutlierApp.DF.shape[0]}"
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
        type=Path,
        nargs="*",
        help="Race results."
    )
    options = parser.parse_args()
    plt.style.use('fivethirtyeight')  # Common style for all the plots
    if options.results:
        pzs = Plotter(options.results[0])
    else:
        pzs = Plotter()
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
        type=Path,
        nargs="*",
        help="Race results."
    )
    options = parser.parse_args()
    df = None
    country_df = None
    if options.results:
        df = load_data(options.results[0])
    if options.country:
        country_df = load_country_details(options.country)
    app = BrowserApp(
        df=df,
        country_data=country_df
    )
    app.title = "Race runners".title()
    app.sub_title = f"Browse details: {app.df.shape[0]}"
    app.run()
