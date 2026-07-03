# PlantIntelligencePlatform/app.py

import streamlit as st
import sys
from pathlib import Path

# ---- Set up paths ----
current_dir = Path(__file__).resolve().parent

shared_candidates = [
    current_dir / "SharedLibraries",
    current_dir.parent / "SharedLibraries",
]

shared_lib_path = None
for p in shared_candidates:
    if p.exists():
        shared_lib_path = p
        break

if shared_lib_path is None:
    st.error("❌ SharedLibraries folder not found.")
    st.stop()

core_path = shared_lib_path / "core" / "src"
engineeros_path = shared_lib_path / "engineeros" / "src"

if core_path.exists():
    sys.path.insert(0, str(core_path))
if engineeros_path.exists():
    sys.path.insert(0, str(engineeros_path))
else:
    st.error(f"❌ EngineerOS path not found: {engineeros_path}")
    st.stop()

# ---- Imports ----
try:
    from calculations.data_engine import EngineeringData
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.stop()

# ---- Initialize data ----
if "data_engine" not in st.session_state:
    st.session_state.data_engine = EngineeringData()

db = st.session_state.data_engine.db

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

# ---- Navigation (All Pages 1–8) ----
try:
    dashboards = [
        st.Page("pages/1_Executive_Dashboard.py", title="Executive Dashboard", icon="📊"),
        st.Page("pages/2_GT_Performance.py", title="GT Performance", icon="⚡"),
        st.Page("pages/3_Heat_Rate.py", title="Heat Rate", icon="🔥"),
        st.Page("pages/4_Corrections.py", title="Corrections", icon="🔧"),
        st.Page("pages/5_AI_Engineer.py", title="AI Engineer", icon="🧠"),
        st.Page("pages/6_Advanced_Analytics.py", title="Advanced Analytics", icon="📈"),
        st.Page("pages/7_Health_Analytics.py", title="Health Analytics", icon="🏥"),
        st.Page("pages/8_Overall_Assessment.py", title="Overall Assessment", icon="📋"),
    ]
    pg = st.navigation(dashboards)
    pg.run()
except Exception as e:
    st.error(f"❌ Navigation error: {e}")
    import traceback
    st.code(traceback.format_exc())