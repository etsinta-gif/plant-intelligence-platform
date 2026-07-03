# utils/unit_helpers.py

import streamlit as st

# Conversion factor
KJ_TO_KCAL = 4.1868

def get_heat_rate_unit():
    """Return the selected unit from session state or default to kJ/kWh."""
    if "hr_unit" not in st.session_state:
        st.session_state.hr_unit = "kJ/kWh"
    return st.session_state.hr_unit

def set_heat_rate_unit(unit):
    st.session_state.hr_unit = unit

def convert_hr(value, from_unit="kJ/kWh"):
    """
    Convert a heat rate value to the currently selected unit.
    If from_unit is "kJ/kWh", convert to kcal/kWh if selected.
    """
    target = get_heat_rate_unit()
    if target == from_unit:
        return value
    if from_unit == "kJ/kWh" and target == "kcal/kWh":
        return value / KJ_TO_KCAL
    if from_unit == "kcal/kWh" and target == "kJ/kWh":
        return value * KJ_TO_KCAL
    return value

def format_hr(value, decimals=0):
    """Return a formatted string with the current unit."""
    unit = get_heat_rate_unit()
    return f"{value:.{decimals}f} {unit}"

def get_hr_label():
    """Return the axis label with current unit."""
    return f"Heat Rate ({get_heat_rate_unit()})"