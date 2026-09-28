"""
Collection of applications to display race findings
author: Jose Vicente Nunez <kodegeek.com@protonmail.com>
"""
from enum import Enum
from pathlib import Path

import matplotlib.pyplot as plt
from pandas import DataFrame, Timedelta
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult, CSSPathType
from textual.containers import Vertical
from textual.driver import Driver
from textual.widgets import DataTable, Footer, Header, Label
from textual.worker import get_current_worker

from empirestaterunup.analyze import (
    SUMMARY_METRICS,
    FastestFilters,
    age_bins,
    count_by_age,
    count_by_gender,
    dt_to_sorted_dict,
    find_fastest,
    get_5_number,
    get_country_counts,
    get_outliers,
    time_bins,
)
from empirestaterunup.data import (
    RaceFields,
    beautify_race_times,
    df_to_list_of_tuples,
    load_country_details,
    load_json_data,
    series_to_list_of_tuples,
)
from empirestaterunup.providers import BrowserAppCommand
from empirestaterunup.screens import OutlierDetailScreen, RunnerDetailScreen


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
            table.loading = True
            yield Vertical(
                Label(str(table_id.value)),
                table
            )
        yield Footer()

    @work(exclusive=False, thread=True)
    def update_summary(self, summary_table: DataTable) -> None:
        columns = [x.title() for x in FiveNumberApp.FIVE_NUMBER_FIELDS]
        columns.insert(0, 'Summary (Minutes)')
        worker = get_current_worker()
        if not worker.is_cancelled:
            self.call_from_thread(
                summary_table.add_columns,
                *columns
            )
            for metric in SUMMARY_METRICS:
                ndf = get_5_number(criteria=metric.value, data=FiveNumberApp.DF)
                rows = [ndf[field] for field in FiveNumberApp.FIVE_NUMBER_FIELDS]
                rows.insert(0, metric.value.title())
                rows[1] = int(rows[1])
                for idx in range(2, len(rows)):  # Pretty print running times
                    if isinstance(rows[idx], Timedelta):
                        rows[idx] = f"{rows[idx].total_seconds() / 60.0:.2f}"
                self.call_from_thread(
                    summary_table.add_row,
                    *rows
                )

    @work(exclusive=False, thread=True)
    def update_age_table(self, age_table: DataTable) -> None:
        adf, age_header = count_by_age(FiveNumberApp.DF)
        worker = get_current_worker()
        if not worker.is_cancelled:
            for column in age_header:
                self.call_from_thread(
                    age_table.add_column,
                    column,
                    key=column
                )
            self.call_from_thread(
                age_table.add_rows,
                dt_to_sorted_dict(adf).items()
            )

    @work(exclusive=False, thread=True)
    def update_gender_table(self, gender_table: DataTable) -> None:
        gdf, gender_header = count_by_gender(FiveNumberApp.DF)
        worker = get_current_worker()
        if not worker.is_cancelled:
            for column in gender_header:
                self.call_from_thread(
                    gender_table.add_column,
                    column,
                    key=column
                )
            gender_rows = dt_to_sorted_dict(gdf).items()
            self.call_from_thread(
                gender_table.add_rows,
                gender_rows
            )

    @work(exclusive=False, thread=True)
    def update_age_bucket_table(self, age_bucket_table: DataTable) -> None:
        age_categories, age_cols_head = age_bins(FiveNumberApp.DF)
        worker = get_current_worker()
        if not worker.is_cancelled:
            for column in age_cols_head:
                self.call_from_thread(
                    age_bucket_table.add_column,
                    column,
                    key=column
                )
            self.call_from_thread(
                age_bucket_table.add_rows,
                dt_to_sorted_dict(age_categories.value_counts()).items()
            )

    @work(exclusive=False, thread=True)
    def update_time_bucket_table(self, time_bucket_table: DataTable) -> None:
        time_categories, time_cols_head = time_bins(FiveNumberApp.DF)
        worker = get_current_worker()
        if not worker.is_cancelled:
            for column in time_cols_head:
                self.call_from_thread(
                    time_bucket_table.add_column,
                    column,
                    key=column
                )
            times = dt_to_sorted_dict(time_categories.value_counts()).items()
            self.call_from_thread(
                time_bucket_table.add_rows,
                times
            )

    @work(exclusive=False, thread=True)
    def update_country_counts_table(self, country_counts_table: DataTable) -> None:
        countries_counts, _, _ = get_country_counts(FiveNumberApp.DF)
        rows = series_to_list_of_tuples(countries_counts)
        worker = get_current_worker()
        if not worker.is_cancelled:
            for column in ['Country', 'Count']:
                self.call_from_thread(
                    country_counts_table.add_column,
                    column,
                    key=column
                )
            self.call_from_thread(
                country_counts_table.add_rows,
                rows
            )

    async def on_mount(self) -> None:
        """
        Initialize component contents
        """

        summary_table = self.get_widget_by_id(id=self.NumbersTables.SUMMARY.name, expect_type=DataTable)
        summary_table.loading = False
        self.update_summary(summary_table=summary_table)

        age_table = self.get_widget_by_id(id=self.NumbersTables.COUNT_BY_AGE.name, expect_type=DataTable)
        self.update_age_table(age_table=age_table)
        age_table.loading = False

        gender_table = self.get_widget_by_id(id=self.NumbersTables.GENDER_BUCKET.name, expect_type=DataTable)
        self.update_gender_table(gender_table=gender_table)
        gender_table.loading = False

        age_bucket_table = self.get_widget_by_id(id=self.NumbersTables.AGE_BUCKET.name, expect_type=DataTable)
        age_bucket_table.loading = False
        self.update_age_bucket_table(age_bucket_table=age_bucket_table)

        time_bucket_table = self.get_widget_by_id(id=self.NumbersTables.TIME_BUCKET.name, expect_type=DataTable)
        self.update_time_bucket_table(time_bucket_table=time_bucket_table)
        time_bucket_table.loading = False

        country_counts_table = self.get_widget_by_id(id=self.NumbersTables.COUNTRY_COUNTS.name, expect_type=DataTable)
        self.update_country_counts_table(country_counts_table=country_counts_table)
        country_counts_table.loading = False

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
                reverse=self.sort_reverse(str(event.column_key.value))
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
            table.loading = True
            if column_name == RaceFields.AGE:
                label = Label(f"{column_name.value} (older) outliers (Minutes):".title())
            else:
                label = Label(f"{column_name.value} (slower) outliers (Minutes):".title())
            yield Vertical(
                label,
                table
            )
        yield Footer()

    @work(exclusive=False, thread=True)
    def update_tables(self, table: DataTable, column: RaceFields) -> None:
        columns = [x.title() for x in ['bib', column.value]]
        worker = get_current_worker()
        if not worker.is_cancelled:
            self.call_from_thread(
                table.add_columns,
                *columns,
            )
        outliers = get_outliers(df=OutlierApp.DF, column=column.value)
        self.log.info(f"Outliers {column}: {outliers} ({len(outliers.keys())})")
        if column == RaceFields.AGE:
            transformed_outliers = outliers.to_dict().items()
        else:
            transformed_outliers = []
            for bib, timedelta in outliers.items():
                transformed_outliers.append((bib, f"{timedelta.total_seconds() / 60.0:.2f}"))
        self.log.info(f"Transformed Outliers {column}: {transformed_outliers}")
        if not worker.is_cancelled:
            self.call_from_thread(
                table.add_rows,
                transformed_outliers
            )

    def on_mount(self) -> None:
        """
        Initialize UI elements
        """
        for column in SUMMARY_METRICS:
            table = self.get_widget_by_id(f'col_{column.name}_outlier', expect_type=DataTable)
            table.loading = False
            self.update_tables(table=table, column=column)

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
            reverse=self.sort_reverse(str(event.column_key.value))
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
        )

        ax.set_title = "Gender participation"
        ax.set_xlabel(f'Gender (Race year: {self.year})')
        # Legend with the fastest runners by gender
        fastest = find_fastest(self.df, FastestFilters.GENDER)
        fastest_legend = [f"{fastest[gender]['name']} - {beautify_race_times(fastest[gender]['time'])}" for gender in
                              fastest]
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
            driver_class: type[Driver] | None = None,
            css_path: CSSPathType | None = None,
            watch_css: bool = False,
            country_data: DataFrame = None,
            df: DataFrame = None
    ):
        """
        Constructor
        """
        super().__init__(driver_class, css_path, watch_css)
        self.country_data = country_data if country_data else load_country_details()
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
        table = DataTable(id='runners')
        table.loading = True
        yield table
        yield Footer()

    @work(exclusive=True, thread=True)
    def update_table(self, table: DataTable) -> None:
        columns_raw, rows = df_to_list_of_tuples(df=self.df)
        worker = get_current_worker()
        if not worker.is_cancelled:
            for column in columns_raw:
                self.call_from_thread(
                    table.add_column,
                    column.title(),
                    key=column
                )
        for number, row in enumerate(rows[0:], start=1):
            label = Text(str(number), style="#B0FC38 italic")
            self.call_from_thread(
                table.add_row,
                *row,
                label=label
            )
        if not worker.is_cancelled:
            self.call_from_thread(
                table.sort,
                RaceFields.TIME.value
            )

    def on_mount(self) -> None:
        """
        UI element rendering
        """
        table = self.get_widget_by_id('runners', expect_type=DataTable)
        table.zebra_stripes = True
        table.cursor_type = 'row'
        table.loading = False
        self.update_table(table=table)

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
            reverse=self.sort_reverse(str(event.column_key.value))
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
