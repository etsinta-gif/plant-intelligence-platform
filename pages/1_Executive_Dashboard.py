# pages/1_Executive_Dashboard.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance
from utils.unit_helpers import get_heat_rate_unit, set_heat_rate_unit, convert_hr, get_hr_label

st.set_page_config(page_title="Executive Dashboard", layout="wide")

# ---- Unit selector in sidebar ----
with st.sidebar:
    st.header("⚙️ Settings")
    current_unit = get_heat_rate_unit()
    new_unit = st.radio(
        "Heat Rate Unit",
        options=["kJ/kWh", "kcal/kWh"],
        index=0 if current_unit == "kJ/kWh" else 1,
        key="hr_unit_radio"
    )
    if new_unit != current_unit:
        set_heat_rate_unit(new_unit)
        st.rerun()

st.title("📊 Executive Dashboard — GT Performance Summary")

# Load data
eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)

# Get all snapshots
snapshots = db.snapshots_list()

# --- Compute results for all snapshots ---
results = []
for snap in snapshots:
    res = gt.calculate(snap)
    if "error" not in res:
        results.append(res)

if not results:
    st.error("No valid data found for any snapshot.")
    st.stop()

df = pd.DataFrame(results)

# ---- Convert heat rates to selected unit ----
df["gross_hr_display"] = df["gross_heat_rate_kj_per_kwh"].apply(lambda x: convert_hr(x, "kJ/kWh"))
df["corrected_hr_display"] = df["corrected_heat_rate_kj_per_kwh"].apply(lambda x: convert_hr(x, "kJ/kWh"))

# --- Top Metrics ---
st.subheader("📈 Overall Performance Summary")
col1, col2, col3, col4 = st.columns(4)

avg_output = df["gross_output_mw"].mean()
avg_hr = df["gross_hr_display"].mean()
avg_eff = df["thermal_efficiency_percent"].mean()
best_hr_snap = df.loc[df["gross_hr_display"].idxmin(), "snapshot"]

with col1:
    st.metric("Avg Gross Output", f"{avg_output:.1f} MW")
with col2:
    unit = get_heat_rate_unit()
    st.metric(f"Avg Gross HR", f"{avg_hr:.0f} {unit}")
with col3:
    st.metric("Avg Efficiency", f"{avg_eff:.2f} %")
with col4:
    st.metric("Best HR Snapshot", best_hr_snap)

st.divider()

# --- Chart 1: Output vs Heat Rate (Dual Axis) ---
st.subheader("📉 Output & Heat Rate Trends")

fig1 = go.Figure()

# Add Gross Output (bar chart)
fig1.add_trace(go.Bar(
    x=df["snapshot"],
    y=df["gross_output_mw"],
    name="Gross Output (MW)",
    marker_color="royalblue",
    yaxis="y1",
    text=df["gross_output_mw"].round(1),
    textposition="outside",
))

# Add Gross Heat Rate (line chart, secondary axis)
fig1.add_trace(go.Scatter(
    x=df["snapshot"],
    y=df["gross_hr_display"],
    name=f"Gross HR ({unit})",
    mode="lines+markers",
    marker_color="crimson",
    line=dict(width=3),
    yaxis="y2",
    text=df["gross_hr_display"].round(0),
    textposition="top center",
))

# Add Corrected HR (line, secondary axis)
fig1.add_trace(go.Scatter(
    x=df["snapshot"],
    y=df["corrected_hr_display"],
    name=f"Corrected HR ({unit})",
    mode="lines+markers",
    marker_color="darkorange",
    line=dict(width=3, dash="dash"),
    yaxis="y2",
    text=df["corrected_hr_display"].round(0),
    textposition="bottom center",
))

fig1.update_layout(
    xaxis=dict(title="Snapshot"),
    yaxis=dict(title="Output (MW)", side="left", showgrid=True),
    yaxis2=dict(
        title=get_hr_label(),
        side="right",
        overlaying="y",
        showgrid=False,
    ),
    legend=dict(x=0.01, y=0.99),
    height=450,
    hovermode="x unified",
)

st.plotly_chart(fig1, use_container_width=True)

# --- Chart 2: Efficiency Trends ---
st.subheader("📊 Efficiency Trends")

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
    yaxis=dict(title="Efficiency (%)", range=[0, max(df["thermal_efficiency_percent"].max() * 1.2, 50)]),
    legend=dict(x=0.01, y=0.99),
    height=400,
    hovermode="x unified",
)

st.plotly_chart(fig2, use_container_width=True)

# --- Chart 3: Correction Factor Trend ---
st.subheader("📈 Correction Factor Product (C1 × ... × C9)")

fig3 = go.Figure()

fig3.add_trace(go.Bar(
    x=df["snapshot"],
    y=df["correction_factor_product"],
    name="Total HR Correction",
    marker_color="purple",
    text=df["correction_factor_product"].round(4),
    textposition="outside",
))

fig3.add_hline(y=1.0, line_dash="dash", line_color="gray", 
               annotation_text="ISO Reference (1.0)", annotation_position="bottom right")

fig3.update_layout(
    xaxis=dict(title="Snapshot"),
    yaxis=dict(title="Correction Factor", range=[0.99, max(df["correction_factor_product"].max() * 1.02, 1.02)]),
    height=350,
    hovermode="x unified",
)

st.plotly_chart(fig3, use_container_width=True)

# --- Data Table ---
with st.expander("📋 Detailed Data Table"):
    display_df = df[[
        "snapshot",
        "gross_output_mw",
        "gross_hr_display",
        "corrected_hr_display",
        "thermal_efficiency_percent",
        "corrected_efficiency_percent",
        "correction_factor_product",
        "pressure_ratio",
    ]].copy()
    display_df.columns = [
        "Snapshot",
        "Gross Output (MW)",
        f"Gross HR ({unit})",
        f"Corrected HR ({unit})",
        "Gross Eff (%)",
        "Corrected Eff (%)",
        "HR Correction",
        "Pressure Ratio",
    ]
    st.dataframe(display_df.style.format({
        "Gross Output (MW)": "{:.1f}",
        f"Gross HR ({unit})": "{:.0f}",
        f"Corrected HR ({unit})": "{:.0f}",
        "Gross Eff (%)": "{:.2f}",
        "Corrected Eff (%)": "{:.2f}",
        "HR Correction": "{:.6f}",
        "Pressure Ratio": "{:.2f}",
    }), use_container_width=True)