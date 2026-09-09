<h1 align="left">
  <img src="assets/icon.png" alt="Logo" width="35">
  Blackboard Deadline Automation
  
</h1>

An agent skill that reads my university Blackboard account — upcoming deadlines
from the calendar, and recent activity stream posts where instructors announce
exams, quizzes and materials. It returns JSON, so an AI agent can answer "what's
due this week?" or "did anything get posted?" against live data.

Built for my own use at LAU, so the login flow is specific to LAU's SAML setup.

---

## What it does

The skill lives in [`skills/blackboard/`](skills/blackboard/) and exposes two
independent sources of information:

| Source | Script | Holds |
|---|---|---|
| Calendar | `eventsFetcher.py` | Items with a real **due date** set by the instructor |
| Activity stream | `streamFetcher.py` | Everything posted to the homepage: announcements, uploaded files, exam and quiz notices |

`cookieFetcher.py` is the shared login. It drives a headless browser through
LAU's SAML flow once and caches the session, so the two fetchers are plain HTTP
and fast.

The two sources genuinely do not overlap. Instructors regularly announce exams
in the stream without ever setting a calendar due date — the calendar can be
completely empty while a quiz sits six days away. That is why the stream fetcher
exists, and why [`SKILL.md`](skills/blackboard/SKILL.md) tells the agent to check
both whenever the question is about what is coming up.

---

## How this project evolved

It started as **G.E.R.A.S** (*Gio's Essential Reminder Automated System*), a
standalone script that scraped my Blackboard deadlines and pushed them to me as
WhatsApp messages on a schedule.

Three things changed since:

**Renamed.** The old acronym said nothing about what the project did.
*Blackboard Deadline Automation* is plainer and actually describes it.

**Turned into an agent skill rather than a standalone script.** This is the big
one. The original design had to guess in advance what I wanted to know, and
deliver it on a fixed schedule in a fixed format. With capable AI agents now able
to run tools on demand, exposing the data as a skill turned out to be far more
useful than pushing notifications: I can ask about anything — a specific course,
a date range, whether an exam was mentioned — and get an answer from live data,
instead of receiving whatever the script decided to send. The scripts were split
so each does one job and returns clean JSON on stdout, and `SKILL.md` documents
for the agent which to reach for.

**Added the activity stream.** Originally only the calendar was read, which meant
anything an instructor posted without a due date was invisible — including exam
announcements, which is exactly the thing you least want to miss. The stream
fetcher closed that gap.

### Status of the WhatsApp reminders

The WhatsApp integration is **no longer a main feature and is not maintained.**
It works, and it stays in the repo for now under [`whatsapp/`](whatsapp/), but
the agent skill has replaced it as the point of the project. It may be removed
later.

---

## Requirements

Python 3.11. The skill needs its own `.env`, with a `.env.example` template
beside it:

`skills/blackboard/.env`

```
UNI_USER               # Blackboard username
UNI_PASS               # Blackboard password
TIMEZONE               # IANA timezone, e.g. Asia/Beirut
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/GiovannyRaad/Blackboard-Deadline-Automation.git
cd Blackboard-Deadline-Automation
```

2. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the skill's dependencies:

```bash
pip install -r skills/blackboard/requirements.txt
```

4. Download the browser Playwright drives for the login:

```bash
playwright install firefox
```

5. Create the `.env` from its template and fill it in:

```bash
cp skills/blackboard/.env.example skills/blackboard/.env
```

---

## Usage

Each script prints JSON to stdout; progress messages go to stderr.

```bash
# upcoming deadlines
python skills/blackboard/eventsFetcher.py

# activity stream, last 7 days by default
python skills/blackboard/streamFetcher.py
python skills/blackboard/streamFetcher.py --days 30

# force a fresh login (the fetchers do this themselves when needed)
python skills/blackboard/cookieFetcher.py
```

Expect a couple of seconds on a warm cookie cache, or around 40 seconds when it
has to log in first.

For agent use, [`skills/blackboard/SKILL.md`](skills/blackboard/SKILL.md) is the
entry point — it covers which script answers which kind of question, the output
shapes, and the traps worth knowing.

---

## Legacy: WhatsApp reminders

> **Unmaintained.** Kept for the time being, may be removed.

The original delivery mechanism: fetch deadlines, then send each one as a
WhatsApp template message via **Meta's [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)**.

<img src="assets/Screenshot.jpeg" alt="Example WhatsApp reminder" width="500">

It needs its own credentials in `whatsapp/.env`:

```
TOKEN                  # Meta Cloud API token
PHONEID                # Sender phone number ID
PHONE                  # Receiver phone number
TEMPLATE_NAME          # Approved WhatsApp message template name
BUSINESS_ACOUNT_ID     # Meta Business Account ID (not read by any code)
```

Then, having installed `whatsapp/requirements.txt` as well:

```bash
cp whatsapp/.env.example whatsapp/.env
python main.py
```

`main.py` loads both `.env` files, fetches the deadlines, and sends one message
per deadline. It was intended to run on a schedule, e.g. weekly.

> ⚠️ WhatsApp per-message pricing may apply: [Pricing](https://business.whatsapp.com/products/platform-pricing)

> Logs and message delivery tracking via Meta Webhooks were planned but never implemented.

---

## Project Structure

```
skills/
  blackboard/                            # the agent skill -- the point of the project
    SKILL.md                             # how an agent should use it
    .env / .env.example                  # Blackboard credentials
    eventsFetcher.py                     # calls the calendar API
    streamFetcher.py                     # calls the activity stream API
    cookieFetcher.py                     # logs in, caches the session
    cookies.json                         # cached session, written on first login
    requirements.txt
whatsapp/                                # legacy reminder delivery, unmaintained
  .env / .env.example                    # Meta Cloud API credentials
  messageSender.py
  webhook.py
  requirements.txt
main.py                                  # legacy entry point: deadlines -> WhatsApp
requirements.txt                         # union of both halves
```

---

## Tech Stack

* Python 3.11
* `playwright` for the SAML login, `requests` for the APIs, `beautifulsoup4` for
  announcement HTML
* `pywa` for the legacy WhatsApp delivery

---

## License

```
MIT License

Copyright (c) 2025 GiovannyRaad

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

![Footer Banner](assets/banner.png)
