---
name: blackboard-deadlines
description: Fetch upcoming assignment deadlines from Blackboard (LAU elearn) as structured JSON. Use when asked for upcoming coursework, due dates, assignment deadlines, or what is due on Blackboard.
---

# Blackboard Deadlines

Fetches due-date calendar items from Blackboard Ultra and returns them as structured data.

## Requirements

Environment variables:

- `UNI_USER` — Blackboard username
- `UNI_PASS` — Blackboard password
- `TIMEZONE` — IANA timezone used to compute "today" (e.g. `Asia/Beirut`)

Dependencies: `pip install -r requirements.txt`, then install the browser the
fallback drives:

```bash
playwright install firefox
```

## Usage

Run standalone to print JSON to stdout:

```bash
python skills/blackboard-deadlines/headlessEventsFetcher.py
```

Or import it:

```python
import headlessEventsFetcher
events = headlessEventsFetcher.run(username, password, tmz)
```

## Output

An id-keyed mapping, one entry per upcoming deadline:

```json
{
  "0": {
    "title": "Assignment 3",
    "endDate": "2026-09-14T20:59:00.000Z",
    "course": "CSC 245 - Objected Oriented Programming"
  }
}
```

`endDate` is ISO 8601 UTC. Format it for display before showing it to a user.

## How it works

1. Reuses cached session cookies from `cookies.json` (written next to this file).
2. If those are missing or return no results, logs in through a headless Firefox
   SAML flow driven by Playwright, re-caches the cookies, and retries.

`eventsFetcher.py` is an in-progress pure-`requests` version of the SAML login that
avoids the browser dependency. It is exploratory and runs at import — not wired in.

## Delivering reminders

This skill only reads deadlines. Sending them over WhatsApp is separate; see the
`whatsapp/` folder at the repo root.
