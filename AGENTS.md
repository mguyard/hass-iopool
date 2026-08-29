# Agent Instructions — hass-iopool

Repository rules for AI coding agents. This file is the source of truth; `CLAUDE.md` imports it and adds only what is specific to Claude Code.

## Precedence

`.claude/rules/` is vendored from the ECC plugin and kept byte-identical to upstream, so it can be refreshed without merge work.
It is generic advice, written for no repository in particular.
**Where it disagrees with this file, this file wins.**

The known divergences, so they do not have to be rediscovered:

| An ECC rule says | This repository does |
|---|---|
| Format with `black`, sort imports with `isort` | `ruff format` only — `lint.yaml` runs `ruff format --check`. Imports are sorted by ruff's isort with `force-sort-within-sections` and `known-first-party = ["homeassistant"]`, the Home Assistant core layout, which isort does not reproduce by default. |
| Prefer `@dataclass(frozen=True)`, never mutate | `IopoolData` is mutable by design: it is Home Assistant's `runtime_data`. `__init__.py` assigns `.filtration`, `.setup_time_events` and `.config` after construction, and `filtration.py` appends to `remove_time_listeners`. |
| `pytest --cov=src`, `@pytest.mark.unit` / `.integration` | There is no `src/` — see Commands below. No marker is registered in `pyproject.toml`, so those two raise `PytestUnknownMarkWarning`. Group cases with `parametrize` instead. |
| Load secrets from `.env` with `python-dotenv`, scan with `bandit` | The iopool API key is entered in the config flow and stored in the config entry, and `manifest.json` declares `"requirements": []`. Security scanning is CodeQL, weekly. |
| camelCase variables, PascalCase types | PEP 8, as `rules/ecc/python/coding-style.md` itself asks. The naming section of `rules/ecc/common/coding-style.md` is written for TypeScript. |
| Anything about FastAPI | `rules/ecc/python/fastapi.md` matches no file here — its globs resolve to nothing. |

## Project

