# Binary Sensor Entity Template

## 1. Constant (`const.py`)

```python
SENSOR_MY_STATUS = "my_status"
```

## 2. EntityDescription (`binary_sensor.py` — add to `POOL_BINARY_SENSORS` list)

```python
BinarySensorEntityDescription(
    key=SENSOR_MY_STATUS,
    translation_key=SENSOR_MY_STATUS,
    icon="mdi:icon-name",
    device_class=BinarySensorDeviceClass.PROBLEM,  # optional
),
```

Common `BinarySensorDeviceClass` values:
- `PROBLEM` — something requires attention (e.g., action required)
- `RUNNING` — a process is active (e.g., filtration pump)
- `CONNECTIVITY` — connection state

## 3. Value logic (`is_on` in `IopoolBinarySensor`)

Override the `is_on` property. Add a `case` branch in the `match key:` block, or implement directly:

```python
@property
def is_on(self) -> bool | None:
    """Return true if the binary sensor is on."""
    pool = self._get_pool()
    if not pool:
        return None

    match self.entity_description.key:
        case "my_status":
            return bool(pool.some_field)
        case _:
            return None
```

## 4. Filtration-aware sensors

If the sensor depends on the `Filtration` object (like the existing `filtration` sensor), access it via:

```python
self._filtration: Filtration = coordinator.config_entry.runtime_data.filtration
```

Then use `self._filtration.is_active` or similar in `is_on`.

## 5. Extra attributes (optional)

```python
@property
def extra_state_attributes(self) -> dict[str, Any]:
    """Return extra state attributes."""
    pool = self._get_pool()
    if not pool:
        return {}
    return {
        "some_field": pool.some_field,
    }
```

## 6. Translations

`en.json` — under `entity.binary_sensor`:
```json
"my_status": {
    "name": "My Status"
}
```

`fr.json` — under `entity.binary_sensor`:
```json
"my_status": {
    "name": "Mon statut"
}
```

## 7. `entities.mdx` table row

```mdx
| My Status (binary sensor) | Description of what triggers the on state | Always |
```
