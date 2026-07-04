# pages/5_AI_Engineer.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# ---- Path setup ----
current_dir = Path(__file__).resolve().parent.parent
shared_lib = current_dir / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "core" / "src"))
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance
from calculations.excel_reader import load_raw_data
from engineeros.services.rule_engine import RuleEngine
from utils.unit_helpers import get_heat_rate_unit, set_heat_rate_unit, convert_hr

st.set_page_config(page_title="AI Engineer", layout="wide")

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
        key="hr_unit_radio_ai"
    )
    if new_unit != current_unit:
        set_heat_rate_unit(new_unit)
        st.rerun()
    
    st.divider()
    st.subheader("🔍 Detection Settings")
    anomaly_threshold = st.slider(
        "Anomaly Z‑Score Threshold",
        min_value=1.5, max_value=3.5, value=2.5, step=0.1,
        help="Metrics with |z| > threshold are flagged as anomalies."
    )

st.title("🧠 AI Engineer – Comprehensive Data Analysis")

# ---- Load data ----
eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)
raw_df = load_raw_data()
snapshots = db.snapshots_list()
unit = get_heat_rate_unit()

# ---- 1. Build a full dataframe with all numeric tags ----
all_tags = db.tags()
numeric_tags = []
data_dict = {"Snapshot": snapshots}

for tag in all_tags:
    try:
        values = [db.value(tag, snap) for snap in snapshots]
        if any(v is not None for v in values):
            numeric_tags.append(tag)
            data_dict[tag] = values
    except:
        continue

df_raw = pd.DataFrame(data_dict)

# ---- 2. Get performance metrics ----
perf_results = []
for snap in snapshots:
    res = gt.calculate(snap)
    if "error" not in res:
        perf_results.append({
            "Snapshot": snap,
            "gross_output_mw": res.get("gross_output_mw"),
            "gross_heat_rate_kj_per_kwh": res.get("gross_heat_rate_kj_per_kwh"),
            "corrected_heat_rate_kj_per_kwh": res.get("corrected_heat_rate_kj_per_kwh"),
            "thermal_efficiency_percent": res.get("thermal_efficiency_percent"),
            "corrected_efficiency_percent": res.get("corrected_efficiency_percent"),
            "pressure_ratio": res.get("pressure_ratio"),
            "correction_factor_product": res.get("correction_factor_product"),
            "fuel_flow_kg_per_s": res.get("fuel_flow_kg_per_s"),
            "lhv_kjkg": res.get("lhv_kjkg"),
            "compressor_inlet_temp_c": res.get("compressor_inlet_temp_c"),
        })
df_perf = pd.DataFrame(perf_results)

# ---- 3. Combine ----
df_combined = df_perf.copy()
for tag in numeric_tags:
    if tag not in df_combined.columns and tag != "Snapshot":
        df_combined[tag] = df_raw[tag].values

df_plot = df_combined.set_index("Snapshot")

# ---- 4. Tabs ----
tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Overview", "🚨 Anomaly Detection", "📈 ABC Analysis", "🔗 Correlations"])

# ---- TAB 1: Data Overview ----
with tab1:
    st.subheader("All Numeric Parameters Across Snapshots")
    numeric_df = df_plot.select_dtypes(include=[np.number])
    if numeric_df.empty:
        st.warning("No numeric data available.")
    else:
        st.dataframe(numeric_df.style.format("{:.2f}"), use_container_width=True)
    
    st.subheader("📋 Basic Statistics")
    stats = numeric_df.describe().transpose()
    st.dataframe(stats.style.format("{:.2f}"), use_container_width=True)

