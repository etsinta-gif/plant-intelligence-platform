# calculations/excel_reader.py

import pandas as pd
import sqlite3
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data.db"
DATA_DIR = BASE_DIR / "Data"
RAW_FILE = DATA_DIR / "BASE LOAD PG TEST DATA 4 sets.xlsx"
DEMO_FILE = DATA_DIR / "Demo_Assumptions.xlsx"


class ExcelReader:
    def __init__(self):
        self.raw = None
        self.demo = None
        self.load()

    def load(self):
        # ---- 1. Try to load from SQLite ----
        if DB_PATH.exists():
            try:
                conn = sqlite3.connect(DB_PATH)
                self.raw = pd.read_sql("SELECT * FROM raw_data", conn)
                self.demo = pd.read_sql("SELECT * FROM demo_assumptions", conn)
                conn.close()

                # Ensure numeric columns are float
                for col in self.raw.columns:
                    if col not in ["Parameter", "Tag", "Unit"]:
                        self.raw[col] = pd.to_numeric(self.raw[col], errors='coerce')

                # Ensure demo numeric columns are float
                for col in self.demo.columns:
                    if col not in ["Test", "Date", "Time", "Plant", "GT Model", "Fuel Supplier"]:
                        self.demo[col] = pd.to_numeric(self.demo[col], errors='coerce')

                # Re-apply dates (if needed)
                self._force_dates()
                return
            except Exception as e:
                print(f"⚠️ SQLite load failed: {e}. Falling back to Excel.")

        # ---- 2. Fallback to Excel ----
        if RAW_FILE.exists():
            try:
                self.raw = pd.read_excel(RAW_FILE, header=0)
                self.raw.columns = self.raw.columns.astype(str).str.strip()
                # Convert snapshot columns to numeric
                for col in self.raw.columns:
                    if col not in ["Parameter", "Tag", "Unit"]:
                        self.raw[col] = pd.to_numeric(self.raw[col], errors='coerce')
            except Exception:
                self.raw = self._generate_dummy_raw()
        else:
            self.raw = self._generate_dummy_raw()

        if DEMO_FILE.exists():
            try:
                self.demo = pd.read_excel(DEMO_FILE)
                if "Test" not in self.demo.columns:
                    self.demo.rename(columns={self.demo.columns[0]: "Test"}, inplace=True)
                # Convert numeric columns
                for col in self.demo.columns:
                    if col not in ["Test", "Date", "Time", "Plant", "GT Model", "Fuel Supplier"]:
                        self.demo[col] = pd.to_numeric(self.demo[col], errors='coerce')
            except Exception:
                self.demo = self._generate_dummy_demo()
        else:
            self.demo = self._generate_dummy_demo()

        self._force_dates()

    def _force_dates(self):
        snapshots = [c for c in self.raw.columns if c not in ["Parameter", "Tag", "Unit"]]
        # Use hardcoded dates (as before)
        actual_dates = ["2025-01-27", "2025-12-23", "2025-04-20", "2024-12-22", "2024-09-13"]
        date_map = dict(zip(snapshots, actual_dates))
        if "Test" in self.demo.columns:
            self.demo["Date"] = self.demo["Test"].map(date_map)
            self.demo["Date"] = pd.to_datetime(self.demo["Date"])

    # ---------- DUMMY DATA GENERATORS ----------
    def _generate_dummy_raw(self):
        # (keep your existing dummy generator – no changes)
        # For brevity, I'll include a placeholder – you can copy the full version from earlier.
        import numpy as np
        snapshots = ["PG TEST DATA", "Set 4 - Base Load", "Set 3 - Base Load", "Set 2 - Base Load", "Set 1 - Base Load"]
        parameters = [
            ("GT LOAD", "DWATT", "MW"),
            ("AMBIENT PRESSURE", "AFPIP", "MMHG"),
            ("COMPRESSOR INLET TEMPERATURE", "CTIM", "DEGC"),
            ("COMPRESSOR DISCHARGE PRESSURE", "CPD", "KG/CM2"),
            ("FUEL GAS FLOW", "FQG", "KG/SEC"),
            ("EXHAUST TEMPERATURE", "TTXM", "DEGC"),
            ("MAX EXHAUST PRESSURE", "96EP#1/2#3", "MMWC"),
            ("BEARING TEMP", "BTJ1_1", "DEGC"),
            ("VIBRATION", "39V-1A", "MM/SEC"),
            ("SPREAD", "TTXSP#1", "DEGC"),
        ]
        rows = []
        for name, tag, unit in parameters:
            row = {"Parameter": name, "Tag": tag, "Unit": unit}
            for snap in snapshots:
                if tag == "DWATT":
                    val = np.random.normal(240, 10)
                elif tag == "FQG":
                    val = np.random.normal(10, 2)
                elif "TEMP" in tag:
                    val = np.random.normal(30, 5)
                elif tag == "AFPIP":
                    val = np.random.normal(675, 2)
                elif tag == "CPD":
                    val = np.random.normal(15, 0.5)
                elif tag == "96EP#1/2#3":
                    val = np.random.uniform(150, 250)
                elif tag == "BTJ1_1":
                    val = np.random.normal(90, 10)
                elif "39V" in tag:
                    val = np.random.uniform(3, 7)
                elif tag == "TTXSP#1":
                    val = np.random.uniform(20, 35)
                else:
                    val = np.random.normal(100, 20)
                if isinstance(val, (int, float)):
                    val = round(max(0, val), 2)
                row[snap] = val
            rows.append(row)
        return pd.DataFrame(rows)

    def _generate_dummy_demo(self):
        snapshots = ["PG TEST DATA", "Set 4 - Base Load", "Set 3 - Base Load", "Set 2 - Base Load", "Set 1 - Base Load"]
        date_list = ["2025-01-27", "2025-12-23", "2025-04-20", "2024-12-22", "2024-09-13"]
        data = []
        for i, snap in enumerate(snapshots):
            row = {
                "Test": snap,
                "Date": date_list[i],
                "Fuel LHV (kcal/Sm³)": 8600 + i*20,
                "Specific Gravity": 0.615 + i*0.001,
                "Generator PF": 0.85 + i*0.01,
                "Ambient Temp (°C)": 25 + i*2,
                "Ambient Pressure (mmHg)": 760 - i*2,
                "Relative Humidity (%)": 60 + i*5,
            }
            data.append(row)
        return pd.DataFrame(data)

    def raw_data(self):
        return self.raw.copy()

    def demo_data(self):
        return self.demo.copy()


_reader = ExcelReader()

def load_raw_data():
    return _reader.raw_data()

def load_demo_data():
    return _reader.demo_data()