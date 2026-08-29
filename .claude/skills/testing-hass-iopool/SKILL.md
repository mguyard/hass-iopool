---
name: testing-hass-iopool
description: Project-specific test setup for hass-iopool — directory structure, test tiers, running pytest in any environment where Home Assistant is importable, shared fixtures, and the ruff gate.
---

# Testing — hass-iopool Project Setup

Use this skill for any task that requires running, writing, or understanding tests in the `custom_components/iopool/` codebase.

For generic testing principles (behavior-based, determinism, unit vs integration strategy), see `../testing-qa/SKILL.md`.

---

## 1. Directory Structure

Tests live **inside** the integration folder, so that a Home Assistant instance mounting only `custom_components/iopool/` still sees them:

```
custom_components/iopool/
├── pyproject.toml       # pytest config (asyncio_mode=auto)
└── tests/
    ├── __init__.py      # Empty, marks as package
    ├── conftest.py      # Shared fixtures
    ├── conftest_hass.py # HA-specific fixtures
    ├── test_api_models.py
    ├── test_binary_sensor.py
    ├── test_config_flow.py
    ├── test_coordinator.py
    ├── test_diagnostics.py
    ├── test_filtration.py
    ├── test_init.py
    ├── test_models.py
    ├── test_select.py
    └── test_sensor.py
```

---

## 2. Test Tiers

| Tier | Scope | HA dependency | Run where |
|------|-------|--------------|-----------|
| Tier 1 | Pure constants (`const.py` via `importlib`) | None | Anywhere |
| Tier 2 | Files that import HA (sensor, binary_sensor, coordinator…) | Yes | Anywhere `homeassistant` is installed |

For Tier 1, load `const.py` directly to bypass `__init__.py` (which imports HA):
```python
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    "iopool_const",
    pathlib.Path(__file__).parent.parent / "const.py",  # tests/ -> iopool/ -> const.py
)
const = importlib.util.module_from_spec(spec)
spec.loader.exec_module(const)
```

---

## 3. Running Tests

The suite needs two things: `homeassistant` importable, and `PYTHONPATH` resolving `custom_components.iopool`. Anything satisfying both works — use whichever you have.

### Standalone virtualenv — portable, and what CI does

```bash
python3.14 -m venv .venv && . .venv/bin/activate
pip install homeassistant pytest pytest-asyncio pytest-cov pytest-timeout pytest-mock aiohttp aiofiles

# from the repository root
PYTHONPATH=. python -m pytest custom_components/iopool/tests/ -v
```

`tests.yaml` does exactly this, against the latest Home Assistant stable and the beta when one is newer. Two virtualenvs, one per Home Assistant version, is the cheapest way to reproduce the CI matrix locally — a fix can pass on stable and fail on beta.

### Inside a Home Assistant devcontainer

```bash
cd <workspace>/config
python -m pytest custom_components/iopool/tests/ -v
```

### From the host, against a container

Resolve it by image rather than hard-coding an id, which changes on every rebuild:

```bash
C=$(docker ps --format '{{.ID}} {{.Image}}' | awk '/vsc-home-assistant-dev/ {print $1}')
docker exec -w <workspace>/config $C python -m pytest custom_components/iopool/tests/ -v
```

> **This section is the canonical source for running tests.** `git-conventions/SKILL.md §3` (pre-commit gate) references it — do not duplicate the commands elsewhere.

---

## 4. Dependencies and pytest Configuration

`homeassistant` is installed as an ordinary pip package. **`pytest-homeassistant-custom-component` is not used and not required.**

There is no `requirements_test.txt`. CI installs the test dependencies inline (`tests.yaml`): `pytest pytest-asyncio pytest-cov pytest-timeout pytest-mock pytest-html`, plus `aiohttp aiofiles`.

pytest is configured via `custom_components/iopool/pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
filterwarnings = [
    "ignore:Setting custom ClientSession.close attribute is discouraged:DeprecationWarning:homeassistant.helpers.aiohttp_client",
    "ignore:Unclosed client session:ResourceWarning",
]
```

