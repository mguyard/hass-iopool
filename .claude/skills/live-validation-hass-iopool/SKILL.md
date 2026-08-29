---
name: live-validation-hass-iopool
description: Proving a filtration or scheduling change works against a running Home Assistant, whatever the hosting — what the environment must provide, driving HA over the REST API, forcing entity states at a precise minute tick, and the scenario catalogue. Mandatory before a pull request that changes runtime behaviour.
---

# Live Validation — hass-iopool

Unit tests are necessary here but not sufficient. Filtration is driven by a real clock through `async_track_time_change`, and three defects have hidden in that gap where no unit test could see them:

- the winter end time was never rounded, so the stop fired a minute late roughly half the time, decided by the sub-second offset of the periodic check;
- a retried slot start published UTC timestamps instead of local ones, because `async_call_later` and `async_track_time_change` pass different time zones;
- a symptom described in a commit message as a retry loop was in fact a frozen state — the pump stopped, but the end event never fired.

Use this skill whenever a change touches scheduling, the stop path, or sensor reads that feed either.

---

## 1. What the environment must provide

Any real Home Assistant works. The method below goes through the REST API, so it does not care how the instance is hosted. It needs four things:

1. **A running Home Assistant with the integration loaded**, configured against an iopool account.
2. **A `switch` entity to act as the pump.** `async_start_filtration` and `async_stop_filtration` call `switch.turn_on` / `switch.turn_off` by name, so an `input_boolean` alone will not do. A template switch driving an `input_boolean` is the easiest stand-in, and lets you flip the pump by hand.
3. **`recorder` enabled** — the elapsed filtration sensor is built on `history_stats`, which queries it.
4. **Read access to `home-assistant.log`**, with `custom_components.iopool` at `debug`:

```yaml
logger:
  default: info
  logs:
    custom_components.iopool: debug
```

### Reaching your instance

Every command below is shown as a plain `curl` against `http://localhost:8123`. Adapt the prefix to where your instance lives:

| Setup | Prefix |
|---|---|
| Home Assistant on this machine | none — call `localhost:8123` directly |
| Any container | `docker exec <container> bash -lc '...'` |
| Remote instance | replace the host, or run the commands over SSH |

For a container, resolve it by image rather than hard-coding an id, which changes on every rebuild. The maintainer uses a Home Assistant devcontainer, where that is:

```bash
C=$(docker ps --format '{{.ID}} {{.Image}}' | awk '/vsc-home-assistant-dev/ {print $1}')
```

### Picking up code changes

**A code change requires a Home Assistant restart.** Reloading the config entry re-runs `async_setup_entry` but does not re-import Python modules. An **options** change is different: `__init__.py` calls `async_reload`, so it takes effect immediately — which is what makes the scenario loop below fast.

How the new code reaches the instance depends on your setup: a bind mount from the working tree makes a `git checkout` enough, otherwise copy `custom_components/iopool/` into the config folder. The maintainer's devcontainer bind-mounts it read-write, so no copy step is involved.

> **Ask the human to restart Home Assistant. Do not restart it yourself** — they usually follow the logs live and want to watch the same run.

## 2. Driving Home Assistant

Everything below goes through the REST API, which needs a long-lived access token.

### Creating the token

It lives in `/tmp/ha_token` **inside the container**, so it is lost whenever the devcontainer is rebuilt — and every call in this skill then fails with `401`. Recreating it takes under a minute, and the user must do both steps because the first one is in the UI:

1. In Home Assistant, open the profile menu (bottom left, click the user name) → **Security** tab → **Long-lived access tokens** → **Create token**. Name it something like `claude-code`. The value is shown **once**.
2. Ask the user to store it without it passing through the conversation:

```bash
read -rs T && echo "$T" > /tmp/ha_token && chmod 600 /tmp/ha_token
# in a container: docker exec -it $C bash -lc 'read -rs T && echo "$T" > /tmp/ha_token && chmod 600 /tmp/ha_token'
```

`read -rs` does not echo, so the token never reaches the terminal output or this transcript. Check it exists before starting a campaign:

```bash
test -s /tmp/ha_token && echo "token present" || echo "token ABSENT — ask the human to recreate it"
```

> Do not create the token yourself, do not read its contents, and never print it. Reference it only by substitution, as below. If a command would expose it, redirect that output to `/dev/null`.

### Using the token

```bash
A="Authorization: Bearer $(cat /tmp/ha_token)"
curl -s -H "$A" http://localhost:8123/api/states/<entity_id>
```

A quick sanity check that the token is valid:

```bash
curl -s -H "$A" http://localhost:8123/api/
# {"message": "API running."}
```

Storing the token in `/tmp` is a choice, not a requirement — it simply means it disappears on a container rebuild. Anywhere outside the git repository works.

Useful endpoints:

| Goal | Call |
|---|---|
| Read a state | `GET /api/states/<entity_id>` |
| Call a service | `POST /api/services/<domain>/<service>` |
| **Force a state** | `POST /api/states/<entity_id>` with `{"state": ..., "attributes": {...}}` |
| Change integration options | the options flow, see §3 |

