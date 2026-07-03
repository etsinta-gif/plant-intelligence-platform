# test_step2.py
from calculations.data_engine import EngineeringData

eng = EngineeringData()
db = eng.db

print("Snapshots found:", db.snapshots_list())
print("\nFirst 10 tags:", db.tags()[:10])

# Test reading a value for the first snapshot
snap = db.snapshots_list()[0]
tag = "DWATT"
val = db.value(tag, snap)
unit = db.unit(tag)
print(f"\n✅ Value of '{tag}' in snapshot '{snap}': {val} {unit}")

# Test reading another tag
tag2 = "FQG"
val2 = db.value(tag2, snap)
unit2 = db.unit(tag2)
print(f"✅ Value of '{tag2}' in snapshot '{snap}': {val2} {unit2}")

# Test reading ambient temperature
tag3 = "CTIM"
val3 = db.value(tag3, snap)
unit3 = db.unit(tag3)
print(f"✅ Value of '{tag3}' in snapshot '{snap}': {val3} {unit3}")