# Rules Management

## How Rules Work

- SMEs edit JSON files in `Rules/`.
- The `RuleEngine` loads them at runtime.
- Pages call `rule_engine.classify(metric, value, asset_type)` to get status and message.

## Adding a New Threshold

Add an entry to `thresholds.json` inside the `"rules"` object.

```json
"New Metric": {
    "asset_type": "GasTurbine",
    "unit": "°C",
    "good_low": 10.0,
    "good_high": 20.0,
    "warn_low": 5.0,
    "warn_high": 25.0,
    "critical_message": "...",
    "warning_message": "..."
}