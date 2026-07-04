# pages/10_RCA_FMEA.py

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

current_dir = Path(__file__).resolve().parent.parent
shared_lib = current_dir / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from engineeros.services.rule_engine import RuleEngine
from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance

st.set_page_config(page_title="RCA & FMEA", layout="wide")
st.title("🔍 Root Cause Analysis (RCA) & FMEA")

rules_path = current_dir / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))
eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)
snapshots = db.snapshots_list()

selected_snapshot = st.selectbox("Select Snapshot for Diagnosis", snapshots)

if st.button("Run Root Cause Diagnosis", type="primary"):
    def get_tag(tag):
        try:
            return db.value(tag, selected_snapshot)
        except:
            return None

    cpd = get_tag("CPD")
    afpip = get_tag("AFPIP")
    pressure_ratio = (cpd / (afpip * 0.133322)) if cpd and afpip else None

    spreads = []
    for t in ["TTXSP#1", "TTXSP#2", "TTXSP#3", "TTXSP#4"]:
        val = get_tag(t)
        if val is not None:
            spreads.append(val)
    max_spread = max(spreads) if spreads else None

    vibes = []
    for t in ["39V-1A", "39V-1B", "39V-5A", "39V-5B"]:
        val = get_tag(t)
        if val is not None:
            vibes.append(val)
    max_vibe = max(vibes) if vibes else None

    bt1_1 = get_tag("BTJ1_1")
    bt1_2 = get_tag("BTJ1_2")
    bearing_temp_rise = (bt1_2 - bt1_1) if bt1_1 and bt1_2 else None

    flame_vals = []
    for t in ["1", "2", "3", "4"]:
        val = get_tag(t)
        if val is not None:
            flame_vals.append(val)
    flame_std = pd.Series(flame_vals).std() if flame_vals else None

    metrics = {}
    if pressure_ratio is not None:
        metrics["Pressure Ratio"] = pressure_ratio
    if max_spread is not None:
        metrics["Max Exhaust Spread"] = max_spread
    if max_vibe is not None:
        metrics["Max Vibration"] = max_vibe
    if bearing_temp_rise is not None:
        metrics["Bearing Temp Rise"] = bearing_temp_rise
    if flame_std is not None:
        metrics["Flame Stability (Std Dev)"] = flame_std

    matches = rule_engine.match_failure_modes(metrics, asset_type="GasTurbine")

    st.subheader(f"Diagnosis for {selected_snapshot}")
    if not matches:
        st.success("✅ No known failure modes detected. Asset is operating within expected parameters.")
    else:
        st.write("**Potential Failure Modes (sorted by likelihood):**")
        for match in matches:
            fmea = match["fmea"]
            score = match["match_score"] * 100
            st.markdown(f"### 🔴 {fmea['failure_mode']} (Match Score: {score:.0f}%)")
            st.write(f"**Component:** {fmea['component']}")
            st.write(f"**Effects:** {fmea['effects']}")
            st.write(f"**Causes:** {fmea['causes']}")
            st.write(f"**RPN:** {fmea['rpn']} (Severity: {fmea['severity']}, Occurrence: {fmea['occurrence']}, Detection: {fmea['detection']})")
            st.info(f"**Recommended Action:** {fmea['recommended_action']}")
            st.divider()

    with st.expander("📋 Full FMEA Library"):
        fmea_list = rule_engine.get_fmea(asset_type="GasTurbine")
        if fmea_list:
            df = pd.DataFrame(fmea_list)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No FMEA entries found.")