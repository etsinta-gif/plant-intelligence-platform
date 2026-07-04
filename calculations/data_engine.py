"""
===========================================================
Engineering Data Engine
Single entry point to the engineering database.
===========================================================
"""

from calculations.excel_reader import (
    load_raw_data,
    load_demo_data
)

from calculations.plant_database import PlantDatabase


class EngineeringData:

    def __init__(self):

        # Raw engineering data
        self.raw = load_raw_data()

        # Demo / assumptions
        self.demo = load_demo_data()

        # Engineering database
        self.db = PlantDatabase(self.raw)

    # -------------------------------------------------

    def reference(self):

        return self.db.reference()

    # -------------------------------------------------

    def operating(self):

        return self.db.operating()

    # -------------------------------------------------

    def snapshots(self):

        return self.db.snapshots_list()