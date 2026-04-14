"""
Strava Activity Pull to JSON
----------------------------
Fetches all activities from the Strava API and writes them to activities.json.

Setup:
  1. Copy .env.example to .env and fill in your credentials.
  2. pip install -r requirements.txt
  3. python strava_pull.py

To get credentials:
  - Create an app at https://www.strava.com/settings/api
  - Authorize with activity:read scope (or activity:read_all for private activities)
    using the URL below — replace YOUR_CLIENT_ID:
      https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all
  - Exchange the returned code for tokens via POST /oauth/token (grant_type=authorization_code)
    to get your refresh_token.

  NOTE: The "read" scope only covers public profile data and does NOT include
  activities. You must have activity:read (or activity:read_all) scope.
"""

import json
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

TOKEN_URL      = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
OUTPUT_FILE    = "activities.json"
PER_PAGE       = 200  # max allowed by Strava


def get_access_token() -> str:
    """Exchange the refresh token for a short-lived access token."""
    resp = requests.post(TOKEN_URL, data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type":    "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_activities(access_token: str) -> list[dict]:
    """Page through all activities and return them as a list."""
    headers    = {"Authorization": f"Bearer {access_token}"}
    activities = []
    page       = 1

    while True:
        resp = requests.get(ACTIVITIES_URL, headers=headers, params={
            "per_page": PER_PAGE,
            "page":     page,
        }, timeout=30)
        resp.raise_for_status()

        batch = resp.json()
        if not batch:
            break

        activities.extend(batch)
        print(f"  page {page}: {len(batch)} activities (total so far: {len(activities)})")

        if len(batch) < PER_PAGE:
            break  # last page
        page += 1

    return activities


def main() -> None:
    missing = [v for v in ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN")
               if not os.getenv(v)]
    if missing:
        sys.exit(f"Missing required environment variables: {', '.join(missing)}\n"
                 "Copy .env.example to .env and fill in your credentials.")

    print("Fetching access token...")
    token = get_access_token()

    print("Fetching activities...")
    activities = fetch_activities(token)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(activities, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(activities)} activities written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
