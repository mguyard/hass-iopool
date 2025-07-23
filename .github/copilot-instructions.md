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
- **Testing:**  
  - Use `pytest` conventions for tests (if/when present).
  - Place tests in a `tests/` directory.
  - **Always suggest adding or updating tests when new features or bug fixes are implemented.**
- **Linting/Formatting:**  
  - Use `flake8` as the linter, with a maximum line length of 150 characters (see `.vscode/settings.json`).
  - You may also use `black` for formatting if desired, but `flake8` is required for linting.

## External Context and Libraries

- You may use context7 for code generation and suggestions.
- You are allowed to use libraries and APIs from:
  - `/home-assistant/core`
  - [developers.home-assistant.io](https://developers.home-assistant.io)
- Use these resources to ensure compatibility and best practices with Home Assistant integrations.

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
- **Always suggest adding or updating tests for new features or bug fixes.**
- **Enforce flake8 linting with a max line length of 150 characters.**

---

These instructions are designed to help GitHub Copilot and Copilot Coding Agent generate code, documentation, and commit messages that are consistent with the project's standards and best practices.
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

---
These instructions are designed to help GitHub Copilot and Copilot Coding Agent generate code, documentation, and commit messages that are consistent with the project's standards and best practices.
