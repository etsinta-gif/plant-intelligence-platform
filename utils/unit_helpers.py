# utils/unit_helpers.py

import streamlit as st
from pathlib import Path
import sys

# ---- Add paths ----
current_dir = Path(__file__).resolve().parent.parent
shared_lib = current_dir / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from engineeros.services.rule_engine import RuleEngine

rules_path = current_dir / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))

# Get conversion factor from Rules
KJ_TO_KCAL = rule_engine.get_constant("KJ_TO_KCAL") or 4.1868

def get_heat_rate_unit():
    if "hr_unit" not in st.session_state:
        st.session_state.hr_unit = "kJ/kWh"
    return st.session_state.hr_unit

def set_heat_rate_unit(unit):
    st.session_state.hr_unit = unit

def convert_hr(value, from_unit="kJ/kWh"):
    target = get_heat_rate_unit()
    if target == from_unit:
        return value
    if from_unit == "kJ/kWh" and target == "kcal/kWh":
        return value / KJ_TO_KCAL
    if from_unit == "kcal/kWh" and target == "kJ/kWh":
        return value * KJ_TO_KCAL
    return value

def format_hr(value, decimals=0):
    unit = get_heat_rate_unit()
    return f"{value:.{decimals}f} {unit}"

def get_hr_label():
    return f"Heat Rate ({get_heat_rate_unit()})"