"""Google Calendar search tool using the Google Calendar API."""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import MAX_SEARCH_RESULTS, CALENDAR_TOKEN_PATH
from utils.helpers import log_info, log_error, calculate_similarity


CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _extract_person_for_birthday_query(query: str) -> str:
    q = (query or "").strip().lower()
    match = re.search(r"when\s+is\s+(.+?)\s+(?:birthday|dob|date\s+of\s+birth)", q)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1).strip())


def _load_calendar_credentials() -> Credentials | None:
    token_path = Path(CALENDAR_TOKEN_PATH)
    if not token_path.exists():
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), CALENDAR_SCOPES)
    except Exception as exc:
        log_error("Failed to parse Calendar token file", exc)
        return None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
        except Exception as exc:
            log_error("Failed to refresh Calendar token", exc)
            return None

    return creds


def _load_oauth_credentials_from_user(email: str) -> Credentials | None:
    project_root = Path(__file__).resolve().parent.parent
    oauth_file = project_root / "backend" / "data" / "oauth_credentials.json"
    if not oauth_file.exists():
        return None

    try:
        oauth_db = json.loads(oauth_file.read_text(encoding="utf-8"))
    except Exception as exc:
        log_error("Failed to parse oauth_credentials.json for calendar", exc)
        return None

    provider_data = oauth_db.get((email or "").lower(), {}).get("google")
    if not provider_data:
        return None

    try:
        creds = Credentials(
            token=provider_data.get("token"),
            refresh_token=provider_data.get("refresh_token"),
            token_uri=provider_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=provider_data.get("client_id"),
            client_secret=provider_data.get("client_secret"),
            scopes=provider_data.get("scopes") or CALENDAR_SCOPES,
        )
    except Exception as exc:
        log_error("Failed to build user Calendar OAuth credentials", exc)
        return None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as exc:
            log_error("Failed to refresh Calendar credentials", exc)
            return None

    return creds


def search_calendar(query: str, user_email: str | None = None) -> List[Dict[str, Any]]:
    """
    Search through Google Calendar events via the Calendar API.

    Args:
        query: User's search query (event title, attendees, description keywords, etc.)

    Returns:
        List of matching calendar event records

    Requires prior OAuth connection via backend /auth/google/calendar route.
    """
    log_info(f"Searching Google Calendar for: {query}")

    try:
        creds = _load_oauth_credentials_from_user(user_email) if user_email else None
        if not creds:
            creds = _load_calendar_credentials()
        if not creds:
            log_info("No Calendar OAuth credentials found for user")
            return []

        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        now = datetime.now(timezone.utc)
        time_min = (now - timedelta(days=365)).isoformat()
        time_max = (now + timedelta(days=365)).isoformat()

        response = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max(MAX_SEARCH_RESULTS * 3, 10),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = response.get("items", [])
        results: List[Dict[str, Any]] = []
        query_lower = query.lower()
        person_for_birthday_query = _extract_person_for_birthday_query(query)
        is_birthday_query = any(token in query_lower for token in ["birthday", "dob", "date of birth"])

        for event in events:
            summary = event.get("summary", "")
            description = event.get("description", "")
            location = event.get("location", "")
            attendees = [a.get("email", "") for a in event.get("attendees", [])]
            attendees_text = " ".join(attendees)

            score = 0.0
            if query:
                if query_lower in summary.lower():
                    score += 0.5
                if description and query_lower in description.lower():
                    score += 0.3
                if location and query_lower in location.lower():
                    score += 0.1
                if attendees_text and query_lower in attendees_text.lower():
                    score += 0.1
                score += calculate_similarity(query, summary) * 0.1

                if is_birthday_query and person_for_birthday_query:
                    person_match_space = f" {person_for_birthday_query} "
                    summary_norm = f" {summary.lower()} "
                    description_norm = f" {description.lower()} "

                    if person_match_space in summary_norm or person_match_space in description_norm:
                        score += 1.25
                    else:
                        score -= 0.75
            else:
                score = 0.5

            start = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", ""))
            end = event.get("end", {}).get("dateTime", event.get("end", {}).get("date", ""))

            organizer = event.get("organizer", {})
            organizer_text = organizer.get("email", "") or organizer.get("displayName", "")

            results.append(
                {
                    "id": event.get("id", ""),
                    "summary": summary,
                    "start": start,
                    "end": end,
                    "location": location,
                    "description": description,
                    "attendees": attendees,
                    "organizer": organizer_text,
                    "link": event.get("htmlLink", ""),
                    "source": "Google Calendar",
                    "relevance_score": score,
                }
            )

        if is_birthday_query and person_for_birthday_query:
            person_filtered = []
            for item in results:
                summary = str(item.get("summary", "")).lower()
                description = str(item.get("description", "")).lower()
                target = person_for_birthday_query
                if target in summary or target in description:
                    person_filtered.append(item)
            if person_filtered:
                results = person_filtered

        results.sort(key=lambda item: item.get("relevance_score", 0.0), reverse=True)
        top_results = results[:MAX_SEARCH_RESULTS]
        log_info(f"Found {len(top_results)} matching Calendar events")
        return top_results

    except Exception as e:
        log_error("Error searching Google Calendar", e)
        return []


# Tool specification for OpenAI function calling
CALENDAR_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_calendar",
        "description": (
            "Search through Google Calendar events by title, description, location, or attendees. "
            "Use this when the user asks about meetings, appointments, schedules, or upcoming events."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant calendar events"
                }
            },
            "required": ["query"]
        }
    }
}


if __name__ == "__main__":
    test_query = "team standup"
    results = search_calendar(test_query)
    print(f"Calendar search results for '{test_query}':")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result.get('summary', '')} "
              f"@ {result.get('start', '')} – {result.get('end', '')} "
              f"(Score: {result.get('relevance_score', 0):.2f})")
