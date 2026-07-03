# calculations/gt_performance.py

import math
from pathlib import Path
import sys

# ---- Add path to SharedLibraries ----
current_dir = Path(__file__).resolve().parent
shared_lib = current_dir.parent / "SharedLibraries"
if shared_lib.exists():
    sys.path.insert(0, str(shared_lib / "engineeros" / "src"))

from engineeros.services.rule_engine import RuleEngine

# ---- Rule Engine (absolute path) ----
rules_path = current_dir.parent / "Rules"
rule_engine = RuleEngine(data_dir=str(rules_path))

# ---- Asset type ----
# This can be passed as a parameter, but we default to GasTurbine for now.
ASSET_TYPE = "GasTurbine"


class GTPerformance:
    """
    GT Performance calculator using RuleEngine for formulas and constants.
    """

    def __init__(self, db):
        self.db = db
        self.asset_type = ASSET_TYPE

    def calculate(self, snapshot: str, apply_corrections: bool = True):
        try:
            # ---- Read tags ----
            dwatt = self.db.value("DWATT", snapshot)
            fqg = self.db.value("FQG", snapshot)
            ctim = self.db.value("CTIM", snapshot)
            cpd = self.db.value("CPD", snapshot)
            afpip = self.db.value("AFPIP", snapshot)

            # ---- Constants ----
            iso_temp = rule_engine.get_constant("ISO_TEMP")
            iso_press = rule_engine.get_constant("ISO_PRESS")
            iso_rh = rule_engine.get_constant("ISO_RH")

            # ---- Fuel LHV (from fuel_engine or default) ----
            # We'll get it from a separate method, but for now we can read from a tag or demo assumptions.
            # For simplicity, use a constant if not available.
            lhv_kjkg = rule_engine.get_constant("LHV_DEFAULT")

            # ---- Unit conversions ----
            cpd_kpa = cpd * 98.0665 if cpd else None
            amb_press_kpa = afpip * 0.133322 if afpip else iso_press

            # ---- Gross Heat Rate (using formula from Rules) ----
            formula_data = rule_engine.get_formula("HR_GROSS", asset_type=self.asset_type)
            if formula_data and dwatt and fqg and lhv_kjkg and dwatt != 0:
                formula_str = formula_data["formula"]
                # Evaluate the formula with current values
                context = {"FQG": fqg, "LHV": lhv_kjkg, "DWATT": dwatt}
                gross_hr = rule_engine._evaluate_formula(formula_str, context)  # We'll add this helper below.
            else:
                gross_hr = None

            # ---- Efficiency (using formula from Rules) ----
            if gross_hr and gross_hr > 0:
                eff_formula = rule_engine.get_formula("EFFICIENCY_GROSS", asset_type=self.asset_type)
                if eff_formula:
                    context = {"HR_GROSS": gross_hr}
                    efficiency = rule_engine._evaluate_formula(eff_formula["formula"], context)
                else:
                    efficiency = 3600 / gross_hr * 100  # fallback
            else:
                efficiency = None

            # ---- Pressure Ratio (using formula from Rules) ----
            pr_formula = rule_engine.get_formula("PRESSURE_RATIO", asset_type=self.asset_type)
            if pr_formula and amb_press_kpa and cpd_kpa and amb_press_kpa != 0:
                context = {"CPD": cpd_kpa, "AFPIP": amb_press_kpa}
                pr = rule_engine._evaluate_formula(pr_formula["formula"], context)
            else:
                pr = None

            # ---- Correction Factors (using curves from Rules) ----
            if apply_corrections and gross_hr is not None:
                # Evaluate C1..C9 from curves
                c1 = rule_engine.evaluate_curve("C1_Inlet_Temp", ctim, asset_type=self.asset_type) if ctim else 1.0
                # C2, C3, C6, C7 – we need to read appropriate tags
                rh = self.db.value("RH", snapshot) if hasattr(self.db, 'value') else iso_rh
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
                # C4, C5, C8, C9 default to 1.0
                c4 = c5 = c8 = c9 = 1.0
                corr_factor = c1 * c2 * c3 * c4 * c5 * c6 * c7 * c8 * c9
                corrected_hr = gross_hr * corr_factor
                corrected_eff = 3600 / corrected_hr * 100 if corrected_hr else None
            else:
                corr_factor = 1.0
                corrected_hr = gross_hr
                corrected_eff = efficiency

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

    # Helper to evaluate formula strings (to avoid exposing eval directly)
    @staticmethod
    def _evaluate_formula(formula: str, context: dict) -> float:
        # We'll use a safe eval with restricted builtins.
        # Alternatively, we could use a simple parser, but for now we trust the data.
        safe_builtins = {"abs": abs, "round": round, "min": min, "max": max, "sum": sum, "pow": pow}
        env = {"__builtins__": safe_builtins, **context}
        return float(eval(formula, env, {}))