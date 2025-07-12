Follow the Conventional Commits format strictly for commit messages. Use the structure below:

```
<type>[optional scope]: <gitmoji> <description>

[optional body]
```

Guidelines:

1. **Type and Scope**: Choose an appropriate type (e.g., `feat`, `fix`) and optional scope to describe the affected module or feature.

2. **Gitmoji**: Use the following gitmoji for each commit type to ensure consistency:
   - `feat`: ✨ (sparkles) — For new features
   - `fix`: 🐛 (bug) — For bug fixes
   - `docs`: 📝 (memo) — For documentation changes (including anything in `docs/` or `docs.json`)
   - `refactor`: ♻️ (recycle) — For code refactoring that does not add features or fix bugs
   - `test`: ✅ (white check mark) — For adding or updating tests
   - `chore`: c (wrench) — For maintenance, build, or tooling changes

3. **Description**: Write a concise, informative description in the header; use backticks if referencing code or specific terms.

4. **Body**: For additional details, use a well-structured body section:
   - Use bullet points (`*`) for clarity.
   - Clearly describe the motivation, context, or technical details behind the change, if applicable.

**Examples:**

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

**Rules:**

- Limit the first line to 72 characters or less.
- Use backticks for code/entity references in the description.
- Write the body in bullet points for clarity if needed.
- Always write commit messages in English.

Commit messages should be clear, informative, and professional, aiding readability and project tracking.