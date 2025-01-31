"""
Module to handle all the providers' logic.
"""
from functools import partial
from typing import Any

from rich.style import Style
from textual.command import Provider, DiscoveryHit, Hit
from textual.screen import Screen
from textual.widgets import DataTable

from empirestaterunup.screens import RunnerDetailScreen
from empirestaterunup.data import RaceFields, FIELD_NAMES_AND_POS

PALETTE_FIELDS = [RaceFields.BIB, RaceFields.NAME, RaceFields.COUNTRY]


class BrowserAppCommand(Provider):
    """
    Racer browser details on the Command palette
    """

    def __init__(
            self, screen: Screen[Any],
            match_style: Style | None = None,
            debug: bool = True
    ) -> None:
        """
        Constructor, load data from file using helper.
        """
        super().__init__(screen, match_style)
        self.table = None
        self.debug = debug
        self.log = self.app.log

    async def startup(self) -> None:
        """
        Data loading on the palette startup
        """
        browser_app = self.app
        self.table = browser_app.query(DataTable).first()
        if self.debug:
            self.log.info(f"Table on provider: {self.table}")
            self.log.info(f"Rows:{len(self.table.rows)}")

    async def discover(self) -> DiscoveryHit:
        """
        Pre-populate the palette with results, to give an idea how the search works
        """
        browser_app = self.screen.app
        for row_key in self.table.rows:
            row = self.table.get_row(row_key)
            for name in PALETTE_FIELDS:
                idx = FIELD_NAMES_AND_POS[name]
                name_idx = FIELD_NAMES_AND_POS[RaceFields.NAME]
                searchable = str(row[idx])
                if name == RaceFields.NAME:
                    details = f"{searchable} - {name.value}"
                else:
                    details = f"{searchable} - {name.value} ({row[name_idx]})"
                runner_detail_screen = RunnerDetailScreen(table=self.table, row=row)
                yield DiscoveryHit(
                        command=partial(browser_app.push_screen, runner_detail_screen),
                        display=f"Field: {name.value.title()}",
                        help=f"{details}"
                )
            break

    async def search(self, query: str) -> Hit:
        """
        Return hits based on a user query
        """
        matcher = self.matcher(query)
        browser_app = self.screen.app
        for row_key in self.table.rows:
            row = self.table.get_row(row_key)
            for name in PALETTE_FIELDS:
                idx = FIELD_NAMES_AND_POS[name]
                name_idx = FIELD_NAMES_AND_POS[RaceFields.NAME]
                searchable = str(row[idx])
                score = matcher.match(searchable)
                if score > 0:
                    if name == RaceFields.NAME:
                        details = f"{searchable} - {name.value}"
                    else:
                        details = f"{searchable} - {name.value} ({row[name_idx]})"
                    runner_detail_screen = RunnerDetailScreen(
                        table=self.table, row=row)
                    yield Hit(
                        score=score,
                        match_display=matcher.highlight(f"{searchable}"),
                        command=partial(browser_app.push_screen, runner_detail_screen),
                        help=f"{details}"
                    )
