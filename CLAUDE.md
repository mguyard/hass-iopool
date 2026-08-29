# CLAUDE.md

@AGENTS.md

The file above holds every repository rule and is shared with other agents. What follows applies to Claude Code only.

## Tooling

- **`gh` is installed and is the way to reach GitHub** — issues, PRs, comments, checks, API calls. There is no MCP GitHub server configured here.
- Use `AskUserQuestion` when a decision is genuinely the user's to make. Do not ask about choices that have an obvious default or facts the repository can answer.
- Context7 is available for library documentation. Prefer it over web search for Home Assistant, aiohttp or voluptuous/Probatio APIs.

## Skills

Project skills live in `.claude/skills/` and load on demand:

| Skill | Load it for |
|---|---|
| `ha-integration-knowledge` | Any implementation in `custom_components/iopool/` — architecture, invariants, HA expectations |
| `testing-hass-iopool` | Running or writing tests, devcontainer setup |
| `live-validation-hass-iopool` | Proving a fix works in a real Home Assistant |
| `git-conventions` | Commits, PRs, branch rules |
| `docs-hass-iopool` | Anything under `docs/` |
| `ha-review` | Reviewing a change or a pull request |
| `ha-quality-scale-verify` | Auditing a quality-scale rule against the code |

Load `ha-integration-knowledge` first for work in the integration, and pair it with the narrower skill for the task at hand.

## Writing to GitHub

- **Never self-reference in commits.** No `Co-Authored-By: Claude`, no `Claude-Session:` trailer, no mention of the assistant or the session — in commit messages, PR bodies or issue text. Only add them if asked for a specific commit.
- **Correct a mistake in an issue or PR by editing the body**, and delete any correction comment already posted. An issue is a specification, not a conversation log. Once a discussion is under way, say in the thread that the body changed rather than editing silently.
- **Never publish personal data.** The pool name, the pool id, the config entry id and the API key must not appear in an issue, a commit, a PR or a published page. Anonymise entity ids to `sensor.iopool_mypool_*` or `<pool>`, and never quote a `coordinator` log line — it carries the pool id and a truncated key.
- Ask before any outward-facing action: opening or closing an issue or PR, posting a comment, pushing to a shared branch.

## Verifying

The user expects claims to be checked, not asserted. Read the code, run the command, measure it on the live instance. When a measurement contradicts an earlier statement, say so plainly and correct it.

For anything touching filtration scheduling, unit tests are necessary but not sufficient: everything is driven by a real clock through `async_track_time_change`, and defects have hidden there that no unit test could see. See `live-validation-hass-iopool`.

## Committing

Do not commit or push unless asked. The user reviews changes first.
