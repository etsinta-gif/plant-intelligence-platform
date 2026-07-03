# pages/4_Corrections.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from calculations.data_engine import EngineeringData
from calculations.corrections import GE9FACorrectionEngine

st.set_page_config(page_title="Correction Factors", layout="wide")
st.title("🔧 GE 9FA 9‑Factor Correction Engine")

# Load data
eng = EngineeringData()
db = eng.db
corr = GE9FACorrectionEngine(db=db)

# Snapshot selection (always visible)
snapshots = db.snapshots_list()
selected = st.selectbox("Select Snapshot", snapshots)

# Compute correction factors automatically for the selected snapshot
factors = corr.get_factors(selected)

# --- Display C factors in columns ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("C1: Inlet Temp", f"{factors['C1_inlet_temp']:.5f}")
    st.metric("C2: Humidity", f"{factors['C2_inlet_rh']:.5f}")
    st.metric("C3: Ambient Pressure", f"{factors['C3_ambient_press']:.5f}")
with col2:
    st.metric("C4: Fuel Composition", f"{factors['C4_fuel_composition']:.5f}")
    st.metric("C5: Generator PF", f"{factors['C5_generator_pf']:.5f}")  # Original C5
    st.metric("C6: Inlet Loss", f"{factors['C6_inlet_loss']:.5f}")      # Original C6
with col3:
    st.metric("C7: Exhaust Loss", f"{factors['C7_exhaust_loss']:.5f}")  # Original C7
    st.metric("C8: Fuel Temp", f"{factors['C8_fuel_temp']:.5f}")
    st.metric("C9: Miscellaneous", f"{factors['C9_misc']:.5f}")

st.divider()

# --- Original Total HR Correction Factor ---
st.metric("📈 Base Total HR Correction Factor (C1 × ... × C9)", 
          f"{factors['hr_correction_factor']:.6f}")

# --- Show raw input values ---
with st.expander("📋 Base Input Values Used"):
    st.json({
        "Ambient Temp (°C)": factors['ambient_temp_c'],
        "RH (%)": factors['rh_percent'],
        "Ambient Press (mbar)": factors['ambient_press_mbar'],
        "Inlet Loss (mmwc)": factors['inlet_loss_mmwc'],
        "Exhaust Loss (mmwc)": factors['exhaust_loss_mmwc'],
        "Fuel Temp (°C)": factors['fuel_temp_c'],
        "Generator PF": factors['generator_pf'],
    })

st.divider()
st.subheader("🎛️ Plant Controllable What-If Scenarios")
st.caption("Adjust sliders to simulate the impact of generator PF (C5), filter fouling (C6), or HRSG backpressure (C7) on overall heat rate correction.")

# --- Store original values for calculations ---
c5_orig = factors['C5_generator_pf']
c6_orig = factors['C6_inlet_loss']
c7_orig = factors['C7_exhaust_loss']
base_total = factors['hr_correction_factor']

# --- Three sliders in a row ---
col_c5, col_c6, col_c7 = st.columns(3)

with col_c5:
    st.markdown("#### ⚡ C5: Generator PF")
    # PF slider adjusts the actual power factor value (not a multiplier)
    pf_value = st.slider(
        "Power Factor",
        min_value=0.80, max_value=1.00, value=float(c5_orig), step=0.001,
        key="c5_slider"
    )
    # Recalculate C5 using the same slope: C5 = 1 + 0.015467 * (PF - 0.85)
    c5_manual = 1.0 + 0.015467 * (pf_value - 0.85)
    
    st.metric("Adjusted C5", f"{c5_manual:.6f}", 
              delta=f"{c5_manual - c5_orig:.6f}",
              delta_color="off")

with col_c6:
    st.markdown("#### 🧹 C6: Inlet Filter Loss")
    original_inlet_loss = factors['inlet_loss_mmwc']
    c6_multiplier = st.slider(
        "Filter Fouling (1.0 = measured)",
        min_value=0.8, max_value=1.5, value=1.0, step=0.01,
        key="c6_slider"
    )
    adjusted_inlet_loss = original_inlet_loss * c6_multiplier
    # C6 slope = -0.00000576 per mmwc
    c6_manual = 1.0 - 0.00000576 * adjusted_inlet_loss
    
    st.metric("Adjusted C6", f"{c6_manual:.6f}", 
              delta=f"{c6_manual - c6_orig:.6f}",
              delta_color="off")

with col_c7:
    st.markdown("#### 🔥 C7: Exhaust Backpressure")
    original_exhaust_loss = factors['exhaust_loss_mmwc']
    c7_multiplier = st.slider(
        "Exhaust Loss (1.0 = measured)",
        min_value=0.8, max_value=1.5, value=1.0, step=0.01,
        key="c7_slider"
    )
    adjusted_exhaust_loss = original_exhaust_loss * c7_multiplier
    # C7 formula: C7 = 1 + slope * (REFERENCE - MEASURED), slope = 0.0000603
    c7_manual = 1.0 + 0.0000603 * (corr.REF_EXHAUST_LOSS - adjusted_exhaust_loss)
    
    st.metric("Adjusted C7", f"{c7_manual:.6f}", 
              delta=f"{c7_manual - c7_orig:.6f}",
              delta_color="off")

# ---- Recalculate Total with manual C5, C6, C7 ----
# Total = (Product of all constants) * c5_manual * c6_manual * c7_manual
# Base = (Product of all constants) * c5_orig * c6_orig * c7_orig
# So Adjusted = Base / (c5_orig * c6_orig * c7_orig) * (c5_manual * c6_manual * c7_manual)
denominator = c5_orig * c6_orig * c7_orig
if denominator != 0:
    adjusted_total = base_total / denominator * (c5_manual * c6_manual * c7_manual)
else:
    adjusted_total = base_total

# ---- Display the new total ----
st.divider()
st.subheader("📊 What-If Result")

col_res1, col_res2, col_res3 = st.columns(3)
with col_res1:
    st.metric("Original Total HR Correction", f"{base_total:.6f}")
with col_res2:
    st.metric("Adjusted Total HR Correction", f"{adjusted_total:.6f}")
with col_res3:
    delta_pct = (adjusted_total - base_total) / base_total * 100
    st.metric("Change in HR Correction", f"{delta_pct:+.3f} %")

# ---- Extra: Explain the impact ----
# Check if any slider has changed from default
c5_changed = abs(pf_value - c5_orig) > 0.0005
c6_changed = abs(c6_multiplier - 1.0) > 0.001
c7_changed = abs(c7_multiplier - 1.0) > 0.001

if c5_changed or c6_changed or c7_changed:
    # Calculate individual percentage changes for the info box
    c5_change_pct = (c5_manual - c5_orig) / c5_orig * 100
    c6_change_pct = (c6_manual - c6_orig) / c6_orig * 100
    c7_change_pct = (c7_manual - c7_orig) / c7_orig * 100
    
    st.info(f"""
    **Interpretation**:
    - C5 (Generator PF) changed by **{c5_change_pct:+.3f}%** (from {c5_orig:.4f} to {pf_value:.4f}).
    - C6 (Filter Loss) changed by **{c6_change_pct:+.3f}%** (multiplier: {c6_multiplier:.2f}×).
    - C7 (Exhaust Loss) changed by **{c7_change_pct:+.3f}%** (multiplier: {c7_multiplier:.2f}×).
    - Total HR correction changed by **{delta_pct:+.3f}%**.
    """)
else:
    st.success("✅ All sliders are at measured values. No adjustments applied.")