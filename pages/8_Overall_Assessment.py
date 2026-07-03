# pages/8_Overall_Assessment.py

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# ---- Fix import path ----
current_dir = Path(__file__).resolve().parent.parent
shared_lib = current_dir / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance
from engineeros.services.rule_engine import RuleEngine

st.set_page_config(page_title="Overall Assessment", layout="wide")
st.title("📋 GT Overall Performance Assessment & Recommendations")

# ---- Rule Engine (absolute path) ----
rules_path = current_dir / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))

# ---- Load data ----
eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)
snapshots = db.snapshots_list()

if not snapshots:
    st.warning("No snapshots found. Please load data first.")
    st.stop()

# ---- Get asset type from session ----
asset_type = st.session_state.get("asset_type", "GasTurbine")

# ============================================================
# Helper: compute health metrics for a given snapshot
# ============================================================
def compute_health_metrics(snapshot):
    """Return dict of health metrics for a snapshot."""
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

    # ---- Pressure Ratio (FIXED) ----
    if tags["CPD"] and tags["AFPIP"]:
        cpd_kpa = tags["CPD"] * 98.0665          # kg/cm² → kPa
        amb_kpa = tags["AFPIP"] * 0.133322       # mmHg → kPa
        if amb_kpa != 0:
            metrics["Pressure Ratio"] = cpd_kpa / amb_kpa

    # Compressor Temp Rise
    if tags["CTIM"] and tags["CTD"]:
        metrics["Compressor Temp Rise"] = tags["CTD"] - tags["CTIM"]

    # Inlet Filter DP
    if tags["AFPCS"]:
        metrics["Inlet Filter DP"] = tags["AFPCS"]

    # Exhaust Spreads
    spreads = [tags["TTXSP#1"], tags["TTXSP#2"], tags["TTXSP#3"], tags["TTXSP#4"]]
    valid_spreads = [s for s in spreads if s is not None]
    if valid_spreads:
        metrics["Max Exhaust Spread"] = max(valid_spreads)
        metrics["Avg Exhaust Spread"] = np.mean(valid_spreads)
        if tags["TTXSPL"]:
            metrics["Spread to Allowable"] = (max(valid_spreads) / tags["TTXSPL"]) * 100

    # Flame Stability
    flame_vals = [tags["1"], tags["2"], tags["3"], tags["4"]]
    valid_flames = [f for f in flame_vals if f is not None]
    if valid_flames:
        metrics["Flame Stability (Std Dev)"] = np.std(valid_flames)

    # Bearing Temp Rise
    if tags["BTJ1_1"] and tags["BTJ1_2"]:
        metrics["Bearing Temp Rise"] = tags["BTJ1_2"] - tags["BTJ1_1"]

    # Vibration
    vibes = [tags["39V-1A"], tags["39V-1B"], tags["39V-5A"], tags["39V-5B"]]
    valid_vibes = [v for v in vibes if v is not None]
    if valid_vibes:
        metrics["Max Vibration"] = max(valid_vibes)
        metrics["Avg Vibration"] = np.mean(valid_vibes)

    # Fuel per MW
    if tags["FQG"] and perf.get("gross_output_mw"):
        metrics["Fuel per MW"] = tags["FQG"] * 3600 / perf["gross_output_mw"]

    # Fuel Pressure Drop (difference in kg/cm²)
    if tags["FPG#1 (P1)"] and tags["FPG#2(P2)"]:
        metrics["Fuel Pressure Drop"] = tags["FPG#1 (P1)"] - tags["FPG#2(P2)"]

    # Power Factor
    if tags["DWATT"] and tags["DVAR"]:
        metrics["Power Factor"] = tags["DWATT"] / (tags["DWATT"] + abs(tags["DVAR"]))

    # Heat Rate & Efficiency
    if perf.get("gross_heat_rate_kj_per_kwh"):
        metrics["Gross Heat Rate"] = perf["gross_heat_rate_kj_per_kwh"]
    if perf.get("thermal_efficiency_percent"):
        metrics["Efficiency"] = perf["thermal_efficiency_percent"]

    metrics["Load (MW)"] = perf.get("gross_output_mw", 0)
    return metrics

# ---- Build DataFrame for trend analysis ----
all_metrics = {}
for snap in snapshots:
    all_metrics[snap] = compute_health_metrics(snap)

df_trend = pd.DataFrame(all_metrics).T
df_trend.index.name = "Snapshot"

# Identify latest and baseline
latest_snap = snapshots[-1]
baseline_snap = snapshots[0]  # PG Test

# ---- Trend Analysis (linear regression using numpy.polyfit) ----
trend_summary = {}
for col in df_trend.columns:
    series = df_trend[col].dropna()
    if len(series) < 2:
        continue
    x = np.arange(len(series))
    y = series.values
    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]
    trend_summary[col] = slope

