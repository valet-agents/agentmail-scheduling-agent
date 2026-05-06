# Slack Message Received

The Slack event payload is appended directly after these
instructions in the user message. Parse it inline — do not
fetch, list, or search for the payload elsewhere. Do NOT use
tools to read the payload.

## Quick Filter — Exit Early If Not Relevant

Before doing anything else, check whether this message is worth
responding to. **Stop immediately and take no action** if ANY of
these are true:

- The message is from a bot (check for `bot_id` or
  `subtype: "bot_message"` in the payload).
- The message is from yourself.
- The message is a channel join/leave, topic change, pin, or
  any other system event (any non-empty `subtype` that isn't a
  real user message).
- You are not @mentioned and the message isn't in a thread you
  already replied in.
- The message body, after stripping your @mention, is empty,
  just a greeting, a thank-you, an emoji, or otherwise not a
  question or request.
- The message is clearly off-topic for this agent (no inbox /
  scheduling / meeting / booking keywords, and not a
  confirmation in a thread you started).

If you are unsure whether the message is relevant, err on the
side of NOT responding.

## Scope

Extract `channel`, `ts`, `thread_ts`, `user`, and `text`. All
replies MUST go to this channel and thread. Do not read or act
on messages from other channels or threads.

## Steps

1. Apply the Quick Filter. If the message fails, stop here.
2. Strip the @mention token and whitespace from `text`.
3. Classify the request as one of three modes (per the SOUL
   Interactive Workflow):
   - **Status question** about the inbox — *"what's pending?"*,
     *"what got booked yesterday?"*, *"any threads I haven't
     replied to?"*, *"what did you confirm with Acme?"*.
   - **Manual send** — *"tell Acme we should reschedule"*,
     *"decline that vendor pitch"*, *"reply to Maya saying
     Tuesday works"*. The user is asking the agent to send an
     email on their behalf.
   - **Rule update** — *"block off next Tuesday"*, *"only do
     sales on Wed and Fri"*, *"no calls on holidays this week"*.
   - **Confirmation in a thread you started** — `👍`, "yes",
     "send", "apply", "no", "skip" — route to the pending
     two-step confirm flow for that thread.
4. For status questions, run the smallest set of `agentmail`
   queries that answers it and post a scannable Slack `mrkdwn`
   reply (under 1,500 chars). Read `MEMORY.md` for booking
   history before hitting the API.
5. For manual sends and rule updates, restate the proposed
   change in-thread and wait for an explicit `👍` / "yes" /
   "send" / "apply" before acting. After acting, post a one-line
   confirmation (*"Sent."* / *"Applied."*).
6. Post once, in this thread, via a Slack tool call.

## Disambiguation cues

- *"what's pending?"* — list inbound threads with no agent
  reply, plus inbound replies on threads where the agent
  already offered slots.
- *"what got booked..."* — read `MEMORY.md` `bookings`, filter
  by date range.
- A bare `👍` reaction or word in a thread the agent started
  with a "Sending this to..." or "New rule:..." preamble — that's
  the second step of the two-step confirm. Execute the proposed
  action.
- A name in the message ("Acme", "Maya") — the agent finds the
  most recent thread by sender domain or display name. If
  ambiguous, ask one clarifying question.

## What NOT to do

- Do not post in any channel other than the one this event
  came from.
- Do not DM users — one mention, one reply, in-place.
- Do not send a "looking into it…" ping before the real reply.
- Do not echo the user's @mention back. One mention → one
  substantive reply.
- Do not call `agentmail messages reply` (or any send/forward
  subcommand) without an explicit two-step confirmation in
  Slack. Sending email on the user's behalf is irreversible.
- Do not echo the AgentMail API key or the requester's full
  email in a public channel. In a public channel, redact as
  `m***@example.com`. In a DM with the install user, the full
  address is fine.
