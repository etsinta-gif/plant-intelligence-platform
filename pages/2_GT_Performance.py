# pages/2_GT_Performance.py

import streamlit as st
import pandas as pd
from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance
from utils.unit_helpers import get_heat_rate_unit, set_heat_rate_unit, convert_hr

st.set_page_config(page_title="GT Performance", layout="wide")

# ---- Unit selector in sidebar ----
with st.sidebar:
    st.header("⚙️ Settings")
    current_unit = get_heat_rate_unit()
    new_unit = st.radio(
        "Heat Rate Unit",
        options=["kJ/kWh", "kcal/kWh"],
        index=0 if current_unit == "kJ/kWh" else 1,
        key="hr_unit_radio_gt"
    )
    if new_unit != current_unit:
        set_heat_rate_unit(new_unit)
        st.rerun()

st.title("⚡ Gas Turbine Performance")

# Load data
eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)

snapshots = db.snapshots_list()
selected = st.selectbox("Select Snapshot", snapshots)

# ---- Comparison toggle ----
baseline_snapshot = "PG TEST DATA"
if baseline_snapshot not in snapshots:
    baseline_snapshot = snapshots[0]

compare_mode = st.checkbox(
    f"Compare to Baseline: {baseline_snapshot}",
    help="Shows deltas (absolute and percentage) compared to the PG Test reference."
)