# ---- TAB 2: Anomaly Detection ----
with tab2:
    st.subheader("🚨 Anomaly Detection by Z‑Score")
    numeric_cols = df_plot.select_dtypes(include=[np.number]).columns
    if numeric_cols.empty:
        st.warning("No numeric data available for anomaly detection.")
    else:
        z_scores = pd.DataFrame(index=df_plot.index)
        for col in numeric_cols:
            if df_plot[col].std() != 0:
                z_scores[col] = (df_plot[col] - df_plot[col].mean()) / df_plot[col].std()
            else:
                z_scores[col] = 0
        
        anomalies = (z_scores.abs() > anomaly_threshold)
        anomaly_count = anomalies.sum().sum()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Anomalies", f"{anomaly_count}")
        with col2:
            st.metric("Anomaly Threshold", f"|z| > {anomaly_threshold}")
        with col3:
            st.metric("Snapshots", len(df_plot))
        
        if anomaly_count > 0:
            st.write("### Anomaly Flag Matrix (Rows: Snapshots, Columns: Metrics)")
            def color_anomaly(val):
                if val == True:
                    return "background-color: #f8d7da; color: #721c24"
                else:
                    return ""
            styled_anom = anomalies.style.map(color_anomaly)
            st.dataframe(styled_anom, use_container_width=True)
            
            st.write("### Anomaly Count per Snapshot")
            anomaly_counts = anomalies.sum(axis=1).sort_values(ascending=False)
            fig = px.bar(x=anomaly_counts.index, y=anomaly_counts.values, 
                         title="Number of Anomalies by Snapshot",
                         labels={"x": "Snapshot", "y": "Anomaly Count"})
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("### Anomaly Count per Metric")
            metric_anomaly = anomalies.sum(axis=0).sort_values(ascending=False)
            fig2 = px.bar(x=metric_anomaly.index, y=metric_anomaly.values,
                          title="Metrics with Most Anomalies",
                          labels={"x": "Metric", "y": "Anomaly Count"})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.success("✅ No anomalies detected at the current threshold.")

