"""
Google OAuth 2.0 Helper Module
Handles OAuth flow for Gmail, Drive, and Calendar APIs
"""

import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

# OAuth configuration
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email'
]

def get_client_config():
    """Get OAuth client configuration from environment variables"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/api/auth/google/callback")
    
    if not client_id or not client_secret:
        raise ValueError(
            "Missing Google OAuth credentials. Please set GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET in your .env file. See OAUTH_SETUP.md for instructions."
        )
    
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }

def get_authorization_url(user_email):
    """
    Generate OAuth authorization URL
    
    Args:
        user_email: Email of the user initiating OAuth
        
    Returns:
        tuple: (authorization_url, state)
    """
    try:
        client_config = get_client_config()
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/api/auth/google/callback")
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=user_email  # Pass user_email as state for tracking
        )
        
        return authorization_url, state
    except Exception as e:
        raise Exception(f"Failed to generate authorization URL: {str(e)}")

def get_credentials_from_code(code, state):
    """
    Exchange authorization code for credentials
    
    Args:
        code: Authorization code from OAuth callback
        state: State parameter (user_email) from OAuth callback
        
    Returns:
        Credentials: Google OAuth credentials object
    """
    try:
        client_config = get_client_config()
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/api/auth/google/callback")
        
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri,
            state=state
        )
        
        flow.fetch_token(code=code)
        return flow.credentials
    except Exception as e:
        raise Exception(f"Failed to exchange code for credentials: {str(e)}")

def credentials_to_dict(credentials):
    """Convert credentials object to dictionary for storage"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def dict_to_credentials(creds_dict):
    """Convert stored dictionary back to Credentials object"""
    return Credentials(
        token=creds_dict['token'],
        refresh_token=creds_dict.get('refresh_token'),
        token_uri=creds_dict['token_uri'],
        client_id=creds_dict['client_id'],
        client_secret=creds_dict['client_secret'],
        scopes=creds_dict['scopes']
    )

def build_gmail_service(credentials):
    """Build Gmail API service"""
    return build('gmail', 'v1', credentials=credentials)

def build_drive_service(credentials):
    """Build Drive API service"""
    return build('drive', 'v3', credentials=credentials)

def build_calendar_service(credentials):
    """Build Calendar API service"""
    return build('calendar', 'v3', credentials=credentials)

def fetch_gmail_messages(credentials, max_results=20, query=''):
    """
    Fetch Gmail messages using credentials
    
    Args:
        credentials: Google OAuth credentials
        max_results: Maximum number of messages to fetch
        query: Gmail search query (optional)
        
    Returns:
        list: List of email messages with metadata
    """
    try:
        service = build_gmail_service(credentials)
        
        # List messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        
        # Fetch details for each message
        detailed_messages = []
        for msg in messages:
            msg_detail = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'To', 'Subject', 'Date']
            ).execute()
            
            headers = {h['name']: h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}
            
            detailed_messages.append({
                'id': msg_detail['id'],
                'threadId': msg_detail['threadId'],
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'snippet': msg_detail.get('snippet', '')
            })
        
        return detailed_messages
    except Exception as e:
        raise Exception(f"Failed to fetch Gmail messages: {str(e)}")
