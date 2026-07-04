# final_check.py
# Run this from PlantIntelligencePlatform/ to verify everything is correct.

import os
import sys
import json
import pandas as pd
from pathlib import Path

# ---- Colours for output ----
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
CHECK = "✅"
CROSS = "❌"
WARN = "⚠️"

print("\n" + "="*60)
print("🔍 FINAL SYSTEM VERIFICATION")
print("="*60 + "\n")

# ---- 1. Check folder structure ----
print("📁 1. Checking folder structure...")
required_files = [
    "app.py",
    "requirements.txt",
    "Data/BASE LOAD PG TEST DATA 4 sets.xlsx",
    "Data/Demo_Assumptions.xlsx",
    "Rules/thresholds.json",
    "Rules/formulas.json",
    "Rules/curves.json",
    "Rules/constants.json",
    "Rules/fmea.json",
    "utils/unit_helpers.py",
]
missing = []
for f in required_files:
    if not Path(f).exists():
        missing.append(f)

if missing:
    print(f"{CROSS} Missing files:")
    for f in missing:
        print(f"   - {f}")
else:
    print(f"{CHECK} All required files present.")

# ---- 2. Check JSON validity ----
print("\n📄 2. Checking JSON validity...")
json_files = [
    "Rules/thresholds.json",
    "Rules/formulas.json",
    "Rules/curves.json",
    "Rules/constants.json",
    "Rules/fmea.json",
]
json_ok = True
for f in json_files:
    try:
        with open(f, "r", encoding="utf-8") as fh:
            json.load(fh)
        print(f"   {CHECK} {f} is valid JSON.")
    except Exception as e:
        print(f"   {CROSS} {f} is invalid: {e}")
        json_ok = False

# ---- 3. Try to import critical modules ----
print("\n📦 3. Testing imports...")
try:
    from calculations.excel_reader import load_raw_data, load_demo_data
    print(f"   {CHECK} calculations.excel_reader")
except Exception as e:
    print(f"   {CROSS} calculations.excel_reader: {e}")

try:
    from calculations.gt_performance import GTPerformance
    from calculations.data_engine import EngineeringData
    print(f"   {CHECK} calculations.gt_performance & data_engine")
except Exception as e:
    print(f"   {CROSS} calculations: {e}")

try:
    from engineeros.services.rule_engine import RuleEngine
    print(f"   {CHECK} engineeros.services.rule_engine")
except Exception as e:
    print(f"   {CROSS} engineeros: {e}")

try:
    from core import init_core, get_repository_factory
    print(f"   {CHECK} core")
except Exception as e:
    print(f"   {CROSS} core: {e}")

# ---- 4. Test Excel loading ----
print("\n📊 4. Testing Excel data loading...")
try:
    raw = load_raw_data()
    demo = load_demo_data()
    print(f"   {CHECK} Raw data: {raw.shape[0]} rows, {raw.shape[1]} columns")
    print(f"   {CHECK} Demo data: {demo.shape[0]} rows, {demo.shape[1]} columns")
    if "Date" in demo.columns:
        print(f"   {CHECK} Demo has 'Date' column with {demo['Date'].count()} non-null values.")
    else:
        print(f"   {WARN} Demo has no 'Date' column.")
except Exception as e:
    print(f"   {CROSS} Failed to load Excel: {e}")

# ---- 5. Test RuleEngine ----
print("\n📐 5. Testing RuleEngine...")
try:
    from engineeros.services.rule_engine import RuleEngine
    re = RuleEngine(data_dir="Rules/")
    print(f"   {CHECK} Thresholds: {len(re.thresholds)} rules")
    print(f"   {CHECK} Formulas: {len(re.formulas)} rules")
    print(f"   {CHECK} Curves: {len(re.curves)} rules")
    print(f"   {CHECK} Constants: {len(re.constants)} items")
    print(f"   {CHECK} FMEA: {len(re.fmea)} failure modes")
except Exception as e:
    print(f"   {CROSS} RuleEngine failed: {e}")

# ---- 6. Test Performance Calculation ----
print("\n⚙️ 6. Testing GT Performance calculation...")
try:
    eng = EngineeringData()
    db = eng.db
    gt = GTPerformance(db)
    snap = db.snapshots_list()[0]
    result = gt.calculate(snap)
    if "error" in result:
        print(f"   {CROSS} Calculation error: {result['error']}")
    else:
        print(f"   {CHECK} Snapshot: {result['snapshot']}")
        print(f"   {CHECK} Gross Output: {result.get('gross_output_mw', 'N/A')} MW")
        print(f"   {CHECK} Gross HR: {result.get('gross_heat_rate_kj_per_kwh', 'N/A')} kJ/kWh")
        print(f"   {CHECK} Efficiency: {result.get('thermal_efficiency_percent', 'N/A')} %")
        print(f"   {CHECK} Pressure Ratio: {result.get('pressure_ratio', 'N/A')}")
        print(f"   {CHECK} Correction Factor: {result.get('correction_factor_product', 'N/A')}")
except Exception as e:
    print(f"   {CROSS} Performance test failed: {e}")

# ---- 7. Test Rule classification ----
print("\n🧪 7. Testing rule classification...")
try:
    re = RuleEngine(data_dir="Rules/")
    test_val = 14.5
    result = re.classify("Pressure Ratio", test_val, asset_type="GasTurbine")
    print(f"   {CHECK} classify('Pressure Ratio', {test_val}) -> {result['status']}: {result['message'][:60]}...")
except Exception as e:
    print(f"   {CROSS} Classification test failed: {e}")

# ---- Final verdict ----
print("\n" + "="*60)
print("✅ VERIFICATION COMPLETE")
print("="*60)
print("\nIf all items show ✅, your system is final and ready for SME review.")
print("If you see ❌ or ⚠️, fix the indicated issues before proceeding.")