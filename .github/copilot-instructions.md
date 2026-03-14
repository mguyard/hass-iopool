# GitHub Copilot Custom Instructions for `hass-iopool`

## Project Context

- **Project Type:**  
  This repository is a **custom integration for [Home Assistant](https://www.home-assistant.io/)**, written in Python.
- **Purpose:**  
  The integration connects Home Assistant to the iopool pool monitoring system, exposing pool data (temperature, pH, ORP, etc.), managing filtration automation (summer/winter modes), and providing Home Assistant entities, events, and diagnostics.
- **Structure:**  
  - All integration code is in `custom_components/iopool/`.
  - Documentation is in the `docs/` directory and `docs.json`.
  - The integration uses Home Assistant's config flow, entity platforms (sensor, binary_sensor, select), and DataUpdateCoordinator pattern.
  - The codebase follows Home Assistant's best practices for custom components.
- **Language:**  
  - All code, comments, and docstrings must be in **English** (even though the maintainer is French).
- **Documentation:**  
  - All files in `docs/` and `docs.json` are documentation and must use the `docs` commit type.
  - Documentation is in Markdown or MDX, and must be clear and concise.
  - Entity reference: `docs/integration/entities.mdx` — keep it up to date when adding/removing entities.
- **Testing:**  
  - Use `pytest` conventions for tests.
  - Tests live in `custom_components/iopool/tests/`.
  - **Always add or update tests when implementing features or bug fixes.**
- **Linting/Formatting:**  
  - Use `flake8` as the linter, with a maximum line length of 150 characters.
  - You may also use `black` for formatting, but `flake8` is required for linting.

## Dev Environment & Commands

> Tests require a full Home Assistant dev container (`/workspaces/home-assistant-dev`).

```bash
# Run all tests (from within the HA dev container)
cd /workspaces/home-assistant-dev/config
PYTHONPATH=/workspaces/home-assistant-dev python -m pytest custom_components/iopool/tests/

# Verbose with short tracebacks
PYTHONPATH=/workspaces/home-assistant-dev python -m pytest custom_components/iopool/tests/ -v --tb=short

# With coverage
PYTHONPATH=/workspaces/home-assistant-dev python -m pytest custom_components/iopool/tests/ --cov=. --cov-report=term-missing

# Shortcut scripts (auto-configure PYTHONPATH)
./custom_components/iopool/tests/run_tests.sh
./custom_components/iopool/run_tests.sh

# Lint
flake8 custom_components/iopool/ --max-line-length=150
```

> ⚠️ **Never create a `pytest.ini`** file — it breaks async test discovery. Config lives in `pyproject.toml` (`asyncio_mode = "auto"`).

## Architecture

### Data Flow

```
Config Flow → ConfigEntry.runtime_data (IopoolData)
                    ├── coordinator  (IopoolDataUpdateCoordinator)  — polls API every 5 min
                    ├── filtration   (Filtration)                   — time-based scheduling
                    └── setup_time_events                           — callback reference
```

### Key Files

| File | Role |
|------|------|
| `__init__.py` | Entry setup, platform loading, runtime_data assembly |
| `coordinator.py` | `DataUpdateCoordinator` — fetches `IopoolAPIResponse` |
| `api_models.py` | Dataclass models for raw API responses |
| `models.py` | `IopoolData`, `IopoolConfigData`, filtration option dataclasses |
| `const.py` | All constants: domain, sensor keys, event types, API URLs |
| `entity.py` | `IopoolEntity(CoordinatorEntity, RestoreEntity)` base class |
| `sensor.py` | Sensor platform (temperature, pH, ORP, mode, recommendations) |
| `binary_sensor.py` | Binary sensor platform (action required, filtration active) |
| `select.py` | Select platform (boost selector, pool mode selectors) |
| `filtration.py` | Time-based filtration slot scheduling (`async_track_time_change`) |

### Platform Loading Order

```python
PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.BINARY_SENSOR]
```

⚠️ **Order matters:** `sensor` must load before `binary_sensor`; filtration entities have a dependency on it.

### Manifest Highlights

- **Domain:** `iopool` | **IoT class:** `cloud_polling` | **Type:** `hub`
- **Quality scale:** `bronze` | **Dependencies:** `["cloud", "history_stats"]`
- **Docs:** https://docs.page/mguyard/hass-iopool

## External Context and Libraries

- You may use context7 for code generation and suggestions.
- You are allowed to use libraries and APIs from:
  - `/home-assistant/core`
  - [developers.home-assistant.io](https://developers.home-assistant.io)
- Use these resources to ensure compatibility and best practices with Home Assistant integrations.

## Pull Request Best Practices

- **Title:**
  - The PR title MUST follow the same format as the commit message guidelines (see below):
    `<type>[optional scope]: <gitmoji> <description>`
  - The title should summarize the main purpose of the PR.

- **Description:**
  - The PR description MUST provide a clear summary of all changes included in the PR.
  - List and briefly explain each commit included in the PR.
  - For each commit, include a direct link to the commit (e.g., `https://github.com/mguyard/hass-iopool/commit/<sha>`).
  - If the PR addresses or closes issues, reference them using GitHub keywords (e.g., `Closes #123`).
  - Use bullet points for clarity if needed.

- **Branch:**
  - All PRs MUST use `dev` as the base branch.

- **General:**
  - Ensure your PR is focused and does not mix unrelated changes.
  - Follow all other project and commit message guidelines described above.


## Commit Message Guidelines

- **Format:**  
  ```
  <type>[optional scope]: <gitmoji> <description>

  [optional body]
  ```
- **Types and Gitmoji:**  
  Use the following gitmoji for each commit type to ensure consistency:
  - `feat`: ✨ (sparkles) — For new features
  - `fix`: 🐛 (bug) — For bug fixes
  - `docs`: 📝 (memo) — For documentation changes (including anything in `docs/` or `docs.json`)
  - `refactor`: ♻️ (recycle) — For code refactoring that does not add features or fix bugs
  - `test`: ✅ (white check mark) — For adding or updating tests
  - `chore`: 🔧 (wrench) — For maintenance, build, or tooling changes

- **Examples:**
  ```
  feat(api): ✨ Add support for multiple pools

  * Implements multi-pool detection and entity creation.
  * Updates API client to handle multiple pool IDs.
  ```

  ```
  docs(setup): 📝 Update installation instructions in docs/setup.mdx

  * Clarifies API key retrieval steps.
  ```

  ```
  fix(sensor): 🐛 Correct temperature rounding logic
  ```

  ```
  refactor(core): ♻️ Simplify DataUpdateCoordinator usage
  ```

  ```
  test(sensor): ✅ Add tests for ORP sensor edge cases
  ```

  ```
  chore(deps): 🔧 Update Home Assistant minimum version requirement
  ```

- **Rules:**
  - Limit the first line to 72 characters or less.
  - Use backticks for code/entity references in the description.
  - Write the body in bullet points for clarity if needed.
  - Always write commit messages in English.

## Python-Specific Best Practices

- Use virtual environments for development.
- Use `async`/`await` for I/O-bound operations.
- Handle exceptions gracefully and log errors.
- Use `logging` instead of `print` for output.
- Prefer list comprehensions and generator expressions for concise code.
- Avoid global variables.
- Use constants for configuration values.

## Home Assistant Integration

- Follow [Home Assistant custom component guidelines](https://developers.home-assistant.io/docs/creating_component_index/).
- Entities should have unique IDs and meaningful names.
- Use translations for entity names and options.
- Ensure all entities are documented in `docs/integration/entities.mdx`.

## For Copilot Coding Agent

- When asked to create or modify files, always use English for code, comments, and docstrings.
- When generating documentation, use Markdown or MDX and English.
- When generating commit messages, follow the Conventional Commits and gitmoji rules above.
- When working with Home Assistant, prefer async APIs and follow the entity/component patterns in the codebase.
- All configuration, code, and documentation must be consistent with the existing project structure and standards.
- **Always add or update tests when implementing features or bug fixes.**
- **Enforce flake8 linting with a max line length of 150 characters.**
- Before editing code, read the relevant file(s) to understand existing patterns.
- When adding a new entity, update `docs/integration/entities.mdx` and both translation files (`en.json`, `fr.json`).
