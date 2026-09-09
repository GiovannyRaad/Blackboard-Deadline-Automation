"""Logs into Blackboard and caches the session cookies.

Run this directly to refresh the cache when the saved cookies stop working:

    python cookieFetcher.py
"""

from playwright.sync_api import sync_playwright
import json
import os

# Resolve the cookie cache next to this file so the skill works from any cwd.
COOKIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.json")

LOGIN_URL = (
    "https://elearn.lau.edu.lb/auth-saml/saml/login"
    "?apId=_240_1&redirectUrl=https://elearn.lau.edu.lb/ultra"
)

# The SAML handshake back to Blackboard routinely takes ~20s, so these are
# deliberately generous; the old 10s limit timed out before login finished.
PAGE_TIMEOUT = 60000


def load_cookies():
    # name -> value, as requests wants them. Raises if there is no cache yet.
    with open(COOKIES_PATH, "r") as f:
        return {c["name"]: c["value"] for c in json.load(f)}


def save_cookies(browser_cookies):
    with open(COOKIES_PATH, "w") as f:
        json.dump(browser_cookies, f)


def refresh(username, password):
    # Log in with a headless browser, cache the cookies, return name -> value.
    if not username or not password:
        raise ValueError(
            "UNI_USER and UNI_PASS must be set (see .env.example in this folder)."
        )

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)  # no gui
        try:
            context = browser.new_context()
            page = context.new_page()

            # Lands on the SAML login page, which redirects to the LAU IdP.
            page.goto(LOGIN_URL, timeout=PAGE_TIMEOUT)

            page.wait_for_selector("#username", timeout=PAGE_TIMEOUT)
            page.fill("#username", username)
            page.fill("#password", password)
            page.press("#password", "Enter")

            # Back on elearn once the IdP hands the session over.
            page.wait_for_url(lambda url: "ultra" in url, timeout=PAGE_TIMEOUT)

            browser_cookies = context.cookies()
        finally:
            browser.close()

    save_cookies(browser_cookies)
    return {c["name"]: c["value"] for c in browser_cookies}


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

    cookies = refresh(os.environ.get("UNI_USER"), os.environ.get("UNI_PASS"))
    print(f"Saved {len(cookies)} cookies to {COOKIES_PATH}")
