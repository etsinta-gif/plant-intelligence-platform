# convert_to_sqlite.py

import pandas as pd
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "Data"
RAW_FILE = DATA_DIR / "BASE LOAD PG TEST DATA 4 sets.xlsx"
DEMO_FILE = DATA_DIR / "Demo_Assumptions.xlsx"
DB_PATH = Path(__file__).resolve().parent / "data.db"

print("📥 Converting Excel data to SQLite...")

# Connect to SQLite
conn = sqlite3.connect(DB_PATH)

# 1. Read raw data
raw_df = pd.read_excel(RAW_FILE, header=0)
raw_df.columns = raw_df.columns.astype(str).str.strip()

# Convert all snapshot columns to numeric (float), coercing errors to NaN
snapshot_cols = [c for c in raw_df.columns if c not in ["Parameter", "Tag", "Unit"]]
for col in snapshot_cols:
    raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce')

# Write to SQLite with explicit type mapping (we'll use floats)
raw_df.to_sql("raw_data", conn, if_exists="replace", index=False, dtype={col: "REAL" for col in snapshot_cols})

# 2. Read demo assumptions
demo_df = pd.read_excel(DEMO_FILE)
demo_columns = demo_df.columns.tolist()

# Convert date column if it exists
if "Date" in demo_columns:
    # Store as text (ISO format) for simplicity
    demo_df["Date"] = pd.to_datetime(demo_df["Date"]).dt.strftime("%Y-%m-%d")

# Convert numeric columns (excluding text columns like Test, Date, Time, Plant, etc.)
text_cols = ["Test", "Date", "Time", "Plant", "GT Model", "Fuel Supplier"]
for col in demo_columns:
    if col not in text_cols:
        demo_df[col] = pd.to_numeric(demo_df[col], errors='coerce')
        # Store as REAL
        demo_df.to_sql("demo_assumptions", conn, if_exists="replace", index=False, dtype={col: "REAL" for col in demo_columns if col not in text_cols})

# 3. Store snapshots list
snapshots = snapshot_cols
snapshots_df = pd.DataFrame({"snapshot": snapshots})
snapshots_df.to_sql("snapshots", conn, if_exists="replace", index=False)

conn.close()
print(f"✅ Data successfully converted to SQLite: {DB_PATH}")