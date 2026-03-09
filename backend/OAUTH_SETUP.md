# Google OAuth Setup Guide

This guide explains how to set up Google OAuth 2.0 for Gmail, Google Drive, and Google Calendar integration.

## Prerequisites

1. A Google Cloud Platform (GCP) account
2. A project in Google Cloud Console
3. Billing enabled (required for some APIs, but free tier is sufficient for development)

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "Context-Aware-Executive")
5. Click "Create"

## Step 2: Enable Required APIs

1. In Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for and enable the following APIs:
   - **Gmail API** - For email access
   - **Google Drive API** - For file access
   - **Google Calendar API** - For calendar access
   - **Google Picker API** - For Drive file picker UI

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** (for testing with any Google account)
3. Fill in the required information:
   - **App name**: Context-Aware Personal Executive
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **Save and Continue**
5. On the Scopes page, click **Add or Remove Scopes**
6. Add the following scopes:
   ```
   https://www.googleapis.com/auth/gmail.readonly
   https://www.googleapis.com/auth/drive.readonly
   https://www.googleapis.com/auth/calendar.readonly
   ```
7. Click **Save and Continue**
8. Add test users (your email addresses) for testing
9. Click **Save and Continue**

## Step 4: Create OAuth 2.0 Credentials

### For Backend API (Server-side)

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose **Web application**
4. Set the following:
   - **Name**: Backend API Client
   - **Authorized JavaScript origins**: 
     - `http://localhost:5000`
     - `http://localhost:3000` (for development)
   - **Authorized redirect URIs**:
     - `http://localhost:5000/api/auth/google/callback`
     - `http://localhost:3000/auth/callback`
5. Click **Create**
6. Save the **Client ID** and **Client Secret**

### For Frontend (Google Picker API)

1. Click **Create Credentials** > **API key**
2. Save the **API Key**
3. Click **Edit API key** (optional but recommended)
4. Under **API restrictions**, select **Restrict key**
5. Select: Google Picker API, Google Drive API
6. Save

## Step 5: Update Environment Variables

Add the following to your `.env` file:

```env
# Google OAuth Credentials
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_API_KEY=your-api-key
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback

# Scopes
GOOGLE_SCOPES=https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/calendar.readonly
```

## Step 6: Install Required Python Packages

Add to `requirements.txt`:

```txt
google-auth>=2.22.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.95.0
```

Then install:

```bash
pip install -r requirements.txt
```

## Step 7: Implement OAuth Flow in Backend

### Create OAuth Helper Module

Create `backend/oauth_helper.py`:

```python
import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# OAuth configuration
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/calendar.readonly'
]

CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")]
    }
}

def get_authorization_url():
    """Generate OAuth authorization URL"""
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return authorization_url, state

def get_credentials_from_code(code, state):
    """Exchange authorization code for credentials"""
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
        state=state
    )
    
    flow.fetch_token(code=code)
    return flow.credentials

def build_gmail_service(credentials):
    """Build Gmail API service"""
    return build('gmail', 'v1', credentials=credentials)

def build_drive_service(credentials):
    """Build Drive API service"""
    return build('drive', 'v3', credentials=credentials)

def build_calendar_service(credentials):
    """Build Calendar API service"""
    return build('calendar', 'v3', credentials=credentials)
```

### Update API Endpoints

Add to `backend/api.py`:

```python
from oauth_helper import (
    get_authorization_url, 
    get_credentials_from_code,
    build_gmail_service,
    build_drive_service,
    build_calendar_service
)

# Store user credentials (in production, use a database)
user_credentials = {}

@app.route('/api/auth/google/initiate', methods=['GET'])
def initiate_google_oauth():
    """Initiate Google OAuth flow"""
    try:
        authorization_url, state = get_authorization_url()
        
        # Store state in session or database
        # session['oauth_state'] = state
        
        return jsonify({
            'authorization_url': authorization_url,
            'state': state
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/google/callback', methods=['GET'])
def google_oauth_callback():
    """Handle OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            return jsonify({'error': 'No authorization code'}), 400
        
        # Exchange code for credentials
        credentials = get_credentials_from_code(code, state)
        
        # Store credentials for user
        user_email = get_current_user()
        user_credentials[user_email] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Redirect to frontend success page
        return redirect('http://localhost:3000/dashboard?oauth=success')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gmail/messages', methods=['GET'])
def get_gmail_messages():
    """Fetch Gmail messages"""
    try:
        user_email = get_current_user()
        
        if user_email not in user_credentials:
            return jsonify({'error': 'Not authenticated with Gmail'}), 401
        
        # Rebuild credentials object
        creds_data = user_credentials[user_email]
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )
        
        # Build Gmail service
        service = build_gmail_service(credentials)
        
        # Fetch messages
        results = service.users().messages().list(
            userId='me',
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        return jsonify({'messages': messages})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## Step 8: Frontend Integration

### Update React Dashboard

Install Google API Client:

```bash
cd frontend
npm install gapi-script
```

Update `Dashboard.jsx` to use real Google Picker:

```javascript
import { useEffect } from 'react';

const GoogleDriveCard = ({ onUpload }) => {
  useEffect(() => {
    // Load Google Picker API
    const script = document.createElement('script');
    script.src = 'https://apis.google.com/js/api.js';
    script.onload = () => {
      window.gapi.load('picker', () => {
        console.log('Google Picker API loaded');
      });
    };
    document.body.appendChild(script);
  }, []);

  const handleDriveUpload = () => {
    const picker = new window.google.picker.PickerBuilder()
      .addView(window.google.picker.ViewId.DOCS)
      .setOAuthToken(accessToken)  // Get from OAuth flow
      .setDeveloperKey(process.env.REACT_APP_GOOGLE_API_KEY)
      .setCallback((data) => {
        if (data.action === window.google.picker.Action.PICKED) {
          const file = data.docs[0];
          onUpload(file);
        }
      })
      .build();
    
    picker.setVisible(true);
  };

  return (
    <button onClick={handleDriveUpload}>
      Open Google Drive Picker
    </button>
  );
};
```

## Step 9: Testing

1. Start the backend: `python backend/api.py`
2. Start the frontend: `cd frontend && npm start`
3. Navigate to Dashboard
4. Click "Connect Gmail" or "Upload from Google Drive"
5. Complete OAuth flow in popup window
6. Verify connection status

## Security Best Practices

1. **Never commit credentials** - Always use environment variables
2. **Use HTTPS in production** - OAuth requires secure connections
3. **Implement CSRF protection** - Validate state parameter
4. **Store tokens securely** - Encrypt refresh tokens in database
5. **Implement token refresh** - Handle expired tokens gracefully
6. **Limit scopes** - Only request necessary permissions
7. **Validate redirect URIs** - Prevent open redirect vulnerabilities

## Troubleshooting

### "redirect_uri_mismatch" Error

- Ensure the redirect URI in Google Console exactly matches the one in your code
- Include protocol (http/https), port, and path

### "invalid_client" Error

- Check that CLIENT_ID and CLIENT_SECRET are correct
- Ensure OAuth consent screen is configured

### "access_denied" Error

- User denied permissions
- Check that all required scopes are requested

### Token Expired

- Implement token refresh using the refresh_token
- Store refresh tokens securely

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- [Google Drive API Python Quickstart](https://developers.google.com/drive/api/quickstart/python)
- [Google Picker API](https://developers.google.com/picker)

## Next Steps

Once OAuth is set up:

1. Implement Gmail message fetching and search
2. Add Google Drive file access and download
3. Integrate Calendar events display
4. Build AI query processing for cross-source search
5. Add real-time sync capabilities
