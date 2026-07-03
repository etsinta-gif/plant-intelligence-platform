# calculations/corrections.py

import math
import pandas as pd
from calculations.fuel_engine import FuelEngine
from calculations.excel_reader import load_demo_data

class GE9FACorrectionEngine:
    """
    Implements the GE 9FA 9‑Factor Correction Method per the official 9F.03 sample.
    All slopes are derived from the PDF sample (Page 1 table).
    
    The engine reads raw tag data from PlantDatabase and fuel/demo data from
    Demo_Assumptions.xlsx to compute each C factor.
    """
    
    # ---- ISO REFERENCE CONDITIONS (from PDF sample) ----
    ISO_TEMP = 15.0          # °C (reference for C1)
    ISO_RH = 60.0            # % (reference for C2)
    ISO_PRESS = 1013.25      # mbar (reference for C3)
    ISO_FUEL_TEMP = 15.0     # °C (reference for C8)
    ISO_PF = 0.85            # reference for C5 (typical GE)
    ISO_SPEED = 3000.0       # RPM (reference for C4 — not used in our code since speed is always near 3000)
    
    # ---- EXHAUST LOSS REFERENCE (from PDF) ----
    REF_EXHAUST_LOSS = 279.91  # mmwc (reference value from PDF)
    
    # ---- SLOPES DERIVED FROM PDF SAMPLE POINT ----
    # Sample point: Ambient 30.2°C, C1=1.0037 => slope = 0.0037/15.2 = 0.0002434
    # Sample point: RH 80.4%, C2=0.9985 => slope = -0.0015/20.4 = -0.0000735
    # Sample point: Press 1002.258 mbar, C3=0.9997 => slope = -0.0003/-10.992 = 0.0000273
    # Sample point: PF 0.9987, C5=1.0023 => slope = 0.0023/0.1487 = 0.015467
    # Sample point: Inlet loss 104.18 mmwc, C6=0.9994 => slope = -0.0006/104.18 = -0.00000576
    # Sample point: Exhaust loss diff 61.35 mmwc, C7=1.0037 => slope = 0.0037/61.35 = 0.0000603
    # Sample point: Fuel temp 182°C, C8=0.9998 => slope = -0.0002/167 = -0.0000012

    def __init__(self, db=None):
        self.db = db
        self.fuel = FuelEngine()
        self.demo_df = load_demo_data()

    def get_factors(self, snapshot: str) -> dict:
        """
        Returns all 9 correction factors (C1..C9) for the given snapshot.
        Also returns the total HR correction factor (product of all C factors).
        """
        
        # ---- STEP 1: Get fuel/demo row for this snapshot ----
        demo_row = self._get_demo_row(snapshot)
        fuel_props = self.fuel.get_properties(snapshot)
        
        # ---- STEP 2: Read values from the demo file ----
        ambient_temp_demo = self._safe_float(demo_row, "Ambient Temp (°C)", default=25.0)
        rh_demo = self._safe_float(demo_row, "Relative Humidity (%)", default=60.0)
        ambient_press_demo_mmhg = self._safe_float(demo_row, "Ambient Pressure (mmHg)", default=760.0)
        ambient_press_demo_mbar = ambient_press_demo_mmhg * 1.33322  # mmHg → mbar
        fuel_temp_demo = self._safe_float(demo_row, "Fuel Gas Temp (°C)", default=25.0)
        pf_demo = self._safe_float(demo_row, "Generator PF", default=0.85)
        
        # GE 9-Factor constants (C4, C7, C8, C9 from demo)
        c4_from_demo = self._safe_float(demo_row, "C4 Fuel Factor", default=1.0)
        c7_from_demo = self._safe_float(demo_row, "C7 Exhaust Factor", default=1.0)
        c8_from_demo = self._safe_float(demo_row, "C8 Frequency Factor", default=1.0)
        c9_from_demo = self._safe_float(demo_row, "C9 Misc Factor", default=1.0)
        
        # ---- STEP 3: Read raw data tags (if db is available) ----
        # These override the demo values (actual measurements > assumptions)
        if self.db is not None:
            try:
                # Compressor Inlet Temp (CTIM) - this is our ambient temp
                ambient_temp = self.db.value("CTIM", snapshot)
            except:
                ambient_temp = ambient_temp_demo
                
            try:
                # Ambient Pressure (AFPIP) in mmHg
                afpip = self.db.value("AFPIP", snapshot)
                ambient_press_mbar = afpip * 1.33322  # mmHg → mbar
            except:
                ambient_press_mbar = ambient_press_demo_mbar
                
            try:
                # Fuel Gas Temp (FTG)
                fuel_temp = self.db.value("FTG", snapshot)
            except:
                fuel_temp = fuel_temp_demo
                
            try:
                # Inlet Pressure Loss (AFPCS) in mmwc
                inlet_loss = self.db.value("AFPCS", snapshot)
            except:
                inlet_loss = 0.0
                
            try:
                # Exhaust Pressure Loss (96EP#1/2#3) in mmwc
                exhaust_loss = self.db.value("96EP#1/2#3", snapshot)
            except:
                exhaust_loss = self.REF_EXHAUST_LOSS  # fallback to reference
                
            # Generator PF is from demo (no raw tag for this)
            gen_pf = pf_demo
            
        else:
            # No db available — use demo values
            ambient_temp = ambient_temp_demo
            ambient_press_mbar = ambient_press_demo_mbar
            fuel_temp = fuel_temp_demo
            inlet_loss = 0.0
            exhaust_loss = self.REF_EXHAUST_LOSS
            gen_pf = pf_demo
        
        # RH is not in raw data — always use demo
        rh = rh_demo
        
        # ---- STEP 4: Calculate each C factor using PDF slopes ----
        
        # C1: Inlet Temperature Correction
        # PDF slope: at 30.2°C, C1=1.0037 vs ISO 15°C
        c1 = 1.0 + 0.0002434 * (ambient_temp - self.ISO_TEMP)
        
        # C2: Inlet Relative Humidity Correction
        # PDF slope: at 80.4%, C2=0.9985 vs ISO 60%
        c2 = 1.0 - 0.0000735 * (rh - self.ISO_RH)
        
        # C3: Ambient Pressure Correction
        # PDF slope: at 1002.258 mbar, C3=0.9997 vs ISO 1013.25 mbar
        c3 = 1.0 + 0.0000273 * (ambient_press_mbar - self.ISO_PRESS)
        
        # C4: Fuel Composition Factor — read from demo
        c4 = c4_from_demo
        
        # C5: Generator Power Factor Correction
        # PDF slope: at PF=0.9987, C5=1.0023 vs ISO 0.85
        c5 = 1.0 + 0.015467 * (gen_pf - self.ISO_PF)
        
        # C6: Inlet Pressure Loss Correction
        # PDF slope: at 104.18 mmwc, C6=0.9994
        c6 = 1.0 - 0.00000576 * inlet_loss
        
        # C7: Exhaust Pressure Loss Correction
        # PDF slope: measured=218.56, reference=279.91, C7=1.0037
        # Formula: C7 = 1 + slope * (REFERENCE - MEASURED)
        # If measured is lower than reference, C7 > 1 (benefit)
        c7 = 1.0 + 0.0000603 * (self.REF_EXHAUST_LOSS - exhaust_loss)
        
        # C8: Fuel Temperature Correction
        # PDF slope: at 182°C, C8=0.9998 vs ISO 15°C
        c8 = 1.0 - 0.0000012 * (fuel_temp - self.ISO_FUEL_TEMP)
        
        # C9: Miscellaneous Factor — read from demo
        c9 = c9_from_demo
        
        # ---- STEP 5: Total HR Correction Factor ----
        # Product of all 9 factors (as per GE method)
        hr_correction = c1 * c2 * c3 * c4 * c5 * c6 * c7 * c8 * c9
        
        # ---- STEP 6: Return results ----
        return {
            "C1_inlet_temp": c1,
            "C2_inlet_rh": c2,
            "C3_ambient_press": c3,
            "C4_fuel_composition": c4,
            "C5_generator_pf": c5,
            "C6_inlet_loss": c6,
            "C7_exhaust_loss": c7,
            "C8_fuel_temp": c8,
            "C9_misc": c9,
            "hr_correction_factor": hr_correction,
            # Include raw values for dashboard display
            "ambient_temp_c": ambient_temp,
            "rh_percent": rh,
            "ambient_press_mbar": ambient_press_mbar,
            "inlet_loss_mmwc": inlet_loss,
            "exhaust_loss_mmwc": exhaust_loss,
            "fuel_temp_c": fuel_temp,
            "generator_pf": gen_pf,
        }

    # ----- HELPERS -----
    
    def _get_demo_row(self, snapshot):
        """Find the row in Demo_Assumptions matching the snapshot name."""
        row = self.demo_df[self.demo_df["Test"] == snapshot]
        if row.empty:
            # Fallback to PG TEST DATA
            print(f"Warning: '{snapshot}' not found in Demo_Assumptions. Using 'PG TEST DATA'.")
            row = self.demo_df[self.demo_df["Test"] == "PG TEST DATA"]
        if row.empty:
            row = self.demo_df.iloc[[0]]
        return row.iloc[0]
    
    def _safe_float(self, row, col_pattern, default=1.0):
        """Extract a float from a column based on partial name match."""
        # Map column names to indices
        col_map = {str(col).strip(): idx for idx, col in enumerate(self.demo_df.columns)}
        
        for col_name, idx in col_map.items():
            if col_pattern.lower() in col_name.lower():
                val = row.iloc[idx]
                if pd.isna(val):
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default
        return default


