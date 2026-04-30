# GitHub Copilot Custom Instructions for `hass-iopool`

## Project Context

- **Project Type:** Custom integration for [Home Assistant](https://www.home-assistant.io/), written in Python.
- **Purpose:** Connects Home Assistant to the iopool pool monitoring system — water quality sensors, filtration management, diagnostics, config flow.
- **Language:** All code, comments, and docstrings must be in **English**.
- **API access:** Direct HTTP calls via `aiohttp` to `https://api.iopool.com/v1`. No external wrapper library — `requirements: []` in `manifest.json`.

## Architecture

```
custom_components/iopool/
├── __init__.py          # Integration setup/teardown, IopoolConfigEntry alias unused here (in models.py)
├── api_models.py        # IopoolAPIResponse, IopoolAPIResponsePool, IopoolLatestMeasure, IopoolAdvice
├── binary_sensor.py     # BinarySensor platform
├── config_flow.py       # UI config flow + options flow (CONFIG_VERSION=1)
├── const.py             # All constants (DOMAIN, endpoints, sensor types, config keys)
├── coordinator.py       # IopoolDataUpdateCoordinator (polls every 300 s)
├── diagnostics.py       # HA diagnostics endpoint
├── entity.py            # Base entity class (IopoolEntity)
├── filtration.py        # Filtration logic and time-based scheduling
├── manifest.json        # Integration metadata (no external requirements)
├── models.py            # IopoolData, IopoolConfigData, IopoolConfigEntry alias
├── select.py            # Select platform
├── sensor.py            # Sensor platform
└── translations/        # en.json, fr.json
```

**Key patterns:**
- `IopoolConfigEntry = ConfigEntry[IopoolData]` — defined in `models.py`. Always use this alias instead of raw `ConfigEntry`.
- Coordinator data: `coordinator.data` is an `IopoolAPIResponse` object; use `coordinator.data.pools` (list of `IopoolAPIResponsePool`) or `coordinator.get_pool_data(pool_id)`.
- `unique_id` pattern: `{entry_id}_{pool_id}_{description.key}`.

## Quick Start — Key Commands

```bash
# Lint
flake8 --max-line-length=150 custom_components/iopool/

# Tests — see .github/skills/testing-hass-iopool/SKILL.md for full environment detection
test -d /workspaces && echo "inside devcontainer" || echo "outside"
# Inside:  cd /workspaces/home-assistant-dev/config && python -m pytest custom_components/iopool/tests/ -v
# Outside: docker ps  →  docker exec -w /workspaces/home-assistant-dev/config <ID> python -m pytest custom_components/iopool/tests/ -v
```

> No Makefile. `pyproject.toml` at `custom_components/iopool/pyproject.toml` configures pytest.

## CI/CD

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `home-assistant.yaml` | push / PR on `main`, `beta` | `hassfest` + HACS validation |
| `tests.yaml` | push / PR on `dev` | PyTest (HA stable + beta matrix) |
| `release.yaml` | tag push | `semantic-release` |
| `codeql.yaml` | weekly + push | CodeQL Python security scan |

**Branch strategy:** `dev` → development. `beta` → beta releases. `main` → stable releases. All PRs target `dev`.

## Mandatory Rules for Copilot Coding Agent

- All code, comments, and docstrings in **English**.
- **After every `custom_components/iopool/*.py` change**, analyse `tests/test_<module>.py` and CREATE, UPDATE, or DELETE tests as needed. Never skip this step.
- **Flake8 max line length: 150 characters.**
- New entities: follow `python-homeassistant/SKILL.md §5`. Add row to `docs/integration/entities.mdx`.
- Commit/PR: follow `python-homeassistant/SKILL.md` §7. PR target branch is always `dev`.
- Use `async`/`await` for all I/O. Use `_LOGGER = logging.getLogger(__name__)`, never `print()`.
- Use `context7` and [developers.home-assistant.io](https://developers.home-assistant.io) for HA API guidance.
- Use the [iopool Public API docs](https://help.iopool.com/en/articles/5537423-iopool-public-api) for iopool API guidance before implementing any API call. Note: the page contains images — use `fetch_webpage` or `view_image` to analyse them.
- **Every question asked to the user MUST use `vscode_askQuestions`.** Never ask questions inline as plain text only. Always set `allowFreeformInput: true` (or leave it at its default) so the user can provide a custom answer alongside the proposed options.
