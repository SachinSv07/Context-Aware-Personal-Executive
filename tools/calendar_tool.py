"""Google Calendar search tool using the Google Calendar API."""

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


def search_calendar(query: str) -> List[Dict[str, Any]]:
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
        creds = _load_calendar_credentials()
        if not creds:
            log_error(f"Calendar token not found or invalid: {CALENDAR_TOKEN_PATH}")
            return []

        service = build("calendar", "v3", credentials=creds)
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
