# test_step4_tags.py
from calculations.data_engine import EngineeringData

eng = EngineeringData()
db = eng.db

snapshot = "Set 4 - Base Load"  # pick one snapshot to test

tags_to_check = ["CTIM", "AFPCS", "96EP#1/2#3", "AFPIP", "FTG", "FQG", "DWATT"]

print(f"Checking tag availability in snapshot: {snapshot}\n")
for tag in tags_to_check:
    try:
        val = db.value(tag, snapshot)
        unit = db.unit(tag)
        print(f"✅ {tag}: {val} {unit}")
    except KeyError:
        print(f"❌ {tag}: NOT FOUND in database")