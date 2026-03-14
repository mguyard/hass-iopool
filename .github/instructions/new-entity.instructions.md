---
description: "Use when adding, removing, or modifying a Home Assistant entity in the iopool integration. Covers sensor, binary_sensor, and select platforms, constants, translations, documentation, and test checklist."
---

# New Entity Checklist

Follow every step below whenever you add or remove an entity from the integration.

## 1. Add the constant in `const.py`

```python
# ALL_CAPS constant name, snake_case string value
SENSOR_MY_FEATURE = "my_feature"
```

The string value becomes the entity's `unique_id` suffix and the translation key.

## 2. Add the entity description in the correct platform file

Choose the file that matches the entity type:

| Type | File | Description class |
|------|------|-------------------|
| Sensor | `sensor.py` | `SensorEntityDescription` |
| Binary sensor | `binary_sensor.py` | `BinarySensorEntityDescription` |
| Select | `select.py` | `SelectEntityDescription` |

**Sensor example:**
```python
SensorEntityDescription(
    key=SENSOR_MY_FEATURE,           # constant from const.py
    translation_key=SENSOR_MY_FEATURE,  # same as key — always
    icon="mdi:icon-name",            # MDI icon — required
    device_class=SensorDeviceClass.X,   # optional, use HA device class
    state_class=SensorStateClass.X,     # optional
    native_unit_of_measurement=...,     # optional
),
```

`translation_key` must always match `key`.

## 3. Add translation keys in both `translations/en.json` and `translations/fr.json`

The key path is `entity.{platform}.{key_name}.name`.

**en.json:**
```json
{
  "entity": {
    "sensor": {
      "my_feature": { "name": "My Feature" }
    }
  }
}
```

**fr.json** — provide the French translation:
```json
{
  "entity": {
    "sensor": {
      "my_feature": { "name": "Ma Fonctionnalité" }
    }
  }
}
```

If the entity has `state` options (e.g., select), add them under `state`:
```json
"my_feature": {
  "name": "My Feature",
  "state": {
    "option_key": "Displayed Label"
  }
}
```

## 4. Update `docs/integration/entities.mdx`

Add a row to the entities table:
```mdx
| My Feature (sensor) | Description of what it measures | Always |
```

- Column 1: `Name (type)` — must match the entity name from translations
- Column 2: Short description
- Column 3: Availability condition (`Always`, `When filtration active`, etc.)

## 5. Write or update tests

- Add tests in the matching `tests/test_{platform}.py` file.
- Cover: entity setup, `native_value` / `is_on`, extra state attributes, unavailable state.
- Use existing fixtures from `conftest.py` and `conftest_hass.py`.
- Follow the `class TestIopoolXxxPlatform:` naming pattern.

## 6. Verify platform loading order

`PLATFORMS` in `__init__.py` **must** remain:
```python
PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.BINARY_SENSOR]
```
Do not change this order — `binary_sensor` depends on `sensor` being loaded first.
