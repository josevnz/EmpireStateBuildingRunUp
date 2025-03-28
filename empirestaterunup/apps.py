"""
Collection of applications to display race findings
author: Jose Vicente Nunez <kodegeek.com@protonmail.com>
"""
from enum import Enum
from pathlib import Path
from typing import Type

from pandas import DataFrame, Timedelta
from rich.text import Text
from textual import on
from textual.app import ComposeResult, App, CSSPathType
from textual.containers import Vertical
from textual.driver import Driver
from textual.widgets import DataTable, Footer, Header, Label
import matplotlib.pyplot as plt

from empirestaterunup.analyze import SUMMARY_METRICS, get_5_number, count_by_age, count_by_gender, \
    dt_to_sorted_dict, get_outliers, age_bins, time_bins, get_country_counts, FastestFilters, \
    find_fastest
from empirestaterunup.data import df_to_list_of_tuples, load_country_details, \
    RaceFields, series_to_list_of_tuples, beautify_race_times, \
    load_json_data
from empirestaterunup.providers import BrowserAppCommand
from empirestaterunup.screens import RunnerDetailScreen, OutlierDetailScreen


class FiveNumberApp(App):
    """
    Application to display 5 numbers
    """
    DF: DataFrame = None
    BINDINGS = [("q", "quit_app", "Quit")]
    FIVE_NUMBER_FIELDS = ('count', 'mean', 'std', 'min', 'max', '25%', '50%', '75%')
    CSS_PATH = "five_numbers.tcss"

    class NumbersTables(Enum):
        """
        Important metrics for 5 number application
        """
        SUMMARY = 'Summary'
        COUNT_BY_AGE = 'Count By Age'
        GENDER_BUCKET = 'Gender Bucket'
        AGE_BUCKET = 'Age Bucket'
        TIME_BUCKET = 'Time Bucket'
        COUNTRY_COUNTS = 'Country Counts'

    ENABLE_COMMAND_PALETTE = False
    current_sorts: set = set()

    def action_quit_app(self):
        """
        Exit handler
        """
        self.exit(0)

    def compose(self) -> ComposeResult:
        """
        UI component layout
        """
        yield Header(show_clock=True)
        for table_id in FiveNumberApp.NumbersTables:
            table = DataTable(id=table_id.name)
            table.cursor_type = 'row'
            table.zebra_stripes = True
            yield Vertical(
                Label(str(table_id.value)),
                table
            )
        yield Footer()

    def on_mount(self) -> None:
        """
        Initialize component contents
        """

        summary_table = self.get_widget_by_id(id=self.NumbersTables.SUMMARY.name, expect_type=DataTable)
        columns = [x.title() for x in FiveNumberApp.FIVE_NUMBER_FIELDS]
        columns.insert(0, 'Summary (Minutes)')
        summary_table.add_columns(*columns)
        for metric in SUMMARY_METRICS:
            ndf = get_5_number(criteria=metric.value, data=FiveNumberApp.DF)
            rows = [ndf[field] for field in FiveNumberApp.FIVE_NUMBER_FIELDS]
            rows.insert(0, metric.value.title())
            rows[1] = int(rows[1])
            for idx in range(2, len(rows)):  # Pretty print running times
                if isinstance(rows[idx], Timedelta):
                    rows[idx] = f"{rows[idx].total_seconds() / 60.0:.2f}"
            summary_table.add_row(*rows)

        age_table = self.get_widget_by_id(id=self.NumbersTables.COUNT_BY_AGE.name, expect_type=DataTable)
        adf, age_header = count_by_age(FiveNumberApp.DF)
        for column in age_header:
            age_table.add_column(column, key=column)
        age_table.add_rows(dt_to_sorted_dict(adf).items())

        gender_table = self.get_widget_by_id(id=self.NumbersTables.GENDER_BUCKET.name, expect_type=DataTable)
        gdf, gender_header = count_by_gender(FiveNumberApp.DF)
        for column in gender_header:
            gender_table.add_column(column, key=column)
        gender_table.add_rows(dt_to_sorted_dict(gdf).items())

        age_bucket_table = self.get_widget_by_id(id=self.NumbersTables.AGE_BUCKET.name, expect_type=DataTable)
        age_categories, age_cols_head = age_bins(FiveNumberApp.DF)
        for column in age_cols_head:
            age_bucket_table.add_column(column, key=column)
        age_bucket_table.add_rows(dt_to_sorted_dict(age_categories.value_counts()).items())

        time_bucket_table = self.get_widget_by_id(id=self.NumbersTables.TIME_BUCKET.name, expect_type=DataTable)
        time_categories, time_cols_head = time_bins(FiveNumberApp.DF)
        for column in time_cols_head:
            time_bucket_table.add_column(column, key=column)
        times = dt_to_sorted_dict(time_categories.value_counts()).items()
        time_bucket_table.add_rows(times)

        country_counts_table = self.get_widget_by_id(id=self.NumbersTables.COUNTRY_COUNTS.name, expect_type=DataTable)
        countries_counts, _, _ = get_country_counts(FiveNumberApp.DF)
        rows = series_to_list_of_tuples(countries_counts)
        for column in ['Country', 'Count']:
            country_counts_table.add_column(column, key=column)
        country_counts_table.add_rows(rows)

        self.notify(
            message=f"All metrics were calculated for {FiveNumberApp.DF.shape[0]} runners.",
            title="Race statistics status",
            severity="information"
        )

    def sort_reverse(self, sort_type: str):
        """
        Toggle sort type. To be passed to sort method
        """
        reverse = sort_type in self.current_sorts
        if reverse:
            self.current_sorts.remove(sort_type)
        else:
            self.current_sorts.add(sort_type)
        return reverse

    @on(DataTable.HeaderSelected)
    def on_header_clicked(self, event: DataTable.HeaderSelected):
        """
        Handler when user clicks the table header
        """
        table = event.data_table
        if table.id != 'SUMMARY':
            table.sort(
                event.column_key,
                reverse=self.sort_reverse(event.column_key.value)
            )


