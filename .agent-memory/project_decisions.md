---
last_updated: 2026-03-10
purpose: "Durable project decisions and invariants. Template file for downstream projects."
---

# Project Decisions

## How to Use

- Add entries only when a decision is durable and likely to matter in future sessions.
- Prefer linking to code/paths and stating invariants/constraints over narrative.
- If a decision is superseded, append an "Update" note to the original entry.
- Keep runtime scratch notes out of this file.
- Separate verified repo facts from assumptions or interpretations.

## Entry Template

```md
## <Decision Title> — YYYY-MM-DD

### Facts
- Verified repo facts with file/path references.

### Inferences
- Assumptions or interpretations that still need validation.

### Decision
- The durable rule, invariant, or operating choice.

### Consequences
- What this changes, constrains, or requires going forward.
```

## Onboarding Snapshot Template

Use this after project familiarization / onboarding runs:

```md
## Onboarding Snapshot — YYYY-MM-DD

### Facts
- Major modules / packages
- Run / build / test commands
- Key conventions and invariants
- Top risks or TODOs worth remembering

### Inferences
- Only if necessary, clearly marked
```

## Entries

## Onboarding Snapshot — 2026-04-22

### Facts

**Project identity**
- Custom Home Assistant integration for iopool pool monitoring system
- HACS-compatible, quality_scale: bronze, version: 1.2.3
- Repo: `mguyard/hass-iopool`, default branch: `main`, dev branch: `dev`, beta branch: `beta`
- All PRs target `dev`

**Module map**
- `__init__.py` — entry setup/teardown, `IopoolData` wiring (filtration, coordinator)
- `api_models.py` — `IopoolAPIResponse`, `IopoolAPIResponsePool`, `IopoolLatestMeasure`, `IopoolAdvice`
- `binary_sensor.py` — BinarySensor platform
- `config_flow.py` — UI config flow + options flow (CONFIG_VERSION=1)
- `const.py` — `DOMAIN`, API endpoints, sensor type constants, config keys
- `coordinator.py` — `IopoolDataUpdateCoordinator`, polled every 300 s via direct aiohttp calls
- `diagnostics.py` — HA diagnostics endpoint
- `entity.py` — `IopoolEntity(CoordinatorEntity, RestoreEntity)`, `_attr_has_entity_name = True`
- `filtration.py` — Filtration logic and time-based scheduling
- `models.py` — `IopoolData`, `IopoolConfigData`, `IopoolConfigEntry` alias
- `select.py` — Select platform
- `sensor.py` — Sensor platform (temperature, pH, ORP, filtration recommendation, etc.)
- `translations/en.json`, `translations/fr.json` — all entity human names

**API access**
- Direct HTTP calls via `aiohttp` to `https://api.iopool.com/v1`
- No external wrapper library (`requirements: []` in `manifest.json`)
- Key endpoints: `GET /pools` (all pools), `GET /pool/{pool_id}` (single pool)

**Coordinator data**
- `coordinator.data` is an `IopoolAPIResponse` object
- `coordinator.data.pools` — list of `IopoolAPIResponsePool`
- `coordinator.get_pool_data(pool_id)` — helper method for single pool lookup

**Key invariants**
- Always use `IopoolConfigEntry` (defined in `models.py`, not raw `ConfigEntry`)
- `unique_id` pattern: `{entry_id}_{pool_id}_{description.key}`
- Translation keys must be added to both `en.json` AND `fr.json`
- Every new entity needs a row in `docs/integration/entities.mdx`

**Run/build/test commands**
- Lint: `flake8 --max-line-length=150 custom_components/iopool/`
- Tests inside devcontainer: `cd /workspaces/home-assistant-dev/config && python -m pytest custom_components/iopool/tests/ -v`
- Tests outside devcontainer: `docker ps` → `docker exec -w /workspaces/home-assistant-dev/config <ID> python -m pytest custom_components/iopool/tests/ -v`
- Detect environment: `test -d /workspaces && echo inside || echo outside`
- Tests live at `custom_components/iopool/tests/` (devcontainer-mounted path)

**CI/CD**
- `home-assistant.yaml`: hassfest + HACS validation (push/PR on `main`, `beta`)
- `tests.yaml`: PyTest matrix (HA stable + beta), triggers on push/PR to `dev`
- `release.yaml`: semantic-release on tag push
- `codeql.yaml`: weekly CodeQL Python security scan
- `devsec.yaml`: FortiDevSec SAST on `dev` branch

**Commit convention**
- Format: `<type>[scope]: <gitmoji> <description>` — see `python-homeassistant/SKILL.md` §7
- Types: feat ✨, fix 🐛, docs 📝, refactor ♻️, test ✅, chore 🔧

**Agent/skills structure**
- Skills in `.github/skills/` — only Python/HA-relevant skills kept
- Domain skill: `python-homeassistant/SKILL.md`
- Universal skills: code-quality, testing-qa, security-best-practices, review-core, review-orchestration, multi-model-review, planning-structure, research-discovery, memory-management, git-worktree, api-design

### Inferences
- None at this time

### memory_meta
- timestamp: 2026-04-04
- author: GitHub Copilot (onboarding scan)
