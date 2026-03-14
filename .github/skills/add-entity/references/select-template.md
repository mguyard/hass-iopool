# Select Entity Template

## 1. Constant (`const.py`)

```python
SENSOR_MY_SELECTOR = "my_selector"
```

## 2. EntityDescription (`select.py` — add to `POOL_SELECTS` list)

```python
SelectEntityDescription(
    key=SENSOR_MY_SELECTOR,
    translation_key=SENSOR_MY_SELECTOR,
    icon="mdi:icon-name",
),
```

## 3. Options list

Define the available options as a constant (list of string values):

```python
MY_SELECTOR_OPTIONS = ["option_a", "option_b", "option_c"]
```

Pass options to the entity in `async_setup_entry` or set `_attr_options` in `__init__`:

```python
self._attr_options = MY_SELECTOR_OPTIONS
```

## 4. Current value logic

Override `current_option` to return the current selection:

```python
@property
def current_option(self) -> str | None:
    """Return the current selected option."""
    pool = self._get_pool()
    if not pool:
        return None
    return pool.some_field  # must match one of the options strings
```

## 5. Selection handler

Override `async_select_option` to act on the user's choice:

```python
async def async_select_option(self, option: str) -> None:
    """Handle the user selecting an option."""
    # e.g., call coordinator or filtration to apply the change
    await self.coordinator.async_request_refresh()
```

For boost-style selectors that trigger an API call, fire a HA event:

```python
self.hass.bus.async_fire(
    f"{DOMAIN}_{EVENT_MY_ACTION}",
    {"pool_id": self._pool_id, "option": option},
)
```

## 6. Translations

`en.json` — under `entity.select`:
```json
"my_selector": {
    "name": "My Selector",
    "state": {
        "option_a": "Option A Label",
        "option_b": "Option B Label",
        "option_c": "Option C Label"
    }
}
```

`fr.json` — under `entity.select`:
```json
"my_selector": {
    "name": "Mon sélecteur",
    "state": {
        "option_a": "Libellé Option A",
        "option_b": "Libellé Option B",
        "option_c": "Libellé Option C"
    }
}
```

## 7. `entities.mdx` table row

```mdx
| My Selector (select) | Description of what the selector controls | Always |
```
