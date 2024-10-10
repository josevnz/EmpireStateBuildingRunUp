#!/usr/bin/env python
"""
I wrote this script to normalize the data results from the 'Empire State Building Run-Up', October 4, 2023.
The race results website doesn't offer an export option and quite honestly writing a web scraper seemed to be overkill.
So just coping and pasting the 8 pages of results took less time, the data normalizer is quite simple and was used
to generate a nicer CSV file.

Author Jose Vicente Nunez (kodegeek.com@protonmail.com)
"""
import csv
from pathlib import Path
from argparse import ArgumentParser
import logging

from matplotlib import pyplot as plt

from empirestaterunup.apps import FiveNumberApp, OutlierApp, Plotter, BrowserApp
from empirestaterunup.data import raw_copy_paste_read, FIELD_NAMES, load_data, load_country_details, RaceFields, \
    raw_csv_read, FIELD_NAMES_FOR_SCRAPING
from empirestaterunup.scraper import RacerLinksScraper, RacerDetailsScraper

logging.basicConfig(format='%(asctime)s %(message)s', encoding='utf-8', level=logging.INFO)


def run_raw_cleaner():
    """
    Entry point for raw cleaner
    """
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Enable verbose mode'
    )
    parser.add_argument(
        '--raw_file',
        type=Path,
        required=True,
        help='Raw file'
    )
    parser.add_argument(
        'report_file',
        type=Path,
        help='New report file'
    )
    options = parser.parse_args()
    try:
        with open(options.report_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES, quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for row in raw_copy_paste_read(options.raw_file):
                try:
                    writer.writerow(row)
                    if options.verbose:
                        logging.warning(row)
                except ValueError as ve:
                    raise ValueError(f"row={row}", ve) from ve
    except KeyboardInterrupt:
        pass


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


def run_scraper():
    """
    Entry point for web scraper
    """
    parser = ArgumentParser(description="Website scraper for race results")
    parser.add_argument(
        "report_file",
        action="store",
        type=Path,
        help="Location of the final SCRAPING results"
    )
    options = parser.parse_args()
    report_file = Path(options.report_file)
    logging.info("Saving results to %s", report_file)
    with RacerLinksScraper(headless=True, debug=False) as link_scraper:
        total = len(link_scraper.racers)
        logging.info("Got %s racer results", total)
        with open(report_file, 'w', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=FIELD_NAMES_FOR_SCRAPING, quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for bib in link_scraper.racers:
                url = link_scraper.racers[bib][RaceFields.URL.value]
                logging.info("Processing BIB: %s, will fetch: %s", bib, url)
                with RacerDetailsScraper(racer=link_scraper.racers[bib], debug_level=0) as rds:
                    try:
                        position = link_scraper.racers[bib][RaceFields.OVERALL_POSITION.value]
                        name = link_scraper.racers[bib][RaceFields.NAME.value]
                        writer.writerow(rds.racer)
                        logging.info("Wrote: name=%s, position=%s, %s", name, position, rds.racer)
                    except ValueError as ve:
                        raise ValueError(f"row={rds.racer}", ve) from ve


def run_csv_cleaner():
    """
    Entry point for CSV cleaner
    """
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Enable verbose mode'
    )
    parser.add_argument(
        '--raw_file',
        type=Path,
        required=True,
        help='Raw file'
    )
    parser.add_argument(
        'report_file',
        type=Path,
        help='New report file'
    )
    options = parser.parse_args()
    try:
        with open(options.report_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELD_NAMES_FOR_SCRAPING, quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for row in raw_csv_read(options.raw_file):
                try:
                    writer.writerow(row)
                    if options.verbose:
                        logging.warning(row)
                except ValueError as ve:
                    raise ValueError(f"row={row}", ve) from ve
    except KeyboardInterrupt:
        pass
