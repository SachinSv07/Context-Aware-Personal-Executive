"""
Google Drive search tool using the Google Drive API
Requires OAuth 2.0 credentials (credentials.json) and the google-api-python-client package.
"""

from typing import List, Dict, Any
from utils.helpers import log_info, log_error, calculate_similarity
from config import MAX_SEARCH_RESULTS


def search_drive(query: str) -> List[Dict[str, Any]]:
    """
    Search through Google Drive files via the Drive API.

    Args:
        query: User's search query (file name, content keywords, etc.)

    Returns:
        List of matching Drive file metadata records

    TODO:
        1. Set up OAuth 2.0 flow using google-auth / google-auth-oauthlib
        2. Build a Drive API service: googleapiclient.discovery.build('drive', 'v3', ...)
        3. Call service.files().list(q=f"fullText contains '{query}'", fields='files(...)') 
        4. Parse id, name, mimeType, modifiedTime, webViewLink from each file record
        5. Rank by relevance using calculate_similarity on file name vs. query
        6. Return top MAX_SEARCH_RESULTS results
        7. Handle token refresh and API errors gracefully
    """
    log_info(f"Searching Google Drive for: {query}")

    try:
        # --- Google API setup (placeholder) ---
        # from google.oauth2.credentials import Credentials
        # from google_auth_oauthlib.flow import InstalledAppFlow
        # from googleapiclient.discovery import build
        #
        # SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        # creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # service = build('drive', 'v3', credentials=creds)
        #
        # response = service.files().list(
        #     q=f"fullText contains '{query}' and trashed = false",
        #     pageSize=MAX_SEARCH_RESULTS,
        #     fields="files(id, name, mimeType, modifiedTime, webViewLink, owners)"
        # ).execute()
        # files = response.get('files', [])
        # results = []
        # for f in files:
        #     score = calculate_similarity(query, f.get('name', ''))
        #     results.append({
        #         'id':           f.get('id', ''),
        #         'name':         f.get('name', ''),
        #         'mime_type':    f.get('mimeType', ''),
        #         'modified':     f.get('modifiedTime', ''),
        #         'link':         f.get('webViewLink', ''),
        #         'owner':        f.get('owners', [{}])[0].get('displayName', ''),
        #         'relevance_score': score
        #     })
        # results.sort(key=lambda x: x['relevance_score'], reverse=True)
        # return results[:MAX_SEARCH_RESULTS]

        # Stub: replace with real API call above
        log_info("Drive API not yet configured – returning empty results")
        return []

    except Exception as e:
        log_error("Error searching Google Drive", e)
        return []


# Tool specification for OpenAI function calling
DRIVE_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "search_drive",
        "description": (
            "Search through Google Drive files by name or content. "
            "Use this when the user asks about documents, spreadsheets, presentations, "
            "or any files stored in Google Drive."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant Google Drive files"
                }
            },
            "required": ["query"]
        }
    }
}


if __name__ == "__main__":
    test_query = "project proposal"
    results = search_drive(test_query)
    print(f"Drive search results for '{test_query}':")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result.get('name', '')} [{result.get('mime_type', '')}] "
              f"— modified {result.get('modified', '')} "
              f"(Score: {result.get('relevance_score', 0):.2f})")