Custom [Home Assistant](https://www.home-assistant.io/) integration for the iopool pool monitoring system: water quality sensors, filtration scheduling, config flow, diagnostics. HACS-compatible, `quality_scale: bronze`.

- All code, comments, docstrings and commit messages in **English**.
- API access is direct `aiohttp` against `https://api.iopool.com/v1`. There is no wrapper library and `manifest.json` declares `"requirements": []`.
- Read the [iopool Public API docs](https://help.iopool.com/en/articles/5537423-iopool-public-api) before implementing any API call — Context7 has no iopool knowledge, and the page carries information in images.
- Use [developers.home-assistant.io](https://developers.home-assistant.io) and Context7 for Home Assistant API guidance.

## Module map

```
custom_components/iopool/
├── __init__.py          # Entry setup/teardown, IopoolData wiring
├── api_models.py        # IopoolAPIResponse, IopoolAPIResponsePool, IopoolLatestMeasure, IopoolAdvice
├── binary_sensor.py     # BinarySensor platform
├── config_flow.py       # UI config flow + options flow (CONFIG_VERSION=1)
├── const.py             # DOMAIN, endpoints, sensor keys, config keys
├── coordinator.py       # IopoolDataUpdateCoordinator — polls every 300 s
├── diagnostics.py       # HA diagnostics endpoint
├── entity.py            # IopoolEntity(CoordinatorEntity, RestoreEntity)
├── filtration.py        # Filtration logic and time-based scheduling
├── frontend/            # Bundled iopool-card Lovelace resource
├── models.py            # IopoolData, IopoolConfigData, IopoolConfigEntry
├── pyproject.toml       # ruff + pytest configuration
├── select.py            # Select platform
├── sensor.py            # Sensor platform
├── tests/               # pytest suite (see below)
└── translations/        # en.json, fr.json — all entity human names
```

## Invariants

- Use `IopoolConfigEntry` from `models.py`, never a raw `ConfigEntry`. It is `ConfigEntry[IopoolData]`.
- Reach runtime state through `entry.runtime_data.coordinator`, `.config`, `.filtration`.
- `coordinator.data` is an `IopoolAPIResponse`. Use `coordinator.get_pool_data(pool_id)` and check for `None` before use.
- Entities extend `IopoolEntity`, which already sets `_attr_has_entity_name = True` and provides `device_info`.
- `unique_id` is `f"{entry_id}_{pool_id}_{description.key}"`.
- Every entity needs a `translation_key`, present in **both** `translations/en.json` and `translations/fr.json`.
- Every new entity needs a row in `docs/integration/entities.mdx`.
- Constants live in `const.py`. No magic strings or numbers inline.
- `_LOGGER = logging.getLogger(__name__)`. Never `print()`.
- All I/O is `async`/`await`. No blocking calls in async context.
- The iopool API key is the only credential. Never log it, never expose it in an issue, a commit message, or a PR body.

## Commands

```bash
# Lint and format — ruff, configured in custom_components/iopool/pyproject.toml
ruff check custom_components/iopool
ruff format --check custom_components/iopool

# Tests — anywhere homeassistant is importable and PYTHONPATH resolves
# `custom_components.iopool`, which is what CI does
PYTHONPATH=<dir containing custom_components> python -m pytest custom_components/iopool/tests/ -v
```

The test command is environment-agnostic: a plain virtualenv with `pip install homeassistant pytest pytest-asyncio pytest-timeout pytest-mock` is enough, and it is what `tests.yaml` sets up. Running inside a Home Assistant devcontainer works too, from `config/`. Use whichever you have — see the `testing-hass-iopool` skill for the variants.

CI pins `ruff==0.16.1`; a newer release must not be able to turn a green PR red on its own. Line length is 88, and `E501` is deliberately ignored — formatting is the formatter's job, not the linter's.

There is no Makefile and no `requirements_test.txt`.

## Python 3.14

Home Assistant requires Python 3.14 since 2026.3, and this integration uses 3.14-only syntax. Do not flag it, and do not suggest workarounds for older versions.

- `except ValueError, TypeError:` without parentheses is valid (PEP 758) and is what `ruff format` produces here. `filtration.py` uses it in three places.
- Annotations are evaluated lazily (PEP 649). Forward references need no quotes.

## CI

| Workflow | Trigger | Purpose |
|---|---|---|
| `tests.yaml` | push / PR on `dev`, paths `custom_components/iopool/**` | pytest on HA stable + beta, Python 3.14 |
| `lint.yaml` | push / PR on `dev`, same paths | `ruff check` + `ruff format --check` |
| `home-assistant.yaml` | push / PR on `main`, `beta`, daily | hassfest + HACS validation |
| `semantic-prs.yml` | PR opened / edited | validates the PR title against Conventional Commits |
| `release.yaml` | push on `main`, `beta` | semantic-release |
| `codeql.yaml` | weekly (Saturday), manual | CodeQL Python security scan |
| `labelers.yml` | push on `main`, manual | issue and PR labels |
| `lock-stale.yml` | daily | locks stale issues |

`tests.yaml` and `lint.yaml` are path-filtered: a change outside `custom_components/iopool/**` does not run them.

## Branches

| Branch | Role |
|---|---|
| `dev` | Development. **All PRs target this branch.** |
| `beta` | Prereleases, published by semantic-release |
| `main` | Stable releases, published by semantic-release. Repository default. |

Never commit or push directly to `beta` or `main` — semantic-release owns them. Always confirm the current branch with `git branch --show-current` before committing.

Because `main` is the default branch, a `Closes #N` keyword only fires when the change reaches `main`, not when a PR merges into `dev`. Issues therefore stay open through the beta cycle by design.

## Commits

```
<type>[optional scope]: <gitmoji> <description>

[optional body — bullet points]

Tests: ✅ N passed, ❌ 0 failed, ⚠ 0 errors
```

- First line in English, 72 characters maximum.
- Types and gitmoji: `feat` ✨, `fix` 🐛, `docs` 📝, `refactor` ♻️, `test` ✅, `chore` 🔧, `perf` ⚡, `ci` 🔧. `semantic-prs.yml` accepts `feat|fix|docs|test|ci|refactor|perf|chore`.
- Scope is the module filename without extension: `sensor`, `coordinator`, `filtration`, `config_flow`, `deps`, `events`…
- The `Tests:` line is required whenever `custom_components/` changed. Use `Tests: N/A (no custom_components change)` otherwise.
- The body explains **why**. Never restate what the diff already shows.

The pre-commit test gate, the pull request description template and the prepare-PR workflow live in the `git-conventions` skill.

Changelog rendering is configured in `.releaserc`: `feat`, `fix`, `perf`, `refactor`, `revert` and `docs` are rendered, everything else is hidden. A change users must know about therefore needs a rendered type — a `docs` commit with an explicit title is the way to surface a contract change.

## Pull requests

- Title follows the commit format; `semantic-prs.yml` enforces it.
- Target `dev`, always.
- Run the full suite and `ruff` before opening. Fix everything first.
- Describe what changed and why, and how it was verified.

## Testing

- Tests live in `custom_components/iopool/tests/`, inside the integration folder so that a Home Assistant instance which mounts only that folder still sees them.
- `asyncio_mode = "auto"`: async tests need no `@pytest.mark.asyncio`.
- **After every change to `custom_components/iopool/*.py`**, review `tests/test_<module>.py` and create, update or delete tests accordingly. Never skip this.
- Write the failing test first, confirm it fails for the right reason, then fix. A test that passes against unfixed code proves nothing — check it is load-bearing.
- Prefer `pytest.mark.parametrize` with named `ids` over duplicated bodies. Avoid branching inside tests.
- The default time zone under pytest is UTC. A test about local time must set its own zone, and restore it in a `finally`.

## Validation against a running Home Assistant

Unit tests are necessary but not sufficient for this integration. Filtration is driven by a real clock through `async_track_time_change`, and defects have hidden in that gap that no unit test could see — an unrounded end time that made the stop fire a minute late half the time, and timestamps switching to UTC after a retry.

**Any change to runtime behaviour must be exercised against a running Home Assistant before the pull request is opened.** That covers `filtration.py`, `coordinator.py`, `config_flow.py`, and anything that reads an entity state or schedules work.

The instance is yours to choose — a Home Assistant devcontainer, a container, a core checkout in a virtualenv, or a spare instance. What matters is that it is real, that the integration is loaded, and that you can read `home-assistant.log`. The `live-validation-hass-iopool` skill describes a portable method over the REST API, along with the scenarios worth replaying.

State in the pull request **what you ran, on which Home Assistant version, and what you observed** — quoting the log lines. A claim that cannot be reproduced from the description is not evidence.

## Documentation

Whenever a feature, entity, event or behaviour is added or changed, check `docs/integration/` for pages that cover it and update them in the same change. Match the existing tone, structure and MDX components — do not introduce new formatting patterns. When unsure whether a change warrants a docs update, ask.

## Comments

Explain why, never what. One short line stating a non-obvious constraint, or no comment at all. Do not restate the following line, do not justify a change by describing what the code looked like before, and do not add section dividers — they go stale and mislead.
