---
description: "Use when writing, running, or debugging tests for the iopool integration. Covers test environment setup, fixture usage, async patterns, and coverage expectations."
applyTo: "custom_components/iopool/tests/**/*.py"
---

# Testing Guidelines

## Environment

Tests **require** a Home Assistant dev container. Before running tests, detect the execution environment automatically.

### Step 1 — Detect if running inside the devcontainer

Check for the presence of the `/workspaces` directory:

```bash
test -d /workspaces && echo "inside devcontainer" || echo "outside devcontainer"
```

**If inside the devcontainer**, run pytest directly:

```bash
cd /workspaces/home-assistant-dev/config
PYTHONPATH=/workspaces/home-assistant-dev python -m pytest custom_components/iopool/tests/

# Or use the shortcut scripts (auto-configure PYTHONPATH)
./custom_components/iopool/tests/run_tests.sh
./custom_components/iopool/run_tests.sh
```

### Step 2 — If NOT inside the devcontainer

List running Docker containers and present the result:

```bash
docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Names}}"
```

- If containers are listed, identify the HA devcontainer and use its ID in Step 3.
- If no container is running, inform the developer: *"No running container found. Please start the HA devcontainer first."*

> ⚠️ The container ID changes every time the devcontainer is restarted. Always retrieve it fresh via `docker ps`.

### Step 3 — Run tests via Docker exec

```bash
docker exec -w /workspaces/home-assistant-dev/config \
  <CONTAINER_ID> \
  bash -c "PYTHONPATH=/workspaces/home-assistant-dev python -m pytest custom_components/iopool/tests/ -v --tb=short"
```

Replace `<CONTAINER_ID>` with the value obtained from `docker ps`.

To run with coverage:

```bash
docker exec -w /workspaces/home-assistant-dev/config \
  <CONTAINER_ID> \
  bash -c "PYTHONPATH=/workspaces/home-assistant-dev python -m pytest custom_components/iopool/tests/ --cov=. --cov-report=term-missing"
```

> ⚠️ **Never create `pytest.ini`** — it breaks async test discovery. All pytest config lives in `pyproject.toml` (`asyncio_mode = "auto"`).

## File Naming

Each integration module has a matching test file:

| Module | Test file |
|--------|-----------|
| `sensor.py` | `test_sensor.py` |
| `binary_sensor.py` | `test_binary_sensor.py` |
| `select.py` | `test_select.py` |
| `filtration.py` | `test_filtration.py` |
| `config_flow.py` | `test_config_flow.py` |
| `coordinator.py` | `test_coordinator.py` |
| `__init__.py` | `test_init.py` |
| `models.py` | `test_models.py` |
| `api_models.py` | `test_api_models.py` |
| `diagnostics.py` | `test_diagnostics.py` |

## Test Structure

Group tests by class. Use `class TestIopool{Module}:` naming:

```python
class TestIopoolSensorPlatform:
    """Test iopool sensor platform."""

    async def test_async_setup_entry(self, hass, mock_config_entry) -> None:
        """Test sensor platform setup."""
        ...
```

- Tests are **async by default** — `asyncio_mode = "auto"` is active, no `@pytest.mark.asyncio` needed.
- Group related tests under one class.
- Name tests clearly: `test_{what}_{condition}` (e.g., `test_temperature_sensor_unavailable`).

## Fixtures

Use fixtures from `conftest.py` and `conftest_hass.py` — do not recreate them:

```python
# Common fixtures available
hass              # MagicMock(spec=HomeAssistant)
mock_config_entry # ConfigEntry mock with runtime_data pre-populated
coordinator       # IopoolDataUpdateCoordinator mock
```

When mocking Home Assistant internals, use `MagicMock(spec=ClassName)` to get proper attribute validation:

```python
from unittest.mock import MagicMock, AsyncMock, patch

hass_mock = MagicMock(spec=HomeAssistant)
hass_mock.async_add_executor_job = AsyncMock()
```

## What to Test Per Entity

For each new entity, cover these scenarios:

1. **Setup** — entity is created with the correct `unique_id` and `name`
2. **Happy path** — `native_value` / `is_on` returns correct data from coordinator
3. **Extra attributes** — `extra_state_attributes` contains expected keys/values
4. **Unavailable state** — entity handles `None` / missing coordinator data gracefully
5. **Restore state** — if entity uses `RestoreEntity`, test last-known state recovery

## Coverage Targets

| Module | Current | Target |
|--------|---------|--------|
| `__init__.py` | 100% | ≥ 100% |
| `coordinator.py` | 100% | ≥ 100% |
| `sensor.py` | 97% | ≥ 95% |
| `binary_sensor.py` | 95% | ≥ 95% |
| `filtration.py` | 51% | improve |
| All others | — | ≥ 70% |

See the **Environment** section above for the appropriate coverage command depending on whether you are inside or outside the devcontainer.
