"""Fetches upcoming deadlines from the Blackboard calendar API.

Uses the cookies cached by cookieFetcher, and re-runs the login through it if
those cookies are missing or no longer accepted.

Run this directly to print the deadlines as JSON:

    python eventsFetcher.py
"""

from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import requests
import urllib.parse
import json
import sys
import os

import cookieFetcher

API_URL = "https://elearn.lau.edu.lb/learn/api/v1/calendars/dueDateCalendarItems"

PAGE_SIZE = 50
MAX_PAGES = 20  # safety net, so a misbehaving API cannot loop forever


class InvalidCookies(Exception):
    # Raised when the cached session will not authenticate any more.
    pass


def add_params(url, params):
    # appends parameters to url end
    return f"{url}?{urllib.parse.urlencode(params)}"


def compute_midnight(tmz):
    # Compute and format date and time to ISO 8601
    local = ZoneInfo(tmz)
    local_midnight = datetime.now(local).replace(hour=0, minute=0, second=0, microsecond=0)
    utc_midnight = local_midnight.astimezone(timezone.utc)
    date_str = utc_midnight.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return date_str


def fetch_events(cookies, tmz):
    # returns json
    # Pages through the calendar; the API caps each response, so a single
    # request would silently drop every deadline past the first page.
    date_str = compute_midnight(tmz)

    client = requests.Session()
    client.cookies.update(cookies)

    results = []
    offset = 0

    for _ in range(MAX_PAGES):
        params = {
            "date": date_str,
            "date_compare": "greaterOrEqual",
            "includeCount": "true",
            "limit": str(PAGE_SIZE),
            "offset": str(offset),
        }

        response = client.get(add_params(API_URL, params))

        if response.status_code in (401, 403):
            raise InvalidCookies(f"API rejected the session ({response.status_code}).")
        response.raise_for_status()

        page = response.json()
        batch = page.get("results") or []
        results.extend(batch)

        # A short page is the last one; `count` closes it out when exact.
        count = (page.get("paging") or {}).get("count")
        offset += len(batch)
        if len(batch) < PAGE_SIZE or (count is not None and offset >= count):
            break

    return {"results": results}


def parse_events(data):
    # Flatten the API payload into id -> {title, endDate, course}
    events_data = {}
    for id, i in enumerate(data.get("results", [])):
        events_data[id] = {
            "title": i.get("title", "No Title"),
            "endDate": i.get("endDate", "No End Date"),
            "course": i.get("calendarNameLocalizable", {}).get("rawValue", "No Course"),
        }
    return events_data


def run(username, password, tmz):
    # Main: try the cached cookies, fall back to a fresh login.
    # Validate the timezone up front: inside the try below, a bad value would be
    # mistaken for a stale session and trigger a pointless browser login.
    if not tmz:
        raise ValueError("TIMEZONE is not set (e.g. Asia/Beirut); see .env.example in this folder.")
    try:
        ZoneInfo(tmz)
    except Exception as e:
        raise ValueError(f"TIMEZONE {tmz!r} is not a valid IANA timezone.") from e

    # An empty result is a real answer (no deadlines due), not a stale session:
    # the API answers 401 when the cookies have actually expired.
    try:
        data = fetch_events(cookieFetcher.load_cookies(), tmz)
        print("Fetched events using saved cookies.", file=sys.stderr)

    except (InvalidCookies, OSError, ValueError) as e:
        print(f"Refreshing cookies: {e}", file=sys.stderr)
        data = fetch_events(cookieFetcher.refresh(username, password), tmz)
        print("Fetched events using a fresh login.", file=sys.stderr)

    return parse_events(data)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

    events = run(
        os.environ.get("UNI_USER"),
        os.environ.get("UNI_PASS"),
        os.environ.get("TIMEZONE"),
    )
    json.dump(events, sys.stdout, indent=2)
    print()