class OutlierApp(App):
    """
    Outlier application
    """
    DF: DataFrame = None
    BINDINGS = [
        ("q", "quit_app", "Quit"),
    ]
    CSS_PATH = "outliers.tcss"
    ENABLE_COMMAND_PALETTE = False
    current_sorts: set = set()

    def action_quit_app(self):
        """
        Exit handler
        """
        self.exit(0)

    def compose(self) -> ComposeResult:
        """
        Layout UI elements
        """
        yield Header(show_clock=True)
        for column_name in SUMMARY_METRICS:
            table = DataTable(id=f'col_{column_name.name}_outlier')
            table.cursor_type = 'row'
            table.zebra_stripes = True
            table.tooltip = "Get runner details"
            if column_name == RaceFields.AGE:
                label = Label(f"{column_name.value} (older) outliers (Minutes):".title())
            else:
                label = Label(f"{column_name.value} (slower) outliers (Minutes):".title())
            yield Vertical(
                label,
                table
            )
        yield Footer()

    def on_mount(self) -> None:
        """
        Initialize UI elements
        """
        for column in SUMMARY_METRICS:
            table = self.get_widget_by_id(f'col_{column.name}_outlier', expect_type=DataTable)
            columns = [x.title() for x in ['bib', column.value]]
            table.add_columns(*columns)
            outliers = get_outliers(df=OutlierApp.DF, column=column.value)
            self.log.info(f"Outliers {column}: {outliers} ({len(outliers.keys())})")
            if column == RaceFields.AGE:
                transformed_outliers = outliers.to_dict().items()
            else:
                transformed_outliers = []
                for bib, timedelta in outliers.items():
                    transformed_outliers.append((bib, f"{timedelta.total_seconds()/60.0:.2f}"))
            self.log.info(f"Transformed Outliers {column}: {transformed_outliers}")
            table.add_rows(transformed_outliers)

        self.notify(
            message=f"All metrics were calculated for {OutlierApp.DF.shape[0]} runners.",
            title="Outliers statistics status",
            severity="information"
        )

    def sort_reverse(self, sort_type: str):
        """
        Toggle sort type. To be passed to sort method
        """
        reverse = sort_type in self.current_sorts
        if reverse:
            self.current_sorts.remove(sort_type)
        else:
            self.current_sorts.add(sort_type)
        return reverse

    @on(DataTable.HeaderSelected)
    def on_header_clicked(self, event: DataTable.HeaderSelected):
        """
        Handle table click events
        """
        table = event.data_table
        table.sort(
            event.column_key,
            reverse=self.sort_reverse(event.column_key.value)
        )

    @on(DataTable.RowSelected)
    def on_row_clicked(self, event: DataTable.RowSelected) -> None:
        """
        Push a new detail screen when an outlier is chosen.
        Reuse the original DataFrame, that has all the runners information, filter by outlier BIB number.
        """
        table = event.data_table
        row = table.get_row(event.row_key)
        bibs = [row[0]]
        outlier_runner = df_to_list_of_tuples(df=OutlierApp.DF, bibs=bibs)
        runner_detail = OutlierDetailScreen(runner_data=outlier_runner)
        self.push_screen(runner_detail)


