# test_step3.py
from calculations.fuel_engine import FuelEngine

fe = FuelEngine()
snapshots = ["PG TEST DATA", "Set 4 - Base Load", "Set 3 - Base Load", "Set 2 - Base Load", "Set 1 - Base Load"]

print("Fuel properties for each snapshot:\n")
for snap in snapshots:
    props = fe.get_properties(snap)
    print(f"{snap}:")
    print(f"  LHV (kcal/Sm³): {props['lhv_kcal_sm3']:.1f}")
    print(f"  Specific Gravity: {props['specific_gravity']:.3f}")
    print(f"  LHV (kJ/kg): {props['lhv_kjkg']:.1f}")
    print()