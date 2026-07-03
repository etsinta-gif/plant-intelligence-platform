# pages/6_Advanced_Analytics.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
from datetime import datetime

# ---- Path setup ----
current_dir = Path(__file__).resolve().parent.parent
shared_lib = current_dir / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "core" / "src"))
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance
from calculations.excel_reader import load_raw_data, load_demo_data
from engineeros.services.rule_engine import RuleEngine
from utils.unit_helpers import get_heat_rate_unit, set_heat_rate_unit, convert_hr

st.set_page_config(page_title="Advanced Analytics", layout="wide")

# ---- Rule Engine ----
rules_path = current_dir / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))
asset_type = st.session_state.get("asset_type", "GasTurbine")

# ---- Unit selector ----
with st.sidebar:
    st.header("⚙️ Settings")
    current_unit = get_heat_rate_unit()
    new_unit = st.radio(
        "Heat Rate Unit",
        options=["kJ/kWh", "kcal/kWh"],
        index=0 if current_unit == "kJ/kWh" else 1,
        key="hr_unit_radio_adv"
    )
    if new_unit != current_unit:
        set_heat_rate_unit(new_unit)
        st.rerun()

st.title("📈 Advanced Engineering Analytics")
st.markdown("""
Diagnostic & descriptive intelligence — trend detection, mode analysis, decomposition, and envelope mapping.
""")

# ---- Load all data ----
eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)
raw_df = load_raw_data()
demo_df = load_demo_data()

snapshots = db.snapshots_list()
unit = get_heat_rate_unit()

# ---- Helper functions ----
def get_snapshot_datetime(snapshot):
    row = demo_df[demo_df["Test"] == snapshot]
    if row.empty:
        return None
    date_str = row["Date"].iloc[0]
    time_str = row["Time"].iloc[0]
    if isinstance(date_str, str):
        date_str = pd.to_datetime(date_str).date()
    if isinstance(time_str, str):
        try:
            time_str = pd.to_datetime(time_str).time()
        except:
            time_str = pd.Timestamp("00:00:00").time()
    return pd.Timestamp.combine(date_str, time_str) if hasattr(date_str, "year") else None

def get_mode(snapshot):
    mode_row = raw_df[raw_df["Parameter"] == "MODE"]
    if mode_row.empty:
        return None
    return mode_row[snapshot].iloc[0]

def get_spread(snapshot, tag):
    try:
        return db.value(tag, snapshot)
    except:
        return None

def get_vibration(snapshot, tag):
    try:
        return db.value(tag, snapshot)
    except:
        return None

# ---- 1. PERFORMANCE DEGRADATION TREND ----
st.header("📉 1. Performance Degradation Trend")
st.markdown("Tracks key KPIs (Heat Rate, Output, Efficiency) over time with a linear trend line to detect degradation.")

trend_data = []
for snap in snapshots:
    dt = get_snapshot_datetime(snap)
    if dt is None:
        continue
    res = gt.calculate(snap)
    if "error" not in res and res.get("gross_heat_rate_kj_per_kwh") is not None:
        trend_data.append({
            "Snapshot": snap,
            "Date": dt,
            "Gross HR (kJ/kWh)": res["gross_heat_rate_kj_per_kwh"],
            "Corrected HR (kJ/kWh)": res["corrected_heat_rate_kj_per_kwh"],
            "Output (MW)": res["gross_output_mw"],
            "Efficiency (%)": res["thermal_efficiency_percent"],
        })

if len(trend_data) < 2:
    st.warning("Not enough data points (with valid dates) to show a trend.")
