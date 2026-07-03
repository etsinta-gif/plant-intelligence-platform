# pages/7_Health_Analytics.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance
from engineeros.services.rule_engine import RuleEngine

st.set_page_config(page_title="Health Analytics", layout="wide")
st.title("🏥 GT Health & Performance Analytics")

# ---- Rule Engine (absolute path) ----
rules_path = Path(__file__).resolve().parent.parent / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))

# ---- Load data ----
eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)
snapshots = db.snapshots_list()

# ---- Get asset type from session ----
asset_type = st.session_state.get("asset_type", "GasTurbine")

# ============================================================
# Helper: compute health metrics for a given snapshot
# ============================================================
def compute_health_metrics(snapshot):
    perf = gt.calculate(snapshot)

    def get_tag(tag):
        try:
            return db.value(tag, snapshot)
        except:
            return None

    tags = {
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
        "FQG": get_tag("FQG"),
        "FPG#1 (P1)": get_tag("FPG#1 (P1)"),
        "FPG#2(P2)": get_tag("FPG#2(P2)"),
        "BTJ1_1": get_tag("BTJ1_1"),
        "BTJ1_2": get_tag("BTJ1_2"),
        "39V-1A": get_tag("39V-1A"),
        "39V-1B": get_tag("39V-1B"),
        "39V-5A": get_tag("39V-5A"),
        "39V-5B": get_tag("39V-5B"),
        "DWATT": get_tag("DWATT"),
        "DVAR": get_tag("DVAR"),
        "1": get_tag("1"),
        "2": get_tag("2"),
        "3": get_tag("3"),
        "4": get_tag("4"),
    }

    metrics = {}

    if tags["CPD"] and tags["AFPIP"]:
        metrics["Pressure Ratio"] = tags["CPD"] / (tags["AFPIP"] * 0.133322)
    if tags["CTIM"] and tags["CTD"]:
        metrics["Compressor Temp Rise"] = tags["CTD"] - tags["CTIM"]
    if tags["AFPCS"]:
        metrics["Inlet Filter DP"] = tags["AFPCS"]
    spreads = [tags["TTXSP#1"], tags["TTXSP#2"], tags["TTXSP#3"], tags["TTXSP#4"]]
    valid_spreads = [s for s in spreads if s is not None]
    if valid_spreads:
        metrics["Max Exhaust Spread"] = max(valid_spreads)
        metrics["Avg Exhaust Spread"] = np.mean(valid_spreads)
        if tags["TTXSPL"]:
            metrics["Spread to Allowable"] = (max(valid_spreads) / tags["TTXSPL"]) * 100
    flame_vals = [tags["1"], tags["2"], tags["3"], tags["4"]]
    valid_flames = [f for f in flame_vals if f is not None]
    if valid_flames:
        metrics["Flame Stability (Std Dev)"] = np.std(valid_flames)
    if tags["BTJ1_1"] and tags["BTJ1_2"]:
        metrics["Bearing Temp Rise"] = tags["BTJ1_2"] - tags["BTJ1_1"]
    vibes = [tags["39V-1A"], tags["39V-1B"], tags["39V-5A"], tags["39V-5B"]]
    valid_vibes = [v for v in vibes if v is not None]
    if valid_vibes:
        metrics["Max Vibration"] = max(valid_vibes)
        metrics["Avg Vibration"] = np.mean(valid_vibes)
    if tags["FQG"] and perf.get("gross_output_mw"):
        metrics["Fuel per MW"] = tags["FQG"] * 3600 / perf["gross_output_mw"]
    if tags["FPG#1 (P1)"] and tags["FPG#2(P2)"]:
        metrics["Fuel Pressure Drop"] = tags["FPG#1 (P1)"] - tags["FPG#2(P2)"]
    if tags["DWATT"] and tags["DVAR"]:
        metrics["Power Factor"] = tags["DWATT"] / (tags["DWATT"] + abs(tags["DVAR"]))
    if perf.get("gross_heat_rate_kj_per_kwh"):
        metrics["Gross Heat Rate"] = perf["gross_heat_rate_kj_per_kwh"]
    if perf.get("thermal_efficiency_percent"):
        metrics["Efficiency"] = perf["thermal_efficiency_percent"]
    metrics["Load (MW)"] = perf.get("gross_output_mw", 0)
    return metrics

