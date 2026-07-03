# test_step1.py
from calculations.excel_reader import load_raw_data, load_demo_data

print("Loading raw data...")
raw = load_raw_data()
print(f"Raw data shape: {raw.shape}")
print("Columns:", raw.columns.tolist()[:10])  # show first 10 columns

print("\nLoading demo data...")
demo = load_demo_data()
print(f"Demo data shape: {demo.shape}")
print("Demo columns:", demo.columns.tolist()[:10])
print("First 2 rows of demo:\n", demo.head(2))