else:
    df_trend = pd.DataFrame(trend_data).sort_values("Date")
    df_trend["Gross HR"] = df_trend["Gross HR (kJ/kWh)"].apply(lambda x: convert_hr(x, "kJ/kWh"))
    df_trend["Corrected HR"] = df_trend["Corrected HR (kJ/kWh)"].apply(lambda x: convert_hr(x, "kJ/kWh"))
    
    x_num = np.arange(len(df_trend))
    coeffs = np.polyfit(x_num, df_trend["Gross HR"], 1)
    trend_line = np.polyval(coeffs, x_num)
    df_trend["HR Trend"] = trend_line
    slope_hr = coeffs[0]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "HR Degradation Slope",
            f"{slope_hr:.2f} {unit}/point",
            delta=f"{slope_hr * len(df_trend):.1f} {unit} over entire period",
            delta_color="inverse" if slope_hr > 0 else "normal"
        )
    with col2:
        coeffs_out = np.polyfit(x_num, df_trend["Output (MW)"], 1)
        slope_out = coeffs_out[0]
        st.metric(
            "Output Degradation Slope",
            f"{slope_out:.3f} MW/point",
            delta=f"{slope_out * len(df_trend):.2f} MW over entire period",
            delta_color="inverse" if slope_out < 0 else "normal"
        )
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_trend["Date"], y=df_trend["Gross HR"], mode="lines+markers",
                             name=f"Gross HR ({unit})", marker=dict(size=10), line=dict(width=2),
                             hovertemplate="<b>%{text}</b><br>Date: %{x}<br>HR: %{y:.1f} " + unit + "<extra></extra>",
                             text=df_trend["Snapshot"]))
    fig.add_trace(go.Scatter(x=df_trend["Date"], y=df_trend["Corrected HR"], mode="lines+markers",
                             name=f"Corrected HR ({unit})", marker=dict(size=10, symbol="diamond"),
                             line=dict(width=2, dash="dash"),
                             hovertemplate="<b>%{text}</b><br>Date: %{x}<br>HR: %{y:.1f} " + unit + "<extra></extra>",
                             text=df_trend["Snapshot"]))
    fig.add_trace(go.Scatter(x=df_trend["Date"], y=df_trend["HR Trend"], mode="lines",
                             name=f"Trend Line ({slope_hr:.2f} {unit}/point)",
                             line=dict(color="gray", dash="dot")))
    fig.update_layout(xaxis_title="Date", yaxis_title=f"Gross Heat Rate ({unit})", height=400,
                      legend=dict(x=0.01, y=0.99), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---- 2. MODE COMPARISON ----
st.header("⚙️ 2. Mode Comparison")

mode_data = []
for snap in snapshots:
    mode = get_mode(snap)
    if mode is None or str(mode).strip() == "":
        continue
    res = gt.calculate(snap)
    if "error" not in res and res.get("gross_heat_rate_kj_per_kwh") is not None:
        mode_data.append({
            "Snapshot": snap,
            "Mode": str(mode).strip(),
            "Gross HR": convert_hr(res["gross_heat_rate_kj_per_kwh"], "kJ/kWh"),
            "Corrected HR": convert_hr(res["corrected_heat_rate_kj_per_kwh"], "kJ/kWh"),
            "Output (MW)": res["gross_output_mw"],
            "Efficiency (%)": res["thermal_efficiency_percent"],
        })

if not mode_data:
    st.warning("No operating mode data found (MODE column might be missing).")
else:
    df_mode = pd.DataFrame(mode_data)
    mode_agg = df_mode.groupby("Mode").agg({
        "Gross HR": "mean",
        "Corrected HR": "mean",
        "Output (MW)": "mean",
        "Efficiency (%)": "mean",
        "Snapshot": "count"
    }).rename(columns={"Snapshot": "Count"}).reset_index()
    
    fig_mode = go.Figure()
    fig_mode.add_trace(go.Bar(x=mode_agg["Mode"], y=mode_agg["Gross HR"],
                              name=f"Avg Gross HR ({unit})", marker_color="royalblue",
                              text=mode_agg["Gross HR"].round(1), textposition="outside"))
    fig_mode.add_trace(go.Bar(x=mode_agg["Mode"], y=mode_agg["Corrected HR"],
                              name=f"Avg Corrected HR ({unit})", marker_color="crimson",
                              text=mode_agg["Corrected HR"].round(1), textposition="outside"))
    fig_mode.update_layout(xaxis_title="Operating Mode", yaxis_title=f"Heat Rate ({unit})",
                           barmode="group", height=400, legend=dict(x=0.01, y=0.99))
    st.plotly_chart(fig_mode, use_container_width=True)
    
    fig_eff = go.Figure()
    fig_eff.add_trace(go.Bar(x=mode_agg["Mode"], y=mode_agg["Efficiency (%)"],
                             name="Avg Efficiency (%)", marker_color="seagreen",
                             text=mode_agg["Efficiency (%)"].round(2), textposition="outside"))
    fig_eff.update_layout(xaxis_title="Operating Mode", yaxis_title="Efficiency (%)", height=350)
    st.plotly_chart(fig_eff, use_container_width=True)
    
    with st.expander("📋 Mode Aggregation Table"):
        st.dataframe(mode_agg.style.format({
            "Gross HR": "{:.1f}",
            "Corrected HR": "{:.1f}",
            "Output (MW)": "{:.2f}",
            "Efficiency (%)": "{:.2f}",
            "Count": "{}",
        }), use_container_width=True)

st.divider()

# ---- 3. HEAT RATE DECOMPOSITION (WATERFALL) ----
st.header("🧩 3. Heat Rate Decomposition (Waterfall)")
st.markdown("Breaks down the difference between the selected snapshot and the baseline into contributions from each correction factor (C1..C9).")

baseline_snap = st.selectbox("Baseline Snapshot", snapshots, index=0, key="waterfall_baseline")
target_snap = st.selectbox("Target Snapshot", snapshots, index=min(1, len(snapshots)-1), key="waterfall_target")

if st.button("Run Decomposition", key="waterfall_btn"):
    if target_snap == baseline_snap:
        st.info("Target and baseline are the same — no decomposition to show.")
    else:
        # Get correction factors using rule engine
        def get_cf(snap):
            # Use the same logic as in corrections page
            ctim = db.value("CTIM", snap) if "CTIM" in db.tags() else None
            rh = db.value("RH", snap) if "RH" in db.tags() else 60.0
            afpip = db.value("AFPIP", snap) if "AFPIP" in db.tags() else None
            afpcs = db.value("AFPCS", snap) if "AFPCS" in db.tags() else None
            exh = db.value("96EP#1/2#3", snap) if "96EP#1/2#3" in db.tags() else None
            c1 = rule_engine.evaluate_curve("C1_Inlet_Temp", ctim, asset_type=asset_type) if ctim else 1.0
            c2 = rule_engine.evaluate_curve("C2_Humidity", rh, asset_type=asset_type) if rh else 1.0
            press_mbar = afpip * 1.33322 if afpip else 1013.25
            c3 = rule_engine.evaluate_curve("C3_Ambient_Pressure", press_mbar, asset_type=asset_type)
            c6 = rule_engine.evaluate_curve("C6_Inlet_Loss", afpcs, asset_type=asset_type) if afpcs else 1.0
            c7 = rule_engine.evaluate_curve("C7_Exhaust_Loss", exh, asset_type=asset_type) if exh else 1.0
            total = c1 * c2 * c3 * c6 * c7  # others default 1
            return {"C1": c1, "C2": c2, "C3": c3, "C6": c6, "C7": c7, "total": total}

        base_factors = get_cf(baseline_snap)
        target_factors = get_cf(target_snap)

        base_res = gt.calculate(baseline_snap)
        target_res = gt.calculate(target_snap)
        if "error" in base_res or "error" in target_res:
            st.error("Error calculating performance for one of the snapshots.")
        else:
            base_hr = convert_hr(base_res["gross_heat_rate_kj_per_kwh"], "kJ/kWh")
            target_hr = convert_hr(target_res["gross_heat_rate_kj_per_kwh"], "kJ/kWh")
            delta_total = target_hr - base_hr

            c_names = {
                "C1": "C1: Inlet Temp",
                "C2": "C2: Humidity",
                "C3": "C3: Pressure",
                "C6": "C6: Inlet Loss",
                "C7": "C7: Exhaust Loss",
            }
            waterfall_data = []
            current_hr = base_hr
            waterfall_data.append({"Category": "Baseline HR", "Value": current_hr, "Label": f"{base_hr:.1f}"})
            for key in ["C1", "C2", "C3", "C6", "C7"]:
                if key in base_factors and key in target_factors:
                    base_val = base_factors[key]
                    target_val = target_factors[key]
                    if base_val != 0:
                        impact = current_hr * (target_val / base_val - 1)
                        current_hr += impact
                        waterfall_data.append({
                            "Category": c_names[key],
                            "Value": impact,
                            "Label": f"{impact:+.1f}",
                            "Delta": impact,
                        })
            waterfall_data.append({"Category": "Final HR", "Value": current_hr, "Label": f"{current_hr:.1f}"})
            df_waterfall = pd.DataFrame(waterfall_data)

            fig_waterfall = go.Figure(go.Waterfall(
                x=df_waterfall["Category"],
                y=df_waterfall["Value"],
                measure=["absolute"] + ["relative"] * (len(df_waterfall) - 2) + ["total"],
                name="HR Decomposition",
                text=df_waterfall["Label"],
                textposition="outside",
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                increasing={"marker": {"color": "red"}},
                decreasing={"marker": {"color": "green"}},
                totals={"marker": {"color": "darkblue"}},
            ))
            fig_waterfall.update_layout(
                title=f"HR Decomposition: {target_snap} vs {baseline_snap}",
                xaxis=dict(title="Correction Factor", tickangle=45),
                yaxis=dict(title=f"Heat Rate ({unit})"),
                height=450,
                hovermode="x",
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"Baseline HR ({baseline_snap})", f"{base_hr:.1f} {unit}")
            with col2:
                st.metric(f"Target HR ({target_snap})", f"{target_hr:.1f} {unit}")
            with col3:
                st.metric("Total Delta", f"{delta_total:+.1f} {unit}", 
                          delta=f"{delta_total/base_hr*100:+.2f}%")

st.divider()

# ---- 4. OPERATING ENVELOPE SCATTER ----
st.header("📐 4. Operating Envelope Scatter")
st.markdown("Plots Heat Rate vs Output to identify the optimal (most efficient) load point.")

scatter_data = []
for snap in snapshots:
    res = gt.calculate(snap)
    if "error" not in res and res.get("gross_output_mw") is not None and res.get("gross_heat_rate_kj_per_kwh") is not None:
        mode = get_mode(snap)
        scatter_data.append({
            "Snapshot": snap,
            "Output (MW)": res["gross_output_mw"],
            "Gross HR": convert_hr(res["gross_heat_rate_kj_per_kwh"], "kJ/kWh"),
            "Corrected HR": convert_hr(res["corrected_heat_rate_kj_per_kwh"], "kJ/kWh"),
            "Efficiency (%)": res["thermal_efficiency_percent"],
            "Mode": str(mode).strip() if mode else "Unknown",
        })

if not scatter_data:
    st.warning("Not enough data for envelope analysis.")
else:
    df_scatter = pd.DataFrame(scatter_data)
    
    fig_scatter = go.Figure()
    for mode in df_scatter["Mode"].unique():
        df_mode_sub = df_scatter[df_scatter["Mode"] == mode]
        fig_scatter.add_trace(go.Scatter(
            x=df_mode_sub["Output (MW)"],
            y=df_mode_sub["Gross HR"],
            mode="markers",
            name=f"Mode {mode}",
            marker=dict(size=12),
            text=df_mode_sub["Snapshot"],
            hovertemplate="<b>%{text}</b><br>Output: %{x:.1f} MW<br>HR: %{y:.1f} " + unit + "<extra></extra>",
        ))
    if len(df_scatter) > 2:
        x_vals = df_scatter["Output (MW)"].values
        y_vals = df_scatter["Gross HR"].values
        coeffs_env = np.polyfit(x_vals, y_vals, 2)
        x_smooth = np.linspace(min(x_vals), max(x_vals), 100)
        y_smooth = np.polyval(coeffs_env, x_smooth)
        fig_scatter.add_trace(go.Scatter(
            x=x_smooth,
            y=y_smooth,
            mode="lines",
            name="Polynomial Trend",
            line=dict(color="gray", dash="dash", width=2),
        ))
        a, b, c = coeffs_env
        if a != 0:
            sweet_spot = -b / (2 * a)
            sweet_hr = np.polyval(coeffs_env, sweet_spot)
            fig_scatter.add_annotation(
                x=sweet_spot,
                y=sweet_hr,
                text=f"Sweet Spot<br>{sweet_spot:.1f} MW<br>{sweet_hr:.1f} {unit}",
                showarrow=True,
                arrowhead=2,
                ax=20,
                ay=-30,
            )
    fig_scatter.update_layout(
        xaxis_title="Gross Output (MW)",
        yaxis_title=f"Gross Heat Rate ({unit})",
        height=450,
        legend=dict(x=0.01, y=0.99),
        hovermode="closest",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ---- 5. INLET FILTER HEALTH MONITOR (Rule-Driven Alarm) ----
st.header("🧹 5. Inlet Filter Health Monitor")
st.markdown("Tracks Inlet Pressure Loss (`AFPCS`) over time with an alarm threshold from Rules.")

filter_data = []
for snap in snapshots:
    dt = get_snapshot_datetime(snap)
    try:
        dp = db.value("AFPCS", snap)
    except:
        dp = None
    if dp is not None and dt is not None:
        filter_data.append({
            "Snapshot": snap,
            "Date": dt,
            "AFPCS (mmwc)": dp,
        })

if not filter_data:
    st.warning("No AFPCS data found.")
else:
    df_filter = pd.DataFrame(filter_data).sort_values("Date")
    
    # ---- Get alarm threshold from Rules ----
    rule = rule_engine.thresholds.get("Inlet Filter DP")
    if rule:
        warn_high = rule.get("warn_high") or 80.0
        critical_high = rule.get("good_high") or 0.0
        alarm_threshold = critical_high if critical_high > warn_high else warn_high
    else:
        alarm_threshold = 80.0  # fallback
    
    fig_filter = go.Figure()
    fig_filter.add_trace(go.Scatter(
        x=df_filter["Date"],
        y=df_filter["AFPCS (mmwc)"],
        mode="lines+markers",
        name="AFPCS (mmwc)",
        marker=dict(size=10, color="royalblue"),
        line=dict(width=2),
        hovertemplate="<b>%{text}</b><br>Date: %{x}<br>DP: %{y:.2f} mmwc<extra></extra>",
        text=df_filter["Snapshot"],
    ))
    fig_filter.add_hline(
        y=alarm_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Alarm Threshold: {alarm_threshold} mmwc",
        annotation_position="bottom right",
    )
    fig_filter.add_hrect(
        y0=alarm_threshold,
        y1=df_filter["AFPCS (mmwc)"].max() * 1.1,
        fillcolor="red",
        opacity=0.1,
        line_width=0,
    )
    fig_filter.update_layout(
        xaxis_title="Date",
        yaxis_title="Inlet Pressure Loss (mmwc)",
        height=400,
        hovermode="x unified",
    )
    st.plotly_chart(fig_filter, use_container_width=True)
    
    latest = df_filter.iloc[-1]
    alert = "🔴 ALERT" if latest["AFPCS (mmwc)"] > alarm_threshold else "🟢 OK"
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Latest DP", f"{latest['AFPCS (mmwc)']:.2f} mmwc", delta=f"{latest['AFPCS (mmwc)'] - alarm_threshold:.2f} from threshold")
    with col2:
        st.metric("Status", alert)
    with col3:
        days = (latest["Date"] - df_filter.iloc[0]["Date"]).days
        st.metric("Monitoring Period", f"{days} days")

st.divider()

# ---- 6. COMBUSTION & VIBRATION SUMMARY (Rule-Driven Alerts) ----
st.header("🔥 6. Combustion & Vibration Health Summary")
st.markdown("Exhaust temperature spreads and bearing vibrations — flagged when exceeding limits defined in Rules.")

spread_tags = ["TTXSP#1", "TTXSP#2", "TTXSP#3", "TTXSP#4"]
vibration_tags = [t for t in db.tags() if t.startswith("39V-")]

health_data = []
for snap in snapshots:
    row = {"Snapshot": snap}
    spreads = []
    for tag in spread_tags:
        val = get_spread(snap, tag)
        if val is not None:
            spreads.append(val)
            row[tag] = val
        else:
            row[tag] = None
    row["Max Spread"] = max(spreads) if spreads else None
    row["Avg Spread"] = np.mean(spreads) if spreads else None
    
    vibes = []
    for tag in vibration_tags:
        val = get_vibration(snap, tag)
        if val is not None:
            vibes.append(val)
            row[tag] = val
    row["Max Vibration"] = max(vibes) if vibes else None
    row["Avg Vibration"] = np.mean(vibes) if vibes else None
    
    health_data.append(row)

df_health = pd.DataFrame(health_data)
df_health_display = df_health.dropna(subset=["Max Spread", "Max Vibration"], how="all")

if df_health_display.empty:
    st.warning("No spread or vibration data available.")
else:
    # ---- Get thresholds from Rules ----
    spread_rule = rule_engine.thresholds.get("Max Exhaust Spread")
    if spread_rule:
        spread_warn = spread_rule.get("warn_high") or 30.0
        spread_crit = spread_rule.get("good_high") or 30.0
    else:
        spread_warn = 30.0
        spread_crit = 40.0

    vibe_rule = rule_engine.thresholds.get("Max Vibration")
    if vibe_rule:
        vibe_warn = vibe_rule.get("warn_high") or 5.0
        vibe_crit = vibe_rule.get("good_high") or 5.0
    else:
        vibe_warn = 5.0
        vibe_crit = 7.0

    def color_spread(val):
        if val is None:
            return ""
        if val > spread_crit:
            return "background-color: #f8d7da; color: #721c24"
        elif val > spread_warn:
            return "background-color: #fff3cd; color: #856404"
        else:
            return "background-color: #d4edda; color: #155724"
    
    def color_vibration(val):
        if val is None:
            return ""
        if val > vibe_crit:
            return "background-color: #f8d7da; color: #721c24"
        elif val > vibe_warn:
            return "background-color: #fff3cd; color: #856404"
        else:
            return "background-color: #d4edda; color: #155724"
    
    display_cols = ["Snapshot", "Max Spread", "Avg Spread", "Max Vibration", "Avg Vibration"]
    display_df = df_health_display[display_cols].copy()
    display_df.columns = ["Snapshot", "Max Spread (°C)", "Avg Spread (°C)", "Max Vibration (mm/s)", "Avg Vibration (mm/s)"]
    
    styled_health = display_df.style.map(color_spread, subset=["Max Spread (°C)", "Avg Spread (°C)"])
    styled_health = styled_health.map(color_vibration, subset=["Max Vibration (mm/s)", "Avg Vibration (mm/s)"])
    
    st.dataframe(styled_health.format({
        "Max Spread (°C)": "{:.2f}",
        "Avg Spread (°C)": "{:.2f}",
        "Max Vibration (mm/s)": "{:.2f}",
        "Avg Vibration (mm/s)": "{:.2f}",
    }), use_container_width=True)
    
    # ---- Alerts summary ----
    alerts = []
    for _, row in display_df.iterrows():
        if row["Max Spread (°C)"] and row["Max Spread (°C)"] > spread_crit:
            alerts.append(f"🔴 {row['Snapshot']}: Spread = {row['Max Spread (°C)']:.1f}°C (Critical)")
        elif row["Max Spread (°C)"] and row["Max Spread (°C)"] > spread_warn:
            alerts.append(f"🟡 {row['Snapshot']}: Spread = {row['Max Spread (°C)']:.1f}°C (Warning)")
        if row["Max Vibration (mm/s)"] and row["Max Vibration (mm/s)"] > vibe_crit:
            alerts.append(f"🔴 {row['Snapshot']}: Vibration = {row['Max Vibration (mm/s)']:.1f} mm/s (Critical)")
        elif row["Max Vibration (mm/s)"] and row["Max Vibration (mm/s)"] > vibe_warn:
            alerts.append(f"🟡 {row['Snapshot']}: Vibration = {row['Max Vibration (mm/s)']:.1f} mm/s (Warning)")
    
    if alerts:
        st.warning("⚠️ Alerts detected:")
        for alert in alerts:
            st.write(alert)
    else:
        st.success("✅ No combustion or vibration alerts. All parameters within healthy limits.")