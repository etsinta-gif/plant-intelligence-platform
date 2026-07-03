# calculations/fuel_engine.py

import pandas as pd
from calculations.excel_reader import load_demo_data

class FuelEngine:
    """
    Reads fuel properties from Demo_Assumptions.xlsx.
    Converts LHV from kcal/Sm³ to kJ/kg using Specific Gravity.
    Also extracts GE 9-Factor correction values (C4, C7, C8, C9, PF)
    so that corrections.py doesn't need to re-parse the file.
    """

    def __init__(self):
        self.demo_df = load_demo_data()
        self._cache = {}  # cache by snapshot name

    def get_properties(self, snapshot_name: str):
        """
        Returns fuel properties dict for a given snapshot.
        Example snapshot_name: "Set 4 - Base Load" or "PG TEST DATA"
        """
        if snapshot_name in self._cache:
            return self._cache[snapshot_name]

        # Try exact match on 'Test' column first
        row = self.demo_df[self.demo_df["Test"] == snapshot_name]

        # Fallback to PG TEST DATA if snapshot not found (e.g., if named differently)
        if row.empty:
            print(f"Warning: '{snapshot_name}' not found. Using 'PG TEST DATA' as fallback.")
            row = self.demo_df[self.demo_df["Test"] == "PG TEST DATA"]

        # Ultimate fallback: use the very first row
        if row.empty:
            row = self.demo_df.iloc[[0]]

        row = row.iloc[0]

        # --- READ VALUES USING EXACT COLUMN NAMES FROM YOUR EXCEL ---
        # (These names come from the output of test_step1.py)
        lhv_kcal_sm3 = row.get("Fuel LHV (kcal/Sm³)", 8600.0)
        sp_gr = row.get("Specific Gravity", 0.615)
        amb_temp = row.get("Ambient Temp (°C)", 25.0)
        amb_press = row.get("Ambient Pressure (mmHg)", 760.0)
        rh = row.get("Relative Humidity (%)", 60.0)
        
        # GE 9-Factor constants from the demo file
        gen_pf = row.get("Generator PF", 0.85)
        c4 = row.get("C4 Fuel Factor", 1.0)
        c7 = row.get("C7 Exhaust Factor", 1.0)
        c8 = row.get("C8 Frequency Factor", 1.0)
        c9 = row.get("C9 Misc Factor", 1.0)

        # --- CONVERSION: kcal/Sm³ -> kJ/kg ---
        # 1 kcal = 4.1868 kJ
        # Density of air at standard conditions = 1.293 kg/Sm³
        # Fuel density = specific_gravity * air_density
        density_fuel = sp_gr * 1.293  # kg/Sm³
        lhv_kjkg = (lhv_kcal_sm3 * 4.1868) / density_fuel

        # --- BUILD RESULT DICTIONARY ---
        result = {
            "lhv_kcal_sm3": float(lhv_kcal_sm3),
            "specific_gravity": float(sp_gr),
            "density_kg_sm3": density_fuel,
            "lhv_kjkg": lhv_kjkg,
            "ambient_temp_c": float(amb_temp),
            "ambient_press_mmhg": float(amb_press),
            "ambient_rh_pct": float(rh),
            "generator_pf": float(gen_pf),
            "c4_fuel_factor": float(c4),
            "c7_exhaust_factor": float(c7),
            "c8_frequency_factor": float(c8),
            "c9_misc_factor": float(c9),
        }

        self._cache[snapshot_name] = result
        return result

    # --- SHORTCUT METHODS FOR COMMON VALUES ---
    def lhv_kjkg(self, snapshot_name: str):
        return self.get_properties(snapshot_name)["lhv_kjkg"]

    def specific_gravity(self, snapshot_name: str):
        return self.get_properties(snapshot_name)["specific_gravity"]


# --- QUICK TEST (Run this file directly to verify) ---
if __name__ == "__main__":
    fe = FuelEngine()
    snapshots = ["PG TEST DATA", "Set 4 - Base Load", "Set 3 - Base Load"]
    
    print("🚀 Testing FuelEngine with your Demo_Assumptions.xlsx\n")
    for snap in snapshots:
        props = fe.get_properties(snap)
        print(f"📊 {snap}:")
        print(f"   LHV (kcal/Sm³): {props['lhv_kcal_sm3']:.1f}")
        print(f"   Specific Gravity: {props['specific_gravity']:.3f}")
        print(f"   LHV (kJ/kg): {props['lhv_kjkg']:.1f}  ← This is what GT engine uses")
        print(f"   Generator PF: {props['generator_pf']:.3f}")
        print(f"   C4, C7, C8, C9: {props['c4_fuel_factor']:.3f}, {props['c7_exhaust_factor']:.3f}, {props['c8_frequency_factor']:.3f}, {props['c9_misc_factor']:.3f}")
        print()