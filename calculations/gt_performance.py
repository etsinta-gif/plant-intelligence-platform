# calculations/gt_performance.py

import math
from calculations.fuel_engine import FuelEngine
from calculations.corrections import GE9FACorrectionEngine

class GTPerformance:
    """
    Main Gas Turbine Performance Calculator for GE 9FA.
    Integrates fuel properties, raw measurements, and GE 9-Factor corrections.
    """

    def __init__(self, db):
        self.db = db
        self.fuel = FuelEngine()
        self.corrections = GE9FACorrectionEngine(db=db)

    def calculate(self, snapshot: str, apply_corrections: bool = True):
        """
        Compute performance for a given snapshot.
        If apply_corrections=True, corrected HR and efficiency are calculated.
        Returns a dictionary with all key metrics.
        """
        try:
            # ---- 1. Read raw data ----
            dwatt = self.db.value("DWATT", snapshot)          # MW
            fqg = self.db.value("FQG", snapshot)              # kg/s (fuel mass flow)
            ctim = self.db.value("CTIM", snapshot)            # °C (compressor inlet temp)
            cpd = self.db.value("CPD", snapshot)              # kg/cm² (compressor discharge)
            afpip = self.db.value("AFPIP", snapshot)          # mmHg (ambient pressure)

            # ---- 2. Fuel properties ----
            lhv_kjkg = self.fuel.lhv_kjkg(snapshot)

            # ---- 3. Unit conversions ----
            cpd_kpa = cpd * 98.0665 if cpd is not None else None
            amb_press_kpa = afpip * 0.133322 if afpip is not None else 101.325

            # ---- 4. Core calculations ----
            if dwatt and fqg and lhv_kjkg and dwatt > 0:
                gross_hr = (fqg * 3.6 * lhv_kjkg) / dwatt
            else:
                gross_hr = None

            if gross_hr and gross_hr > 0:
                efficiency = 3600 / gross_hr * 100.0
            else:
                efficiency = None

            if amb_press_kpa and cpd_kpa and amb_press_kpa > 0:
                pr = cpd_kpa / amb_press_kpa
            else:
                pr = None

            # ---- 5. Apply corrections ----
            if apply_corrections and gross_hr is not None:
                factors = self.corrections.get_factors(snapshot)
                corr_factor = factors["hr_correction_factor"]
                corrected_hr = gross_hr * corr_factor
                corrected_eff = 3600 / corrected_hr * 100 if corrected_hr else None
            else:
                corr_factor = 1.0
                corrected_hr = gross_hr
                corrected_eff = efficiency

            # ---- 6. Build result ----
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

    # ---- NEW: Compare to baseline (PG Test) ----
    def compare(self, snapshot: str, baseline_snapshot: str = "PG TEST DATA"):
        """
        Compare performance of a snapshot against a baseline (default: PG TEST DATA).
        Returns a dict with selected data, baseline data, and deltas.
        """
        # Calculate both snapshots
        snap_result = self.calculate(snapshot)
        base_result = self.calculate(baseline_snapshot)

        if "error" in snap_result:
            return {"error": f"Error calculating {snapshot}: {snap_result['error']}"}
        if "error" in base_result:
            return {"error": f"Error calculating baseline {baseline_snapshot}: {base_result['error']}"}

        # Safely compute deltas (handle None values)
        def safe_delta(val1, val2):
            if val1 is None or val2 is None:
                return None
            return val1 - val2

        def safe_pct(val1, val2):
            if val1 is None or val2 is None or val2 == 0:
                return None
            return ((val1 - val2) / abs(val2)) * 100

        # Key metrics to compare
        metrics = [
            "gross_output_mw",
            "gross_heat_rate_kj_per_kwh",
            "thermal_efficiency_percent",
            "corrected_heat_rate_kj_per_kwh",
            "corrected_efficiency_percent",
            "correction_factor_product",
            "pressure_ratio",
        ]

        deltas = {}
        pct_changes = {}
        for m in metrics:
            val1 = snap_result.get(m)
            val2 = base_result.get(m)
            deltas[m] = safe_delta(val1, val2)
            pct_changes[m] = safe_pct(val1, val2)

        return {
            "snapshot": snapshot,
            "baseline": baseline_snapshot,
            "selected": snap_result,
            "baseline_data": base_result,
            "deltas": deltas,
            "pct_changes": pct_changes,
        }