The connector name `agentmail` IS the CLI command on PATH. Never
invoke `npx agentmail-cli`, `agentmail-cli`, or any npm package
name — always just `agentmail`. The CLI is preconfigured with
`AGENTMAIL_API_KEY` from the connector slot, so you do not pass
`--api-key` at the command line.

─── Running commands non-interactively ──────────────────────────

Always invoke the CLI with this shape:

  PAGER=cat agentmail <root-flags> <resource> <subcommand> <subcommand-flags>

Three rules that bite if you get them wrong:

1. Disable the pager. When stdout is a TTY, the CLI may pipe
   output through `$PAGER` (default `less`) and hang waiting for
   keypresses. Prefix every invocation with `PAGER=cat` (or pipe
   to `| cat`).

2. Root flags go BEFORE the resource, subcommand flags go AFTER.
   `--format`, `--debug`, `--yes` / `-y` are root flags on
   `agentmail` itself — placing them after the subcommand makes
   them unknown flags.

3. Always request structured output. Pass `--format json` (single
   envelope) or `--format jsonl` (one record per line, easier to
   pipe). Never parse the human-readable default — it is for
   humans, not agents.

Confirm the exact subcommand surface with
`PAGER=cat agentmail --help` and `PAGER=cat agentmail <resource>
--help` on first use, then cache the resolved shape.

─── Resources you actually use ──────────────────────────────────

  inboxes        List, create, and read inboxes.
  threads        List threads in an inbox; read a single thread.
  messages       List messages in a thread; read a single
                 message; reply (with attachments) and mark read.
  webhooks       List, create, and delete webhook subscriptions.

─── First-fire bootstrap ────────────────────────────────────────

On the first webhook fire after deploy (no `inbox_id` in
`MEMORY.md`):

1. List inboxes:

     PAGER=cat agentmail --format json inboxes list

2. If exactly one inbox exists, use it. If none exist, create a
   dedicated scheduling inbox:

     PAGER=cat agentmail --format json inboxes create \
       --display-name "Scheduling agent"

   The CLI returns an inbox with `inbox_id` and `email`. Cache
   both into `MEMORY.md`.

3. If multiple inboxes exist, prefer the one whose username
   contains `schedul` or `book`; otherwise pick the first
   returned and cache it. The user can override by deleting the
   `inbox_id` line in MEMORY and re-firing.

─── Reading a thread ────────────────────────────────────────────

The webhook payload includes the message id and thread id.
Fetch the full thread so you have the full back-and-forth:

  PAGER=cat agentmail --format json threads get \
    --inbox $INBOX_ID \
    --id $THREAD_ID

Pick the latest inbound message (`from` ≠ inbox email) — that's
the one the requester just sent. Strip quoted-reply blocks (lines
prefixed with `>`) and signature blocks before classifying.

─── Replying with an .ics calendar invite ───────────────────────

The .ics format is plain text — RFC 5545. Email clients (Gmail,
Outlook, Apple Mail) auto-detect `text/calendar` attachments and
offer "Add to calendar" with one click. No external calendar API
required.

When the requester confirms a slot:

1. Build the .ics body. Substitute the four variables — title,
   start (in UTC), end (in UTC), and uid. The `start_iso` you
   collected from the agent's earlier offer must include the
   user's timezone offset (e.g. `2026-05-04T10:00:00-07:00`);
   convert to UTC for `DTSTART` / `DTEND` (suffix `Z`):

     BEGIN:VCALENDAR
     VERSION:2.0
     PRODID:-//AgentMail Scheduling Agent//EN
     METHOD:REQUEST
     CALSCALE:GREGORIAN
     BEGIN:VEVENT
     UID:<uuid>@agentmail-scheduling-agent
     DTSTAMP:<now-utc, basic format YYYYMMDDTHHMMSSZ>
     DTSTART:<start-utc, basic format YYYYMMDDTHHMMSSZ>
     DTEND:<end-utc, basic format YYYYMMDDTHHMMSSZ>
     SUMMARY:<meeting title — escape ; , \\ \\n>
     DESCRIPTION:<short description — same escaping>
     ORGANIZER;CN=<inbox-email>:mailto:<inbox-email>
     ATTENDEE;RSVP=TRUE;CN=<requester>;ROLE=REQ-PARTICIPANT:mailto:<requester>
     ATTENDEE;RSVP=TRUE;CN=<user-email>;ROLE=REQ-PARTICIPANT:mailto:<user-email>
     STATUS:CONFIRMED
     SEQUENCE:0
     END:VEVENT
     END:VCALENDAR

   Lines must be CRLF-separated. Escape `;`, `,`, `\\`, and
   newline characters in any quoted field.

2. Write the .ics to a temp file:

     ICS_FILE=$(mktemp -t invite.XXXXXX).ics
     cat > "$ICS_FILE" <<'EOF'
     ...the .ics body above...
     EOF

3. Reply with the attachment:

     PAGER=cat agentmail --format json messages reply \
       --inbox $INBOX_ID \
       --id $MESSAGE_ID \
       --text "$REPLY_BODY" \
       --cc $USER_EMAIL \
       --attach "$ICS_FILE"

   Verify the exact attachment flag with
   `agentmail messages reply --help` on first use — it may be
   `--attachment` or `--attach`. If the CLI does not accept a
   file path directly, fall back to the inline base64 form
   documented in `agentmail messages send --help` and adapt.

   `--cc` is omitted if the requester's email matches
   `$USER_EMAIL` (avoid CC'ing the user back to themselves).

4. Mark the inbound message read so duplicate webhook fires don't
   re-trigger:

     PAGER=cat agentmail messages update \
       --inbox $INBOX_ID \
       --id $MESSAGE_ID \
       --remove-label unread

─── Plain-text reply (offering slots, asking a question) ────────

When the agent is offering slots or asking a clarifying question
— no .ics yet — drop the `--attach` flag:

  PAGER=cat agentmail --format json messages reply \
    --inbox $INBOX_ID \
    --id $MESSAGE_ID \
    --text "$REPLY_BODY" \
    --cc $USER_EMAIL

Same `--cc` rule: skip if requester is the user.

─── Subscribing AgentMail webhooks to the agent ─────────────────

Once after deploy, the user (or the agent on first run) registers
a webhook so AgentMail starts pushing each new email:

  PAGER=cat agentmail webhooks create \
    --url "$AGENT_WEBHOOK_URL" \
    --event message.received

The agent webhook URL is shown in the dashboard after deploy.

─── Hygiene ─────────────────────────────────────────────────────

- Never call any send / reply / forward subcommand on a Slack
  *manual send* request without an explicit in-thread `👍` or
  "send" from the user. The webhook (auto-scheduling) flow is
  the only path that replies without a Slack confirm — and
  that's because the requester emailed the agent expecting a
  reply.
- Always pass `--format json` or `--format jsonl` for parseable
  output.
- Cache the resolved inbox id and email in `MEMORY.md` so
  subsequent webhooks skip discovery.
- Mark messages read after replying so duplicate webhooks
  de-duplicate cleanly.
- Redact obvious PII when re-posting email contents to a public
  Slack channel (mask the requester's address as
  `m***@example.com`). Full address is fine in a DM with the
  install user.
- Never echo the AgentMail API key in any output, log, or reply.
