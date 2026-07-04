# pages/11_Predictive_Forecast.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import sys
from datetime import timedelta

# ---- Path setup ----
current_dir = Path(__file__).resolve().parent.parent
shared_lib = current_dir / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "core" / "src"))
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance
from engineeros.services.rule_engine import RuleEngine
from calculations.excel_reader import load_demo_data

st.set_page_config(page_title="Predictive Forecast", layout="wide")
st.title("🔮 Predictive Forecasting – Time to Threshold")

# ---- Initialise ----
eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)
snapshots = db.snapshots_list()
demo_df = load_demo_data()

rules_path = current_dir / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))
asset_type = st.session_state.get("asset_type", "GasTurbine")

if not snapshots:
    st.warning("No snapshots found. Please load data first.")
    st.stop()

# ---- Helper: snapshot date (robust) ----
def get_snapshot_datetime(snapshot):
    try:
        row = demo_df[demo_df["Test"] == snapshot]
        if not row.empty:
            date_val = row["Date"].iloc[0]
            if pd.notna(date_val):
                return pd.Timestamp(date_val)
    except:
        pass
    hardcoded = {
        "PG TEST DATA": "2025-01-27",
        "Set 4 - Base Load": "2025-12-23",
        "Set 3 - Base Load": "2025-04-20",
        "Set 2 - Base Load": "2024-12-22",
        "Set 1 - Base Load": "2024-09-13",
    }
    if snapshot in hardcoded:
        return pd.Timestamp(hardcoded[snapshot])
    if snapshot in snapshots:
        idx = snapshots.index(snapshot)
        base_date = pd.Timestamp("2024-01-01")
        return base_date + pd.Timedelta(days=idx * 30)
    return None

# ---- Compute health metrics for all snapshots ----
def compute_metrics(snapshot):
    perf = gt.calculate(snapshot)
    def get_tag(tag):
        try:
            val = db.value(tag, snapshot)
            if val is None:
                return None
            try:
                return float(val)
            except:
                return None
        except:
            return None
    tags = {
        "DWATT": get_tag("DWATT"),
        "FQG": get_tag("FQG"),
        "CTIM": get_tag("CTIM"),
        "CTD": get_tag("CTD"),
        "CPD": get_tag("CPD"),
        "AFPIP": get_tag("AFPIP"),
        "AFPCS": get_tag("AFPCS"),
        "TTXSP#1": get_tag("TTXSP#1"),
        "TTXSP#2": get_tag("TTXSP#2"),
        "TTXSP#3": get_tag("TTXSP#3"),
        "TTXSP#4": get_tag("TTXSP#4"),
        "TTXSPL": get_tag("TTXSPL"),
        "FPG#1 (P1)": get_tag("FPG#1 (P1)"),
        "FPG#2(P2)": get_tag("FPG#2(P2)"),
        "BTJ1_1": get_tag("BTJ1_1"),
        "BTJ1_2": get_tag("BTJ1_2"),
        "39V-1A": get_tag("39V-1A"),
        "39V-1B": get_tag("39V-1B"),
        "39V-5A": get_tag("39V-5A"),
        "39V-5B": get_tag("39V-5B"),
        "DVAR": get_tag("DVAR"),
        "1": get_tag("1"),
        "2": get_tag("2"),
        "3": get_tag("3"),
        "4": get_tag("4"),
    }
    metrics = {}
    # Pressure Ratio
    if tags["CPD"] and tags["AFPIP"]:
        cpd_kpa = tags["CPD"] * 98.0665
        amb_kpa = tags["AFPIP"] * 0.133322
        if amb_kpa != 0:
            metrics["Pressure Ratio"] = cpd_kpa / amb_kpa
    # Compressor Temp Rise
    if tags["CTIM"] and tags["CTD"]:
        metrics["Compressor Temp Rise"] = tags["CTD"] - tags["CTIM"]
    # Inlet Filter DP
    if tags["AFPCS"]:
        metrics["Inlet Filter DP"] = tags["AFPCS"]
    # Max Exhaust Spread
    spreads = [tags["TTXSP#1"], tags["TTXSP#2"], tags["TTXSP#3"], tags["TTXSP#4"]]
    valid_spreads = [s for s in spreads if s is not None]
    if valid_spreads:
        metrics["Max Exhaust Spread"] = max(valid_spreads)
    # Max Vibration
    vibes = [tags["39V-1A"], tags["39V-1B"], tags["39V-5A"], tags["39V-5B"]]
    valid_vibes = [v for v in vibes if v is not None]
    if valid_vibes:
        metrics["Max Vibration"] = max(valid_vibes)
    # Bearing Temp Rise
    if tags["BTJ1_1"] and tags["BTJ1_2"]:
        metrics["Bearing Temp Rise"] = tags["BTJ1_2"] - tags["BTJ1_1"]
    # Fuel Pressure Drop
    if tags["FPG#1 (P1)"] and tags["FPG#2(P2)"]:
        metrics["Fuel Pressure Drop"] = tags["FPG#1 (P1)"] - tags["FPG#2(P2)"]
    # Efficiency
    if perf.get("thermal_efficiency_percent"):
        metrics["Efficiency"] = perf["thermal_efficiency_percent"]
    # Heat Rate
    if perf.get("gross_heat_rate_kj_per_kwh"):
        metrics["Gross Heat Rate"] = perf["gross_heat_rate_kj_per_kwh"]
    return metrics

