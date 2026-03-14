---
name: add-entity
description: 'Use when adding a new Home Assistant entity to the iopool integration. Guides through the full workflow: constant, entity description, data mapping, translations (en + fr), entities.mdx documentation, and tests. Use for sensor, binary_sensor, or select platform entities.'
argument-hint: 'Describe the entity: name, type (sensor/binary_sensor/select), what data it exposes, and where the data comes from in the API response.'
---

# Add Entity Workflow

Guides the full end-to-end process for adding a new entity to the iopool integration.

## When to Use

- "Add a new sensor for X"
- "Create a binary sensor that shows Y"
- "Add a select entity to control Z"
- Any request to expose new pool data in Home Assistant

## Step-by-Step Procedure

### Step 1 — Clarify the entity

Before writing any code, confirm:
1. **Platform**: `sensor`, `binary_sensor`, or `select`?
2. **Data source**: Which field in `IopoolAPIResponse` / `api_models.py` holds the value?
3. **Display name** (English) and **French translation**
4. **Availability**: Is data always present, or only under certain conditions?

### Step 2 — Add the constant in `const.py`

```python
SENSOR_MY_FEATURE = "my_feature"   # ALL_CAPS name, snake_case value
```

The value becomes the `unique_id` suffix, `translation_key`, and `entity_id` suffix.

### Step 3 — Add the entity description

Choose the template for the correct platform:
- Sensor → [sensor-template.md](./references/sensor-template.md)
- Binary sensor → [binary-sensor-template.md](./references/binary-sensor-template.md)
- Select → [select-template.md](./references/select-template.md)

Add the description to the matching list constant at the top of the platform file.

### Step 4 — Implement the value logic

In the `native_value` property (sensor) or `is_on` property (binary_sensor), add a `case` branch:

```python
case "my_feature":
    value = pool.some_object.some_field if pool.some_object else None
```

For `select`, implement `async_select_option` to handle the user's selection.

### Step 5 — Update translations

Add to **both** `translations/en.json` and `translations/fr.json` under `entity.{platform}`:

```json
"my_feature": {
    "name": "My Feature Display Name"
}
```

For select entities with fixed options, also add `state` keys:
```json
"my_feature": {
    "name": "My Feature",
    "state": {
        "option_key": "Displayed Label"
    }
}
```

### Step 6 — Update `docs/integration/entities.mdx`

Add a row to the entities table:

```mdx
| My Feature (sensor) | What this entity measures or represents | Always |
```

Columns: `Name (type)` | Description | Availability

### Step 7 — Write tests

In `tests/test_{platform}.py`, add tests covering:
1. Entity is created with correct `unique_id` and `entity_id`
2. `native_value` / `is_on` returns the correct value from coordinator data
3. `extra_state_attributes` contains expected keys (if applicable)
4. Entity returns `None` / unavailable when data is missing

### Step 8 — Verify platform loading order

`PLATFORMS` in `__init__.py` must stay:
```python
PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.BINARY_SENSOR]
```
Do not reorder — `binary_sensor` depends on `sensor` being initialized first.

## Completion Checklist

- [ ] Constant added in `const.py`
- [ ] EntityDescription added to platform list
- [ ] Value logic implemented in `native_value` / `is_on` / `async_select_option`
- [ ] `en.json` updated
- [ ] `fr.json` updated
- [ ] `docs/integration/entities.mdx` updated
- [ ] Tests written in `tests/test_{platform}.py`
- [ ] `PLATFORMS` order unchanged
