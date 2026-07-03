"""
===========================================================
Plant Database
Builds an engineering database from the raw snapshot table.
===========================================================
"""


class PlantDatabase:

    def __init__(self, raw_dataframe):

        self.raw = raw_dataframe

        self.parameters = {}

        self.snapshots = []

        self.reference_snapshot = None

        self._build()

    # -----------------------------------------------------

    def _build(self):

        fixed_columns = ["Parameter", "Tag", "Unit"]

        self.snapshots = [

            c for c in self.raw.columns

            if c not in fixed_columns

        ]

        if len(self.snapshots) == 0:

            raise Exception("No snapshots found.")

        # First snapshot is always PG Test Reference

        self.reference_snapshot = self.snapshots[0]

        # ------------------------------------------

        for _, row in self.raw.iterrows():

            tag = str(row["Tag"]).strip()

            if tag == "" or tag.lower() == "nan":

                continue

            values = {}

            for snap in self.snapshots:

                values[snap] = row[snap]

            self.parameters[tag] = {

                "parameter": row["Parameter"],

                "tag": tag,

                "unit": row["Unit"],

                "values": values

            }

    # =====================================================
    # Public API
    # =====================================================

    def value(self, tag, snapshot):

        return self.parameters[tag]["values"][snapshot]

    # -----------------------------------------------------

    def unit(self, tag):

        return self.parameters[tag]["unit"]

    # -----------------------------------------------------

    def parameter(self, tag):

        return self.parameters[tag]["parameter"]

    # -----------------------------------------------------

    def tags(self):

        return sorted(self.parameters.keys())

    # -----------------------------------------------------

    def snapshots_list(self):

        return self.snapshots

    # -----------------------------------------------------

    def reference(self):

        return self.reference_snapshot

    # -----------------------------------------------------

    def operating(self):

        return self.snapshots[1:]

    # -----------------------------------------------------

    def exists(self, tag):

        return tag in self.parameters

    # -----------------------------------------------------

    def record(self, tag):

        return self.parameters[tag]