# ---- TAB 3: ABC Analysis (Rule-Driven) ----
with tab3:
    st.subheader("📈 ABC Analysis – Variability Classification")
    st.markdown("""
    **ABC Analysis** classifies metrics based on their **Coefficient of Variation (CV)**:
    - **A (High Variability)** – top 20% of CV – most influential/dynamic parameters.
    - **B (Medium Variability)** – middle 30%.
    - **C (Low Variability)** – bottom 50% – stable parameters.
    """)
    
    # ---- Read thresholds from Rules ----
    ABC_A = rule_engine.get_constant("ABC_A_THRESHOLD") or 70.0
    ABC_B = rule_engine.get_constant("ABC_B_THRESHOLD") or 90.0
    CV_HIGH = rule_engine.get_constant("ABC_CV_HIGH") or 20.0
    CV_MEDIUM = rule_engine.get_constant("ABC_CV_MEDIUM") or 10.0

    numeric_cols = df_plot.select_dtypes(include=[np.number]).columns
    if numeric_cols.empty:
        st.warning("No numeric data available for ABC analysis.")
    else:
        cv_data = {}
        for col in numeric_cols:
            mean_val = df_plot[col].mean()
            std_val = df_plot[col].std()
            if mean_val != 0 and not np.isnan(mean_val) and not np.isnan(std_val):
                cv = (std_val / abs(mean_val)) * 100
                cv_data[col] = cv
        
        if not cv_data:
            st.warning("No valid CV data.")
        else:
            cv_df = pd.DataFrame(list(cv_data.items()), columns=["Metric", "CV (%)"])
            cv_df = cv_df.sort_values("CV (%)", ascending=False).reset_index(drop=True)
            
            total_cv = cv_df["CV (%)"].sum()
            cv_df["Cumulative %"] = cv_df["CV (%)"].cumsum() / total_cv * 100
            
            def classify_cv(row):
                if row["Cumulative %"] <= ABC_A:
                    return "A (High)"
                elif row["Cumulative %"] <= ABC_B:
                    return "B (Medium)"
                else:
                    return "C (Low)"
            cv_df["ABC Class"] = cv_df.apply(classify_cv, axis=1)
            
            # ---- Custom styling using rule thresholds ----
            def color_cv(val):
                if val > CV_HIGH:
                    return 'background-color: #ffcccc; color: #721c24'
                elif val > CV_MEDIUM:
                    return 'background-color: #ffe6b3; color: #7a6000'
                else:
                    return 'background-color: #ccffcc; color: #006600'
            
            styled_cv = cv_df.style.map(color_cv, subset=["CV (%)"])
            st.dataframe(styled_cv, use_container_width=True)
            
            # ---- Pareto chart ----
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=cv_df["Metric"],
                y=cv_df["CV (%)"],
                name="CV (%)",
                marker_color="royalblue",
                text=cv_df["CV (%)"].round(2),
                textposition="outside"
            ))
            fig.add_trace(go.Scatter(
                x=cv_df["Metric"],
                y=cv_df["Cumulative %"],
                name="Cumulative %",
                mode="lines+markers",
                yaxis="y2",
                marker_color="crimson",
                line=dict(width=2)
            ))
            fig.update_layout(
                xaxis=dict(title="Metric", tickangle=45),
                yaxis=dict(title="Coefficient of Variation (%)", side="left"),
                yaxis2=dict(title="Cumulative %", side="right", overlaying="y", range=[0, 100]),
                legend=dict(x=0.8, y=0.9),
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("🔴 A (High Variability)")
                st.write(cv_df[cv_df["ABC Class"] == "A (High)"]["Metric"].tolist())
            with col2:
                st.subheader("🟡 B (Medium)")
                st.write(cv_df[cv_df["ABC Class"] == "B (Medium)"]["Metric"].tolist())
            with col3:
                st.subheader("🟢 C (Low)")
                st.write(cv_df[cv_df["ABC Class"] == "C (Low)"]["Metric"].tolist())

# ---- TAB 4: Correlations ----
with tab4:
    st.subheader("🔗 Correlation Matrix & Impact on Heat Rate")
    
    numeric_cols = df_plot.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < 2:
        st.warning("Not enough numeric columns for correlation.")
    else:
        corr_data = df_plot[numeric_cols].dropna(axis=1, how="any")
        if corr_data.shape[1] < 2:
            st.warning("Insufficient data after dropping NaNs.")
        else:
            corr_matrix = corr_data.corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale="RdBu_r",
                zmin=-1, zmax=1,
                text=corr_matrix.values.round(2),
                texttemplate="%{text}",
                textfont={"size": 10},
            ))
            fig.update_layout(
                title="Correlation Heatmap",
                height=600,
                xaxis=dict(tickangle=45),
            )
            st.plotly_chart(fig, use_container_width=True)
            
            hr_col = None
            if "gross_heat_rate_kj_per_kwh" in corr_matrix.columns:
                hr_col = "gross_heat_rate_kj_per_kwh"
            elif "corrected_heat_rate_kj_per_kwh" in corr_matrix.columns:
                hr_col = "corrected_heat_rate_kj_per_kwh"
            
            if hr_col:
                st.subheader(f"📊 Top Correlates with {hr_col}")
                corr_hr = corr_matrix[hr_col].drop(hr_col).sort_values(key=abs, ascending=False)
                top_corr = corr_hr.head(10)
                fig2 = go.Figure(go.Bar(
                    x=top_corr.index,
                    y=top_corr.values,
                    marker_color=["green" if v > 0 else "red" for v in top_corr.values],
                    text=top_corr.values.round(2),
                    textposition="outside"
                ))
                fig2.update_layout(
                    title="Top 10 Parameters Correlated with Heat Rate",
                    xaxis=dict(title="Parameter", tickangle=45),
                    yaxis=dict(title="Correlation Coefficient"),
                    height=400
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                st.info("""
                **Interpretation**:
                - **Positive correlation** (red) → as the parameter increases, heat rate increases (worse performance).
                - **Negative correlation** (green) → as the parameter increases, heat rate decreases (better performance).
                """)
            else:
                st.info("Heat Rate column not found in correlation matrix.")