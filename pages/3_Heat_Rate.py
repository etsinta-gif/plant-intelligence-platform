# pages/3_Heat_Rate.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance
from utils.unit_helpers import get_heat_rate_unit, set_heat_rate_unit, convert_hr, get_hr_label

st.set_page_config(page_title="Heat Rate Analysis", layout="wide")

# ---- Unit selector in sidebar ----
with st.sidebar:
    st.header("⚙️ Settings")
    current_unit = get_heat_rate_unit()
    new_unit = st.radio(
        "Heat Rate Unit",
        options=["kJ/kWh", "kcal/kWh"],
        index=0 if current_unit == "kJ/kWh" else 1,
        key="hr_unit_radio_hr"
    )
    if new_unit != current_unit:
        set_heat_rate_unit(new_unit)
        st.rerun()

st.title("🔥 Heat Rate Analysis")

# Load data
eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)

# Get all snapshots
snapshots = db.snapshots_list()

results = []
for snap in snapshots:
    res = gt.calculate(snap)
    if "error" not in res:
        results.append(res)

if not results:
    st.error("No valid data found for any snapshot.")
    st.stop()

df = pd.DataFrame(results)

# ---- Convert heat rates ----
df["gross_hr_display"] = df["gross_heat_rate_kj_per_kwh"].apply(lambda x: convert_hr(x, "kJ/kWh"))
df["corrected_hr_display"] = df["corrected_heat_rate_kj_per_kwh"].apply(lambda x: convert_hr(x, "kJ/kWh"))

unit = get_heat_rate_unit()

# --- Top Metrics ---
st.subheader("📊 Heat Rate Summary")
col1, col2, col3, col4 = st.columns(4)

avg_gross_hr = df["gross_hr_display"].mean()
avg_corrected_hr = df["corrected_hr_display"].mean()
best_hr = df["gross_hr_display"].min()
best_snap = df.loc[df["gross_hr_display"].idxmin(), "snapshot"]

with col1:
    st.metric(f"Avg Gross HR", f"{avg_gross_hr:.0f} {unit}")
with col2:
    st.metric(f"Avg Corrected HR", f"{avg_corrected_hr:.0f} {unit}")
with col3:
    st.metric(f"Best Gross HR", f"{best_hr:.0f} {unit}")
with col4:
    st.metric("Best Snapshot", best_snap)

st.divider()

# --- Chart: Gross vs Corrected HR ---
st.subheader("📉 Gross vs Corrected Heat Rate")

fig1 = go.Figure()

fig1.add_trace(go.Bar(
    x=df["snapshot"],
    y=df["gross_hr_display"],
    name=f"Gross HR ({unit})",
    marker_color="royalblue",
    text=df["gross_hr_display"].round(0),
    textposition="outside",
))

fig1.add_trace(go.Bar(
    x=df["snapshot"],
    y=df["corrected_hr_display"],
    name=f"Corrected HR ({unit})",
    marker_color="crimson",
    text=df["corrected_hr_display"].round(0),
    textposition="outside",
))

fig1.update_layout(
    xaxis=dict(title="Snapshot"),
    yaxis=dict(title=get_hr_label()),
    legend=dict(x=0.01, y=0.99),
    height=450,
    barmode="group",
    hovermode="x unified",
)

st.plotly_chart(fig1, use_container_width=True)

# --- Chart: Efficiency ---
st.subheader("📈 Thermal Efficiency")

fig2 = go.Figure()

fig2.add_trace(go.Bar(
    x=df["snapshot"],
    y=df["thermal_efficiency_percent"],
    name="Gross Efficiency (%)",
    marker_color="seagreen",
    text=df["thermal_efficiency_percent"].round(2),
    textposition="outside",
))

fig2.add_trace(go.Scatter(
    x=df["snapshot"],
    y=df["corrected_efficiency_percent"],
    name="Corrected Efficiency (%)",
    mode="lines+markers",
    marker_color="darkblue",
    line=dict(width=3, dash="dash"),
    text=df["corrected_efficiency_percent"].round(2),
    textposition="top center",
))

fig2.update_layout(
    xaxis=dict(title="Snapshot"),
    yaxis=dict(title="Efficiency (%)"),
    legend=dict(x=0.01, y=0.99),
    height=400,
    hovermode="x unified",
)

st.plotly_chart(fig2, use_container_width=True)

# --- Chart: Correction Factor ---
st.subheader("📊 Correction Factor Product")

fig3 = go.Figure()

fig3.add_trace(go.Scatter(
    x=df["snapshot"],
    y=df["correction_factor_product"],
    name="HR Correction",
    mode="lines+markers",
    marker_color="purple",
    line=dict(width=3),
    text=df["correction_factor_product"].round(4),
    textposition="top center",
))

fig3.add_hline(y=1.0, line_dash="dash", line_color="gray", 
               annotation_text="ISO Reference (1.0)", annotation_position="bottom right")

fig3.update_layout(
    xaxis=dict(title="Snapshot"),
    yaxis=dict(title="Correction Factor"),
    height=350,
    hovermode="x unified",
)

st.plotly_chart(fig3, use_container_width=True)

# --- Detailed Table ---
with st.expander("📋 Detailed Heat Rate Data"):
    display_cols = [
        "snapshot",
        "gross_hr_display",
        "corrected_hr_display",
        "thermal_efficiency_percent",
        "corrected_efficiency_percent",
        "correction_factor_product",
        "gross_output_mw",
        "fuel_flow_kg_per_s",
        "lhv_kjkg",
    ]
    display_df = df[display_cols].copy()
    display_df.columns = [
        "Snapshot",
        f"Gross HR ({unit})",
        f"Corrected HR ({unit})",
        "Gross Eff (%)",
        "Corrected Eff (%)",
        "HR Correction",
        "Output (MW)",
        "Fuel Flow (kg/s)",
        "LHV (kJ/kg)",
    ]
    st.dataframe(display_df.style.format({
        f"Gross HR ({unit})": "{:.0f}",
        f"Corrected HR ({unit})": "{:.0f}",
        "Gross Eff (%)": "{:.2f}",
        "Corrected Eff (%)": "{:.2f}",
        "HR Correction": "{:.6f}",
        "Output (MW)": "{:.1f}",
        "Fuel Flow (kg/s)": "{:.3f}",
        "LHV (kJ/kg)": "{:.1f}",
    }), use_container_width=True)