"""Google Drive search tool using the Google Drive API."""

import json
from pathlib import Path
from typing import List, Dict, Any
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from config import MAX_SEARCH_RESULTS, DRIVE_TOKEN_PATH
from utils.helpers import log_info, log_error, calculate_similarity

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _load_drive_credentials() -> Credentials | None:
    token_path = Path(DRIVE_TOKEN_PATH)
    if not token_path.exists():
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), DRIVE_SCOPES)
    except Exception as exc:
        log_error("Failed to parse Drive token file", exc)
        return None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
        except Exception as exc:
            log_error("Failed to refresh Drive token", exc)
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
        log_error("Failed to parse oauth_credentials.json for drive", exc)
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
            scopes=provider_data.get("scopes") or DRIVE_SCOPES,
        )
    except Exception as exc:
        log_error("Failed to build user Drive OAuth credentials", exc)
        return None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as exc:
            log_error("Failed to refresh Drive credentials", exc)
            return None

    return creds


def _escape_drive_query_text(text: str) -> str:
    return (text or "").replace("'", "\\'")


def _extract_content_from_file(service, file_id: str, mime_type: str, file_name: str) -> str:
    """
    Extract content from various file types stored in Google Drive.
    
    Handles:
    - Google Sheets: Export as CSV
    - Google Docs: Export as plain text
    - Google Slides: Export as text
    - PDFs: Extract text using pdfplumber
    - Text files (.txt, .csv, .json, .md): Download and read
    - Folders: Return "(This is a folder)"
    - Other: Return "(Content not extractable for this file type)"
    """
    try:
        # Folders don't have extractable content
        if mime_type == "application/vnd.google-apps.folder":
            return "(This is a folder)"
        
        # Google Sheets: Export as CSV
        if mime_type == "application/vnd.google-apps.spreadsheet":
            try:
                request = service.files().export(fileId=file_id, mimeType="text/csv")
                file_content = request.execute()
                content_str = file_content.decode("utf-8") if isinstance(file_content, bytes) else str(file_content)
                # Truncate to first 500 chars
                return content_str[:500] + ("...[truncated]" if len(content_str) > 500 else "")
            except Exception as e:
                log_error(f"Failed to export Google Sheet {file_name}", e)
                return "(Could not export Sheets content)"
        
        # Google Docs: Export as plain text
        if mime_type == "application/vnd.google-apps.document":
            try:
                request = service.files().export(fileId=file_id, mimeType="text/plain")
                file_content = request.execute()
                content_str = file_content.decode("utf-8") if isinstance(file_content, bytes) else str(file_content)
                return content_str[:500] + ("...[truncated]" if len(content_str) > 500 else "")
            except Exception as e:
                log_error(f"Failed to export Google Doc {file_name}", e)
                return "(Could not export Docs content)"
        
        # Google Slides: Export as text
        if mime_type == "application/vnd.google-apps.presentation":
            try:
                request = service.files().export(fileId=file_id, mimeType="text/plain")
                file_content = request.execute()
                content_str = file_content.decode("utf-8") if isinstance(file_content, bytes) else str(file_content)
                return content_str[:500] + ("...[truncated]" if len(content_str) > 500 else "")
            except Exception as e:
                log_error(f"Failed to export Google Slides {file_name}", e)
                return "(Could not export Slides content)"
        
        # PDFs: Extract text using pdfplumber
        if mime_type == "application/pdf":
            if pdfplumber is None:
                return "(PDF library not available)"
            try:
                request = service.files().get_media(fileId=file_id)
                file_content = BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                
                file_content.seek(0)
                with pdfplumber.open(file_content) as pdf:
                    text = ""
                    for page in pdf.pages[:3]:  # First 3 pages max
                        text += page.extract_text() + "\n"
                    return text[:500] + ("...[truncated]" if len(text) > 500 else "")
            except Exception as e:
                log_error(f"Failed to extract PDF {file_name}", e)
                return "(Could not extract PDF content)"
        
        # Text files, CSV, JSON, Markdown, etc.
        if mime_type in ["text/plain", "text/csv", "application/json", "text/markdown", "text/x-python"]:
            try:
                request = service.files().get_media(fileId=file_id)
                file_content = BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                
                content_str = file_content.getvalue().decode("utf-8", errors="ignore")
                return content_str[:500] + ("...[truncated]" if len(content_str) > 500 else "")
            except Exception as e:
                log_error(f"Failed to read text file {file_name}", e)
                return "(Could not read file content)"
        
        # Scripts and other non-extractable types
        return f"(Content not extractable for file type: {mime_type.split('.')[-1]})"
    
    except Exception as e:
        log_error(f"Error extracting content from {file_name}", e)
        return "(Error reading file)"


def search_drive(query: str, user_email: str | None = None) -> List[Dict[str, Any]]:
    """
    Search through Google Drive files via the Drive API.

    Args:
        query: User's search query (file name, content keywords, etc.)

    Returns:
        List of matching Drive file metadata records

    Requires prior OAuth connection via backend /auth/google/drive route.
    """
    log_info(f"Searching Google Drive for: {query}")

    try:
        creds = _load_oauth_credentials_from_user(user_email) if user_email else None
        if not creds:
            creds = _load_drive_credentials()
        if not creds:
            log_info("No Drive OAuth credentials found for user")
            return []

        service = build("drive", "v3", credentials=creds)
        
        # First, try searching with the specific query
        escaped_query = _escape_drive_query_text(query)
        api_query = (
            f"trashed = false and (name contains '{escaped_query}' "
            f"or fullText contains '{escaped_query}')"
        )

        response = service.files().list(
            q=api_query,
            pageSize=max(MAX_SEARCH_RESULTS * 3, 10),
            fields="files(id, name, description, mimeType, modifiedTime, webViewLink, owners(displayName,emailAddress))",
        ).execute()

        files = response.get("files", [])
        
        # Fallback: if specific query returns no results and query is not empty,
        # search with all files to give user something useful
        if not files and query.strip():
            log_info(f"No results for '{query}', falling back to all Drive files")
            fallback_query = "trashed = false"
            response = service.files().list(
                q=fallback_query,
                pageSize=max(MAX_SEARCH_RESULTS * 3, 10),
                fields="files(id, name, description, mimeType, modifiedTime, webViewLink, owners(displayName,emailAddress))",
            ).execute()
            files = response.get("files", [])
        
        results: List[Dict[str, Any]] = []
        query_lower = query.lower()

        for file_item in files:
            name = file_item.get("name", "")
            description = file_item.get("description", "")
            mime_type = file_item.get("mimeType", "")
            score = 0.0

            if query_lower in name.lower():
                score += 0.6
            if description and query_lower in description.lower():
                score += 0.3
            score += calculate_similarity(query, name) * 0.1

            owners = file_item.get("owners", [])
            owner = ""
            if owners:
                owner = owners[0].get("displayName") or owners[0].get("emailAddress", "")

            results.append(
                {
                    "id": file_item.get("id", ""),
                    "name": name,
                    "description": description,
                    "mime_type": mime_type,
                    "modified": file_item.get("modifiedTime", ""),
                    "link": file_item.get("webViewLink", ""),
                    "owner": owner,
                    "content": _extract_content_from_file(service, file_item.get("id", ""), mime_type, name),
                    "source": "Google Drive",
                    "relevance_score": score,
                }
            )

        results.sort(key=lambda item: item.get("relevance_score", 0.0), reverse=True)
        top_results = results[:MAX_SEARCH_RESULTS]
        log_info(f"Found {len(top_results)} matching Drive files")
        return top_results

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
