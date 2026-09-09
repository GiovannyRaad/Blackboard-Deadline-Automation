---
name: blackboard
description: Read a student's LAU Blackboard as JSON — upcoming assignment deadlines from the calendar, and recent activity stream posts where instructors announce exams, quizzes, and materials. Use when asked what is due, what coursework or exams are coming up, whether anything was posted or announced, or to check Blackboard generally.
---

# Blackboard

Reads one student's Blackboard account. There are two independent sources of
information, and they do not overlap:

| Source | Script | Holds |
|---|---|---|
| Calendar | `eventsFetcher.py` | Items with a real **due date** set by the instructor |
| Activity stream | `streamFetcher.py` | Everything posted to the homepage: announcements, uploaded files, exam and quiz notices |

`cookieFetcher.py` is the shared login. It is not a source of information.

## Which one to run

- **"What's due?" / "any assignments due?"** → `eventsFetcher.py`
- **"What's new?" / "did anything get posted?" / "check my Blackboard"** → `streamFetcher.py`
- **"What's coming up?" / "any exams or quizzes?" / "anything I should know about?"** → **run both**

Read that last case carefully, because it is the common one and the calendar
alone will mislead you. **Instructors routinely announce exams in the stream
without ever setting a calendar due date.** A real example from this account: the
calendar returned `{}` — nothing due at all — while the stream carried a quiz
scheduled six days later. Answering "nothing is due" from `eventsFetcher` alone
would have been wrong.

So whenever the question is about what is *coming up*, rather than strictly what
has a *due date*, check the stream too.

## Running them

Both print JSON to **stdout**; progress messages go to **stderr**. Parse stdout.

```bash
python skills/blackboard/eventsFetcher.py

python skills/blackboard/streamFetcher.py            # last 7 days
python skills/blackboard/streamFetcher.py --days 30  # wider window
```

They work from any directory. Or import them:

```python
import eventsFetcher, streamFetcher
events = eventsFetcher.run(username, password, tmz)
posts  = streamFetcher.run(days=7, username=username, password=password)
```

**Expect ~2-6 seconds** on a warm cookie cache. If the cache is stale the script
logs in through a headless browser first and takes **~40 seconds** — that is
normal, not a hang. Do not kill it and do not retry.

## Reading the output

`eventsFetcher` — an id-keyed mapping, one entry per upcoming deadline:

```json
{
  "0": {
    "title": "Assignment 3",
    "endDate": "2026-09-14T20:59:00.000Z",
    "course": "CSC 245 - Object Oriented Programming"
  }
}
```

`streamFetcher` — a list, newest first:

```json
[
  {
    "title": "First Quiz \u2013 Tuesday, September 15, 2026",
    "course": "Parallel Progg/Multic.&Cluster",
    "posted": "2026-09-08T11:01:04.445000+00:00",
    "type": "content",
    "body": "Dear Students, We will conduct the first quiz on Tuesday September 15 ...",
    "url": null
  }
]
```

### Things that will trip you up

**`type` does not tell you what an entry is.** It reflects which Blackboard
subsystem produced the entry, not its importance. In the example above a quiz
announcement came through as `"content"` — the same value as an uploaded `.c`
file — because the instructor attached it to course material. Never filter for
exams by `type`. **The meaning is in `title` and `body`;** read them.

**An empty result is a real answer,** not a failure. `{}` from `eventsFetcher`
means nothing is due; `[]` from `streamFetcher` means nothing was posted in the
window. Say so plainly. Do not retry, and do not run `cookieFetcher` to "fix" it
— a broken session raises an error instead.

**Dates are ISO 8601 UTC.** Convert to the student's `TIMEZONE` (`Asia/Beirut`)
before showing them, and prefer a readable form like "Monday, September 15 at
2:00 PM".

**Do not paste raw JSON at the user.** Summarise: lead with whatever is
time-sensitive, group by course, and give the dates in their timezone.

**`--days` filters client-side**, so it cannot reach further back than the window
Blackboard itself returns — roughly the last 30 entries. Asking for 400 days
returns barely more than 30 does. If a wide window comes back suspiciously small,
that ceiling is why.

## When something goes wrong

Both fetchers refresh the session themselves when the cache is missing or the API
rejects it, so **do not run `cookieFetcher.py` preemptively.** Run it only to
force a fresh login, or if a fetcher reports a login failure:

```bash
python skills/blackboard/cookieFetcher.py
```

If it fails, check in this order: credentials in `.env`, then whether
`playwright install firefox` has been run, then whether LAU's login page is up.

If you need both fetchers *and* the cache is cold, run `cookieFetcher.py` once
first — otherwise the two scripts each open their own browser and log in twice.

## Setup

`.env` in this folder (copy `.env.example`):

- `UNI_USER` — Blackboard username
- `UNI_PASS` — Blackboard password
- `TIMEZONE` — IANA timezone used to compute "today" (e.g. `Asia/Beirut`)

Then:

```bash
pip install -r requirements.txt
playwright install firefox
```

## How it works

- `cookieFetcher.py` drives a headless Firefox through LAU's SAML login and
  caches the session in `cookies.json` beside it. The SAML handshake takes about
  20 seconds; the timeouts allow for that.
- `eventsFetcher.py` and `streamFetcher.py` are plain HTTP — no browser — and
  reuse those cookies. Each falls back to `cookieFetcher.refresh()` on a 401/403
  or a missing cache.
- The stream API primes its providers on the first POST and only returns entries
  on a later one, so `streamFetcher` polls. It also needs an `X-Blackboard-Xsrf`
  header scraped from the stream page's HTML; there is no XSRF cookie.

## Scope

This skill only reads Blackboard. Sending reminders over WhatsApp is separate —
see the `whatsapp/` folder at the repo root.
