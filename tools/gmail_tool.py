"""
Gmail search tool using the Google Gmail API
Requires OAuth 2.0 credentials (credentials.json) and the google-api-python-client package.
"""

from typing import List, Dict, Any
from utils.helpers import log_info, log_error, calculate_similarity
from config import MAX_SEARCH_RESULTS


def search_gmail(query: str) -> List[Dict[str, Any]]:
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
        # --- Google API setup (placeholder) ---
        # from google.oauth2.credentials import Credentials
        # from google_auth_oauthlib.flow import InstalledAppFlow
        # from googleapiclient.discovery import build
        #
        # SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        # creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # service = build('gmail', 'v1', credentials=creds)
        #
        # response = service.users().messages().list(userId='me', q=query,
        #                                             maxResults=MAX_SEARCH_RESULTS).execute()
        # messages = response.get('messages', [])
        # results = []
        # for msg in messages:
        #     detail = service.users().messages().get(
        #         userId='me', id=msg['id'], format='metadata',
        #         metadataHeaders=['Subject', 'From', 'To', 'Date']).execute()
        #     headers = {h['name']: h['value'] for h in detail['payload']['headers']}
        #     results.append({
        #         'id': msg['id'],
        #         'subject': headers.get('Subject', ''),
        #         'from':    headers.get('From', ''),
        #         'to':      headers.get('To', ''),
        #         'date':    headers.get('Date', ''),
        #         'snippet': detail.get('snippet', ''),
        #         'relevance_score': calculate_similarity(query, headers.get('Subject', ''))
        #     })
        # results.sort(key=lambda x: x['relevance_score'], reverse=True)
        # return results[:MAX_SEARCH_RESULTS]

        # Stub: replace with real API call above
        log_info("Gmail API not yet configured – returning empty results")
        return []

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
