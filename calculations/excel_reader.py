# calculations/excel_reader.py

import pandas as pd
from pathlib import Path

# ---- Paths (hardcoded relative to this file) ----
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"

RAW_FILE = DATA_DIR / "BASE LOAD PG TEST DATA 4 sets.xlsx"
DEMO_FILE = DATA_DIR / "Demo_Assumptions.xlsx"


class ExcelReader:
    def __init__(self):
        self.raw = None
        self.demo = None
        self.load()

    def load(self):
        if RAW_FILE.exists():
            self.raw = pd.read_excel(RAW_FILE, header=0)
            self.raw.columns = self.raw.columns.astype(str).str.strip()
        else:
            raise FileNotFoundError(f"Raw data file not found: {RAW_FILE}")

        if DEMO_FILE.exists():
            self.demo = pd.read_excel(DEMO_FILE)
        else:
            raise FileNotFoundError(f"Demo file not found: {DEMO_FILE}")

    def raw_data(self):
        return self.raw.copy()

    def demo_data(self):
        return self.demo.copy()


# ---- Global instance ----
_reader = ExcelReader()

def load_raw_data():
    return _reader.raw_data()

def load_demo_data():
    return _reader.demo_data()