---
name: blackboard-deadlines
description: Fetch upcoming assignment deadlines from Blackboard (LAU elearn) as structured JSON. Use when asked for upcoming coursework, due dates, assignment deadlines, or what is due on Blackboard.
---

# Blackboard Deadlines

Fetches due-date calendar items from Blackboard Ultra and returns them as structured data.

## Requirements

Environment variables, read from `.env` in this folder (copy `.env.example`):

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
python skills/blackboard-deadlines/eventsFetcher.py
```

Or import it:

```python
import eventsFetcher
events = eventsFetcher.run(username, password, tmz)
```

If the cached session stops working, `eventsFetcher` logs in again on its own.
To refresh the cookies by hand:

```bash
python skills/blackboard-deadlines/cookieFetcher.py
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

Two scripts, one job each:

- `eventsFetcher.py` — calls the calendar API and shapes the results.
- `cookieFetcher.py` — owns the login, and the `cookies.json` cache beside it.

`eventsFetcher` tries the cached cookies first. If the cache is missing, or the API
answers 401/403, or no events come back, it asks `cookieFetcher` for a fresh login
through a headless Firefox SAML flow and retries once.

## Delivering reminders

This skill only reads deadlines. Sending them over WhatsApp is separate; see the
`whatsapp/` folder at the repo root.
