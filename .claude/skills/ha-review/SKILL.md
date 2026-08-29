---
name: ha-review
description: Reviews code changes and pull requests for hass-iopool with a consistent contract and output format. Covers reviewing a working tree, a branch, or a GitHub PR, and auditing whether existing review comments have been addressed.
---

# Review Code Changes — hass-iopool

Adapted from the Home Assistant core review skill. Use it whenever a review is requested, on a branch, on uncommitted work, or on a pull request.

## Scope

Unless told otherwise, review the full change — the branch plus anything uncommitted — against the target branch. `dev` is the default base here; a PR's base comes from `gh pr view`. This repository has a single remote, so resolve the base as `origin/<base>` and fall back to the local branch:

```bash
BASE=origin/dev
git diff "$(git merge-base "$BASE" HEAD)"
```

## Reviewing a pull request

```bash
gh pr view <n>          # title, description, base branch
gh pr diff <n>          # the change itself
gh pr checks <n>        # whether CI already caught something
```

Pass the PR's actual base to the diff step rather than assuming `dev`.

Read the description critically. A claim in a PR body is not evidence: this repository has already received a PR whose stated test environment was impossible on the declared Python version. Check what the description asserts against what the repository actually does.

## Auditing existing review comments

Run this when checking whether feedback has been handled, either alone or as part of a full review:

```bash
gh api repos/mguyard/hass-iopool/pulls/<n>/comments --paginate
```

Flag a comment when it has not been addressed, and when the author replied without implementing the suggestion — summarise the reply in that case. Flag comments where the author asked for clarification. Do not list comments that were addressed. Include a link for each one flagged.

## What to look for

- Correctness and edge cases, especially error paths
- Consistency with the invariants in `ha-integration-knowledge`
- Performance and blocking calls in async context
- Security: never a secret in a log, an event payload or a diagnostics dump
- Test coverage of what changed, and whether the new tests are load-bearing
- Documentation under `docs/` when behaviour or a contract changed

If the change touches `quality_scale.yaml`, verify each added or modified rule with the `ha-quality-scale-verify` skill and fold the result into the review.

If the change touches filtration scheduling, ask whether unit tests alone can prove it — see `live-validation-hass-iopool`.

## Verification

After drafting the findings, re-check each one before reporting it. Prefer disproving your own finding to reporting it optimistically: a plausible-but-wrong finding costs the reader more than a missed nitpick. State a finding as confirmed only when you can name the input that triggers it and the resulting behaviour.

## Rules

- **Review only. Make no changes.**
- Report in the console. Do not post to GitHub unless explicitly asked.
- Be specific and constructive. Suggest an improvement rather than only naming a problem.
- Do not highlight what is already fine.
- No need to run tests or linters — CI does that. Read the code.

## Output format

List findings per file and line, then close with an overall assessment.

```
Overall assessment: request changes.
- [CRITICAL] filtration.py:143 - pump never stops when the sensor reads "unavailable"
- [PROBLEM] coordinator.py:87 - blocking call inside an async method
- [SUGGESTION] test_init.py:45 - parametrise instead of duplicating the body
```

Use `approve`, `request changes`, or `comment` as the assessment. Always include file and line where possible.
