"""
Module to handle all the sub-screen details.
"""
from typing import List, Any, Dict, Union, Tuple
from textual import on
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import MarkdownViewer, Button, DataTable

from empirestaterunup.data import FIELD_NAMES_AND_POS, RaceFields


class RunnerDetailScreen(ModalScreen):
    """
    Modal runner detail screen
    """
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = "runner_details.tcss"

    def __init__(
            self,
            name: str | None = None,
            ident: str | None = None,
            classes: str | None = None,
            row: List[Any] | None = None,
            table: DataTable | None = None,
            debug: bool = True,
    ):
        """
        Constructor
        """
        super().__init__(name, ident, classes)
        self.row = row
        self.table = table
        self.debug = debug

    def compose(self) -> ComposeResult:
        """
        UI element initial layout
        """
        bib_idx = FIELD_NAMES_AND_POS[RaceFields.BIB]
        bib = [self.row[bib_idx]][0]
        row_markdown = ""
        if self.table:
            col_map: Dict[int, str] = {idx: val.label.plain for idx, val in zip(range(0, len(self.table.columns)), self.table.columns.values())}
            if self.debug:
                col_def = dict(self.table.columns.items())
                self.log.info(f"Columns def: {col_def}")
                self.log.info(f"Row: {self.row}")
                self.log.info(f"Col Map: {col_map}")
            for idx, col_name in col_map.items():
                value = self.row[idx]
                row_markdown += f"* **{col_name}**: {value}\n"

        yield MarkdownViewer(f"""# Full Course Race details
## Runner BIO (BIB: {bib})
{row_markdown}         
        """)
        btn = Button("Close", variant="primary", id="close")
        btn.tooltip = "Back to main screen"
        yield btn

    @on(Button.Pressed, "#close")
    def on_button_pressed(self, _) -> None:
        """
        Handler on button pressed
        """
        self.app.pop_screen()


class OutlierDetailScreen(ModalScreen):
    """
    Display outliers details
    """
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = "runner_details.tcss"

    def __init__(
            self,
            name: str | None = None,
            ident: str | None = None,
            classes: str | None = None,
            runner_data: Union[Tuple | list[Tuple]] = None,
            debug: bool = True,
    ):
        """
        Constructor
        """
        super().__init__(name, ident, classes)
        self.runner_data = runner_data
        self.debug = debug

    def compose(self) -> ComposeResult:
        """
        UI element initial layout
        (('bib', 'name', 'gender', 'age', 'country', 'state', 'locality', 'full course', '20th floor', '65th floor'), [(545, 'Jay Winkler', 'NOT SPECIFIED', 33, 'United States of America', 'New
York', 'Massapequa', Timedelta('0 days 01:05:19'), Timedelta('0 days 00:07:52'), Timedelta('0 days 00:46:03'))])
        """
        bib = self.runner_data[1][0][0]
        row_markdown = ""
        if self.runner_data:
            if self.debug:
                self.log.info(f"Runners data: {self.runner_data}")
            for col_name, value in zip(self.runner_data[0], self.runner_data[1][0]):
                row_markdown += f"* **{col_name.title()}**: {value}\n"

        yield MarkdownViewer(f"""# Full Course Race details
## Runner BIO (BIB: {bib})
{row_markdown}         
        """)
        btn = Button("Close", variant="primary", id="close")
        btn.tooltip = "Back to main screen"
        yield btn

    @on(Button.Pressed, "#close")
    def on_button_pressed(self, _) -> None:
        """
        Handler on button pressed
        """
        self.app.pop_screen()