if st.button("Calculate", type="primary"):
    unit = get_heat_rate_unit()
    
    # ---- If comparing the same snapshot, just show single mode ----
    if compare_mode and selected == baseline_snapshot:
        st.info("ℹ️ The selected snapshot is the same as the baseline. No differences to show.")
        compare_mode = False  # fallback to single mode
    
    if compare_mode:
        # ---- Comparison Mode (selected != baseline) ----
        comp = gt.compare(selected, baseline_snapshot)
        
        if "error" in comp:
            st.error(f"Error: {comp['error']}")
        else:
            sel = comp["selected"]
            base = comp["baseline_data"]
            deltas = comp["deltas"]
            pct = comp["pct_changes"]
            
            # ---- Display side-by-side ----
            st.subheader(f"📊 Performance Comparison: {selected} vs {baseline_snapshot}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Metric**")
                st.write("Gross Output (MW)")
                st.write(f"Gross HR ({unit})")
                st.write(f"Corrected HR ({unit})")
                st.write("Efficiency (%)")
                st.write("Corrected Eff (%)")
                st.write("Pressure Ratio")
                st.write("Correction Factor")
            
            with col2:
                st.markdown(f"**{baseline_snapshot}**")
                st.write(f"{base['gross_output_mw']:.2f}" if base['gross_output_mw'] is not None else "N/A")
                hr_base = convert_hr(base['gross_heat_rate_kj_per_kwh'], "kJ/kWh") if base['gross_heat_rate_kj_per_kwh'] is not None else None
                st.write(f"{hr_base:.1f}" if hr_base is not None else "N/A")
                hr_corr_base = convert_hr(base['corrected_heat_rate_kj_per_kwh'], "kJ/kWh") if base['corrected_heat_rate_kj_per_kwh'] is not None else None
                st.write(f"{hr_corr_base:.1f}" if hr_corr_base is not None else "N/A")
                st.write(f"{base['thermal_efficiency_percent']:.2f}" if base['thermal_efficiency_percent'] is not None else "N/A")
                st.write(f"{base['corrected_efficiency_percent']:.2f}" if base['corrected_efficiency_percent'] is not None else "N/A")
                st.write(f"{base['pressure_ratio']:.2f}" if base['pressure_ratio'] is not None else "N/A")
                st.write(f"{base['correction_factor_product']:.6f}" if base['correction_factor_product'] is not None else "N/A")
            
            with col3:
                st.markdown(f"**{selected}**")
                st.write(f"{sel['gross_output_mw']:.2f}" if sel['gross_output_mw'] is not None else "N/A")
                hr_sel = convert_hr(sel['gross_heat_rate_kj_per_kwh'], "kJ/kWh") if sel['gross_heat_rate_kj_per_kwh'] is not None else None
                st.write(f"{hr_sel:.1f}" if hr_sel is not None else "N/A")
                hr_corr_sel = convert_hr(sel['corrected_heat_rate_kj_per_kwh'], "kJ/kWh") if sel['corrected_heat_rate_kj_per_kwh'] is not None else None
                st.write(f"{hr_corr_sel:.1f}" if hr_corr_sel is not None else "N/A")
                st.write(f"{sel['thermal_efficiency_percent']:.2f}" if sel['thermal_efficiency_percent'] is not None else "N/A")
                st.write(f"{sel['corrected_efficiency_percent']:.2f}" if sel['corrected_efficiency_percent'] is not None else "N/A")
                st.write(f"{sel['pressure_ratio']:.2f}" if sel['pressure_ratio'] is not None else "N/A")
                st.write(f"{sel['correction_factor_product']:.6f}" if sel['correction_factor_product'] is not None else "N/A")
            
            # ---- Delta Table with Nuanced Status ----
            st.divider()
            st.subheader("📈 Deltas (Selected - Baseline)")
            
            # Define tolerance thresholds (relative %)
            # For heat rate: better if < -0.5%, poor if > +0.5%, else meets
            # For efficiency/output: better if > +0.5%, poor if < -0.5%, else meets
            # For pressure ratio: similar to output
            # For correction factor: similar to heat rate (closer to 1 is better, but we treat same as HR)
            # We'll define per metric
            tolerance = {
                "gross_output_mw": 0.5,           # % change
                "gross_heat_rate_kj_per_kwh": 0.5,
                "corrected_heat_rate_kj_per_kwh": 0.5,
                "thermal_efficiency_percent": 0.5,
                "corrected_efficiency_percent": 0.5,
                "pressure_ratio": 0.5,
                "correction_factor_product": 0.5,
            }
            
            delta_data = []
            for metric, value in deltas.items():
                if value is None:
                    continue
                pct_val = pct.get(metric)
                if pct_val is None:
                    continue
                
                # Determine status based on metric type and percentage change
                # For HR & Correction Factor: lower is better
                if metric in ["gross_heat_rate_kj_per_kwh", "corrected_heat_rate_kj_per_kwh", "correction_factor_product"]:
                    if pct_val < -tolerance[metric]:
                        status = "🟢 Better"
                    elif pct_val > tolerance[metric]:
                        status = "🔴 Poor"
                    else:
                        status = "🟡 Meets"
                # For Output, Efficiency, Pressure Ratio: higher is better
                elif metric in ["gross_output_mw", "thermal_efficiency_percent", "corrected_efficiency_percent", "pressure_ratio"]:
                    if pct_val > tolerance[metric]:
                        status = "🟢 Better"
                    elif pct_val < -tolerance[metric]:
                        status = "🔴 Poor"
                    else:
                        status = "🟡 Meets"
                else:
                    status = "N/A"
                
                # Format display value
                if metric in ["gross_heat_rate_kj_per_kwh", "corrected_heat_rate_kj_per_kwh"]:
                    display_value = convert_hr(value, "kJ/kWh")
                else:
                    display_value = value
                
                display_names = {
                    "gross_output_mw": "Gross Output (MW)",
                    "gross_heat_rate_kj_per_kwh": f"Gross HR ({unit})",
                    "corrected_heat_rate_kj_per_kwh": f"Corrected HR ({unit})",
                    "thermal_efficiency_percent": "Efficiency (%)",
                    "corrected_efficiency_percent": "Corrected Eff (%)",
                    "pressure_ratio": "Pressure Ratio",
                    "correction_factor_product": "Correction Factor",
                }
                display_name = display_names.get(metric, metric)
                
                delta_data.append({
                    "Metric": display_name,
                    "Delta": f"{display_value:+.2f}" if isinstance(display_value, (int, float)) else "N/A",
                    "Change": f"{pct_val:+.2f}%",
                    "Status": status,
                })
            
            df_delta = pd.DataFrame(delta_data)
            
            # Apply styling using .map (replaces deprecated .applymap)
            def color_status(val):
                if "🟢" in str(val):
                    return "background-color: #d4edda"  # light green
                elif "🟡" in str(val):
                    return "background-color: #fff3cd"  # light yellow
                elif "🔴" in str(val):
                    return "background-color: #f8d7da"  # light red
                else:
                    return ""
            
            styled_df = df_delta.style.map(color_status, subset=["Status"])
            st.dataframe(styled_df, use_container_width=True)
            
            # ---- Individual result expanders ----
            with st.expander("📋 Full Data: Selected Snapshot"):
                st.json(sel)
            with st.expander("📋 Full Data: Baseline Snapshot"):
                st.json(base)
    
    else:
        # ---- Single Snapshot Mode (no comparison) ----
        result = gt.calculate(selected)
        
        if "error" in result:
            st.error(f"Error: {result['error']}")
        else:
            # Convert heat rates
            gross_hr_display = convert_hr(result['gross_heat_rate_kj_per_kwh'], "kJ/kWh") if result['gross_heat_rate_kj_per_kwh'] is not None else None
            corrected_hr_display = convert_hr(result['corrected_heat_rate_kj_per_kwh'], "kJ/kWh") if result['corrected_heat_rate_kj_per_kwh'] is not None else None
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gross Output", f"{result['gross_output_mw']:.2f} MW" if result['gross_output_mw'] is not None else "N/A")
                st.metric("Fuel Flow", f"{result['fuel_flow_kg_per_s']:.3f} kg/s" if result['fuel_flow_kg_per_s'] is not None else "N/A")
                st.metric("LHV", f"{result['lhv_kjkg']:.1f} kJ/kg" if result['lhv_kjkg'] is not None else "N/A")
            with col2:
                st.metric(f"Gross Heat Rate", f"{gross_hr_display:.1f} {unit}" if gross_hr_display is not None else "N/A")
                st.metric(f"Corrected Heat Rate", f"{corrected_hr_display:.1f} {unit}" if corrected_hr_display is not None else "N/A")
                st.metric("Pressure Ratio", f"{result['pressure_ratio']:.2f}" if result['pressure_ratio'] is not None else "N/A")
            with col3:
                st.metric("Efficiency (Gross)", f"{result['thermal_efficiency_percent']:.2f} %" if result['thermal_efficiency_percent'] is not None else "N/A")
                st.metric("Efficiency (Corrected)", f"{result['corrected_efficiency_percent']:.2f} %" if result['corrected_efficiency_percent'] is not None else "N/A")
                st.metric("Correction Factor", f"{result['correction_factor_product']:.6f}" if result['correction_factor_product'] is not None else "N/A")
            
            with st.expander("📋 Full Result Data"):
                st.json(result)