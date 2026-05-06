"""
Tiny helper to build an iCalendar (.ics) invite from scratch.

The .ics format is plain text — RFC 5545. Email clients (Gmail, Outlook, Apple
Mail) auto-detect text/calendar attachments and offer "Add to calendar" with
one click. No external service or OAuth required.

Vendored from agentmail-to/agentmail-scheduling-agent (MIT). The upstream's
`_ics_escape` and `build_ics` are preserved verbatim. The upstream's
`ics_attachment` helper (which wraps the ICS in an AgentMail Python SDK
`SendAttachment`) is dropped — this template uses the `agentmail` CLI's
`--attach <path>` flag, not the Python SDK, so the wrapper isn't needed.

Usage (from the agent source root):

    python skills/scheduler/calendar_invite.py \\
      --title "Intro call" \\
      --start-iso "2026-05-04T10:00:00-07:00" \\
      --duration-minutes 30 \\
      --organizer scheduler@example.agentmail.to \\
      --attendee maya@example.com \\
      --attendee jane@example.com \\
      > /tmp/invite.ics

The `start_iso` value MUST include the timezone offset. Falling back to
UTC silently is a footgun — the agent should reject any classifier output
that doesn't include the offset.
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from typing import Iterable
from uuid import uuid4


def _ics_escape(text: str) -> str:
    """Escape iCal special chars (RFC 5545 §3.3.11)."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def build_ics(
    title: str,
    start_iso: str,
    duration_minutes: int,
    organizer_email: str,
    attendees: Iterable[str],
    description: str = "",
) -> str:
    """Build a VEVENT iCalendar string for a single meeting."""
    start = datetime.fromisoformat(start_iso)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    end = start + timedelta(minutes=duration_minutes)

    fmt = "%Y%m%dT%H%M%SZ"
    dtstart = start.astimezone(timezone.utc).strftime(fmt)
    dtend = end.astimezone(timezone.utc).strftime(fmt)
    dtstamp = datetime.now(timezone.utc).strftime(fmt)

    attendee_lines = [
        f"ATTENDEE;RSVP=TRUE;CN={a};ROLE=REQ-PARTICIPANT:mailto:{a}"
        for a in attendees
        if a
    ]

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AgentMail Scheduling Agent//EN",
        "METHOD:REQUEST",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{uuid4()}@agentmail-scheduling-agent",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{_ics_escape(title)}",
        f"DESCRIPTION:{_ics_escape(description)}",
        f"ORGANIZER;CN={organizer_email}:mailto:{organizer_email}",
        *attendee_lines,
        "STATUS:CONFIRMED",
        "SEQUENCE:0",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    # iCal lines should be CRLF-separated.
    return "\r\n".join(lines) + "\r\n"


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an .ics calendar invite and write it to stdout.",
    )
    parser.add_argument("--title", required=True, help="Meeting subject")
    parser.add_argument(
        "--start-iso",
        required=True,
        help="ISO 8601 start with timezone offset, e.g. 2026-05-04T10:00:00-07:00",
    )
    parser.add_argument(
        "--duration-minutes", type=int, required=True, help="Meeting length"
    )
    parser.add_argument(
        "--organizer", required=True, help="Organizer email (the agent's inbox)"
    )
    parser.add_argument(
        "--attendee",
        action="append",
        default=[],
        dest="attendees",
        help="Attendee email — pass once per attendee",
    )
    parser.add_argument(
        "--description", default="", help="Optional event description"
    )
    args = parser.parse_args()

    if "+" not in args.start_iso and "-" not in args.start_iso[10:]:
        print(
            "error: --start-iso must include a timezone offset (e.g. -07:00)",
            file=sys.stderr,
        )
        return 2

    ics = build_ics(
        title=args.title,
        start_iso=args.start_iso,
        duration_minutes=args.duration_minutes,
        organizer_email=args.organizer,
        attendees=args.attendees,
        description=args.description,
    )
    sys.stdout.write(ics)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
