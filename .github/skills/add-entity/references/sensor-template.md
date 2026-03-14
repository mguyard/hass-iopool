# Sensor Entity Template

## 1. Constant (`const.py`)

```python
SENSOR_MY_FEATURE = "my_feature"
```

## 2. EntityDescription (`sensor.py` — add to `POOL_SENSORS` list)

Minimal (no device class):
```python
SensorEntityDescription(
    key=SENSOR_MY_FEATURE,
    translation_key=SENSOR_MY_FEATURE,
    icon="mdi:icon-name",
),
```

With measurement metadata:
```python
SensorEntityDescription(
    key=SENSOR_MY_FEATURE,
    translation_key=SENSOR_MY_FEATURE,
    icon="mdi:icon-name",
    device_class=SensorDeviceClass.TEMPERATURE,       # optional
    state_class=SensorStateClass.MEASUREMENT,          # optional
    suggested_display_precision=1,                     # optional
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,  # optional
),
```

Available `SensorDeviceClass` values relevant to pool monitoring:
`TEMPERATURE`, `PH` (use `None` for pH — no official HA device class), `VOLTAGE` (for ORP mV)

## 3. Value logic (`native_value` in `IopoolSensor.native_value`)

Add a `case` branch inside the existing `match key:` block:

```python
case "my_feature":
    value = pool.latest_measure.my_field if pool.latest_measure else None
```

Common data paths:
- `pool.latest_measure.temperature` — water temperature
- `pool.latest_measure.ph` — pH value
- `pool.latest_measure.orp` — ORP in mV
- `pool.advice.filtration_duration` — recommended filtration hours
- `pool.mode` — current pool mode string

## 4. Extra attributes (optional)

If the entity needs extra state attributes, override `extra_state_attributes`:

```python
@property
def extra_state_attributes(self) -> dict[str, Any]:
    """Return extra state attributes."""
    pool = self._get_pool()
    if not pool or not pool.latest_measure:
        return {}
    return {
        "measured_at": pool.latest_measure.measured_at,
        "is_valid": pool.latest_measure.is_valid,
    }
```

## 5. Translations

`en.json` — under `entity.sensor`:
```json
"my_feature": {
    "name": "My Feature"
}
```

`fr.json` — under `entity.sensor`:
```json
"my_feature": {
    "name": "Ma fonctionnalité"
}
```

## 6. `entities.mdx` table row

```mdx
| My Feature (sensor) | Description of the measurement | Always |
```
