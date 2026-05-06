This folder contains the source for a Skilled Agent originally built for the Valet runtime. Changes should follow the Skilled Agent open standard.

Ported from the upstream [AgentMail Scheduling Agent](https://github.com/agentmail-to/agentmail-scheduling-agent) (MIT). Same product idea — an inbox that books your meetings — re-architected on top of the Valet platform: webhooks instead of polling, Slack as the operator console, the API key collected via a connector slot at deploy, and everything else (name, email, timezone, scheduling rules) edited in `SOUL.md` before deploy.

## Setup

### Connectors

- **agentmail**: The AgentMail CLI, preconfigured via the connector's `slot_descriptions.AGENTMAIL_API_KEY`. The connector name `agentmail` IS the CLI command on PATH — invoke it as `agentmail`, never as `npx agentmail-cli` or any npm package name. The agent uses it to list/create the dedicated inbox, list threads, read messages, and reply with the .ics invite attached. See `skills/agentmail/SKILL.md` for invocation patterns.

| Slot | Description |
|------|-------------|
| `AGENTMAIL_API_KEY` | API key minted at agentmail.to (Settings → API Keys). Pasted during the deploy flow. |

The .ics body itself is built by `skills/scheduler/calendar_invite.py` — a stdlib-only Python helper vendored verbatim from the upstream AgentMail template. It runs as `python3 skills/scheduler/calendar_invite.py --title ... --start-iso ... > /tmp/invite.ics`, rejects bare ISO strings without a timezone offset, and writes RFC 5545 to stdout. Requires `python3` on the agent runtime — no `pip install` needed.

### Channels

- **slack** (slack): The agent's per-agent Slack bot — your console for the inbox. Listens for @mentions and replies in-thread. Three modes: status questions ("what's pending?"), manual sends ("decline that vendor pitch"), and rule updates ("block off Tuesday"). All sends require an explicit two-step confirm. Slack writes use the auto-injected outbound Slack connector.
- **webhook** (webhook): The generic webhook channel. AgentMail pushes each `message.received` event to the agent's webhook URL, and the agent's per-event reply flow runs on receipt — see `channels/webhook.md`.

### Secrets

- **AGENTMAIL_API_KEY** — the only secret. Collected at deploy time via the `agentmail` connector's `slot_descriptions.AGENTMAIL_API_KEY` entry in `valet.yaml`. Sourced from the AgentMail dashboard at agentmail.to.

The Slack bot is provisioned via OAuth in the dashboard, so no other secrets are required. Per-user values (your name, email, timezone, scheduling rules) are NOT secrets — they live in the Configuration section at the top of `SOUL.md` and are edited before deploy.

### External Setup

1. Sign up for AgentMail at agentmail.to, mint an API key (Settings → API Keys), and paste it into the `AGENTMAIL_API_KEY` slot during deploy. The agent creates its own dedicated scheduling inbox the first time the webhook fires — you don't need to create one upfront.
2. **Open `SOUL.md` and edit the Configuration section at the top** — name, email, timezone, scheduling rules. Each user-editable value is marked `<EDIT — ...>` so it's impossible to miss. Save before clicking deploy. The agent reads these values on every fire.
3. Install the agent's Slack bot from the dashboard. Invite it to one channel where you want a window into the inbox. Status questions, manual sends, and rule updates all happen via @mention in that channel.
4. After deploy, copy the agent's webhook URL from the dashboard, then run this once from your terminal (with your AgentMail API key in the environment):

   ```sh
   PAGER=cat agentmail webhooks create \
     --url "<agent-webhook-url>" \
     --event message.received
   ```

   AgentMail starts pushing each new email to the agent in real time. Test by sending an email to the agent's inbox address (you'll see it printed in the agent's first run log, or via `agentmail inboxes list`).

You can also update the scheduling rules at runtime by @mentioning the Slack bot ("only do sales on Wed and Fri") — the agent persists overrides to `MEMORY.md` and reads from there first, falling back to the SOUL.md Configuration section.

## Customizing

- **Change the scheduling rules**: edit the *Scheduling rules* section of `SOUL.md` to reset the defaults, or @mention the Slack bot at runtime ("only do sales on Wed and Fri") and the agent persists the override to `MEMORY.md`. From the next webhook onwards the agent reads from `MEMORY.md` first, falling back to SOUL defaults.
- **Tighten or loosen the OOO regex**: the *Quick Filter* in `channels/webhook.md` ignores out-of-office bounces. Add patterns for languages or templates your inbox sees regularly.
- **Adjust the `--earliest slot offered`**: SOUL Phase 4 says "at least 24 hours out". Bump to 48h for a longer prep window, or to 1h for same-day scheduling.
- **Change the email-reply word cap**: SOUL Phase 6 caps replies at 100 words. Drop to 60 for a tighter voice, raise for a more conversational one.
- **Pin a specific inbox**: if your AgentMail account already has multiple inboxes and you don't want auto-creation, set the `INBOX_ID` env var on the agent (or pre-populate `MEMORY.md` `inbox_id`). The first-fire bootstrap in `skills/agentmail/SKILL.md` will skip discovery.
- **Drop Slack entirely**: this template defaults to a Slack-as-console UX. If you want a purely email-driven agent (no Slack at all), remove the `slack` channel from `valet.yaml`, drop `channels/slack.md`, and trim the *Interactive Workflow* section from `SOUL.md`. The webhook flow runs unchanged.
