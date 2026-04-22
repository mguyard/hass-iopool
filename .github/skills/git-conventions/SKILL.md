---
name: git-conventions
description: Commit message format, PR conventions, branch rules, and pre-commit test gate for hass-iopool.
user-invocable: false
---

# Git Conventions — hass-iopool

Use this skill for any commit, PR creation, or pre-commit verification task in the hass-iopool project.

---

## 1. Commit Message Format

```
<type>[optional scope]: <gitmoji> <description>

[optional body — bullet points]

Tests: N passed, 0 failed, 0 errors
```

- First line: **max 72 characters**, in **English**
- Body: bullet points only when needed for clarity
- `Tests:` line: **always required** — run the test gate (§3) before committing

---

## 2. Types, Gitmoji, and Scopes

### 2.1 Types → Gitmoji

| Type | Gitmoji | Use When |
|------|---------|----------|
| `feat` | ✨ | New feature or entity |
| `fix` | 🐛 | Bug fix |
| `docs` | 📝 | Anything in `docs/` or `docs.json` |
| `refactor` | ♻️ | Code restructure, no feature/fix |
| `test` | ✅ | Adding or updating tests |
| `chore` | 🔧 | Deps, CI, build, maintenance |

### 2.2 Scope (optional)

Use the module filename without extension:
- `sensor`, `binary_sensor`, `select`, `coordinator`, `config_flow`
- `filtration`, `diagnostics`, `entity`, `models`, `const`, `api_models`
- `deps` (dependency bumps), `readme`, `entities` (doc pages)

### 2.3 Examples

```
feat(sensor): ✨ Add pool mode sensor entity

- Added IopoolPoolModeSensor to sensor.py
- Added translation keys to en.json and fr.json

Tests: ✅ 42 passed, ❌ 0 failed, ⚠️ 0 errors

fix(coordinator): 🐛 Retain stale data when API returns empty response

Tests: ✅ 42 passed, ❌ 0 failed, ⚠️ 0 errors

test(sensor): ✅ Add test for filtration recommendation sensor

Tests: ✅ 43 passed, ❌ 0 failed, ⚠️ 0 errors

chore(deps): 🔧 Bump minimum Home Assistant version to 2026.3.0

Tests: ✅ 42 passed, ❌ 0 failed, ⚠️ 0 errors
```

---

## 3. Pre-commit Gate (Mandatory)

The pre-commit gate applies **only when `custom_components/` has changed** in the current commit.

### 3.0 Branch Check (Step Zero — Always Required)

Before any commit, verify the current branch:

```bash
git branch --show-current
```

- If the branch is `beta` or `main` → **stop immediately**. Switch to `dev` first:
	```bash
	git checkout dev
	git pull origin dev
	```
	Then re-stage changes and continue.
- If the branch is `dev` or a feature branch → proceed to §3.1.

> **Never commit or push directly to `beta` or `main`.** These branches are managed exclusively by `semantic-release` CI. The VS Code context may report `Current branch: beta` — ignore this for commit targeting; always check with `git branch --show-current`.

Before running, check whether the staged or changed files include `custom_components/`:
```bash
git diff --name-only HEAD | grep -q "^custom_components/" && echo "tests required" || echo "tests not required"
```

If no file under `custom_components/` is modified → skip the gate, use `Tests: N/A (no custom_components change)` in the commit body.

If any file under `custom_components/` is modified → the gate is mandatory. No commit may be created until all tests pass at 100%.

### 3.1 Run Tests

Follow `@skills/testing-hass-iopool/SKILL.md §3` for the canonical run commands (environment detection, devcontainer vs `docker exec`).

Quick summary:
```bash
# Detect environment
test -d /workspaces && echo "inside devcontainer" || echo "outside"
# Then run python -m pytest custom_components/iopool/tests/ -v (see testing-hass-iopool §3 for full commands)
```

Capture the output to extract the summary line.

### 3.2 Pass Gate

Parse the last summary line from pytest output:
```
N passed, 0 failed, 0 errors
```

- If **0 failures and 0 errors** → gate passes, proceed to commit
- If **any failure or error** → go to §3.3

### 3.3 Fix Loop (when gate fails)

1. Read the failing test output and identify the root cause
2. Fix the code or test causing the failure
3. Rerun tests (§3.1)
4. Repeat until gate passes
5. Do NOT commit until 100% pass — this rule has no exceptions

### 3.4 Embed Results in Commit Body

After gate passes (or is skipped), embed the test summary as the final line of the commit body:

```
feat(sensor): ✨ Add battery level sensor entity

- Added IopoolPoolModeSensor to sensor.py
- Added translation keys to en.json and fr.json

Tests: ✅ 42 passed, ❌ 0 failed, ⚠️ 0 errors
```

Format:
- `Tests: ✅ N passed, ❌ M failed, ⚠️ E errors` — when gate ran
- `Tests: N/A (no custom_components change)` — when gate was skipped

### 3.5 Issue Comment (When Issue is Referenced)

If an issue number is provided in the user request (e.g., "fixes #42", "related to #17", or any explicit `#N` reference), you **must** post a comment on that issue **before creating the commit**.

#### When to apply

- The user's request mentions an issue number explicitly (`#N`)
- The implementation directly fixes or addresses a known issue

#### Comment content (in the language used by the issue — French if the issue is in French, English otherwise)

The comment must include:
1. **What was done** — summary of the change (files modified, logic applied)
2. **Why** — root cause or motivation for the change
3. **How** — approach taken (e.g., sentinel value, refactored logic, new test coverage)
4. **Availability** — mention that the fix will be available in the next release

#### How to post

Use MCP GitHub tools: `mcp_github_add_issue_comment` on `mguyard/hass-iopool` with the issue number and the comment body.

> This step is mandatory and must complete successfully before the commit is created. Do not skip it even if the commit message already references the issue with `Fixes #N`.

---

## 4. PR Conventions

### 4.1 PR Title

Same format as the commit first line:
```
<type>[optional scope]: <gitmoji> <description>
```

### 4.2 PR Description Template

```markdown
## Summary

<One paragraph explaining the purpose and impact of the change.>

## Commits

- [`abc1234`](https://github.com/mguyard/hass-iopool/commit/abc1234) feat(sensor): ✨ Add pool mode sensor — short explanation
- [`def5678`](https://github.com/mguyard/hass-iopool/commit/def5678) docs(entities): 📝 Document pool mode sensor

## Tests

```
pytest tests/ -v
✅ N passed, ❌ 0 failed, ⚠️ 0 errors
```

## Related Issues

Closes #<issue_number>
```

> `## Tests` is **mandatory**. Run the pre-commit gate (§3) on the source branch before opening the PR. Fix all failures before opening.

### 4.3 Branch Rules

| Branch | Role |
|--------|------|
| `dev` | Development — **all PRs must target this branch** |
| `beta` | Beta releases — merged only by `semantic-release` CI |
| `main` | Stable releases — merged only by `semantic-release` CI |

- Never open a PR directly against `beta` or `main`.
- Never commit or push directly to `beta` or `main` — even if the VS Code session context reports `Current branch: beta`. Always verify with `git branch --show-current` (see §3.0).

### 4.4 Prepare PR Workflow

1. Ensure you are on the feature branch
2. Run pre-commit gate (§3) on the source branch
3. Run `git log origin/dev..HEAD --oneline` — list commits for the `## Commits` section
4. Run `git diff origin/dev --stat` — verify scope of changes
5. Produce PR title + description using the template (§4.2)
6. Target branch: **always `dev`**
