"""Gmail search tool using stored Google OAuth credentials."""

import base64
import json
import re
from html import unescape
from pathlib import Path
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from utils.helpers import log_info, log_error, calculate_similarity, extract_keywords
from config import MAX_SEARCH_RESULTS, GMAIL_TOKEN_PATH


GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _decode_base64url(data: str) -> str:
    if not data:
        return ""
    try:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode((data + padding).encode("utf-8")).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_payload_text(payload: Dict[str, Any]) -> str:
    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")
    parts = payload.get("parts") or []

    if mime_type == "text/plain" and body_data:
        return _decode_base64url(body_data)

    if mime_type == "text/html" and body_data:
        html_text = _decode_base64url(body_data)
        html_text = re.sub(r"<style[^>]*>.*?</style>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
        html_text = re.sub(r"<script[^>]*>.*?</script>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
        stripped = re.sub(r"<[^>]+>", " ", html_text)
        return re.sub(r"\s+", " ", unescape(stripped)).strip()

    if parts:
        plain_chunks = []
        html_chunks = []
        for part in parts:
            part_text = _extract_payload_text(part)
            if not part_text:
                continue
            if part.get("mimeType") == "text/plain":
                plain_chunks.append(part_text)
            else:
                html_chunks.append(part_text)

        combined = "\n".join(plain_chunks if plain_chunks else html_chunks)
        return re.sub(r"\s+", " ", combined).strip()

    if body_data:
        return _decode_base64url(body_data)

    return ""


def _extract_query_focused_content(content: str, query: str, snippet: str) -> str:
    text = (content or "").strip()
    if not text:
        return snippet or ""

    if not query or not query.strip():
        return text[:700]

    query_terms = [term for term in extract_keywords(query) if len(term) > 2]
    if not query_terms:
        return text[:700]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    matched = []
    min_terms = 1 if len(query_terms) <= 2 else 2
    for sentence in sentences:
        lowered = sentence.lower()
        matched_count = sum(1 for term in query_terms if term in lowered)
        if matched_count >= min_terms:
            matched.append(sentence.strip())
        if len(" ".join(matched)) > 700:
            break

    if matched:
        return " ".join(matched)[:900]

    return (snippet or text[:700]).strip()


def _load_oauth_credentials_from_user(email: str) -> Credentials | None:
    oauth_file = Path("backend/data/oauth_credentials.json")
    if not oauth_file.exists():
        return None

    try:
        oauth_db = json.loads(oauth_file.read_text(encoding="utf-8"))
    except Exception as exc:
        log_error("Failed to parse oauth_credentials.json", exc)
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
            scopes=provider_data.get("scopes") or GMAIL_SCOPES,
        )
    except Exception as exc:
        log_error("Failed to build user OAuth credentials", exc)
        return None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as exc:
            log_error("Failed to refresh Gmail credentials", exc)
            return None

    return creds


def _load_gmail_credentials(user_email: str | None = None) -> Credentials | None:
    if user_email:
        creds = _load_oauth_credentials_from_user(user_email)
        if creds:
            return creds

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


def search_gmail(query: str, user_email: str | None = None) -> List[Dict[str, Any]]:
    """
    Search through Gmail messages via the Gmail API.

    Args:
        query: User's search query (subject, sender, keywords, etc.)

    Returns:
        List of matching Gmail message summaries

    TODO:
        1. Set up OAuth 2.0 flow using google-auth / google-auth-oauthlib
        2. Build a Gmail API service: googleapiclient.discovery.build('gmail', 'v1', ...)
        3. Call service.users().messages().list(userId='me', q=query) to fetch matching IDs
        4. For each message ID call service.users().messages().get() to retrieve headers/body
        5. Parse Subject, From, To, Date, and snippet fields
        6. Rank by relevance using calculate_similarity and return top MAX_SEARCH_RESULTS
        7. Handle token refresh and API errors gracefully
    """
    log_info(f"Searching Gmail for: {query}")

    try:
        creds = _load_gmail_credentials(user_email)
        if not creds:
            log_info("No Gmail OAuth credentials found for search")
            return []

        service = build("gmail", "v1", credentials=creds)
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max(MAX_SEARCH_RESULTS * 3, 10),
        ).execute()

        messages = response.get("messages", [])
        if not messages and query.strip():
            log_info(f"No Gmail matches for '{query}', falling back to recent inbox messages")
            response = service.users().messages().list(
                userId="me",
                maxResults=max(MAX_SEARCH_RESULTS * 4, 20),
            ).execute()
            messages = response.get("messages", [])

        results: List[Dict[str, Any]] = []
        query_lower = (query or "").lower()

        for msg in messages:
            detail = service.users().messages().get(
                userId="me",
                id=msg.get("id"),
                format="full",
                metadataHeaders=["Subject", "From", "To", "Date"],
            ).execute()

            headers = {
                h.get("name", ""): h.get("value", "")
                for h in detail.get("payload", {}).get("headers", [])
            }

            subject = headers.get("Subject", "")
            sender = headers.get("From", "")
            recipient = headers.get("To", "")
            snippet = detail.get("snippet", "")
            content = _extract_payload_text(detail.get("payload", {}))
            matched_content = _extract_query_focused_content(content, query, snippet)

            score = 0.0
            if query_lower in subject.lower():
                score += 0.5
            if query_lower in sender.lower() or query_lower in recipient.lower():
                score += 0.2
            if query_lower in snippet.lower():
                score += 0.2
            score += calculate_similarity(query, subject) * 0.1

            results.append(
                {
                    "id": msg.get("id", ""),
                    "subject": subject,
                    "from": sender,
                    "to": recipient,
                    "date": headers.get("Date", ""),
                    "snippet": snippet,
                    "content": content[:2000],
                    "matched_content": matched_content,
                    "source": "Gmail",
                    "relevance_score": score,
                }
            )

        results.sort(key=lambda x: x.get("relevance_score", 0.0), reverse=True)
        top_results = results[:MAX_SEARCH_RESULTS]
        log_info(f"Found {len(top_results)} Gmail matches")
        return top_results

    except Exception as e:
        log_error("Error searching Gmail", e)
        return []


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
