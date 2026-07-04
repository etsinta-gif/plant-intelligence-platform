# pages/9_Rule_Explorer.py

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import sys

current_dir = Path(__file__).resolve().parent.parent
shared_lib = current_dir / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from engineeros.services.rule_engine import RuleEngine

st.set_page_config(page_title="Rule Explorer", layout="wide")
rules_path = current_dir / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))

st.title("📋 Engineering Rule Explorer & Editor")

with st.sidebar:
    if st.button("🔄 Refresh Rules from JSON"):
        rule_engine._load_all()
        st.success("Rules reloaded.")
        st.rerun()
    edit_mode = st.checkbox("✏️ Edit Mode", value=False)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Thresholds", "Formulas", "Curves", "Constants", "FMEA"])

def display_section(filename, title, is_fmea=False):
    filepath = rules_path / filename
    if not filepath.exists():
        st.warning(f"File {filename} not found.")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if edit_mode:
        new_content = st.text_area(f"Edit {filename}", value=content, height=400, key=f"edit_{filename}")
        if st.button(f"Save {title}", key=f"save_{filename}"):
            try:
                json.loads(new_content)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                rule_engine._load_all()
                st.success(f"✅ {filename} saved.")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
    else:
        data = rule_engine._load_file(filename)
        if is_fmea:
            modes = data.get("failure_modes", [])
            if modes:
                st.dataframe(pd.DataFrame(modes), use_container_width=True)
        elif filename == "constants.json":
            items = data.get("constants", {})
            if items:
                st.dataframe(pd.DataFrame(list(items.items()), columns=["Constant", "Value"]), use_container_width=True)
        else:
            rules = data.get("rules", {})
            if rules:
                st.dataframe(pd.DataFrame(rules).T, use_container_width=True)

with tab1:
    display_section("thresholds.json", "Thresholds")
with tab2:
    display_section("formulas.json", "Formulas")
with tab3:
    display_section("curves.json", "Curves")
with tab4:
    display_section("constants.json", "Constants")
with tab5:
    display_section("fmea.json", "FMEA", is_fmea=True)