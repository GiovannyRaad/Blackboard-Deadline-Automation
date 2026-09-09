---
name: blackboard-deadlines
description: Read a student's Blackboard (LAU elearn) as structured JSON — upcoming assignment deadlines from the calendar, and recent activity stream posts where instructors announce exams, quizzes and materials. Use when asked what is due, what coursework is upcoming, or what is new on Blackboard.
---

# Blackboard

Two capabilities, both returning JSON on stdout:

1. **Deadlines** — due-date calendar items (`eventsFetcher.py`).
2. **Activity stream** — recent homepage posts (`streamFetcher.py`). Instructors
   often announce exams and quizzes here without ever setting a calendar due
   date, so check this as well as the deadlines.

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

Deadlines:

```bash
python skills/blackboard-deadlines/eventsFetcher.py
```

Activity stream — defaults to the last 7 days, `--days` widens the window:

```bash
python skills/blackboard-deadlines/streamFetcher.py
python skills/blackboard-deadlines/streamFetcher.py --days 30
```

Status messages go to stderr, so stdout is always parseable JSON.

Or import them:

```python
import eventsFetcher, streamFetcher
events = eventsFetcher.run(username, password, tmz)
posts = streamFetcher.run(days=7, username=username, password=password)
```

If the cached session stops working, `eventsFetcher` logs in again on its own.
To refresh the cookies by hand:

```bash
python skills/blackboard-deadlines/cookieFetcher.py
```

## Output

`eventsFetcher` returns an id-keyed mapping, one entry per upcoming deadline:

```json
{
  "0": {
    "title": "Assignment 3",
    "endDate": "2026-09-14T20:59:00.000Z",
    "course": "CSC 245 - Objected Oriented Programming"
  }
}
```

`streamFetcher` returns a list, newest first:

```json
[
  {
    "title": "First Quiz – Tuesday, September 15, 2026",
    "course": "Parallel Progg/Multic.&Cluster",
    "posted": "2026-09-08T11:01:04.445000+00:00",
    "type": "content",
    "body": "Dear Students, We will conduct the first quiz on ...",
    "url": null
  }
]
```

`type` is one of `announcement`, `content`, `grade`, `discussion`, `calendar`,
`blog`, `wiki`, `achievement`. Dates are ISO 8601 UTC — format them for display
before showing them to a user.

An empty result is a real answer: no deadlines due, or nothing posted in the
window.

## How it works

Three scripts, one job each:

- `eventsFetcher.py` — calls the calendar API and shapes the results.
- `streamFetcher.py` — calls the activity stream API and shapes the results.
- `cookieFetcher.py` — owns the login, and the `cookies.json` cache beside it.

Both fetchers try the cached cookies first, and ask `cookieFetcher` for a fresh
login through a headless Firefox SAML flow if the cache is missing or the API
rejects it.

The stream API primes its providers on the first POST and only returns entries on
a later one, so `streamFetcher` polls until entries arrive. It also needs an XSRF
token, which it scrapes from the stream page's HTML — there is no XSRF cookie.
Filtering by date happens client-side, so `--days` cannot reach further back than
the window Blackboard itself returns (roughly the last few dozen entries).

## Delivering reminders

This skill only reads deadlines. Sending them over WhatsApp is separate; see the
`whatsapp/` folder at the repo root.
