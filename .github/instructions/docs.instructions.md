---
description: "Use when creating or editing documentation files in docs/ or docs.json. Covers MDX format, frontmatter structure, navigation, commit conventions, and the docs.page platform."
applyTo: "docs/**, docs.json"
---

# Documentation Guidelines

## Format

All documentation files use **MDX** (Markdown + JSX). Do not use plain `.md` files in `docs/`.

Every MDX file must start with YAML frontmatter:

```mdx
---
title: Page Title
description: One-line summary shown in search results and meta tags
previous: /integration/previous-page
previousTitle: Previous Page
next: /integration/next-page
nextTitle: Next Page
---
```

`title` and `description` are required. `previous`/`next` are required for pages in a sequential flow.

## Commit Convention

Any change to `docs/` or `docs.json` must use the `docs` commit type:

```
docs(entities): 📝 Add salinity sensor to entity reference
```

Never mix documentation changes with code changes in the same commit.

## `docs/integration/entities.mdx` — Entity Reference

This file is the **single source of truth for all HA entities**. Keep it up to date whenever you add or remove an entity.

Table format:
```mdx
| Entity Name (type) | Description | Availability |
|--|--|--|
| Temperature (sensor) | The water temperature in °C | Always |
| Filtration (binary sensor) | Whether the pump is running | Always |
| Boost Selector (select) | Set a temporary filtration boost | Always |
```

- Column 1: `Display Name (entity type)` — must match the translation name exactly
- Column 2: Plain English description of what the entity represents
- Column 3: When it is available (`Always`, `When filtration enabled`, etc.)

Use `<Info>` blocks for tips and callouts:
```mdx
<Info>
All entities are refreshed every `5 minutes` by default.
</Info>
```

## `docs.json` — Navigation Structure

`docs.json` controls the sidebar and tab navigation on docs.page. When adding a new page:

1. Create the `.mdx` file at the correct path under `docs/`.
2. Add the page to the `sidebar` array in `docs.json` under the appropriate group:

```json
{
  "title": "My New Page",
  "href": "/integration/my-new-page",
  "icon": "optional-lucide-icon-name"
}
```

Do not duplicate page entries or create orphan pages (pages not referenced in `docs.json`).

## Language and Style

- All documentation must be in **English**.
- Write for end users, not developers — avoid internal code references unless necessary.
- Keep descriptions short and factual.
- Link to the official docs site when referencing the integration: https://docs.page/mguyard/hass-iopool
