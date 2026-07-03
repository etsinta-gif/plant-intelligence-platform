import pandas as pd

from pathlib import Path

from config.settings import RAW_DATA_PATH, DEMO_DATA_PATH


class ExcelReader:
    """
    Reads engineering Excel files.

    This class is the ONLY place in the project that knows
    data comes from Excel.
    """

    def __init__(self):

        self.raw = None
        self.demo = None

    # -------------------------------------------------

    def load(self):

        self.raw = pd.read_excel(

            RAW_DATA_PATH,

            sheet_name="FEBRUARY 2026",

            header=0

        )

        self.raw.columns = (

            self.raw.columns

            .astype(str)

            .str.strip()

        )

        self.demo = pd.read_excel(

            DEMO_DATA_PATH,

            header=0

        )

    # -------------------------------------------------

    def raw_data(self):

        if self.raw is None:

            self.load()

        return self.raw.copy()

    # -------------------------------------------------

    def demo_data(self):

        if self.demo is None:

            self.load()

        return self.demo.copy()


# -----------------------------------------------------


_reader = ExcelReader()


def load_raw_data():

    return _reader.raw_data()


def load_demo_data():

    return _reader.demo_data()