# ============================================================
# SECTION 1: TREND
# ============================================================
st.subheader("📈 Health Metrics Trend Across Snapshots")

all_metrics = {snap: compute_health_metrics(snap) for snap in snapshots}
common_metrics = sorted(set().union(*[set(m.keys()) for m in all_metrics.values()]))
selected_metrics = st.multiselect("Select metrics to plot", common_metrics, default=common_metrics[:5])

if selected_metrics:
    trend_data = {}
    for snap in snapshots:
        trend_data[snap] = {m: all_metrics[snap].get(m, None) for m in selected_metrics}
    df_trend = pd.DataFrame(trend_data).T
    df_trend.index.name = "Snapshot"

    pg_test_values = {m: all_metrics[snapshots[0]].get(m, None) for m in selected_metrics} if snapshots else {}

    fig = go.Figure()
    for m in selected_metrics:
        fig.add_trace(go.Scatter(x=df_trend.index, y=df_trend[m], mode="lines+markers", name=m, line=dict(width=2), marker=dict(size=8)))
        if pg_test_values.get(m) is not None:
            fig.add_hline(y=pg_test_values[m], line_dash="dash", line_color="gray", annotation_text=f"PG Test ({m})", annotation_position="bottom right")
    fig.update_layout(xaxis_title="Snapshot", yaxis_title="Metric Value", height=400, hovermode="x unified", legend=dict(x=0.01, y=0.99))
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("📊 Full Trend Data Table"):
        st.dataframe(df_trend, use_container_width=True)
        st.caption(f"**PG Test Reference Values:** {pg_test_values}")
else:
    st.info("Select at least one metric to display the trend.")

st.divider()

# ============================================================
# SECTION 2: Detailed Health Check
# ============================================================
st.subheader("🔍 Detailed Health Check for a Specific Snapshot")
selected_snapshot = st.selectbox("Select Snapshot for Detailed Check", snapshots)

if st.button("Run Detailed Health Check", type="primary"):
    metrics = all_metrics[selected_snapshot]
    rows = []
    for metric_name, value in metrics.items():
        result = rule_engine.classify(metric_name, value, asset_type=asset_type)
        rows.append({
            "Metric": metric_name,
            "Value": f"{value:.3f}",
            "Status": result["status"],
            "Recommendation": result["message"]
        })
    df_detail = pd.DataFrame(rows)
    st.subheader(f"📊 Health Check Summary for {selected_snapshot}")
    st.dataframe(df_detail, use_container_width=True)

    # ---- Raw tags using the raw DataFrame directly ----
    with st.expander("📋 Full Raw Tag Data (All Parameters)"):
        raw_df = eng.raw  # The original Excel DataFrame
        if selected_snapshot not in raw_df.columns:
            st.warning(f"Snapshot '{selected_snapshot}' not found in raw data.")
        else:
            raw_data = []
            for _, row in raw_df.iterrows():
                tag = row.get("Tag", "")
                if pd.isna(tag) or tag == "":
                    continue
                val = row.get(selected_snapshot)
                if pd.isna(val) or val is None:
                    continue
                raw_data.append({
                    "Parameter": row.get("Parameter", ""),
                    "Tag": tag,
                    "Unit": row.get("Unit", ""),
                    "Value": val
                })
            if raw_data:
                st.dataframe(pd.DataFrame(raw_data), use_container_width=True)
            else:
                st.warning("No valid tag values found for this snapshot.")

    st.caption("""
    **💡 Legend:**
    - 🟢 OK → Normal. Continue monitoring.
    - 🟡 Warning → Investigate. Schedule maintenance.
    - 🔴 Critical → Immediate action required.
    """)