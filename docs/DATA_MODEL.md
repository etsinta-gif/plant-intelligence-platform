# Data Model

## Enterprise Hierarchy

Company → Plant → Unit → Asset → Subsystem → Equipment → Instrument → Tag

## Rules Storage

All engineering rules are stored as JSON in `Rules/`:

- `thresholds.json`: health thresholds
- `formulas.json`: calculation formulas
- `curves.json`: OEM correction curves
- `constants.json`: global constants (ISO conditions, conversion factors)

## Tag Data

Excel files in `Data/` store raw measurements and snapshot data.