`asyncio_mode = "auto"` means **no `@pytest.mark.asyncio` decorator is needed** on async tests.

Tests must run with `custom_components/`'s parent on `PYTHONPATH`, so that `from custom_components.iopool.xxx import ...` resolves.

---

## 5. Shared Fixtures (conftest.py)

Full bootstrap:

```python
"""Shared test fixtures for hass-iopool."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from homeassistant.core import HomeAssistant
from custom_components.iopool.api_models import IopoolAPIResponse, IopoolAPIResponsePool
from custom_components.iopool.coordinator import IopoolDataUpdateCoordinator


@pytest.fixture
def hass():
    """Return a mock Home Assistant instance."""
    hass_mock = MagicMock(spec=HomeAssistant)
    hass_mock.data = {}
    hass_mock.config = MagicMock()
    hass_mock.config.language = "en"
    hass_mock.states = MagicMock()
    hass_mock.bus = MagicMock()
    hass_mock.config_entries = MagicMock()
    hass_mock.config_entries.flow = MagicMock()
    return hass_mock


@pytest.fixture
def pool_mock():
    """Return a mock IopoolAPIResponsePool."""
    mock = MagicMock(spec=IopoolAPIResponsePool)
    mock.id = "pool-123"
    mock.title = "My Pool"
    mock.mode = "STANDARD"
    mock.has_action_required = False
    mock.latest_measure = MagicMock()
    mock.latest_measure.temperature = 26.5
    mock.latest_measure.ph = 7.2
    mock.latest_measure.orp = 680
    mock.latest_measure.is_valid = True
    return mock


@pytest.fixture
def api_response_mock(pool_mock):
    """Return a mock IopoolAPIResponse."""
    mock = MagicMock(spec=IopoolAPIResponse)
    mock.pools = [pool_mock]
    return mock


@pytest.fixture
def coordinator_mock(hass, api_response_mock):
    """Return a fully populated coordinator mock."""
    mock = MagicMock(spec=IopoolDataUpdateCoordinator)
    mock.data = api_response_mock
    mock.get_pool_data = MagicMock(return_value=api_response_mock.pools[0])
    return mock
```

---

## 6. Mocking Strategy

- Use `MagicMock(spec=HomeAssistant)` for the HA instance
- **Never make real HTTP calls** — always mock at the `aiohttp` session boundary
- Mock coordinator data as an `IopoolAPIResponse` object with `.pools` list
- Use `AsyncMock` for coroutines (e.g., `session.get`, `coordinator.async_request_refresh`)
- Patch module-level utilities: `@patch("custom_components.iopool.sensor.dt_util")`

---

## 7. Test Impact Analysis (Mandatory)

Every time a file in `custom_components/iopool/*.py` is created or modified, perform this analysis **before finishing the task**:

1. **Identify** the corresponding test file: `tests/test_<module>.py`
2. **Read** the existing tests in that file (if it exists)
3. **For each function or class that was added, changed, or removed**, decide:
   - `CREATE` — new behaviour needs a new test
   - `UPDATE` — existing test no longer reflects the new logic
   - `DELETE` — function was removed and its test is now dead code
4. **Apply** all required test changes immediately — never skip silently
5. **Run** the test suite (§3) to validate no regression

---

## 8. Ruff Gate

`lint.yaml` runs both commands on every push and PR touching `custom_components/iopool/**`. Run them before committing:

```bash
ruff check custom_components/iopool
ruff format --check custom_components/iopool
```

`ruff format` may rewrite `except (A, B):` into `except A, B:` — that is PEP 758, valid on Python 3.14, and matches the rest of the file. Accept it.

---

## 9. Time Zones in Tests

The default time zone under pytest is **UTC**. A test that compares local time with UTC will therefore compare a value with itself and pass against unfixed code. Force a zone explicitly and restore it:

```python
previous_tz = dt_util.get_default_time_zone()
dt_util.set_default_time_zone(zoneinfo.ZoneInfo("Europe/Paris"))
try:
    ...
finally:
    dt_util.set_default_time_zone(previous_tz)
```

Without the `finally`, a failing assertion leaks the zone into every later test in the same process.
