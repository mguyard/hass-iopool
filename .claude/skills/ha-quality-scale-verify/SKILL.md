---
name: ha-quality-scale-verify
description: Verifies whether the hass-iopool integration follows a Home Assistant quality-scale rule, checking the code against the official rule definition. Use when asked to check a rule by name, to assess a whole tier (Bronze, Silver, Gold, Platinum), or to produce or update quality_scale.yaml.
---

# Verify a Quality Scale Rule — hass-iopool

Adapted from the Home Assistant core skill. Verify **one rule at a time**; to assess a whole tier, work through that tier's rules.

## Context for this repository

`manifest.json` declares `quality_scale: bronze`, and there is **no `quality_scale.yaml`**. The declaration dates from a plan to publish into Home Assistant core; the project ships through HACS instead, for release flexibility.

Treat bronze as a **target worth converging on for code cleanliness**, not as a statement of current compliance. hassfest does not enforce `quality_scale.yaml` for custom integrations, so CI will never report a gap here.

## 1. Fetch the rule definition

```
https://raw.githubusercontent.com/home-assistant/developers.home-assistant/refs/heads/master/docs/core/integration-quality-scale/rules/{rule}.md
```

`{rule}` is the identifier, for example `config-flow`, `entity-unique-id`, `runtime-data`. Never assess a rule from memory — the definitions change.

## 2. Understand what it requires

Extract the mandatory implementations, the exact code patterns expected, the common violations, the exemption criteria, and which tier the rule belongs to.

## 3. Read the code

The integration lives at `custom_components/iopool/` and its tests at `custom_components/iopool/tests/` — not at the core paths the upstream skill assumes.

Useful sources beyond the code:

- `manifest.json` — declared scale, dependencies, `iot_class`
- `hacs.json` — minimum supported Home Assistant version
- `docs/` — the rules whose identifier starts with `docs-` are satisfied by documentation, not by code
- `https://pypi.org/pypi/<package>/json` for a dependency's metadata

## 4. Verify

Rules are **cumulative**: bronze applies to any integration declaring a scale, silver adds to bronze, and so on. Check only the rules of the targeted tier and below.

For each rule, decide `done`, `todo`, or `exempt`, and justify it against the code rather than against intent. An exemption needs a reason that survives scrutiny — "not applicable" is not one.

Several bronze rules are about documentation rather than code. This repository documents on [docs.page](https://use.docs.page/) under `docs/`, so check there rather than expecting a core-style markdown page.

## 5. Report

Report only rules with a problem — non-compliance, or an exemption that does not hold. For each one:

- **Rule** — identifier and what is wrong
- **Evidence** — file and line showing it
- **Recommendation** — the concrete change that would satisfy it

If every rule checked passes, say so in one line. If a rule definition cannot be fetched or the relevant code cannot be found, say what is missing rather than guessing.

## 6. Producing `quality_scale.yaml`

When the audit covers a full tier, write the result as `custom_components/iopool/quality_scale.yaml`, using the core template's shape:

```yaml
rules:
  # Bronze
  action-setup: todo
  appropriate-polling: done
  brands:
    status: exempt
    comment: Custom integration distributed through HACS, not listed in the brands repository.
```

Every `exempt` carries a `comment` giving the reason. `done` means verified against the code, not intended.
