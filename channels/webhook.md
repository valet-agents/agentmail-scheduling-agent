# AgentMail Webhook (`message.received`)

The webhook payload is appended directly after these instructions
in the user message. Parse it inline — do not refetch the message
via the API. The payload is a JSON object with at least
`event_type: "message.received"` and `message: { ... }`.

## Quick Filter — Exit Early If Not Relevant

Before doing anything else, check whether this event is worth
acting on. **Stop immediately and take no action** if ANY of
these are true:

- `event_type` is anything other than `message.received`.
- `message.from` matches the agent's own inbox address (echo /
  loop guard — sent mail occasionally re-fires).
- `message.from` matches the user's address (the **Your email**
  value in the Configuration section at the top of `SOUL.md`) —
  they CC'd themselves on a reply, not a scheduling request.
- The message has an out-of-office indicator (the `auto-replied`
  header, an `Auto-Submitted: auto-replied` value, or a body
  matching the OOO regex below).
- The message is a delivery-failure bounce (`mailer-daemon@`,
  `postmaster@`, or `Subject: Undelivered Mail Returned to
  Sender`).
- The body, after stripping signature and quoted-reply blocks,
  is empty or contains no schedulable intent (a thank-you, a
  one-word "ok", a forward with no instruction).
- A booking for `message.message_id` already exists in
  `MEMORY.md` `bookings` (this webhook is a duplicate fire).

If you are unsure whether the message is relevant, err on the
side of NOT replying. It's better to miss one and let the user
@mention "what's pending" later than to send an off-tone reply.

OOO regex (case-insensitive, match anywhere in the body):
`out of (the )?office|on vacation|away from email|out until|annual leave`.

## Steps

1. Apply the Quick Filter. If the message fails any check, stop.
2. Resolve the inbox: read `MEMORY.md` `inbox_id`. If unset, run
   the agentmail discovery flow (see `skills/agentmail/SKILL.md`)
   and cache.
3. Fetch the full thread via `agentmail threads get` so you have
   the complete back-and-forth. Strip quoted-reply blocks and
   signatures from each message.
4. Decide which phase of the SOUL Workflow this is in:
   - **No prior agent reply on this thread** → Phase 3
     (classify) → Phase 4 (offer 3 slots).
   - **The latest agent reply offered slots, current message is
     none-of-them** → another Phase 4 round (offer 3 different
     slots, different days). After 2 such rounds, switch to
     "ask the requester to suggest a time".
   - **The latest agent reply offered slots, current message
     accepts one of them (or proposes a specific time that
     verifies against the rules)** → Phase 5 (confirm + .ics
     attached).
   - **The thread already has a confirmed booking in
     `MEMORY.md`** → only reply if the requester is asking a
     follow-up question; otherwise stop.
5. Reply in-thread with `agentmail messages reply`. CC the user
   (skip if requester is the user). Attach the .ics on
   confirmation.
6. Mark the inbound message read so duplicate webhook fires don't
   re-trigger the flow.
7. Update `MEMORY.md` — `bookings` on confirmation, otherwise
   nothing.

## What NOT to do

- Do not refetch the message body — it's already in the payload.
- Do not list the entire inbox; only the thread for this event.
- Do not send a status update to Slack on every webhook fire.
  Slack visibility is on-demand: the user @mentions "what's
  pending?" when they want to see.
- Do not retry on transient failures inside the webhook handler.
  The next webhook (or the user's "what's pending?" check) is
  the recovery.
