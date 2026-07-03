# pages/4_Corrections.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
import sys

# ---- Fix import path ----
current_dir = Path(__file__).resolve().parent.parent
shared_lib = current_dir / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from calculations.data_engine import EngineeringData
from engineeros.services.rule_engine import RuleEngine

st.set_page_config(page_title="Correction Factors", layout="wide")
st.title("🔧 GE 9FA 9‑Factor Correction Curves & Trends")

# ---- Rule Engine (absolute path) ----
rules_path = current_dir / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))

# ---- Load data ----
eng = EngineeringData()
db = eng.db
snapshots = db.snapshots_list()

# ---- Get asset type from session ----
asset_type = st.session_state.get("asset_type", "GasTurbine")

# ============================================================
# Helper: compute correction factors for a given snapshot
# ============================================================
def compute_correction_factors(snapshot):
    """Return dict of all C1..C9 and total factor using RuleEngine."""
    def get_tag(tag):
        try:
            return db.value(tag, snapshot)
        except:
            return None

    # Get raw inputs
    ctim = get_tag("CTIM")          # Compressor inlet temp (°C)
    rh = get_tag("RH")              # Relative humidity (%)
    afpip = get_tag("AFPIP")        # Ambient pressure (mmHg)
    afpcs = get_tag("AFPCS")        # Inlet pressure loss (mmwc)
    exh_loss = get_tag("96EP#1/2#3") # Exhaust pressure loss (mmwc)
    ftg = get_tag("FTG")            # Fuel gas temp (°C)

    # If RH not available, use default from constants
    if rh is None:
        rh = rule_engine.get_constant("ISO_RH")
    if rh is None:
        rh = 60.0  # fallback

    # ---- Evaluate curves ----
    c1 = rule_engine.evaluate_curve("C1_Inlet_Temp", ctim, asset_type=asset_type) if ctim is not None else 1.0
    c2 = rule_engine.evaluate_curve("C2_Humidity", rh, asset_type=asset_type) if rh is not None else 1.0

    if afpip is not None:
        press_mbar = afpip * 1.33322
        c3 = rule_engine.evaluate_curve("C3_Ambient_Pressure", press_mbar, asset_type=asset_type)
    else:
        c3 = 1.0

    c6 = rule_engine.evaluate_curve("C6_Inlet_Loss", afpcs, asset_type=asset_type) if afpcs is not None else 1.0
    c7 = rule_engine.evaluate_curve("C7_Exhaust_Loss", exh_loss, asset_type=asset_type) if exh_loss is not None else 1.0

    # C4, C5, C8, C9 – we can keep them as 1.0 or read from demo assumptions.
    c4 = 1.0
    c5 = 1.0
    c8 = 1.0
    c9 = 1.0

    total = c1 * c2 * c3 * c4 * c5 * c6 * c7 * c8 * c9

    return {
        "C1": c1,
        "C2": c2,
        "C3": c3,
        "C4": c4,
        "C5": c5,
        "C6": c6,
        "C7": c7,
        "C8": c8,
        "C9": c9,
        "total": total,
        "raw": {
            "CTIM": ctim,
            "RH": rh,
            "AFPIP": afpip,
            "AFPCS": afpcs,
            "EXH_LOSS": exh_loss,
            "FTG": ftg,
        }
    }

# ============================================================
# SECTION 1: TREND (Always Visible)
# ============================================================
st.subheader("📈 Correction Factors Trend Across Snapshots")

all_factors = {}
for snap in snapshots:
    all_factors[snap] = compute_correction_factors(snap)

factor_names = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "total"]
selected_factors = st.multiselect(
    "Select factors to plot",
    factor_names,
    default=["C1", "C6", "C7", "total"]
)

