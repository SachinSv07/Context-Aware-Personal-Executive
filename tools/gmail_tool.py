"""Gmail search tool using the Google Gmail API."""

import base64
import json
import re
from html import unescape
from pathlib import Path
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import MAX_SEARCH_RESULTS, GMAIL_TOKEN_PATH
from utils.helpers import log_info, log_error, calculate_similarity


GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _decode_part_data(data: str) -> str:
    if not data:
        return ""
    try:
        decoded = base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="ignore")
        return decoded
    except Exception:
        return ""


def _clean_html_text(html_text: str) -> str:
    if not html_text:
        return ""
    text = re.sub(r"<style[\\s\\S]*?</style>", " ", html_text, flags=re.IGNORECASE)
    text = re.sub(r"<script[\\s\\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text


def _extract_body_from_payload(payload: Dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return ""

    def walk(part: Dict[str, Any]) -> tuple[str, str]:
        text_plain = ""
        text_html = ""

        mime_type = (part.get("mimeType") or "").lower()
        body = part.get("body") or {}
        data = body.get("data")

        if data:
            decoded = _decode_part_data(data)
            if mime_type == "text/plain":
                text_plain += decoded
            elif mime_type == "text/html":
                text_html += decoded

        for child in part.get("parts", []) or []:
            child_plain, child_html = walk(child)
            if child_plain:
                text_plain += "\n" + child_plain
            if child_html:
                text_html += "\n" + child_html

        return text_plain.strip(), text_html.strip()

    plain, html = walk(payload)
    if plain:
        return re.sub(r"\s+", " ", plain).strip()
    if html:
        return _clean_html_text(html)
    return ""


def _load_gmail_credentials() -> Credentials | None:
    """Load and refresh Gmail OAuth credentials from token file."""
    token_path = Path(GMAIL_TOKEN_PATH)
    if not token_path.exists():
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), GMAIL_SCOPES)
    except Exception as exc:
        log_error("Failed to parse Gmail token file", exc)
        return None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
        except Exception as exc:
            log_error("Failed to refresh Gmail token", exc)
            return None

    return creds


def search_gmail(query: str) -> List[Dict[str, Any]]:
    """
    Search through Gmail messages via the Gmail API.

    Args:
        query: User's search query (subject, sender, keywords, etc.)

    Returns:
        List of matching Gmail message summaries

    Requires prior OAuth connection via backend /auth/google route.
    """
    log_info(f"Searching Gmail for: {query}")

    try:
        creds = _load_gmail_credentials()
        if not creds:
            log_error(f"Gmail token not found or invalid: {GMAIL_TOKEN_PATH}")
            return []

        service = build("gmail", "v1", credentials=creds)
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=MAX_SEARCH_RESULTS,
        ).execute()

        messages = response.get("messages", [])
        results: List[Dict[str, Any]] = []

        for msg in messages:
            detail = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full",
                metadataHeaders=["Subject", "From", "To", "Date"],
            ).execute()

            headers = {
                item.get("name", ""): item.get("value", "")
                for item in detail.get("payload", {}).get("headers", [])
            }

            subject = headers.get("Subject", "")
            snippet = detail.get("snippet", "")
            body_content = _extract_body_from_payload(detail.get("payload"))
            score = 0.0
            if query.lower() in subject.lower():
                score += 0.6
            if query.lower() in snippet.lower():
                score += 0.3
            if body_content and query.lower() in body_content.lower():
                score += 0.4
            score += calculate_similarity(query, subject) * 0.1
            if body_content:
                score += calculate_similarity(query, body_content[:2000]) * 0.1

            results.append(
                {
                    "id": msg.get("id", ""),
                    "subject": subject,
                    "from": headers.get("From", ""),
                    "to": headers.get("To", ""),
                    "date": headers.get("Date", ""),
                    "snippet": snippet,
                    "content": body_content,
                    "relevance_score": score,
                    "source": "Gmail",
                }
            )

        results.sort(key=lambda item: item["relevance_score"], reverse=True)
        top_results = results[:MAX_SEARCH_RESULTS]
        log_info(f"Found {len(top_results)} matching Gmail messages")
        return top_results

    except Exception as e:
        log_error("Error searching Gmail", e)
        return []


class GmailTool:
    """
    Class-based Gmail search tool using the Google Gmail API.
    Requires an authenticated service object built via OAuth 2.0.

    Usage:
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        tool = GmailTool(service)
        results = tool.run("meeting tomorrow")
    """

    def __init__(self, service):
        """
        Args:
            service: Authenticated Gmail API service object from
                     googleapiclient.discovery.build('gmail', 'v1', credentials=creds)
        """
        self.service = service

    def run(self, query: str):
        """
        Search Gmail messages matching the query.

        Args:
            query: Gmail search query string (same syntax as Gmail search bar).

        Returns:
            List of message snippet strings, or a 'not found' message.
        """
        try:
            results = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=MAX_SEARCH_RESULTS,
            ).execute()

            messages = results.get("messages", [])
            emails = []

            for msg in messages:
                msg_data = self.service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                ).execute()

                headers = {
                    item.get("name", ""): item.get("value", "")
                    for item in msg_data.get("payload", {}).get("headers", [])
                }
                snippet = msg_data.get("snippet", "")
                emails.append(
                    {
                        "subject": headers.get("Subject", ""),
                        "from": headers.get("From", ""),
                        "date": headers.get("Date", ""),
                        "snippet": snippet,
                    }
                )

            if not emails:
                return "No relevant Gmail messages found"

            return emails

        except Exception as e:
            return f"Error searching Gmail: {e}"


# Tool specification for OpenAI function calling
GMAIL_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_gmail",
        "description": (
            "Search through Gmail messages by subject, sender, recipient, or content. "
            "Use this when the user asks about emails, inbox messages, or Gmail correspondence."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant Gmail messages"
                }
            },
            "required": ["query"]
        }
    }
}


if __name__ == "__main__":
    test_query = "meeting tomorrow"
    results = search_gmail(test_query)
    print(f"Gmail search results for '{test_query}':")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. [{result.get('date', '')}] {result.get('subject', '')} "
              f"— from {result.get('from', '')} "
              f"(Score: {result.get('relevance_score', 0):.2f})")