# ---- Generate report ----
def generate_report():
    report = []
    report.append(f"**GT Performance Assessment Report**\n")
    report.append(f"**Analysis Period:** {snapshots[0]} to {latest_snap}\n")
    report.append(f"**Baseline (PG Test):** {baseline_snap}\n")
    report.append(f"**Asset Type:** {asset_type}\n\n")

    # 1. Degradation & Trend Analysis
    report.append("## 🔍 Degradation & Trend Analysis\n")
    for metric, slope in trend_summary.items():
        if abs(slope) < 1e-6:
            continue
        direction = "increasing" if slope > 0 else "decreasing"
        current = df_trend.loc[latest_snap, metric]
        report.append(f"- **{metric}**: trend is **{direction}** (slope = {slope:.3f}).")
        # Interpretation
        if metric == "Pressure Ratio":
            if slope < 0:
                report.append("  - Declining pressure ratio suggests compressor fouling or IGV misalignment.")
            else:
                report.append("  - Increasing pressure ratio may indicate IGV scheduling issues or instrument drift.")
        elif metric == "Gross Heat Rate":
            if slope > 0:
                report.append("  - Rising heat rate indicates performance degradation (fouling, wear, or combustion issues).")
            else:
                report.append("  - Improving heat rate is positive, possibly due to maintenance or better operating conditions.")
        elif metric == "Max Exhaust Spread":
            if slope > 0:
                report.append("  - Increasing exhaust spread points to uneven combustion or nozzle wear.")
        elif metric == "Max Vibration":
            if slope > 0:
                report.append("  - Vibration trend rising: possible bearing wear or rotor imbalance.")
        elif metric == "Efficiency":
            if slope < 0:
                report.append("  - Efficiency declining correlates with heat rate increase.")
    report.append("\n")

    # 2. Performance vs PG Test Baseline
    report.append("## 📊 Performance vs PG Test Baseline\n")
    for metric in df_trend.columns:
        baseline_val = df_trend.loc[baseline_snap, metric]
        latest_val = df_trend.loc[latest_snap, metric]
        if pd.isna(baseline_val) or pd.isna(latest_val):
            continue
        pct_change = ((latest_val - baseline_val) / abs(baseline_val)) * 100
        direction = "higher" if latest_val > baseline_val else "lower"
        report.append(f"- **{metric}**: {latest_val:.2f} vs baseline {baseline_val:.2f} ({pct_change:+.1f}%) – {direction} than PG Test.")
        # Interpretation
        if metric == "Pressure Ratio":
            if pct_change < -5:
                report.append("  - Significant drop in pressure ratio; consider offline compressor wash.")
            elif pct_change < -2:
                report.append("  - Moderate drop; monitor trend.")
        elif metric == "Gross Heat Rate":
            if pct_change > 5:
                report.append("  - Significant HR increase; investigate compressor, turbine, and fuel system.")
            elif pct_change > 2:
                report.append("  - Moderate HR increase; review maintenance schedule.")
        elif metric == "Max Exhaust Spread":
            if pct_change > 20:
                report.append("  - Spread increase >20%; borescope inspection recommended.")
        elif metric == "Efficiency":
            if pct_change < -5:
                report.append("  - Efficiency drop >5%; major overhaul may be needed.")
    report.append("\n")

    # 3. Alerts Summary (using RuleEngine)
    report.append("## 🚨 Current Alerts Summary\n")
    alerts = []
    for metric, value in all_metrics[latest_snap].items():
        result = rule_engine.classify(metric, value, asset_type=asset_type)
        if result["status"] != "Good":
            alerts.append(f"- **{metric}**: {value:.3f} – {result['status']} – {result['message']}")
    if alerts:
        report.extend(alerts)
    else:
        report.append("✅ All monitored parameters are within healthy ranges.\n")
    report.append("\n")

    # 4. Recommendations
    report.append("## 💡 Recommendations\n")
    recs = []
    # Based on trends and current status
    for metric, slope in trend_summary.items():
        if abs(slope) < 1e-6:
            continue
        if metric == "Pressure Ratio" and slope < -0.1:
            recs.append("- Schedule an online compressor wash and monitor trend.")
        if metric == "Gross Heat Rate" and slope > 5:
            recs.append("- Investigate heat rate degradation: inspect compressor blading, turbine clearance, and fuel nozzles.")
        if metric == "Max Exhaust Spread" and slope > 0.5:
            recs.append("- Plan a borescope inspection of combustor cans.")
        if metric == "Max Vibration" and slope > 0.1:
            recs.append("- Monitor vibration trend; consider vibration analysis and bearing check.")
    # Also check latest values
    for metric, value in all_metrics[latest_snap].items():
        result = rule_engine.classify(metric, value, asset_type=asset_type)
        if result["status"] == "Critical":
            recs.append(f"- {result['message']} (Immediate action required.)")
        elif result["status"] == "Warning":
            recs.append(f"- {result['message']} (Plan corrective action.)")
    if not recs:
        recs.append("- Continue routine monitoring; no major concerns identified.")
    # Deduplicate
    recs = list(dict.fromkeys(recs))
    report.extend(recs)

    report.append("\n---\n*Report generated automatically based on current data and thresholds.*")
    return "\n".join(report)

# ---- Display ----
st.subheader("📄 Engineer's Overall Assessment")
if st.button("Generate Assessment Report", type="primary"):
    report = generate_report()
    st.markdown(report)

# ---- Optional: LLM Enhancement ----
st.divider()
st.subheader("🤖 Enhance with AI (Optional)")
st.caption("If you have an OpenAI API key, you can send the report to an LLM for a more natural, expanded narrative.")
api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
if api_key and st.button("Generate Enhanced Assessment with AI"):
    try:
        import openai
        openai.api_key = api_key
        prompt = f"""
        You are a senior gas turbine performance engineer. Based on the following data and analysis, write a professional, concise performance assessment for the plant manager. Include key findings, areas of concern, and actionable recommendations. Use plain, clear language.

        {generate_report()}
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800
        )
        enhanced = response.choices[0].message.content
        st.markdown("### Enhanced Assessment (AI-generated)")
        st.markdown(enhanced)
    except ImportError:
        st.warning("OpenAI package not installed. Run `pip install openai`.")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Enter your OpenAI API key above to generate an enhanced narrative.")