# test_step6_gt.py
from calculations.data_engine import EngineeringData
from calculations.gt_performance import GTPerformance

eng = EngineeringData()
db = eng.db
gt = GTPerformance(db)

snapshots = ["PG TEST DATA", "Set 4 - Base Load", "Set 3 - Base Load", "Set 2 - Base Load", "Set 1 - Base Load"]

print("GT Performance Results\n" + "="*50)
for snap in snapshots:
    result = gt.calculate(snap)
    if "error" in result:
        print(f"❌ {snap}: Error - {result['error']}")
    else:
        print(f"\n{snap}:")
        print(f"  Gross Output: {result['gross_output_mw']:.2f} MW")
        print(f"  Fuel Flow: {result['fuel_flow_kg_per_s']:.3f} kg/s")
        print(f"  LHV: {result['lhv_kjkg']:.1f} kJ/kg")
        print(f"  Gross HR: {result['gross_heat_rate_kj_per_kwh']:.1f} kJ/kWh")
        print(f"  Corrected HR: {result['corrected_heat_rate_kj_per_kwh']:.1f} kJ/kWh")
        print(f"  Efficiency (Gross): {result['thermal_efficiency_percent']:.2f} %")
        print(f"  Efficiency (Corrected): {result['corrected_efficiency_percent']:.2f} %")
        print(f"  Pressure Ratio: {result['pressure_ratio']:.2f}")
        print(f"  Correction Factor: {result['correction_factor_product']:.6f}")