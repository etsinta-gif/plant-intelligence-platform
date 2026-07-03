# test_step4_corrections.py
from calculations.data_engine import EngineeringData
from calculations.corrections import GE9FACorrectionEngine

eng = EngineeringData()
db = eng.db
corr = GE9FACorrectionEngine(db=db)

snapshot = "Set 4 - Base Load"
factors = corr.get_factors(snapshot)

print(f"\n📊 Correction Factors for: {snapshot}\n")
for key in ["C1_inlet_temp", "C2_inlet_rh", "C3_ambient_press", "C4_fuel_composition", 
            "C5_generator_pf", "C6_inlet_loss", "C7_exhaust_loss", "C8_fuel_temp", "C9_misc"]:
    print(f"  {key}: {factors[key]:.6f}")
print(f"\n  ▶ Total HR Correction: {factors['hr_correction_factor']:.6f}")