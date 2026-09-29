"""
Module to handle all the providers' logic.
"""
from collections.abc import AsyncGenerator
from functools import partial
from typing import Any

from rich.style import Style
from textual.command import DiscoveryHit, Hit, Provider
from textual.screen import Screen
from textual.widgets import DataTable

from empirestaterunup.data import FIELD_NAMES_AND_POS, RaceFields
from empirestaterunup.screens import RunnerDetailScreen

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
        # Cache for row data to avoid repeated table lookups
        self._row_cache: dict[Any, tuple] = {}

    async def startup(self) -> None:
        """
        Data loading on the palette startup
        """
        browser_app = self.app
        self.table = browser_app.query(DataTable).first()
        if self.debug:
            self.log.info(f"Table on provider: {self.table}")
            self.log.info(f"Rows:{len(self.table.rows)}")
        # Pre-cache all rows for faster search/discover
        self._build_row_cache()

    def _build_row_cache(self) -> None:
        """Build a cache of row data for faster lookups."""
        self._row_cache.clear()
        if self.table is None:
            return
        name_idx = FIELD_NAMES_AND_POS[RaceFields.NAME]
        for row_key in self.table.rows:
            row = self.table.get_row(row_key)
            self._row_cache[row_key] = (row, row[name_idx])

    async def discover(self) -> AsyncGenerator[DiscoveryHit, Any]:
        """
        Pre-populate the palette with results, to give an idea how the search works
        """
        browser_app = self.screen.app
        # Only yield first few rows for discovery (not all rows as before)
        # The original code had a break after first iteration anyway
        row_keys = list(self._row_cache.keys())
        for row_key in row_keys[:10]:  # Limit to first 10 for discovery
            row, runner_name = self._row_cache[row_key]
            for name in PALETTE_FIELDS:
                idx = FIELD_NAMES_AND_POS[name]
                searchable = str(row[idx])
                if name == RaceFields.NAME:
                    details = f"{searchable} - {name.value}"
                else:
                    details = f"{searchable} - {name.value} ({runner_name})"
                runner_detail_screen = RunnerDetailScreen(table=self.table, row=row)
                yield DiscoveryHit(
                    command=partial(browser_app.push_screen, runner_detail_screen),
                    display=f"Field: {name.value.title()}",
                    help=f"{details}"
                )

    async def search(self, query: str) -> AsyncGenerator[Hit, Any]:
        """
        Return hits based on a user query
        """
        matcher = self.matcher(query)
        browser_app = self.screen.app
        # Use cached row data instead of repeated table.get_row() calls
        for _row_key, (row, runner_name) in self._row_cache.items():
            for name in PALETTE_FIELDS:
                idx = FIELD_NAMES_AND_POS[name]
                searchable = str(row[idx])
                score = matcher.match(searchable)
                if score > 0:
                    if name == RaceFields.NAME:
                        details = f"{searchable} - {name.value}"
                    else:
                        details = f"{searchable} - {name.value} ({runner_name})"
                    runner_detail_screen = RunnerDetailScreen(
                        table=self.table, row=row)
                    yield Hit(
                        score=score,
                        match_display=matcher.highlight(f"{searchable}"),
                        command=partial(browser_app.push_screen, runner_detail_screen),
                        help=f"{details}"
                    )