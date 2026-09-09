"""Fetches recent entries from the Blackboard activity stream.

The stream is the Blackboard homepage (https://elearn.lau.edu.lb/ultra/stream),
where instructors post announcements, upload material, and mention exams that
never make it onto the calendar as a due date.

Talks to the same JSON API the page itself uses, over plain HTTP requests,
reusing the cookies cached by cookieFetcher.

    python streamFetcher.py            # last 7 days
    python streamFetcher.py --days 30  # last 30 days

Status messages go to stderr, so stdout stays parseable JSON.
"""

from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
import argparse
import json
import time
import sys
import re
import os

import cookieFetcher

BASE = "https://elearn.lau.edu.lb"
STREAM_PAGE = f"{BASE}/ultra/stream"
STREAM_API = f"{BASE}/learn/api/v1/streams/ultra"

DEFAULT_DAYS = 7

# providerId -> a friendlier label
ENTRY_TYPES = {
    "bb-announcement": "announcement",
    "bb-nautilus": "content",
    "bb_mygrades": "grade",
    "bb_disc": "discussion",
    "bb_calendar": "calendar",
    "bb_blog": "blog",
    "bb_Wiki": "wiki",
    "bb_ach_stream": "achievement",
}


class InvalidCookies(Exception):
    # Raised when the cached session will not authenticate any more.
    pass


class StreamIncomplete(Exception):
    # Raised when the API never finished assembling the stream. Deliberately not
    # caught by run(): the session is fine, so logging in again would not help,
    # and returning [] would look identical to "nothing was posted".
    pass


def get_xsrf(session):
    # The token is embedded in the stream page's HTML, not in a cookie.
    html = session.get(STREAM_PAGE, timeout=30).text
    match = re.search(r'xsrf["\']?\s*:\s*["\']([^"\']+)["\']', html)
    if not match:
        raise InvalidCookies("No XSRF token in the stream page; the session looks stale.")
    return match.group(1)


def fetch_stream(cookies, polls=6, delay=3):
    # returns json
    # The API primes its providers on the first POST and only returns entries on
    # a later one, so poll until entries show up.
    session = requests.Session()
    session.cookies.update(cookies)

    headers = {"X-Blackboard-Xsrf": get_xsrf(session), "Content-Type": "application/json"}
    providers = {}
    data = {}

    for attempt in range(polls):
        response = session.post(
            STREAM_API,
            headers=headers,
            json={"providers": providers, "forOverview": False, "retrieveOnly": True},
            timeout=60,
        )
        if response.status_code in (401, 403):
            raise InvalidCookies(f"API rejected the session ({response.status_code}).")
        response.raise_for_status()

        data = response.json()
        # Entries arrived, or the API says it has nothing more coming -- either
        # way this is the real answer. sv_moreData stays true only while the
        # stream is still being assembled.
        if data.get("sv_streamEntries") or not data.get("sv_moreData"):
            return data

        # Hand the provider state back so the next poll returns the entries.
        providers = {
            p["sp_provider"]: {k: v for k, v in p.items() if k != "sp_provider"}
            for p in data.get("sv_providers") or []
            if isinstance(p, dict) and "sp_provider" in p
        }
        if attempt < polls - 1:
            time.sleep(delay)

    raise StreamIncomplete(
        f"The stream API still reported more data after {polls} polls; "
        "no entries were returned. Try again."
    )


def html_to_text(html):
    # Announcement bodies are HTML; flatten them to a readable one-liner.
    if not html:
        return ""
    return " ".join(BeautifulSoup(html, "html.parser").get_text(" ").split())


def parse_stream(data, days=DEFAULT_DAYS):
    # Flatten the payload into a list of entries newer than `days` ago.
    courses = {
        c.get("id"): c.get("name")
        for c in data.get("sv_extras", {}).get("sx_courses", [])
    }
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000

    entries = []
    for e in data.get("sv_streamEntries", []):
        timestamp = e.get("se_timestamp")
        if not timestamp or timestamp < cutoff:
            continue

        item = e.get("itemSpecificData") or {}
        notif = item.get("notificationDetails") or {}

        url = notif.get("announcementUrl")
        entries.append({
            "title": notif.get("announcementTitle") or item.get("title") or "No Title",
            "course": (courses.get(e.get("se_courseId"))
                       or courses.get(notif.get("courseId"))
                       or "Institution-wide"),
            "posted": datetime.fromtimestamp(timestamp / 1000, timezone.utc).isoformat(),
            "type": ENTRY_TYPES.get(e.get("providerId"), e.get("providerId")),
            "body": html_to_text(notif.get("announcementBody")) or html_to_text(item.get("contentExtract")),
            "url": urljoin(BASE, url) if url else None,
        })

    entries.sort(key=lambda x: x["posted"], reverse=True)
    return entries


def run(days=DEFAULT_DAYS, username=None, password=None):
    # Main: try the cached cookies, fall back to a fresh login.
    try:
        data = fetch_stream(cookieFetcher.load_cookies())
    except (InvalidCookies, OSError, ValueError) as e:
        print(f"Refreshing cookies: {e}", file=sys.stderr)
        data = fetch_stream(cookieFetcher.refresh(username, password))
        print("Fetched stream using a fresh login.", file=sys.stderr)
    else:
        print("Fetched stream using saved cookies.", file=sys.stderr)

    return parse_stream(data, days)


if __name__ == "__main__":
    from dotenv import load_dotenv

    parser = argparse.ArgumentParser(description="Fetch recent Blackboard activity stream entries.")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS,
                        help=f"how many days back to include (default: {DEFAULT_DAYS})")
    args = parser.parse_args()

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

    entries = run(
        days=args.days,
        username=os.environ.get("UNI_USER"),
        password=os.environ.get("UNI_PASS"),
    )
    json.dump(entries, sys.stdout, indent=2)
    print()
