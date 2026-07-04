# calculations/gt_performance.py

import math
from pathlib import Path
import sys
import pandas as pd

current_dir = Path(__file__).resolve().parent
shared_lib = current_dir.parent / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from engineeros.services.rule_engine import RuleEngine
from calculations.excel_reader import load_demo_data

rules_path = current_dir.parent / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))
ASSET_TYPE = "GasTurbine"
_demo_df = load_demo_data()


class GTPerformance:
    def __init__(self, db):
        self.db = db
        self.asset_type = ASSET_TYPE

    def _get_demo_value(self, snapshot, column, default=None):
        row = _demo_df[_demo_df["Test"] == snapshot]
        if row.empty:
            return default
        val = row.iloc[0].get(column, default)
        if pd.isna(val):
            return default
        return val

    def calculate(self, snapshot, apply_corrections=True):
        try:
            dwatt = self.db.value("DWATT", snapshot)
            fqg = self.db.value("FQG", snapshot)
            ctim = self.db.value("CTIM", snapshot)
            cpd = self.db.value("CPD", snapshot)
            afpip = self.db.value("AFPIP", snapshot)

            iso_temp = rule_engine.get_constant("ISO_TEMP")
            iso_press = rule_engine.get_constant("ISO_PRESS")
            iso_rh = rule_engine.get_constant("ISO_RH")
            lhv_kjkg = rule_engine.get_constant("LHV_DEFAULT")

            cpd_kpa = cpd * 98.0665 if cpd else None
            amb_press_kpa = afpip * 0.133322 if afpip else iso_press

            rh = self._get_demo_value(snapshot, "Relative Humidity (%)", iso_rh)

            gross_hr = None
            if dwatt and fqg and lhv_kjkg and dwatt != 0:
                try:
                    context = {"FQG": fqg, "LHV": lhv_kjkg, "DWATT": dwatt}
                    gross_hr = rule_engine.evaluate_formula("HR_GROSS", context, asset_type=self.asset_type)
                except Exception:
                    gross_hr = (fqg * 3.6 * lhv_kjkg) / dwatt

            efficiency = None
            if gross_hr and gross_hr > 0:
                try:
                    context = {"HR_GROSS": gross_hr}
                    efficiency = rule_engine.evaluate_formula("EFFICIENCY_GROSS", context, asset_type=self.asset_type)
                except Exception:
                    efficiency = 3600 / gross_hr * 100

            pr = None
            if amb_press_kpa and cpd_kpa and amb_press_kpa != 0:
                try:
                    context = {"CPD": cpd_kpa, "AFPIP": amb_press_kpa}
                    pr = rule_engine.evaluate_formula("PRESSURE_RATIO", context, asset_type=self.asset_type)
                except Exception:
                    pr = cpd_kpa / amb_press_kpa

            corr_factor = 1.0
            corrected_hr = gross_hr
            corrected_eff = efficiency

            if apply_corrections and gross_hr is not None:
                c1 = rule_engine.evaluate_curve("C1_Inlet_Temp", ctim, asset_type=self.asset_type) if ctim else 1.0
                c2 = rule_engine.evaluate_curve("C2_Humidity", rh, asset_type=self.asset_type) if rh else 1.0
                if afpip:
                    press_mbar = afpip * 1.33322
                    c3 = rule_engine.evaluate_curve("C3_Ambient_Pressure", press_mbar, asset_type=self.asset_type)
                else:
                    c3 = 1.0
                afpcs = self.db.value("AFPCS", snapshot)
                c6 = rule_engine.evaluate_curve("C6_Inlet_Loss", afpcs, asset_type=self.asset_type) if afpcs else 1.0
                exh_loss = self.db.value("96EP#1/2#3", snapshot)
                c7 = rule_engine.evaluate_curve("C7_Exhaust_Loss", exh_loss, asset_type=self.asset_type) if exh_loss else 1.0
                c4 = c5 = c8 = c9 = 1.0
                corr_factor = c1 * c2 * c3 * c4 * c5 * c6 * c7 * c8 * c9
                corrected_hr = gross_hr * corr_factor
                corrected_eff = 3600 / corrected_hr * 100 if corrected_hr else None

            result = {
                "snapshot": snapshot,
                "gross_output_mw": dwatt,
                "fuel_flow_kg_per_s": fqg,
                "fuel_flow_kg_per_h": fqg * 3600 if fqg else None,
                "lhv_kjkg": lhv_kjkg,
                "compressor_inlet_temp_c": ctim,
                "compressor_discharge_pressure_kpa": cpd_kpa,
                "ambient_pressure_kpa": amb_press_kpa,
                "pressure_ratio": pr,
                "gross_heat_rate_kj_per_kwh": gross_hr,
                "thermal_efficiency_percent": efficiency,
                "corrected_heat_rate_kj_per_kwh": corrected_hr,
                "corrected_efficiency_percent": corrected_eff,
                "correction_factor_product": corr_factor,
            }
            return result
        except Exception as e:
            return {"error": str(e), "snapshot": snapshot}