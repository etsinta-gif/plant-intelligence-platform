# calculations/excel_reader.py

import pandas as pd
from pathlib import Path

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
        # ---- Load raw data ----
        if not RAW_FILE.exists():
            raise FileNotFoundError(f"Raw data file not found: {RAW_FILE}")
        self.raw = pd.read_excel(RAW_FILE, header=0)
        self.raw.columns = self.raw.columns.astype(str).str.strip()
        
        # Ensure required columns exist (rename first 3 if necessary)
        expected = ["Parameter", "Tag", "Unit"]
        if not all(col in self.raw.columns for col in expected):
            first_cols = self.raw.columns[:3]
            rename_map = {first_cols[0]: "Parameter", first_cols[1]: "Tag", first_cols[2]: "Unit"}
            self.raw.rename(columns=rename_map, inplace=True)

        # ---- Load demo assumptions ----
        if not DEMO_FILE.exists():
            raise FileNotFoundError(f"Demo file not found: {DEMO_FILE}")
        self.demo = pd.read_excel(DEMO_FILE)
        
        # Ensure 'Test' column exists (rename first column if needed)
        if "Test" not in self.demo.columns:
            self.demo.rename(columns={self.demo.columns[0]: "Test"}, inplace=True)

        # ---- Force dates based on snapshot order (ensures trends work) ----
        snapshots = [c for c in self.raw.columns if c not in ["Parameter", "Tag", "Unit"]]
        # Hardcoded dates (matching your original data order)
        actual_dates = [
            "2025-01-27",  # PG TEST DATA
            "2025-12-23",  # Set 4
            "2025-04-20",  # Set 3
            "2024-12-22",  # Set 2
            "2024-09-13",  # Set 1
        ]
        date_map = dict(zip(snapshots, actual_dates))
        self.demo["Date"] = self.demo["Test"].map(date_map)
        # Convert to datetime
        self.demo["Date"] = pd.to_datetime(self.demo["Date"])

    def raw_data(self):
        return self.raw.copy()

    def demo_data(self):
        return self.demo.copy()


_reader = ExcelReader()

def load_raw_data():
    return _reader.raw_data()

def load_demo_data():
    return _reader.demo_data()