# ---- Build DataFrame of metrics over time ----
all_metrics = {}
for snap in snapshots:
    all_metrics[snap] = compute_metrics(snap)

df_metrics = pd.DataFrame(all_metrics).T
df_metrics.index.name = "Snapshot"

# ---- Attach dates ----
dates = {}
for snap in snapshots:
    d = get_snapshot_datetime(snap)
    if d is not None:
        dates[snap] = d
df_metrics["Date"] = df_metrics.index.map(lambda x: dates.get(x))
df_metrics = df_metrics.dropna(subset=["Date"])
if df_metrics.empty:
    st.warning("No snapshots with valid dates found.")
    st.stop()

# ---- For each metric, compute trend and days to threshold ----
metrics_list = ["Pressure Ratio", "Compressor Temp Rise", "Inlet Filter DP",
                "Max Exhaust Spread", "Max Vibration", "Bearing Temp Rise",
                "Fuel Pressure Drop", "Efficiency", "Gross Heat Rate"]

results = []
for metric in metrics_list:
    if metric not in df_metrics.columns:
        continue
    series = df_metrics[metric].dropna()
    if len(series) < 2:
        continue
    x = np.arange(len(series))
    y = series.values
    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]
    intercept = coeffs[1]
    rule = rule_engine.thresholds.get(metric)
    if not rule:
        continue
    warn_val = rule.get("warn_high") or rule.get("warn_low")
    crit_val = rule.get("good_high") or rule.get("good_low")
    current_val = series.iloc[-1]
    threshold = None
    if slope > 0 and rule.get("warn_high") is not None:
        threshold = rule["warn_high"]
    elif slope < 0 and rule.get("warn_low") is not None:
        threshold = rule["warn_low"]
    else:
        continue
    if len(df_metrics) > 1:
        date_diff = df_metrics["Date"].diff().dt.days
        avg_days = date_diff.mean()
    else:
        avg_days = 1
    slope_per_day = slope / avg_days if avg_days else 0
    if slope_per_day == 0:
        continue
    days_to_threshold = (threshold - current_val) / slope_per_day
    if days_to_threshold < 0:
        days_to_threshold = 0
    results.append({
        "Metric": metric,
        "Current Value": current_val,
        "Slope (per day)": slope_per_day,
        "Threshold": threshold,
        "Days to Threshold": days_to_threshold,
        "Unit": rule.get("unit", "")
    })

df_forecast = pd.DataFrame(results)

# ---- Display ----
st.subheader("📊 Forecasted Time to Threshold")

if df_forecast.empty:
    st.info("No metrics with both trend and threshold available.")
else:
    df_forecast = df_forecast.sort_values("Days to Threshold")
    st.dataframe(df_forecast.style.format({
        "Current Value": "{:.2f}",
        "Slope (per day)": "{:.4f}",
        "Threshold": "{:.2f}",
        "Days to Threshold": "{:.0f}"
    }), use_container_width=True)

    urgent = df_forecast[df_forecast["Days to Threshold"] <= 30]
    if not urgent.empty:
        st.warning("🚨 The following metrics are predicted to reach their threshold within 30 days:")
        st.dataframe(urgent, use_container_width=True)

# ---- Plot forecast for selected metric ----
st.subheader("📈 Detailed Forecast for a Selected Metric")
selected_metric = st.selectbox("Select Metric", df_forecast["Metric"].tolist() if not df_forecast.empty else [])

if selected_metric:
    series = df_metrics[selected_metric].dropna()
    if len(series) < 2:
        st.warning("Not enough data points.")
    else:
        x = np.arange(len(series))
        y = series.values
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        intercept = coeffs[1]
        avg_days = df_metrics["Date"].diff().dt.days.mean()
        slope_per_day = slope / avg_days if avg_days else 0
        last_date = df_metrics["Date"].iloc[-1]
        last_val = series.iloc[-1]
        rule = rule_engine.thresholds.get(selected_metric)
        threshold = None
        if rule and slope > 0 and rule.get("warn_high") is not None:
            threshold = rule["warn_high"]
        elif rule and slope < 0 and rule.get("warn_low") is not None:
            threshold = rule["warn_low"]
        future_days = 90
        future_dates = [last_date + timedelta(days=i) for i in range(1, future_days+1)]
        future_vals = [last_val + slope_per_day * i for i in range(1, future_days+1)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_metrics["Date"],
            y=series,
            mode="lines+markers",
            name="Historical",
            line=dict(color="blue")
        ))
        trend_x = np.arange(len(series))
        trend_y = coeffs[0]*trend_x + coeffs[1]
        fig.add_trace(go.Scatter(
            x=df_metrics["Date"],
            y=trend_y,
            mode="lines",
            name="Trend",
            line=dict(color="gray", dash="dash")
        ))
        fig.add_trace(go.Scatter(
            x=future_dates,
            y=future_vals,
            mode="lines",
            name="Forecast",
            line=dict(color="red", dash="dot")
        ))
        if threshold is not None:
            fig.add_hline(y=threshold, line_dash="dash", line_color="orange",
                          annotation_text=f"Threshold: {threshold}")
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=selected_metric,
            height=450,
            hovermode="x"
        )
        st.plotly_chart(fig, use_container_width=True)