# --- QUICK TEST (Run this file directly to verify) ---
if __name__ == "__main__":
    from calculations.data_engine import EngineeringData
    
    print("🚀 Testing GE9FACorrectionEngine with your data\n")
    
    eng = EngineeringData()
    db = eng.db
    corr = GE9FACorrectionEngine(db=db)
    
    snapshots = ["PG TEST DATA", "Set 4 - Base Load", "Set 3 - Base Load", "Set 2 - Base Load", "Set 1 - Base Load"]
    
    for snap in snapshots:
        factors = corr.get_factors(snap)
        print(f"📊 {snap}:")
        print(f"   C1 (Inlet Temp):   {factors['C1_inlet_temp']:.6f}")
        print(f"   C2 (RH):           {factors['C2_inlet_rh']:.6f}")
        print(f"   C3 (Pressure):     {factors['C3_ambient_press']:.6f}")
        print(f"   C4 (Fuel Comp):    {factors['C4_fuel_composition']:.6f}")
        print(f"   C5 (Generator PF): {factors['C5_generator_pf']:.6f}")
        print(f"   C6 (Inlet Loss):   {factors['C6_inlet_loss']:.6f}")
        print(f"   C7 (Exhaust Loss): {factors['C7_exhaust_loss']:.6f}")
        print(f"   C8 (Fuel Temp):    {factors['C8_fuel_temp']:.6f}")
        print(f"   C9 (Misc):         {factors['C9_misc']:.6f}")
        print(f"   ▶ Total HR Correction: {factors['hr_correction_factor']:.6f}")
        print()