if selected_factors:
    trend_data = {}
    for snap in snapshots:
        trend_data[snap] = {f: all_factors[snap].get(f, None) for f in selected_factors}
    df_trend = pd.DataFrame(trend_data).T
    df_trend.index.name = "Snapshot"

    fig = go.Figure()
    for f in selected_factors:
        fig.add_trace(go.Scatter(
            x=df_trend.index,
            y=df_trend[f],
            mode="lines+markers",
            name=f,
            line=dict(width=2),
            marker=dict(size=8)
        ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="ISO Reference (1.0)")
    fig.update_layout(
        xaxis_title="Snapshot",
        yaxis_title="Correction Factor",
        height=400,
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📊 Full Trend Data Table"):
        st.dataframe(df_trend.style.format("{:.5f}"), use_container_width=True)
else:
    st.info("Select at least one factor to display the trend.")

st.divider()

# ============================================================
# SECTION 2: Snapshot Details
# ============================================================
st.subheader("📊 Snapshot Details")
selected_snapshot = st.selectbox("Select Snapshot for Details", snapshots)

if st.button("Compute Corrections for Snapshot", type="primary"):
    factors = all_factors[selected_snapshot]
    raw = factors["raw"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("C1: Inlet Temp", f"{factors['C1']:.5f}")
        st.metric("C2: Humidity", f"{factors['C2']:.5f}")
        st.metric("C3: Ambient Pressure", f"{factors['C3']:.5f}")
    with col2:
        st.metric("C4: Fuel Composition", f"{factors['C4']:.5f}")
        st.metric("C5: Generator PF", f"{factors['C5']:.5f}")
        st.metric("C6: Inlet Loss", f"{factors['C6']:.5f}")
    with col3:
        st.metric("C7: Exhaust Loss", f"{factors['C7']:.5f}")
        st.metric("C8: Fuel Temp", f"{factors['C8']:.5f}")
        st.metric("C9: Miscellaneous", f"{factors['C9']:.5f}")

    st.divider()
    st.metric("📈 Total HR Correction Factor", f"{factors['total']:.6f}")

    with st.expander("📋 Input Values Used"):
        st.json(raw)

    st.divider()
    st.subheader("📐 Correction Curves")

    def plot_curve(curve_name, x_label, x_value, measured_y, x_range, title):
        x_vals = np.linspace(x_range[0], x_range[1], 100)
        y_vals = [rule_engine.evaluate_curve(curve_name, x, asset_type=asset_type) for x in x_vals]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines", name="OEM Curve", line=dict(color="blue", width=3)))
        if x_value is not None and measured_y is not None:
            fig.add_trace(go.Scatter(x=[x_value], y=[measured_y], mode="markers",
                                     name=f"Measured ({x_value:.1f})", marker=dict(size=14, color="red", symbol="x")))
        fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="ISO Reference (1.0)")
        fig.update_layout(xaxis_title=x_label, yaxis_title=title, height=300, hovermode="x")
        st.plotly_chart(fig, use_container_width=True)

    if raw["CTIM"] is not None:
        plot_curve("C1_Inlet_Temp", "Ambient Temp (°C)", raw["CTIM"], factors["C1"], (0, 50), "C1 Factor")

    if raw["RH"] is not None:
        plot_curve("C2_Humidity", "Relative Humidity (%)", raw["RH"], factors["C2"], (0, 100), "C2 Factor")

    if raw["AFPIP"] is not None:
        press_mbar = raw["AFPIP"] * 1.33322
        plot_curve("C3_Ambient_Pressure", "Ambient Pressure (mbar)", press_mbar, factors["C3"], (950, 1060), "C3 Factor")

    if raw["AFPCS"] is not None:
        plot_curve("C6_Inlet_Loss", "Inlet Pressure Loss (mmwc)", raw["AFPCS"], factors["C6"], (0, 150), "C6 Factor")

    if raw["EXH_LOSS"] is not None:
        plot_curve("C7_Exhaust_Loss", "Exhaust Pressure Loss (mmwc)", raw["EXH_LOSS"], factors["C7"], (100, 350), "C7 Factor")

    st.caption("""
    **📌 Note:** These curves are generated from the OEM slopes extracted from the GE 9F.03 PDF.
    The red **'X'** marker shows the current snapshot's measured point.
    """)