class Plotter:
    """
    Plot different metrics
    """
    def __init__(self, year: int, data_file: Path = None):
        """
        Constructor, load data from file using helper.
        """
        self.df = load_json_data(data_file=data_file, use_pretty=False)
        self.year = year

    def plot_age(self, gtype: str):
        """
        Plot age.
        Borrowed coloring recipe for histogram from Matplotlib documentation
        """
        if gtype == 'box':
            series = self.df[RaceFields.AGE.value]
            _, ax = plt.subplots(layout='constrained')
            ax.boxplot(series)
            ax.set_title(f"Age details (Race year: {self.year})")
            ax.set_ylabel('Years')
            ax.set_xlabel('Age')
            ax.grid(True)
        elif gtype == 'hist':
            series = self.df[RaceFields.AGE.value]
            _, ax = plt.subplots(layout='constrained')
            _, bins, _ = ax.hist(series, density=False, alpha=0.75)
            ax.set_xlabel('Age [years]')
            ax.set_ylabel('Count')
            ax.set_title(f'Age details for {series.shape[0]} racers\nBins={len(bins)}\nYear={self.year}\n')
            ax.grid(True)

    def plot_country(self):
        """
        Plot country details
        """
        fastest = find_fastest(self.df, FastestFilters.COUNTRY)
        series = self.df[RaceFields.COUNTRY.value].value_counts()
        series.sort_values(inplace=True)
        _, ax = plt.subplots(layout='constrained')
        rects = ax.barh(series.keys(), series.values)
        ax.bar_label(
            rects,
            [f"{country_count} - {fastest[country]['name']}({beautify_race_times(fastest[country]['time'])})" for
             country, country_count in series.items()],
            padding=1,
            color='black'
        )
        ax.set_title = f"Participants per country (Race year: {self.year})"
        ax.set_stacked = True
        ax.set_ylabel('Country')
        ax.set_xlabel('Count per country')

    def plot_gender(self):
        """
        Plot gender details
        """
        series = self.df[RaceFields.GENDER.value].value_counts()
        _, ax = plt.subplots(layout='constrained')
        wedges, _, _ = ax.pie(
            series.values,
            labels=series.keys(),
            autopct="%%%.2f",
            shadow=True,
            startangle=90,
            explode=(0.1, 0, 0)
        )
        ax.set_title = "Gender participation"
        ax.set_xlabel(f'Gender (Race year: {self.year})')
        # Legend with the fastest runners by gender
        fastest = find_fastest(self.df, FastestFilters.GENDER)
        fastest_legend = [f"{fastest[gender]['name']} - {beautify_race_times(fastest[gender]['time'])}" for gender in
                          series.keys()]
        ax.legend(wedges, fastest_legend,
                  title=f"Fastest (Race year: {self.year})",
                  loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1))


class BrowserApp(App):
    """
    Racer detail browser  application
    Shows racers for a given year on a table.
    """
    BINDINGS = [("q", "quit_app", "Quit")]
    CSS_PATH = "browser.tcss"
    ENABLE_COMMAND_PALETTE = True
    COMMANDS = App.COMMANDS | {BrowserAppCommand}
    current_sorts: set = set()

    def __init__(
            self,
            driver_class: Type[Driver] | None = None,
            css_path: CSSPathType | None = None,
            watch_css: bool = False,
            country_data: DataFrame = None,
            df: DataFrame = None
    ):
        """
        Constructor
        """
        super().__init__(driver_class, css_path, watch_css)
        self.country_data = load_country_details() if not country_data else country_data
        self.df = load_json_data() if (df is None or df.empty) else df

    def action_quit_app(self):
        """
        Exit handler
        """
        self.exit(0)

    def compose(self) -> ComposeResult:
        """
        UI element layout
        """
        yield Header(show_clock=True)
        yield DataTable(id='runners')
        yield Footer()

    def on_mount(self) -> None:
        """
        UI element rendering
        """
        table = self.get_widget_by_id('runners', expect_type=DataTable)
        table.zebra_stripes = True
        table.cursor_type = 'row'
        columns_raw, rows = df_to_list_of_tuples(df=self.df)
        for column in columns_raw:
            table.add_column(column.title(), key=column)
        for number, row in enumerate(rows[0:], start=1):
            label = Text(str(number), style="#B0FC38 italic")
            table.add_row(*row, label=label)
        table.sort(RaceFields.TIME.value)

        self.notify(
            message=f"Loaded all data for {self.df.shape[0]} runners.",
            title="Race Runners",
            severity="information"
        )

    def sort_reverse(self, sort_type: str):
        """
        Toggle sort type. To be passed to sort method
        """
        reverse = sort_type in self.current_sorts
        if reverse:
            self.current_sorts.remove(sort_type)
        else:
            self.current_sorts.add(sort_type)
        return reverse

    @on(DataTable.HeaderSelected, '#runners')
    def on_header_clicked(self, event: DataTable.HeaderSelected):
        """
        Callback when user clicks the table column header
        """
        table = event.data_table
        table.sort(
            event.column_key,
            reverse=self.sort_reverse(event.column_key.value)
        )

    @on(DataTable.RowSelected)
    def on_row_clicked(self, event: DataTable.RowSelected) -> None:
        """
        Callback when the user clicks a row, to get more racer details displayed
        """
        table = event.data_table
        row = table.get_row(event.row_key)
        runner_detail_screen = RunnerDetailScreen(table=table, row=row)
        self.push_screen(runner_detail_screen)