`POST /api/states/` writes straight into the state machine. The entity object is unaware and will overwrite it on its next `async_write_ha_state()` — which is exactly what makes the forcing temporary, and what makes §4 necessary.

---

## 3. Changing integration options

The options flow is reachable over REST and triggers a reload, so no restart is needed. Find the entry id once:

```bash
python3 -c "
import json
d = json.load(open('<config>/.storage/core.config_entries'))
print([(e['entry_id'], e['title']) for e in d['data']['entries'] if e['domain'] == 'iopool'])"
```

`<config>` is the Home Assistant configuration directory — `/config` in a container, `~/.homeassistant` for a core checkout, `config/` inside a devcontainer workspace.

Then `POST /api/config/config_entries/options/flow` with `{"handler": "<entry_id>"}` and submit the returned `flow_id` with a `filtration` section holding **every** flat key — omitted keys are not preserved. Read the current values from `.storage/core.config_entries` and patch only what changes.

**Constraints that will bite:**

- `slot1.start` must be strictly before `slot2.start`, else the flow returns `slot1_start_greater_than_equal_slot2_start`.
- To neutralise a slot, give it a time already past today — the trigger reschedules for tomorrow.
- Slot duration is `round(max_duration × duration_percent / 100)`, the API recommendation being clamped by `max_duration`. Drive `max_duration` to get 1–3 minute slots.
- The elapsed filtration sensor **accumulates from midnight**. Always read it before sizing a scenario that depends on a deficit, and never predict a percentage from an earlier run.
- Restore the original options at the end of a campaign, and say so.

---

## 4. Forcing a state at a precise tick

The periodic check runs at `second=0` with a sub-second offset of its own, and the history_stats coordinator rewrites the elapsed sensor roughly 50 ms before the check reads it. A single write loses that race. Hammer a short window around the tick instead:

```python
# every 20-30 ms for a few seconds, starting ~3 s before the target minute
while time.time() < end:
    urllib.request.urlopen(urllib.request.Request(
        f"http://localhost:8123/api/states/{eid}",
        data=json.dumps({"state": value, "attributes": attrs}).encode(),
        headers=H, method="POST"))
    time.sleep(0.02)
```

Cover several consecutive ticks when the scenario needs the outage to last. Afterwards, either let the entity's own coordinator restore it, or `POST` the real value back — the iopool coordinator only refreshes every 300 s, so waiting can take longer than the scenario.

The log line the code emits when it reads the state is the proof the forcing landed. Check it rather than assuming.

---

## 5. Scenario catalogue

Play each one **twice**: once against the unfixed code, once against the fix. A scenario that is not run before the change proves nothing about it.

| # | Setup | What it exercises |
|---|---|---|
| W1 | `Active-Winter`, start `+3 min`, duration 3 | Nominal winter cycle, objective published in the end event |
| W2 | W1 + elapsed sensor forced unreadable on the end tick | Stop path with no usable reading |
| S1 | `Standard`, slot 1 of 3 min | Nominal slot 1 |
| S2 | S1 + slot 2 sized to leave a deficit | The slot 2 catch-up branch |
| S3 | Elapsed sensor lost **after** the catch-up push | Stop at a deadline already computed and persisted |
| S4 | Elapsed sensor lost **at** the scheduled end | Catch-up skipped, normal stop |
| S5 | Slot 1, elapsed sensor unreadable at the end | End event and attribute clearing |
| J1 | Slot 1, elapsed sensor forced to `abc` | A value outside the `unavailable`/`unknown` pair |
| I1 | Recommendation sensor unreadable at a slot **start** | Start path, retry chain |

S3 and S4 look alike and are not: in S4 the integration knows nothing and extends blindly; in S3 it had computed the exact deadline a minute earlier from good data. Both must be checked.

---

## 6. Collecting evidence

Mark the log before each scenario, then read only what was added:

```bash
LOG=<config>/home-assistant.log
wc -l < "$LOG" > /tmp/mark
tail -n +$(cat /tmp/mark) "$LOG" \
  | grep -E "custom_components.iopool.filtration" \
  | grep -iE "Firing event|Stopping|Starting|Remaining|Ajusting|ERROR|WARNING|retrying"
```

With `custom_components.iopool` at `debug` (§1), `publish_event` logs the full event payload, so there is no need to listen on the bus.

After a failure scenario, check the residual attributes — a lost end event leaves them stale:

```bash
curl -s -H "$A" http://localhost:8123/api/states/binary_sensor.iopool_<pool>_filtration \
  | python3 -c "import json,sys;a=json.load(sys.stdin)['attributes'];print('next_stop_time' in a, 'active_slot' in a)"
```

When comparing a run against an earlier one, ignore `day_filtration_elapsed_minutes` and `day_filtration_elapsed_percent` in absolute terms: the elapsed sensor accumulates from midnight and the campaign itself runs the pump, so a payload reading `percent: 125` on the second run says nothing about a regression. Compare what does not depend on that accumulation — which source the objective came from, whether the event fired at all, `null` against `0`, whether the attributes were cleared, and which tick the stop landed on.

> **Before quoting a log line anywhere public** — issue, PR, commit — replace the
> pool name in entity ids with `mypool`, and drop every `coordinator` line: those
> carry the pool id and a truncated API key.
