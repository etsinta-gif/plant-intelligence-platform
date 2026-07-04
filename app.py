# app.py

import streamlit as st
import sys
from pathlib import Path

# ---- Setup paths ----
current_dir = Path(__file__).resolve().parent
shared_lib = current_dir / "SharedLibraries"

if shared_lib.exists():
    core_path = shared_lib / "core" / "src"
    engineeros_path = shared_lib / "engineeros" / "src"
    if core_path.exists():
        sys.path.insert(0, str(core_path))
    if engineeros_path.exists():
        sys.path.insert(0, str(engineeros_path))
else:
    st.error("❌ SharedLibraries folder not found. Please ensure it exists.")
    st.stop()

# ---- Imports ----
try:
    from calculations.data_engine import EngineeringData
    from engineeros.services.rule_engine import RuleEngine
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.stop()

# ---- Initialise RuleEngine and Data ----
rules_path = current_dir / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))

try:
    if "data_engine" not in st.session_state:
        st.session_state.data_engine = EngineeringData()
    db = st.session_state.data_engine.db
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# ---- Sidebar ----
with st.sidebar:
    st.title("🏭 Plant Intelligence")
    st.divider()

    snapshots = db.snapshots_list()
    if snapshots:
        selected_snapshot = st.selectbox("Select Snapshot", snapshots)
        st.session_state.snapshot = selected_snapshot
    else:
        st.warning("No snapshots found. Please load data first.")

    st.session_state.asset_type = "GasTurbine"
    st.session_state.asset_code = "GT-1"
    st.session_state.plant_name = "Bangalore Yelekha"

    st.info(f"Asset: {st.session_state.asset_code} ({st.session_state.asset_type})")
    st.divider()
    st.caption("Powered by EngineerOS")

# ---- Pages ----
dashboards = [
    st.Page("pages/1_Executive_Dashboard.py", title="Executive Dashboard", icon="📊"),
    st.Page("pages/2_GT_Performance.py", title="GT Performance", icon="⚡"),
    st.Page("pages/3_Heat_Rate.py", title="Heat Rate", icon="🔥"),
    st.Page("pages/4_Corrections.py", title="Corrections", icon="🔧"),
    st.Page("pages/5_AI_Engineer.py", title="AI Engineer", icon="🧠"),
    st.Page("pages/6_Advanced_Analytics.py", title="Advanced Analytics", icon="📈"),
    st.Page("pages/7_Health_Analytics.py", title="Health Analytics", icon="🏥"),
    st.Page("pages/8_Overall_Assessment.py", title="Overall Assessment", icon="📋"),
    st.Page("pages/9_Rule_Explorer.py", title="Rule Explorer", icon="📐"),
    st.Page("pages/10_RCA_FMEA.py", title="RCA & FMEA", icon="🔍"),
    st.Page("pages/11_Predictive_Forecast.py", title="Predictive Forecast", icon="🔮"),
]

pg = st.navigation(dashboards)
pg.run()